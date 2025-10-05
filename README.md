# SIH-2024

# 🌍 Automatic SAR Change Detection using Google Earth Engine  

### 🚀 Smart India Hackathon 2024 Project  

This project automates **Synthetic Aperture Radar (SAR)**–based change detection using **Google Earth Engine (GEE)** and **Sentinel-1** imagery.  
It allows users to draw an **area of interest (AOI)** on an interactive map, automatically extract coordinates and date ranges, and detect significant surface changes between two time periods — such as **deforestation, floods, or construction activity**.  

---

## 🧩 Features  

✅ **Interactive AOI Selection**  
- Users select an area on a local HTML map and export it as a GeoJSON file.  

✅ **Automated Workflow**  
- The script handles everything: authentication, coordinate extraction, Earth Engine processing, and result export.  

✅ **Change Detection Using Sentinel-1 SAR Data**  
- Uses VV polarization from **COPERNICUS/S1_GRD** collection.  
- Performs pixel-wise differencing between baseline and comparison periods.  
- Highlights **significant changes** based on a configurable threshold.  

✅ **Full Integration with GEE**  
- Automatically generates and pastes the Earth Engine JavaScript code into the **GEE Code Editor**.  
- Starts a **Drive export task** and opens the AOI in Google Maps for visualization.  

---

## 🧠 Workflow Overview  

```mermaid
flowchart TD
    A[Start Script] --> B[Authenticate with GEE]
    B --> C[Open interactive_map.html]
    C --> D[User Exports GeoJSON]
    D --> E[Extract Coordinates + Dates]
    E --> F[Compute Change using Sentinel-1]
    F --> G[Export to Drive]
    G --> H[Open Google Maps + GEE Editor]
