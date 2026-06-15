import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import numpy as np
import pandas as pd
import os
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backends.backend_pdf import PdfPages
import skrf as rf

class UniversalDataAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Data & RF Analyzer - Rectenna Edition")
        self.root.geometry("1450x850") 
        
        self.bg_color = "#f0f4f8"       
        self.accent_color = "#0056b3"   
        self.text_color = "#333333"     
        self.panel_bg = "#ffffff"       
        
        self.apply_modern_theme()
            
        self.loaded_datasets = []
        self.active_markers = []          
        self.active_markers_smith = []    
        self.marker_counter_rect = 0
        self.marker_counter_smith = 0     

        self.colors = ['#0056b3', '#d62728', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
        
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['axes.edgecolor'] = '#cccccc'
        plt.rcParams['grid.color'] = '#e0e0e0'
        
        self.setup_ui()
        self.setup_plots()

    def apply_modern_theme(self):
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            
        self.root.configure(bg=self.bg_color)
        style.configure('.', background=self.bg_color, foreground=self.text_color, font=('Segoe UI', 10))
        style.configure('TNotebook', background=self.bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'), padding=[15, 5], background='#e1e8ed', foreground=self.text_color)
        style.map('TNotebook.Tab', background=[('selected', self.panel_bg)], foreground=[('selected', self.accent_color)])
        style.configure('TLabelframe', background=self.bg_color, bordercolor='#cccccc', borderwidth=1)
        style.configure('TLabelframe.Label', font=('Segoe UI', 10, 'bold'), foreground=self.accent_color, background=self.bg_color)
        style.configure('TFrame', background=self.bg_color)
        style.configure('Panel.TFrame', background=self.panel_bg)
        style.configure('TButton', font=('Segoe UI', 10), padding=5, background='#e1e8ed', borderwidth=1)
        style.map('TButton', background=[('active', '#c0d1dd')])
        style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'), padding=5, background=self.accent_color, foreground='white')
        style.map('Primary.TButton', background=[('active', '#004494')])
        style.configure('TSeparator', background='#cccccc')

    def setup_ui(self):
        top_container = ttk.Frame(self.root, padding="10")
        top_container.pack(side=tk.TOP, fill=tk.X)
        
        frame_data = ttk.LabelFrame(top_container, text="Data Management", padding="10")
        frame_data.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        self.btn_load = ttk.Button(frame_data, text="📁 Load Data (.sNp / .csv / .txt)", command=self.load_file)
        self.btn_load.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(frame_data, text="Trace:").pack(side=tk.LEFT, padx=5)
        self.combo_trace = ttk.Combobox(frame_data, state="readonly", width=15)
        self.combo_trace.pack(side=tk.LEFT, padx=5)
        
        self.btn_remove = ttk.Button(frame_data, text="🗑️ Remove Trace", command=self.remove_trace)
        self.btn_remove.pack(side=tk.LEFT, padx=5)

        frame_markers = ttk.LabelFrame(top_container, text="Interactive Markers", padding="10")
        frame_markers.pack(side=tk.LEFT, fill=tk.Y, padx=5, expand=True)
        
        ttk.Label(frame_markers, text="Target X:").pack(side=tk.LEFT, padx=5)
        self.entry_x_target = ttk.Entry(frame_markers, width=12)
        self.entry_x_target.pack(side=tk.LEFT, padx=5)
        
        self.btn_add_marker = ttk.Button(frame_markers, text="➕ Drop Pin", command=self.add_marker_from_ui)
        self.btn_add_marker.pack(side=tk.LEFT, padx=5)
        
        self.btn_clear = ttk.Button(frame_markers, text="❌ Clear Pins", command=self.clear_markers)
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        frame_export = ttk.LabelFrame(top_container, text="Reporting", padding="10")
        frame_export.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        self.btn_pdf = ttk.Button(frame_export, text="📄 Export PDF Report", command=self.show_pdf_export_dialog, style='Primary.TButton')
        self.btn_pdf.pack(side=tk.LEFT, padx=5)

        bot_container = ttk.Frame(self.root, padding="10")
        bot_container.pack(side=tk.TOP, fill=tk.X)
        
        frame_style = ttk.LabelFrame(bot_container, text="2D Graph Styling", padding="10")
        frame_style.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(frame_style, text="Graph Title:").pack(side=tk.LEFT, padx=5)
        self.entry_title = ttk.Entry(frame_style, width=25)
        self.entry_title.insert(0, "Universal Data Plot")
        self.entry_title.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(frame_style, text="X-Axis:").pack(side=tk.LEFT, padx=10)
        self.entry_xlabel = ttk.Entry(frame_style, width=15)
        self.entry_xlabel.insert(0, "Frequency (GHz)")
        self.entry_xlabel.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(frame_style, text="Y-Axis:").pack(side=tk.LEFT, padx=10)
        self.entry_ylabel = ttk.Entry(frame_style, width=15)
        self.entry_ylabel.insert(0, "Magnitude (dB)")
        self.entry_ylabel.pack(side=tk.LEFT, padx=5)
        
        self.btn_update_axes = ttk.Button(frame_style, text="🔄 Update Labels", command=self.update_axis_labels)
        self.btn_update_axes.pack(side=tk.LEFT, padx=15)

    def setup_plots(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.tab_rect = ttk.Frame(self.notebook, style='Panel.TFrame')
        self.tab_smith = ttk.Frame(self.notebook, style='Panel.TFrame')
        self.tab_polar = ttk.Frame(self.notebook, style='Panel.TFrame') 
        self.tab_crlh = ttk.Frame(self.notebook, padding="30", style='Panel.TFrame') 
        
        self.notebook.add(self.tab_rect, text='  📈 2D Plot  ')
        self.notebook.add(self.tab_smith, text='  🎯 Smith Chart & Match  ')
        self.notebook.add(self.tab_polar, text='  📡 Radiation Pattern  ') 
        self.notebook.add(self.tab_crlh, text='  🧮 Phase Solver (CRLH)  ')
        
        self.fig_rect, self.ax_rect = plt.subplots(figsize=(10, 6), facecolor=self.panel_bg)
        self.fig_rect.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.1)
        self.ax_rect.set_facecolor('#ffffff')
        self.ax_rect.set_title('Universal Data Plot', fontsize=14, fontweight='bold', color=self.text_color)
        
        self.rect_summary_text = self.fig_rect.text(0.02, 0.90, "", va='top', ha='left', fontsize=10, 
                                        bbox=dict(boxstyle="round,pad=0.5", fc="#f8f9fa", ec="gray", alpha=0.9))
        self.rect_summary_text.set_visible(False)
        
        self.canvas_rect = FigureCanvasTkAgg(self.fig_rect, master=self.tab_rect)
        toolbar_frame_rect = ttk.Frame(self.tab_rect, style='Panel.TFrame')
        toolbar_frame_rect.pack(side=tk.BOTTOM, fill=tk.X)
        NavigationToolbar2Tk(self.canvas_rect, toolbar_frame_rect)
        self.canvas_rect.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.fig_rect.canvas.mpl_connect('button_press_event', self.on_plot_click_rect)
        
        self.fig_smith, self.ax_smith = plt.subplots(figsize=(8, 8), facecolor=self.panel_bg)
        self.fig_smith.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        self.ax_smith.set_title('RF Impedance Smith Chart', fontsize=14, fontweight='bold', color=self.text_color)
        self.ax_smith.axis('off') 
        
        self.smith_summary_text = self.fig_smith.text(0.02, 0.95, "", va='top', ha='left', fontsize=10, 
                                        bbox=dict(boxstyle="round,pad=0.5", fc="#f8f9fa", ec="gray", alpha=0.9))
        self.smith_summary_text.set_visible(False)
        
        self.canvas_smith = FigureCanvasTkAgg(self.fig_smith, master=self.tab_smith)
        toolbar_frame_smith = ttk.Frame(self.tab_smith, style='Panel.TFrame')
        toolbar_frame_smith.pack(side=tk.BOTTOM, fill=tk.X)
        self.toolbar_smith = NavigationToolbar2Tk(self.canvas_smith, toolbar_frame_smith)
        self.canvas_smith.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.fig_smith.canvas.mpl_connect('button_press_event', self.on_plot_click_smith)

        self.setup_polar_tab()
        self.setup_crlh_tab()

    def show_pdf_export_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Export PDF Report")
        dialog.geometry("380x280")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root) 
        dialog.grab_set() 

        ttk.Label(dialog, text="Select components to include in your report:", font=('Segoe UI', 11, 'bold')).pack(pady=15)

        var_rect = tk.BooleanVar(value=True)
        var_smith = tk.BooleanVar(value=True)
        var_polar = tk.BooleanVar(value=True)
        var_crlh = tk.BooleanVar(value=True)

        chk_frame = ttk.Frame(dialog)
        chk_frame.pack(anchor='center', pady=10)

        ttk.Checkbutton(chk_frame, text="📈 2D Universal Plot", variable=var_rect).grid(row=0, column=0, sticky='w', pady=5)
        ttk.Checkbutton(chk_frame, text="🎯 RF Smith Chart", variable=var_smith).grid(row=1, column=0, sticky='w', pady=5)
        ttk.Checkbutton(chk_frame, text="📡 Radiation Pattern", variable=var_polar).grid(row=2, column=0, sticky='w', pady=5)
        ttk.Checkbutton(chk_frame, text="🧮 Metamaterial (CRLH) Results", variable=var_crlh).grid(row=3, column=0, sticky='w', pady=5)

        def on_export():
            selections = {'rect': var_rect.get(), 'smith': var_smith.get(), 'polar': var_polar.get(), 'crlh': var_crlh.get()}
            if not any(selections.values()):
                messagebox.showwarning("Warning", "Select at least one item.", parent=dialog)
                return
            filepath = filedialog.asksaveasfilename(title="Save Report", defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], parent=dialog)
            if not filepath: return
            dialog.destroy()
            self.execute_pdf_export(filepath, selections)

        ttk.Button(dialog, text="Export Document", command=on_export, style='Primary.TButton').pack(pady=15)

    def execute_pdf_export(self, filepath, selections):
        try:
            with PdfPages(filepath) as pdf:
                if selections['rect']: pdf.savefig(self.fig_rect, facecolor='#ffffff')
                if selections['smith']: pdf.savefig(self.fig_smith, facecolor='#ffffff')
                if selections['polar']: pdf.savefig(self.fig_polar, facecolor='#ffffff')
                if selections['crlh']:
                    fig_text, ax_text = plt.subplots(figsize=(8.5, 11))
                    ax_text.axis('off')
                    crlh_content = self.crlh_results.get(1.0, tk.END).strip()
                    if not crlh_content: crlh_content = "No Phase/CRLH calculations performed."
                    report_text = f"RF Rectenna System Report\n" + "="*50 + f"\n\n{crlh_content}"
                    ax_text.text(0.1, 0.9, report_text, fontsize=10, va='top', family='monospace')
                    pdf.savefig(fig_text)
                    plt.close(fig_text)
            messagebox.showinfo("Success", f"Professional PDF Report successfully generated:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to generate PDF:\n{str(e)}")

    def on_plot_click_rect(self, e):
        if e.inaxes != self.ax_rect or self.toolbar_rect.mode != '': return
        if e.button == 3 and self.active_markers: 
            xr, yr = self.ax_rect.get_xlim()[1] - self.ax_rect.get_xlim()[0], self.ax_rect.get_ylim()[1] - self.ax_rect.get_ylim()[0]
            md, ci = float('inf'), -1
            for i, m in enumerate(self.active_markers):
                d = ((m['x'] - e.xdata) / xr)**2 + ((m['y'] - e.ydata) / yr)**2
                if d < md: md, ci = d, i
            if ci != -1 and md < 0.05: 
                p = self.active_markers.pop(ci); p['pt'][0].remove(); p['lbl'].remove(); self.update_rect_summary()
        elif e.button == 1 and self.loaded_datasets: 
            bd, bds = float('inf'), None
            for ds in self.loaded_datasets:
                i = np.abs(ds['freq'] - e.xdata).argmin()
                if np.abs(ds['freq'][i] - e.xdata) < bd: bd, bds = np.abs(ds['freq'][i] - e.xdata), ds
            if bds and bd < (self.ax_rect.get_xlim()[1] - self.ax_rect.get_xlim()[0])*0.1: 
                self.add_marker_rect(e.xdata, bds)

    def on_plot_click_smith(self, e):
        if e.inaxes != self.ax_smith or self.toolbar_smith.mode != '': return
        if e.button == 3 and self.active_markers_smith: 
            md, ci = float('inf'), -1
            for i, m in enumerate(self.active_markers_smith):
                d = (m['x'] - e.xdata)**2 + (m['y'] - e.ydata)**2
                if d < md: md, ci = d, i
            if ci != -1 and md < 0.1: 
                p = self.active_markers_smith.pop(ci); p['pt'][0].remove(); p['lbl'].remove(); p['pt_conj'][0].remove(); p['line_conj'][0].remove(); self.update_smith_summary()
        elif e.button == 1: 
            bd, bds, bidx = float('inf'), None, -1
            for ds in self.loaded_datasets:
                if not ds.get('is_rf'): continue 
                dists = (np.real(ds['s_complex']) - e.xdata)**2 + (np.imag(ds['s_complex']) - e.ydata)**2
                i = dists.argmin()
                if dists[i] < bd: bd, bds, bidx = dists[i], ds, i
            if bds and bd < 0.15: self.add_marker_smith_by_idx(bds, bidx)

    # --- UPDATED: CST RADIATION PATTERN LOGIC ---
    def setup_polar_tab(self):
        polar_control = ttk.Frame(self.tab_polar, padding="10", style='Panel.TFrame')
        polar_control.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(polar_control, text="📁 Load CST Patterns (.txt/.csv)", command=self.load_polar_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(polar_control, text="❌ Clear Polar Plot", command=self.clear_polar).pack(side=tk.LEFT, padx=10)
        
        self.fig_polar, self.ax_polar = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'}, facecolor=self.panel_bg)
        self.fig_polar.subplots_adjust(top=0.85, bottom=0.1)
        self.ax_polar.set_facecolor('#ffffff')
        
        # 1. FIXED MIRRORING: 1 = Counter-Clockwise (Puts Phi=90 on the Left, exactly like CST)
        self.ax_polar.set_theta_direction(1)
        self.ax_polar.set_theta_zero_location("N")
        
        self.ax_polar.set_title('Antenna Radiation Pattern', fontsize=14, fontweight='bold', pad=20, color=self.text_color)
        
        self.canvas_polar = FigureCanvasTkAgg(self.fig_polar, master=self.tab_polar)
        toolbar_frame_polar = ttk.Frame(self.tab_polar, style='Panel.TFrame')
        toolbar_frame_polar.pack(side=tk.BOTTOM, fill=tk.X)
        NavigationToolbar2Tk(self.canvas_polar, toolbar_frame_polar)
        self.canvas_polar.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def load_polar_data(self):
        filepaths = filedialog.askopenfilenames(title="Select CST Polar Data", filetypes=(("Text/CSV", "*.txt *.csv"), ("All", "*.*")))
        if not filepaths: return
        
        for filepath in filepaths:
            try:
                angles = []
                magnitudes = []
                
                with open(filepath, 'r') as f:
                    lines = f.readlines()
                    
                for line in lines:
                    if 'Theta' in line or '---' in line or line.strip() == '':
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            theta = float(parts[0])
                            phi = float(parts[1])
                            mag = float(parts[2]) # Extracting Directivity
                            
                            # CST maps back-lobe to Phi=270 or 180. 
                            # Since we set theta_direction to 1 (CCW), Angle mapping:
                            # Phi = 90  -> plots to Left  (0 to 180)
                            # Phi = 270 -> plots to Right (360 down to 180)
                            if phi >= 180:
                                angle_deg = 360 - theta
                            else:
                                angle_deg = theta
                                
                            angles.append(angle_deg)
                            magnitudes.append(mag)
                        except ValueError:
                            pass
                            
                if not angles:
                    raise ValueError("Could not extract data. Ensure it's a CST Farfield text export.")

                angles_rad = np.deg2rad(angles)
                mags = np.array(magnitudes)
                
                fname = os.path.basename(filepath)
                self.ax_polar.plot(angles_rad, mags, linewidth=2, label=fname)
                
                # 2. FIXED SCALING: Give the graph the exact same padded center as CST (-15 in your case)
                min_mag = np.min(mags)
                max_mag = np.max(mags)
                
                # Rounds down to the nearest cleanly divisible 5 (e.g. -10.08 becomes -15.0)
                rmin_clean = np.floor(min_mag / 5) * 5 - 5 
                rmax_clean = np.ceil(max_mag / 5) * 5
                
                self.ax_polar.set_ylim(rmin_clean, rmax_clean)
                
                # Set the internal rings to exactly -15, -10, -5, 0, 5 like CST
                ticks = np.arange(rmin_clean + 5, rmax_clean + 1, 5)
                self.ax_polar.set_rticks(ticks)

                self.ax_polar.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
                self.canvas_polar.draw()
                
            except Exception as e:
                messagebox.showerror("Polar Parsing Error", f"Failed to plot {os.path.basename(filepath)}:\n{str(e)}")

    def clear_polar(self):
        self.ax_polar.clear()
        self.ax_polar.set_theta_direction(1)
        self.ax_polar.set_theta_zero_location("N")
        self.ax_polar.set_title('Antenna Radiation Pattern', fontsize=14, fontweight='bold', pad=20, color=self.text_color)
        self.canvas_polar.draw()

    def setup_crlh_tab(self):
        main_split = ttk.Frame(self.tab_crlh, style='Panel.TFrame')
        main_split.pack(fill=tk.BOTH, expand=True)

        main_split.columnconfigure(0, weight=1, uniform="group1")
        main_split.columnconfigure(1, weight=1, uniform="group1")
        main_split.rowconfigure(0, weight=1)

        left_panel = ttk.Frame(main_split, style='Panel.TFrame')
        left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 10))

        right_panel = ttk.Frame(main_split, style='Panel.TFrame')
        right_panel.grid(row=0, column=1, sticky='nsew', padx=(10, 0))

        title = ttk.Label(left_panel, text="Phase Compensation Solver", font=('Segoe UI', 18, 'bold'), foreground=self.accent_color, background=self.panel_bg)
        title.pack(pady=(0, 20), anchor='w')
        
        frame_b1 = ttk.LabelFrame(left_panel, text="Band 1 (Required)", padding="15")
        frame_b1.pack(fill=tk.X, pady=5)
        ttk.Label(frame_b1, text="Select Marker:").grid(row=0, column=0, pady=5, sticky='w')
        self.crlh_combo_m1 = ttk.Combobox(frame_b1, state="readonly", width=18)
        self.crlh_combo_m1.grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(frame_b1, text="⬇️ Fetch Data", command=lambda: self.fetch_marker_data(1)).grid(row=0, column=2, padx=5)
        ttk.Label(frame_b1, text="Target Freq (GHz):").grid(row=1, column=0, pady=5, sticky='w')
        self.crlh_f1 = ttk.Entry(frame_b1, width=15); self.crlh_f1.grid(row=1, column=1, sticky='w', padx=10, pady=5)
        ttk.Label(frame_b1, text="Required Phase Φ1 (Deg):").grid(row=2, column=0, pady=5, sticky='w')
        self.crlh_p1 = ttk.Entry(frame_b1, width=15); self.crlh_p1.grid(row=2, column=1, sticky='w', padx=10, pady=5)

        frame_b2 = ttk.LabelFrame(left_panel, text="Band 2 (Optional - Leave blank for Single-Band mode)", padding="15")
        frame_b2.pack(fill=tk.X, pady=15)
        ttk.Label(frame_b2, text="Select Marker:").grid(row=0, column=0, pady=5, sticky='w')
        self.crlh_combo_m2 = ttk.Combobox(frame_b2, state="readonly", width=18)
        self.crlh_combo_m2.grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(frame_b2, text="⬇️ Fetch Data", command=lambda: self.fetch_marker_data(2)).grid(row=0, column=2, padx=5)
        ttk.Label(frame_b2, text="Target Freq (GHz):").grid(row=1, column=0, pady=5, sticky='w')
        self.crlh_f2 = ttk.Entry(frame_b2, width=15); self.crlh_f2.grid(row=1, column=1, sticky='w', padx=10, pady=5)
        ttk.Label(frame_b2, text="Required Phase Φ2 (Deg):").grid(row=2, column=0, pady=5, sticky='w')
        self.crlh_p2 = ttk.Entry(frame_b2, width=15); self.crlh_p2.grid(row=2, column=1, sticky='w', padx=10, pady=5)

        frame_sys = ttk.LabelFrame(left_panel, text="System Parameters", padding="15")
        frame_sys.pack(fill=tk.X, pady=5)
        ttk.Label(frame_sys, text="Characteristic Impedance Z0 (Ω):").grid(row=0, column=0, pady=5, sticky='w')
        self.crlh_z0 = ttk.Entry(frame_sys, width=15); self.crlh_z0.insert(0, "50"); self.crlh_z0.grid(row=0, column=1, padx=10, pady=5, sticky='w')
        ttk.Label(frame_sys, text="Number of Unit Cells (N):").grid(row=1, column=0, pady=5, sticky='w')
        self.crlh_n = ttk.Entry(frame_sys, width=15); self.crlh_n.insert(0, "1"); self.crlh_n.grid(row=1, column=1, padx=10, pady=5, sticky='w')

        btn_frame = ttk.Frame(left_panel, style='Panel.TFrame')
        btn_frame.pack(fill=tk.X, pady=20)
        ttk.Button(btn_frame, text="⚙️ Calculate L & C Parameters", command=self.solve_crlh_equations, style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="📘 View Theory & Equations", command=self.show_theory_dialog).pack(side=tk.LEFT)

        term_title = ttk.Label(right_panel, text="Solver Terminal Output:", font=('Segoe UI', 12, 'bold'), foreground=self.text_color, background=self.panel_bg)
        term_title.pack(pady=(0, 5), anchor='w')
        
        self.crlh_results = tk.Text(right_panel, font=('Consolas', 11), bg='#0d1117', fg='#00ff00', insertbackground='white', padx=15, pady=15)
        self.crlh_results.pack(fill=tk.BOTH, expand=True)

    def show_theory_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Mathematical Proof & Theory")
        dialog.geometry("650x550")
        dialog.configure(bg=self.bg_color)
        lbl = tk.Label(dialog, text="CRLH Metamaterial Mathematical Derivation", font=('Segoe UI', 14, 'bold'), bg=self.bg_color, fg=self.accent_color)
        lbl.pack(pady=15)
        text = tk.Text(dialog, wrap=tk.WORD, font=('Consolas', 10), bg='#ffffff', fg=self.text_color, padx=15, pady=15)
        text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        theory = """--- The Two Laws of Transmission Lines ---
Every lossless transmission line is governed by two fundamental rules:

1. Characteristic Impedance (Z0):
The ratio of voltage to current depends on inductance and capacitance.
Z0 = sqrt(L / C)

2. Phase Delay (Φ):
Phase shift is dictated by frequency (ω), unit cells (N), and the LC product.
Φ = -N * ω * sqrt(L * C)

--- Right-Handed Derivation (Standard Copper) ---
We isolate the square root term from the phase equation into a constant (PR):
PR = sqrt(L_R * C_R) = |Φ| / (N * ω)

We now have a system of two equations:
(A) Z0 = sqrt(L_R / C_R)
(B) PR = sqrt(L_R * C_R)

To solve for Series Inductance (L_R):
Multiply (A) and (B). Capacitance cancels out perfectly:
Z0 * PR = sqrt(L_R / C_R) * sqrt(L_R * C_R) = sqrt(L_R^2) = L_R

To solve for Shunt Capacitance (C_R):
Divide (B) by (A). Inductance cancels out:
PR / Z0 = sqrt(L_R * C_R) / sqrt(L_R / C_R) = sqrt(C_R^2) = C_R

--- Left-Handed Derivation (Metamaterial Gaps & Vias) ---
The left-handed constant (PL) is isolated similarly:
PL = 1 / sqrt(L_L * C_L)

Using the same characteristic impedance boundary condition (Z0 = sqrt(L_L / C_L)), we can solve for the physical gap and via parameters.

To solve for Shunt Inductance (L_L):
L_L = Z0 / PL

To solve for Series Capacitance (C_L):
C_L = 1 / (PL * Z0)
"""
        text.insert(tk.END, theory)
        text.config(state=tk.DISABLED)

    def update_crlh_dropdowns(self):
        opts = [f"{m['name']} ({m['freq']:.3f} GHz)" for m in self.active_markers_smith]
        self.crlh_combo_m1['values'] = opts; self.crlh_combo_m2['values'] = opts
        if opts and self.crlh_combo_m1.get() not in opts: self.crlh_combo_m1.set('')
        if opts and self.crlh_combo_m2.get() not in opts: self.crlh_combo_m2.set('')

    def fetch_marker_data(self, b_id):
        cb = self.crlh_combo_m1 if b_id == 1 else self.crlh_combo_m2
        sel = cb.get()
        if not sel: return messagebox.showwarning("Missing", f"Select marker for Band {b_id}.")
        m_name = sel.split(" ")[0]
        m = next((m for m in self.active_markers_smith if m['name'] == m_name), None)
        if m:
            f, p = self.crlh_f1 if b_id==1 else self.crlh_f2, self.crlh_p1 if b_id==1 else self.crlh_p2
            f.delete(0, tk.END); f.insert(0, f"{m['freq']:.3f}")
            p.delete(0, tk.END); p.insert(0, f"{m['phase']:.2f}")

    def solve_crlh_equations(self):
        try:
            f1s, p1s = self.crlh_f1.get().strip(), self.crlh_p1.get().strip()
            f2s, p2s = self.crlh_f2.get().strip(), self.crlh_p2.get().strip()
            if not f1s or not p1s: return messagebox.showerror("Error", "Band 1 required.")
            f1, p1 = float(f1s) * 1e9, float(p1s) * (np.pi/180.0) 
            w1, Z0, N = 2*np.pi*f1, float(self.crlh_z0.get()), float(self.crlh_n.get())
            self.crlh_results.delete(1.0, tk.END)

            if not f2s or not p2s:
                if p1 < 0:
                    PR = abs(p1) / (N * w1)
                    res =  f"> SINGLE-BAND CALCULATION (Right-Handed Microstrip)\n"
                    res += f"> -------------------------------------------------\n"
                    res += f"> Step 1. Phase Constant (PR) = |Φ| / (N*ω) = {PR:.3e} s/rad\n"
                    res += f"> Step 2. Inductance (L_R) = PR * Z0\n"
                    res += f"> Step 3. Capacitance(C_R) = PR / Z0\n\n"
                    res += f"> FINAL COMPONENTS:\n> L_R: {PR*Z0 * 1e9:.3f} nH\n> C_R: {PR/Z0 * 1e12:.3f} pF\n"
                    self.crlh_results.insert(tk.END, res)
                elif p1 > 0:
                    PL = (p1 * w1) / N
                    res =  f"> SINGLE-BAND CALCULATION (Left-Handed Metamaterial)\n"
                    res += f"> --------------------------------------------------\n"
                    res += f"> Step 1. Phase Constant (PL) = (Φ*ω) / N = {PL:.3e} rad/s\n"
                    res += f"> Step 2. Inductance (L_L) = Z0 / PL\n"
                    res += f"> Step 3. Capacitance(C_L) = 1 / (PL*Z0)\n\n"
                    res += f"> FINAL COMPONENTS:\n> L_L: {Z0/PL * 1e9:.3f} nH\n> C_L: {1/(PL*Z0) * 1e12:.3f} pF\n"
                    self.crlh_results.insert(tk.END, res)
                else:
                    self.crlh_results.insert(tk.END, "> ERROR: Phase cannot be exactly 0 for a single band.")
                return

            f2, p2 = float(f2s) * 1e9, float(p2s) * (np.pi/180.0)
            w2 = 2*np.pi*f2
            if w1 == w2: return messagebox.showerror("Error", "Frequencies must differ.")
            
            PR = (p2 * w2 - p1 * w1) / (N * (w1**2 - w2**2))
            PL = (w1**2) * PR + (p1 * w1) / N
            
            if PR <= 0 or PL <= 0: return self.crlh_results.insert(tk.END, "> ERROR: Unrealizable phase shift combination.")
            
            res =  f"> DUAL-BAND CALCULATION (CRLH Metamaterial Unit Cell)\n"
            res += f"> ---------------------------------------------------\n"
            res += f"> Math Step 1. Derived RH Constant (PR): {PR:.3e} s/rad\n"
            res += f"> Math Step 2. Derived LH Constant (PL): {PL:.3e} rad/s\n"
            res += f"> Math Step 3. Extracting L and C values using Z0 = {Z0} Ω\n\n"
            res += f"> FINAL METAMATERIAL COMPONENTS:\n"
            res += f"> [Right-Handed / Standard Copper Properties]\n"
            res += f"> L_R (Series Inductance) : {PR*Z0 * 1e9:.3f} nH\n"
            res += f"> C_R (Shunt Capacitance) : {PR/Z0 * 1e12:.3f} pF\n"
            res += f"> [Left-Handed / Gap & Via Properties]\n"
            res += f"> L_L (Shunt Inductance)  : {Z0/PL * 1e9:.3f} nH\n"
            res += f"> C_L (Series Capacitance): {1/(PL*Z0) * 1e12:.3f} pF\n"
            
            self.crlh_results.insert(tk.END, res)
        except ValueError: messagebox.showerror("Input Error", "Valid numbers only.")

    def update_axis_labels(self):
        self.ax_rect.set_title(self.entry_title.get(), fontsize=14, fontweight='bold', color=self.text_color)
        self.ax_rect.set_xlabel(self.entry_xlabel.get(), fontsize=12)
        self.ax_rect.set_ylabel(self.entry_ylabel.get(), fontsize=12)
        self.canvas_rect.draw()

    def update_rect_summary(self):
        self.rect_summary_text.set_visible(bool(self.active_markers))
        if self.active_markers: self.rect_summary_text.set_text("--- 2D MARKERS ---\n\n" + "\n\n".join([m['details'] for m in self.active_markers]))
        self.canvas_rect.draw()

    def update_smith_summary(self):
        self.smith_summary_text.set_visible(bool(self.active_markers_smith))
        if self.active_markers_smith: self.smith_summary_text.set_text("--- SMITH MARKERS ---\n\n" + "\n\n".join([m['details'] for m in self.active_markers_smith]))
        self.canvas_smith.draw(); self.update_crlh_dropdowns()

    def load_file(self):
        fp = filedialog.askopenfilename(filetypes=(("Touchstone", "*.s1p *.s2p *.s3p *.s4p *.sp2"), ("Data", "*.txt *.csv"), ("All", "*.*")))
        if not fp: return 
        fn, ext = os.path.basename(fp), os.path.splitext(fp)[1].lower()
        col = self.colors[len(self.loaded_datasets) % len(self.colors)]
        is_ts = bool(re.match(r'^\.s\dp$', ext)) or ext == '.sp2'
        try:
            if is_ts:
                nw = rf.Network(fp)
                x, y, sc = nw.f / 1e9, nw.s_db[:, 0, 0], nw.s[:, 0, 0]
                nw.plot_s_smith(m=0, n=0, ax=self.ax_smith, label=os.path.splitext(fn)[0], color=col, linewidth=2)
                self.canvas_smith.draw()
            elif ext in ['.csv', '.txt']:
                df = pd.read_csv(fp, sep=r'[,\s;]+', engine='python', header=None, comment='!').apply(pd.to_numeric, errors='coerce').dropna(axis=1, how='all').dropna()
                x, y, sc, is_ts, nw = df.iloc[:, 0].to_numpy(), df.iloc[:, 1].to_numpy(), None, False, None
            else: return
            self.loaded_datasets.append({'name': os.path.splitext(fn)[0], 'freq': x, 's11': y, 's_complex': sc, 'color': col, 'is_rf': is_ts, 'nw': nw})
            self.combo_trace['values'] = [d['name'] for d in self.loaded_datasets]; self.combo_trace.current(len(self.loaded_datasets) - 1)
            self.ax_rect.plot(x, y, label=os.path.splitext(fn)[0], color=col, linestyle='-' if is_ts else '--', linewidth=2)
            self.ax_rect.legend(loc='best', fontsize=10); self.ax_rect.relim(); self.ax_rect.autoscale_view(); self.canvas_rect.draw()
        except Exception as e: messagebox.showerror("Load Error", str(e))

    def remove_trace(self):
        sel = self.combo_trace.get()
        if not sel or not messagebox.askyesno("Confirm", f"Remove '{sel}'?"): return
        self.loaded_datasets = [d for d in self.loaded_datasets if d['name'] != sel]
        self.combo_trace['values'] = [d['name'] for d in self.loaded_datasets]
        self.combo_trace.set(self.combo_trace['values'][-1] if self.loaded_datasets else '')
        self.clear_markers(); self.ax_rect.clear(); self.ax_smith.clear()
        self.ax_rect.set_title(self.entry_title.get(), fontsize=14, fontweight='bold', color=self.text_color)
        self.ax_smith.set_title('RF Impedance Smith Chart', fontsize=14, fontweight='bold', color=self.text_color); self.ax_smith.axis('off')
        for d in self.loaded_datasets:
            self.ax_rect.plot(d['freq'], d['s11'], label=d['name'], color=d['color'], linestyle='-' if d['is_rf'] else '--', linewidth=2)
            if d['is_rf']: d['nw'].plot_s_smith(m=0, n=0, ax=self.ax_smith, label=d['name'], color=d['color'], linewidth=2)
        if self.loaded_datasets: self.ax_rect.legend(loc='best', fontsize=10)
        self.ax_rect.relim(); self.ax_rect.autoscale_view(); self.canvas_rect.draw(); self.canvas_smith.draw()

    def add_marker_rect(self, tgt_x, ds):
        idx = np.abs(ds['freq'] - tgt_x).argmin()
        x_ex, y_ex, col = ds['freq'][idx], ds['s11'][idx], ds['color']
        self.marker_counter_rect += 1
        m_name = f"m{self.marker_counter_rect}"
        pt = self.ax_rect.plot(x_ex, y_ex, marker='o', color=col, markersize=8, markeredgecolor='black', zorder=5)
        
        xlbl = self.entry_xlabel.get()
        ylbl = self.entry_ylabel.get()
        lbl = self.ax_rect.annotate(
            m_name, xy=(x_ex, y_ex), xytext=(8, 8), textcoords='offset points', 
            fontsize=10, fontweight='bold', color=col, zorder=6,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=col, alpha=0.8)
        )
        self.active_markers.append({'name': m_name, 'x': x_ex, 'y': y_ex, 'pt': pt, 'lbl': lbl, 'details': f"{m_name} ({ds['name']})\n{xlbl}: {x_ex:.3g}\n{ylbl}: {y_ex:.3g}"})
        self.update_rect_summary()

    def add_marker_smith_by_idx(self, ds, idx):
        f_ex, s_val, col = ds['freq'][idx], ds['s_complex'][idx], ds['color']
        self.marker_counter_smith += 1
        m_name = f"M{self.marker_counter_smith}"
        x_ex, y_ex, s_cj = np.real(s_val), np.imag(s_val), np.conj(s_val)
        x_cj, y_cj, p_deg = np.real(s_cj), np.imag(s_cj), np.angle(s_val, deg=True)
        if np.abs(s_val - 1.0) < 1e-6: z_str = z_cj_str = "Z0 * (∞)"
        else:
            zn = (1 + s_val) / (1 - s_val)
            z_str = f"Z0 * ({np.real(zn):.3f} {'+' if np.imag(zn)>=0 else '-'} j{abs(np.imag(zn)):.3f})"
            zc = np.conj(zn)
            z_cj_str = f"Z0 * ({np.real(zc):.3f} {'+' if np.imag(zc)>=0 else '-'} j{abs(np.imag(zc)):.3f})"
        
        pt = self.ax_smith.plot(x_ex, y_ex, marker='o', color=col, markersize=8, markeredgecolor='black', zorder=10)
        lbl = self.ax_smith.annotate(
            m_name, xy=(x_ex, y_ex), xytext=(8, 8), textcoords='offset points', 
            fontsize=10, fontweight='bold', color=col, zorder=11,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=col, alpha=0.8)
        )
        pt_cj = self.ax_smith.plot(x_cj, y_cj, marker='X', color=col, markersize=8, markeredgecolor='black', alpha=0.6, zorder=9)
        ln_cj = self.ax_smith.plot([x_ex, x_cj], [y_ex, y_cj], color=col, linestyle=':', alpha=0.5, zorder=8)
        dets = f"{m_name} ({ds['name']})\nfreq={f_ex:.3f}GHz\nPhase={p_deg:.3f}°\nZ = {z_str}\nZ_Match = {z_cj_str}"
        self.active_markers_smith.append({'name': m_name, 'x': x_ex, 'y': y_ex, 'pt': pt, 'lbl': lbl, 'details': dets, 'pt_conj': pt_cj, 'line_conj': ln_cj, 'freq': f_ex, 'phase': p_deg})
        self.update_smith_summary()

    def add_marker_from_ui(self):
        if not self.loaded_datasets: return
        try: tgt = float(self.entry_x_target.get())
        except ValueError: return messagebox.showerror("Error", "Invalid X.")
        ds = next((d for d in self.loaded_datasets if d['name'] == self.combo_trace.get()), None)
        if not ds: return
        idx_tab = self.notebook.index(self.notebook.select())
        if idx_tab == 0: self.add_marker_rect(tgt, ds)
        elif idx_tab == 1 and ds.get('is_rf'): self.add_marker_smith_by_idx(ds, np.abs(ds['freq'] - tgt).argmin())

    def clear_markers(self):
        for m in self.active_markers: m['pt'][0].remove(); m['lbl'].remove()
        for m in self.active_markers_smith: m['pt'][0].remove(); m['lbl'].remove(); m['pt_conj'][0].remove(); m['line_conj'][0].remove()
        self.active_markers.clear(); self.active_markers_smith.clear()
        self.marker_counter_rect = self.marker_counter_smith = 0 
        self.update_rect_summary(); self.update_smith_summary()

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalDataAnalyzer(root)
    root.mainloop()