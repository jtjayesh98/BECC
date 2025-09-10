import ee
import geemap

# Initialize
ee.Initialize()

region = "Dhenkanal"


classified2 = ee.Image("projects/cogent-range-308518/assets/Pangatira_KMeans_Cluster")


# Load GAUL dataset
gaul = ee.FeatureCollection("FAO/GAUL/2015/level2")

district = (gaul
            .filter(ee.Filter.eq('ADM0_NAME', 'India'))
            .filter(ee.Filter.eq('ADM2_NAME', region)))

geometry = district.geometry()

site = "Pangatira"

params = {
    'min': 0,
    'max': 6,
    'palette': ['red', 'green', 'blue', 'yellow', 'orange', 'cyan', 'purple']
}

# ---------- Function to get class boundary ----------
def getClassBoundary(classValue):
    classMask = classified2.eq(classValue)
    vectors = classMask.selfMask().reduceToVectors(
        geometry=classified2.geometry(),
        scale=25,
        geometryType='polygon',
        eightConnected=False,
        labelProperty='class',
        maxPixels=1e13
    )
    return vectors.map(lambda f: f.set('class', classValue))

cluster = 1
boundary = getClassBoundary(cluster)

# ---------- Satellite Embeddings ----------
startDate = ee.Date.fromYMD(2022, 1, 1)
endDate = startDate.advance(1, "year")

embeddings = ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
embeddingsFiltered = (embeddings
                      .filterDate(startDate, endDate)
                      .filterBounds(geometry))

embeddingsProjection = embeddingsFiltered.first().select(0).projection()

embeddingsImage = (embeddingsFiltered.mosaic()
                   .setDefaultProjection(embeddingsProjection))

# ---------- GEDI Dataset ----------
dataset = ee.Image("LARSE/GEDI/GEDI04_B_002")

# Mask unreliable GEDI
def errorMask(image):
    relative_se = image.select("SE").divide(image.select("MU"))
    return image.updateMask(relative_se.lte(0.5))

# Mask slope > 30%
def slopeMask(image):
    glo30 = ee.ImageCollection("COPERNICUS/DEM/GLO30")
    glo30Filtered = glo30.filterBounds(geometry).select("DEM")

    demProj = glo30Filtered.first().select(0).projection()

    elevation = glo30Filtered.mosaic().rename("dem").setDefaultProjection(demProj)
    slope = ee.Terrain.slope(elevation)
    return image.updateMask(slope.lt(30))

datasetProjection = dataset.select("MU").projection()
datasetProcessed = slopeMask(errorMask(dataset))
datasetMosaic = datasetProcessed.select("MU").setDefaultProjection(datasetProjection)

datasetVis = {
    "min": 0,
    "max": 200,
    "palette": ["#edf8fb", "#b2e2e2", "#66c2a4", "#2ca25f", "#006d2c"],
    "bands": ["MU"],
}

# ---------- Create stacked image ----------
gridScale = 100
gridProjection = ee.Projection("EPSG:3857").atScale(gridScale)

stacked = embeddingsImage.addBands(datasetMosaic).resample("bilinear")
stackedResampled = (stacked
                    .reduceResolution(reducer=ee.Reducer.mean(), maxPixels=1024)
                    .reproject(crs=gridProjection))

stackedResampled = stackedResampled.updateMask(stackedResampled.mask().gt(0))

# Export stackedResampled to Asset
exportFolder = "projects/cogent-range-308518/assets/"
mosaicExportImage = "gedi_mosaic_" + region
mosaicExportImagePath = exportFolder + mosaicExportImage

task1 = ee.batch.Export.image.toAsset(
    image=stackedResampled.clip(geometry),
    description="GEDI_Mosaic_Export",
    assetId=mosaicExportImagePath,
    region=geometry,
    scale=gridScale,
    maxPixels=1e10
)
task1.start()

stackedResampled = ee.Image(mosaicExportImagePath)

predictors = embeddingsImage.bandNames()
predicted = datasetMosaic.bandNames().get(0)

predictorImage = stackedResampled.select(predictors)
predictedImage = stackedResampled.select([predicted])

classMask = predictedImage.mask().toInt().rename("class")

numSamples = 1000
training = (stackedResampled.addBands(classMask)
            .stratifiedSample(
                numPoints=numSamples,
                classBand="class",
                region=geometry,
                scale=gridScale,
                classValues=[0, 1],
                classPoints=[0, numSamples],
                dropNulls=True,
                tileScale=16
            ))

# ---------- Train RF Regressor ----------
model = (ee.Classifier.smileRandomForest(50)
         .setOutputMode("REGRESSION")
         .train(features=training,
                classProperty=predicted,
                inputProperties=predictors))

predictedSamples = training.classify(model, outputName="agbd_predicted")

# RMSE calculation
def calculateRmse(input_fc):
    observed = ee.Array(input_fc.aggregate_array("MU"))
    predicted_vals = ee.Array(input_fc.aggregate_array("agbd_predicted"))
    rmse = observed.subtract(predicted_vals).pow(2).reduce("mean", [0]).sqrt().get([0])
    return rmse

rmse = calculateRmse(predictedSamples)
print("RMSE:", rmse.getInfo())

# Predict across region
predictedImage = stackedResampled.classify(model, outputName="MU")

predictedExportImage = "predicted_agbd_" + region
predictedExportImagePath = exportFolder + predictedExportImage

task2 = ee.batch.Export.image.toAsset(
    image=predictedImage.clip(geometry),
    description="Predicted_Image_Export",
    assetId=predictedExportImagePath,
    region=geometry,
    scale=gridScale,
    maxPixels=1e10
)
task2.start()

predictedImage = ee.Image(predictedExportImagePath)

gediVis = {
    "min": 0,
    "max": 200,
    "palette": ["#edf8fb", "#b2e2e2", "#66c2a4", "#2ca25f", "#006d2c"],
    "bands": ["MU"],
}

# ---------- Landcover masking ----------
worldcover = ee.ImageCollection("ESA/WorldCover/v200").first()
worldcoverResampled = (worldcover
                       .reduceResolution(reducer=ee.Reducer.mode(), maxPixels=1024)
                       .reproject(crs=gridProjection))

landCoverMask = (worldcoverResampled.eq(10)
                 .Or(worldcoverResampled.eq(20))
                 .Or(worldcoverResampled.eq(30))
                 .Or(worldcoverResampled.eq(40))
                 .Or(worldcoverResampled.eq(95)))

predictedImageMasked = predictedImage.updateMask(landCoverMask)

pixelAreaHa = ee.Image.pixelArea().divide(10000)
predictedAgb = predictedImageMasked.multiply(pixelAreaHa).clip(boundary)

stats = predictedAgb.reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=geometry,
    scale=gridScale,
    maxPixels=1e10,
    tileScale=16
)

totalAgb = stats.getNumber("MU")
print("Total AGB (Mg):", totalAgb.getInfo())

# ---------- Visualization ----------
Map = geemap.Map()
Map.centerObject(geometry, 8)
Map.addLayer(embeddingsImage, {}, "Embeddings", False)
Map.addLayer(datasetMosaic, datasetVis, "GEDI L4A (Filtered)", False)
Map.addLayer(predictedImage, gediVis, "Predicted AGBD")
Map.addLayer(predictedImageMasked, gediVis, "Predicted AGBD (Masked)")
Map
