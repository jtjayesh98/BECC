import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import box
import numpy as np 

import pandas as pd
# Paths

import sys
import os


'''
Establishing Global Parameters
------------------------------
state_name: Name of the state
district_name: Name of the district
site_name: Name of the site
start_year: Start year of the project
mid_pt: End point of monitoring period
end_year: End year of the project (Projection period)
'''

if len(sys.argv) > 1:
    state_name = sys.argv[1]
    district_name = sys.argv[2]
    site_name = sys.argv[3]
    start_year = int(sys.argv[4])
    mid_pt = int(sys.argv[5])
    end_year = int(sys.argv[6])
else:
    state_name = 'Odisha'
    district_name = 'Dhenkanal'
    site_name = 'Pangatira'
    start_year = 2010
    mid_pt = 2015
    end_year = 2020


'''
File Locations/Paths
--------------------
sampling_plot: Name of the sampling plot (same as site_name)
pred_path: Path to the predicted deforestation raster
mask_path: Path to the KMeans clustered raster for the sampling plot
outpath: Path to save the masked raster
def1_path: Path to the deforestation raster for the monitoring period
def2_path: Path to the deforestation raster for the projection period
aff1_path: Path to the afforestation raster for the monitoring period
aff2_path: Path to the afforestation raster for the projection period
'''

sampling_plot = site_name
pred_path = f'./data/GEE_exports_{district_name}/Acre_Adjucted_Density_Map_VP.tif'
mask_path = f'./data/GEE_exports_{district_name}/' + sampling_plot + '_KMeans_clusters.tif'
outpath = f'./data/GEE_exports_{district_name}/export_masked.tif'
def1_path = f"./data/GEE_exports_{district_name}/deforestation_map_{start_year}_{mid_pt}.tif"
def2_path = f"./data/GEE_exports_{district_name}/deforestation_map_{start_year}_{end_year}.tif"
aff1_path = f"./data/GEE_exports_{district_name}/afforestation_{start_year}_{mid_pt}.tif"
aff2_path = f"./data/GEE_exports_{district_name}/afforestation_{start_year}_{end_year}.tif"

# Initialize final result dataframe
final_result = pd.DataFrame(columns=['cluster', 'projected deforestation', 'deforestation_2010_2015', 'deforestation_2010_2020', 'afforestation_2010_2015', 'afforestation_2010_2020'])




for j in range(7):  # Assuming clusters are labeled from 1 to 7
    k = j + 1 # Cluster 0 -> 1, Cluster 1 -> 2, ..., Cluster 6 -> 0
    result = [k%7]
    for i in range(5): # 0: predicted deforestation, 1: def1, 2: def2, 3: aff1, 4: aff2
        if i == 0:
            src_path = pred_path
        elif i == 1:
            src_path = def1_path
        elif i == 2:
            src_path = def2_path
        elif i == 3:
            src_path = aff1_path
        elif i == 4:
            src_path = aff2_path
        # Open source raster
        with rasterio.open(src_path) as src:
            src_crs = src.crs
            src_transform = src.transform
            src_width = src.width
            src_height = src.height
            src_meta = src.meta.copy()

        # Open mask raster and reproject it to source raster's CRS and shape
        with rasterio.open(mask_path) as mask_r:
            mask_data = mask_r.read(1)
            mask_data[mask_data == 0] = 7 # Change 0 to 7 (0 is non-forest in our case)            
            mask_data = np.empty((mask_r.count, src_height, src_width), dtype=mask_r.dtypes[0])
            reproject(
                source=rasterio.band(mask_r, 1),
                destination=mask_data[0],
                src_transform=mask_r.transform,
                src_crs=mask_r.crs,
                dst_transform=src_transform,
                dst_crs=src_crs,
                resampling=Resampling.nearest
            )

        # Open source raster again to read data
        with rasterio.open(src_path) as src:
            src_data = src.read()

        # Create boolean mask where mask raster == 1
        value_mask = mask_data[0] == k

        # Apply mask to source raster
        masked_data = np.where(value_mask, src_data, 0)

        # Save output
        with rasterio.open(outpath, "w", **src_meta) as dst:
            dst.write(masked_data)
        if i == 0:
            result.append(sum(sum(masked_data[0]))*0.404686)

        else:
            result.append(sum(sum(masked_data[0]))*0.09)


    final_result.loc[len(final_result)] = result
final_result.to_csv(f'./data/GEE_exports_{district_name}/' + sampling_plot + '_forest_cover_change.csv', index=False)


'''
Calculating Additionality
----------------------
Dataframe columns:
cluster: Cluster number
projected_deforestation: Projected deforestation area (in hectares)
actual_deforestation: Actual deforestation area (in hectares)
afforestation: Afforestation area (in hectares)
additionality_area: Additionality area (in hectares)
'''

additionality_table = pd.DataFrame(columns=['cluster', 'projected_deforestation', 'actual_deforestation', 'afforestation'])
additionality_area = []
for i in range(len(final_result)):
    row = [final_result.iloc[i]['cluster']]
    row.append(final_result.iloc[i]['projected deforestation'])
    row.append(final_result.iloc[i]['deforestation_2010_2020'])
    row.append(final_result.iloc[i]['afforestation_2010_2020'])
    additionality_area.append(final_result.iloc[i]['projected deforestation'] - final_result.iloc[i]['deforestation_2010_2020'] + final_result.iloc[i]['afforestation_2010_2020'])
    additionality_table.loc[len(additionality_table)] = row

additionality_table['additionality_area'] = additionality_area
additionality_table  =additionality_table.sort_values(by='cluster', ascending=True)
additionality_table.loc[len(additionality_table)] = ['Total', additionality_table['projected_deforestation'].sum(), additionality_table['actual_deforestation'].sum(), additionality_table['afforestation'].sum(), additionality_table['additionality_area'].sum()]
additionality_table = additionality_table.round(2)
# additionality_table.rename(columns={'projected_deforestation': 'Projected Deforestation (ha)', 'actual_deforestation': 'Actual Deforestation (ha)', 'afforestation': 'Afforestation (ha)', 'additionality_area': 'Additionality Area (ha)'}, inplace=True)

additionality_table.to_csv(f'./data/GEE_exports_{district_name}/' + sampling_plot + '_additionality_per_cluster.csv', index=False)

print(additionality_table)