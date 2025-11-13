import os
import subprocess
from pathlib import Path

# Define the base directory containing scenario folders
base_dir = Path("Scenarios")
output_base_dir = Path("Outputs")

# Ensure the output directory exists
output_base_dir.mkdir(parents=True, exist_ok=True)

# Gather all scenario folders and extract their numeric suffixes
scenario_map = {}
for scenario_dir in base_dir.iterdir():
    if scenario_dir.is_dir():
        # Extract the numeric suffix from the folder name
        folder_name = scenario_dir.name
        try:
            # Assume the numeric suffix is the last part of the folder name after an underscore
            numeric_suffix = int(folder_name.split("_")[-1])
            scenario_map[numeric_suffix] = scenario_dir
        except ValueError:
            print(f"Skipping folder '{folder_name}' as it does not have a numeric suffix.")

# Function to process a single scenario
def process_scenario(scenario_dir):
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

# Main loop for user interaction
while True:
    # Display available scenarios to the user
    print("\nAvailable scenarios:")
    for number in sorted(scenario_map.keys()):
        print(f"{number}: {scenario_map[number].name}")

    # Get user input to select all scenarios or a specific one
    print("\nDo you want to process all scenarios or a specific one?")
    print("Enter 'all' to process all scenarios, the number of a specific scenario, or 'finish' to exit:")
    user_choice = input("Your choice: ").strip()

    if user_choice.lower() == "finish":
        print("Exiting. Goodbye!")
        break
    elif user_choice.lower() == "all":
        # Process all scenarios
        for scenario_dir in scenario_map.values():
            process_scenario(scenario_dir)
    elif user_choice.isdigit() and int(user_choice) in scenario_map:
        # Process the specific scenario based on the numeric suffix
        scenario_dir = scenario_map[int(user_choice)]
        process_scenario(scenario_dir)
    else:
        print(f"Invalid choice: '{user_choice}'. Please try again.")