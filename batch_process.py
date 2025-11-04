import os
import subprocess
from pathlib import Path

# Define the base directory containing scenario folders
base_dir = Path("Scenarios")
output_base_dir = Path("Outputs")

# Ensure the output directory exists
output_base_dir.mkdir(parents=True, exist_ok=True)

# Iterate through each scenario folder
for scenario_dir in base_dir.iterdir():
    if scenario_dir.is_dir():
        input_file = scenario_dir / "input.json"
        dem_file = scenario_dir / "topofan.asc"
        output_dir = output_base_dir / scenario_dir.name

        # Check if both input.json and topofan.asc exist
        if input_file.exists() and dem_file.exists():
            print(f"Processing scenario: {scenario_dir.name}")
            try:
                # Call the simulation script with the file paths
                subprocess.run(
                    [
                        "python",
                        "TopRunDF.py",  # Replace with the name of your simulation script
                        "--input", str(input_file),
                        "--dem", str(dem_file),
                        "--output", str(output_dir)
                    ],
                    check=True
                )
            except subprocess.CalledProcessError as e:
                print(f"Error running simulation for {scenario_dir.name}: {e}")
        else:
            print(f"Missing files in {scenario_dir.name}. Skipping...")