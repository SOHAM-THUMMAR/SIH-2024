// Hardcoded coordinates for quick processing
var min_longitude = 30.5;
var min_latitude = 49.5;
var max_longitude = 30.6;
var max_latitude = 49.6;

// Define the original area of interest (AOI)
var geometry = ee.Geometry.Rectangle([min_longitude, min_latitude, max_longitude, max_latitude]);

// Define time periods for analysis
var start_date1 = '2023-01-01';
var end_date1 = '2023-01-10';
var start_date2 = '2023-01-11';
var end_date2 = '2023-01-20';

// Function to classify water based on a threshold
var classifyWater = function(image) {
  var vv = image.select('VV');
  var waterMask = vv.lt(-16).rename('water'); // Adjust threshold as needed
  return image.updateMask(waterMask.not()); // Mask out water areas
};

// Load and process the first image collection
var collection1 = ee.ImageCollection('COPERNICUS/S1_GRD')
    .filterBounds(geometry)
    .filterDate(start_date1, end_date1)
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
    .filter(ee.Filter.eq('instrumentMode', 'IW'))
    .select('VV')
    .median()
    .clip(geometry);

// Apply water classification to the first image
var classifiedImage1 = classifyWater(collection1);

// Load and process the second image collection
var collection2 = ee.ImageCollection('COPERNICUS/S1_GRD')
    .filterBounds(geometry)
    .filterDate(start_date2, end_date2)
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
    .filter(ee.Filter.eq('instrumentMode', 'IW'))
    .select('VV')
    .median()
    .clip(geometry);

// Apply water classification to the second image
var classifiedImage2 = classifyWater(collection2);

// Calculate the change between the two classified images
var change = classifiedImage2.subtract(classifiedImage1).rename('Change');

// Threshold to identify significant changes (adjust as needed)
var significantChange = change.gt(0.1);

// Center the map on the geometry
Map.centerObject(geometry, 10);

// Add the "Change Detection" layer with a color palette
Map.addLayer(change, {min: -2, max: 2, palette: ['yellow', 'black', 'red'], opacity: 0.3}, 'Change Detection');

// Add the "Significant Change" layer with a color palette
Map.addLayer(significantChange.updateMask(significantChange), {palette: ['red'], opacity: 0.6}, 'Significant Change');
