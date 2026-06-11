import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import numpy as np
import pandas as pd
import os
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import skrf as rf

class UniversalDataAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Data & RF Analyzer")
        self.root.geometry("1350x850") # Slightly wider to fit the new button
        
        self.loaded_datasets = []
        self.active_markers = []          
        self.active_markers_smith = []    
        self.marker_counter_rect = 0
        self.marker_counter_smith = 0     
        
        self.colors = ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
        
        self.setup_ui()
        self.setup_plots()

    def setup_ui(self):
        # --- TOP CONTROL PANEL ---
        control_frame_top = ttk.Frame(self.root, padding="5")
        control_frame_top.pack(side=tk.TOP, fill=tk.X)
        
        self.btn_load = ttk.Button(control_frame_top, text="📁 Load Data (.sNp / .csv / .txt)", command=self.load_file)
        self.btn_load.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(control_frame_top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Label(control_frame_top, text="Target X-Value:").pack(side=tk.LEFT, padx=5)
        self.entry_x_target = ttk.Entry(control_frame_top, width=10)
        self.entry_x_target.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame_top, text="Trace:").pack(side=tk.LEFT, padx=5)
        self.combo_trace = ttk.Combobox(control_frame_top, state="readonly", width=18)
        self.combo_trace.pack(side=tk.LEFT, padx=5)
        
        # NEW: Remove Trace Button
        self.btn_remove = ttk.Button(control_frame_top, text="🗑️ Remove Trace", command=self.remove_trace)
        self.btn_remove.pack(side=tk.LEFT, padx=5)
        
        self.btn_add_marker = ttk.Button(control_frame_top, text="➕ Add Marker", command=self.add_marker_from_ui)
        self.btn_add_marker.pack(side=tk.LEFT, padx=5)
        
        self.btn_clear = ttk.Button(control_frame_top, text="❌ Clear Markers", command=self.clear_markers)
        self.btn_clear.pack(side=tk.LEFT, padx=15)

        # --- SECOND CONTROL PANEL (Custom Labels) ---
        control_frame_bot = ttk.Frame(self.root, padding="5")
        control_frame_bot.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Label(control_frame_bot, text="Graph Title:").pack(side=tk.LEFT, padx=5)
        self.entry_title = ttk.Entry(control_frame_bot, width=25)
        self.entry_title.insert(0, "Universal Data Plot")
        self.entry_title.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame_bot, text="X-Axis:").pack(side=tk.LEFT, padx=15)
        self.entry_xlabel = ttk.Entry(control_frame_bot, width=15)
        self.entry_xlabel.insert(0, "X-Axis")
        self.entry_xlabel.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame_bot, text="Y-Axis:").pack(side=tk.LEFT, padx=15)
        self.entry_ylabel = ttk.Entry(control_frame_bot, width=15)
        self.entry_ylabel.insert(0, "Y-Axis")
        self.entry_ylabel.pack(side=tk.LEFT, padx=5)
        
        self.btn_update_axes = ttk.Button(control_frame_bot, text="🔄 Update Graph Labels", command=self.update_axis_labels)
        self.btn_update_axes.pack(side=tk.LEFT, padx=15)

    def setup_plots(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.tab_rect = ttk.Frame(self.notebook)
        self.tab_smith = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_rect, text='📈 2D Plot (Universal)')
        self.notebook.add(self.tab_smith, text='🎯 Smith Chart (Touchstone Only)')
        
        # --- RECTANGULAR PLOT SETUP ---
        self.fig_rect, self.ax_rect = plt.subplots(figsize=(10, 6))
        self.fig_rect.subplots_adjust(left=0.28, right=0.95, top=0.9, bottom=0.1)
        self.ax_rect.set_title('Universal Data Plot', fontsize=14, fontweight='bold')
        self.ax_rect.set_xlabel('X-Axis', fontsize=12)
        self.ax_rect.set_ylabel('Y-Axis', fontsize=12)
        self.ax_rect.grid(True, linestyle=':', alpha=0.6)
        
        self.rect_summary_text = self.fig_rect.text(0.02, 0.90, "", va='top', ha='left', fontsize=10, 
                                        bbox=dict(boxstyle="round,pad=0.5", fc="#f8f9fa", ec="gray", alpha=0.9))
        self.rect_summary_text.set_visible(False)
        
        self.canvas_rect = FigureCanvasTkAgg(self.fig_rect, master=self.tab_rect)
        
        toolbar_frame_rect = ttk.Frame(self.tab_rect)
        toolbar_frame_rect.pack(side=tk.BOTTOM, fill=tk.X)
        self.toolbar_rect = NavigationToolbar2Tk(self.canvas_rect, toolbar_frame_rect)
        
        self.canvas_rect.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # --- SMITH CHART SETUP ---
        self.fig_smith, self.ax_smith = plt.subplots(figsize=(8, 8))
        self.fig_smith.subplots_adjust(left=0.28, right=0.95, top=0.95, bottom=0.05)
        self.ax_smith.set_title('RF Impedance Smith Chart', fontsize=14, fontweight='bold')
        self.ax_smith.axis('off') 
        
        self.smith_summary_text = self.fig_smith.text(0.02, 0.95, "", va='top', ha='left', fontsize=10, 
                                        bbox=dict(boxstyle="round,pad=0.5", fc="#f8f9fa", ec="gray", alpha=0.9))
        self.smith_summary_text.set_visible(False)
        
        self.canvas_smith = FigureCanvasTkAgg(self.fig_smith, master=self.tab_smith)
        
        toolbar_frame_smith = ttk.Frame(self.tab_smith)
        toolbar_frame_smith.pack(side=tk.BOTTOM, fill=tk.X)
        self.toolbar_smith = NavigationToolbar2Tk(self.canvas_smith, toolbar_frame_smith)
        
        self.canvas_smith.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.fig_rect.canvas.mpl_connect('button_press_event', self.on_plot_click_rect)
        self.fig_smith.canvas.mpl_connect('button_press_event', self.on_plot_click_smith)

    def update_axis_labels(self):
        self.ax_rect.set_title(self.entry_title.get(), fontsize=14, fontweight='bold')
        self.ax_rect.set_xlabel(self.entry_xlabel.get(), fontsize=12)
        self.ax_rect.set_ylabel(self.entry_ylabel.get(), fontsize=12)
        self.canvas_rect.draw()

    def update_rect_summary(self):
        if not self.active_markers:
            self.rect_summary_text.set_visible(False)
        else:
            full_text = "--- 2D MARKERS ---\n\n"
            full_text += "\n\n".join([m['details'] for m in self.active_markers])
            self.rect_summary_text.set_text(full_text)
            self.rect_summary_text.set_visible(True)
        self.canvas_rect.draw()

    def update_smith_summary(self):
        if not self.active_markers_smith:
            self.smith_summary_text.set_visible(False)
        else:
            full_text = "--- SMITH MARKERS ---\n\n"
            full_text += "\n\n".join([m['details'] for m in self.active_markers_smith])
            self.smith_summary_text.set_text(full_text)
            self.smith_summary_text.set_visible(True)
        self.canvas_smith.draw()

    def load_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=(("Touchstone Files", "*.s1p *.s2p *.s3p *.s4p *.sp2"), ("Text/CSV Data", "*.txt *.csv"), ("All Files", "*.*"))
        )
        if not filepath: return 
            
        fname = os.path.basename(filepath)
        clean_name = os.path.splitext(fname)[0]
        ext = os.path.splitext(fname)[1].lower()
        color = self.colors[len(self.loaded_datasets) % len(self.colors)]
        
        is_touchstone = bool(re.match(r'^\.s\dp$', ext)) or ext == '.sp2'
        
        try:
            if is_touchstone:
                nw = rf.Network(filepath)
                x_val = nw.f / 1e9 
                y_val = nw.s_db[:, 0, 0] 
                s_complex = nw.s[:, 0, 0] 
                style = '-'
                is_rf_data = True
                
                nw.plot_s_smith(m=0, n=0, ax=self.ax_smith, label=clean_name, color=color, linewidth=2)
                self.canvas_smith.draw()

            elif ext in ['.csv', '.txt']:
                df = pd.read_csv(filepath, sep=r'[,\s;]+', engine='python', header=None, comment='!', skipinitialspace=True)
                df = df.apply(pd.to_numeric, errors='coerce').dropna(axis=1, how='all').dropna()
                
                if len(df) == 0:
                    messagebox.showerror("Error", f"{fname} is empty or unreadable.")
                    return
                if len(df.columns) < 2:
                    messagebox.showerror("Format Error", f"{fname} lacks 2 columns.")
                    return
                
                x_val = df.iloc[:, 0].to_numpy()
                y_val = df.iloc[:, 1].to_numpy()
                s_complex = None
                style = '--'
                is_rf_data = False
                nw = None
                
            else:
                messagebox.showerror("Error", "Unsupported file type.")
                return
                
            # Storing the skrf Network object 'nw' so we can redraw it later if needed
            dataset = {'name': clean_name, 'freq': x_val, 's11': y_val, 's_complex': s_complex, 
                       'color': color, 'is_rf': is_rf_data, 'nw': nw if is_rf_data else None}
            self.loaded_datasets.append(dataset)
            
            self.combo_trace['values'] = [ds['name'] for ds in self.loaded_datasets]
            self.combo_trace.current(len(self.loaded_datasets) - 1)
            
            self.ax_rect.plot(x_val, y_val, label=clean_name, color=color, linestyle=style, linewidth=2)
            self.ax_rect.relim()
            self.ax_rect.autoscale_view()
            self.ax_rect.legend(loc='best', fontsize=10)
            self.canvas_rect.draw()
            
        except Exception as e:
            messagebox.showerror("Loading Error", f"Failed to read {fname}\nError: {str(e)}")

    # --- NEW: REMOVE TRACE LOGIC ---
    def remove_trace(self):
        if not self.loaded_datasets: return
        selected_name = self.combo_trace.get()
        if not selected_name: return

        if not messagebox.askyesno("Confirm Remove", f"Are you sure you want to remove '{selected_name}'?"):
            return

        # 1. Remove from data list
        self.loaded_datasets = [ds for ds in self.loaded_datasets if ds['name'] != selected_name]

        # 2. Update Combobox
        self.combo_trace['values'] = [ds['name'] for ds in self.loaded_datasets]
        if self.loaded_datasets:
            self.combo_trace.current(len(self.loaded_datasets) - 1)
        else:
            self.combo_trace.set('')

        # 3. Clear all markers to prevent orphaned text
        self.clear_markers()

        # 4. Wipe both graphs completely clean
        self.ax_rect.clear()
        self.ax_smith.clear()

        # 5. Restore Graph Styling
        self.ax_rect.set_title(self.entry_title.get(), fontsize=14, fontweight='bold')
        self.ax_rect.set_xlabel(self.entry_xlabel.get(), fontsize=12)
        self.ax_rect.set_ylabel(self.entry_ylabel.get(), fontsize=12)
        self.ax_rect.grid(True, linestyle=':', alpha=0.6)

        self.ax_smith.set_title('RF Impedance Smith Chart', fontsize=14, fontweight='bold')
        self.ax_smith.axis('off')

        # 6. Re-plot whatever is left in the memory
        for ds in self.loaded_datasets:
            style = '-' if ds.get('is_rf') else '--'
            self.ax_rect.plot(ds['freq'], ds['s11'], label=ds['name'], color=ds['color'], linestyle=style, linewidth=2)
            
            if ds.get('is_rf') and ds.get('nw') is not None:
                ds['nw'].plot_s_smith(m=0, n=0, ax=self.ax_smith, label=ds['name'], color=ds['color'], linewidth=2)

        if self.loaded_datasets:
            self.ax_rect.legend(loc='best', fontsize=10)

        self.ax_rect.relim()
        self.ax_rect.autoscale_view()
        
        self.canvas_rect.draw()
        self.canvas_smith.draw()

    def add_marker_rect(self, target_x, dataset):
        idx = np.abs(dataset['freq'] - target_x).argmin()
        x_exact = dataset['freq'][idx]
        y_exact = dataset['s11'][idx]
        col = dataset['color']
        
        self.marker_counter_rect += 1
        m_name = f"m{self.marker_counter_rect}"
        
        pt = self.ax_rect.plot(x_exact, y_exact, marker='o', color=col, markersize=8, markeredgecolor='black', zorder=5)
        lbl = self.ax_rect.annotate(m_name, xy=(x_exact, y_exact), xytext=(8, 8), textcoords='offset points',
                    fontsize=10, fontweight='bold', color=col, zorder=6)
        
        details = f"{m_name} ({dataset['name']})\nX: {x_exact:.3g}\nY: {y_exact:.3g}"
        
        self.active_markers.append({'x': x_exact, 'y': y_exact, 'pt': pt, 'lbl': lbl, 'details': details})
        self.update_rect_summary()

    def add_marker_smith_by_idx(self, dataset, idx):
        f_exact = dataset['freq'][idx]
        s_val = dataset['s_complex'][idx]
        col = dataset['color']
        
        self.marker_counter_smith += 1
        m_name = f"m{self.marker_counter_smith}"
        
        x_exact = np.real(s_val)
        y_exact = np.imag(s_val)
        mag_lin = np.abs(s_val)
        phase_deg = np.angle(s_val, deg=True)
        
        if np.abs(s_val - 1.0) < 1e-6:
            z_str = "Z0 * (∞)"
        else:
            z_norm = (1 + s_val) / (1 - s_val)
            r_norm = np.real(z_norm)
            x_norm = np.imag(z_norm)
            sign = '+' if x_norm >= 0 else '-'
            z_str = f"Z0 * ({r_norm:.3f} {sign} j{abs(x_norm):.3f})"
            
        pt = self.ax_smith.plot(x_exact, y_exact, marker='o', color=col, markersize=8, markeredgecolor='black', zorder=10)
        lbl = self.ax_smith.annotate(m_name, xy=(x_exact, y_exact), xytext=(8, 8), textcoords='offset points',
                    fontsize=10, fontweight='bold', color=col, zorder=11)
        
        details = (
            f"{m_name} ({dataset['name']})\n"
            f"freq={f_exact:.3f}GHz\n"
            f"SP.S(1,1)={mag_lin:.3f} / {phase_deg:.3f}\n"
            f"impedance = {z_str}"
        )
        
        self.active_markers_smith.append({'x': x_exact, 'y': y_exact, 'pt': pt, 'lbl': lbl, 'details': details})
        self.update_smith_summary()

    def add_marker_from_ui(self):
        if not self.loaded_datasets: return
        try:
            target_x = float(self.entry_x_target.get())
        except ValueError:
            messagebox.showerror("Error", "Target X must be a valid number.")
            return
            
        selected_name = self.combo_trace.get()
        target_ds = next((ds for ds in self.loaded_datasets if ds['name'] == selected_name), None)
        if not target_ds: return
        
        current_tab = self.notebook.index(self.notebook.select())
        
        if current_tab == 0:
            self.add_marker_rect(target_x, target_ds)
        elif current_tab == 1:
            if not target_ds.get('is_rf', False):
                messagebox.showerror("Error", "Smith Chart markers are only for Touchstone (.sNp) files.")
                return
            idx = np.abs(target_ds['freq'] - target_x).argmin()
            self.add_marker_smith_by_idx(target_ds, idx)

    def clear_markers(self):
        for m in self.active_markers:
            m['pt'][0].remove(); m['lbl'].remove()
        self.active_markers.clear()
        self.marker_counter_rect = 0
        self.update_rect_summary()
        
        for m in self.active_markers_smith:
            m['pt'][0].remove(); m['lbl'].remove()
        self.active_markers_smith.clear()
        self.marker_counter_smith = 0 
        self.update_smith_summary()

    def on_plot_click_rect(self, event):
        if event.inaxes != self.ax_rect or self.toolbar_rect.mode != '': return
        click_x, click_y = event.xdata, event.ydata

        if event.button == 3 and self.active_markers: 
            x_range = self.ax_rect.get_xlim()[1] - self.ax_rect.get_xlim()[0]
            y_range = self.ax_rect.get_ylim()[1] - self.ax_rect.get_ylim()[0]
            min_dist, closest_idx = float('inf'), -1
            for idx, m in enumerate(self.active_markers):
                dist = ((m['x'] - click_x) / x_range)**2 + ((m['y'] - click_y) / y_range)**2
                if dist < min_dist:
                    min_dist, closest_idx = dist, idx
            if closest_idx != -1 and min_dist < 0.005:
                popped = self.active_markers.pop(closest_idx)
                popped['pt'][0].remove(); popped['lbl'].remove()
                self.update_rect_summary()
            return

        if event.button == 1 and self.loaded_datasets: 
            best_dist, best_ds = float('inf'), None
            for ds in self.loaded_datasets:
                idx = np.abs(ds['freq'] - click_x).argmin()
                dist = np.abs(ds['freq'][idx] - click_x)
                if dist < best_dist:
                    best_dist, best_ds = dist, ds
            if best_ds:
                self.add_marker_rect(click_x, best_ds)

    def on_plot_click_smith(self, event):
        if event.inaxes != self.ax_smith or self.toolbar_smith.mode != '': return
        click_x, click_y = event.xdata, event.ydata

        if event.button == 3 and self.active_markers_smith: 
            min_dist, closest_idx = float('inf'), -1
            for idx, m in enumerate(self.active_markers_smith):
                dist = (m['x'] - click_x)**2 + (m['y'] - click_y)**2
                if dist < min_dist:
                    min_dist, closest_idx = dist, idx
            if closest_idx != -1 and min_dist < 0.05:
                popped = self.active_markers_smith.pop(closest_idx)
                popped['pt'][0].remove(); popped['lbl'].remove()
                self.update_smith_summary()
            return

        if event.button == 1: 
            best_dist, best_ds, best_idx = float('inf'), None, -1
            for ds in self.loaded_datasets:
                if not ds.get('is_rf', False): continue 
                
                re_s = np.real(ds['s_complex'])
                im_s = np.imag(ds['s_complex'])
                
                dists = (re_s - click_x)**2 + (im_s - click_y)**2
                idx = dists.argmin()
                
                if dists[idx] < best_dist:
                    best_dist = dists[idx]
                    best_ds = ds
                    best_idx = idx
                    
            if best_ds and best_dist < 0.05: 
                self.add_marker_smith_by_idx(best_ds, best_idx)

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalDataAnalyzer(root)
    root.mainloop()