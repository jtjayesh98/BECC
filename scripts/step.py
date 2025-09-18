
import sys


'''
Establishing Global Parameters
------------------------------
state_name: Name of the state
start_year: Start year of the project
mid_pt: End point of monitoring period
end_year: End year of the project (Projection period)
'''

if len(sys.argv) > 2:
    state_name = sys.argv[2]
    start_year = int(sys.argv[3])
    mid_pt = int(sys.argv[4])
    end_year = int(sys.argv[5])
else:
    state_name = "Dhenkanal"
    start_year = 2010
    mid_pt = 2015
    end_year = 2020


years = list(range(start_year, end_year + 1))

print(f"State: {state_name}")
print(f"Years: {years}")
print(f"Mid Point: {mid_pt}")

import ee
ee.Authenticate()
ee.Initialize(project="cogent-range-308518")

import os
import pandas as pd
import geemap
import folium
from typing import List
import rasterio
import time

import ee
# from google.colab import drive
from typing import List
import os
import time
import folium
import geemap
import rasterio
from rasterio.warp import reproject, Resampling, calculate_default_transform
from rasterio.transform import Affine
from rasterio.windows import Window
from osgeo import gdal
from GEE_Manager import GEEManager
import numpy as np
from scipy.ndimage import distance_transform_edt
from FinalClass import RiskMaps


# Initialize the RiskMaps engine
engine = RiskMaps(f'C:\\Users\\Jayesh Tripathi\\Desktop\\BECC\\data\\GEE_exports_{state_name}', start_year, mid_pt, end_year, state_name)

if sys.argv[1] == "1":
    # Run the GEE operations
    engine.perform_gee_operations()
else:
    # Run the operations without GEE
    if os.path.exists(f'./data/GEE_exports_{state_name}'):
        engine.run_wo_gee()
        print("Please create the back-up by uploalding the data to the Drive")
    else:
        print("Run Step 1 first and download the appropriate from the drive to the correct location")

