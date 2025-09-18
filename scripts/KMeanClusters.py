import ee
ee.Authenticate()
ee.Initialize(project="cogent-range-308518")
import pandas as pd

import os
import sys
import json


'''
Establishing Global Parameters
------------------------------
state_name: Name of the state
district_name: Name of the district
site_name: Name of the site
'''

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
    '''
    Function to mask clouds in a Sentinel-2 image
    Args:
        img: ee.Image, Sentinel-2 image
    '''
    qa = img.select('QA60')
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11

    mask = (qa.bitwiseAnd(cloudBitMask).eq(0)).And(
        qa.bitwiseAnd(cirrusBitMask).eq(0))

    return img.updateMask(mask).divide(10000)

def kmeans_wrapper(img):
    '''
    Wrapper function to apply KMeans clustering to an image
    Args:
        img: ee.Image, input image
    '''
    return applyKMeans(img, img.geometry(), 7)

def calculateNDVI(image):
    '''
    Function to calculate NDVI for a Sentinel-2 image
    Args:
        image: ee.Image, Sentinel-2 image
    Returns:
        ee.Image, image with NDVI band added
    '''
    nir = image.select('B8')
    red = image.select('B4')
    ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
    return image.addBands(ndvi)


def applySNIC_with_meanNDVI(image):
    '''
    Apply SNIC segmentation and compute mean NDVI per segment.
    Args:
        image: ee.Image with NDVI band
    Returns:
        ee.Image with SNIC mean NDVI band
    '''
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
    '''
    Function to apply KMeans clustering to an image based on mean NDVI of SNIC segments.
    Args:
        image: ee.Image with mean NDVI band
        geometry: ee.Geometry, region of interest
        num_clusters: int, number of clusters for KMeans
    Returns:
        ee.Image with KMeans cluster band
    '''
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


# Load the sites file for the specified state
if os.path.exists(f'C:\\Users\\Jayesh Tripathi\\Desktop\\BECC\\data\\GEE_exports_{district_name}\\{state_name}_sites.csv'):
    state_sites = pd.read_csv(f'C:\\Users\\Jayesh Tripathi\\Desktop\\BECC\\data\\GEE_exports_{district_name}\\{state_name}_sites.csv')
    run = True
else:
    print("Please Upload the Sites file to the Data Folder")

if run:
    site = state_sites[state_sites['Name'] == site_name]
    num_site = len(site)

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
