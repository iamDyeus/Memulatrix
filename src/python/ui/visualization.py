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
            # Create a tab view for the charts with larger dimensions
            self.tab_view = ctk.CTkTabview(self.parent)
            self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Configure the tab view to have a minimum height
            self.tab_view.configure(height=800)
            # Create tabs for each chart with scrollable frames
            self.combined_tab = self.tab_view.add("Combined Metrics")
            self.tlb_hits_tab = self.tab_view.add("TLB Hits")
            self.tlb_rate_tab = self.tab_view.add("TLB Hit Rate")
            self.page_faults_tab = self.tab_view.add("Page Faults")
            self.ram_usage_tab = self.tab_view.add("RAM Usage")
            # Create scrollable frames for each tab with minimum heights
            self.combined_scroll = ctk.CTkScrollableFrame(self.combined_tab, height=600)
            self.combined_scroll.pack(fill="both", expand=True, padx=5, pady=5)
            
            self.tlb_hits_scroll = ctk.CTkScrollableFrame(self.tlb_hits_tab, height=500)
            self.tlb_hits_scroll.pack(fill="both", expand=True, padx=5, pady=5)
            
            self.tlb_rate_scroll = ctk.CTkScrollableFrame(self.tlb_rate_tab, height=500)
            self.tlb_rate_scroll.pack(fill="both", expand=True, padx=5, pady=5)
            
            self.page_faults_scroll = ctk.CTkScrollableFrame(self.page_faults_tab, height=500)
            self.page_faults_scroll.pack(fill="both", expand=True, padx=5, pady=5)
            
            self.ram_usage_scroll = ctk.CTkScrollableFrame(self.ram_usage_tab, height=500)
            self.ram_usage_scroll.pack(fill="both", expand=True, padx=5, pady=5)
            # Create the charts in scrollable frames
            self.create_combined_metrics_chart(self.combined_scroll, results)
            self.create_tlb_hits_chart(self.tlb_hits_scroll, results)
            self.create_tlb_hit_rate_chart(self.tlb_rate_scroll, results)
            self.create_page_faults_chart(self.page_faults_scroll, results)
            self.create_ram_usage_chart(self.ram_usage_scroll, results)
            
            return True
        except Exception as e:
            print(f"Error creating charts: {e}")
            return False
            
    def create_combined_metrics_chart(self, parent, results):
        """Create chart showing multiple metrics over time"""
        fig, ax1 = plt.subplots(figsize=(6, 4), dpi=100)
        
        # Set up multiple y-axes for different metrics
        ax2 = ax1.twinx()  # Create a second y-axis sharing the same x-axis
        
        # Colors for different metrics
        colors = {
            'tlb_hit_rate': 'blue',
            'page_faults': 'red',
            'ram_usage': 'green',
            'tlb_hits': 'purple',
            'tlb_misses': 'orange'
        }
        
        time_steps = []
        
        # Check if we have time series data
        if 'time_series' in results:
            time_series = results['time_series']
            
            # Get all available time steps
            all_time_steps = set()
            
            if 'ram_usage' in time_series:
                for t, _ in time_series['ram_usage']:
                    all_time_steps.add(t)
            
            if 'page_faults' in time_series and time_series['page_faults']:
                for process_data in time_series['page_faults']:
                    for t, _ in process_data:
                        all_time_steps.add(t)
            
            time_steps = sorted(list(all_time_steps))
        
        if not time_steps:
            time_steps = list(range(100))  # Default if no time steps found
        
        # Plot RAM usage on left axis
        if 'time_series' in results and 'ram_usage' in results['time_series']:
            ram_data = results['time_series']['ram_usage']
            times = [t for t, _ in ram_data]
            values = [v for _, v in ram_data]
            line1 = ax1.plot(times, values, color=colors['ram_usage'], marker='o', 
                            markersize=4, label='RAM Frames Used')
            
            # Set left y-axis label
            ax1.set_ylabel('RAM Frames Used', color=colors['ram_usage'])
            ax1.tick_params(axis='y', labelcolor=colors['ram_usage'])
        
        # Plot TLB hit rate on right axis
        if 'time_series' in results and 'tlb_hit_rate' in results['time_series']:
            hit_rates = {}
            max_rate = 0
            
            for process_idx, process_data in enumerate(results['time_series']['tlb_hit_rate']):
                hit_rates[f"Process {process_idx+1}"] = {
                    'times': [t for t, _ in process_data],
                    'rates': [r * 100 for _, r in process_data]  # Convert to percentage
                }
                max_rate = max(max_rate, max([r for _, r in process_data]) * 100)
            
            # Plot each process's hit rate
            for process, data in hit_rates.items():
                line2 = ax2.plot(data['times'], data['rates'], 
                               color=colors['tlb_hit_rate'], marker='s', 
                               markersize=4, linestyle='--',
                               alpha=0.7, label=f'TLB Hit Rate ({process})')
            
            # Set right y-axis label and scale
            ax2.set_ylabel('TLB Hit Rate (%)', color=colors['tlb_hit_rate'])
            ax2.tick_params(axis='y', labelcolor=colors['tlb_hit_rate'])
            ax2.set_ylim(0, 100)
        
        # Add page fault markers
        if 'time_series' in results and 'page_faults' in results['time_series']:
            fault_data = {}
            
            for process_idx, process_data in enumerate(results['time_series']['page_faults']):
                process_name = f"Process {process_idx+1}"
                fault_data[process_name] = {
                    'times': [t for t, _ in process_data],
                    'faults': [f for _, f in process_data]
                }
            
            # Create a third y-axis for page faults
            ax3 = ax1.twinx()
            # Offset the axis to the right
            ax3.spines['right'].set_position(('outward', 60))
            
            # Plot page faults for each process
            for process, data in fault_data.items():
                ax3.plot(data['times'], data['faults'], 
                        color=colors['page_faults'], marker='^', 
                        markersize=5, linestyle='-.', 
                        alpha=0.8, label=f'Page Faults ({process})')
            
            # Set the third y-axis label
            ax3.set_ylabel('Page Faults', color=colors['page_faults'])
            ax3.tick_params(axis='y', labelcolor=colors['page_faults'])
        
        ax1.set_xlabel('Time Steps')
        ax1.set_title('Combined Memory Metrics Over Time')
        ax1.grid(True, linestyle='--', alpha=0.3)
        
        # Combine legends from different axes
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels() 
        
        if 'time_series' in results and 'page_faults' in results['time_series']:
            lines3, labels3 = ax3.get_legend_handles_labels()
            lines = lines1 + lines2 + lines3
            labels = labels1 + labels2 + labels3
        else:
            lines = lines1 + lines2
            labels = labels1 + labels2
        
        ax1.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.15),
                  ncol=2, fancybox=True, shadow=True)
        
        fig.tight_layout()
        plt.subplots_adjust(bottom=0.2)
        # Embed in Tkinter with proper sizing
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        canvas.draw()
        
        self.charts['combined_metrics'] = canvas_widget
    
    def create_tlb_hits_chart(self, parent, results):
        """Create TLB hits vs time chart"""
        # Extract data
        if 'tlb_stats' not in results or 'hits' not in results['tlb_stats']:
            return
        
        fig, ax = plt.subplots(figsize=(7, 4.5), dpi=100)
        
        # Check if we have time series data
        if 'time_series' in results and 'tlb_hits' in results['time_series']:
            # Process the time series data
            for process_idx, process_data in enumerate(results['time_series']['tlb_hits']):
                times = [t for t, _ in process_data]
                hits = [h for _, h in process_data]
                ax.plot(times, hits, marker='o', label=f"Process {process_idx+1}")
        else:
            # Process the static data
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
        # Embed in Tkinter with proper sizing
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        canvas.draw()
        
        self.charts['tlb_hits'] = canvas_widget
    
    def create_tlb_hit_rate_chart(self, parent, results):
        """Create TLB hit rate chart"""
        # Extract data
        if 'tlb_stats' not in results or 'hit_rate' not in results['tlb_stats']:
            return
        
        fig, ax = plt.subplots(figsize=(7, 4.5), dpi=100)
        
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
        # Embed in Tkinter with proper sizing
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        canvas.draw()
        
        self.charts['tlb_hit_rate'] = canvas_widget
    
    def create_page_faults_chart(self, parent, results):
        """Create page faults vs time chart"""
        # Extract data
        if 'page_faults' not in results:
            return
        
        fig, ax = plt.subplots(figsize=(7, 4.5), dpi=100)
        
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
        # Embed in Tkinter with proper sizing
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        canvas.draw()
        
        self.charts['page_faults'] = canvas_widget

    def create_ram_usage_chart(self, parent, results):
        """Create RAM occupancy vs time chart"""
        # This is an estimation since we don't have direct RAM occupancy data
        # We'll use the process data and page faults to simulate RAM usage
        
        fig, ax = plt.subplots(figsize=(7, 4.5), dpi=100)
        
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
        
        # Embed in Tkinter with proper sizing
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
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
