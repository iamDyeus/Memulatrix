import customtkinter as ctk
from .input_ui_constraints import LogicHandler, CustomMessageBox

class VirtualMemoryUI:
    def __init__(self, app, env_file_path=None, proc_file_path=None):
        self.app = app
        self.app.title("Memulatrix - The Virtual Memory Simulator")
        self.app.resizable(True, True)
        self.app.minsize(800, 600)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Initialize the logic handler with the provided file paths
        self.logic_handler = LogicHandler(self, env_file_path, proc_file_path)

        # Header Frame
        self.header_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        self.header_frame.pack(pady=10, padx=20, fill="x")

        self.title = ctk.CTkLabel(self.header_frame, text="Memulatrix", font=("Arial", 28, "bold"))
        self.title.pack(side="left", padx=20)

        self.theme_toggle = ctk.CTkButton(self.header_frame, text="Toggle Theme", command=self.toggle_theme)
        self.theme_toggle.pack(side="right", padx=20)

        # Settings Frame
        self.settings_frame = ctk.CTkFrame(self.app)
        self.settings_frame.pack(pady=(5, 10), padx=20, fill="x")

        self.ram_frame = ctk.CTkFrame(self.settings_frame)
        self.ram_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.memory_frame = ctk.CTkFrame(self.settings_frame)
        self.memory_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.process_frame = ctk.CTkFrame(self.settings_frame)
        self.process_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        self.settings_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.settings_frame.grid_rowconfigure(0, weight=1)

        # RAM Frame contents
        ctk.CTkLabel(self.ram_frame, text="RAM & ROM Settings", font=("Arial", 16)).pack(pady=5)
        self.ram_size_var = ctk.StringVar(value="1")
        ram_sizes = ["1", "2"] + [str(i) for i in range(4, 65, 4)]
        self.ram_dropdown = ctk.CTkOptionMenu(self.ram_frame, values=ram_sizes, variable=self.ram_size_var, command=self.logic_handler.update_options)
        self.ram_dropdown.pack(pady=5)

        ctk.CTkLabel(self.ram_frame, text="ROM Size:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=2)
        self.rom_size_var = ctk.StringVar(value="32 GB")
        rom_sizes = ["32 GB", "64 GB", "128 GB", "256 GB", "512 GB", "1 TB", "2 TB", "4 TB"]
        self.rom_size_menu = ctk.CTkOptionMenu(self.ram_frame, values=rom_sizes, variable=self.rom_size_var)
        self.rom_size_menu.pack(pady=5)

        # Memory Frame contents
        ctk.CTkLabel(self.memory_frame, text="Memory Settings", font=("Arial", 16)).pack(pady=5)
        ctk.CTkLabel(self.memory_frame, text="Page Size (KB):", font=("Arial", 12)).pack(anchor="w", padx=10, pady=2)
        self.page_size_var = ctk.StringVar()
        self.page_size_menu = ctk.CTkOptionMenu(self.memory_frame, values=[], variable=self.page_size_var)
        self.page_size_menu.configure(state="disabled")
        self.page_size_menu.pack(pady=5)

        ctk.CTkLabel(self.memory_frame, text="TLB Size:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=2)
        self.tlb_size_var = ctk.StringVar()
        self.tlb_size_menu = ctk.CTkOptionMenu(self.memory_frame, values=[], variable=self.tlb_size_var)
        self.tlb_size_menu.configure(state="disabled")
        self.tlb_size_menu.pack(pady=5)

        self.tlb_enabled_var = ctk.BooleanVar()
        self.tlb_checkbox = ctk.CTkCheckBox(self.memory_frame, text="Enable TLB Usage", variable=self.tlb_enabled_var)
        self.tlb_checkbox.pack(pady=5)

        ctk.CTkLabel(self.memory_frame, text="Virtual Address Size:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=2)
        self.va_size_var = ctk.StringVar(value="16-bit")
        self.va_size_menu = ctk.CTkOptionMenu(self.memory_frame, values=["16-bit"], variable=self.va_size_var)
        self.va_size_menu.pack(pady=5)

        self.config_button = ctk.CTkButton(self.memory_frame, text="Set Configuration", command=self.logic_handler.set_configuration)
        self.config_button.pack(pady=10)

        # Process Frame contents
        ctk.CTkLabel(self.process_frame, text="Add Process", font=("Arial", 16)).pack(pady=5)
        ctk.CTkLabel(self.process_frame, text="Name:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=2)
        self.process_name_entry = ctk.CTkEntry(self.process_frame, placeholder_text="e.g., Process1")
        self.process_name_entry.pack(pady=5)

        ctk.CTkLabel(self.process_frame, text="Size (GB):", font=("Arial", 12)).pack(anchor="w", padx=10, pady=2)
        self.process_size_entry = ctk.CTkEntry(self.process_frame, placeholder_text="e.g., 1")
        self.process_size_entry.pack(pady=5)

        ctk.CTkLabel(self.process_frame, text="Type:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=2)
        self.process_type_var = ctk.StringVar(value="User")
        self.process_type_menu = ctk.CTkOptionMenu(self.process_frame, values=["User", "System"], variable=self.process_type_var, command=self.logic_handler.toggle_system_dropdown)
        self.process_type_menu.pack(pady=5)

        self.system_process_frame = ctk.CTkFrame(self.process_frame)
        ctk.CTkLabel(self.system_process_frame, text="System Process:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=2)
        self.system_process_var = ctk.StringVar(value="kernel")
        system_processes = ["kernel", "scheduler", "memory_manager", "file_system", "network_stack"]
        self.system_process_menu = ctk.CTkOptionMenu(self.system_process_frame, values=system_processes, variable=self.system_process_var)
        self.system_process_menu.pack(pady=5)

        self.set_priority_var = ctk.BooleanVar()
        self.priority_checkbutton = ctk.CTkCheckBox(self.process_frame, text="Set Priority?", variable=self.set_priority_var)
        self.priority_checkbutton.pack(pady=5)

        self.add_process_button = ctk.CTkButton(self.process_frame, text="Add Process", command=self.logic_handler.save_process)
        self.add_process_button.pack(pady=5)

        self.logic_handler.disable_process_add_section()

        # Frame for Active Processes
        self.outer_frame = ctk.CTkFrame(self.app)
        self.outer_frame.pack(padx=10, pady=10, fill="both", expand=True)

        ctk.CTkLabel(self.outer_frame, text="Active Processes", font=("Arial", 16)).pack(anchor="w", padx=10, pady=5)

        self.process_frame_container = ctk.CTkFrame(self.outer_frame)
        self.process_frame_container.pack(fill="both", expand=True)

        self.process_container = ctk.CTkFrame(self.process_frame_container, fg_color="transparent")
        self.process_container.pack(fill="both", expand=True)

        self.process_list = []
        self.no_processes_label = ctk.CTkLabel(self.process_container, text="No active processes", font=("Arial", 12, "italic"))
        self.no_processes_label.pack(pady=20)

        self.logic_handler.load_processes_from_json()
        self.logic_handler.update_options(None)
        self.app.protocol("WM_DELETE_WINDOW", self.logic_handler.on_closing)

    def toggle_theme(self):
        if ctk.get_appearance_mode() == "Light":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def disable_process_add_section(self):
        self.process_name_entry.configure(state="disabled")
        self.process_size_entry.configure(state="disabled")
        self.process_type_var.set("User")
        self.process_type_menu.configure(state="disabled")
        self.system_process_menu.configure(state="disabled")
        self.set_priority_var.set(False)
        self.priority_checkbutton.configure(state="disabled")
        self.add_process_button.configure(state="disabled")

    def enable_process_add_section(self):
        self.process_name_entry.configure(state="normal")
        self.process_size_entry.configure(state="normal")
        self.process_type_menu.configure(state="normal")
        if self.process_type_var.get() == "System":
            self.system_process_menu.configure(state="normal")
        else:
            self.system_process_menu.configure(state="disabled")
        self.priority_checkbutton.configure(state="normal")
        self.add_process_button.configure(state="normal")

    def toggle_system_dropdown(self, value):
        if self.process_type_var.get() == "System":
            self.system_process_frame.pack(anchor="w", pady=5)
            self.system_process_menu.configure(state="normal")
        else:
            self.system_process_frame.pack_forget()
            self.system_process_menu.configure(state="disabled")

    def add_process_to_list(self, process_info, process_idx, is_stopped):
        if self.no_processes_label.winfo_exists():
            self.no_processes_label.destroy()

        process_frame = ctk.CTkFrame(self.process_container)
        process_frame.pack(fill="x", pady=2)

        process_label = ctk.CTkLabel(process_frame, text=process_info, font=("Arial", 12))
        process_label.pack(side="left", padx=5, pady=5)

        remove_button = ctk.CTkButton(
            process_frame,
            text="Remove",
            command=lambda: self.logic_handler.remove_process(process_frame, process_idx),
            fg_color="#FF6666",
            width=80
        )
        remove_button.pack(side="right", padx=5)

        stop_resume_button = ctk.CTkButton(
            process_frame,
            text="Stop" if not is_stopped else "Resume",
            command=lambda: self.logic_handler.stop_process(process_frame, process_idx) if not is_stopped else self.logic_handler.resume_process(process_frame, process_idx),
            fg_color="#0e19e6" if not is_stopped else "#66CC66",  # Changed Stop button color to red
            width=80
        )
        stop_resume_button.pack(side="right", padx=5)

        process_frame.button = stop_resume_button
        self.process_list.append((process_frame, process_idx))

if __name__ == "__main__":
    app = ctk.CTk()
    ui = VirtualMemoryUI(app)
    app.mainloop()