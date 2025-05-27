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
        self.geometry("600x450")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Center the window
        self.center_window()

        self.result = None
        
        # Modern colors
        self.colors = {
            'primary': '#2563eb',
            'success': '#059669', 
            'warning': '#d97706',
            'danger': '#dc2626',
            'surface': '#f8fafc',
            'card': '#ffffff'
        }

        # Main container
        main_container = ctk.CTkFrame(self, fg_color=self.colors['surface'])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header with icon
        header_frame = ctk.CTkFrame(main_container, fg_color=self.colors['primary'], corner_radius=15)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Determine icon based on title
        icon = self.get_icon_for_title(title)
        
        header_label = ctk.CTkLabel(
            header_frame,
            text=f"{icon} {title}",
            font=("Segoe UI", 18, "bold"),
            text_color="white"
        )
        header_label.pack(pady=20)

        # Message container
        message_container = ctk.CTkFrame(main_container, fg_color=self.colors['card'], corner_radius=15)
        message_container.pack(fill="both", expand=True, pady=(0, 20))

        # Scrollable message area
        message_scroll = ctk.CTkScrollableFrame(message_container, fg_color="transparent")
        message_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        message_label = ctk.CTkLabel(
            message_scroll,
            text=message,
            wraplength=500,
            font=("Segoe UI", 12),
            justify="left",
            text_color="#1e293b"
        )
        message_label.pack(pady=10, anchor="w")

        # Button container
        button_container = ctk.CTkFrame(main_container, fg_color="transparent")
        button_container.pack(fill="x")

        self.buttons = []
        button_frame = ctk.CTkFrame(button_container, fg_color="transparent")
        button_frame.pack(expand=True)

        for i, option in enumerate(options):
            color = self.get_button_color(option, i, len(options))
            btn = ctk.CTkButton(
                button_frame,
                text=option,
                command=lambda opt=option: self.on_button_click(opt),
                width=120,
                height=40,
                corner_radius=10,
                font=("Segoe UI", 12, "bold"),
                fg_color=color,
                hover_color=f"{color}dd"
            )
            btn.pack(side="left", padx=10, pady=10)
            self.buttons.append(btn)

    def center_window(self):
        """Center the window on screen"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (450 // 2)
        self.geometry(f"600x450+{x}+{y}")

    def get_icon_for_title(self, title):
        """Get appropriate icon based on dialog title"""
        title_lower = title.lower()
        if "error" in title_lower:
            return "❌"
        elif "success" in title_lower:
            return "✅"
        elif "confirm" in title_lower:
            return "❓"
        elif "warning" in title_lower:
            return "⚠️"
        elif "simulation" in title_lower:
            return "🚀"
        else:
            return "ℹ️"

    def get_button_color(self, option, index, total):
        """Get appropriate color for button based on option text"""
        option_lower = option.lower()
        if option_lower in ["ok", "yes", "confirm", "save"]:
            return self.colors['success']
        elif option_lower in ["cancel", "no", "close"]:
            return self.colors['danger']
        elif option_lower in ["maybe", "later"]:
            return self.colors['warning']
        else:
            return self.colors['primary']

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
                CustomMessageBox(self.ui.app, "❌ Error", "Simulator executable not found", ["OK"])
                return False
                
            try:
                self.simulator_process = subprocess.Popen([self.simulator_path])
            except Exception as e:
                CustomMessageBox(self.ui.app, "❌ Error", f"Failed to start simulator: {str(e)}", ["OK"])
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
            CustomMessageBox(self.ui.app, "❌ Error", f"Failed to save settings: {str(e)}", ["OK"])
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
                CustomMessageBox(self.ui.app, "❌ Error", f"Failed to load process data: {str(e)}", ["OK"])
                
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
                            dialog = CustomMessageBox(self.ui.app, "✅ Success", "Simulation completed successfully.", ["OK"])
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
            
            CustomMessageBox(self.ui.app, "❌ Error", "Simulator did not generate valid results after multiple attempts", ["OK"])
            return False

        except Exception as e:
            print(f"Simulation error: {str(e)}")
            CustomMessageBox(self.ui.app, "❌ Error", f"Failed to process simulation: {str(e)}", ["OK"])
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
            f"🔧 Environment Configuration Summary:\n\n"
            f"💾 RAM Size: {settings['ram_size']} GB\n"
            f"📄 Page Size: {settings['page_size']}\n"
            f"⚡ TLB Size: {settings['tlb_size']}\n"
            f"🔌 TLB Enabled: {'Yes' if settings['tlb_enabled'] else 'No'}\n"
            f"🏠 Virtual Address Size: {settings['virtual_address_size']}\n"
            f"💿 ROM Size: {settings['rom_size']}\n"
            f"🔄 Swap Size: {settings['swap_size']:.0f}%\n"
            f"📦 Allocation Type: {settings['allocation_type']}\n\n"
            f"✅ Click OK to confirm and enable process management."
        )

        dialog = CustomMessageBox(self.ui.app, "❓ Confirm Environment Settings", message, ["OK", "Cancel"])
        if dialog.get() == "OK":
            if self.save_to_json():
                self.enable_process_add_section()
                self.ui.config_button.configure(text="🔄 Update Configuration")
                dialog = CustomMessageBox(self.ui.app, "✅ Success", "Environment settings saved successfully!\n\nYou can now add processes to the simulation.", ["OK"])
                dialog.get()

    def confirm_processes(self):
        if not self.process_data:
            CustomMessageBox(self.ui.app, "⚠️ Warning", "No processes have been added yet.\n\nPlease add at least one process before starting the simulation.", ["OK"])
            return
        
        # First, save the configuration
        if not self.save_to_json():
            CustomMessageBox(self.ui.app, "❌ Error", "Failed to save configuration", ["OK"])
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
            CustomMessageBox(self.ui.app, "❌ Error", "Failed to start simulator", ["OK"])
            return
            
        dialog = CustomMessageBox(self.ui.app, "🚀 Simulation Started", 
                                "🔄 Simulation is now running...\n\nPlease wait while the virtual memory simulator processes your configuration and active processes.\n\nThis may take a few moments.", ["OK"])
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
                            dialog = CustomMessageBox(self.ui.app, "✅ Success", 
                                                    "🎉 Simulation completed successfully!\n\nResults are now available in the 'Simulation Results' tab.\n\nYou can view detailed charts and performance metrics.", ["OK"])
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
                    
            CustomMessageBox(self.ui.app, "❌ Error", "Simulator did not generate valid results after multiple attempts.\n\nPlease check your configuration and try again.", ["OK"])
            
        except Exception as e:
            print(f"Simulation error: {str(e)}")
            CustomMessageBox(self.ui.app, "❌ Error", f"Error during simulation:\n\n{str(e)}", ["OK"])

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
            CustomMessageBox(self.ui.app, "⚠️ Validation Error", "📝 All required fields must be filled!\n\nPlease provide:\n• Process name\n• Process size (in GB)", ["OK"])
            return

        try:
            size_value = float(process_size)
            if size_value <= 0:
                CustomMessageBox(self.ui.app, "⚠️ Validation Error", "📏 Process size must be greater than 0 GB.", ["OK"])
                return
        except ValueError:
            CustomMessageBox(self.ui.app, "⚠️ Validation Error", "📏 Process size must be a valid number.", ["OK"])
            return

        process_id = str(self.next_process_id)
        self.next_process_id += 1
        virtual_address = self.generate_virtual_address()

        display_name = system_process if process_type == "System" else process_name
        process_info = f"ID: {process_id}, Name: {display_name}, Size: {process_size}GB, Type: {process_type}, VA: {virtual_address}"

        process_entry = {
            "id": process_id,
            "name": display_name,
            "size_gb": float(process_size),
            "type": process_type,
            "has_priority": False,
            "is_process_stop": False,
            "virtual_address": virtual_address
        }

        self.process_data.append(process_entry)
        self.ui.add_process_to_list(process_info, process_id, False)
        self.save_to_json()

        # Clear and reset form
        self.ui.process_name_entry.delete(0, "end")
        self.ui.process_size_entry.delete(0, "end")
        
        # Show success message
        CustomMessageBox(self.ui.app, "✅ Success", f"🎉 Process '{display_name}' added successfully!\n\nProcess ID: {process_id}\nSize: {process_size} GB\nType: {process_type}", ["OK"])

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
                
                # Update button text and color
                action_text = "▶️ Resume" if is_stopped else "⏸️ Stop"
                action_color = self.ui.colors['success'] if is_stopped else self.ui.colors['warning']
                
                frame.button.configure(
                    text=action_text,
                    fg_color=action_color,
                    hover_color=f"{action_color}dd",
                    command=lambda pid=process_id: self.resume_process(frame, pid) if is_stopped else self.stop_process(frame, pid)
                )
                found = True
                break
        if not found:
            self.reorder_process_list()

    def resume_process(self, process_frame, process_id):
        idx = self.find_process_index(process_id)
        if idx == -1:
            CustomMessageBox(self.ui.app, "❌ Error", f"Process with ID {process_id} not found.", ["OK"])
            return

        process_name = self.process_data[idx]["name"]
        dialog = CustomMessageBox(self.ui.app, "❓ Confirm Resume", f"▶️ Resume process '{process_name}'?\n\nThis will restart the process in the simulation.", ["Resume", "Cancel"])
        
        if dialog.get() == "Resume":
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
            self.ui.no_processes_label = ctk.CTkLabel(
                self.ui.process_container,
                text="🔍 No active processes\nAdd a process to get started",
                font=("Segoe UI", 14),
                text_color=self.ui.colors['text_secondary']
            )
            self.ui.no_processes_label.pack(pady=50)
            return

        for proc in self.process_data:
            process_info = f"ID: {proc['id']}, Name: {proc['name']}, Size: {proc['size_gb']}GB, Type: {proc['type']}, VA: {proc['virtual_address']}"
            self.ui.add_process_to_list(process_info, proc['id'], proc["is_process_stop"])

        self.save_to_json()

    def remove_process(self, process_frame, process_id):
        idx = self.find_process_index(process_id)
        if idx == -1:
            CustomMessageBox(self.ui.app, "❌ Error", f"Process with ID {process_id} not found.", ["OK"])
            return

        proc = self.process_data[idx]
        dialog = CustomMessageBox(self.ui.app, "❓ Confirm Removal", f"🗑️ Remove process '{proc['name']}'?\n\nProcess ID: {proc['id']}\nSize: {proc['size_gb']} GB\n\nThis action cannot be undone.", ["Remove", "Cancel"])
        
        if dialog.get() == "Remove":
            self.process_data.pop(idx)
            self.ui.remove_process(process_frame, process_id)
            self.reorder_process_list()
            if self.process_data:
                self.send_to_cpp()

    def stop_process(self, process_frame, process_id):
        idx = self.find_process_index(process_id)
        if idx == -1:
            CustomMessageBox(self.ui.app, "❌ Error", f"Process with ID {process_id} not found.", ["OK"])
            return

        process_name = self.process_data[idx]["name"]
        dialog = CustomMessageBox(self.ui.app, "❓ Confirm Stop", f"⏸️ Stop process '{process_name}'?\n\nThis will pause the process in the simulation.", ["Stop", "Cancel"])
        
        if dialog.get() == "Stop":
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
        self.ui.main_tabview.set("📊 Simulation Results")
        
        # Create the charts using the ChartViewer
        if self.ui.chart_viewer.create_charts(results_path):
            print("Charts created successfully")
        else:
            print("Failed to create charts")
            CustomMessageBox(self.ui.app, "❌ Error", "Failed to display simulation results charts.\n\nPlease check the simulation output and try again.", ["OK"])