import os
import sys
import json
import time
import subprocess
import customtkinter as ctk
from ui.input_ui import VirtualMemoryUI
from ui.input_ui_constraints import LogicHandler, CustomMessageBox

class AppManager:
    def __init__(self):
        self.root = ctk.CTk()
        self.ui = VirtualMemoryUI(self.root)
        self.bin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), r"..\..\bin"))
        self.env_file_path = os.path.join(self.bin_dir, "environment_settings.json")
        self.proc_file_path = os.path.join(self.bin_dir, "processes.json")
        self.result_path = os.path.join(self.bin_dir, "result.json")
        self.simulator_path = os.path.join(self.bin_dir, "virtual_memory_simulator.exe")
        self.ui.logic_handler = LogicHandler(self.ui, self.env_file_path, self.proc_file_path)

    def run(self):
        print("Starting UI...")
        self.root.mainloop()
        print("Closing application...")

if __name__ == "__main__":
    app = AppManager()
    app.run()