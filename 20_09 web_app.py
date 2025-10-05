# -- coding: utf-8 --
import ee
import time
import webbrowser
import pyautogui  # Ensure this library is installed
import pyperclip  # Ensure this library is installed
import json
import folium
from folium import plugins
import os
import rasterio
import matplotlib.pyplot as plt
from typing import List, Tuple


# Function to create a map with drawing capabilities
def create_map(map_file):
    m = folium.Map(location=[20.0, 0.0], zoom_start=2)
    plugins.Draw(export=True).add_to(m)
    #m.save(map_file)
    print(f"Interactive map has been saved as {map_file}. Open this file in a web browser to interact with the map.")

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
    try:
        ee.Authenticate()
        ee.Initialize()
        print("Successfully authenticated.")
    except Exception as e:
        print("Authentication required. Please log in.")
        webbrowser.open("https://earthengine.google.com/")
        input("After logging in, press Enter to continue...")  # Wait for user to log in
        ee.Initialize()  # Try initializing again after login

# Wait for the user to export the GeoJSON file
def wait_for_geojson(downloads_folder):
    geojson_file = os.path.join(downloads_folder, 'map_data.json')
    while not os.path.exists(geojson_file):
        print("Waiting for the user to export the GeoJSON file...")
        time.sleep(5)  # Adjust the waiting period
    return geojson_file

# Main workflow
def main():
    # Step 1: Create and open the map
    map_file = 'interactive_map.html'
    create_map(map_file)
    open_map(map_file)

    # Step 2: Wait for the user to export the GeoJSON file to Downloads folder
    downloads_folder = os.path.expanduser('~/Downloads')
    geojson_file = wait_for_geojson(downloads_folder)

    # Function to extract coordinates and date periods from GeoJSON file
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

    # Step 3: Extract coordinates and date periods from GeoJSON
    coords, baseline_period, comparison_period = extract_data_from_geojson(geojson_file)

    # Step 4: Calculate min/max latitude and longitude
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
    baseline_start = baseline_period.get('start_date', 'Not Available')  # Default to 'Not Available' if the key is missing
    baseline_end = baseline_period.get('end_date', 'Not Available')
    comparison_start = comparison_period.get('start_date', 'Not Available')
    comparison_end = comparison_period.get('end_date', 'Not Available')

    # Print the dates
    print(f"Baseline Period: Start: {baseline_start}, End: {baseline_end}")
    print(f"Comparison Period: Start: {comparison_start}, End: {comparison_end}")
    
    # Define the geometry based on the extracted coordinates
    geometry = ee.Geometry.Rectangle([min_longitude, min_latitude, max_longitude, max_latitude])
    coordinates = f"{(min_latitude + max_latitude) / 2},{(min_longitude + max_longitude) / 2}"  # Center for GMaps

    # Step 7: Load image collections and calculate change using Earth Engine
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
        collection1 = check_image_bands(load_image_collection(baseline_start, baseline_end))
        collection2 = check_image_bands(load_image_collection(comparison_start, comparison_end))
        change = collection2.subtract(collection1).rename('Change')

        # Apply a threshold to identify significant changes
        threshold = 0.1  # Adjust threshold
        significantChange = change.gt(threshold)
    except ValueError as e:
        print(f"Error in image processing: {e}")
        return

    # Step 8: Export the image to Google Drive
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

    # Step 9: Open Google Maps with the area of interest
    webbrowser.open(f"https://www.google.com/maps/@{coordinates},15z")

    # Step 10: Prepare the GEE script
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
      {{min: -2, max: 2, palette: ['blue', 'white', 'red'], opacity: 0.3}},  // Reduced opacity to 0.4
      'Change Detection'
    );
    
    // Add the "Significant Change" layer with reduced opacity
    Map.addLayer(significantChange.updateMask(significantChange), 
      {{palette: ['red'], opacity: 0.2}},  // Reduced opacity to 0.6
      'Significant Change'
    );
    """

    # Copy the script to clipboard and open GEE Code Editor
    pyperclip.copy(gee_script)
    webbrowser.open("https://code.earthengine.google.com/")
    time.sleep(15)
    pyautogui.hotkey('ctrl', 'v')
    print("JavaScript code pasted into the Google Earth Engine Code Editor.")
    pyautogui.hotkey('ctrl', 'enter')
    print("Code executed in GEE Code Editor.")

    # Step 11: Visualize the exported TIFF file
    tiff_file = os.path.join(downloads_folder, 'Sentinel1_SAR_VV_Image.tif')

    # Wait for the TIFF file to be downloaded
    while not os.path.exists(tiff_file):
        print("Waiting for the Sentinel1_SAR_VV_Image.tif file to download...")
        time.sleep(5)  # Adjust the waiting period if necessary

    # Open the TIFF file using rasterio
    try:
        with rasterio.open(tiff_file) as src:
            print(f"Number of bands: {src.count}")
            print(f"Image width: {src.width}")
            print(f"Image height: {src.height}")
            
            # Read the first band
            band1 = src.read(1)
            
            # Plot the band using matplotlib
            plt.figure(figsize=(10, 10))
            plt.title("SAR Image Band 1")
            plt.imshow(band1, cmap="gray")
            plt.colorbar(label="Backscatter values")
            plt.show()
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
