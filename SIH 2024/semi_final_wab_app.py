# -- coding: utf-8 --
import ee
import time
import webbrowser
import pyautogui
import pyperclip
import json
import folium
from folium import plugins
import os

# Initialize the Earth Engine library
def authenticate():
    try:
        ee.Initialize()
        print("Successfully authenticated.")
    except Exception as e:
        print("Authentication required. Please log in.")
        webbrowser.open("https://earthengine.google.com/")
        input("After logging in, press Enter to continue...")  # Wait for user to log in
        ee.Initialize()  # Try initializing again after login

# Create a map with drawing capabilities
def create_map(map_file):
    m = folium.Map(location=[20.0, 0.0], zoom_start=2)
    plugins.Draw(export=True).add_to(m)
    # m.save(map_file)
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

# Wait for the user to export the GeoJSON file
def wait_for_geojson(downloads_folder):
    geojson_file = os.path.join(downloads_folder, 'map_data.json')
    while not os.path.exists(geojson_file):
        print("Waiting for the user to export the GeoJSON file...")
        time.sleep(5)  # Adjust the waiting period
    return geojson_file

# Load and export all images in the collection
def load_and_export_images(start_date, end_date, prefix):
    collection = (ee.ImageCollection('COPERNICUS/S1_GRD')
                  .filterBounds(geometry)
                  .filterDate(start_date, end_date)
                  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                  .filter(ee.Filter.eq('instrumentMode', 'IW'))
                  .select('VV'))
    
    images = collection.toList(collection.size())
    num_images = images.size().getInfo()
    print(f"Number of images in collection from {start_date} to {end_date}: {num_images}")
    
    for i in range(num_images):
        image = ee.Image(images.get(i))
        description = f"{prefix}_image_{i}"
        task = ee.batch.Export.image.toDrive(
            image=image,
            description=description,
            scale=10,
            region=geometry,
            maxPixels=1e13
        )
        task.start()
        print(f"Export task started for image {i}. Check your Google Drive for the result.")
        while task.active():
            print('Waiting for task to complete...')
            time.sleep(10)
        print(f'Export task for image {i} completed.')

# Main workflow
def main():
    # Step 1: Create and open the map
    map_file = 'interactive_map.html'
    create_map(map_file)
    open_map(map_file)

    # Step 2: Wait for the user to export the GeoJSON file to Downloads folder
    downloads_folder = os.path.expanduser('~/Downloads')
    geojson_file = wait_for_geojson(downloads_folder)

    # Step 3: Extract coordinates from GeoJSON
    coords = extract_coordinates_from_geojson(geojson_file)
    
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
        return

    # Step 5: Authenticate the user with Earth Engine
    authenticate()

    # Step 6: Ask for user input for date ranges
    start_date1 = input("Enter start date for baseline period (YYYY-MM-DD): ")
    end_date1 = input("Enter end date for baseline period (YYYY-MM-DD): ")
    start_date2 = input("Enter start date for comparison period (YYYY-MM-DD): ")
    end_date2 = input("Enter end date for comparison period (YYYY-MM-DD): ")

    # Define the geometry based on the extracted coordinates
    global geometry
    geometry = ee.Geometry.Rectangle([min_longitude, min_latitude, max_longitude, max_latitude])
    coordinates = f"{(min_latitude + max_latitude) / 2},{(min_longitude + max_longitude) / 2}"  # Center for GMaps

    # Step 7: Load and export all images from each period
    print("Exporting images for the baseline period...")
    load_and_export_images(start_date1, end_date1, "baseline_period")
    
    print("Exporting images for the comparison period...")
    load_and_export_images(start_date2, end_date2, "comparison_period")

    # Step 8: Open Google Maps with the area of interest
    webbrowser.open(f"https://www.google.com/maps/@{coordinates},15z")

    # Step 9: Prepare the GEE script
    gee_script = f"""
    var geometry = ee.Geometry.Rectangle([{min_longitude}, {min_latitude}, {max_longitude}, {max_latitude}]);
    
    var collection1 = ee.ImageCollection('COPERNICUS/S1_GRD')
                        .filterBounds(geometry)
                        .filterDate('{start_date1}', '{end_date1}')
                        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                        .filter(ee.Filter.eq('instrumentMode', 'IW'))
                        .select('VV');
    
    var collection2 = ee.ImageCollection('COPERNICUS/S1_GRD')
                        .filterBounds(geometry)
                        .filterDate('{start_date2}', '{end_date2}')
                        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                        .filter(ee.Filter.eq('instrumentMode', 'IW'))
                        .select('VV');
    
    var change = collection2.mean().subtract(collection1.mean()).rename('Change');
    var significantChange = change.gt(0.1);
    Map.centerObject(geometry, 10);
    
    // Create a land mask
    var landMask = ee.Image('MODIS/006/MCD12Q1/2018_01_01')
                     .select('LC_Type1')
                     .eq(1)  // 1 corresponds to 'Water'
                     .not(); // Invert the mask to get land areas
    
    // Apply the land mask
    var maskedChange = change.updateMask(landMask);
    
    // Adjust the color palette for smooth transitions
    Map.addLayer(maskedChange, 
      {{min: -1, max: 1, palette: ['blue', 'white', 'yellow', 'red'], opacity: 0.6}}, 
      'Change Detection'
    );
    
    Map.addLayer(significantChange.updateMask(significantChange).updateMask(landMask), 
      {{palette: ['red'], opacity: 0.3}}, 
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

if __name__ == "__main__":
    main()









'''
# Hardcoded date ranges for quick processing
start_date1 = 2023-01-01
end_date1 = 2023-01-10
start_date2 = 2023-01-11
end_date2 = 2023-01-20
'''
