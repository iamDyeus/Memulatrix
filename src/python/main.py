import customtkinter as ctk
import subprocess
import os
import time
from ui.input_ui import VirtualMemoryUI

class AppManager:
    def __init__(self):
        self.root = ctk.CTk()
        self.simulator_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "bin", "virtual_memory_simulator.exe"))
        self.simulator_process = None
        # Don't start the simulator automatically - wait for user to click "Confirm Processes"
        self.ui = VirtualMemoryUI(
            self.root,
            env_file_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "bin", "environment.json")),
            proc_file_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "bin", "processes.json")),
            simulator_path=self.simulator_path,
            simulator_process=self.simulator_process
        )

    def start_simulator(self):
        if not os.path.exists(self.simulator_path):
            print(f"Error: Simulator not found at {self.simulator_path}")
            return
        print("Simulator started. Waiting for initialization...")
        try:
            self.simulator_process = subprocess.Popen(self.simulator_path, shell=True)
            time.sleep(2.0)
            print("Simulator running.")
        except Exception as e:
            print(f"Error starting simulator: {e}")

    def run(self):
        print("Starting UI...")
        self.root.mainloop()

if __name__ == "__main__":
    app = AppManager()
    app.run()