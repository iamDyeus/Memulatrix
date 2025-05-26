import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk
import json
import os

class ChartViewer:
    def __init__(self, parent):
        """Initialize the chart viewer with a parent widget"""
        self.parent = parent
        self.charts = {}

    def create_charts(self, results_path):
        """Create all simulation result charts"""
        if not os.path.exists(results_path):
            return False
        
        try:
            with open(results_path, 'r') as f:
                results = json.load(f)
            
            # First destroy any existing charts properly
            self.destroy_charts()
            
            # Create a tab view for the charts
            self.tab_view = ctk.CTkTabview(self.parent)
            self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Create tabs for each chart
            self.tlb_hits_tab = self.tab_view.add("TLB Hits")
            self.tlb_rate_tab = self.tab_view.add("TLB Hit Rate")
            self.page_faults_tab = self.tab_view.add("Page Faults")
            self.ram_usage_tab = self.tab_view.add("RAM Occupancy")
            
            # Create the charts
            self.create_tlb_hits_chart(self.tlb_hits_tab, results)
            self.create_tlb_hit_rate_chart(self.tlb_rate_tab, results)
            self.create_page_faults_chart(self.page_faults_tab, results)
            self.create_ram_occupancy_chart(self.ram_usage_tab, results)
            
            return True
        except Exception as e:
            print(f"Error creating charts: {e}")
            return False

    def create_tlb_hits_chart(self, parent, results):
        """Create TLB hits vs time chart"""
        # Extract data
        if 'tlb_stats' not in results or 'hits' not in results['tlb_stats']:
            return
        
        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        
        # Process the data
        tlb_hits_data = results['tlb_stats']['hits']
        process_ids = list(set([entry[0] for entry in tlb_hits_data]))
        
        # Create time steps (we don't have actual time in the data)
        for pid in process_ids:
            hits = [entry[1] for entry in tlb_hits_data if entry[0] == pid]
            times = list(range(len(hits)))
            ax.plot(times, hits, marker='o', label=f"Process {pid}")
        
        ax.set_title('TLB Hits vs Time')
        ax.set_xlabel('Time Steps')
        ax.set_ylabel('Number of TLB Hits')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True)
        canvas.draw()
        
        self.charts['tlb_hits'] = canvas_widget
    
    def create_tlb_hit_rate_chart(self, parent, results):
        """Create TLB hit rate chart"""
        # Extract data
        if 'tlb_stats' not in results or 'hit_rate' not in results['tlb_stats']:
            return
        
        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        
        # Process the data
        tlb_hit_rate_data = results['tlb_stats']['hit_rate']
        process_ids = list(set([entry[0] for entry in tlb_hit_rate_data]))
        
        for pid in process_ids:
            hit_rates = [entry[1] * 100 for entry in tlb_hit_rate_data if entry[0] == pid]  # Convert to percentage
            times = list(range(len(hit_rates)))
            ax.plot(times, hit_rates, marker='o', label=f"Process {pid}")
        
        ax.set_title('TLB Hit Rate Over Time')
        ax.set_xlabel('Time Steps')
        ax.set_ylabel('Hit Rate (%)')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_ylim(0, 100)
        ax.legend()
        
        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True)
        canvas.draw()
        
        self.charts['tlb_hit_rate'] = canvas_widget
    
    def create_page_faults_chart(self, parent, results):
        """Create page faults vs time chart"""
        # Extract data
        if 'page_faults' not in results:
            return
        
        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        
        # Process the data
        page_faults_data = results['page_faults']
        process_ids = list(set([entry[0] for entry in page_faults_data]))
        
        for pid in process_ids:
            faults = [entry[1] for entry in page_faults_data if entry[0] == pid]
            times = list(range(len(faults)))
            ax.plot(times, faults, marker='o', label=f"Process {pid}")
        
        # Also plot cumulative page faults
        all_times = list(range(len(page_faults_data)))
        cumulative_faults = []
        current_total = 0
        for entry in page_faults_data:
            current_total += entry[1]
            cumulative_faults.append(current_total)
        
        ax.plot(all_times, cumulative_faults, marker='s', linestyle='--', 
                color='black', linewidth=2, label="Cumulative")
        
        ax.set_title('Page Faults vs Time')
        ax.set_xlabel('Time Steps')
        ax.set_ylabel('Number of Page Faults')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True)
        canvas.draw()
        
        self.charts['page_faults'] = canvas_widget

    def create_ram_occupancy_chart(self, parent, results):
        """Create RAM occupancy vs time chart"""
        # This is an estimation since we don't have direct RAM occupancy data
        # We'll use the process data and page faults to simulate RAM usage
        
        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        
        # We can use the page faults data to simulate RAM occupancy
        # Each page fault would likely correspond to loading a page into RAM
        if 'page_faults' not in results:
            ax.text(0.5, 0.5, "No RAM occupancy data available", 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes)
        else:
            # Create synthetic RAM occupancy data based on page faults
            # This is just an estimation
            page_faults_data = results['page_faults']
            process_ids = list(set([entry[0] for entry in page_faults_data]))
            
            # Simulate RAM occupancy starting at 20% and increasing with page faults
            base_occupancy = 20  # starting at 20%
            ram_usage = []
            
            for i, (pid, faults) in enumerate(page_faults_data):
                # Increase RAM usage with each fault
                if i == 0:
                    ram_usage.append(base_occupancy + (faults * 5))
                else:
                    ram_usage.append(ram_usage[-1] + (faults * 5))
            
            # Ensure RAM usage doesn't exceed 100%
            ram_usage = [min(usage, 100) for usage in ram_usage]
            
            times = list(range(len(ram_usage)))
            ax.plot(times, ram_usage, marker='o', color='green', linewidth=2)
            
            ax.set_title('Estimated RAM Occupancy Over Time')
            ax.set_xlabel('Time Steps')
            ax.set_ylabel('RAM Usage (%)')
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.set_ylim(0, 100)
        
        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True)
        canvas.draw()
        
        self.charts['ram_occupancy'] = canvas_widget

    def destroy_charts(self):
        """Destroy all charts to clean up memory"""
        try:
            # Close all matplotlib figures to prevent memory leaks
            plt.close('all')
            
            # Destroy all chart widgets
            for widget in self.charts.values():
                if widget:
                    widget.destroy()
            self.charts = {}
            
            # Destroy tab view if it exists
            if hasattr(self, 'tab_view'):
                self.tab_view.destroy()
                delattr(self, 'tab_view')
                
        except Exception as e:
            print(f"Error destroying charts: {e}")
