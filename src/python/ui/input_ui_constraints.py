import customtkinter as ctk
import json
import os
import time
import hashlib

class CustomMessageBox(ctk.CTkToplevel):
    def __init__(self, parent, title, message, options):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result = None

        message_frame = ctk.CTkFrame(self)
        message_frame.pack(pady=10, padx=10, fill="both", expand=True)

        ctk.CTkLabel(message_frame, text=message, wraplength=350, font=("Arial", 12)).pack(pady=10, padx=10)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=10, fill="x", padx=10)

        for option in options:
            btn = ctk.CTkButton(
                button_frame,
                text=option,
                command=lambda opt=option: self.on_button_click(opt),
                width=80
            )
            btn.pack(side="left", padx=10, pady=5)

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
    def __init__(self, ui):
        self.ui = ui
        self.process_data = []
        self.next_process_id = 1001

    def on_closing(self):
        if os.path.exists("processes.json"):
            os.remove("processes.json")
        if os.path.exists("environment_settings.json"):
            os.remove("environment_settings.json")
        self.ui.app.destroy()

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
                with open("environment_settings.json", "w") as f:
                    json.dump(settings, f, indent=4)
                self.enable_process_add_section()
                self.ui.config_button.configure(text="Update Configuration")
                CustomMessageBox(self.ui.app, "Success", "Environment settings confirmed. You can now add processes.", ["OK"])
        else:
            try:
                with open("environment_settings.json", "r") as f:
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
                CustomMessageBox(self.ui.app, "No Changes", "No changes detected. Please modify at least one setting to update.", ["OK"])
                return

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
            dialog = CustomMessageBox(self.ui.app, "Update Environment Settings", message, ["OK", "Cancel"])
            if dialog.get() == "OK":
                try:
                    with open("environment_settings.json", "w") as f:
                        json.dump(settings, f, indent=4)
                    CustomMessageBox(self.ui.app, "Success", "Environment settings updated successfully!", ["OK"])
                except Exception as e:
                    CustomMessageBox(self.ui.app, "Error", f"Failed to update settings: {str(e)}", ["OK"])

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
        if os.path.exists("processes.json"):
            with open("processes.json", "r") as f:
                self.process_data = json.load(f)
                for idx, proc in enumerate(self.process_data):
                    process_info = f"ID: {proc['id']}, Name: {proc['name']}, Size: {proc['size_gb']}GB, Type: {proc['type']}, Has Priority: {proc['has_priority']}, VA: {proc['virtual_address']}"
                    self.ui.add_process_to_list(process_info, idx, proc.get("is_process_stop", False))
                self.reorder_process_list()
                self.next_process_id = max(self.next_process_id, int(proc['id']) + 1)

    def save_processes_to_json(self):
        with open("processes.json", "w") as f:
            json.dump(self.process_data, f, indent=4)

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

        existing_addresses = {int(proc["virtual_address"], 16) for proc in self.process_data}
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

        self.process_data.append({
            "id": process_id,
            "name": display_name,
            "size_gb": int(process_size),
            "type": process_type,
            "has_priority": has_priority,
            "virtual_address": virtual_address,
            "is_process_stop": False,
            "timestamp": timestamp
        })

        self.ui.add_process_to_list(process_info, len(self.process_data) - 1, False)
        self.reorder_process_list()
        self.save_processes_to_json()
        CustomMessageBox(self.ui.app, "Success", f"Added Process: {process_info}", ["OK"])

        self.ui.process_name_entry.delete(0, "end")
        self.ui.process_name_entry.insert(0, "e.g., Process1")
        self.ui.process_size_entry.delete(0, "end")
        self.ui.process_size_entry.insert(0, "e.g., 1")

    def reorder_process_list(self):
        for frame, _ in self.ui.process_list:
            frame.destroy()
        self.ui.process_list.clear()

        if self.ui.no_processes_label.winfo_exists():
            self.ui.no_processes_label.destroy()

        if not self.process_data:
            self.ui.no_processes_label = ctk.CTkLabel(self.ui.process_container, text="No active processes", font=("Arial", 12, "italic"))
            self.ui.no_processes_label.pack(pady=20)
            return

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

        for idx, proc in enumerate(ordered_data):
            process_info = f"ID: {proc['id']}, Name: {proc['name']}, Size: {proc['size_gb']}GB, Type: {proc['type']}, Has Priority: {proc['has_priority']}, VA: {proc['virtual_address']}"
            self.ui.add_process_to_list(process_info, idx, proc["is_process_stop"])

    def remove_process(self, process_frame, process_idx):
        self.process_data.pop(process_idx)

        new_process_list = []
        for frame, idx in self.ui.process_list:
            if idx == process_idx:
                frame.destroy()
                continue
            new_idx = idx if idx < process_idx else idx - 1
            if hasattr(frame, 'button'):
                is_stopped = frame.button.cget("text") == "Resume"
                frame.button.configure(
                    command=lambda: self.stop_process(frame, new_idx) if not is_stopped else self.resume_process(frame, new_idx)
                )
            new_process_list.append((frame, new_idx))
        self.ui.process_list = new_process_list

        self.reorder_process_list()
        self.save_processes_to_json()

    def stop_process(self, process_frame, process_idx):
        self.process_data[process_idx]["is_process_stop"] = True
        process_frame.button.configure(
            text="Resume",
            fg_color="#66CC66",
            command=lambda: self.resume_process(process_frame, process_idx)
        )
        self.reorder_process_list()
        self.save_processes_to_json()
        CustomMessageBox(self.ui.app, "Info", f"Process {self.process_data[process_idx]['name']} stopped", ["OK"])

    def resume_process(self, process_frame, process_idx):
        self.process_data[process_idx]["is_process_stop"] = False
        process_frame.button.configure(
            text="Stop",
            fg_color="#C4A484",  # Changed Stop button color to red
            command=lambda: self.stop_process(process_frame, process_idx)
        )
        self.reorder_process_list()
        self.save_processes_to_json()
        CustomMessageBox(self.ui.app, "Info", f"Process {self.process_data[process_idx]['name']} resumed", ["OK"])