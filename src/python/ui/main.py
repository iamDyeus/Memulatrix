import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random

def create_graph(title, x, y):
    fig, ax = plt.subplots(figsize=(4, 3))  # Reduced from (6, 4)
    ax.plot(x, y)
    ax.set_title(title, fontsize=8)  # Smaller font size
    ax.grid(True)
    plt.tight_layout()
    return fig

# Initialize customtkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# App window
app = ctk.CTk()
app.title("Memulatrix - The Virtual Memory Simulator")
app.iconbitmap("./assets/app_icon.ico")  # Add app icon
app.state('zoomed')  # Fullscreen on start
app.resizable(False, False)

# Header frame for title and theme toggle
header_frame = ctk.CTkFrame(app, fg_color="transparent")  # Transparent background
header_frame.pack(pady=10, padx=20, fill="x")

# Title in header frame
title = ctk.CTkLabel(header_frame, text="Memulatrix", font=("Arial", 28, "bold"))
title.pack(side="left", padx=20)

# Theme toggle in header frame
def toggle_theme():
    if ctk.get_appearance_mode() == "Light":
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")

theme_toggle = ctk.CTkButton(header_frame, text="Toggle Theme", command=toggle_theme)
theme_toggle.pack(side="right", padx=20)

# Frame for settings (RAM, Memory, Process)
settings_frame = ctk.CTkFrame(app)
settings_frame.pack(pady=(5, 10), padx=20, fill="x")

# Sub-frames inside settings
ram_frame = ctk.CTkFrame(settings_frame)
ram_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

memory_frame = ctk.CTkFrame(settings_frame)
memory_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

process_frame = ctk.CTkFrame(settings_frame)
process_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

# RAM Frame contents
ctk.CTkLabel(ram_frame, text="RAM Size", font=("Arial", 16)).pack(pady=5)
ram_dropdown = ctk.CTkOptionMenu(ram_frame, values=["4 GB", "8 GB", "16 GB"])
ram_dropdown.set("8 GB")
ram_dropdown.pack(pady=5)

# Memory Frame contents
ctk.CTkLabel(memory_frame, text="Memory Settings", font=("Arial", 16)).pack(pady=5)
page_size_dropdown = ctk.CTkOptionMenu(memory_frame, values=["4 KB", "8 KB", "16 KB"])
page_size_dropdown.set("4 KB")
page_size_dropdown.pack(pady=5)

tlb_size_entry = ctk.CTkEntry(memory_frame, placeholder_text="TLB Size")
tlb_size_entry.pack(pady=5)

tlb_checkbox = ctk.CTkCheckBox(memory_frame, text="Enable TLB Usage")
tlb_checkbox.pack(pady=5)

# Process Frame contents
ctk.CTkLabel(process_frame, text="Add Process", font=("Arial", 16)).pack(pady=5)
process_id_entry = ctk.CTkEntry(process_frame, placeholder_text="Process ID")
process_id_entry.pack(pady=5)

name_entry = ctk.CTkEntry(process_frame, placeholder_text="Name")
name_entry.pack(pady=5)

type_dropdown = ctk.CTkOptionMenu(process_frame, values=["System", "User"])
type_dropdown.set("Type")
type_dropdown.pack(pady=5)

priority_entry = ctk.CTkEntry(process_frame, placeholder_text="Priority")
priority_entry.pack(pady=5)

add_process_btn = ctk.CTkButton(process_frame, text="Add Process")
add_process_btn.pack(pady=5)

# Frame for Graphs
outer_frame = ctk.CTkFrame(app)
# Configure outer frame to expand
outer_frame.pack(padx=10, pady=10, fill="both", expand=True)

# Create scrollable frame
scrollable_frame = ctk.CTkScrollableFrame(outer_frame, height=350)  
scrollable_frame.pack(fill="both", expand=True) 

# Adjust scroll speed
def mouse_scroll(event):
    if event.delta:
        scrollable_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / 2.4)), "units") 
    else:
        if event.num == 5:
            scrollable_frame._parent_canvas.yview_scroll(25, "units") 
        else:
            scrollable_frame._parent_canvas.yview_scroll(-25, "units")  

# Bind mousewheel for Windows and Linux/Mac
scrollable_frame.bind_all("<MouseWheel>", mouse_scroll)  # Windows
scrollable_frame.bind_all("<Button-4>", mouse_scroll)    # Linux/Mac scroll up
scrollable_frame.bind_all("<Button-5>", mouse_scroll)    # Linux/Mac scroll down

# Random data
x = list(range(10))
y1 = [random.randint(0, 10) for _ in range(10)]
y2 = [random.randint(0, 5) for _ in range(10)]
y3 = [random.randint(5, 15) for _ in range(10)]
y4 = [random.randint(2, 8) for _ in range(10)]
y5 = [random.randint(0, 20) for _ in range(10)]
y6 = [random.randint(1, 7) for _ in range(10)]

# List of graphs
graph_titles = [
    "Memory Usage Over Time", 
    "Page Faults", 
    "TLB Hit/Miss Rates", 
    "CPU Usage", 
    "Disk I/O Over Time", 
    "Network Activity"
]
graph_data = [y1, y2, y3, y4, y5, y6]

# Display graphs in grid (2 graphs per row)
row = 0
col = 0
for i in range(6):
    fig = create_graph(graph_titles[i], x, graph_data[i])
    canvas = FigureCanvasTkAgg(fig, master=scrollable_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")  # Added sticky
    
    # Configure grid weights for the current row and column
    scrollable_frame.grid_columnconfigure(col, weight=1)
    scrollable_frame.grid_rowconfigure(row, weight=1)

    col += 1
    if col > 1:
        col = 0
        row += 1

# Run the app
app.mainloop()
