
# RF Data & Smith Chart Analyzer

This tool provides high-precision visualization and analysis for S-parameter data, streamlining the testing phase of microstrip antenna systems.

## Features

* **Universal Data Parsing:** Natively handles Touchstone files (`.s1p` to `.s4p`) as well as standard `.csv` and `.txt` measurement data.
* **Interactive Visualization:**
* **2D Plotting:** Real-time plotting of reflection coefficients ($S_{11}$) in dB.
* **Smith Chart:** Dynamic RF impedance visualization using `scikit-rf`.


* **Professional Marker System:**
* ADS-style marker displays including Frequency, Magnitude (dB), Phase (°), and Normalized Impedance ($Z = Z_0 \times (r \pm jx)$).
* Left-side summary panel for organized, report-ready data tracking.


* **Research-Grade Workflow:** Designed to support the simulation and experimental validation of dual-band rectenna systems.

## Technical Stack

* **Language:** Python 3.11
* **Core Libraries:**
* `scikit-rf`: For microwave network analysis and Smith Chart generation.
* `matplotlib`: For high-fidelity technical plotting.
* `tkinter`: For a lightweight, responsive graphical interface.
* `PyInstaller`: For standalone Windows deployment.



## Installation

1. Navigate to the **Releases** section on the right sidebar.
2. Download the latest `RF_Analyzer.exe`.
3. Run the application—no Python installation or environment setup required.

## Usage

* **Load Data:** Click the "Load Data" button to import your measurement files.
* **Add Markers:** Input a specific frequency and click "Add Marker" to analyze impedance at that point.
* **Analyze:** Use left-click to drop markers directly onto curves and right-click to remove them.
* **Report:** Use the built-in toolbar at the bottom of each tab to save high-resolution plots for your project reports.

---

*Developed by Hamza Amr.*

---
