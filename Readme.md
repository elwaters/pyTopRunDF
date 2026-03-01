# pyTopRunDF

A fast, two-dimensional runout simulation tool for debris flows to estimate potential inundation (deposition) areas on torrential fans.

## Background

pyTopRunDF implements a semi-empirical runout prediction approach originally proposed for volcanic mudflows (lahars) by
[Iverson et al. (1998)](https://doi.org/10.1130/0016-7606(1998)110<0972:ODOLIH>2.3.CO;2).
They describe power-law relationships between the planimetric deposit area **B** and the deposit volume **V**, assuming geometric similarity:

\[
V = B \, \overline{h}
\]

where **B** is the deposited area and \(\overline{h}\) is the mean deposition thickness.

Geometric similarity between **B** and \(\overline{h}\) is expressed using a constant ratio \(\epsilon\), leading to:

<div style="display: flex; justify-content: center;">
  <img src="docs/geometric similarity.png" alt="Geometric similarity concept" width="300">
</div>

The potential deposition area **B** can then be estimated from event volume **V** and a mobility coefficient \(k_B\),
which captures average flow mobility during deposition:

\[
B = k_B V^{2/3}
\]

### Typical ranges of mobility coefficients \(k_B\) for alpine mass movements

| Study | Process Type | \(k_B\) |
|------|--------------|--------:|
| [Crosta (2003)](https://doi.org/10.5194/nhess-3-407-2003) | Granular debris flows | 6 |
| [Scheidl and Rickenmann (2010)](https://doi.org/10.1002/esp.1897) | Granular debris flows (IT) | 18 |
| [Griswold (2004)](https://doi.org/10.3133/sir20075276) | Debris flows | 19 |
| [Berti (2007)](https://doi.org/10.1016/j.geomorph.2007.01.014) | Debris flows | 30 |
| [Scheidl and Rickenmann (2010)](https://doi.org/10.1002/esp.1897) | Debris flows (CH) | 32 |
| [Scheidl and Rickenmann (2010)](https://doi.org/10.1002/esp.1897) | Debris flows (AUT) | 45 |
| [Capra (2002)](https://doi.org/10.1016/S0377-0273(01)00252-9) | Earth slides | 51 |
| [Scheidl and Rickenmann (2010)](https://doi.org/10.1002/esp.1897) | Debris floods (AUT) | 57 |
| [Waythomas (2000)](https://doi.org/10.1016/S0377-0273(00)00202-X) | Volcanic earth flows | 92 |
| [Iverson et al. (1998)](https://doi.org/10.1130/0016-7606(1998)110<0972:ODOLIH>2.3.CO;2) | Lahars | 200 |

## Features

- **2D deposition modelling** (deposit height / thickness) from event volume \(V\) and mobility coefficient \(k_B\)
- **Fast computation**
- **Topography-aware** (fan surface influences deposition patterns)
- Designed for **preliminary hazard zoning / screening**

## Documentation

- Detailed usage notes: see [`docs/Instructions.md`](docs/Instructions.md)

## Requirements

- **Python 3.8+** (tested successfully with **Python 3.11**)
- `pip`

> Tip: If installation fails on older Python versions due to dependency constraints, use Python **3.11**.

## Installation

### 1) Clone the repository

Run: `git clone https://github.com/schidli/pyTopRunDF.git`  
Then: `cd pyTopRunDF`

### 2) Create and activate a virtual environment

**macOS / Linux**

- Create: `python3 -m venv pytoprundf`
- Activate: `source pytoprundf/bin/activate`

**Windows (PowerShell)**

- Create: `python -m venv pytoprundf`
- Activate: `.\pytoprundf\Scripts\Activate.ps1`

### 3) Upgrade pip tooling (recommended)

Run: `python -m pip install --upgrade pip setuptools wheel`

### 4) Install dependencies

Run: `pip install -r requirements.txt`

## Running the model

### Batch run (multiple scenarios)

Run: `python batch_selected_process.py`

## Inputs and outputs

### Scenarios

Each scenario folder contains:

- `topofan.asc` — input DTM raster (ASCII grid)
- `input.json` — scenario configuration / event parameters

### Outputs

For each scenario, results are written to an output folder, for example:

- `depo.asc` — output deposition raster (ASCII grid)
- `<eventname>_deposition.png` — result plot

## Project structure

pyTopRunDF/  
├── batch_selected_process.py        # Start script (batch runs)  
├── TopRunDF.py                      # Main simulation logic  
├── Scenarios/  
│   ├── Scenario_1/  
│   │   ├── topofan.asc              # Input DTM (ASCII grid)  
│   │   └── input.json               # Scenario input parameters  
│   ├── Scenario_2/  
│   │   ├── topofan.asc  
│   │   └── input.json  
│   └── ...  
├── Outputs/  
│   ├── Scenario_1/  
│   │   ├── depo.asc                 # Output deposition raster  
│   │   └── <eventname>_deposition.png  
│   └── ...  
├── RandomSingleFlow.py              # Random walk logic  
├── PlotResult.py                    # Plotting utilities  
└── requirements.txt                 # Python dependencies  

## Citation

If you use pyTopRunDF in academic or technical work, please cite:

- Iverson, R. M., Schilling, S. P., & Vallance, J. W. (1998). *Objective delineation of lahar-inundation hazard zones*. Geological Society of America Bulletin, 110(8), 972–984. https://doi.org/10.1130/0016-7606(1998)110<0972:ODOLIH>2.3.CO;2