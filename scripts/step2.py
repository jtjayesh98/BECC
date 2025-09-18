import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import pairwise_distances
import os
import rasterio
from rasterio.warp import transform
import pandas as pd
import glob
import os
import math

from FinalStage_utils import applySNIC_with_meanNDVI, applyKMeans, maskS2clouds, calculateNDVI

import ee
ee.Authenticate()
ee.Initialize(project="cogent-range-308518")

import rasterio
import pandas as pd

import sys
import os



'''
Establishing Global Parameters
------------------------------
site_name: Name of the site
district_name: Name of the district
state_name: Name of the state
'''

if len(sys.argv) > 1:
    site_name = sys.argv[1]
    district_name = sys.argv[2]
    state_name = sys.argv[3]
else:
    site_name = 'Pangatira'
    district_name = 'Dhenkanal'
    state_name = 'Odisha'



def create_image_collection(district_name):
    '''
    Function to create an image collection for the specified district.
    Args:
        district_name: Name of the district
    Returns:
        Tuple containing the image and its geometry.
    '''
    site_name = 'Pangatira'

    # Define the region of interest: Dhenkanal district of Odisha
    admin2 = ee.FeatureCollection("FAO/GAUL/2015/level2").filter(ee.Filter.eq("ADM2_NAME", "Dhenkanal"))
    geometry = admin2.geometry()

    dataset = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterDate('2020-01-01', '2020-01-30')
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                .filterBounds(geometry)
                .map(maskS2clouds)
                .map(calculateNDVI)
                .map(applySNIC_with_meanNDVI)
                .map(lambda img: applyKMeans(img, district_name, num_clusters=7)))

    image = dataset.first().clip(geometry)

    return (image, geometry)

def individual_cluster_biomass(site_name):
    '''
    Function to assign cluster values to individual plot data and save cluster-wise CSV files.
    Args:
        site_name: Name of the site
    '''
    site_name2 = site_name
    # File paths (update these to your actual file locations)
    geotiff_path = f'./data/GEE_exports_{district_name}/' +site_name2 + '_KMeans_clusters.tif'  # Replace with your GeoTIFF file path
    csv_path = f'./data/GEE_exports_{district_name}/' + site_name.upper() + '_biomass.csv'          # Your CSV file

    # Load GeoTIFF
    dataset = rasterio.open(geotiff_path)

    # Load CSV
    df = pd.read_csv(csv_path)

    # Define coordinate systems
    src_crs = 'EPSG:4326'  # CSV coordinates are in WGS84 (lat/long)
    dst_crs = dataset.crs  # GeoTIFF coordinate system

    # Extract coordinates from CSV
    lons = df['Plot Long']
    lats = df['Plot Lat']

    # Transform coordinates to GeoTIFF CRS
    xs, ys = transform(src_crs, dst_crs, lons, lats)

    # Get GeoTIFF bounds for failsafe check
    bounds = dataset.bounds

    # Function to check if a point is within GeoTIFF bounds
    def is_within_bounds(x, y, bounds):
        return bounds.left <= x <= bounds.right and bounds.bottom <= y <= bounds.top

    # Assign cluster values to each point
    cluster_values = []
    for x, y in zip(xs, ys):
        if is_within_bounds(x, y, bounds):
            # Sample the cluster value from the GeoTIFF (assuming single-band raster)
            value = next(dataset.sample([(x, y)]))[0]
            cluster_values.append(value)
        else:
            # Failsafe: assign None for points outside the GeoTIFF
            cluster_values.append(None)

    # Add cluster column to DataFrame
    df['Cluster'] = cluster_values

    # Group by cluster and save to separate files
    for cluster, group in df.groupby('Cluster'):
        if cluster is not None:
            # Save each cluster group to a CSV file
            group.to_csv(f'./data/GEE_exports_{district_name}/cluster_{int(cluster)}.csv', index=False)
        else:
            # Optionally save points outside the GeoTIFF to a separate file
            group.to_csv(f'./data/GEE_exports_{district_name}/cluster_outside.csv', index=False)

    # Close the GeoTIFF dataset
    dataset.close()




# Find all cluster CSV files

def calculate_area(df):
    '''
    Function to calculate total area based on plot data.
    Args:
        df: DataFrame containing plot data
    Returns:
        Total area calculated from the plots
    '''
    plots = df["Plot No"].unique()
    area = 0
    print(plots)
    for plot in plots:
        area = area + math.pi*100
        # area += df[df["Plot No"] == plot]["Area"].iloc[0]
    return area

def calculate_biomass_plot(df):
    '''
    Function to calculate total biomass based on plot data.
    Args:
        df: DataFrame containing plot data
    Returns:
        Total biomass calculated from the plots
    '''
    individual_biomass = df['Total biomass']
    return individual_biomass.sum()

