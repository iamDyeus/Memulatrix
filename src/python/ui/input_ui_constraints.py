import customtkinter as ctk
import json
import os
import time
import subprocess
import socket
import random

class CustomMessageBox(ctk.CTkToplevel):
    def __init__(self, parent, title, message, options):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result = None

        message_frame = ctk.CTkFrame(self)
        message_frame.pack(pady=10, padx=10, fill="both", expand=True)

        message_label = ctk.CTkLabel(message_frame, text=message, wraplength=450, font=("Arial", 12))
        message_label.pack(pady=10, padx=10)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=10, fill="x", padx=10)

        self.buttons = []
        for option in options:
            btn = ctk.CTkButton(
                button_frame,
                text=option,
                command=lambda opt=option: self.on_button_click(opt),
                width=100
            )
            btn.pack(side="left", padx=15, pady=10)
            self.buttons.append(btn)
            btn.update()

        self.update_idletasks()

        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.geometry(f"+{x}+{y}")

    def on_button_click(self, option):
        self.result = option
        self.destroy()

    def get(self):
        self.wait_window()
        return self.result

class LogicHandler:
    def __init__(self, ui, env_file_path=None, proc_file_path=None, simulator_path=None, simulator_process=None):
        self.ui = ui
        self.env_file_path = env_file_path
        self.proc_file_path = proc_file_path
        self.process_data = []
        self.next_process_id = 1001
        self.simulator_path = simulator_path
        self.simulator_process = simulator_process
        self.sock = None
        self.setup_socket()

    def setup_socket(self):
        max_attempts = 10
        time.sleep(3.0)  # Initial delay to ensure simulator is ready
        for attempt in range(max_attempts):
            try:
                print(f"Attempt {attempt + 1}: Connecting to TCP server at 127.0.0.1:12345")
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect(("127.0.0.1", 12345))
                print(f"Attempt {attempt + 1}: Successfully connected to TCP server")
                return
            except socket.error as e:
                print(f"Attempt {attempt + 1}: Failed to connect, error: {e}")
                self.sock.close()
                self.sock = None
                time.sleep(1.0)
                if attempt == max_attempts - 1:
                    raise RuntimeError(f"Failed to connect to TCP server after {max_attempts} attempts. Last error: {e}")

    def reconnect_socket(self):
        if self.sock:
            try:
                self.sock.close()
            except socket.error as e:
                print(f"Error closing socket: {e}")
            self.sock = None
        time.sleep(1.0)
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                print(f"Reconnect attempt {attempt + 1}: Connecting to TCP server")
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect(("127.0.0.1", 12345))
                print(f"Reconnect attempt {attempt + 1}: Successfully reconnected")
                return
            except socket.error as e:
                print(f"Reconnect attempt {attempt + 1}: Failed, error: {e}")
                time.sleep(1.0)
                if attempt == max_attempts - 1:
                    print("Restarting simulator due to repeated reconnect failures")
                    self.start_simulator(force_new=True)
                    self.setup_socket()

    def start_simulator(self, force_new=False):
        if force_new and self.simulator_process:
            self.simulator_process.terminate()
            self.simulator_process = None
        if not self.simulator_process or self.simulator_process.poll() is not None:
            if not os.path.exists(self.simulator_path):
                CustomMessageBox(self.ui.app, "Error", f"Simulator not found at {self.simulator_path}", ["OK"])
                return False
            try:
                self.simulator_process = subprocess.Popen(self.simulator_path, shell=True)
                time.sleep(3.0)
                if self.simulator_process.poll() is not None:
                    CustomMessageBox(self.ui.app, "Error", "Simulator failed to start.", ["OK"])
                    return False
                return True
            except Exception as e:
                CustomMessageBox(self.ui.app, "Error", f"Error starting simulator: {e}", ["OK"])
                return False
        return True

    def on_closing(self):
        if self.simulator_process:
            self.simulator_process.terminate()
        if self.sock:
            try:
                self.sock.close()
                print("Closed TCP socket on UI exit")
            except socket.error as e:
                print(f"Error closing socket: {e}")
            self.sock = None
        self.ui.app.destroy()

    def send_to_cpp(self, force_new=False):
        if not self.start_simulator(force_new):
            return

        settings = {
            "ram_size_gb": int(self.ui.ram_size_var.get()),
            "page_size_kb": int(self.ui.page_size_var.get().replace("KB", "")) if self.ui.page_size_var.get() else 0,
            "tlb_size": int(self.ui.tlb_size_var.get()) if self.ui.tlb_size_var.get() else 0,
            "tlb_enabled": self.ui.tlb_enabled_var.get(),
            "virtual_address_size": self.ui.va_size_var.get(),
            "rom_size": self.ui.rom_size_var.get(),
            "swap_percent": float(self.ui.swap_percent_var.get()),
            "allocation_type": self.ui.memory_allocation_var.get(),
            "processes": self.process_data
        }

        config_str = json.dumps(settings)
        config_bytes = config_str.encode('utf-8')
        config_size = len(config_bytes)

        print(f"Sending configuration to C++: {config_str[:50]}...")
        print(f"Configuration size: {config_size} bytes")

        try:
            self.sock.sendall(config_bytes)
            print("Configuration sent to server")

            result_str = ""
            start_time = time.time()
            timeout = 15.0
            self.sock.settimeout(0.1)  # Non-blocking for polling
            while time.time() - start_time < timeout:
                try:
                    data = self.sock.recv(1024 * 1024)
                    if not data:
                        print("Server closed connection, attempting to reconnect...")
                        self.reconnect_socket()
                        self.sock.sendall(config_bytes)
                        continue
                    result_str += data.decode('utf-8', errors='ignore')
                    if result_str:
                        break
                except socket.timeout:
                    continue
                except socket.error as e:
                    print(f"Receive error: {e}, attempting to reconnect...")
                    self.reconnect_socket()
                    self.sock.sendall(config_bytes)
                    continue
            self.sock.settimeout(None)  # Restore blocking mode

            if not result_str:
                dialog = CustomMessageBox(self.ui.app, "Error", "No simulation results received.", ["OK"])
                dialog.get()
                return

            try:
                results = json.loads(result_str)
                message = (
                    f"Simulation Results:\n"
                    f"TLB Hits: {results['tlb_stats']['total_hits']}\n"
                    f"TLB Misses: {results['tlb_stats']['total_misses']}\n"
                    f"Page Faults: {results['total_faults']}"
                )
                dialog = CustomMessageBox(self.ui.app, "Results", message, ["OK"])
                dialog.get()
            except json.JSONDecodeError:
                dialog = CustomMessageBox(self.ui.app, "Error", "Invalid simulation results.", ["OK"])
                dialog.get()
        except socket.error as e:
            dialog = CustomMessageBox(self.ui.app, "Error", f"Failed to communicate with simulator: {str(e)}", ["OK"])
            dialog.get()

    def save_to_json(self):
        settings = {
            "ram_size": self.ui.ram_size_var.get(),
            "rom_size": self.ui.rom_size_var.get(),
            "swap_size": float(self.ui.swap_percent_var.get()),
            "page_size": self.ui.page_size_var.get(),
            "tlb_enabled": self.ui.tlb_enabled_var.get(),
            "tlb_size": self.ui.tlb_size_var.get(),
            "virtual_address_size": self.ui.va_size_var.get(),
            "allocation_type": self.ui.memory_allocation_var.get(),
        }
        if self.env_file_path:
            try:
                with open(self.env_file_path, "w") as f:
                    json.dump(settings, f, indent=4)
            except Exception as e:
                dialog = CustomMessageBox(self.ui.app, "Error", f"Failed to save environment settings: {e}", ["OK"])
                dialog.get()

        if self.proc_file_path and isinstance(self.proc_file_path, (str, bytes, os.PathLike)):
            try:
                with open(self.proc_file_path, "w") as f:
                    json.dump(self.process_data, f, indent=4)
            except Exception as e:
                dialog = CustomMessageBox(self.ui.app, "Error", f"Failed to save process data: {e}", ["OK"])
                dialog.get()

    def load_processes_from_json(self):
        if self.proc_file_path and isinstance(self.proc_file_path, (str, bytes, os.PathLike)) and os.path.exists(self.proc_file_path):
            try:
                with open(self.proc_file_path, "r") as f:
                    self.process_data = json.load(f)
                for proc in self.process_data:
                    process_info = f"ID: {proc['id']}, Name: {proc['name']}, Size: {proc['size_gb']}GB, Type: {proc['type']}, Has Priority: {proc['has_priority']}, VA: {proc['virtual_address']}"
                    self.ui.add_process_to_list(process_info, proc['id'], proc["is_process_stop"])
                if self.process_data:
                    self.next_process_id = max(self.next_process_id, max(int(proc['id']) for proc in self.process_data) + 1)
                    self.ui.confirm_process_button.configure(state="normal")
            except Exception as e:
                dialog = CustomMessageBox(self.ui.app, "Error", f"Failed to load process data: {e}", ["OK"])
                dialog.get()

    def disable_process_add_section(self):
        self.ui.disable_process_add_section()

    def enable_process_add_section(self):
        self.ui.enable_process_add_section()

    def set_configuration(self):
        settings = {
            "ram_size": self.ui.ram_size_var.get(),
            "page_size": self.ui.page_size_var.get(),
            "tlb_size": self.ui.tlb_size_var.get(),
            "tlb_enabled": self.ui.tlb_enabled_var.get(),
            "virtual_address_size": self.ui.va_size_var.get(),
            "rom_size": self.ui.rom_size_var.get(),
            "swap_size": float(self.ui.swap_percent_var.get()),
            "allocation_type": self.ui.memory_allocation_var.get(),
        }

        if self.ui.config_button.cget("text") == "Set Configuration":
            message = (
                f"Please confirm the environment settings:\n\n"
                f"RAM Size: {settings['ram_size']} GB\n"
                f"Page Size: {settings['page_size']}\n"
                f"TLB Size: {settings['tlb_size']}\n"
                f"TLB Enabled: {settings['tlb_enabled']}\n"
                f"Virtual Address Size: {settings['virtual_address_size']}\n"
                f"ROM Size: {settings['rom_size']}\n"
                f"Swap Size: {settings['swap_size']:.0f}%\n"
                f"Allocation Type: {settings['allocation_type']}\n\n"
                f"Click OK to confirm."
            )
            dialog = CustomMessageBox(self.ui.app, "Confirm Environment Settings", message, ["OK", "Cancel"])
            if dialog.get() == "OK":
                self.save_to_json()
                self.enable_process_add_section()
                self.ui.config_button.configure(text="Update Configuration")
                self.send_to_cpp(force_new=True)
        else:
            message = (
                f"Environment Settings Update:\n\n"
                f"New Settings:\n"
                f"RAM Size: {settings['ram_size']} GB\n"
                f"Page Size: {settings['page_size']}\n"
                f"TLB Size: {settings['tlb_size']}\n"
                f"TLB Enabled: {settings['tlb_enabled']}\n"
                f"Virtual Address Size: {settings['virtual_address_size']}\n"
                f"ROM Size: {settings['rom_size']}\n"
                f"Swap Size: {settings['swap_size']:.0f}%\n"
                f"Allocation Type: {settings['allocation_type']}\n\n"
                f"Click OK to update."
            )
            dialog = CustomMessageBox(self.ui.app, "Update Environment Settings", message, ["OK", "Cancel"])
            if dialog.get() == "OK":
                self.save_to_json()
                dialog = CustomMessageBox(self.ui.app, "Success", "Environment settings updated.", ["OK"])
                dialog.get()
                self.send_to_cpp(force_new=True)

    def toggle_system_dropdown(self, value):
        self.ui.toggle_system_dropdown(value)

    def update_options(self, event):
        ram_size_gb = int(self.ui.ram_size_var.get())
        ram_bytes = ram_size_gb * 1024 * 1048576
        page_sizes = [2**i for i in range(12, 22) if 2**i <= ram_bytes // 1024]
        page_options = [f"{size//1024}KB" for size in page_sizes]
        self.ui.page_size_menu.configure(values=page_options)
        self.ui.page_size_menu.configure(state="normal" if page_options else "disabled")
        self.ui.page_size_var.set(page_options[0] if page_options else "")

        if ram_size_gb <= 16:
            tlb_options = ["16"]
        elif ram_size_gb <= 32:
            tlb_options = ["16", "32"]
        else:
            tlb_options = ["16", "32", "64"]
        self.ui.tlb_size_menu.configure(values=tlb_options)
        self.ui.tlb_size_menu.configure(state="normal" if tlb_options else "disabled")
        self.ui.tlb_size_var.set(tlb_options[0] if tlb_options else "")

        va_size_options = ["16-bit", "32-bit", "64-bit"]

        self.ui.va_size_menu.configure(values=va_size_options)
        self.ui.va_size_menu.configure(state="normal" if va_size_options else "disabled")
        self.ui.va_size_var.set(va_size_options[0] if va_size_options else "")

    def generate_virtual_address(self):
        va_size = self.ui.va_size_var.get()
        if va_size == "16-bit":
            bits = 16
        elif va_size == "32-bit":
            bits = 32
        else:
            bits = 64
        max_va = (1 << bits) - 1
        ram_size_bytes = int(self.ui.ram_size_var.get()) * 1024 * 1048576
        virtual_address = random.randint(0, min(max_va, ram_size_bytes - 1))
        if bits == 16:
            return f"0x{virtual_address:04x}"
        elif bits == 32:
            return f"0x{virtual_address:08x}"
        else:
            return f"0x{virtual_address:016x}"

    def save_process(self):
        process_name = self.ui.process_name_entry.get()
        process_size = self.ui.process_size_entry.get()
        process_type = self.ui.process_type_var.get()
        system_process = self.ui.system_process_var.get() if process_type == "System" else None
        has_priority = self.ui.set_priority_var.get()

        if process_name in ["", "e.g., Process1"] or process_size in ["", "e.g., 1"]:
            CustomMessageBox(self.ui.app, "Error", "All required fields must be filled!", ["OK"])
            return

        process_id = str(self.next_process_id)
        self.next_process_id += 1
        virtual_address = self.generate_virtual_address()

        display_name = system_process if process_type == "System" else process_name
        process_info = f"ID: {process_id}, Name: {display_name}, Size: {process_size}GB, Type: {process_type}, Has Priority: {has_priority}, VA: {virtual_address}"

        process_entry = {
            "id": process_id,
            "name": display_name,
            "size_gb": int(process_size),
            "type": process_type,
            "has_priority": has_priority,
            "is_process_stop": False,
            "virtual_address": virtual_address
        }

        self.process_data.append(process_entry)
        self.ui.add_process_to_list(process_info, process_id, False)
        self.save_to_json()

        self.ui.process_name_entry.delete(0, "end")
        self.ui.process_name_entry.insert(0, "e.g., Process1")
        self.ui.process_size_entry.delete(0, "end")
        self.ui.process_size_entry.insert(0, "e.g., 1")

    def find_process_index(self, process_id):
        for idx, proc in enumerate(self.process_data):
            if proc["id"] == process_id:
                return idx
        return -1

    def update_process_ui(self, process_id):
        idx = self.find_process_index(process_id)
        if idx == -1:
            self.reorder_process_list()
            return

        found = False
        for frame, pid in self.ui.process_list:
            if pid == process_id:
                proc = self.process_data[idx]
                is_stopped = proc["is_process_stop"]
                frame.button.configure(
                    text="Resume" if is_stopped else "Stop",
                    fg_color="#66CC66" if is_stopped else "#0e19e6",
                    command=lambda pid=process_id: self.resume_process(frame, pid) if is_stopped else self.stop_process(frame, pid)
                )
                found = True
                break
        if not found:
            self.reorder_process_list()

    def reorder_process_list(self):
        priority_running = sorted(
            [proc for proc in self.process_data if proc["has_priority"] and not proc["is_process_stop"]],
            key=lambda x: x["id"]
        )
        non_priority_running = sorted(
            [proc for proc in self.process_data if not proc["has_priority"] and not proc["is_process_stop"]],
            key=lambda x: x["id"]
        )
        stopped = sorted(
            [proc for proc in self.process_data if proc["is_process_stop"]],
            key=lambda x: x["id"]
        )

        ordered_data = priority_running + non_priority_running + stopped
        self.process_data = ordered_data

        for frame, _ in self.ui.process_list:
            frame.destroy()
        self.ui.process_list.clear()

        if self.ui.no_processes_label.winfo_exists():
            self.ui.no_processes_label.destroy()

        if not self.process_data:
            self.ui.no_processes_label = ctk.CTkLabel(self.ui.process_container, text="No active processes", font=("Arial", 12, "italic"))
            self.ui.no_processes_label.pack(pady=20)
            return

        for proc in self.process_data:
            process_info = f"ID: {proc['id']}, Name: {proc['name']}, Size: {proc['size_gb']}GB, Type: {proc['type']}, Has Priority: {proc['has_priority']}, VA: {proc['virtual_address']}"
            self.ui.add_process_to_list(process_info, proc['id'], proc["is_process_stop"])

        self.save_to_json()

    def remove_process(self, process_frame, process_id):
        idx = self.find_process_index(process_id)
        if idx == -1:
            CustomMessageBox(self.ui.app, "Error", f"Process with ID {process_id} not found.", ["OK"])
            return

        proc = self.process_data[idx]
        dialog = CustomMessageBox(self.ui.app, "Confirm Removal", f"Are you sure you want to remove process {proc['name']} (ID: {proc['id']})?", ["OK", "Cancel"])
        if dialog.get() == "OK":
            self.process_data.pop(idx)
            self.ui.remove_process(process_frame, process_id)
            self.reorder_process_list()
            if self.process_data:
                self.send_to_cpp()

    def stop_process(self, process_frame, process_id):
        idx = self.find_process_index(process_id)
        if idx == -1:
            CustomMessageBox(self.ui.app, "Error", f"Process with ID {process_id} not found.", ["OK"])
            return

        self.process_data[idx]["is_process_stop"] = True
        self.update_process_ui(process_id)
        self.reorder_process_list()
        self.send_to_cpp()

    def resume_process(self, process_frame, process_id):
        idx = self.find_process_index(process_id)
        if idx == -1:
            CustomMessageBox(self.ui.app, "Error", f"Process with ID {process_id} not found.", ["OK"])
            return

        self.process_data[idx]["is_process_stop"] = False
        self.update_process_ui(process_id)
        self.reorder_process_list()
        self.send_to_cpp()

    def confirm_processes(self):
        if not self.process_data:
            dialog = CustomMessageBox(self.ui.app, "Error", "No processes to simulate.", ["OK"])
            dialog.get()
            return
        self.send_to_cpp()
        dialog = CustomMessageBox(self.ui.app, "Success", "Simulation has been triggered.", ["OK"])
        dialog.get()