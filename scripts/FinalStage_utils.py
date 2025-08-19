import ee
from ee import batch

def maskS2clouds(image):
    """
    Function to mask clouds using the Sentinel-2 QA band
    Args:
        image: ee.Image, Sentinel-2 image
    Returns:
        ee.Image, cloud masked Sentinel-2 image
    """
    qa = image.select('QA60')
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11
    mask = qa.bitwiseAnd(cloudBitMask).eq(0) \
            .And(qa.bitwiseAnd(cirrusBitMask).eq(0))
    return image.updateMask(mask).divide(10000)

def calculateNDVI(image):
    """
    Function to calculate NDVI for a Sentinel-2 image
    Args:
        image: ee.Image, Sentinel-2 image
    Returns:
        ee.Image, image with NDVI band added
    """
    nir = image.select('B8')
    red = image.select('B4')
    ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
    return image.addBands(ndvi)

def applySNIC_with_meanNDVI(image):
    """
    Apply SNIC segmentation and compute mean NDVI per segment.
    Args:
        image: ee.Image with NDVI band
    Returns:
        ee.Image with SNIC mean NDVI band
    """
    ndvi = image.select('NDVI')

    # Apply SNIC
    snic = ee.Algorithms.Image.Segmentation.SNIC(
        image=ndvi,
        size=10,
        compactness=1,
        connectivity=8,
        neighborhoodSize=256
    )

    # Get cluster ID band
    clusters = snic.select('clusters').rename('SNIC_clusters')

    # Add the clusters to the image
    clustered_image = image.addBands(clusters)

    # Compute mean NDVI per SNIC cluster
    meanNDVI = ndvi.addBands(clusters).reduceConnectedComponents(
        reducer=ee.Reducer.mean(),
        labelBand='SNIC_clusters'
    ).rename('mean_NDVI_SNIC')

    # Add mean NDVI as a new band
    return image.addBands(meanNDVI)


def applyKMeans(image, region, num_clusters=7,):
    """
    Function to apply K-means clustering on SNIC clusters to fix the number of strata
    Args:
        image: ee.Image, Sentinel-2 image with SNIC_clusters band
        num_clusters: int, number of desired strata
    Returns:
        ee.Image, image with K-means cluster band
    """
    # Select the SNIC clusters and NDVI for clustering
    # training_image = image.select(['SNIC_clusters', 'NDVI'])
    admin2 = ee.FeatureCollection("FAO/GAUL/2015/level2").filter(ee.Filter.eq("ADM2_NAME", region))
    geometry = admin2.geometry()
    
    training_image = image.select([
        'mean_NDVI_SNIC'
    ])

    # Sample the image to create a FeatureCollection
    training_data = training_image.sample(
        region=geometry,
        scale=30,
        numPixels=5000,  # Adjust number of points as needed
        seed=0,
        geometries=True
    )

    # Create and train a K-means clusterer
    clusterer = ee.Clusterer.wekaKMeans(num_clusters).train(training_data)

    # Apply the clusterer to the image
    kmeans_clusters = image.cluster(clusterer).rename('KMeans_clusters')

    return image.addBands(kmeans_clusters)

