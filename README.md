

# Universal Data & RF Analyzer - Rectenna Edition 📡

A comprehensive, Python-based Electronic Design Automation (EDA) dashboard built to analyze RF networks, evaluate antenna radiation patterns, and calculate composite right/left-handed (CRLH) metamaterial parameters.

This software was developed specifically as the computational engineering tool for our **Electrical and Electronics Engineering Graduation Project** at **Badr University Cairo**.

## Project Context 🎓

This tool was created to support the research, design, and mathematical verification of our final thesis:
**"Design and Implementation of a Dual-Band Microstrip Rectenna System for Sustainable Energy Harvesting in Wi-Fi Networks."**


## Key Features ⚙️

* **Interactive 2D Plotting:** Load standard `.csv` or `.txt` data files to visualize circuit parameters with an interactive, highly tolerant click-to-pin marker system.
* **Touchstone & Smith Chart Integration:** Import standard `.sNp` files (like `.s1p` and `.s2p`) directly from Keysight ADS or CST Studio. Dynamically tracks markers across a 2D magnitude plot and an RF Impedance Smith Chart simultaneously, while automatically calculating and plotting the conjugate matching target ($Z_{Match}$).
* **CST Farfield Parser:** A robust data parser built to read raw ASCII Farfield Directivity/Gain exports from CST Studio. Automatically translates multi-column spatial data into highly formatted, presentation-ready polar plots.
* **Metamaterial Phase Solver:** An analytical tool designed to extract the Right-Handed ($L_R$, $C_R$) and Left-Handed ($L_L$, $C_L$) unit cell parameters required for dual-band phase compensation. It intelligently scales between Standard RH Microstrip mode and Dual-Band CRLH Metamaterial mode.
* **Automated PDF Reporting:** A one-click documentation tool that compiles all active graphs, Smith Charts, Polar Plots, and terminal math derivations into a clean, formatted PDF for academic reporting.

## Technology Stack 💻

* **Language:** Python
* **GUI Framework:** Tkinter (Modern Clam Theme)
* **RF Analysis:** scikit-rf
* **Data Handling & Parsing:** Pandas, NumPy
* **Data Visualization:** Matplotlib

## How to Run 🚀

1. Clone this repository to your local machine.
2. Ensure you have the required dependencies installed: `pip install numpy pandas matplotlib scikit-rf`
3. Run the main script: `python graph_plot.py`
4. Alternatively, use the standalone executable (`.exe`) provided in the latest release!
