import tkinter as tk
from tkinter import ttk, messagebox

class VirtualMemoryUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Memory Simulator")
        self.root.geometry("600x500")
        self.root.configure(bg="#f0f4f8")  # Light background

        # Style configuration
        style = ttk.Style()
        style.configure("TLabel", font=("Helvetica", 10), background="#f0f4f8")
        style.configure("TCombobox", font=("Helvetica", 10))
        style.configure("TButton", font=("Helvetica", 10, "bold"))
        style.configure("TCheckbutton", background="#f0f4f8", font=("Helvetica", 10))

        # Title
        tk.Label(root, text="Virtual Memory Simulator", font=("Helvetica", 16, "bold"), bg="#f0f4f8", fg="#2c3e50").pack(pady=15)

        # Main Frame to hold all sections side by side
        main_frame = tk.Frame(root, bg="#f0f4f8")
        main_frame.pack(pady=10, padx=10, fill="x")

        # RAM Selection Frame
        ram_frame = tk.Frame(main_frame, bg="#dfe6e9", padx=10, pady=10, relief="groove", borderwidth=2)
        ram_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        tk.Label(ram_frame, text="RAM Size", font=("Helvetica", 11, "bold"), bg="#dfe6e9", fg="#2d3436").pack(anchor="w")
        tk.Label(ram_frame, text="Select RAM Size (GB):", bg="#dfe6e9").pack(anchor="w")
        self.ram_var = tk.StringVar(value="1")
        ram_sizes = ["1", "2"] + [str(i) for i in range(4, 65, 4)]  # 1GB, 2GB, then multiples of 4GB
        ram_menu = ttk.Combobox(ram_frame, textvariable=self.ram_var, values=ram_sizes, width=15)
        ram_menu.pack(pady=5)
        ram_menu.bind("<<ComboboxSelected>>", self.update_options)

        # Memory Settings Frame
        size_frame = tk.Frame(main_frame, bg="#dfe6e9", padx=10, pady=10, relief="groove", borderwidth=2)
        size_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        tk.Label(size_frame, text="Memory Settings", font=("Helvetica", 11, "bold"), bg="#dfe6e9", fg="#2d3436").pack(anchor="w")
        tk.Label(size_frame, text="Page Size (KB):", bg="#dfe6e9").pack(anchor="w", pady=2)
        self.page_var = tk.StringVar()
        self.page_menu = ttk.Combobox(size_frame, textvariable=self.page_var, state="disabled", width=15)
        self.page_menu.pack(pady=5)
        tk.Label(size_frame, text="TLB Size:", bg="#dfe6e9").pack(anchor="w", pady=2)
        self.tlb_var = tk.StringVar()
        self.tlb_menu = ttk.Combobox(size_frame, textvariable=self.tlb_var, state="disabled", width=15)
        self.tlb_menu.pack(pady=5)
        self.tlb_check = tk.BooleanVar()  # Initialize here
        tk.Checkbutton(size_frame, text="Enable TLB Usage", variable=self.tlb_check).pack(anchor="w", pady=5)

        # Process Addition Frame
        process_frame = tk.Frame(main_frame, bg="#dfe6e9", padx=10, pady=10, relief="groove", borderwidth=2)
        process_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        tk.Label(process_frame, text="Add Process", font=("Helvetica", 11, "bold"), bg="#dfe6e9", fg="#2d3436").pack(anchor="w")
        tk.Label(process_frame, text="Process ID:", bg="#dfe6e9").pack(anchor="w", pady=2)
        self.pid_entry = tk.Entry(process_frame, width=20)
        self.pid_entry.pack(pady=5)
        tk.Label(process_frame, text="Name:", bg="#dfe6e9").pack(anchor="w", pady=2)
        self.name_entry = tk.Entry(process_frame, width=20)
        self.name_entry.pack(pady=5)
        tk.Label(process_frame, text="Type:", bg="#dfe6e9").pack(anchor="w", pady=2)
        self.type_var = tk.StringVar(value="User")
        type_menu = ttk.Combobox(process_frame, textvariable=self.type_var, values=["User", "System"], width=17)
        type_menu.pack(pady=5)
        tk.Label(process_frame, text="Priority:", bg="#dfe6e9").pack(anchor="w", pady=2)
        self.priority_entry = tk.Entry(process_frame, width=20)
        self.priority_entry.pack(pady=5)
        tk.Button(process_frame, text="Add Process", bg="#0984e3", fg="white", command=self.save_process).pack(pady=10)

        # Configure grid weights for responsive layout
        main_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Initial update
        self.update_options(None)

    def update_options(self, event):
        ram_gb = int(self.ram_var.get())
        ram_bytes = ram_gb * 1024 * 1024 * 1024

        # Calculate possible page sizes based on RAM
        page_sizes = [2**i for i in range(12, 22) if 2**i <= ram_bytes // 1024]
        page_options = [f"{size//1024}KB" for size in page_sizes]
        self.page_menu['values'] = page_options
        self.page_menu['state'] = "readonly" if page_options else "disabled"
        self.page_var.set(page_options[0] if page_options else "")

        # TLB sizes
        tlb_options = ["16KB", "32KB", "64KB"]
        self.tlb_menu['values'] = tlb_options
        self.tlb_menu['state'] = "readonly" if page_options else "disabled"
        self.tlb_var.set(tlb_options[0] if tlb_options else "")

    def save_process(self):
        pid = self.pid_entry.get()
        name = self.name_entry.get()
        process_type = self.type_var.get()
        priority = self.priority_entry.get()
        if pid and name and priority:
            messagebox.showinfo("Success", f"Added Process: ID={pid}, Name={name}, Type={process_type}, Priority={priority}")
            self.pid_entry.delete(0, tk.END)
            self.name_entry.delete(0, tk.END)
            self.priority_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "All fields are required!")

if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualMemoryUI(root)
    root.mainloop()