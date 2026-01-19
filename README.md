# SIH-2024

Automatic SAR Change Detection using Google Earth Engine

This repository contains the code and resources for the Smart India Hackathon 2024 project titled *Automatic SAR Change Detection using Google Earth Engine*. The project automates change detection from Synthetic Aperture Radar (SAR) satellite data, allowing users to draw areas of interest on an interactive map and detect significant surface changes between two time periods using Sentinel-1 imagery.

---

## Overview

This project was developed as part of the Smart India Hackathon 2024, a nationwide initiative that brings student teams together to solve real-world challenges with innovative technology solutions. SIH is organized with support from government and industry partners and encourages practical problem solving at scale. :contentReference[oaicite:0]{index=0}

---

## Features

- Interactive selection of an Area of Interest (AOI) via a map  
- Automates data extraction and preprocessing from Google Earth Engine (GEE)  
- Uses Sentinel-1 SAR imagery for detecting surface change  
- Pixel-wise comparison between baseline and comparison periods  
- Automatically generates GEE JavaScript code for full analysis  
- Opens visualization in both Google Earth Engine Editor and Google Maps  

---

## Project Structure

```
/
├── interactive_map.html        # Map interface to draw AOI and export GeoJSON
├── webapp.py                   # Flask app (or similar) for hosting tools
├── semi_final_wab_app.py       # Intermediate version of web app
├── updated_script.py           # Updated automation script
├── 20_09 web_app.py            # Web application script for change detection
├── best_baby_javascript.js     # JavaScript used in interactive map
├── README.md                  # This file
```

The primary code files handle:
- Interactive AOI drawing and GeoJSON generation  
- Earth Engine authentication and data processing  
- Automated SAR change detection workflow  

---

## How It Works

1. User opens the interactive map (`interactive_map.html`) in a browser.  
2. The user draws an Area of Interest (AOI).  
3. The drawn AOI is exported as a GeoJSON file.  
4. The script extracts coordinates and date ranges from this file.  
5. Google Earth Engine processes the SAR data for specified dates.  
6. A change detection map is produced using pixel-wise differencing of SAR bands.  
7. Results can be exported and visualized.  

This workflow enables rapid and repeatable analysis of land surface changes such as deforestation, flooding, or construction activity.  

---

## Getting Started

### Prerequisites

- Python 3.x installed  
- Google Earth Engine account and authentication  
- Web browser for interactive_map.html  
- Required Python libraries (install via pip)  

Example installation:
```bash
pip install earthengine-api flask
```

### Usage

1. Authenticate with Google Earth Engine:
```bash
earthengine authenticate
```

2. Run the web app:
```bash
python webapp.py
```

3. Open `interactive_map.html` in your browser.

4. Draw your area of interest, export GeoJSON, and follow prompts for change detection.

---

## Contributions

This repository was developed for the Smart India Hackathon 2024. Contributions can include improvements to automation scripts, UI enhancements for the interactive map, better documentation, or adding support for additional satellite data sources.

To contribute:
```bash
# Fork the repository
# Create a new branch
git checkout -b feature-name

# Make your changes and commit
git commit -m "Add feature"

# Push and open a Pull Request
```

---

## About SIH

Smart India Hackathon (SIH) is India’s largest nationwide initiative to engage young innovators in practical problem solving across software and hardware domains. The 2024 edition featured a range of challenges requiring modern technology solutions.

---

## Acknowledgements

This project was built as a part of participation in the Smart India Hackathon 2024, which brings together students from across the nation to tackle real world problems through innovation and collaboration.
