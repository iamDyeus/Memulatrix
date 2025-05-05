import os
import customtkinter as ctk
from ui.input_ui import VirtualMemoryUI

class AppManager:
    def __init__(self):
        # Explicitly set the working directory to the script's directory
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(self.script_dir)

        # Define relative paths for JSON files (relative to D:\projects\Memulatrix\src\python)
        self.bin_dir = r"..\..\bin"
        self.env_file_path = os.path.join(self.bin_dir, "environment_settings.json")
        self.proc_file_path = os.path.join(self.bin_dir, "processes.json")

        # Create bin directory if it doesn't exist
        if not os.path.exists(self.bin_dir):
            os.makedirs(self.bin_dir)

        # Initialize UI
        self.app = ctk.CTk()
        self.ui = VirtualMemoryUI(self.app, env_file_path=self.env_file_path, proc_file_path=self.proc_file_path)

        # Bind the closing event
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        print("Closing application...")
        # Call the UI's on_closing method to clean up JSON files
        self.ui.logic_handler.on_closing()
        self.app.destroy()

    def run(self):
        print("Starting UI...")
        self.app.mainloop()

def main():
    app_manager = AppManager()
    app_manager.run()

if __name__ == "__main__":
    main()