def biomass_summary():
    '''
    Function to summarize biomass for each cluster and save the results to a CSV file.
    '''
    cluster_files = glob.glob(f'./data/GEE_exports_{district_name}/cluster_*.csv')
    # Initialize list to store results
    results = []
    # Process each cluster file
    for file in cluster_files:
        # Extract cluster ID from filename (e.g., 'cluster_0.csv' -> 0)
        if os.path.basename(file).split('_')[1].split('.')[0].isnumeric():
            cluster_id = int(os.path.basename(file).split('_')[1].split('.')[0])

        # Read the CSV file
            df = pd.read_csv(file)

            # Sum the 'Total biomass' column
            # total_biomass = df['Total biomass'].sum()
            total_biomass = calculate_biomass_plot(df)
            # total_area_m2 = df['Area'].sum() # Here we are assuming the area is in m2, you can change it later according to the new information/data available
            total_area_m2 = calculate_area(df)
            if total_area_m2 > 0:
                biomass_per_ha = (total_biomass * 1.25) / (total_area_m2 / 10000)
            else:
                biomass_per_ha = None # Handle division by zero if needed

            # Append result
            results.append({'Cluster_ID': cluster_id, 'Total_Biomass': total_biomass, 'Total_Area_m2': total_area_m2, 'Biomass_per_ha': biomass_per_ha})

    # Create DataFrame from results
    results_df = pd.DataFrame(results)

    # Sort by Cluster_ID for clarity
    results_df = results_df.sort_values('Cluster_ID')

    # Save to CSV
    results_df.to_csv(f'./data/GEE_exports_{district_name}/cluster_biomass_summary.csv', index=False)




site_name2 = site_name
image, geometry = create_image_collection(district_name=district_name)

biomass_csv_path = f'./data/GEE_exports_{district_name}/cluster_biomass_summary.csv'
output_csv_path = f'./data/GEE_exports_{district_name}/imputed_biomass_clusters.csv'
cluster_tif = f'./data/GEE_exports_{district_name}/' + site_name2 +'_KMeans_clusters.tif'

# Load Sentinel-2 image collection for the year 2020
s2_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
    .filterBounds(geometry) \
    .filterDate('2020-01-01', '2020-12-31') \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
# Calculate EVI: 2.4 * (NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1)
s2 = s2_collection.median()
band_names = s2.bandNames().getInfo()
nir = s2.select('B8')
red = s2.select('B4')
blue = s2.select('B2')
try:
    evi = s2.expression(
        '2.4 * (NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1)',
        {
            'NIR': nir,
            'RED': red,
            'BLUE': blue
        }
    ).rename('EVI')
except ee.EEException as e:
    print("Error calculating EVI:", e)
    raise


# Load SRTM and calculate slope
srtm = ee.Image('USGS/SRTMGL1_003')
slope = ee.Terrain.slope(srtm).rename('SLOPE')
predictors = evi.addBands(slope)
predictors.bandNames().getInfo()
clusters = image.select('KMeans_clusters')
cluster_bands = clusters.bandNames().getInfo()
print(f"Cluster image bands: {cluster_bands}")
# Assume first band contains cluster values
cluster_band = cluster_bands[0]
# Get unique cluster values (approximate, may be slow for large images)
unique_values = clusters.reduceRegion(
    reducer=ee.Reducer.frequencyHistogram(),
    geometry=geometry,
    scale=10,
    maxPixels=1e9
).get(cluster_band).getInfo()
print(f"Unique cluster values in {site_name}: {list(unique_values.keys())}")

# Function to extract mean EVI and slope per cluster
def extract_features_per_cluster(cluster_id):
    try:
        # Create mask for the cluster
        mask = clusters.select(cluster_band).eq(cluster_id)

        # Check if the cluster has any pixels in the geometry
        pixel_count_dict = mask.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=10,
            maxPixels=1e9
        )
        pixel_count = pixel_count_dict.get(cluster_band).getInfo() if pixel_count_dict.get(cluster_band) is not None else 0

        if pixel_count == 0:
            print(f"No pixels found for cluster {cluster_id}. Returning NaN.")
            return [np.nan, np.nan]

        # Apply mask to predictors
        masked_predictors = predictors.updateMask(mask)

        # Calculate mean EVI and slope
        stats = masked_predictors.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=10,
            maxPixels=1e9
        )

        evi_val = stats.get('EVI').getInfo() if stats.get('EVI') is not None else None
        slope_val = stats.get('SLOPE').getInfo() if stats.get('SLOPE') is not None else None

        print(f"Cluster {cluster_id}: Pixel count = {int(pixel_count)} EVI = {evi_val}, SLOPE = {slope_val}")
        return [evi_val if evi_val is not None else np.nan,
                slope_val if slope_val is not None else np.nan]

    except ee.EEException as e:
        print(f"Error processing cluster {cluster_id}: {e}")
        return [np.nan, np.nan]
    
