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
        
        # Modern color palette for charts
        self.colors = {
            'primary': '#2563eb',
            'secondary': '#7c3aed', 
            'success': '#059669',
            'warning': '#d97706',
            'danger': '#dc2626',
            'info': '#0891b2',
            'surface': '#f8fafc'
        }
        
        # Set matplotlib style for modern look
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams.update({
            'font.family': 'Segoe UI',
            'font.size': 10,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'figure.titlesize': 16
        })
    
    def create_charts(self, results_path):
        """Create all simulation result charts with modern styling"""
        if not os.path.exists(results_path):
            return False
            
        try:
            with open(results_path, 'r') as f:
                results = json.load(f)
            
            # Destroy any existing charts
            self.destroy_charts()
            
            # Create header
            self.create_results_header()
            
            # Create modern tab view for charts
            self.tab_view = ctk.CTkTabview(
                self.parent,
                corner_radius=15,
                border_width=1,
                border_color="#e2e8f0"
            )
            self.tab_view.pack(fill="both", expand=True, padx=20, pady=(10, 20))
            
            # Create tabs with icons and better names
            self.overview_tab = self.tab_view.add("📊 Overview")
            self.tlb_performance_tab = self.tab_view.add("⚡ TLB Performance") 
            self.memory_usage_tab = self.tab_view.add("💾 Memory Usage")
            self.detailed_metrics_tab = self.tab_view.add("📈 Detailed Metrics")
            
            # Create scrollable frames for each tab
            self.create_scrollable_tab_content()
            
            # Generate charts
            self.create_overview_dashboard(self.overview_scroll, results)
            self.create_tlb_performance_charts(self.tlb_scroll, results)
            self.create_memory_usage_charts(self.memory_scroll, results)
            self.create_detailed_metrics_charts(self.detailed_scroll, results)
            
            return True
            
        except Exception as e:
            print(f"Error creating charts: {e}")
            return False

    def create_results_header(self):
        """Create a modern header for the results section"""
        header_frame = ctk.CTkFrame(
            self.parent,
            fg_color=self.colors['primary'],
            corner_radius=15,
            height=60
        )
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            header_frame,
            text="📊 Simulation Results Dashboard",
            font=("Segoe UI", 20, "bold"),
            text_color="white"
        ).pack(expand=True)

    def create_scrollable_tab_content(self):
        """Create scrollable content areas for each tab"""
        self.overview_scroll = ctk.CTkScrollableFrame(
            self.overview_tab,
            fg_color=self.colors['surface']
        )
        self.overview_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tlb_scroll = ctk.CTkScrollableFrame(
            self.tlb_performance_tab,
            fg_color=self.colors['surface']
        )
        self.tlb_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.memory_scroll = ctk.CTkScrollableFrame(
            self.memory_usage_tab,
            fg_color=self.colors['surface']
        )
        self.memory_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.detailed_scroll = ctk.CTkScrollableFrame(
            self.detailed_metrics_tab,
            fg_color=self.colors['surface']
        )
        self.detailed_scroll.pack(fill="both", expand=True, padx=10, pady=10)

    def create_chart_container(self, parent, title, subtitle=""):
        """Create a modern container for charts"""
        container = ctk.CTkFrame(
            parent,
            fg_color="white",
            corner_radius=15,
            border_width=1,
            border_color="#e2e8f0"
        )
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Chart header
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))
        
        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=("Segoe UI", 16, "bold"),
            text_color="#1e293b"
        )
        title_label.pack(anchor="w")
        
        if subtitle:
            subtitle_label = ctk.CTkLabel(
                header,
                text=subtitle,
                font=("Segoe UI", 12),
                text_color="#64748b"
            )
            subtitle_label.pack(anchor="w")
        
        return container

    def create_overview_dashboard(self, parent, results):
        """Create an overview dashboard with key metrics"""
        # Summary metrics card
        metrics_container = self.create_chart_container(
            parent,
            "📋 Simulation Summary",
            "Key performance indicators from the simulation"
        )
        
        # Create metrics grid
        metrics_frame = ctk.CTkFrame(metrics_container, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=20, pady=10)
        
        # Calculate summary metrics
        total_processes = len(set([entry[0] for entry in results.get('page_faults', [])]))
        total_page_faults = sum([entry[1] for entry in results.get('page_faults', [])])
        
        if 'tlb_stats' in results and 'hit_rate' in results['tlb_stats']:
            avg_hit_rate = sum([entry[1] for entry in results['tlb_stats']['hit_rate']]) / len(results['tlb_stats']['hit_rate']) * 100
        else:
            avg_hit_rate = 0
            
        # Create metric cards
        self.create_metric_card(metrics_frame, "🔢 Total Processes", str(total_processes), self.colors['primary'], 0, 0)
        self.create_metric_card(metrics_frame, "⚠️ Page Faults", str(total_page_faults), self.colors['warning'], 0, 1)
        self.create_metric_card(metrics_frame, "⚡ Avg TLB Hit Rate", f"{avg_hit_rate:.1f}%", self.colors['success'], 0, 2)
        
        # Combined metrics chart
        chart_container = self.create_chart_container(
            parent,
            "📈 Performance Overview",
            "Combined view of key metrics over time"
        )
        self.create_modern_combined_chart(chart_container, results)

    def create_metric_card(self, parent, title, value, color, row, col):
        """Create a modern metric card"""
        card = ctk.CTkFrame(
            parent,
            fg_color=color,
            corner_radius=10,
            width=200,
            height=80
        )
        card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
        parent.grid_columnconfigure(col, weight=1)
        
        ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 12),
            text_color="white"
        ).pack(pady=(15, 0))
        
        ctk.CTkLabel(
            card,
            text=value,
            font=("Segoe UI", 20, "bold"),
            text_color="white"
        ).pack(pady=(0, 15))

    def create_modern_combined_chart(self, parent, results):
        """Create a modern combined metrics chart"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), dpi=100)
        fig.patch.set_facecolor('white')
        
        # Modern color scheme
        colors = [self.colors['primary'], self.colors['secondary'], self.colors['success'], self.colors['warning']]
        
        # Plot 1: TLB Performance
        if 'tlb_stats' in results and 'hit_rate' in results['tlb_stats']:
            hit_rate_data = results['tlb_stats']['hit_rate']
            process_ids = list(set([entry[0] for entry in hit_rate_data]))
            
            for i, pid in enumerate(process_ids):
                hit_rates = [entry[1] * 100 for entry in hit_rate_data if entry[0] == pid]
                times = list(range(len(hit_rates)))
                ax1.plot(times, hit_rates, marker='o', linewidth=2.5, 
                        color=colors[i % len(colors)], label=f"Process {pid}",
                        markersize=6, alpha=0.8)
        
        ax1.set_title('TLB Hit Rate Performance', fontsize=14, fontweight='bold', pad=20)
        ax1.set_ylabel('Hit Rate (%)', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(frameon=True, fancybox=True, shadow=True)
        ax1.set_ylim(0, 100)
        
        # Plot 2: Page Faults
        if 'page_faults' in results:
            page_faults_data = results['page_faults']
            process_ids = list(set([entry[0] for entry in page_faults_data]))
            
            for i, pid in enumerate(process_ids):
                faults = [entry[1] for entry in page_faults_data if entry[0] == pid]
                times = list(range(len(faults)))
                ax2.bar([t + i*0.2 for t in times], faults, width=0.2, 
                       color=colors[i % len(colors)], label=f"Process {pid}",
                       alpha=0.8)
        
        ax2.set_title('Page Faults Distribution', fontsize=14, fontweight='bold', pad=20)
        ax2.set_xlabel('Time Steps', fontweight='bold')
        ax2.set_ylabel('Page Faults', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(frameon=True, fancybox=True, shadow=True)
        
        plt.tight_layout()
        
        # Embed in container
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        canvas.draw()
        
        self.charts['overview'] = canvas_widget

    def create_tlb_performance_charts(self, parent, results):
        """Create TLB performance charts"""
        # TLB Hits Chart
        hits_container = self.create_chart_container(
            parent,
            "⚡ TLB Hits Over Time",
            "Number of TLB hits for each process"
        )
        self.create_modern_tlb_hits_chart(hits_container, results)
        
        # TLB Hit Rate Chart
        rate_container = self.create_chart_container(
            parent,
            "📊 TLB Hit Rate Analysis",
            "Hit rate percentage for optimal performance tracking"
        )
        self.create_modern_tlb_rate_chart(rate_container, results)

    def create_memory_usage_charts(self, parent, results):
        """Create memory usage charts"""
        # Page Faults Chart
        faults_container = self.create_chart_container(
            parent,
            "⚠️ Page Faults Analysis",
            "Page fault occurrences and patterns"
        )
        self.create_modern_page_faults_chart(faults_container, results)
        
        # RAM Usage Chart
        ram_container = self.create_chart_container(
            parent,
            "💾 RAM Usage Estimation",
            "Estimated RAM occupancy based on simulation data"
        )
        self.create_modern_ram_chart(ram_container, results)

    def create_detailed_metrics_charts(self, parent, results):
        """Create detailed metrics charts"""
        # Detailed combined view
        detailed_container = self.create_chart_container(
            parent,
            "📈 Detailed Performance Metrics",
            "Comprehensive view of all simulation metrics"
        )
        self.create_detailed_combined_chart(detailed_container, results)

    def create_modern_tlb_hits_chart(self, parent, results):
        """Create modern TLB hits chart"""
        if 'tlb_stats' not in results or 'hits' not in results['tlb_stats']:
            return
        
        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        fig.patch.set_facecolor('white')
        
        colors = [self.colors['primary'], self.colors['secondary'], self.colors['success'], self.colors['warning']]
        
        tlb_hits_data = results['tlb_stats']['hits']
        process_ids = list(set([entry[0] for entry in tlb_hits_data]))
        
        for i, pid in enumerate(process_ids):
            hits = [entry[1] for entry in tlb_hits_data if entry[0] == pid]
            times = list(range(len(hits)))
            ax.plot(times, hits, marker='o', linewidth=2.5, markersize=6,
                   color=colors[i % len(colors)], label=f"Process {pid}", alpha=0.8)
        
        ax.set_title('TLB Hits Over Time', fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Time Steps', fontweight='bold')
        ax.set_ylabel('Number of TLB Hits', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(frameon=True, fancybox=True, shadow=True)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        canvas.draw()
        
        self.charts['tlb_hits'] = canvas_widget

    def create_modern_tlb_rate_chart(self, parent, results):
        """Create modern TLB hit rate chart"""
        if 'tlb_stats' not in results or 'hit_rate' not in results['tlb_stats']:
            return
        
        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        fig.patch.set_facecolor('white')
        
        colors = [self.colors['primary'], self.colors['secondary'], self.colors['success'], self.colors['warning']]
        
        tlb_hit_rate_data = results['tlb_stats']['hit_rate']
        process_ids = list(set([entry[0] for entry in tlb_hit_rate_data]))
        
        for i, pid in enumerate(process_ids):
            hit_rates = [entry[1] * 100 for entry in tlb_hit_rate_data if entry[0] == pid]
            times = list(range(len(hit_rates)))
            ax.plot(times, hit_rates, marker='s', linewidth=2.5, markersize=6,
                   color=colors[i % len(colors)], label=f"Process {pid}", alpha=0.8)
        
        ax.set_title('TLB Hit Rate Performance', fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Time Steps', fontweight='bold')
        ax.set_ylabel('Hit Rate (%)', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)
        ax.legend(frameon=True, fancybox=True, shadow=True)
        
        # Add performance zones
        ax.axhspan(80, 100, alpha=0.1, color=self.colors['success'], label='Excellent')
        ax.axhspan(60, 80, alpha=0.1, color=self.colors['warning'], label='Good')
        ax.axhspan(0, 60, alpha=0.1, color=self.colors['danger'], label='Needs Improvement')
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        canvas.draw()
        
        self.charts['tlb_rate'] = canvas_widget

    def create_modern_page_faults_chart(self, parent, results):
        """Create modern page faults chart"""
        if 'page_faults' not in results:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), dpi=100)
        fig.patch.set_facecolor('white')
        
        colors = [self.colors['primary'], self.colors['secondary'], self.colors['success'], self.colors['warning']]
        
        page_faults_data = results['page_faults']
        process_ids = list(set([entry[0] for entry in page_faults_data]))
        
        # Line chart
        for i, pid in enumerate(process_ids):
            faults = [entry[1] for entry in page_faults_data if entry[0] == pid]
            times = list(range(len(faults)))
            ax1.plot(times, faults, marker='o', linewidth=2.5, markersize=6,
                    color=colors[i % len(colors)], label=f"Process {pid}", alpha=0.8)
        
        ax1.set_title('Page Faults Over Time', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Time Steps', fontweight='bold')
        ax1.set_ylabel('Page Faults', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Pie chart for distribution
        total_faults_per_process = {}
        for pid in process_ids:
            total_faults_per_process[pid] = sum([entry[1] for entry in page_faults_data if entry[0] == pid])
        
        if total_faults_per_process:
            ax2.pie(total_faults_per_process.values(), 
                   labels=[f"Process {pid}" for pid in total_faults_per_process.keys()],
                   colors=colors[:len(total_faults_per_process)],
                   autopct='%1.1f%%', startangle=90)
            ax2.set_title('Page Faults Distribution', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        canvas.draw()
        
        self.charts['page_faults'] = canvas_widget

    def create_modern_ram_chart(self, parent, results):
        """Create modern RAM usage chart"""
        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        fig.patch.set_facecolor('white')
        
        if 'page_faults' not in results:
            ax.text(0.5, 0.5, "📊 No RAM occupancy data available\nData will appear after simulation", 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14, color=self.colors['primary'])
        else:
            # Simulate RAM occupancy based on page faults
            page_faults_data = results['page_faults']
            base_occupancy = 20
            ram_usage = []
            
            for i, (pid, faults) in enumerate(page_faults_data):
                if i == 0:
                    ram_usage.append(base_occupancy + (faults * 5))
                else:
                    ram_usage.append(ram_usage[-1] + (faults * 5))
            
            ram_usage = [min(usage, 100) for usage in ram_usage]
            times = list(range(len(ram_usage)))
            
            # Create gradient effect
            ax.fill_between(times, ram_usage, alpha=0.3, color=self.colors['success'])
            ax.plot(times, ram_usage, marker='o', linewidth=3, markersize=6,
                   color=self.colors['success'], alpha=0.9)
            
            # Add threshold lines
            ax.axhline(y=80, color=self.colors['warning'], linestyle='--', alpha=0.7, label='Warning (80%)')
            ax.axhline(y=90, color=self.colors['danger'], linestyle='--', alpha=0.7, label='Critical (90%)')
        
        ax.set_title('Estimated RAM Usage Over Time', fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Time Steps', fontweight='bold')
        ax.set_ylabel('RAM Usage (%)', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)
        ax.legend(frameon=True, fancybox=True, shadow=True)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        canvas.draw()
        
        self.charts['ram_usage'] = canvas_widget

    def create_detailed_combined_chart(self, parent, results):
        """Create detailed combined metrics chart"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10), dpi=100)
        fig.patch.set_facecolor('white')
        
        colors = [self.colors['primary'], self.colors['secondary'], self.colors['success'], self.colors['warning']]
        
        # TLB Hits
        if 'tlb_stats' in results and 'hits' in results['tlb_stats']:
            tlb_hits_data = results['tlb_stats']['hits']
            process_ids = list(set([entry[0] for entry in tlb_hits_data]))
            
            for i, pid in enumerate(process_ids):
                hits = [entry[1] for entry in tlb_hits_data if entry[0] == pid]
                times = list(range(len(hits)))
                ax1.plot(times, hits, marker='o', color=colors[i % len(colors)], 
                        label=f"Process {pid}", linewidth=2, alpha=0.8)
        
        ax1.set_title('TLB Hits', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # TLB Hit Rate
        if 'tlb_stats' in results and 'hit_rate' in results['tlb_stats']:
            tlb_hit_rate_data = results['tlb_stats']['hit_rate']
            process_ids = list(set([entry[0] for entry in tlb_hit_rate_data]))
            
            for i, pid in enumerate(process_ids):
                hit_rates = [entry[1] * 100 for entry in tlb_hit_rate_data if entry[0] == pid]
                times = list(range(len(hit_rates)))
                ax2.plot(times, hit_rates, marker='s', color=colors[i % len(colors)], 
                        label=f"Process {pid}", linewidth=2, alpha=0.8)
        
        ax2.set_title('TLB Hit Rate (%)', fontweight='bold')
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Page Faults
        if 'page_faults' in results:
            page_faults_data = results['page_faults']
            process_ids = list(set([entry[0] for entry in page_faults_data]))
            
            for i, pid in enumerate(process_ids):
                faults = [entry[1] for entry in page_faults_data if entry[0] == pid]
                times = list(range(len(faults)))
                ax3.bar([t + i*0.2 for t in times], faults, width=0.2, 
                       color=colors[i % len(colors)], label=f"Process {pid}", alpha=0.8)
        
        ax3.set_title('Page Faults', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        # RAM Usage Estimation
        if 'page_faults' in results:
            page_faults_data = results['page_faults']
            base_occupancy = 20
            ram_usage = []
            
            for i, (pid, faults) in enumerate(page_faults_data):
                if i == 0:
                    ram_usage.append(base_occupancy + (faults * 5))
                else:
                    ram_usage.append(ram_usage[-1] + (faults * 5))
            
            ram_usage = [min(usage, 100) for usage in ram_usage]
            times = list(range(len(ram_usage)))
            
            ax4.fill_between(times, ram_usage, alpha=0.3, color=self.colors['success'])
            ax4.plot(times, ram_usage, marker='o', color=self.colors['success'], linewidth=2)
        
        ax4.set_title('RAM Usage (%)', fontweight='bold')
        ax4.set_ylim(0, 100)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        canvas.draw()
        
        self.charts['detailed'] = canvas_widget

    def destroy_charts(self):
        """Destroy all charts to clean up memory"""
        try:
            plt.close('all')
            
            for widget in self.charts.values():
                if widget:
                    widget.destroy()
            self.charts = {}
            
            if hasattr(self, 'tab_view'):
                self.tab_view.destroy()
                delattr(self, 'tab_view')
                
        except Exception as e:
            print(f"Error destroying charts: {e}")