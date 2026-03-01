import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib import colors
from matplotlib.cm import ScalarMappable


class HillshadePlotter:
    def __init__(self, z_exag=3.0, deposition_z_scale=0.35, max_grid_size=400):
        self.z_exag = z_exag
        self.deposition_z_scale = deposition_z_scale
        self.max_grid_size = max_grid_size
        self.terrain_cmap = plt.cm.gist_earth
        self.overlay_cmap = plt.cm.OrRd
        self.lightsource = colors.LightSource(azdeg=315, altdeg=45)

    @staticmethod
    def hillshade(array, azimuth, angle_altitude):
        """Creates a shaded relief file from a DEM."""
        from numpy import arctan, arctan2, cos, gradient, pi, sin, sqrt

        if np.isnan(array).all():
            return np.zeros_like(array, dtype=np.float64)

        fill_value = np.nanmean(array)
        filled = np.where(np.isnan(array), fill_value, array)

        x, y = gradient(filled)
        slope = pi / 2.0 - arctan(sqrt(x * x + y * y))
        aspect = arctan2(-x, y)
        azimuthrad = azimuth * pi / 180.0
        altituderad = angle_altitude * pi / 180.0

        shaded = (
            sin(altituderad) * sin(slope)
            + cos(altituderad) * cos(slope) * cos(azimuthrad - aspect)
        )
        hillshade = 255 * (shaded + 1) / 2
        hillshade[np.isnan(array)] = np.nan
        return hillshade

    @staticmethod
    def _read_ascii_grid(grid_path):
        with open(grid_path, "r", encoding="utf-8") as grid_file:
            header = grid_file.readlines()[:6]

        header_values = [item.strip().split()[-1] for item in header]
        metadata = {
            "cols": int(header_values[0]),
            "rows": int(header_values[1]),
            "xll": float(header_values[2]),
            "yll": float(header_values[3]),
            "cellsize": float(header_values[4]),
            "nodata": float(header_values[5]),
        }

        array = np.loadtxt(grid_path, dtype=np.float64, skiprows=6)
        array[array == metadata["nodata"]] = np.nan
        return metadata, array

    @staticmethod
    def _coordinate_grids(metadata):
        x_coords = metadata["xll"] + (np.arange(metadata["cols"]) + 0.5) * metadata["cellsize"]
        y_coords = metadata["yll"] + (
            metadata["rows"] - np.arange(metadata["rows"]) - 0.5
        ) * metadata["cellsize"]
        return np.meshgrid(x_coords, y_coords)

    @staticmethod
    def _filled_dem(dem_array):
        if np.isnan(dem_array).all():
            return np.zeros_like(dem_array, dtype=np.float64)

        minimum = np.nanmin(dem_array)
        return np.where(np.isnan(dem_array), minimum, dem_array)

    @staticmethod
    def _normalize(values):
        if np.isnan(values).all():
            return np.zeros_like(values, dtype=np.float64)

        vmin = float(np.nanmin(values))
        vmax = float(np.nanmax(values))
        if vmin == vmax:
            vmax = vmin + 1e-9
        return np.nan_to_num((values - vmin) / (vmax - vmin), nan=0.0)

    @staticmethod
    def _contour_levels(surface, count=10):
        if np.isnan(surface).all():
            return None

        vmin = float(np.nanmin(surface))
        vmax = float(np.nanmax(surface))
        if vmin == vmax:
            return None

        levels = np.linspace(vmin, vmax, count)
        if np.unique(levels).size < 2:
            return None
        return levels

    @staticmethod
    def _as_rgba(rgb_array, alpha_mask):
        rgba = np.empty(rgb_array.shape[:2] + (4,), dtype=np.float64)
        rgba[..., :3] = rgb_array
        rgba[..., 3] = alpha_mask.astype(np.float64)
        return rgba

    def _build_scene(self, depo_path, dem_path):
        dem_meta, dem_array = self._read_ascii_grid(dem_path)
        _, depo_array = self._read_ascii_grid(depo_path)

        dep_visible = np.where(
            np.isnan(depo_array) | (depo_array < 0.005), np.nan, depo_array
        )

        x_grid, y_grid = self._coordinate_grids(dem_meta)
        terrain = self._filled_dem(dem_array)

        if np.isnan(terrain).all():
            terrain_display = np.zeros_like(terrain, dtype=np.float64)
        else:
            terrain_min = float(np.nanmin(terrain))
            terrain_display = terrain_min + (terrain - terrain_min) * self.z_exag

        z_surface = terrain_display + np.nan_to_num(dep_visible, nan=0.0) * self.deposition_z_scale

        rows, cols = dem_array.shape
        step = max(1, int(max(rows, cols) / self.max_grid_size))
        sample = (slice(None, None, step), slice(None, None, step))

        x_ds = x_grid[sample]
        y_ds = y_grid[sample]
        dem_ds = dem_array[sample]
        dep_ds = dep_visible[sample]
        terrain_display_ds = terrain_display[sample]
        z_ds = z_surface[sample]

        valid_dem = ~np.isnan(dem_ds)
        if np.any(valid_dem):
            shade_surface = np.where(valid_dem, terrain_display_ds, np.nanmin(terrain_display_ds[valid_dem]))
        else:
            shade_surface = np.zeros_like(terrain_display_ds, dtype=np.float64)

        terrain_rgb = self.terrain_cmap(self._normalize(terrain_display_ds))[..., :3]
        base_rgb = self.lightsource.shade_rgb(terrain_rgb, shade_surface, blend_mode="overlay")
        facecolors = self._as_rgba(base_rgb, valid_dem)

        dep_valid = ~np.isnan(dep_ds)
        dep_norm = None
        dep_min = None
        dep_max = None
        if np.any(dep_valid):
            dep_min = float(np.nanmin(dep_ds))
            dep_max = float(np.nanmax(dep_ds))
            if dep_min == dep_max:
                dep_max = dep_min + 1e-9

            dep_norm = colors.Normalize(vmin=dep_min, vmax=dep_max)
            dep_rgb = self.overlay_cmap(dep_norm(np.nan_to_num(dep_ds, nan=dep_min)))[..., :3]
            dep_shaded = self.lightsource.shade_rgb(dep_rgb, shade_surface, blend_mode="soft")
            blend = 0.85
            rgb_channels = facecolors[..., :3]
            rgb_channels[dep_valid] = (
                rgb_channels[dep_valid] * (1.0 - blend) + dep_shaded[dep_valid] * blend
            )
            facecolors[..., :3] = rgb_channels

        if np.isnan(z_ds).all():
            z_min = 0.0
            z_max = 1.0
        else:
            z_min = float(np.nanmin(z_ds))
            z_max = float(np.nanmax(z_ds))

        z_span = max(z_max - z_min, 1.0)
        base_offset = z_min - z_span * 0.12

        return {
            "dem_meta": dem_meta,
            "dem_array": dem_array,
            "dep_visible": dep_visible,
            "x_grid": x_grid,
            "y_grid": y_grid,
            "terrain_display": terrain_display,
            "z_surface": z_surface,
            "x_ds": x_ds,
            "y_ds": y_ds,
            "dem_ds": dem_ds,
            "dep_ds": dep_ds,
            "terrain_display_ds": terrain_display_ds,
            "z_ds": z_ds,
            "facecolors": facecolors,
            "dep_valid": dep_valid,
            "dep_norm": dep_norm,
            "dep_min": dep_min,
            "dep_max": dep_max,
            "base_offset": base_offset,
            "z_span": z_span,
            "contour_levels": self._contour_levels(terrain_display_ds),
        }

    def plot(self, depo_path, dem_path, eventname, outdir):
        """
        Plots the deposition result on the hillshaded DEM.
        """
        scene = self._build_scene(depo_path, dem_path)
        dem_meta = scene["dem_meta"]

        dem_extent = [
            dem_meta["xll"],
            dem_meta["xll"] + dem_meta["cols"] * dem_meta["cellsize"],
            dem_meta["yll"],
            dem_meta["yll"] + dem_meta["rows"] * dem_meta["cellsize"],
        ]

        terrain_fill = self._filled_dem(scene["dem_array"])
        shaded_background = self.lightsource.shade(
            terrain_fill,
            cmap=self.terrain_cmap,
            blend_mode="overlay",
        )

        fig, ax = plt.subplots(figsize=(4.9, 3.6))
        ax.set_title(f"Deposition - {eventname}")
        ax.imshow(shaded_background, extent=dem_extent, origin="upper")

        dep_plot = np.ma.masked_invalid(scene["dep_visible"])
        img_plot = ax.imshow(
            dep_plot,
            extent=dem_extent,
            origin="upper",
            cmap=self.overlay_cmap,
            alpha=0.88,
        )

        cbar = plt.colorbar(img_plot, orientation="vertical", aspect=14)
        cbar.set_label("Deposition heights [m]")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")

        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        output_plot_path = outdir / f"{eventname}_deposition.png"
        fig.savefig(output_plot_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

        print(f"Plot saved to {output_plot_path}")

    def _save_matplotlib_presets(self, fig, ax, eventname, outdir):
        presets = [
            ("deposition_3d", 40, 225),
            ("deposition_3d_context", 28, 315),
            ("deposition_3d_plan", 88, 270),
        ]

        saved_paths = []
        for suffix, elev, azim in presets:
            ax.view_init(elev=elev, azim=azim)
            output_path = outdir / f"{eventname}_{suffix}.png"
            fig.savefig(output_path, dpi=300, bbox_inches="tight")
            saved_paths.append(output_path)

        return saved_paths

    def plot_interactive_3d(self, depo_path, dem_path, eventname, outdir, show=True):
        """
        Creates a rotatable Matplotlib 3D view with hillshaded terrain, projected
        contours, vertical exaggeration, and fixed camera preset exports.
        """
        scene = self._build_scene(depo_path, dem_path)

        fig = plt.figure(figsize=(11, 8))
        ax = fig.add_subplot(111, projection="3d")
        ax.set_title(
            f"3D Deposition - {eventname} (terrain x{self.z_exag:.1f}, deposition x{self.deposition_z_scale:.2f})"
        )

        ax.plot_surface(
            scene["x_ds"],
            scene["y_ds"],
            scene["z_ds"],
            facecolors=scene["facecolors"],
            rstride=1,
            cstride=1,
            linewidth=0,
            antialiased=False,
            shade=False,
        )

        if scene["contour_levels"] is not None:
            ax.contour(
                scene["x_ds"],
                scene["y_ds"],
                scene["terrain_display_ds"],
                zdir="z",
                offset=scene["base_offset"],
                levels=scene["contour_levels"],
                colors="black",
                linewidths=0.35,
                alpha=0.32,
            )

        if scene["dep_norm"] is not None:
            mappable = ScalarMappable(norm=scene["dep_norm"], cmap=self.overlay_cmap)
            mappable.set_array([])
            colorbar = fig.colorbar(mappable, ax=ax, shrink=0.62, pad=0.08)
            colorbar.set_label("Deposition heights [m]")
        else:
            print("No deposition values exceeded the display threshold for the 3D overlay.")

        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Visual elevation [m]")
        ax.set_zlim(scene["base_offset"], np.nanmax(scene["z_ds"]) + scene["z_span"] * 0.05)

        try:
            ax.set_box_aspect((1, 1, 0.35))
        except Exception:
            pass

        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        plt.tight_layout()
        saved_paths = self._save_matplotlib_presets(fig, ax, eventname, outdir)
        print("Saved Matplotlib 3D views:", ", ".join(str(path) for path in saved_paths))

        ax.view_init(elev=40, azim=225)
        if show:
            plt.show()
        plt.close(fig)

    def export_plotly_3d(self, depo_path, dem_path, eventname, outdir, auto_open=False):
        """
        Saves an interactive Plotly HTML view when Plotly is installed.
        """
        try:
            import plotly.graph_objects as go
        except ImportError:
            print("Plotly is not installed. Skipping Plotly 3D export.")
            return

        scene = self._build_scene(depo_path, dem_path)
        fig = go.Figure()

        fig.add_surface(
            x=scene["x_ds"],
            y=scene["y_ds"],
            z=scene["terrain_display_ds"],
            surfacecolor=self._normalize(scene["terrain_display_ds"]),
            colorscale="Gray",
            showscale=False,
            hovertemplate="X=%{x:.2f}<br>Y=%{y:.2f}<br>Terrain=%{z:.2f}<extra></extra>",
            lighting={
                "ambient": 0.38,
                "diffuse": 0.88,
                "specular": 0.08,
                "roughness": 0.92,
            },
        )

        if scene["dep_norm"] is not None:
            dep_surface = np.where(scene["dep_valid"], scene["z_ds"], np.nan)
            fig.add_surface(
                x=scene["x_ds"],
                y=scene["y_ds"],
                z=dep_surface,
                surfacecolor=scene["dep_ds"],
                colorscale="OrRd",
                cmin=scene["dep_min"],
                cmax=scene["dep_max"],
                opacity=0.94,
                colorbar={"title": "Deposition heights [m]"},
                hovertemplate="X=%{x:.2f}<br>Y=%{y:.2f}<br>Deposition=%{surfacecolor:.3f} m<extra></extra>",
                lighting={
                    "ambient": 0.45,
                    "diffuse": 0.8,
                    "specular": 0.12,
                    "roughness": 0.85,
                },
            )

        fig.update_layout(
            title=f"3D Topography + Deposition - {eventname}",
            scene={
                "xaxis_title": "X",
                "yaxis_title": "Y",
                "zaxis_title": "Visual elevation [m]",
                "camera": {
                    "eye": {"x": -1.65, "y": -1.55, "z": 0.9},
                    "up": {"x": 0.0, "y": 0.0, "z": 1.0},
                },
            },
            margin={"l": 0, "r": 0, "b": 0, "t": 50},
        )

        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        output_html_path = outdir / f"{eventname}_deposition_3d_plotly.html"
        fig.write_html(str(output_html_path), include_plotlyjs=True, auto_open=auto_open)
        print(f"Plotly 3D view saved to {output_html_path}")

    def export_pyvista_3d(self, depo_path, dem_path, eventname, outdir, show=False):
        """
        Saves a PyVista screenshot and can optionally open a PyVista viewer when
        PyVista is installed.
        """
        try:
            import pyvista as pv
        except ImportError:
            print("PyVista is not installed. Skipping PyVista 3D export.")
            return

        scene = self._build_scene(depo_path, dem_path)
        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        output_image_path = outdir / f"{eventname}_deposition_3d_pyvista.png"

        grid = pv.StructuredGrid(scene["x_ds"], scene["y_ds"], scene["z_ds"])
        if scene["dep_norm"] is not None:
            scalars = scene["dep_ds"].ravel(order="F")
            scalar_kwargs = {
                "scalars": scalars,
                "cmap": "OrRd",
                "clim": [scene["dep_min"], scene["dep_max"]],
                "show_scalar_bar": True,
                "scalar_bar_args": {"title": "Deposition heights [m]"},
                "nan_color": "lightgrey",
                "nan_opacity": 1.0,
            }
        else:
            scalars = scene["terrain_display_ds"].ravel(order="F")
            scalar_kwargs = {
                "scalars": scalars,
                "cmap": "gist_earth",
                "show_scalar_bar": False,
            }

        plotter = pv.Plotter(off_screen=not show)
        plotter.add_mesh(
            grid,
            smooth_shading=True,
            ambient=0.25,
            diffuse=0.85,
            specular=0.12,
            **scalar_kwargs,
        )
        plotter.add_text(
            f"{eventname} | terrain x{self.z_exag:.1f} | deposition x{self.deposition_z_scale:.2f}",
            font_size=10,
        )
        plotter.view_isometric()

        if show:
            plotter.show(screenshot=str(output_image_path))
        else:
            plotter.show(auto_close=True, screenshot=str(output_image_path))

        print(f"PyVista 3D view saved to {output_image_path}")
