import tkinter as tk
from tkinter import ttk, messagebox

class VirtualMemoryUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Memory Simulator")
        self.root.geometry("400x500")

        # RAM Size Selection
        tk.Label(root, text="Select RAM Size (GB):").pack(pady=5)
        self.ram_var = tk.StringVar(value="1")
        ram_sizes = [str(i) for i in range(1, 65)]  # 1GB to 64GB
        ram_menu = ttk.Combobox(root, textvariable=self.ram_var, values=ram_sizes)
        ram_menu.pack(pady=5)
        ram_menu.bind("<<ComboboxSelected>>", self.update_options)

        # Page Size and TLB Size Options
        self.page_var = tk.StringVar()
        self.tlb_var = tk.StringVar()
        tk.Label(root, text="Select Page Size:").pack(pady=5)
        self.page_menu = ttk.Combobox(root, textvariable=self.page_var, state="disabled")
        self.page_menu.pack(pady=5)
        tk.Label(root, text="Select TLB Size:").pack(pady=5)
        self.tlb_menu = ttk.Combobox(root, textvariable=self.tlb_var, state="disabled")
        self.tlb_menu.pack(pady=5)

        # Add Process Button
        tk.Button(root, text="Add Process", command=self.add_process_dialog).pack(pady=10)

        # TLB Usage Checkbox
        self.tlb_check = tk.BooleanVar()
        tk.Checkbutton(root, text="Enable TLB Usage", variable=self.tlb_check).pack(pady=5)

        # Initial update
        self.update_options(None)

    def update_options(self, event):
        ram_gb = int(self.ram_var.get())
        ram_bytes = ram_gb * 1024 * 1024 * 1024

        # Calculate possible page sizes based on RAM (e.g., powers of 2 up to 1/1024 of RAM)
        page_sizes = [2**i for i in range(12, 22) if 2**i <= ram_bytes // 1024]
        page_options = [f"{size//1024}KB" for size in page_sizes]
        self.page_menu['values'] = page_options
        self.page_menu['state'] = "readonly" if page_options else "disabled"
        self.page_var.set(page_options[0] if page_options else "")

        # TLB sizes based on page sizes (e.g., 16 to 64 entries)
        tlb_options = ["16", "32", "64"]
        self.tlb_menu['values'] = tlb_options
        self.tlb_menu['state'] = "readonly" if page_options else "disabled"
        self.tlb_var.set(tlb_options[0] if tlb_options else "")

    def add_process_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Process")
        dialog.geometry("300x200")

        tk.Label(dialog, text="Process ID:").pack(pady=5)
        pid_entry = tk.Entry(dialog)
        pid_entry.pack(pady=5)

        tk.Label(dialog, text="Name:").pack(pady=5)
        name_entry = tk.Entry(dialog)
        name_entry.pack(pady=5)

        tk.Label(dialog, text="Type:").pack(pady=5)
        type_var = tk.StringVar(value="User")
        type_menu = ttk.Combobox(dialog, textvariable=type_var, values=["User", "System"])
        type_menu.pack(pady=5)

        tk.Label(dialog, text="Priority:").pack(pady=5)
        priority_entry = tk.Entry(dialog)
        priority_entry.pack(pady=5)

        def save_process():
            pid = pid_entry.get()
            name = name_entry.get()
            process_type = type_var.get()
            priority = priority_entry.get()
            if pid and name and priority:
                messagebox.showinfo("Success", f"Added Process: ID={pid}, Name={name}, Type={process_type}, Priority={priority}")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "All fields are required!")

        tk.Button(dialog, text="Save", command=save_process).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualMemoryUI(root)
    root.mainloop()