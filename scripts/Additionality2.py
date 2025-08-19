import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import box
import numpy as np 

import pandas as pd
# Paths

sampling_plot = 'Pangatira'
pred_path = './data/GEE_exports_Dhenkanal/Acre_Adjucted_Density_Map_VP.tif'
mask_path = './data/GEE_exports_Dhenkanal/' + sampling_plot + '_KMeans_Cluster.tif'
outpath = './data/GEE_exports_Dhenkanal/export_masked.tif'
def1_path = "./data/GEE_exports_Dhenkanal/deforestation_map_2010_2015.tif"
def2_path = "./data/GEE_exports_Dhenkanal/deforestation_map_2010_2020.tif"
aff1_path = "./data/GEE_exports_Dhenkanal/afforestation_2010_2015.tif"
aff2_path = "./data/GEE_exports_Dhenkanal/afforestation_2010_2020.tif"



# Open mask raster



final_result = pd.DataFrame(columns=['cluster', 'projected deforestation', 'deforestation_2010_2015', 'deforestation_2010_2020', 'afforestation_2010_2015', 'afforestation_2010_2020'])

for j in range(7):
    k = j + 1
    result = [k%7]

    for i in range(5):
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
            mask_data[mask_data == 0] = 7
            
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
            # print(sum(sum(masked_data[0]))*0.404686)
        else:
            result.append(sum(sum(masked_data[0]))*0.09)
            # print(sum(sum(masked_data[0]))*0.09) 
        print(result)
    final_result.loc[len(final_result)] = result
final_result.to_csv(f'./data/GEE_exports_Dhenkanal/' + sampling_plot + '_forest_cover_change.csv', index=False)


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

additionality_table.to_csv(f'./data/GEE_exports_Dhenkanal/' + sampling_plot + '_additionality_per_cluster.csv', index=False)

print(additionality_table)