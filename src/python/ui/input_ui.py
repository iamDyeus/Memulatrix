import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import time
import hashlib

class VirtualMemoryUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Memory Simulator")
        self.root.geometry("800x500")
        self.root.configure(bg="lightblue")

        # Style configuration
        style = ttk.Style()
        style.configure("TLabel", font=("Helvetica", 10), background="lightblue")
        style.configure("TCombobox", font=("Helvetica", 10))
        style.configure("TButton", font=("Helvetica", 10, "bold"))
        style.configure("TCheckbutton", background="lightblue", font=("Helvetica", 10))

        # Title
        tk.Label(root, text="Virtual Memory Simulator", font=("Helvetica", 16, "bold"), bg="lightblue", fg="darkslategray").pack(pady=15)

        # Main Frame to hold all sections side by side
        main_frame = tk.Frame(root, bg="lightblue")
        main_frame.pack(pady=10, padx=10, fill="x")

        # RAM Selection Frame
        ram_selection_frame = tk.Frame(main_frame, bg="lightskyblue", padx=10, pady=10, relief="groove", borderwidth=2)
        ram_selection_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        tk.Label(ram_selection_frame, text="RAM & ROM Settings", font=("Helvetica", 11, "bold"), bg="lightskyblue", fg="darkslategray").pack(anchor="w")
        tk.Label(ram_selection_frame, text="Select RAM Size (GB):", bg="lightskyblue").pack(anchor="w")
        self.ram_size_var = tk.StringVar(value="1")
        ram_sizes = ["1", "2"] + [str(i) for i in range(4, 65, 4)]
        ram_menu = ttk.Combobox(ram_selection_frame, textvariable=self.ram_size_var, values=ram_sizes, width=15)
        ram_menu.pack(pady=5)
        ram_menu.bind("<<ComboboxSelected>>", self.update_options)
        # ROM Size Selection
        tk.Label(ram_selection_frame, text="ROM Size:", bg="lightskyblue").pack(anchor="w", pady=2)
        self.rom_size_var = tk.StringVar(value="32 GB")
        rom_sizes = ["32 GB", "64 GB", "128 GB", "256 GB", "512 GB", "1 TB", "2 TB", "4 TB"]
        self.rom_size_menu = ttk.Combobox(ram_selection_frame, textvariable=self.rom_size_var, values=rom_sizes, width=15)
        self.rom_size_menu.pack(pady=5)

        # Memory Settings Frame
        memory_settings_frame = tk.Frame(main_frame, bg="lightskyblue", padx=10, pady=10, relief="groove", borderwidth=2)
        memory_settings_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        tk.Label(memory_settings_frame, text="Memory Settings", font=("Helvetica", 11, "bold"), bg="lightskyblue", fg="darkslategray").pack(anchor="w")
        tk.Label(memory_settings_frame, text="Page Size (KB):", bg="lightskyblue").pack(anchor="w", pady=2)
        self.page_size_var = tk.StringVar()
        self.page_size_menu = ttk.Combobox(memory_settings_frame, textvariable=self.page_size_var, state="disabled", width=15)
        self.page_size_menu.pack(pady=5)
        tk.Label(memory_settings_frame, text="TLB Size:", bg="lightskyblue").pack(anchor="w", pady=2)
        self.tlb_size_var = tk.StringVar()
        self.tlb_size_menu = ttk.Combobox(memory_settings_frame, textvariable=self.tlb_size_var, state="disabled", width=15)
        self.tlb_size_menu.pack(pady=5)
        self.tlb_enabled_var = tk.BooleanVar()
        tk.Checkbutton(memory_settings_frame, text="Enable TLB Usage", variable=self.tlb_enabled_var).pack(anchor="w", pady=5)
        # Virtual Address Size Selection
        tk.Label(memory_settings_frame, text="Virtual Address Size:", bg="lightskyblue").pack(anchor="w", pady=2)
        self.va_size_var = tk.StringVar(value="16-bit")
        self.va_size_menu = ttk.Combobox(memory_settings_frame, textvariable=self.va_size_var, values=["16-bit"], width=15)
        self.va_size_menu.pack(pady=5)

        # Set/Update Configuration Button
        self.config_button = tk.Button(
            memory_settings_frame,
            text="Set Configuration",
            bg="dodgerblue",
            fg="white",
            command=self.set_configuration
        )
        self.config_button.pack(pady=10)

        # Process Addition Frame
        self.process_add_frame = tk.Frame(main_frame, bg="lightskyblue", padx=10, pady=10, relief="groove", borderwidth=2)
        self.process_add_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        tk.Label(self.process_add_frame, text="Add Process", font=("Helvetica", 11, "bold"), bg="lightskyblue", fg="darkslategray").pack(anchor="w")
        
        # Process Name
        tk.Label(self.process_add_frame, text="Name:", bg="lightskyblue").pack(anchor="w", pady=2)
        self.process_name_entry = tk.Entry(self.process_add_frame, width=20, fg="gray")
        self.process_name_entry.insert(0, "e.g., Process1")
        self.process_name_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(self.process_name_entry, "e.g., Process1"))
        self.process_name_entry.bind("<FocusOut>", lambda e: self.add_placeholder(self.process_name_entry, "e.g., Process1"))
        self.process_name_entry.pack(pady=5)

        # Process Size
        tk.Label(self.process_add_frame, text="Size (GB):", bg="lightskyblue").pack(anchor="w", pady=2)
        self.process_size_entry = tk.Entry(self.process_add_frame, width=20, fg="gray")
        self.process_size_entry.insert(0, "e.g., 1")
        self.process_size_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(self.process_size_entry, "e.g., 1"))
        self.process_size_entry.bind("<FocusOut>", lambda e: self.add_placeholder(self.process_size_entry, "e.g., 1"))
        self.process_size_entry.pack(pady=5)

        # Process Type
        tk.Label(self.process_add_frame, text="Type:", bg="lightskyblue").pack(anchor="w", pady=2)
        self.process_type_var = tk.StringVar(value="User")
        self.process_type_menu = ttk.Combobox(self.process_add_frame, textvariable=self.process_type_var, values=["User", "System"], width=17)
        self.process_type_menu.pack(pady=5)
        self.process_type_menu.bind("<<ComboboxSelected>>", self.toggle_system_dropdown)

        # System Process Dropdown (hidden by default)
        self.system_process_frame = tk.Frame(self.process_add_frame, bg="lightskyblue")
        tk.Label(self.system_process_frame, text="System Process:", bg="lightskyblue").pack(anchor="w", pady=2)
        self.system_process_var = tk.StringVar(value="kernel")
        system_processes = ["kernel", "scheduler", "memory_manager", "file_system", "network_stack"]
        self.system_process_menu = ttk.Combobox(self.system_process_frame, textvariable=self.system_process_var, values=system_processes, width=17)
        self.system_process_menu.pack(pady=5)

        # Set Priority Checkbox
        self.set_priority_var = tk.BooleanVar()
        self.priority_checkbutton = tk.Checkbutton(self.process_add_frame, text="Set Priority?", variable=self.set_priority_var, bg="lightskyblue")
        self.priority_checkbutton.pack(anchor="w", pady=5)

        # Add Process Button
        self.add_process_button = tk.Button(self.process_add_frame, text="Add Process", bg="dodgerblue", fg="white", command=self.save_process)
        self.add_process_button.pack(pady=10)

        # Disable process addition section initially
        self.disable_process_add_section()

        # Active Processes Frame
        active_processes_frame = tk.Frame(root, bg="lightcyan", padx=10, pady=10, relief="groove", borderwidth=2)
        active_processes_frame.pack(pady=10, padx=10, fill="both", expand=True)
        tk.Label(active_processes_frame, text="Active Processes", font=("Helvetica", 11, "bold"), bg="lightcyan", fg="darkslategray").pack(anchor="w")
        self.process_container = tk.Frame(active_processes_frame, bg="lightcyan")
        self.process_container.pack(fill="both", expand=True)
        self.process_list = []  # List of tuples: (frame, process_index)
        self.process_data = []  # List to store process info for JSON
        self.no_processes_label = tk.Label(self.process_container, text="No active processes", font=("Helvetica", 10, "italic"), bg="lightcyan", fg="gray")
        self.no_processes_label.pack(pady=20)

        # Process ID counter
        self.next_process_id = 1001

        # Load existing processes from JSON if available
        self.load_processes_from_json()

        # Configure grid weights for responsive layout
        main_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Initial update
        self.update_options(None)

        # Bind the window close event to delete JSON files
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        # Delete processes.json and environment_settings.json when the UI is closed
        if os.path.exists("processes.json"):
            os.remove("processes.json")
        if os.path.exists("environment_settings.json"):
            os.remove("environment_settings.json")
        self.root.destroy()

    def disable_process_add_section(self):
        self.process_name_entry.config(state="disabled")
        self.process_size_entry.config(state="disabled")
        self.process_type_var.set("User")  # Reset to default
        self.process_type_menu.config(state="disabled")
        self.system_process_menu.config(state="disabled")
        self.set_priority_var.set(False)
        self.priority_checkbutton.config(state="disabled")
        self.add_process_button.config(state="disabled")

    def enable_process_add_section(self):
        self.process_name_entry.config(state="normal")
        self.process_size_entry.config(state="normal")
        self.process_type_menu.config(state="readonly")
        if self.process_type_var.get() == "System":
            self.system_process_menu.config(state="readonly")
        else:
            self.system_process_menu.config(state="disabled")
        self.priority_checkbutton.config(state="normal")
        self.add_process_button.config(state="normal")
        # Ensure placeholder text is visible if fields are empty
        self.add_placeholder(self.process_name_entry, "e.g., Process1")
        self.add_placeholder(self.process_size_entry, "e.g., 1")

    def set_configuration(self):
        # Gather current settings
        settings = {
            "ram_size_gb": self.ram_size_var.get(),
            "page_size_kb": self.page_size_var.get().replace("KB", "") if self.page_size_var.get() else "0",
            "tlb_size": self.tlb_size_var.get() if self.tlb_size_var.get() else "0",
            "tlb_enabled": self.tlb_enabled_var.get(),
            "virtual_address_size": self.va_size_var.get(),
            "rom_size": self.rom_size_var.get()
        }

        # If this is the initial setup (Set Configuration)
        if self.config_button["text"] == "Set Configuration":
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
            if messagebox.askokcancel("Confirm Environment Settings", message):
                # Save settings to environment_settings.json
                with open("environment_settings.json", "w") as f:
                    json.dump(settings, f, indent=4)
                # Enable process addition section
                self.enable_process_add_section()
                # Change button to "Update Configuration"
                self.config_button.config(text="Update Configuration")
                messagebox.showinfo("Success", "Environment settings confirmed. You can now add processes.")
        else:
            # Update Configuration
            # Load previous settings
            try:
                with open("environment_settings.json", "r") as f:
                    prev_settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                messagebox.showerror("Error", "Could not load previous settings. Please set the configuration again.")
                self.config_button.config(text="Set Configuration")
                self.disable_process_add_section()
                return

            # Compare new settings with previous settings
            settings_unchanged = (
                settings["ram_size_gb"] == prev_settings["ram_size_gb"] and
                settings["page_size_kb"] == prev_settings["page_size_kb"] and
                settings["tlb_size"] == prev_settings["tlb_size"] and
                settings["tlb_enabled"] == prev_settings["tlb_enabled"] and
                settings["virtual_address_size"] == prev_settings["virtual_address_size"] and
                settings["rom_size"] == prev_settings["rom_size"]
            )

            if settings_unchanged:
                messagebox.showinfo("No Changes", "No changes detected. Please modify at least one setting to update.")
                return

            # Handle virtual address size change
            prev_bits = self.get_bits(prev_settings["virtual_address_size"])
            new_bits = self.get_bits(settings["virtual_address_size"])
            if prev_bits != new_bits and self.process_data:
                if new_bits > prev_bits:
                    # Increasing virtual address size: prepend zeros
                    for proc in self.process_data:
                        addr_int = int(proc["virtual_address"], 16)
                        proc["virtual_address"] = self.format_virtual_address(addr_int, new_bits)
                    self.reorder_process_list()
                    self.save_processes_to_json()
                else:
                    # Decreasing virtual address size: identify processes that cannot be trimmed
                    processes_to_delete = []
                    indices_to_delete = []
                    for idx, proc in enumerate(self.process_data):
                        addr_int = int(proc["virtual_address"], 16)
                        if self.has_non_zero_msb(addr_int, prev_bits, new_bits):
                            processes_to_delete.append(proc)
                            indices_to_delete.append(idx)

                    if processes_to_delete:
                        # Show dialog box with details of processes to be deleted
                        delete_message = (
                            "The following processes cannot be reduced and will be deleted:\n\n"
                        )
                        for proc in processes_to_delete:
                            delete_message += (
                                f"ID: {proc['id']}, Name: {proc['name']}, Virtual Address: {proc['virtual_address']}\n"
                            )
                        delete_message += "\nClick OK to proceed."
                        if not messagebox.askokcancel("Virtual Address Size Reduction", delete_message):
                            # Revert virtual address size to previous value
                            self.va_size_var.set(prev_settings["virtual_address_size"])
                            return

                        # Remove the identified processes (in reverse order to avoid index shifting)
                        indices_to_delete.sort(reverse=True)
                        for idx in indices_to_delete:
                            self.process_data.pop(idx)

                        # Clear the UI completely
                        for frame, _ in self.process_list:
                            frame.destroy()
                        self.process_list.clear()

                        # Rebuild the UI only with remaining processes
                        if not self.process_data:
                            # Ensure any existing no_processes_label is destroyed before creating a new one
                            if self.no_processes_label.winfo_exists():
                                self.no_processes_label.destroy()
                            self.no_processes_label = tk.Label(self.process_container, text="No active processes", font=("Helvetica", 10, "italic"), bg="lightcyan", fg="gray")
                            self.no_processes_label.pack(pady=20)
                        else:
                            for idx, proc in enumerate(self.process_data):
                                process_info = f"ID: {proc['id']}, Name: {proc['name']}, Size: {proc['size_gb']}GB, Type: {proc['type']}, Has Priority: {proc['has_priority']}, VA: {proc['virtual_address']}"
                                self.add_process_to_list(process_info, idx, proc["is_process_stop"])

                    # Reformat addresses for remaining processes to match new bit size
                    for proc in self.process_data:
                        addr_int = int(proc["virtual_address"], 16)
                        proc["virtual_address"] = self.format_virtual_address(addr_int, new_bits)
                    self.reorder_process_list()
                    self.save_processes_to_json()

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
            if messagebox.askokcancel("Update Environment Settings", message):
                # Update environment_settings.json
                try:
                    with open("environment_settings.json", "w") as f:
                        json.dump(settings, f, indent=4)
                    messagebox.showinfo("Success", "Environment settings updated successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update settings: {str(e)}")

    def get_bits(self, va_size):
        if va_size == "16-bit":
            return 16
        elif va_size == "32-bit":
            return 32
        else:  # 64-bit
            return 64

    def has_non_zero_msb(self, addr_int, prev_bits, new_bits):
        # Check if the bits that would be truncated (from new_bits to prev_bits) are non-zero
        mask = (1 << prev_bits) - 1  # Mask for all bits up to prev_bits
        truncated_bits = (1 << prev_bits) - (1 << new_bits)  # Bits that will be truncated
        return (addr_int & truncated_bits) != 0

    def format_virtual_address(self, addr_int, bits):
        if bits == 16:
            return f"0x{addr_int:04x}"  # 4 hex digits for 16 bits
        elif bits == 32:
            return f"0x{addr_int:08x}"  # 8 hex digits for 32 bits
        else:  # 64-bit
            return f"0x{addr_int:016x}"  # 16 hex digits for 64 bits

    def clear_placeholder(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg="black")

    def add_placeholder(self, entry, placeholder):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg="gray")

    def toggle_system_dropdown(self, event):
        if self.process_type_var.get() == "System":
            self.system_process_frame.pack(anchor="w", pady=5)
            self.system_process_menu.config(state="readonly")
        else:
            self.system_process_frame.pack_forget()
            self.system_process_menu.config(state="disabled")

    def update_options(self, event):
        ram_size_gb = int(self.ram_size_var.get())
        ram_bytes = ram_size_gb * 1024 * 1024 * 1024
        page_sizes = [2**i for i in range(12, 22) if 2**i <= ram_bytes // 1024]
        page_options = [f"{size//1024}KB" for size in page_sizes]
        self.page_size_menu['values'] = page_options
        self.page_size_menu['state'] = "readonly" if page_options else "disabled"
        self.page_size_var.set(page_options[0] if page_options else "")

        # Update TLB size options based on RAM size
        if ram_size_gb <= 16:
            tlb_options = ["16"]
        elif ram_size_gb <= 32:
            tlb_options = ["16", "32"]
        else:  # ram_size_gb > 32
            tlb_options = ["16", "32", "64"]
        self.tlb_size_menu['values'] = tlb_options
        self.tlb_size_menu['state'] = "readonly" if tlb_options else "disabled"
        self.tlb_size_var.set(tlb_options[0] if tlb_options else "")

        # Update virtual address size options based on RAM size
        va_size_options = []
        if ram_size_gb < 16:
            va_size_options = ["16-bit"]
        elif ram_size_gb < 32:
            va_size_options = ["16-bit", "32-bit"]
        else:  # ram_size_gb < 64
            va_size_options = ["16-bit", "32-bit", "64-bit"]
        self.va_size_menu['values'] = va_size_options
        self.va_size_menu['state'] = "readonly" if va_size_options else "disabled"
        # Set default to the smallest available option
        self.va_size_var.set(va_size_options[0] if va_size_options else "")

    def load_processes_from_json(self):
        if os.path.exists("processes.json"):
            with open("processes.json", "r") as f:
                self.process_data = json.load(f)
                for idx, proc in enumerate(self.process_data):
                    process_info = f"ID: {proc['id']}, Name: {proc['name']}, Size: {proc['size_gb']}GB, Type: {proc['type']}, Has Priority: {proc['has_priority']}, VA: {proc['virtual_address']}"
                    self.add_process_to_list(process_info, idx, proc.get("is_process_stop", False))
                self.reorder_process_list()
                self.next_process_id = max(self.next_process_id, int(proc['id']) + 1)

    def save_processes_to_json(self):
        with open("processes.json", "w") as f:
            json.dump(self.process_data, f, indent=4)

    def generate_virtual_address(self, timestamp):
        # Hash the timestamp to generate a virtual address
        hash_obj = hashlib.sha256(str(timestamp).encode())
        hash_value = int(hash_obj.hexdigest(), 16)

        # Determine max virtual address based on selected size
        va_size = self.va_size_var.get()
        if va_size == "16-bit":
            max_va = (1 << 16) - 1  # 2^16 - 1
            bits = 16
        elif va_size == "32-bit":
            max_va = (1 << 32) - 1  # 2^32 - 1
            bits = 32
        else:  # 64-bit
            max_va = (1 << 64) - 1  # 2^64 - 1
            bits = 64

        # Ensure virtual address fits within the selected virtual address size
        virtual_address = hash_value & max_va

        # Ensure the virtual address maps to a physical address within RAM size
        ram_size_bytes = int(self.ram_size_var.get()) * 1024 * 1024 * 1024
        max_physical_address = ram_size_bytes - 1
        # Simple mapping: modulo the virtual address to fit within RAM size
        virtual_address = virtual_address % (max_physical_address + 1)

        # Check for conflicts with existing virtual addresses
        existing_addresses = {int(proc["virtual_address"], 16) for proc in self.process_data}
        attempt = 0
        original_hash = virtual_address
        while virtual_address in existing_addresses and attempt < 1000:
            # Increment the timestamp slightly and rehash to avoid conflict
            attempt += 1
            hash_obj = hashlib.sha256((str(timestamp) + str(attempt)).encode())
            virtual_address = int(hash_obj.hexdigest(), 16) & max_va
            virtual_address = virtual_address % (max_physical_address + 1)

        if attempt >= 1000:
            # Fallback: use a random offset if we can't find a unique address
            virtual_address = (original_hash + len(existing_addresses) + 1) & max_va
            virtual_address = virtual_address % (max_physical_address + 1)

        # Format the virtual address with the correct number of hex digits
        return self.format_virtual_address(virtual_address, bits)

    def save_process(self):
        process_name = self.process_name_entry.get()
        process_size = self.process_size_entry.get()
        process_type = self.process_type_var.get()
        system_process = self.system_process_var.get() if process_type == "System" else None
        has_priority = self.set_priority_var.get()

        if process_name in ["", "e.g., Process1"] or process_size in ["", "e.g., 1"]:
            messagebox.showerror("Error", "All required fields must be filled!")
            return

        # Generate process ID
        process_id = str(self.next_process_id)
        self.next_process_id += 1

        # Capture timestamp for virtual address and addition time
        timestamp = time.time()

        # Generate virtual address (in hexadecimal)
        virtual_address = self.generate_virtual_address(timestamp)

        # Use system process name if type is System
        display_name = system_process if process_type == "System" else process_name
        process_info = f"ID: {process_id}, Name: {display_name}, Size: {process_size}GB, Type: {process_type}, Has Priority: {has_priority}, VA: {virtual_address}"

        # Add to process data list with timestamp and is_process_stop set to False
        self.process_data.append({
            "id": process_id,
            "name": display_name,
            "size_gb": int(process_size),
            "type": process_type,
            "has_priority": has_priority,
            "virtual_address": virtual_address,
            "is_process_stop": False,
            "timestamp": timestamp  # Store the time the process was added
        })

        # Update UI and JSON
        self.add_process_to_list(process_info, len(self.process_data) - 1, False)
        self.reorder_process_list()
        self.save_processes_to_json()
        messagebox.showinfo("Success", f"Added Process: {process_info}")

        # Reset fields
        self.process_name_entry.delete(0, tk.END)
        self.process_name_entry.insert(0, "e.g., Process1")
        self.process_name_entry.config(fg="gray")
        self.process_size_entry.delete(0, tk.END)
        self.process_size_entry.insert(0, "e.g., 1")
        self.process_size_entry.config(fg="gray")

    def reorder_process_list(self):
        # Clear the current display
        for frame, _ in self.process_list:
            frame.destroy()
        self.process_list.clear()

        # Remove any existing "No active processes" label
        if self.no_processes_label.winfo_exists():
            self.no_processes_label.destroy()

        if not self.process_data:
            self.no_processes_label = tk.Label(self.process_container, text="No active processes", font=("Helvetica", 10, "italic"), bg="lightcyan", fg="gray")
            self.no_processes_label.pack(pady=20)
            return

        # Sort processes:
        # 1. Priority processes first, ordered by timestamp
        # 2. Non-priority processes next, ordered by timestamp
        # 3. Stopped processes last, maintaining their relative order
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

        # Combine the lists in the correct order
        ordered_data = priority_running + non_priority_running + stopped

        # Rebuild the UI list in the new order
        for idx, proc in enumerate(ordered_data):
            process_info = f"ID: {proc['id']}, Name: {proc['name']}, Size: {proc['size_gb']}GB, Type: {proc['type']}, Has Priority: {proc['has_priority']}, VA: {proc['virtual_address']}"
            self.add_process_to_list(process_info, idx, proc["is_process_stop"])

    def add_process_to_list(self, process_info, process_idx, is_stopped):
        # Ensure the "No active processes" label is removed before adding a new process
        if self.no_processes_label.winfo_exists():
            self.no_processes_label.destroy()

        process_frame = tk.Frame(self.process_container, bg="white" if len(self.process_list) % 2 == 0 else "whitesmoke", bd=1, relief="solid")
        process_frame.pack(fill="x", pady=2)
        tk.Label(process_frame, text=process_info, font=("Helvetica", 10), bg=process_frame.cget("bg"), fg="darkslategray").pack(side="left", padx=5, pady=5)
        tk.Button(process_frame, text="Remove", bg="salmon", fg="white", font=("Helvetica", 8, "bold"), command=lambda: self.remove_process(process_frame, process_idx)).pack(side="right", padx=5)
        
        # Create a container for the stop/resume button
        process_frame.button = tk.Button(
            process_frame,
            text="Stop" if not is_stopped else "Resume",
            bg="orange" if not is_stopped else "green",
            fg="white",
            font=("Helvetica", 8, "bold"),
            command=lambda: self.stop_process(process_frame, process_idx) if not is_stopped else self.resume_process(process_frame, process_idx)
        )
        process_frame.button.pack(side="right", padx=5)
        
        self.process_list.append((process_frame, process_idx))

    def remove_process(self, process_frame, process_idx):
        # Remove the process from process_data
        self.process_data.pop(process_idx)

        # Remove the corresponding entry from process_list and update indices
        new_process_list = []
        for frame, idx in self.process_list:
            if idx == process_idx:
                frame.destroy()  # Destroy the frame for the removed process
                continue
            # Adjust indices for remaining processes
            new_idx = idx if idx < process_idx else idx - 1
            # Update the button commands with the new index
            if hasattr(frame, 'button'):
                is_stopped = frame.button.cget("text") == "Resume"
                frame.button.configure(
                    command=lambda: self.stop_process(frame, new_idx) if not is_stopped else self.resume_process(frame, new_idx)
                )
            new_process_list.append((frame, new_idx))
        self.process_list = new_process_list

        # Reorder the list and save to JSON
        self.reorder_process_list()
        self.save_processes_to_json()

    def stop_process(self, process_frame, process_idx):
        self.process_data[process_idx]["is_process_stop"] = True
        process_frame.button.configure(
            text="Resume",
            bg="green",
            command=lambda: self.resume_process(process_frame, process_idx)
        )
        self.reorder_process_list()
        self.save_processes_to_json()
        messagebox.showinfo("Info", f"Process {self.process_data[process_idx]['name']} stopped")

    def resume_process(self, process_frame, process_idx):
        self.process_data[process_idx]["is_process_stop"] = False
        process_frame.button.configure(
            text="Stop",
            bg="orange",
            command=lambda: self.stop_process(process_frame, process_idx)
        )
        self.reorder_process_list()
        self.save_processes_to_json()
        messagebox.showinfo("Info", f"Process {self.process_data[process_idx]['name']} resumed")

if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualMemoryUI(root)
    root.mainloop()