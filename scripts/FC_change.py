import rasterio
import numpy as np

forest_cover1 = "./data/GEE_exports_Dhenkanal/Dhenkanal_2010.tif"
forest_cover2 = "./data/GEE_exports_Dhenkanal/Dhenkanal_2015.tif"
forest_cover3 = "./data/GEE_exports_Dhenkanal/Dhenkanal_2020.tif"

for i in range(2):
    with rasterio.open(forest_cover1) as src:
        data0 = src.read(1)
        meta = src.meta.copy() 
    
    if i == 0:
        change_cover = forest_cover2
    elif i == 1:
        change_cover = forest_cover3
    with rasterio.open(change_cover) as src1:
        data1 = src1.read(1)


    change = np.zeros_like(data0, dtype=np.int8)
    change[(data0 == 1) & (data1 == 0)] = -1
    change[(data0 == 0) & (data1 == 1)] = 1
    change[(data0 == 1) & (data1 == 1)] = 0
    change[(data0 == 0) & (data1 == 0)] = 0

    meta.update(dtype=rasterio.int8)
    deforestation_mask = np.zeros_like(change, dtype=np.int8)
    deforestation_mask[change == 1] = -1
    afforestation_mask = np.zeros_like(change, dtype=np.int8)
    afforestation_mask[change == 1] = 1
    print(change.shape)
    if i == 0:
        with rasterio.open("./data/GEE_exports_Dhenkanal/afforestation_2010_2015.tif", "w", **meta) as dst:
            dst.write(afforestation_mask, 1)
    elif i == 1:
        with rasterio.open("./data/GEE_exports_Dhenkanal/afforestation_2010_2020.tif", "w", **meta) as dst:
            dst.write(afforestation_mask, 1)

    