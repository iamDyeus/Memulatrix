import customtkinter as ctk
import os
import matplotlib
matplotlib.use('TkAgg')  # Set the backend before importing pyplot
from .input_ui_constraints import LogicHandler, CustomMessageBox
from .visualization import ChartViewer

class VirtualMemoryUI:
    def __init__(self, app, env_file_path=None, proc_file_path=None, simulator_path=None, simulator_process=None):
        self.app = app
        self.app.title("🧠 Memulatrix - Virtual Memory Simulator")
        self.app.resizable(True, True)
        self.app.minsize(1000, 700)
        
        # Modern color scheme
        self.colors = {
            'primary': '#2563eb',      # Blue
            'secondary': '#7c3aed',    # Purple  
            'success': '#059669',      # Green
            'warning': '#d97706',      # Orange
            'danger': '#dc2626',       # Red
            'surface': '#f8fafc',      # Light gray
            'card': '#ffffff',         # White
            'text_primary': '#1e293b', # Dark gray
            'text_secondary': '#64748b' # Medium gray
        }

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.simulator_path = simulator_path
        self.simulator_process = simulator_process

        # Initialize the logic handler before setting up UI
        self.logic_handler = LogicHandler(self, env_file_path, proc_file_path, simulator_path, simulator_process)

        self.setup_modern_ui()

    def setup_modern_ui(self):
        # Main container with padding
        self.main_container = ctk.CTkFrame(self.app, fg_color=self.colors['surface'])
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header Section
        self.create_header()
        
        # Configuration Section
        self.create_configuration_section()
        
        # Main Content Area
        self.create_main_content()

    def create_header(self):
        """Create modern header with gradient-like styling"""
        self.header_frame = ctk.CTkFrame(
            self.main_container, 
            height=80,
            fg_color=self.colors['primary'],
            corner_radius=15
        )
        self.header_frame.pack(fill="x", pady=(0, 20))
        self.header_frame.pack_propagate(False)

        # Title with icon
        self.title_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_frame.pack(side="left", fill="y", padx=30, pady=15)
        
        self.title = ctk.CTkLabel(
            self.title_frame, 
            text="🧠 Memulatrix", 
            font=("Segoe UI", 28, "bold"),
            text_color="white"
        )
        self.title.pack(side="top", anchor="w")
        self.subtitle = ctk.CTkLabel(
            self.title_frame,
            text="Virtual Memory Simulator",
            font=("Segoe UI", 14),
            text_color="#e2e8f0"
        )
        self.subtitle.pack(side="top", anchor="w")        
        
        # Header controls
        self.header_controls = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.header_controls.pack(side="right", fill="y", padx=30, pady=20)
        self.theme_toggle = ctk.CTkButton(
            self.header_controls,
            text="🌙 Dark Mode",
            command=self.toggle_theme,
            fg_color="#ffffff",         # white with transparency handled by CustomTkinter
            hover_color="#e6e6e6",      # slightly darker white for hover
            border_width=1,
            border_color="#e0e0e0",     # light gray border
            corner_radius=10,
            font=("Segoe UI", 12)
        )
        self.theme_toggle.pack(pady=5)

    def create_configuration_section(self):
        """Create modern configuration cards"""
        self.config_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.config_container.pack(fill="x", pady=(0, 20))

        # Configuration title
        config_title = ctk.CTkLabel(
            self.config_container,
            text="⚙️ System Configuration",
            font=("Segoe UI", 20, "bold"),
            text_color=self.colors['text_primary']
        )
        config_title.pack(anchor="w", pady=(0, 15))

        # Cards container
        self.cards_frame = ctk.CTkFrame(self.config_container, fg_color="transparent")
        self.cards_frame.pack(fill="x")
        self.cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # RAM & Storage Card
        self.create_ram_card()
        
        # Memory Settings Card  
        self.create_memory_card()
        
        # Process Management Card
        self.create_process_card()

    def create_ram_card(self):
        """Create RAM & Storage configuration card"""
        self.ram_card = ctk.CTkFrame(
            self.cards_frame,
            fg_color=self.colors['card'],
            corner_radius=15,
            border_width=1,
            border_color="#e2e8f0"
        )
        self.ram_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Card header
        header = ctk.CTkFrame(self.ram_card, fg_color=self.colors['primary'], corner_radius=10)
        header.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header,
            text="💾 RAM & Storage",
            font=("Segoe UI", 16, "bold"),
            text_color="white"
        ).pack(pady=10)

        # Card content
        content = ctk.CTkFrame(self.ram_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # RAM Size
        self.create_setting_row(content, "RAM Size (GB):", "ram")
        self.ram_size_var = ctk.StringVar(value="1")
        ram_sizes = ["1", "2"] + [str(i) for i in range(4, 65, 4)]
        self.ram_dropdown = ctk.CTkOptionMenu(
            content,
            values=ram_sizes,
            variable=self.ram_size_var,
            command=self.logic_handler.update_options,
            fg_color=self.colors['primary'],
            button_color=self.colors['primary'],
            corner_radius=8
        )
        self.ram_dropdown.pack(pady=(5, 15), padx=10, fill="x")

        # ROM Size
        self.create_setting_row(content, "ROM Size:", "storage")
        self.rom_size_var = ctk.StringVar(value="32 GB")
        rom_sizes = ["32 GB", "64 GB", "128 GB", "256 GB", "512 GB", "1 TB", "2 TB", "4 TB"]
        self.rom_size_menu = ctk.CTkOptionMenu(
            content,
            values=rom_sizes,
            variable=self.rom_size_var,
            fg_color=self.colors['secondary'],
            button_color=self.colors['secondary'],
            corner_radius=8
        )
        self.rom_size_menu.pack(pady=(5, 15), padx=10, fill="x")

        # Swap Size with modern slider
        self.create_setting_row(content, "Swap Size (%):", "swap")
        self.swap_percent_var = ctk.DoubleVar(value=0)
        
        slider_frame = ctk.CTkFrame(content, fg_color="transparent")
        slider_frame.pack(fill="x", padx=10, pady=5)
        
        self.swap_slider = ctk.CTkSlider(
            slider_frame,
            from_=0,
            to=20,
            number_of_steps=20,
            variable=self.swap_percent_var,
            progress_color=self.colors['warning'],
            button_color=self.colors['warning']
        )
        self.swap_slider.pack(side="left", fill="x", expand=True)
        
        self.swap_label = ctk.CTkLabel(
            slider_frame,
            text=f"{self.swap_percent_var.get():.0f}%",
            font=("Segoe UI", 12, "bold"),
            text_color=self.colors['warning'],
            width=40
        )
        self.swap_label.pack(side="right", padx=(10, 0))
        self.swap_percent_var.trace_add("write", self.update_swap_label)

    def create_memory_card(self):
        """Create Memory Settings card"""
        self.memory_card = ctk.CTkFrame(
            self.cards_frame,
            fg_color=self.colors['card'],
            corner_radius=15,
            border_width=1,
            border_color="#e2e8f0"
        )
        self.memory_card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Card header
        header = ctk.CTkFrame(self.memory_card, fg_color=self.colors['secondary'], corner_radius=10)
        header.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header,
            text="⚡ Memory Settings",
            font=("Segoe UI", 16, "bold"),
            text_color="white"
        ).pack(pady=10)

        # Card content
        content = ctk.CTkFrame(self.memory_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Page Size
        self.create_setting_row(content, "Page Size (KB):", "page")
        self.page_size_var = ctk.StringVar()
        self.page_size_menu = ctk.CTkOptionMenu(
            content,
            values=[],
            variable=self.page_size_var,
            state="disabled",
            corner_radius=8
        )
        self.page_size_menu.pack(pady=(5, 15), padx=10, fill="x")

        # TLB Size
        self.create_setting_row(content, "TLB Size:", "tlb")
        self.tlb_size_var = ctk.StringVar()
        self.tlb_size_menu = ctk.CTkOptionMenu(
            content,
            values=[],
            variable=self.tlb_size_var,
            state="disabled",
            corner_radius=8
        )
        self.tlb_size_menu.pack(pady=(5, 15), padx=10, fill="x")

        # TLB Checkbox with modern styling
        self.tlb_enabled_var = ctk.BooleanVar()
        self.tlb_checkbox = ctk.CTkCheckBox(
            content,
            text="Enable TLB Usage",
            variable=self.tlb_enabled_var,
            font=("Segoe UI", 12),
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=5
        )
        self.tlb_checkbox.pack(pady=10, padx=10, anchor="w")

        # Virtual Address Size
        self.create_setting_row(content, "Virtual Address Size:", "address")
        self.va_size_var = ctk.StringVar(value="16-bit")
        self.va_size_menu = ctk.CTkOptionMenu(
            content,
            values=["16-bit"],
            variable=self.va_size_var,
            corner_radius=8
        )
        self.va_size_menu.pack(pady=(5, 15), padx=10, fill="x")

        # Memory Allocation Type
        self.create_setting_row(content, "Memory Allocation:", "allocation")
        self.memory_allocation_var = ctk.StringVar(value="Contiguous")
        self.memory_allocation_menu = ctk.CTkOptionMenu(
            content,
            values=["Contiguous", "Non-Contiguous"],
            variable=self.memory_allocation_var,
            corner_radius=8
        )
        self.memory_allocation_menu.pack(pady=(5, 15), padx=10, fill="x")

        # Configuration button with modern styling
        self.config_button = ctk.CTkButton(
            content,
            text="✅ Set Configuration",
            command=self.logic_handler.set_configuration,
            fg_color=self.colors['success'],
            hover_color="#047857",
            corner_radius=10,
            height=40,
            font=("Segoe UI", 12, "bold")
        )
        self.config_button.pack(pady=15, padx=10, fill="x")

    def create_process_card(self):
        """Create Process Management card"""
        self.process_card = ctk.CTkFrame(
            self.cards_frame,
            fg_color=self.colors['card'],
            corner_radius=15,
            border_width=1,
            border_color="#e2e8f0"
        )
        self.process_card.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        # Card header
        header = ctk.CTkFrame(self.process_card, fg_color=self.colors['success'], corner_radius=10)
        header.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header,
            text="🔧 Add Process",
            font=("Segoe UI", 16, "bold"),
            text_color="white"
        ).pack(pady=10)

        # Card content
        content = ctk.CTkFrame(self.process_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Process Name
        self.create_setting_row(content, "Process Name:", "name")
        self.process_name_entry = ctk.CTkEntry(
            content,
            placeholder_text="e.g., Process1",
            corner_radius=8,
            height=35,
            font=("Segoe UI", 12)
        )
        self.process_name_entry.pack(pady=(5, 15), padx=10, fill="x")

        # Process Size
        self.create_setting_row(content, "Size (GB):", "size")
        self.process_size_entry = ctk.CTkEntry(
            content,
            placeholder_text="e.g., 1",
            corner_radius=8,
            height=35,
            font=("Segoe UI", 12)
        )
        self.process_size_entry.pack(pady=(5, 15), padx=10, fill="x")

        # Process Type
        self.create_setting_row(content, "Process Type:", "type")
        self.process_type_var = ctk.StringVar(value="User")
        self.process_type_menu = ctk.CTkOptionMenu(
            content,
            values=["User", "System"],
            variable=self.process_type_var,
            command=self.logic_handler.toggle_system_dropdown,
            corner_radius=8
        )
        self.process_type_menu.pack(pady=(5, 15), padx=10, fill="x")

        # System Process dropdown (initially hidden)
        self.system_process_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.create_setting_row(self.system_process_frame, "System Process:", "system")
        self.system_process_var = ctk.StringVar(value="kernel")
        system_processes = ["kernel", "scheduler", "memory_manager", "file_system", "network_stack"]
        self.system_process_menu = ctk.CTkOptionMenu(
            self.system_process_frame,
            values=system_processes,
            variable=self.system_process_var,
            corner_radius=8
        )
        self.system_process_menu.pack(pady=(5, 15), padx=10, fill="x")

        # Action buttons with modern styling
        self.button_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.button_frame.pack(fill="x", pady=10)

        self.add_process_button = ctk.CTkButton(
            self.button_frame,
            text="➕ Add Process",
            command=self.logic_handler.save_process,
            fg_color=self.colors['primary'],
            hover_color="#1d4ed8",
            corner_radius=8,
            height=35,
            font=("Segoe UI", 11, "bold")
        )
        self.add_process_button.pack(side="top", fill="x", padx=10, pady=5)

        self.confirm_process_button = ctk.CTkButton(
            self.button_frame,
            text="🚀 Start Simulation",
            command=self.logic_handler.confirm_processes,
            state="disabled",
            fg_color=self.colors['warning'],
            hover_color="#b45309",
            corner_radius=8,
            height=35,
            font=("Segoe UI", 11, "bold")
        )
        self.confirm_process_button.pack(side="top", fill="x", padx=10, pady=5)

        self.logic_handler.disable_process_add_section()

    def create_main_content(self):
        """Create main content area with modern tabbed interface"""
        # Create a modern tabview
        self.main_tabview = ctk.CTkTabview(
            self.main_container,
            corner_radius=15,
            border_width=1,
            border_color="#e2e8f0"
        )
        self.main_tabview.pack(fill="both", expand=True)
        
        # Create tabs with icons
        self.processes_tab = self.main_tabview.add("📋 Active Processes")
        self.results_tab = self.main_tabview.add("📊 Simulation Results")
        
        # Set processes as the default tab
        self.main_tabview.set("📋 Active Processes")
        
        # Setup processes tab
        self.setup_processes_tab()
        
        # Setup results tab
        self.setup_results_tab()

    def setup_processes_tab(self):
        """Setup the processes tab with modern styling"""
        # Main container for processes
        self.outer_frame = ctk.CTkFrame(
            self.processes_tab,
            fg_color=self.colors['surface'],
            corner_radius=10
        )
        self.outer_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header for processes section
        processes_header = ctk.CTkFrame(self.outer_frame, fg_color="transparent")
        processes_header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            processes_header,
            text="📋 Active Processes",
            font=("Segoe UI", 20, "bold"),
            text_color=self.colors['text_primary']
        ).pack(side="left")

        # Process count badge
        self.process_count_label = ctk.CTkLabel(
            processes_header,
            text="0 processes",
            font=("Segoe UI", 12),
            text_color=self.colors['text_secondary'],
            fg_color="#f1f5f9",
            corner_radius=15,
            width=100,
            height=30
        )
        self.process_count_label.pack(side="right")

        # Scrollable process container
        self.process_frame_container = ctk.CTkScrollableFrame(
            self.outer_frame,
            fg_color=self.colors['card'],
            corner_radius=10
        )
        self.process_frame_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.process_container = ctk.CTkFrame(self.process_frame_container, fg_color="transparent")
        self.process_container.pack(fill="both", expand=True)

        self.process_list = []
        self.no_processes_label = ctk.CTkLabel(
            self.process_container,
            text="🔍 No active processes\nAdd a process to get started",
            font=("Segoe UI", 14),
            text_color=self.colors['text_secondary']
        )
        self.no_processes_label.pack(pady=50)

    def setup_results_tab(self):
        """Setup the results tab"""
        self.results_scrollable_frame = ctk.CTkScrollableFrame(
            self.results_tab,
            fg_color=self.colors['surface']
        )
        self.results_scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.results_frame = ctk.CTkFrame(
            self.results_scrollable_frame,
            fg_color=self.colors['card'],
            corner_radius=15
        )
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initialize the chart viewer
        self.chart_viewer = ChartViewer(self.results_frame)

    def create_setting_row(self, parent, label_text, icon_type):
        """Create a setting row with icon and label"""
        icons = {
            "ram": "💾", "storage": "💿", "swap": "🔄", "page": "📄",
            "tlb": "⚡", "address": "🏠", "allocation": "📦",
            "name": "📝", "size": "📏", "type": "🏷️", "system": "⚙️"
        }
        
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=10, pady=2)
        
        icon = icons.get(icon_type, "•")
        label = ctk.CTkLabel(
            row_frame,
            text=f"{icon} {label_text}",
            font=("Segoe UI", 12, "bold"),
            text_color=self.colors['text_primary']
        )
        label.pack(anchor="w")

    def update_swap_label(self, *args):
        """Update swap percentage label with color coding"""
        value = self.swap_percent_var.get()
        color = self.colors['success'] if value < 10 else self.colors['warning'] if value < 15 else self.colors['danger']
        self.swap_label.configure(text=f"{value:.0f}%", text_color=color)

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        if ctk.get_appearance_mode() == "Light":
            ctk.set_appearance_mode("dark")
            self.theme_toggle.configure(text="☀️ Light Mode")
        else:
            ctk.set_appearance_mode("light")
            self.theme_toggle.configure(text="🌙 Dark Mode")

    def enable_process_add_section(self):
        """Enable process addition controls"""
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
        """Disable process addition controls"""
        self.process_name_entry.configure(state="disabled")
        self.process_size_entry.configure(state="disabled")
        self.process_type_var.set("User")
        self.process_type_menu.configure(state="disabled")
        self.system_process_menu.configure(state="disabled")
        self.add_process_button.configure(state="disabled")
        self.confirm_process_button.configure(state="disabled")

    def add_process_to_list(self, process_info, process_idx, is_stopped):
        """Add process to list with modern card styling"""
        if self.no_processes_label.winfo_exists():
            self.no_processes_label.destroy()

        # Modern process card
        process_frame = ctk.CTkFrame(
            self.process_container,
            fg_color=self.colors['card'],
            corner_radius=10,
            border_width=1,
            border_color="#e2e8f0"
        )
        process_frame.pack(fill="x", padx=15, pady=8)
        
        # Process info section
        info_section = ctk.CTkFrame(process_frame, fg_color="transparent")
        info_section.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        
        # Status indicator
        status_color = self.colors['danger'] if is_stopped else self.colors['success']
        status_text = "⏸️ Stopped" if is_stopped else "▶️ Running"
        status_label = ctk.CTkLabel(
            info_section,
            text=status_text,
            font=("Segoe UI", 10, "bold"),
            text_color=status_color,
            fg_color="#f8fafc",  # Light background color
            corner_radius=12,
            width=80,
            height=24
        )
        status_label.pack(anchor="w", pady=(0, 5))
        
        info_label = ctk.CTkLabel(
            info_section,
            text=process_info,
            anchor="w",
            font=("Segoe UI", 12),
            text_color=self.colors['text_primary']
        )
        info_label.pack(anchor="w", fill="x")
        
        # Button section
        button_section = ctk.CTkFrame(process_frame, fg_color="transparent")
        button_section.pack(side="right", padx=15, pady=15)
        
        # Action button
        action_text = "▶️ Resume" if is_stopped else "⏸️ Stop"
        action_color = self.colors['success'] if is_stopped else self.colors['warning']
        process_frame.button = ctk.CTkButton(
            button_section,
            text=action_text,
            fg_color=action_color,
            hover_color=action_color,  # Same color with built-in hover effect
            width=90,
            height=32,
            corner_radius=8,
            font=("Segoe UI", 10, "bold"),
            command=lambda: self.logic_handler.resume_process(process_frame, process_idx) if is_stopped 
                           else self.logic_handler.stop_process(process_frame, process_idx)
        )
        process_frame.button.pack(side="top", pady=(0, 5))
        
        # Remove button
        remove_button = ctk.CTkButton(
            button_section,
            text="🗑️ Remove",
            fg_color=self.colors['danger'],
            hover_color=self.colors['danger'],  # Same color with built-in hover effect
            width=90,
            height=32,
            corner_radius=8,
            font=("Segoe UI", 10, "bold"),
            command=lambda: self.logic_handler.remove_process(process_frame, process_idx)
        )
        remove_button.pack(side="top")
        
        self.process_list.append((process_frame, process_idx))
        
        # Update process count
        self.update_process_count()
        
        # Enable confirm button if this is the first process
        if len(self.process_list) == 1:
            self.confirm_process_button.configure(state="normal")

    def update_process_count(self):
        """Update the process count display"""
        count = len(self.process_list)
        text = f"{count} process{'es' if count != 1 else ''}"
        self.process_count_label.configure(text=text)

    def remove_process(self, process_frame, process_id):
        """Remove process with updated styling"""
        process_frame.destroy()
        self.process_list = [(frame, pid) for frame, pid in self.process_list if pid != process_id]
        
        self.update_process_count()
        
        if not self.process_list:
            self.no_processes_label = ctk.CTkLabel(
                self.process_container,
                text="🔍 No active processes\nAdd a process to get started",
                font=("Segoe UI", 14),
                text_color=self.colors['text_secondary']
            )
            self.no_processes_label.pack(pady=50)
            self.confirm_process_button.configure(state="disabled")
            
    def toggle_system_dropdown(self, value):
        """Toggle system process dropdown visibility"""
        if value == "System":
            self.system_process_frame.pack(fill="x", pady=5)
        else:
            self.system_process_frame.pack_forget()