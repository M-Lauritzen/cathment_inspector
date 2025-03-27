#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Catchment Inspection Tool

Created on: 2025-03-25

Authors: Mikkel Lauritzen
"""

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
from matplotlib.colors import Normalize
from streamline import streamline
import os
import configparser
import matplotlib

# Change the working directory to the location of this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

config = configparser.ConfigParser()
# Create user config file if it does not exist
if not os.path.exists('settings.ini'):
    with open('settings.ini', 'w') as configfile:
        config['Paths'] = {
            'shapefile': '',
            'velocity_data': ''
        }
        config.write(configfile)

# Read settings and paths from settings file
config.read('settings.default.ini')
config.read('settings.ini')

# Check if the shapefile path is set in the configuration
if 'shapefile' not in config['Paths'] or not config['Paths']['shapefile']:
    raise ValueError("The path to the shapefile is not set in the configuration file. Please set 'shapefile' under the 'Paths' section in settings.ini.")
if 'velocity_data' not in config['Paths'] or not config['Paths']['velocity_data']:
    raise ValueError("The path to the velocity data is not set in the configuration file. Please set 'velocity_data' under the 'Paths' section in settings.ini.")

# Load the shapefile and velocity dataset
basins = gpd.read_file(config['Paths']['shapefile'])
velocity_data = xr.open_dataset(config['Paths']['velocity_data']).squeeze()

# Flip y-axis if its in the wrong direction
if velocity_data.y[0] > velocity_data.y[1]:
    velocity_data = velocity_data.reindex(y=velocity_data.y[::-1])

# Extract velocity components and calculate magnitude
u = velocity_data['land_ice_surface_easting_velocity']
v = velocity_data['land_ice_surface_northing_velocity']
speed = velocity_data['land_ice_surface_velocity_magnitude']

def inspect_basin(n,starting_point=(np.nan,np.nan),speed_threshold=float(config['Processing']['speed_threshold'])):
    global new_point
    new_point = starting_point
    # Access the n'th entry of the GeoDataFrame
    entry = basins.iloc[n]
    polygon = entry.geometry
    name = entry.NAME.replace('_', ' ').title()

    # Subset the velocity data to the extent of the polygon
    minx, miny, maxx, maxy = polygon.bounds
    u_subset = u.sel(x=slice(minx, maxx), y=slice(miny, maxy))
    v_subset = v.sel(x=slice(minx, maxx), y=slice(miny, maxy))
    speed_subset = speed.sel(x=slice(minx, maxx), y=slice(miny, maxy))
    # Subset the x and y coordinates to the extent of the polygon
    x_subset = velocity_data['x'].sel(x=slice(minx, maxx))
    y_subset = velocity_data['y'].sel(y=slice(miny, maxy))

    # Create a mask for points inside the polygon
    xv, yv = np.meshgrid(x_subset.data, y_subset.data)
    points = np.vstack((xv.ravel(), yv.ravel())).T
    mask_polygon = np.array([polygon.contains(gpd.points_from_xy([p[0]], [p[1]])[0]) for p in points]).reshape(xv.shape)
    # Create a mask where speeds are over the threshold
    mask_speed = speed_subset>speed_threshold
    # Combine the masks
    mask = mask_polygon & mask_speed

    # Check if there are speeds over threshold
    if not np.any(mask):
        print('No speeds over {} m pr day for {}'.format(speed_threshold, name))
        return (np.nan,np.nan)
    
    # Create subsets of the data from the bounds of the mask
    i_bounds = np.where(np.any(mask, axis=1))[0][[0,-1]]
    j_bounds = np.where(np.any(mask, axis=0))[0][[0,-1]]
    # Determine the extent of the masked region
    extent = [x_subset[j_bounds[0]].item(), x_subset[j_bounds[1]].item(),
              y_subset[i_bounds[0]].item(), y_subset[i_bounds[1]].item()]

    #Use subsets of the data only where the mask is true
    u_subset = u_subset[i_bounds[0]:i_bounds[1], j_bounds[0]:j_bounds[1]]
    v_subset = v_subset[i_bounds[0]:i_bounds[1], j_bounds[0]:j_bounds[1]]
    speed_subset = speed_subset[i_bounds[0]:i_bounds[1], j_bounds[0]:j_bounds[1]]
    xv = xv[i_bounds[0]:i_bounds[1], j_bounds[0]:j_bounds[1]]
    yv = yv[i_bounds[0]:i_bounds[1], j_bounds[0]:j_bounds[1]]
    mask = mask[i_bounds[0]:i_bounds[1], j_bounds[0]:j_bounds[1]]
    x_subset = x_subset[j_bounds[0]:j_bounds[1]]
    y_subset = y_subset[i_bounds[0]:i_bounds[1]]


    # Apply the mask to the speed
    speed_masked = np.where(mask, speed_subset.data, np.nan)

    # Create figure
    fig, ax = plt.subplots(1,1,figsize=(10,10))
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    mvel = ax.pcolormesh(xv, yv, speed_masked, shading='auto', cmap='viridis', norm=Normalize(vmin=0, vmax=np.nanmax(speed_masked)))

    # Create a grid for streamlines
    X, Y = np.meshgrid(x_subset, y_subset)

    # Mask the velocity components for streamlines
    u_stream = np.where(mask, u_subset, np.nan)
    v_stream = np.where(mask, v_subset, np.nan)

    # Plot the old starting point
    # If there is no saved starting_point set it to the centroid of the polygon
    if np.isnan(new_point[0]):
        new_point = [polygon.centroid.x, polygon.centroid.y]
    ax.plot(new_point[0], new_point[1], 'ro', label='Old starting point')
    user_point = ax.plot([], [], 'yo', label='New starting point')

    # calculate streamline from old starting point
    sl = streamline(X, Y, u_stream, v_stream,[new_point[0], new_point[1]],t_max=1000000)
    ax.plot(sl[:,0],sl[:,1],'r')

    # set new streamline to be empty
    usl = ax.plot([],[],'y')

    ax.axis('off')  # Turn off the axes
    plt.colorbar(mvel, ax=ax, label='Velocity magnitude (m/day)')
    # Add title and legend
    ax.set_title(name)
    plt.legend(loc='lower right')
    # Function to handle mouse clicks
    def on_click(event):
        if event.inaxes:
            global new_point
            # Get the clicked point
            new_point = (event.xdata, event.ydata)
            # Add a streamline from the new point
            sl = streamline(X, Y, u_stream, v_stream,[new_point[0], new_point[1]])
            usl[0].set_data(sl[:,0],sl[:,1])
            # Plot the new point
            user_point[0].set_data([new_point[0]], [new_point[1]])
            plt.draw()  # Redraw the plot

    # Connect the click event to the handler
    cid = fig.canvas.mpl_connect('button_press_event', on_click)
    # Function to handle keypress events
    def on_key(event):
        if event.key == 'enter':  # Close the figure if 'Enter' is pressed
            plt.close('all')
        elif event.key == 'escape':  # Exit the program if 'Escape' is pressed
            plt.close('all')
            print('Exiting')
            exit()

    # Connect the keypress event to the handler
    kid = fig.canvas.mpl_connect('key_press_event', on_key)
    # # Show the plot
    plt.show()
    return new_point

if __name__ == "__main__":
    # Check the current backend
    current_backend = matplotlib.get_backend()
    print(f"Current Matplotlib backend: {current_backend}")

    # Ensure the backend supports interactivity
    if current_backend not in ['Qt5Agg', 'TkAgg', 'MacOSX']:
        print("Switching to an interactive backend...")
        matplotlib.use('TkAgg')  # Switch to a commonly used interactive backend
    save_file = config['Paths']['save_file']
    if os.path.exists(save_file):
        points = np.genfromtxt(save_file, delimiter=',', skip_header=1)
    else:
        points = np.full((len(basins),2), np.nan)
    for i in range(len(basins)):
        points[i,:] = inspect_basin(i,points[i,:])
        np.savetxt(save_file, points, delimiter=',', header='x,y', comments='')