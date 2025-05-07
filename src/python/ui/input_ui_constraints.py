import customtkinter as ctk
import json
import os
import time
import hashlib
import subprocess

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
    def __init__(self, ui, env_file_path=None, proc_file_path=None):
        self.ui = ui
        self.process_data = []
        self.next_process_id = 1001
        self.has_run_simulation = False  # Track if the simulation has run at least once
        self.bin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), r"..\..\..\bin"))
        self.env_file_path = env_file_path if env_file_path is not None else os.path.join(self.bin_dir, "environment_settings.json")
        self.proc_file_path = proc_file_path if proc_file_path is not None else os.path.join(self.bin_dir, "processes.json")
        self.result_path = os.path.join(self.bin_dir, "result.json")
        self.simulator_path = os.path.join(self.bin_dir, "virtual_memory_simulator.exe")

        try:
            os.makedirs(self.bin_dir, exist_ok=True)
        except Exception as e:
            CustomMessageBox(self.ui.app, "Error", f"Failed to create bin directory at {self.bin_dir}: {str(e)}", ["OK"])
            raise

    def on_closing(self):
        if os.path.exists(self.proc_file_path):
            try:
                os.remove(self.proc_file_path)
            except Exception as e:
                CustomMessageBox(self.ui.app, "Error", f"Failed to remove file {self.proc_file_path}: {str(e)}", ["OK"])
        if os.path.exists(self.env_file_path):
            try:
                os.remove(self.env_file_path)
            except Exception as e:
                CustomMessageBox(self.ui.app, "Error", f"Failed to remove file {self.env_file_path}: {str(e)}", ["OK"])
        if os.path.exists(self.result_path):
            try:
                os.remove(self.result_path)
            except Exception as e:
                CustomMessageBox(self.ui.app, "Error", f"Failed to remove file {self.result_path}: {str(e)}", ["OK"])
        self.ui.app.destroy()

    def send_jsons_to_cpp(self, force_run=False):
        settings = {
            "ram_size_gb": self.ui.ram_size_var.get(),
            "page_size_kb": self.ui.page_size_var.get().replace("KB", "") if self.ui.page_size_var.get() else "0",
            "tlb_size": self.ui.tlb_size_var.get() if self.ui.tlb_size_var.get() else "0",
            "tlb_enabled": self.ui.tlb_enabled_var.get(),
            "virtual_address_size": self.ui.va_size_var.get(),
            "rom_size": self.ui.rom_size_var.get()
        }

        try:
            with open(self.env_file_path, "w") as f:
                json.dump(settings, f, indent=4)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            CustomMessageBox(self.ui.app, "Error", f"Failed to write environment settings to {self.env_file_path}: {str(e)}", ["OK"])
            return

        if not os.path.exists(self.proc_file_path):
            try:
                with open(self.proc_file_path, "w") as f:
                    json.dump([], f, indent=4)
            except Exception as e:
                CustomMessageBox(self.ui.app, "Error", f"Failed to create processes.json: {str(e)}", ["OK"])
                return

        # Check if both JSON files are non-empty before running the simulation (first time)
        env_non_empty = os.path.exists(self.env_file_path) and os.path.getsize(self.env_file_path) > 0
        proc_non_empty = os.path.exists(self.proc_file_path) and os.path.getsize(self.proc_file_path) > 0
        try:
            with open(self.proc_file_path, "r") as f:
                processes = json.load(f)
            proc_non_empty = proc_non_empty and len(processes) > 0
        except Exception:
            proc_non_empty = False

        should_run = False
        if force_run:  # Used by confirm_processes to always run the simulation
            should_run = True
        elif not self.has_run_simulation:
            # First run: only execute if both JSONs are non-empty
            should_run = env_non_empty and proc_non_empty
        else:
            # Subsequent runs: execute on any update to either JSON
            should_run = True

        if not should_run:
            return

        try:
            if not os.path.exists(self.simulator_path):
                CustomMessageBox(self.ui.app, "Error", f"Virtual Memory Simulator executable not found at {self.simulator_path}", ["OK"])
                return

            cmd = [self.simulator_path, self.env_file_path, self.proc_file_path]
            subprocess.run(cmd, capture_output=True, text=True)
            self.has_run_simulation = True
        except Exception as e:
            CustomMessageBox(self.ui.app, "Error", f"Failed to run simulation: {str(e)}", ["OK"])
            return

    def disable_process_add_section(self):
        self.ui.disable_process_add_section()

    def enable_process_add_section(self):
        self.ui.enable_process_add_section()

    def set_configuration(self):
        settings = {
            "ram_size_gb": self.ui.ram_size_var.get(),
            "page_size_kb": self.ui.page_size_var.get().replace("KB", "") if self.ui.page_size_var.get() else "0",
            "tlb_size": self.ui.tlb_size_var.get() if self.ui.tlb_size_var.get() else "0",
            "tlb_enabled": self.ui.tlb_enabled_var.get(),
            "virtual_address_size": self.ui.va_size_var.get(),
            "rom_size": self.ui.rom_size_var.get()
        }

        if self.ui.config_button.cget("text") == "Set Configuration":
            message = (
                "Please confirm the environment settings:\n\n"
                f"RAM Size: {settings['ram_size_gb']} GB\n"
                f"Page Size: {settings['page_size_kb']} KB\n"
                f"TLB Size: {settings['tlb_size']}\n"
                f"TLB Enabled: {settings['tlb_enabled']}\n"
                f"Virtual Address Size: {settings['virtual_address_size']}\n"
                f"ROM Size: {settings['rom_size']}\n\n"
                "Click OK to confirm."
            )
            dialog = CustomMessageBox(self.ui.app, "Confirm Environment Settings", message, ["OK", "Cancel"])
            if dialog.get() == "OK":
                try:
                    with open(self.env_file_path, "w") as f:
                        json.dump(settings, f, indent=4)
                except Exception as e:
                    CustomMessageBox(self.ui.app, "Error", f"Failed to write environment settings to {self.env_file_path}: {str(e)}", ["OK"])
                    return
                self.enable_process_add_section()
                self.ui.config_button.configure(text="Update Configuration")
                self.send_jsons_to_cpp()
        else:
            try:
                with open(self.env_file_path, "r") as f:
                    prev_settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                CustomMessageBox(self.ui.app, "Error", "Could not load previous settings. Please set the configuration again.", ["OK"])
                self.ui.config_button.configure(text="Set Configuration")
                self.disable_process_add_section()
                return

            settings_unchanged = (
                settings["ram_size_gb"] == prev_settings["ram_size_gb"] and
                settings["page_size_kb"] == prev_settings["page_size_kb"] and
                settings["tlb_size"] == prev_settings["tlb_size"] and
                settings["tlb_enabled"] == prev_settings["tlb_enabled"] and
                settings["virtual_address_size"] == prev_settings["virtual_address_size"] and
                settings["rom_size"] == prev_settings["rom_size"]
            )

            if settings_unchanged:
                return

            message = (
                "Environment Settings Update:\n\n"
                "Previous Settings:\n"
                f"RAM Size: {prev_settings['ram_size_gb']} GB\n"
                f"Page Size: {prev_settings['page_size_kb']} KB\n"
                f"TLB Size: {prev_settings['tlb_size']}\n"
                f"TLB Enabled: {prev_settings['tlb_enabled']}\n"
                f"Virtual Address Size: {prev_settings['virtual_address_size']}\n"
                f"ROM Size: {prev_settings['rom_size']}\n\n"
                "New Settings:\n"
                f"RAM Size: {settings['ram_size_gb']} GB\n"
                f"Page Size: {settings['page_size_kb']} KB\n"
                f"TLB Size: {settings['tlb_size']}\n"
                f"TLB Enabled: {settings['tlb_enabled']}\n"
                f"Virtual Address Size: {settings['virtual_address_size']}\n"
                f"ROM Size: {settings['rom_size']}\n\n"
                "Click OK to update."
            )

            prev_bits = self.get_bits(prev_settings["virtual_address_size"])
            new_bits = self.get_bits(settings["virtual_address_size"])
            if prev_bits != new_bits and self.process_data:
                if new_bits > prev_bits:
                    for proc in self.process_data:
                        addr_int = int(proc["virtual_address"], 16)
                        proc["virtual_address"] = self.format_virtual_address(addr_int, new_bits)
                    self.reorder_process_list()
                    self.save_processes_to_json()
                else:
                    processes_to_delete = []
                    indices_to_delete = []
                    for idx, proc in enumerate(self.process_data):
                        addr_int = int(proc["virtual_address"], 16)
                        if self.has_non_zero_msb(addr_int, prev_bits, new_bits):
                            processes_to_delete.append(proc)
                            indices_to_delete.append(idx)

                    if processes_to_delete:
                        delete_message = (
                            "The following processes cannot be reduced and will be deleted:\n\n"
                        )
                        for proc in processes_to_delete:
                            delete_message += (
                                f"ID: {proc['id']}, Name: {proc['name']}, Virtual Address: {proc['virtual_address']}\n"
                            )
                        delete_message += "\nClick OK to proceed."
                        dialog = CustomMessageBox(self.ui.app, "Virtual Address Size Reduction", delete_message, ["OK", "Cancel"])
                        if dialog.get() != "OK":
                            self.ui.va_size_var.set(prev_settings["virtual_address_size"])
                            return

                        indices_to_delete.sort(reverse=True)
                        for idx in indices_to_delete:
                            self.process_data.pop(idx)

                        for frame, _ in self.ui.process_list:
                            frame.destroy()
                        self.ui.process_list.clear()

                        if not self.process_data:
                            if self.ui.no_processes_label.winfo_exists():
                                self.ui.no_processes_label.destroy()
                            self.ui.no_processes_label = ctk.CTkLabel(self.ui.process_container, text="No active processes", font=("Arial", 12, "italic"))
                            self.ui.no_processes_label.pack(pady=20)
                        else:
                            for idx, proc in enumerate(self.process_data):
                                process_info = f"ID: {proc['id']}, Name: {proc['name']}, Size: {proc['size_gb']}GB, Type: {proc['type']}, Has Priority: {proc['has_priority']}, VA: {proc['virtual_address']}"
                                self.ui.add_process_to_list(process_info, idx, proc["is_process_stop"])

                    for proc in self.process_data:
                        addr_int = int(proc["virtual_address"], 16)
                        proc["virtual_address"] = self.format_virtual_address(addr_int, new_bits)
                    self.reorder_process_list()
                    self.save_processes_to_json()
                    self.send_jsons_to_cpp()

            dialog = CustomMessageBox(self.ui.app, "Update Environment Settings", message, ["OK", "Cancel"])
            if dialog.get() == "OK":
                try:
                    with open(self.env_file_path, "w") as f:
                        json.dump(settings, f, indent=4)
                    dialog = CustomMessageBox(self.ui.app, "Success", "Environment settings updated successfully!", ["OK"])
                    dialog.get()
                except Exception as e:
                    CustomMessageBox(self.ui.app, "Error", f"Failed to update settings: {str(e)}", ["OK"])
                    return
                self.send_jsons_to_cpp()

    def get_bits(self, va_size):
        if va_size == "16-bit":
            return 16
        elif va_size == "32-bit":
            return 32
        else:
            return 64

    def has_non_zero_msb(self, addr_int, prev_bits, new_bits):
        mask = (1 << prev_bits) - 1
        truncated_bits = (1 << prev_bits) - (1 << new_bits)
        return (addr_int & truncated_bits) != 0

    def format_virtual_address(self, addr_int, bits):
        if bits == 16:
            return f"0x{addr_int:04x}"
        elif bits == 32:
            return f"0x{addr_int:08x}"
        else:
            return f"0x{addr_int:016x}"

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

        va_size_options = []
        if ram_size_gb < 16:
            va_size_options = ["16-bit"]
        elif ram_size_gb < 32:
            va_size_options = ["16-bit", "32-bit"]
        else:
            va_size_options = ["16-bit", "32-bit", "64-bit"]
        self.ui.va_size_menu.configure(values=va_size_options)
        self.ui.va_size_menu.configure(state="normal" if va_size_options else "disabled")
        self.ui.va_size_var.set(va_size_options[0] if va_size_options else "")

    def load_processes_from_json(self):
        if os.path.exists(self.proc_file_path):
            try:
                with open(self.proc_file_path, "r") as f:
                    self.process_data = json.load(f)
                    for idx, proc in enumerate(self.process_data):
                        process_info = f"ID: {proc['id']}, Name: {proc['name']}, Size: {proc['size_gb']}GB, Type: {proc['type']}, Has Priority: {proc['has_priority']}, VA: {proc['virtual_address']}"
                        self.ui.add_process_to_list(process_info, idx, proc.get("is_process_stop", False))
                    if self.process_data:
                        self.next_process_id = max(self.next_process_id, max(int(proc['id']) for proc in self.process_data) + 1)
            except Exception as e:
                CustomMessageBox(self.ui.app, "Error", f"Failed to load processes from {self.proc_file_path}: {str(e)}", ["OK"])
        else:
            try:
                with open(self.proc_file_path, "w") as f:
                    json.dump([], f, indent=4)
            except Exception as e:
                CustomMessageBox(self.ui.app, "Error", f"Failed to create processes.json: {str(e)}", ["OK"])
        self.reorder_process_list()

    def save_processes_to_json(self):
        try:
            with open(self.proc_file_path, "w") as f:
                json.dump(self.process_data, f, indent=4)
        except Exception as e:
            CustomMessageBox(self.ui.app, "Error", f"Failed to save processes to {self.proc_file_path}: {str(e)}", ["OK"])
        self.send_jsons_to_cpp()

    def confirm_processes(self):
        self.send_jsons_to_cpp(force_run=True)
        dialog = CustomMessageBox(
            self.ui.app,
            "Success",
            "Simulation has been triggered.",
            ["OK"]
        )
        dialog.get()

    def generate_virtual_address(self, timestamp):
        hash_obj = hashlib.sha256(str(timestamp).encode())
        hash_value = int(hash_obj.hexdigest(), 16)

        va_size = self.ui.va_size_var.get()
        if va_size == "16-bit":
            max_va = (1 << 16) - 1
            bits = 16
        elif va_size == "32-bit":
            max_va = (1 << 32) - 1
            bits = 32
        else:
            max_va = (1 << 64) - 1
            bits = 64

        virtual_address = hash_value & max_va
        ram_size_bytes = int(self.ui.ram_size_var.get()) * 1024 * 1048576
        max_physical_address = ram_size_bytes - 1
        virtual_address = virtual_address % (max_physical_address + 1)

        try:
            with open(self.proc_file_path, "r") as f:
                processes = json.load(f)
        except Exception:
            processes = []

        existing_addresses = {int(proc["virtual_address"], 16) for proc in processes}
        attempt = 0
        original_hash = virtual_address
        while virtual_address in existing_addresses and attempt < 1000:
            attempt += 1
            hash_obj = hashlib.sha256((str(timestamp) + str(attempt)).encode())
            virtual_address = int(hash_obj.hexdigest(), 16) & max_va
            virtual_address = virtual_address % (max_physical_address + 1)

        if attempt >= 1000:
            virtual_address = (original_hash + len(existing_addresses) + 1) & max_va
            virtual_address = virtual_address % (max_physical_address + 1)

        return self.format_virtual_address(virtual_address, bits)

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
        timestamp = time.time()
        virtual_address = self.generate_virtual_address(timestamp)

        display_name = system_process if process_type == "System" else process_name
        process_info = f"ID: {process_id}, Name: {display_name}, Size: {process_size}GB, Type: {process_type}, Has Priority: {has_priority}, VA: {virtual_address}"

        process_entry = {
            "id": process_id,
            "name": display_name,
            "size_gb": int(process_size),
            "type": process_type,
            "has_priority": has_priority,
            "virtual_address": virtual_address,
            "is_process_stop": False,
            "timestamp": timestamp
        }

        try:
            with open(self.proc_file_path, "r") as f:
                self.process_data = json.load(f)
        except Exception:
            self.process_data = []

        self.process_data.append(process_entry)
        self.save_processes_to_json()

        self.ui.add_process_to_list(process_info, len(self.process_data) - 1, False)
        self.reorder_process_list()

        self.ui.process_name_entry.delete(0, "end")
        self.ui.process_name_entry.insert(0, "e.g., Process1")
        self.ui.process_size_entry.delete(0, "end")
        self.ui.process_size_entry.insert(0, "e.g., 1")

    def find_process_index(self, process_id):
        try:
            with open(self.proc_file_path, "r") as f:
                processes = json.load(f)
        except Exception:
            return -1

        for idx, proc in enumerate(processes):
            proc_id = str(proc["id"])
            if proc_id == process_id:
                return idx
        return -1

    def update_process_ui(self, process_id):
        idx = self.find_process_index(process_id)
        if idx == -1:
            self.reorder_process_list()
            return

        try:
            with open(self.proc_file_path, "r") as f:
                processes = json.load(f)
        except Exception:
            return

        found = False
        for frame, pid in self.ui.process_list:
            if pid == process_id:
                proc = processes[idx]
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
        try:
            with open(self.proc_file_path, "r") as f:
                self.process_data = json.load(f)
        except Exception:
            self.process_data = []

        process_states = {proc["id"]: proc["is_process_stop"] for proc in self.process_data}

        priority_running = sorted(
            [proc for proc in self.process_data if proc["has_priority"] and not proc["is_process_stop"]],
            key=lambda x: x["timestamp"]
        )
        non_priority_running = sorted(
            [proc for proc in self.process_data if not proc["has_priority"] and not proc["is_process_stop"]],
            key=lambda x: x["timestamp"]
        )
        stopped = sorted(
            [proc for proc in self.process_data if proc["is_process_stop"]],
            key=lambda x: x["timestamp"]
        )

        ordered_data = priority_running + non_priority_running + stopped

        self.process_data = ordered_data
        self.save_processes_to_json()

        for frame, _ in self.ui.process_list:
            frame.destroy()
        self.ui.process_list.clear()

        if self.ui.no_processes_label.winfo_exists():
            self.ui.no_processes_label.destroy()

        if not self.process_data:
            self.ui.no_processes_label = ctk.CTkLabel(self.ui.process_container, text="No active processes", font=("Arial", 12, "italic"))
            self.ui.no_processes_label.pack(pady=20)
            return

        for idx, proc in enumerate(self.process_data):
            process_info = f"ID: {proc['id']}, Name: {proc['name']}, Size: {proc['size_gb']}GB, Type: {proc['type']}, Has Priority: {proc['has_priority']}, VA: {proc['virtual_address']}"
            self.ui.add_process_to_list(process_info, idx, proc["is_process_stop"])

    def remove_process(self, process_frame, process_id):
        idx = self.find_process_index(process_id)
        if idx == -1:
            CustomMessageBox(self.ui.app, "Error", f"Process with ID {process_id} not found.", ["OK"])
            return

        try:
            with open(self.proc_file_path, "r") as f:
                self.process_data = json.load(f)
        except Exception:
            return

        proc = self.process_data[idx]
        dialog = CustomMessageBox(self.ui.app, "Confirm Removal", f"Are you sure you want to remove process {proc['name']} (ID: {proc['id']})?", ["OK", "Cancel"])
        if dialog.get() == "OK":
            self.process_data.pop(idx)
            self.save_processes_to_json()
            self.ui.remove_process(process_frame, process_id)
            self.reorder_process_list()

    def stop_process(self, process_frame, process_id):
        idx = self.find_process_index(process_id)
        if idx == -1:
            CustomMessageBox(self.ui.app, "Error", f"Process with ID {process_id} not found.", ["OK"])
            return

        try:
            with open(self.proc_file_path, "r") as f:
                self.process_data = json.load(f)
        except Exception:
            return

        self.process_data[idx]["is_process_stop"] = True
        self.save_processes_to_json()
        self.update_process_ui(process_id)
        self.reorder_process_list()

    def resume_process(self, process_frame, process_id):
        idx = self.find_process_index(process_id)
        if idx == -1:
            CustomMessageBox(self.ui.app, "Error", f"Process with ID {process_id} not found.", ["OK"])
            return

        try:
            with open(self.proc_file_path, "r") as f:
                self.process_data = json.load(f)
        except Exception:
            return

        self.process_data[idx]["is_process_stop"] = False
        self.save_processes_to_json()
        self.update_process_ui(process_id)
        self.reorder_process_list()