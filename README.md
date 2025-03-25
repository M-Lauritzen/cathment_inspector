## Overview
This Python script allows users to inspect and visualize ice flow velocity data within specified drainage basins in Greenland. It loads velocity data from a NetCDF file and overlays it with basin boundaries from a shapefile. Users can interactively select starting points and compute streamlines to analyze ice flow patterns.

## Features
- Loads and visualizes ice velocity data.
- Overlays drainage basins from a shapefile.
- Allows interactive selection of starting points.
- Computes and plots streamlines to analyze ice flow direction.
- Saves selected starting points to a CSV file.

## Dependencies
Ensure you have the following Python packages installed:

- `xarray`
- `matplotlib`
- `numpy`
- `geopandas`
- `scipy`

## Data Requirements
### Input Files
- **Shapefile**: Contains Greenland basin boundaries.
- **Velocity Data (NetCDF)**: Contains ice velocity information.
- Paths must be set in config

Ensure these files exist and update the paths in the script if necessary.

### Output File
- `starting_points.csv`: Stores the selected starting points for each basin.

## Usage
Run the script using:
```sh
python script.py
```
For each basin:
- The script will display a velocity map.
- Click to select a new starting point for streamlines.
- Press `Enter` to move to the next basin.
- Press `Escape` to exit.

## Customization
- Modify the `speed_threshold` parameter to filter low-velocity areas.

## Author
Mikkel Lauritzen

## License
This project is licensed under the MIT License.