cluster_ids = [0, 1, 2, 3, 4, 5, 6]
features = []
for cid in cluster_ids:
    try:
        feat = extract_features_per_cluster(cid)
        features.append(feat)
    except Exception as e:
        print(f"Error processing cluster {cid}: {e}")
        features.append([np.nan, np.nan])


# Create DataFrame with features
feature_df = pd.DataFrame(features, columns=['EVI', 'SLOPE'], index=cluster_ids)
# Load known biomass data
individual_cluster_biomass(site_name=site_name)
biomass_summary()
try:
    biomass_df = pd.read_csv(biomass_csv_path)
    biomass_df.set_index('Cluster_ID', inplace=True)
except FileNotFoundError:
    print(f"Error: File '{biomass_csv_path}' not found.")
    raise
# Merge features with biomass
data_df = feature_df.join(biomass_df, how='left')
# Check for missing features
if data_df[['EVI', 'SLOPE']].isna().all().any():
    print("Error: Some clusters have no EVI or SLOPE values. Check clusters.tif or geometry.")
    raise ValueError("Missing features for some clusters")
elif data_df[['EVI', 'SLOPE']].isna().any().any():
    print("Warning: Missing EVI or SLOPE values for some clusters. Imputation may be affected.")

# Prepare data for imputation
X = data_df[['EVI', 'SLOPE']].values
y = data_df['Biomass_per_ha'].values


from sklearn.neighbors import KNeighborsRegressor

# Drop rows with missing X values (EVI/SLOPE must be present for imputation)
valid_mask = ~np.isnan(X).any(axis=1)

# Split into known and missing biomass
X_known = X[valid_mask & ~np.isnan(y)]
y_known = y[valid_mask & ~np.isnan(y)]

X_missing = X[valid_mask & np.isnan(y)]
missing_indices = np.where(valid_mask & np.isnan(y))[0]

# Fit k-NN regressor
knn = KNeighborsRegressor(n_neighbors=1, weights='distance')
knn.fit(X_known, y_known)

# Predict missing y
y_pred = knn.predict(X_missing)

# Fill in missing values
y_imputed = y.copy()
y_imputed[missing_indices] = y_pred
print(y_imputed)
imputed_df = pd.DataFrame({
    'Cluster_ID': cluster_ids,
    'Biomass_per_ha': y_imputed
})
imputed_df.to_csv(output_csv_path, index=False)
print(f"Imputed biomass saved to {output_csv_path}")

site_name = site_name

file = f"./data/GEE_exports_{district_name}/" + site_name + "_additionality_per_cluster.csv"

df = pd.read_csv(file)
additionality_biomass = 0
actual_deforestation_biomass = 0
projected_deforestation_biomass = 0
print(df)
biomass_deforested = []
biomass_projected_deforested = []
biomass_afforested = []
for i in range(7):
  additionality_biomass += df.iloc[i]["additionality_area"]*imputed_df.iloc[i]["Biomass_per_ha"]
  actual_deforestation_biomass += df.iloc[i]["actual_deforestation"]*imputed_df.iloc[i]["Biomass_per_ha"]
  projected_deforestation_biomass += df.iloc[i]["projected_deforestation"]*imputed_df.iloc[i]["Biomass_per_ha"]
  biomass_deforested.append(df.iloc[i]["actual_deforestation"]*imputed_df.iloc[i]["Biomass_per_ha"])
  biomass_projected_deforested.append(df.iloc[i]["projected_deforestation"]*imputed_df.iloc[i]["Biomass_per_ha"])
  biomass_afforested.append(df.iloc[i]["afforestation"]*imputed_df.iloc[i]["Biomass_per_ha"])
biomass_deforested.append(sum(biomass_deforested))
biomass_projected_deforested.append(sum(biomass_projected_deforested))
biomass_afforested.append(sum(biomass_afforested))
df['biomass_deforested'] = biomass_deforested
df['biomass_projected_deforested'] = biomass_projected_deforested
df['biomass_afforested'] = biomass_afforested
print(df)
print(f'Total Biomass Deforested is {actual_deforestation_biomass} kg')
print(f'Total Biomass Projected to be deforested is {projected_deforestation_biomass} kg')
print(f'Total Biomass saved is {additionality_biomass} kg')


print("Actual Deforestated Carbon Weight:" +  str((actual_deforestation_biomass).sum()/2) + " kg")
print("Expected Deforestated Carbon Weight" +  str((projected_deforestation_biomass).sum()/2) + " kg")
print("Additionality of Carbon by Weight:" +  str(additionality_biomass/2) + " kg")
print("Actual Deforestated Carbon Dioxide by Weight:" +  str((actual_deforestation_biomass).sum()*11/6) + " kg")
print("Expected Deforestated Carbon Dioxide by Weight:" +  str((projected_deforestation_biomass).sum()*11/6) + " kg")
print("Additionality of Carbon Dioxide by Weight:" +  str((additionality_biomass)*11/6) + " kg")