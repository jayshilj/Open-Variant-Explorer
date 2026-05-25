# 📊 Open-Variant Explorer

### *Open-Source Process Mining, Discovery & Variant Analysis Dashboard*

Open-Variant Explorer is a professional-grade, self-hosted process mining application that mirrors the core analysis features of enterprise tools like **Celonis**. 

Built with **Python**, **Streamlit**, and the industry-standard **PM4Py** engine, it allows business analysts, consultants, and developers to instantly ingest event logs, discover execution paths, explore process variants, and locate SLA bottlenecks—all within a clean, modern web interface.

---

## 🚀 Key Features

### 1. 📡 Process Map Discovery (DFG)
* **Directly-Follows Graph (DFG)**: Discover how processes flow in practice based on real event log history.
* **Dual Performance Metrics**: 
  * Toggle the DFG to display **Case Frequencies** (throughput volumes).
  * Toggle to display **Performance (Average / Median Durations)** to pinpoint bottlenecks.
* **Physics-Based Graphs**: Fully interactive graph layouts with drag-and-drop nodes, zooming, and tooltips.
* **⚙️ Dynamic Physics controls**: Collapsible sliders to customize node repulsion gravity and connection spring distance in real-time.

### 2. 🧬 Variant Explorer
* **Path Sequencing**: Categorize and rank every unique sequence of activities (variants) present in the log.
* **Frequency Analysis**: Instantly see what percentage of cases follow the standard path (happy path) vs. custom/edge-case loops.
* **Dynamic DFG Highlighting**: Selecting a specific variant highlights only its corresponding nodes and transitions on the process map.

### 3. ⏱️ Lead Time & SLA Analytics
* **Throughput Time Distribution**: Analyze cycle times across all cases with violin/histogram visualizations.
* **Customizable SLA Targets**: Adjustable SLA input slider reactively flags compliant vs violating case flows.
* **SLA Compliance Donut Visuals**: High-level donut chart displays compliant case share percentages instantly.
* **Bottleneck Ledger**: Interactive ledger lists all cases with custom status emoji badges (`🚨 Violation` vs `✅ Compliant`).

### 4. 📊 Activity Outbound Latency (New!)
* **Activity Waiting Times**: Discover average waiting/idle duration triggered immediately following each individual activity node.
* **Operational Frequencies**: Detailed frequency distribution table sorting unique steps executed in the event log.

---

## 🛠️ Tech Stack
* **UI/Frontend**: Streamlit (Modern dashboard design system)
* **Process Mining Core**: PM4Py (Process Mining for Python)
* **Visualizations**: Plotly (interactive charts), Graphviz / Pyvis (dynamic network graphs)
* **Data Processing**: Pandas & DuckDB (blazing-fast event log preprocessing)

---

## 📂 Project Structure
```plaintext
Open-Variant-Explorer/
├── app.py                 # Main Streamlit application entry point
├── Makefile               # UNIX builder directives (run, test, clean)
├── run_tests.ps1          # Windows automated PowerShell test runner
├── src/
│   ├── parser.py          # Log parser and PM4Py aggregation pipelines
│   └── visualizer.py      # Process map network rendering logic
├── tests/
│   ├── __init__.py        # Python package definition
│   └── test_parser.py     # Unit tests for log parsing & validators
├── datasets/              # Sample CSV/XES event logs for testing
│   ├── sample_o2c.csv     # 105-case Order-to-Cash process
│   └── sample_financial.csv # Financial loan approval process template
├── requirements.txt       # Project dependencies
├── .gitignore             # Git ignore patterns
└── README.md              # Documentation
```

---

## 📦 Installation & Setup

### Prerequisites
* Python 3.9+

### Setup and Running with Makefile (UNIX/macOS)
```bash
# Run the test suite
make test

# Start the Streamlit application
make run

# Clean cache directories
make clean
```

### Setup and Running with PowerShell (Windows)
```powershell
# Run the test suite
.\run_tests.ps1

# Run the Streamlit application
.\venv\Scripts\streamlit run app.py
```

---

## 🛡️ License
Distributed under the **MIT License**. See `LICENSE` for details.
