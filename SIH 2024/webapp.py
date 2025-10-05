# -- coding: utf-8 --
import ee
import time
import webbrowser
import pyautogui
import pyperclip
import json
import os
from typing import List, Tuple

# Open the HTML map file
def open_map(map_file):
    webbrowser.open(f"file://{os.path.abspath(map_file)}")

# Extract coordinates from GeoJSON file
def extract_coordinates_from_geojson(geojson_file):
    with open(geojson_file, 'r') as file:
        data = json.load(file)
        coordinates = []
        for feature in data['features']:
            geometry = feature['geometry']
            if geometry['type'] == 'Polygon':
                coords = geometry['coordinates'][0]
                for coord in coords:
                    coordinates.append(coord)
        return coordinates

# Authenticate the user with Google Earth Engine
def authenticate():
    ee.Authenticate()  # Ensure user completes this step in the browser
    ee.Initialize(project='ee-sthummar444')

# Wait for the user to export the GeoJSON file
def wait_for_geojson(downloads_folder):
    geojson_file = os.path.join(downloads_folder, "map_data.json")
    
    # Check if the file already exists and delete it
    if os.path.exists(geojson_file):
        print(f"{geojson_file} already exists. Overwriting the file...")
        os.remove(geojson_file)  # Remove the existing file

    # Wait for the new GeoJSON file to be created
    while not os.path.exists(geojson_file):
        print("Waiting for the user to export the GeoJSON file...")
        time.sleep(5)

    return geojson_file  # Fixed indentation issue here

# Extract coordinates and date periods from GeoJSON file
def extract_data_from_geojson(geojson_file: str) -> Tuple[List[Tuple[float, float]], dict, dict]:
    """Extract coordinates and dates from a GeoJSON file."""
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

# Main workflow
def main():
    authenticate()  # Ensure authentication before proceeding

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

    # Final output containing the periods and coordinates
    final_data = {
        "baseline_period": {
            "start_date": baseline_period.get("start_date", "Not Available"),
            "end_date": baseline_period.get("end_date", "Not Available")
        },
        "comparison_period": {
            "start_date": comparison_period.get("start_date", "Not Available"),
            "end_date": comparison_period.get("end_date", "Not Available")
        },
        "coordinates": {
            "min_latitude": min_latitude,
            "max_latitude": max_latitude,
            "min_longitude": min_longitude,
            "max_longitude": max_longitude
        }
    }

    # Print the date ranges from the GeoJSON file
    baseline_start = baseline_period.get('start_date', 'Not Available')
    baseline_end = baseline_period.get('end_date', 'Not Available')
    comparison_start = comparison_period.get('start_date', 'Not Available')
    comparison_end = comparison_period.get('end_date', 'Not Available')

    # Define the geometry based on the extracted coordinates
    geometry = ee.Geometry.Rectangle([min_longitude, min_latitude, max_longitude, max_latitude])
    coordinates = f"{(min_latitude + max_latitude) / 2},{(min_longitude + max_longitude) / 2}"  # Center for GMaps

    # Load image collections and calculate change using Earth Engine
    def load_image_collection(start_date, end_date):
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

    def check_image_bands(image):
        if image is None:
            raise ValueError("No images found in the collection.")
        bands = image.bandNames().getInfo()
        if not bands:
            raise ValueError("Image does not have any bands.")
        return image

    try:
        # Use the dates from GeoJSON
        collection1 = check_image_bands(load_image_collection(baseline_start, baseline_end))
        collection2 = check_image_bands(load_image_collection(comparison_start, comparison_end))
        change = collection2.subtract(collection1).rename('Change')

        # Apply a threshold to identify significant changes
        threshold = 0.1  # Adjust threshold
        significantChange = change.gt(threshold)
    except ValueError as e:
        print(f"Error in image processing: {e}")
        return

    # Export the image to Google Drive
    try:
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
    except Exception as e:
        print(f"An error occurred during export: {e}")

    # Open Google Maps with the area of interest
    webbrowser.open(f"https://www.google.com/maps/@{coordinates},15z")

    # Prepare the GEE script
    gee_script = f"""
    var geometry = ee.Geometry.Rectangle([{min_longitude}, {min_latitude}, {max_longitude}, {max_latitude}]);
    
    var collection1 = ee.ImageCollection('COPERNICUS/S1_GRD')
                        .filterBounds(geometry)
                        .filterDate('{baseline_start}', '{baseline_end}')
                        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                        .filter(ee.Filter.eq('instrumentMode', 'IW'))
                        .select('VV')
                        .median();
    
    var collection2 = ee.ImageCollection('COPERNICUS/S1_GRD')
                        .filterBounds(geometry)
                        .filterDate('{comparison_start}', '{comparison_end}')
                        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                        .filter(ee.Filter.eq('instrumentMode', 'IW'))
                        .select('VV')
                        .median();
    
    var change = collection2.subtract(collection1).rename('Change');
    var significantChange = change.gt(0.1);
    Map.centerObject(geometry, 10);
    
    // Add the "Change Detection" layer with reduced opacity
    Map.addLayer(change, 
      {{min: -2, max: 2, palette: ['yellow', 'black', 'red'], opacity: 0.3}},  // Reduced opacity to 0.3
      'Change Detection'
    );
    
    // Add the "Significant Change" layer with reduced opacity
    Map.addLayer(significantChange.updateMask(significantChange), 
      {{palette: ['red'], opacity: 0.2}},  // Reduced opacity to 0.2
      'Significant Change'
    );
    """

    # Copy the script to clipboard and open GEE Code Editor
    pyperclip.copy(gee_script)
    webbrowser.open("https://code.earthengine.google.com/")
    time.sleep(15)
    pyautogui.hotkey('ctrl', 'v')
    print("JavaScript code pasted into the Google Earth Engine Code Editor.")
    time.sleep(5)
    pyautogui.hotkey('ctrl', 'enter')
    time.sleep(10)
    pyautogui.click(x=1000,y=500)
    pyautogui.hotkey('1')
    print("Code executed in GEE Code Editor.")

if __name__ == "__main__":
    main()



