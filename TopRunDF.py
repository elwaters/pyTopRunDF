# -*- coding: utf-8 -*-
import rasterio
import os
import sys
import numpy as np
import json
import pandas as pd
from pathlib import Path  # For cross-platform path handling
import matplotlib.pyplot as plt
import RandomSingleFlow as randomsfp
import argparse
import mmap
from scipy.ndimage import convolve
from PlotResult import HillshadePlotter
import matplotlib as mpl

# Set global font size for plots
mpl.rcParams['font.size'] = 8  # Set font size to 12
mpl.rcParams['axes.titlesize'] = 12  # Set title font size
mpl.rcParams['axes.labelsize'] = 8  # Set axis label font size
mpl.rcParams['xtick.labelsize'] = 8  # Set x-axis tick font size
mpl.rcParams['ytick.labelsize'] = 8  # Set y-axis tick font size


#################################################################################################
# Funktion zum Testen ob unterschiedliche Dezimaltrennzeichen in den Rasterdaten vorliegen
def needs_preprocessing(file_path):
    """Check if the file contains commas as decimal separators."""
    with open(file_path, "r", encoding="utf-8") as f:
        with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
            return b',' in mm
#################################################################################################
def preprocess_raster(file_path):
    """Preprocess raster file to replace commas with periods in numeric values."""
    if not needs_preprocessing(file_path):
        return file_path  # Return the original file if no preprocessing is needed

    temp_file = file_path.with_suffix(".asc")  # Create a temporary file

    with open(file_path, "r", encoding="utf-8") as f_in:
        # Map the file into memory
        with mmap.mmap(f_in.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
            # Read the entire file content
            content = mm.read().decode("utf-8")
            # Replace commas with periods
            updated_content = content.replace(",", ".")
            # Ensure no extra newlines are introduced
            updated_content = "\n".join(line.strip() for line in updated_content.splitlines())

    # Write the updated content to a temporary file
    with open(temp_file, "w", encoding="utf-8") as f_out:
        f_out.write(updated_content)

    return temp_file

#################################################################################################
# Funktion zur Adaptierung unterschiedlicher Dezimaltrennzeichen für Eingabewerte
def parse_decimal(input_string):
    # Prüfen, ob ein Komma als Dezimaltrennzeichen verwendet wird
    if ',' in input_string and '.' not in input_string:
        input_string = input_string.replace(',', '.')
    try:
        return float(input_string)
    except ValueError:
        raise ValueError("Invalid input. Please enter a number with a valid decimal separator.")

#################################################################################################

# Start of the main script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run deposition simulation for a given scenario.")
    parser.add_argument("--input", required=True, help="Path to the input JSON file.")
    parser.add_argument("--dem", required=True, help="Path to the topography file (topofan.asc).")
    parser.add_argument("--output", required=True, help="Path to save the output files.")
    args = parser.parse_args()

    input_file = Path(args.input)
    dem_file = Path(args.dem)
    output_dir = Path(args.output)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    fin = None
    eventname = input_file.stem
    output_raster_path = output_dir / "depo.asc"

    try:
        # Load input.json
        with open(input_file, "r", encoding="utf-8") as f:
            input_data = json.load(f)

        # Extract parameters from input.json
        artificial_height = input_data["energy_height"]
        if artificial_height == "elevation":
            artificial_raster_height = rasterio.open(output_dir / "elevation.asc")
        else:
            artificial_height = parse_decimal(str(artificial_height))

        eventname = input_data["name"]
        XKoord = parse_decimal(str(input_data["X_coord"]))
        YKoord = parse_decimal(str(input_data["Y_coord"]))
        volume = parse_decimal(str(input_data["volume"]))
        coefficient = parse_decimal(str(input_data["coefficient"]))

        # Open the DEM file
        # Preprocess the DEM file if necessary
        processed_dem_file = preprocess_raster(dem_file)
        dataset = rasterio.open(processed_dem_file)
        band = dataset.read(1)
        gridsize = dataset.res[0]
        # Initialize variables
        simarea = volume ** (2 / 3) * coefficient
        perimeter = simarea / gridsize**2
        row, col = dataset.index(XKoord, YKoord)
        band2 = np.copy(band)
        band3 = np.copy(band)
        band3.fill(0)
        area = 0
        mcsmax = 500

        # Flowpath simulation
        for x in range(0, 100000):
            if area >= perimeter:
                break
            else:
                # In order to avoid implausible deposition heights due to an identical starting point, each starting point of a single flow run is determined randomly within a certain radius. 
                random_radius = 3  # Define the radius for random starting points to be defined; Default: 3 gridsizes.
                row = np.random.randint(max(0, row - random_radius), min(dataset.height, row + random_radius))
                col = np.random.randint(max(0, col - random_radius), min(dataset.width, col + random_radius))
                position = [row, col]
                band2.fill(0)
                mcs = 0
                while (
                    mcs < mcsmax
                    and position[0] <= dataset.height - 1
                    and position[1] <= dataset.width - 1
                ):
                    if position[0] > 0 and position[1] > 0:
                        if area >= perimeter:
                            break
                        else:
                            # Adjust energy height dynamically to avoid unplausible depo-heights at the start cell.
                            # The denominator in the exponent of the decay_factor (default: 100) scales the "range" of the 
                            # decay. A larger denominator results in slower decay, meaning the decay factor remains 
                            # significant over longer distances. A smaller denominator causes faster decay, meaning 
                            # the decay factor approaches zero more quickly.
                            distance = np.sqrt((position[0] - row)**2 + (position[1] - col)**2)
                            decay_factor = np.exp(-distance / 100)  # Example decay factor with denominantor=100
                            if isinstance(artificial_height, float):
                                temp_height = artificial_height * gridsize * decay_factor
                            else:
                                temp_height = (
                                    artificial_raster_height.read(1)[position[0], position[1]]
                                    * gridsize * decay_factor
                                )
                            obj1 = randomsfp.MonteCarloSingleFlowPath(
                                dataset, band2, position, temp_height
                            )
                            position = obj1.NextStartCell()
                            band2[position[0], position[1]] = True
                            band3[position[0], position[1]] += 1
                            if band3[position[0], position[1]] == 1:
                                area += 1
                    else:
                        mcs += 1
                        position = [row, col]
                        band2.fill(0)

        band3[0, 0] = 0
        max_val = np.amax(band3)
        band3 = band3 / max_val
        meanh = volume / perimeter
        band4 = band3 * meanh

        dummy = np.sum(band3)
        diff = volume / (dummy * gridsize**2)
        meannew = meanh * diff
        band4 = band3 * meannew
        #############################################################################################
        # Several strategies for distributing the input volume plausibly across the storage area:
        #############################################################################################
        # --A-- # Diffusion algorithm:
        # A diffusion algorithm is a method used to smooth values in a grid or matrix 
        # and distribute them more evenly. It simulates the physical process of diffusion, 
        # in which material or energy moves from areas of high concentration to areas of low 
        # concentration.
        kernel = np.array([[0.05, 0.1, 0.05],
                           [0.1, 0.4, 0.1],
                           [0.05, 0.1, 0.05]])
        band4 = convolve(band4, kernel, mode='constant', cval=0.0)
         #############################################################################################
        # --B-- # Apply Gaussian smoothing to reduce sharp peaks
        #from scipy.ndimage import gaussian_filter
        #band4 = gaussian_filter(band4, sigma=2)
        #############################################################################################
        # --C-- # Ablagerungshöhe über mittlere Ablagerungshöhe normiert:
        #band4 = band4 / np.max(band4) * meanh
        
        # Adjust deposition values to match input volume
        total_deposited_volume = np.sum(band4) * gridsize**2
        volume_difference = volume - total_deposited_volume
        if abs(volume_difference) > 1e-6:
            adjustment_factor = volume / total_deposited_volume
            band4 *= adjustment_factor
            print(f"Adjusted deposition values by factor: {adjustment_factor}")
        else:
            print("Deposition volume matches input volume.")

        # Save the output raster
        out_meta = dataset.meta.copy()
        out_meta.update({"driver": "AAIGrid", "dtype": "float32"})
        with rasterio.open(output_raster_path, "w", **out_meta) as dest:
            dest.write(band4, 1)
        # Clean up the temporary file if preprocessing was done
        if processed_dem_file != dem_file:
            processed_dem_file.unlink()  # Deletes the temporary file
        fin = "finished"

    except Exception as e:
        print(f"Error during simulation: {e}")
        fin = "terminated"

    finally:
        if fin is None:
            fin = "terminated"
        print("Simulation", fin)

    if fin == "finished":
        plotter = HillshadePlotter()
        try:
            plotter.plot(output_raster_path, dem_file, eventname, output_dir)
            plotter.plot_interactive_3d(
                output_raster_path, dem_file, eventname, output_dir
            )
            plotter.export_plotly_3d(
                output_raster_path, dem_file, eventname, output_dir
            )
            plotter.export_pyvista_3d(
                output_raster_path, dem_file, eventname, output_dir, show=False
            )
        except Exception as plot_error:
            print(f"Error during plotting: {plot_error}")
