# -- coding: utf-8 --
"""
Created on Thu Sep 19 22:01:53 2024

@author: YASH
"""

import ee
import time
import webbrowser
import pyautogui  # Ensure this library is installed
import pyperclip  # Ensure this library is installed
import json
import os
from typing import List, Tuple

# Open the HTML map file
def open_map(map_file):
    webbrowser.open(f"file://{os.path.abspath(map_file)}")

# Authenticate the user with Google Earth Engine
def authenticate():
    ee.Authenticate()
    ee.Initialize(project='ee-sthummar444')

# Wait for the user to export the GeoJSON file
def wait_for_geojson(downloads_folder):
    geojson_file = os.path.join(downloads_folder, 'map_data.json')
    while not os.path.exists(geojson_file):
        print("Waiting for the user to export the GeoJSON file...")
        time.sleep(5)  # Adjust the waiting period
    return geojson_file

# Extract coordinates and date periods from GeoJSON file
def extract_data_from_geojson(geojson_file: str) -> Tuple[List[Tuple[float, float]], dict, dict]:
    with open(geojson_file, 'r') as f:
        data = json.load(f)

    # Extract date periods
    baseline_period = data.get("baseline_period", {})
    comparison_period = data.get("comparison_period", {})

    # Extract coordinates
    features = data.get('features', [])
    coords = []
    
    for feature in features:
        geometry = feature.get('geometry', {})
        if geometry.get('type') == 'Polygon':
            coords.extend(geometry['coordinates'][0])

    return coords, baseline_period, comparison_period

# Load image collections and calculate change using Earth Engine
def load_image_collection(start_date, end_date, geometry):
    collection = (ee.ImageCollection('COPERNICUS/S1_GRD')
                  .filterBounds(geometry)
                  .filterDate(start_date, end_date)
                  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                  .filter(ee.Filter.eq('instrumentMode', 'IW'))
                  .select('VV'))
    size = collection.size().getInfo()
    print(f"Number of images in collection from {start_date} to {end_date}: {size}")
    if size == 0:
        return None  # No images found, return None
    return collection.median()

def main():
    # Authenticate with Earth Engine
    authenticate()

    # Open the existing map file
    map_file = 'interactive_map.html'  # Adjust the path if necessary
    open_map(map_file)

    # Wait for the user to export the GeoJSON file to Downloads folder
    downloads_folder = os.path.expanduser('~/Downloads')
    geojson_file = wait_for_geojson(downloads_folder)

    # Extract coordinates and date periods from GeoJSON
    coords, baseline_period, comparison_period = extract_data_from_geojson(geojson_file)

    # Calculate min/max latitude and longitude
    if coords:
        latitudes = [coord[1] for coord in coords]
        longitudes = [coord[0] for coord in coords]
        
        min_latitude = min(latitudes)
        max_latitude = max(latitudes)
        min_longitude = min(longitudes)
        max_longitude = max(longitudes)
        
        # Print the coordinates
        print(f"Min Longitude: {min_longitude}")
        print(f"Min Latitude: {min_latitude}")
        print(f"Max Longitude: {max_longitude}")
        print(f"Max Latitude: {max_latitude}")
    else:
        print("No coordinates found in the GeoJSON file.")
        return

    # Prepare the geometry
    geometry = ee.Geometry.Rectangle([min_longitude, min_latitude, max_longitude, max_latitude])

    # Load image collections for baseline and comparison periods
    baseline_start = baseline_period.get('start_date', 'Not Available')
    baseline_end = baseline_period.get('end_date', 'Not Available')
    comparison_start = comparison_period.get('start_date', 'Not Available')
    comparison_end = comparison_period.get('end_date', 'Not Available')

    try:
        collection1 = load_image_collection(baseline_start, baseline_end, geometry)
        collection2 = load_image_collection(comparison_start, comparison_end, geometry)
        
        if collection1 is None or collection2 is None:
            print("No valid image collections found for the specified dates.")
            return

        change = collection2.subtract(collection1).rename('Change')
        significantChange = change.gt(0.1)  # Adjust threshold

        # Export the image to Google Drive
        task = ee.batch.Export.image.toDrive(
            image=change,
            description='area_of_interest',
            scale=10,
            region=geometry,
            maxPixels=1e13
        )
        task.start()
        print("Export task started. Check your Google Drive for the result.")
        while task.active():
            print('Waiting for task to complete...')
            time.sleep(10)
        print('Export task completed.')

        # Open Google Maps with the area of interest
        coordinates = f"{(min_latitude + max_latitude) / 2},{(min_longitude + max_longitude) / 2}"
        webbrowser.open(f"https://www.google.com/maps/@{coordinates},15z")

        # Prepare the GEE script
        gee_script = f"""
        var min_longitude = {min_longitude};
        var min_latitude = {min_latitude};
        var max_longitude = {max_longitude};
        var max_latitude = {max_latitude};
        
        var geometry = ee.Geometry.Rectangle([min_longitude, min_latitude, max_longitude, max_latitude]);
        
        Map.centerObject(geometry, 10);
        Map.addLayer(geometry, {{color: 'blue'}}, 'Area of Interest');        
        """

        # Copy the script to clipboard and open GEE Code Editor
        pyperclip.copy(gee_script)
        webbrowser.open("https://code.earthengine.google.com/")
        time.sleep(15)
        pyautogui.hotkey('ctrl', 'v')
        print("JavaScript code pasted into the Google Earth Engine Code Editor.")
        time.sleep(5)
        pyautogui.hotkey('ctrl', 'enter')
        print("Code executed in GEE Code Editor.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
