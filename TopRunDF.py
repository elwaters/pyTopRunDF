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
#################################################################################################
# Funktion zur Erstellung eines Hillshades basierend auf einem digitalen Höhenmodell
# Ein Test zum neuen Branch
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
# Funktion zur Adaptierung unterschiedlicher Dezimaltrennzeichen
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
    # Change to the script's directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    fin = None
    try:
        # Read the input.csv file
        input_file = script_dir / "input.json"
        with open(input_file, "r", encoding="utf-8") as f:
            input_data = json.load(f)  # JSON-Daten einlesen
    except BaseException as err:
        fin = "terminated"
        print("Error reading input.json:", err)
    else:
        # Extract the work path
        workpath = script_dir / "DEM"
        try:
            # Check if artificial height is specified
            artificial_height = input_data["energy_height"]
            if artificial_height == "elevation":
                artificial_raster_height = rasterio.open(workpath / "elevation.asc")
            else:
                #artificial_height = float(artificial_height)
                artificial_height = parse_decimal(str(artificial_height))
            eventname=input_data["name"]
            # Open the DEM file
            dataset = rasterio.open(workpath / "topofan.asc")
            band = dataset.read(1)

            # Generate hillshade
            hs_array = hillshade(band, 34, 45)

        except BaseException as err1:
            fin = "terminated"
            print("Error processing DEM or energy height too low:", err1)
        else:
            # Extract simulation parameters
            XKoord = parse_decimal(str(input_data["X_coord"]))
            YKoord = parse_decimal(str(input_data["Y_coord"]))
            volume = parse_decimal(str(input_data["volume"]))
            coefficient = parse_decimal(str(input_data["coefficient"]))
            gridsize = dataset.res[0]

            simarea = volume ** (2 / 3) * coefficient
            mcs = 0
            mcsmax = 500
            perimeter = simarea / gridsize**2
            row, col = dataset.index(XKoord, YKoord)
            band1 = dataset.read(1)
            band2 = np.copy(band1)
            band3 = np.copy(band1)
            band3.fill(0)
            area = 0

            # Monte Carlo simulation (not a real statistical MC simulation,repeating random walk)
            # Default 100.000 steps to find targeted deposition area on the topography
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
                                # Adjust artificial height dynamically to avoid unplausible depo-height
                                # at the start cell.
                                # The denominator in the exponent of the decay_factor (default 100) scales the "range" of the 
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
            # Mehrere Strategien um das Eingangsvolumen auf die Ablagerungsfläche plausibel zu verteilen:
            #############################################################################################
            # Diffusionsalgorithmus:
            # Ein Diffusionsalgorithmus ist eine Methode, die verwendet wird, um Werte in einem Raster oder einer Matrix 
            # zu glätten und gleichmäßiger zu verteilen. Er simuliert den physikalischen Prozess der Diffusion, 
            # bei dem sich Material oder Energie von Bereichen mit hoher Konzentration zu Bereichen mit niedriger 
            # Konzentration bewegt.
            from scipy.ndimage import convolve
            kernel = np.array([[0.05, 0.1, 0.05],
                   [0.1, 0.4, 0.1],
                   [0.05, 0.1, 0.05]])
            band4 = convolve(band4, kernel, mode='constant', cval=0.0)
            #############################################################################################
            # Apply Gaussian smoothing to reduce sharp peaks
            #from scipy.ndimage import gaussian_filter
            #band4 = gaussian_filter(band4, sigma=2)
            #############################################################################################
            # Ablagerungshöhe über mittlere Ablagerungshöhe normiert:
            #band4 = band4 / np.max(band4) * meanh
            total_deposited_volume = np.sum(band4) * gridsize**2  # Calculate total volume
            volume_difference = volume - total_deposited_volume  # Difference between input and deposited volume
            if abs(volume_difference) > 1e-6:  # Allow a small tolerance for floating-point errors
            # Adjust deposition values proportionally to match the input volume
                adjustment_factor = volume / total_deposited_volume
                band4 *= adjustment_factor
                print(f"Adjusted deposition values by factor: {adjustment_factor}")
            else:
                print("Deposition volume matches input volume.")
            
            # Save the output raster
            out_meta = dataset.meta.copy()
            with rasterio.open(workpath / "depo.asc", "w", **out_meta) as dest:
                dest.write(band4, 1)

            # Read and process the output raster
            with open(workpath / "depo.asc", "r") as prism_f:
                prism_header = prism_f.readlines()[:6]

            prism_header = [item.strip().split()[-1] for item in prism_header]
            prism_cols = int(prism_header[0])
            prism_rows = int(prism_header[1])
            prism_xll = float(prism_header[2])
            prism_yll = float(prism_header[3])
            prism_cs = float(prism_header[4])
            prism_nodata = float(prism_header[5])

            prism_array = np.loadtxt(workpath / "depo.asc", dtype=np.float64, skiprows=6)
            a = np.ma.masked_where(prism_array < 0.005, prism_array)
            prism_array[prism_array == prism_nodata] = np.nan

            # Plot the results
            cmap = plt.cm.OrRd
            cmap.set_bad(color="white")
            fig, ax = plt.subplots()
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
            plt.show()
    finally:
        if fin is None:
            fin = "terminated"
        print("Simulation", fin)