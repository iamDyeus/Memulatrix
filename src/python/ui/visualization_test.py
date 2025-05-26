"""
Test file to verify chart visualization works correctly.
Run this script directly to test the chart visualization with the simulated data.
"""

import sys
import os
import customtkinter as ctk

# Add the parent directory to the path so we can import from it
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the visualization module
from ui.visualization import ChartViewer

class TestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chart Viewer Test")
        self.root.geometry("900x700")

        # Frame for charts
        self.charts_frame = ctk.CTkFrame(self.root)
        self.charts_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Create the chart viewer
        self.chart_viewer = ChartViewer(self.charts_frame)

        # Button to create charts
        self.create_btn = ctk.CTkButton(
            self.root, 
            text="Create Charts", 
            command=self.create_charts
        )
        self.create_btn.pack(pady=(0, 10))

    def create_charts(self):
        # Get the path to simulation_results.json
        results_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "bin", "simulation_results.json")

        if not os.path.exists(results_path):
            print(f"Results file not found at {results_path}")
            return

        # Create the charts
        success = self.chart_viewer.create_charts(results_path)
        print(f"Charts created: {success}")

if __name__ == "__main__":
    app = ctk.CTk()
    test_app = TestApp(app)
    app.mainloop()
