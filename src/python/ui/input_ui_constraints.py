import os
import json
import time
import random
import subprocess
from tkinter import messagebox
import customtkinter as ctk

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

    def on_button_click(self, option):
        self.result = option
        self.destroy()

    def get(self):
        self.wait_window()
        return self.result

class LogicHandler:
    def __init__(self, ui, env_file_path=None, proc_file_path=None, simulator_path=None, simulator_process=None):
        self.ui = ui
        self.env_file_path = env_file_path or os.path.join("bin", "environment.json")
        self.proc_file_path = proc_file_path or os.path.join("bin", "processes.json")
        self.process_data = []
        self.next_process_id = 1001
        self.simulator_path = simulator_path or os.path.join("bin", "virtual_memory_simulator.exe")
        self.simulator_process = simulator_process
        
        # Create bin directory if it doesn't exist
        os.makedirs("bin", exist_ok=True)
        
        # Initialize fresh settings
        self.initialize_fresh_settings()

    def initialize_fresh_settings(self):
        """Initialize fresh settings and empty process list"""
        default_settings = {
            "ram_size_gb": 1,
            "page_size_kb": 4,
            "tlb_size": 16,
            "tlb_enabled": False,
            "virtual_address_size": "16-bit",
            "rom_size": "32 GB",
            "swap_percent": 0,
            "allocation_type": "Contiguous"
        }
        
        # Always write fresh default settings
        with open(self.env_file_path, 'w') as f:
            json.dump(default_settings, f, indent=4)
                
        # Always start with empty process list
        with open(self.proc_file_path, 'w') as f:
            json.dump([], f)

    def start_simulator(self, force_new=False):
        if force_new and self.simulator_process:
            self.simulator_process.terminate()
            self.simulator_process = None
        if not self.simulator_process or self.simulator_process.poll() is not None:
            if not os.path.exists(self.simulator_path):
                messagebox.showerror("Error", "Simulator executable not found")
                return False
                
            try:
                self.simulator_process = subprocess.Popen([self.simulator_path])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start simulator: {str(e)}")
                return False
        
        return True

    def on_closing(self):
        if self.simulator_process:
            self.simulator_process.terminate()
            self.simulator_process = None
        self.ui.app.destroy()

    def save_to_json(self):
        try:
            # Convert string values to proper numerical types before saving
            ram_size = max(1, int(self.ui.ram_size_var.get()))
            page_size = int(self.ui.page_size_var.get().replace("KB", "").strip())
            tlb_size = int(self.ui.tlb_size_var.get())
            swap_percent = float(self.ui.swap_percent_var.get() or "10")
            
            # Ensure all values are valid before saving
            settings = {
                "ram_size_gb": ram_size,
                "page_size_kb": page_size,
                "tlb_size": tlb_size,
                "tlb_enabled": bool(self.ui.tlb_enabled_var.get()),
                "virtual_address_size": str(self.ui.va_size_var.get() or "32-bit"),
                "rom_size": str(self.ui.rom_size_var.get() or "1GB"),
                "swap_percent": swap_percent,
                "allocation_type": str(self.ui.memory_allocation_var.get() or "First Fit")
            }
            
            # Save environment settings
            with open(self.env_file_path, 'w') as f:
                json.dump(settings, f, indent=4)

            # Save process data
            with open(self.proc_file_path, 'w') as f:
                json.dump(self.process_data, f, indent=4)
                
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            return False    
        
    def load_processes_from_json(self):
        if self.proc_file_path and os.path.exists(self.proc_file_path):
            try:
                with open(self.proc_file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.process_data = data
                        for process in self.process_data:
                            process_info = f"ID: {process['id']}, Name: {process['name']}, Size: {process['size_gb']}GB, Type: {process['type']}, VA: {process['virtual_address']}"
                            self.ui.add_process_to_list(process_info, process['id'], process['is_process_stop'])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load process data: {str(e)}")
                
    def send_to_cpp(self, force_new=False):
        # Make sure to save settings first
        if not self.save_to_json():
            return False
        
        # Start the simulator only after settings are confirmed
        if not self.start_simulator(force_new):
            return False

        try:
            print("Starting simulation...")
            
            # Wait for simulator to complete with a timeout
            if self.simulator_process:
                max_wait = 80  # Maximum wait time in seconds
                start_time = time.time()
                while time.time() - start_time < max_wait:
                    if self.simulator_process.poll() is not None:
                        break
                    time.sleep(0.5)
                else:
                    print("Simulator is taking too long, checking for results anyway")

            # Check for results
            results_path = os.path.join("bin", "simulation_results.json")
            attempt = 0
            max_attempts = 5
            while attempt < max_attempts:
                if os.path.exists(results_path):
                    try:
                        with open(results_path, 'r') as f:
                            results = json.load(f)
                            dialog = CustomMessageBox(self.ui.app, "Success", "Simulation completed successfully.", ["OK"])
                            dialog.get()
                            # Display the results in the UI
                            self.display_results(results_path)
                            return True
                    except json.JSONDecodeError:
                        print(f"Invalid JSON in results file (attempt {attempt + 1})")
                        time.sleep(1)
                else:
                    print(f"Results file not found (attempt {attempt + 1})")
                    time.sleep(1)
                attempt += 1
            
            messagebox.showerror("Error", "Simulator did not generate valid results after multiple attempts")
            return False

        except Exception as e:
            print(f"Simulation error: {str(e)}")
            messagebox.showerror("Error", f"Failed to process simulation: {str(e)}")
            return False

    def set_configuration(self):
        settings = {
            "ram_size": self.ui.ram_size_var.get(),
            "page_size": self.ui.page_size_var.get(),
            "tlb_size": self.ui.tlb_size_var.get(),
            "tlb_enabled": self.ui.tlb_enabled_var.get(),
            "virtual_address_size": self.ui.va_size_var.get(),
            "rom_size": self.ui.rom_size_var.get(),
            "swap_size": float(self.ui.swap_percent_var.get() or "10"),
            "allocation_type": self.ui.memory_allocation_var.get(),
        }

        message = (
            f"Environment Settings:\n\n"
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
            if self.save_to_json():
                self.enable_process_add_section()
                self.ui.config_button.configure(text="Update Configuration")
                dialog = CustomMessageBox(self.ui.app, "Success", "Environment settings saved.", ["OK"])
                dialog.get()

    def confirm_processes(self):
        if not self.process_data:
            messagebox.showerror("Error", "No processes added yet")
            return
        
        # First, save the configuration
        if not self.save_to_json():
            messagebox.showerror("Error", "Failed to save configuration")
            return
        
        # Create a ready flag file to tell the simulator to start
        ready_flag_path = os.path.join("bin", "ready.flag")
        try:
            with open(ready_flag_path, 'w') as f:
                f.write("ready")
        except Exception as e:
            print(f"Failed to create ready flag: {str(e)}")
            
        # Then start the simulator
        if not self.start_simulator(force_new=True):
            messagebox.showerror("Error", "Failed to start simulator")
            return
            
        dialog = CustomMessageBox(self.ui.app, "Simulation Started", 
                                "Simulation has been started. Please wait for results...", ["OK"])
        dialog.get()
        
        # Wait for the simulator to generate results
        try:
            print("Starting simulation...")
            
            # Wait for simulator to complete with a timeout
            if self.simulator_process:
                max_wait = 80  # Maximum wait time in seconds
                start_time = time.time()
                while time.time() - start_time < max_wait:
                    if self.simulator_process.poll() is not None:
                        break
                    time.sleep(0.5)
                else:
                    print("Simulator is taking too long, checking for results anyway")

            # Check for results
            results_path = os.path.join("bin", "simulation_results.json")
            attempt = 0
            max_attempts = 5
            
            while attempt < max_attempts:
                attempt += 1                
                if os.path.exists(results_path):
                    try:
                        with open(results_path, 'r') as f:
                            results = json.load(f)
                            dialog = CustomMessageBox(self.ui.app, "Success", 
                                                    "Simulation completed successfully.", ["OK"])
                            dialog.get()
                            # Display the results in the UI
                            self.display_results(results_path)
                            return
                    except json.JSONDecodeError:
                        print(f"Invalid JSON in results file (attempt {attempt})")
                        time.sleep(1)
                else:
                    print(f"Results file not found (attempt {attempt})")
                    time.sleep(1)
                    
            messagebox.showerror("Error", "Simulator did not generate valid results after multiple attempts")
            
        except Exception as e:
            print(f"Simulation error: {str(e)}")
            messagebox.showerror("Error", f"Error during simulation: {str(e)}")

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

        if process_name in ["", "e.g., Process1"] or process_size in ["", "e.g., 1"]:
            CustomMessageBox(self.ui.app, "Error", "All required fields must be filled!", ["OK"])
            return

        process_id = str(self.next_process_id)
        self.next_process_id += 1
        virtual_address = self.generate_virtual_address()

        display_name = system_process if process_type == "System" else process_name
        process_info = f"ID: {process_id}, Name: {display_name}, Size: {process_size}GB, Type: {process_type}, VA: {virtual_address}"

        process_entry = {
            "id": process_id,
            "name": display_name,
            "size_gb": int(process_size),
            "type": process_type,
            "has_priority": False,
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

    def resume_process(self, process_frame, process_id):
        idx = self.find_process_index(process_id)
        if idx == -1:
            CustomMessageBox(self.ui.app, "Error", f"Process with ID {process_id} not found.", ["OK"])
            return

        self.process_data[idx]["is_process_stop"] = False
        self.update_process_ui(process_id)
        self.reorder_process_list()
        self.send_to_cpp()

    def reorder_process_list(self):
        running = sorted(
            [proc for proc in self.process_data if not proc["is_process_stop"]],
            key=lambda x: x["id"]
        )
        stopped = sorted(
            [proc for proc in self.process_data if proc["is_process_stop"]],
            key=lambda x: x["id"]
        )

        self.process_data = running + stopped

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
            process_info = f"ID: {proc['id']}, Name: {proc['name']}, Size: {proc['size_gb']}GB, Type: {proc['type']}, VA: {proc['virtual_address']}"
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

    def enable_process_add_section(self):
        self.ui.process_name_entry.configure(state="normal")
        self.ui.process_size_entry.configure(state="normal")
        self.ui.process_type_menu.configure(state="normal")
        self.ui.add_process_button.configure(state="normal")

    def disable_process_add_section(self):
        self.ui.process_name_entry.configure(state="disabled")
        self.ui.process_size_entry.configure(state="disabled")
        self.ui.process_type_menu.configure(state="disabled")
        self.ui.add_process_button.configure(state="disabled")
        
    def display_results(self, results_path):
        """Display simulation results in charts"""
        # Switch to the Results tab
        self.ui.main_tabview.set("Results")
        
        # Create the charts using the ChartViewer
        if self.ui.chart_viewer.create_charts(results_path):
            print("Charts created successfully")
        else:
            print("Failed to create charts")
            messagebox.showerror("Error", "Failed to display simulation results charts")