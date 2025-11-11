import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

class HillshadePlotter:
    def __init__(self):
        pass

    @staticmethod
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

    def plot(self, depo_path, dem_path, eventname, outdir):
        """
        Plots the deposition result on the hillshade based on the DEM.

        Parameters:
        - depo_path: Path to the deposition raster file.
        - dem_path: Path to the digital elevation model (DEM) raster file.
        - eventname: Title of the plot.
        - outdir: Directory to save the output plot.
        """
        # Read DEM and deposition data
        with open(dem_path, "r") as dem_f:
            dem_header = dem_f.readlines()[:6]

        dem_header = [item.strip().split()[-1] for item in dem_header]
        dem_cols = int(dem_header[0])
        dem_rows = int(dem_header[1])
        dem_xll = float(dem_header[2])
        dem_yll = float(dem_header[3])
        dem_cs = float(dem_header[4])
        dem_nodata = float(dem_header[5])

        dem_array = np.loadtxt(dem_path, dtype=np.float64, skiprows=6)
        dem_array[dem_array == dem_nodata] = np.nan

        # Generate the hillshade for visualization
        hs_array = self.hillshade(dem_array, azimuth=34, angle_altitude=45)

        # Read deposition data
        depo_array = np.loadtxt(depo_path, dtype=np.float64, skiprows=6)
        depo_array = np.ma.masked_where(depo_array < 0.005, depo_array)

        # Plot the results
        cmap = plt.cm.OrRd
        cmap.set_bad(color="white")
        fig, ax = plt.subplots(figsize=(4.27, 3.2))
        ax.set_title(f"Deposition - {eventname}")
        dem_extent = [
            dem_xll,
            dem_xll + dem_cols * dem_cs,
            dem_yll,
            dem_yll + dem_rows * dem_cs,
        ]
        img_plot = ax.imshow(hs_array, extent=dem_extent, cmap="Greys")
        img_plot = ax.imshow(depo_array, extent=dem_extent, cmap=cmap, alpha=0.7)
        cbar = plt.colorbar(img_plot, orientation="vertical", aspect=14)
        cbar.set_label("Deposition heights [m]")
        plt.show()
        # Save the plot
        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        output_plot_path = outdir / f"{eventname}_deposition.png"
        fig.savefig(output_plot_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

        print(f"Plot saved to {output_plot_path}")