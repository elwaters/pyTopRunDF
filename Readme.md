# pyTopRunDF

A two dimensional runout simulation tool for debris flows to predict inundation areas on torrential fans.
Calculations are based on a semi-empirical runout prediction model for volcanic mudflows (lahars) as proposed by
[Iverson et al. (1998)](https://doi.org/10.1130/0016-7606(1998)110<0972:ODOLIH>2.3.CO;2)
They determined power-law relationships between the planimetric area of the deposits (B) and the deposit volume (V) by assuming geometric similarity:  
$V=B\overline{h}$  
with $B$ the deposited area and $\overline{h}$ the average deposition height.  

Iverson et al. (1998) suggest geometric similarity between $B$ and $\overline{h}$ by assuming a constant ratio $\epsilon$ which yields to:  
<center> 
$\overline{h}=B^{1/2}\epsilon$  
$B^{1/2}\epsilon=VB^{-1}$  
$B=\epsilon^{-2/3}V^{2/3}$  
$B=k_BV^{2/3}$  
</center>

## Features

-   Model potential 2D debris-flow deposition (heights) based on a given event volume and a mobility coefficient.
-   Accounts for the fan topography.

## Instructions

-   See [instructions](docs/Instructions.md)

## Requirements

-   Python 3.8 or higher
-   pip (Python package manager)

## How to Run

### Step 1: Clone the Repository

First, clone this repository to your local machine:

``` bash
git clone <https://github.com/schidli/pyTopRunDF.git>

cd pyTopRunDF
```

### Step 2: Create a Virtual Environment

Create a virtual environment to isolate the dependencies:

``` bash
python -m venv pytoprundf
```

Activate the virtual environment

-   on Windows:

``` bash
pytoprundf\Scripts\activate
```

-   on MacOS/Linux:

``` bash
source pytoprundf\Scripts\activate
```

### Step 3: Install Dependencies

Install the required Python packages using the requirements.txt file:

``` bash
pip install -r requirements.txt
```

### Step 4: Run the Script

Run the main script:

``` bash
python TopRunDF.py
```

### Step 5: View the Results

The script will generate output files (e.g., depo.asc) and display a plot of the results. Check the output directory for the generated files.

Project Structure:

```         
pyTopRunDF/
├── TopRunDF.py:          Main script for the simulation.
├── input.json:            Input data file.
├── DEM/
│   ├── topofan.asc:      Input digital terrain model (DTM).
│   └── depo.asc:         Output deposition raster.
├── RandomSingleFlow.py:  External Python file for random walk logic.
└── requirements.txt:     Python dependencies.
```
