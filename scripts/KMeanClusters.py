import ee
ee.Authenticate()
ee.Initialize(project="cogent-range-308518")
import pandas as pd

import os
import sys



if len(sys.argv) > 1:
    state_name = sys.argv[1]
    district_name = sys.argv[2]
    site_name = sys.argv[3]
else:
    state_name = 'Odisha'
    district_name = 'Dhenkanal'
    site_name = 'Pangatira'


run = False

def maskClouds(img):
    qa = img.select('QA60')
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11

    mask = (qa.bitwiseAnd(cloudBitMask).eq(0)).And(
        qa.bitwiseAnd(cirrusBitMask).eq(0))

    return img.updateMask(mask).divide(10000)

def kmeans_wrapper(img):
    return applyKMeans(img, img.geometry(), 7)

def calculateNDVI(image):
    nir = image.select('B8')
    red = image.select('B4')
    ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
    return image.addBands(ndvi)


def applySNIC_with_meanNDVI(image):
    ndvi = image.select('NDVI')
    snic = ee.Algorithms.Image.Segmentation.SNIC(
        image=ndvi,
        size=10,
        compactness=1,
        connectivity=8,
        neighborhoodSize=256
    )
    clusters = snic.select('clusters').rename('SNIC_clusters')
    clustered_image = image.addBands(clusters)
    meanNDVI = ndvi.addBands(clusters).reduceConnectedComponents(
        reducer=ee.Reducer.mean(),
        labelBand='SNIC_clusters'
    ).rename('mean_NDVI_SNIC')
    return image.addBands(meanNDVI)

def applyKMeans(image, geometry, num_clusters=7):
    training_image = image.select(['mean_NDVI_SNIC'])
    training_data = training_image.sample(
        region=geometry,
        scale=30,
        numPixels=5000,
        seed=0,
        geometries=True
    )
    clusterer = ee.Clusterer.wekaKMeans(num_clusters).train(training_data)
    result = training_image.cluster(clusterer).rename('KMeans_clusters')
    return image.addBands(result)


if os.path.exists(f'C:\\Users\\Jayesh Tripathi\\Desktop\\BECC\\data\\GEE_exports_{district_name}\\{state_name}_sites.csv'):
    state_sites = pd.read_csv(f'C:\\Users\\Jayesh Tripathi\\Desktop\\BECC\\data\\GEE_exports_{district_name}\\{state_name}_sites.csv')
    run = True
else:
    print("Please Upload the Sites file to the Data Folder")

if run:
    site = state_sites[state_sites['Name'] == site_name]
    num_site = len(site)

    # if (num_site == 0):
    #     print("No feature found with Name = '" + site_name + "'. Check the Name value or asset.")
    # elif (num_site > 1):
    #     print("Warning: {num_site} features found with Name = '" + site_name + "'. Using the first one.")
    # print("Number of " + site_name + " features: " + str(num_site))

    import json

    if num_site > 0:
        site_feature = site.iloc[0]
        geojson_dict = json.loads(site_feature['.geo'])
        site_geometry = ee.Geometry(geojson_dict)
        geojson = site_geometry.getInfo()
    else:
        print("No site found.")


    geometry = ee.Geometry.Polygon([geojson['coordinates']])





    feature = ee.Feature(geometry)

    # Paint into an image (value = 1 inside polygon)
    polygon_img = ee.Image().paint(
        featureCollection=ee.FeatureCollection([feature]),
        color=1
    )


    # ...existing code...

    # Define your image collection
    collection = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterDate('2020-01-01', '2021-01-30')
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        .filterBounds(geometry)
        .map(maskClouds)
        .map(calculateNDVI)
        .map(applySNIC_with_meanNDVI)
    )



    # Apply KMeans to each image in the collection


    collection_with_kmeans = collection.map(kmeans_wrapper)

    # Get the first image from the collection with KMeans clusters
    first_img = collection_with_kmeans.first().clip(geometry)



    first_img = first_img.toFloat()


    task = ee.batch.Export.image.toDrive(
        image=first_img.select('KMeans_clusters').clip(geometry),
        description=f'{site_name}_KMeans_clusters',
        folder='GEE_exports_' + district_name,  # Change this to your desired Drive folder name
        fileNamePrefix=f'{site_name}_KMeans_clusters',
        region=geometry,
        scale=30,
        maxPixels=1e13
    )
    task.start()
    print("Export to Google Drive started. Check the Earth Engine Tasks tab for progress.")
