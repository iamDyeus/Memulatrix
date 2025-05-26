import customtkinter as ctk
import os
import matplotlib
matplotlib.use('TkAgg')  # Set the backend before importing pyplot
from .input_ui_constraints import LogicHandler, CustomMessageBox
from .visualization import ChartViewer

class VirtualMemoryUI:
    def __init__(self, app, env_file_path=None, proc_file_path=None, simulator_path=None, simulator_process=None):
        self.app = app
        self.app.title("Memulatrix - The Virtual Memory Simulator")
        self.app.resizable(True, True)
        self.app.minsize(800, 600)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.simulator_path = simulator_path
        self.simulator_process = simulator_process

        # Initialize the logic handler before setting up UI
        self.logic_handler = LogicHandler(self, env_file_path, proc_file_path, simulator_path, simulator_process)

        # Header Frame
        self.header_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        self.header_frame.pack(pady=(5, 3), padx=20, fill="x")  # Reduced padding

        self.title = ctk.CTkLabel(self.header_frame, text="Memulatrix", font=("Arial", 24, "bold"))  # Reduced font size
        self.title.pack(side="left", padx=20)

        self.theme_toggle = ctk.CTkButton(self.header_frame, text="Toggle Theme", command=self.toggle_theme)
        self.theme_toggle.pack(side="right", padx=20)

        # Settings Frame
        self.settings_frame = ctk.CTkFrame(self.app)
        self.settings_frame.pack(pady=(3, 5), padx=20, fill="x")  # Reduced padding

        self.ram_frame = ctk.CTkFrame(self.settings_frame)
        self.ram_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")  # Reduced padding

        self.memory_frame = ctk.CTkFrame(self.settings_frame)
        self.memory_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")  # Reduced padding

        self.process_frame = ctk.CTkFrame(self.settings_frame)
        self.process_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")  # Reduced padding

        self.settings_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.settings_frame.grid_rowconfigure(0, weight=1)

        # RAM Frame contents
        ctk.CTkLabel(self.ram_frame, text="RAM & ROM Settings", font=("Arial", 14)).pack(pady=2)  # Reduced font and padding
        
        ctk.CTkLabel(self.ram_frame, text="RAM Size (GB):", font=("Arial", 12)).pack(anchor="w", padx=10, pady=1)  # Reduced pady
        self.ram_size_var = ctk.StringVar(value="1")
        ram_sizes = ["1", "2"] + [str(i) for i in range(4, 65, 4)]
        self.ram_dropdown = ctk.CTkOptionMenu(self.ram_frame, values=ram_sizes, variable=self.ram_size_var, command=self.logic_handler.update_options)
        self.ram_dropdown.pack(pady=2)  # Reduced padding

        ctk.CTkLabel(self.ram_frame, text="ROM Size:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=1)  # Reduced pady
        self.rom_size_var = ctk.StringVar(value="32 GB")
        rom_sizes = ["32 GB", "64 GB", "128 GB", "256 GB", "512 GB", "1 TB", "2 TB", "4 TB"]
        self.rom_size_menu = ctk.CTkOptionMenu(self.ram_frame, values=rom_sizes, variable=self.rom_size_var)
        self.rom_size_menu.pack(pady=2)  # Reduced padding

        ctk.CTkLabel(self.ram_frame, text="Swap Size (%):", font=("Arial", 12)).pack(anchor="w", padx=10, pady=1)  # Reduced pady
        self.swap_percent_var = ctk.DoubleVar(value=0)
        self.swap_slider = ctk.CTkSlider(
            self.ram_frame,
            from_=0,
            to=20,
            number_of_steps=20,
            variable=self.swap_percent_var
        )
        self.swap_slider.pack(pady=2)  # Reduced padding
        self.swap_label = ctk.CTkLabel(self.ram_frame, text=f"{self.swap_percent_var.get():.0f}%", font=("Arial", 12))
        self.swap_label.pack(pady=1)  # Reduced padding
        self.swap_percent_var.trace_add("write", self.update_swap_label)

        # Memory Frame contents
        ctk.CTkLabel(self.memory_frame, text="Memory Settings", font=("Arial", 14)).pack(pady=2)  # Reduced font and padding
        ctk.CTkLabel(self.memory_frame, text="Page Size (KB):", font=("Arial", 12)).pack(anchor="w", padx=10, pady=1)  # Reduced pady
        self.page_size_var = ctk.StringVar()
        self.page_size_menu = ctk.CTkOptionMenu(self.memory_frame, values=[], variable=self.page_size_var)
        self.page_size_menu.configure(state="disabled")
        self.page_size_menu.pack(pady=2)  # Reduced padding

        ctk.CTkLabel(self.memory_frame, text="TLB Size:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=1)  # Reduced pady
        self.tlb_size_var = ctk.StringVar()
        self.tlb_size_menu = ctk.CTkOptionMenu(self.memory_frame, values=[], variable=self.tlb_size_var)
        self.tlb_size_menu.configure(state="disabled")
        self.tlb_size_menu.pack(pady=2)  # Reduced padding

        self.tlb_enabled_var = ctk.BooleanVar()
        self.tlb_checkbox = ctk.CTkCheckBox(self.memory_frame, text="Enable TLB Usage", variable=self.tlb_enabled_var)
        self.tlb_checkbox.pack(pady=2)  # Reduced padding

        ctk.CTkLabel(self.memory_frame, text="Virtual Address Size:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=1)  # Reduced pady
        self.va_size_var = ctk.StringVar(value="16-bit")
        self.va_size_menu = ctk.CTkOptionMenu(self.memory_frame, values=["16-bit"], variable=self.va_size_var)
        self.va_size_menu.pack(pady=2)  # Reduced padding

        ctk.CTkLabel(self.memory_frame, text="Memory Allocation Type:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=1)  # Reduced pady
        self.memory_allocation_var = ctk.StringVar(value="Contiguous")
        self.memory_allocation_menu = ctk.CTkOptionMenu(
            self.memory_frame,
            values=["Contiguous", "Non-Contiguous"],
            variable=self.memory_allocation_var
        )
        self.memory_allocation_menu.pack(pady=2)  # Reduced padding

        self.config_button = ctk.CTkButton(self.memory_frame, text="Set Configuration", command=self.logic_handler.set_configuration)
        self.config_button.pack(pady=5)  # Reduced padding

        # Process Frame contents
        ctk.CTkLabel(self.process_frame, text="Add Process", font=("Arial", 14)).pack(pady=2)  # Reduced font and padding
        ctk.CTkLabel(self.process_frame, text="Name:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=1)  # Reduced pady
        self.process_name_entry = ctk.CTkEntry(self.process_frame, placeholder_text="e.g., Process1")
        self.process_name_entry.pack(pady=2)  # Reduced padding

        ctk.CTkLabel(self.process_frame, text="Size (GB):", font=("Arial", 12)).pack(anchor="w", padx=10, pady=1)  # Reduced pady
        self.process_size_entry = ctk.CTkEntry(self.process_frame, placeholder_text="e.g., 1")
        self.process_size_entry.pack(pady=2)  # Reduced padding

        ctk.CTkLabel(self.process_frame, text="Type:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=1)  # Reduced pady
        self.process_type_var = ctk.StringVar(value="User")
        self.process_type_menu = ctk.CTkOptionMenu(self.process_frame, values=["User", "System"], variable=self.process_type_var, command=self.logic_handler.toggle_system_dropdown)
        self.process_type_menu.pack(pady=2)  # Reduced padding

        self.system_process_frame = ctk.CTkFrame(self.process_frame)
        ctk.CTkLabel(self.system_process_frame, text="System Process:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=1)  # Reduced pady
        self.system_process_var = ctk.StringVar(value="kernel")
        system_processes = ["kernel", "scheduler", "memory_manager", "file_system", "network_stack"]
        self.system_process_menu = ctk.CTkOptionMenu(self.system_process_frame, values=system_processes, variable=self.system_process_var)
        self.system_process_menu.pack(pady=2)  # Reduced padding

        # Button Frame for Add Process and Confirm Processes
        self.button_frame = ctk.CTkFrame(self.process_frame, fg_color="transparent")
        self.button_frame.pack(pady=3)  # Reduced padding

        self.add_process_button = ctk.CTkButton(self.button_frame, text="Add Process", command=self.logic_handler.save_process)
        self.add_process_button.pack(side="left", padx=5)

        self.confirm_process_button = ctk.CTkButton(
            self.button_frame,
            text="Confirm Processes",
            command=self.logic_handler.confirm_processes,
            state="disabled"
        )
        self.confirm_process_button.pack(side="left", padx=5)

        self.logic_handler.disable_process_add_section()        # Frame for Active Processes        
        # # Create a tabview for processes and results
        self.main_tabview = ctk.CTkTabview(self.app)
        self.main_tabview.pack(padx=10, pady=(0, 10), fill="both", expand=True)
        
        # Create processes tab
        self.processes_tab = self.main_tabview.add("Processes")
        self.results_tab = self.main_tabview.add("Results")
        
        # Set processes as the default tab
        self.main_tabview.set("Processes")
        
        # Create the processes frame in the processes tab
        self.outer_frame = ctk.CTkFrame(self.processes_tab)
        self.outer_frame.pack(padx=10, pady=10, fill="both", expand=True)

        ctk.CTkLabel(self.outer_frame, text="Active Processes", font=("Arial", 16)).pack(anchor="w", padx=10, pady=5)

        self.process_frame_container = ctk.CTkFrame(self.outer_frame)
        self.process_frame_container.pack(fill="both", expand=True)
        
        # Create the results frame in the results tab
        self.results_frame = ctk.CTkFrame(self.results_tab)
        self.results_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Initialize the chart viewer for the results tab
        self.chart_viewer = ChartViewer(self.results_frame)

        self.process_container = ctk.CTkFrame(self.process_frame_container, fg_color="transparent")
        self.process_container.pack(fill="both", expand=True)

        self.process_list = []
        self.no_processes_label = ctk.CTkLabel(self.process_container, text="No active processes", font=("Arial", 12, "italic"))
        self.no_processes_label.pack(pady=20)

        self.logic_handler.load_processes_from_json()
        self.logic_handler.update_options(None)
        self.app.protocol("WM_DELETE_WINDOW", self.logic_handler.on_closing)

    def update_swap_label(self, *args):
        self.swap_label.configure(text=f"{self.swap_percent_var.get():.0f}%")

    def toggle_theme(self):
        if ctk.get_appearance_mode() == "Light":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def enable_process_add_section(self):
        self.process_name_entry.configure(state="normal")
        self.process_size_entry.configure(state="normal")
        self.process_type_menu.configure(state="normal")
        if self.process_type_var.get() == "System":
            self.system_process_menu.configure(state="normal")
        else:
            self.system_process_menu.configure(state="disabled")
        self.add_process_button.configure(state="normal")
        if self.process_list:
            self.confirm_process_button.configure(state="normal")

    def disable_process_add_section(self):
        self.process_name_entry.configure(state="disabled")
        self.process_size_entry.configure(state="disabled")
        self.process_type_var.set("User")
        self.process_type_menu.configure(state="disabled")
        self.system_process_menu.configure(state="disabled")
        self.add_process_button.configure(state="disabled")
        self.confirm_process_button.configure(state="disabled")

    def add_process_to_list(self, process_info, process_idx, is_stopped):
        if self.no_processes_label.winfo_exists():
            self.no_processes_label.destroy()

        process_frame = ctk.CTkFrame(self.process_container)
        process_frame.pack(fill="x", expand=True, pady=2, padx=10)
        
        info_label = ctk.CTkLabel(process_frame, text=process_info, anchor="w", font=("Arial", 12))
        info_label.pack(side="left", padx=10)
        
        button_frame = ctk.CTkFrame(process_frame, fg_color="transparent")
        button_frame.pack(side="right", padx=10)
        
        process_frame.button = ctk.CTkButton(
            button_frame, 
            text="Resume" if is_stopped else "Stop", 
            fg_color="#66CC66" if is_stopped else "#0e19e6",
            width=70,
            command=lambda: self.logic_handler.resume_process(process_frame, process_idx) if is_stopped 
                           else self.logic_handler.stop_process(process_frame, process_idx)
        )
        process_frame.button.pack(side="left", padx=5)
        
        remove_button = ctk.CTkButton(
            button_frame, 
            text="Remove", 
            fg_color="#FF5555", 
            width=70,
            command=lambda: self.logic_handler.remove_process(process_frame, process_idx)
        )
        remove_button.pack(side="left", padx=5)
        
        self.process_list.append((process_frame, process_idx))
        
        # If this is the first process we're adding, enable the confirm button
        if len(self.process_list) == 1:
            self.confirm_process_button.configure(state="normal")

    def remove_process(self, process_frame, process_id):
        process_frame.destroy()
        self.process_list = [(frame, pid) for frame, pid in self.process_list if pid != process_id]
        
        if not self.process_list:
            self.no_processes_label = ctk.CTkLabel(self.process_container, text="No active processes", font=("Arial", 12, "italic"))
            self.no_processes_label.pack(pady=20)
            self.confirm_process_button.configure(state="disabled")
            
    def toggle_system_dropdown(self, value):
        if value == "System":
            self.system_process_frame.pack(pady=5)
        else:
            self.system_process_frame.pack_forget()