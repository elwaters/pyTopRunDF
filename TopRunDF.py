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

import matplotlib as mpl

# Set global font size for plots
mpl.rcParams['font.size'] = 8  # Set font size to 12
mpl.rcParams['axes.titlesize'] = 12  # Set title font size
mpl.rcParams['axes.labelsize'] = 8  # Set axis label font size
mpl.rcParams['xtick.labelsize'] = 8  # Set x-axis tick font size
mpl.rcParams['ytick.labelsize'] = 8  # Set y-axis tick font size

#################################################################################################
# Funktion zur Erstellung eines Hillshades basierend auf einem digitalen Höhenmodell
def hillshade(array, azimuth, angle_altitude):
    """Creates a shaded relief file from a DEM."""
    from numpy import gradient, pi, arctan, arctan2, sin, cos, sqrt

    x, y = gradient(array)
    slope = pi / 2.0 - arctan(sqrt(x * x + y * y))
    aspect = arctan2(-x, y)
    azimuthrad = azimuth * pi / 180.0
    altituderad = angle_altitude * pi / 180.0

    shaded = (
        sin(altituderad) * sin(slope)
        + cos(altituderad) * cos(slope) * cos(azimuthrad - aspect)
    )
    return 255 * (shaded + 1) / 2
#################################################################################################
# Funktion zum Testen ob unterschiedliche Dezimaltrennzeichen in den Rasterdaten vorliegen
def needs_preprocessing(file_path):
    """Check if the file contains commas as decimal separators."""
    with open(file_path, "r", encoding="utf-8") as f:
        with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
            return b',' in mm
#################################################################################################
# Funktion zur Adaptierung unterschiedlicher Dezimaltrennzeichen in den Rasterdaten
def preprocess_raster(file_path):
    if not needs_preprocessing(file_path):
        return file_path  # Return the original file if no preprocessing is needed
    """Preprocess raster file to replace commas with periods in numeric values."""
    temp_file = file_path.with_suffix(".asc")  # Create a temporary file

    with open(file_path, "r+", encoding="utf-8") as f_in:
        # Map the file into memory
        with mmap.mmap(f_in.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
            # Read the entire file content
            content = mm.read().decode("utf-8")
            # Replace commas with periods
            updated_content = content.replace(",", ".")

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

        # Monte Carlo simulation
        for x in range(0, 100000):
            if area >= perimeter:
                break
            else:
                random_radius = 3  # Define the radius for random starting points
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
                            # Adjust artificial height dynamically
                            distance = np.sqrt((position[0] - row)**2 + (position[1] - col)**2)
                            decay_factor = np.exp(-distance / 100)
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

        # Apply diffusion smoothing
        kernel = np.array([[0.05, 0.1, 0.05],
                           [0.1, 0.4, 0.1],
                           [0.05, 0.1, 0.05]])
        band4 = convolve(band4, kernel, mode='constant', cval=0.0)

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
        output_raster_path = output_dir / "depo.asc"
        with rasterio.open(output_raster_path, "w", **out_meta) as dest:
            dest.write(band4, 1)

        # Plot the results
         # Read and process the output raster
            with open(output_raster_path, "r") as prism_f:
                prism_header = prism_f.readlines()[:6]

            prism_header = [item.strip().split()[-1] for item in prism_header]
            prism_cols = int(prism_header[0])
            prism_rows = int(prism_header[1])
            prism_xll = float(prism_header[2])
            prism_yll = float(prism_header[3])
            prism_cs = float(prism_header[4])
            prism_nodata = float(prism_header[5])

            prism_array = np.loadtxt(output_raster_path, dtype=np.float64, skiprows=6)
            a = np.ma.masked_where(prism_array < 0.005, prism_array)
            prism_array[prism_array == prism_nodata] = np.nan
             # Generate the hillshade for visualization
            hs_array = hillshade(band, azimuth=34, angle_altitude=45)
            # Plot the results
            cmap = plt.cm.OrRd
            cmap.set_bad(color="white")
            fig, ax = plt.subplots(figsize=(4.27, 3.2))
            ax.set_title(f"Deposition - {eventname}")
            prism_extent = [
                prism_xll,
                prism_xll + prism_cols * prism_cs,
                prism_yll,
                prism_yll + prism_rows * prism_cs,
            ]
            img_plot = ax.imshow(hs_array, extent=prism_extent, cmap="Greys")
            img_plot = ax.imshow(a, extent=prism_extent)
            cbar = plt.colorbar(img_plot, orientation="vertical", aspect=14)
            cbar.set_label("Deposition heights [m]")
            fin = "finished"
            #plt.show()

        # Save the plot
        output_plot_path = output_dir / f"{eventname}_deposition.png"
        fig.savefig(output_plot_path, dpi=300, bbox_inches="tight")
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