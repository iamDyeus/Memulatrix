import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

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
        tk.Label(ram_selection_frame, text="RAM Size", font=("Helvetica", 11, "bold"), bg="lightskyblue", fg="darkslategray").pack(anchor="w")
        tk.Label(ram_selection_frame, text="Select RAM Size (GB):", bg="lightskyblue").pack(anchor="w")
        self.ram_size_var = tk.StringVar(value="1")
        ram_sizes = ["1", "2"] + [str(i) for i in range(4, 65, 4)]
        ram_menu = ttk.Combobox(ram_selection_frame, textvariable=self.ram_size_var, values=ram_sizes, width=15)
        ram_menu.pack(pady=5)
        ram_menu.bind("<<ComboboxSelected>>", self.update_options)

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

        # Process Addition Frame
        process_add_frame = tk.Frame(main_frame, bg="lightskyblue", padx=10, pady=10, relief="groove", borderwidth=2)
        process_add_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        tk.Label(process_add_frame, text="Add Process", font=("Helvetica", 11, "bold"), bg="lightskyblue", fg="darkslategray").pack(anchor="w")
        
        # Process Name
        tk.Label(process_add_frame, text="Name:", bg="lightskyblue").pack(anchor="w", pady=2)
        self.process_name_entry = tk.Entry(process_add_frame, width=20, fg="gray")
        self.process_name_entry.insert(0, "e.g., Process1")
        self.process_name_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(self.process_name_entry, "e.g., Process1"))
        self.process_name_entry.bind("<FocusOut>", lambda e: self.add_placeholder(self.process_name_entry, "e.g., Process1"))
        self.process_name_entry.pack(pady=5)

        # Process Size
        tk.Label(process_add_frame, text="Size (GB):", bg="lightskyblue").pack(anchor="w", pady=2)
        self.process_size_entry = tk.Entry(process_add_frame, width=20, fg="gray")
        self.process_size_entry.insert(0, "e.g., 1")
        self.process_size_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(self.process_size_entry, "e.g., 1"))
        self.process_size_entry.bind("<FocusOut>", lambda e: self.add_placeholder(self.process_size_entry, "e.g., 1"))
        self.process_size_entry.pack(pady=5)

        # Process Type
        tk.Label(process_add_frame, text="Type:", bg="lightskyblue").pack(anchor="w", pady=2)
        self.process_type_var = tk.StringVar(value="User")
        type_menu = ttk.Combobox(process_add_frame, textvariable=self.process_type_var, values=["User", "System"], width=17)
        type_menu.pack(pady=5)
        type_menu.bind("<<ComboboxSelected>>", self.toggle_system_dropdown)

        # System Process Dropdown (hidden by default)
        self.system_process_frame = tk.Frame(process_add_frame, bg="lightskyblue")
        tk.Label(self.system_process_frame, text="System Process:", bg="lightskyblue").pack(anchor="w", pady=2)
        self.system_process_var = tk.StringVar(value="kernel")
        system_processes = ["kernel", "scheduler", "memory_manager", "file_system", "network_stack"]
        self.system_process_menu = ttk.Combobox(self.system_process_frame, textvariable=self.system_process_var, values=system_processes, width=17)
        self.system_process_menu.pack(pady=5)

        # Set Priority Checkbox
        self.set_priority_var = tk.BooleanVar()
        tk.Checkbutton(process_add_frame, text="Set Priority?", variable=self.set_priority_var, bg="lightskyblue", command=self.toggle_priority_entry).pack(anchor="w", pady=5)

        # Priority Entry (hidden by default)
        self.priority_frame = tk.Frame(process_add_frame, bg="lightskyblue")
        tk.Label(self.priority_frame, text="Priority:", bg="lightskyblue").pack(anchor="w", pady=2)
        self.priority_entry = tk.Entry(self.priority_frame, width=20, fg="gray")
        self.priority_entry.insert(0, "e.g., 5")
        self.priority_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(self.priority_entry, "e.g., 5"))
        self.priority_entry.bind("<FocusOut>", lambda e: self.add_placeholder(self.priority_entry, "e.g., 5"))
        self.priority_entry.pack(pady=5)

        # Add Process Button
        tk.Button(process_add_frame, text="Add Process", bg="dodgerblue", fg="white", command=self.save_process).pack(pady=10)

        # Active Processes Frame
        active_processes_frame = tk.Frame(root, bg="lightcyan", padx=10, pady=10, relief="groove", borderwidth=2)
        active_processes_frame.pack(pady=10, padx=10, fill="both", expand=True)
        tk.Label(active_processes_frame, text="Active Processes", font=("Helvetica", 11, "bold"), bg="lightcyan", fg="darkslategray").pack(anchor="w")
        self.process_container = tk.Frame(active_processes_frame, bg="lightcyan")
        self.process_container.pack(fill="both", expand=True)
        self.process_list = []
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
        else:
            self.system_process_frame.pack_forget()

    def toggle_priority_entry(self):
        if self.set_priority_var.get():
            self.priority_frame.pack(anchor="w", pady=5)
        else:
            self.priority_frame.pack_forget()

    def update_options(self, event):
        ram_size_gb = int(self.ram_size_var.get())
        ram_bytes = ram_size_gb * 1024 * 1024 * 1024
        page_sizes = [2**i for i in range(12, 22) if 2**i <= ram_bytes // 1024]
        page_options = [f"{size//1024}KB" for size in page_sizes]
        self.page_size_menu['values'] = page_options
        self.page_size_menu['state'] = "readonly" if page_options else "disabled"
        self.page_size_var.set(page_options[0] if page_options else "")
        tlb_options = ["16", "32", "64"]
        self.tlb_size_menu['values'] = tlb_options
        self.tlb_size_menu['state'] = "readonly" if page_options else "disabled"
        self.tlb_size_var.set(tlb_options[0] if tlb_options else "")

    def load_processes_from_json(self):
        if os.path.exists("processes.json"):
            with open("processes.json", "r") as f:
                self.process_data = json.load(f)
                for proc in self.process_data:
                    process_info = f"ID: {proc['id']}, Name: {proc['name']}, Size: {proc['size_gb']}GB, Type: {proc['type']}, Priority: {proc['priority']}"
                    self.add_process_to_list(process_info)
                    self.next_process_id = max(self.next_process_id, int(proc['id']) + 1)

    def save_processes_to_json(self):
        with open("processes.json", "w") as f:
            json.dump(self.process_data, f, indent=4)

    def save_process(self):
        process_name = self.process_name_entry.get()
        process_size = self.process_size_entry.get()
        process_type = self.process_type_var.get()
        system_process = self.system_process_var.get() if process_type == "System" else None
        set_priority = self.set_priority_var.get()
        priority = self.priority_entry.get() if set_priority else "N/A"

        if (process_name in ["", "e.g., Process1"] or process_size in ["", "e.g., 1"] or (set_priority and priority in ["", "e.g., 5"])):
            messagebox.showerror("Error", "All required fields must be filled!")
            return

        # Generate process ID
        process_id = str(self.next_process_id)
        self.next_process_id += 1

        # Use system process name if type is System
        display_name = system_process if process_type == "System" else process_name
        process_info = f"ID: {process_id}, Name: {display_name}, Size: {process_size}GB, Type: {process_type}, Priority: {priority}"

        # Add to process data list
        self.process_data.append({
            "id": process_id,
            "name": display_name,
            "size_gb": int(process_size),
            "type": process_type,
            "priority": priority
        })

        # Update UI and JSON
        self.add_process_to_list(process_info)
        self.save_processes_to_json()
        messagebox.showinfo("Success", f"Added Process: {process_info}")

        # Reset fields
        self.process_name_entry.delete(0, tk.END)
        self.process_name_entry.insert(0, "e.g., Process1")
        self.process_name_entry.config(fg="gray")
        self.process_size_entry.delete(0, tk.END)
        self.process_size_entry.insert(0, "e.g., 1")
        self.process_size_entry.config(fg="gray")
        if set_priority:
            self.priority_entry.delete(0, tk.END)
            self.priority_entry.insert(0, "e.g., 5")
            self.priority_entry.config(fg="gray")

    def add_process_to_list(self, process_info):
        if self.no_processes_label.winfo_exists():
            self.no_processes_label.destroy()

        process_frame = tk.Frame(self.process_container, bg="white" if len(self.process_list) % 2 == 0 else "whitesmoke", bd=1, relief="solid")
        process_frame.pack(fill="x", pady=2)
        tk.Label(process_frame, text=process_info, font=("Helvetica", 10), bg=process_frame.cget("bg"), fg="darkslategray").pack(side="left", padx=5, pady=5)
        tk.Button(process_frame, text="Remove", bg="salmon", fg="white", font=("Helvetica", 8, "bold"), command=lambda: self.remove_process(process_frame)).pack(side="right", padx=5)
        tk.Button(process_frame, text="Stop", bg="orange", fg="white", font=("Helvetica", 8, "bold"), command=lambda: self.stop_process(process_frame)).pack(side="right", padx=5)
        self.process_list.append(process_frame)

    def remove_process(self, process_frame):
        # Find the index of the process to remove
        idx = self.process_list.index(process_frame)
        self.process_data.pop(idx)
        process_frame.destroy()
        self.process_list.remove(process_frame)
        if not self.process_list:
            self.no_processes_label = tk.Label(self.process_container, text="No active processes", font=("Helvetica", 10, "italic"), bg="lightcyan", fg="gray")
            self.no_processes_label.pack(pady=20)
        self.save_processes_to_json()

    def stop_process(self, process_frame):
        messagebox.showinfo("Info", "Process stopped (functionality to be implemented)")

if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualMemoryUI(root)
    root.mainloop()