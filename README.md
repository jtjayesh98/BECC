# Pipeline
The following pipeline will generate Forest Cover Maps for a given region, that are used to estimate the change in the forest cover and train a model that can predict the change in the near future. During the implemententioant of hte pipeline, the following maps will be produced:
* Forest Covers
* Edge to Distance of the Forest
* Jurisdiction Maps
* Predicted Deforestation Maps
There are 1 steps involved in the process, and at the end of each step, a physical action related to file movement is required (such as installing the file from the folder in the Google Drive).

# SETUP

Create a Python Environment and install all the dependencies with the help of `requirements.txt` available in the repository

If in case osgeo/GDAL library's wheel is not installing, please install the pre-built wheel and install the package directly. You can find the prebuilt library for Windows (AMD 64bit) systems with Python 3.13 <a = https://drive.google.com/drive/folders/11syOJuhaX7qSCeN-mvk003r3JkrfuFyP?usp=drive_link>here</a>.


# Step 1: Implementing GEE Operations
Google Earth Engine is used to generate the Forest Covers and Jurisdiction Maps and derive Edge to Distance of the Forest Maps. To run the GEE Operations please run the following CLI operation

`python step.py 1 <DISTRICT = "Dhenkanal"> <START_YEAR = "2010"> <END_OF_MODELING_YEAR = "2015"> <PREDICTION_YEAR = "2020">`

All the files produced will be saved in the Drive in the folder associated with the GEE account. The name of the folder is "GEE_exports_{<DISTRICT>}"; if no DISTRICT was provided, the folder will be named "GEE_exports_Dhenkanal".

Please install the entire folder in the "./data/" folder.

# Step 2: Generating Prediction Maps
After the necessary folder has been installed in the "./data/" folder, running the following command will generate the prediction maps for the given region for the year 2020. The current implementation produces the results based on the guidelines provided from ClarkLabs {CITE}

`python ./scripts/step.py 0 <DISTRICT = "Dhenkanal"> <START_YEAR = "2010"> <END_OF_MODELING_YEAR = "2015"> <PREDICTION_YEAR = "2020"`

All the necessary prediction files will be saved in the "./data/GEE_exports_{<DISTRICT>}" folder.

# Step 3: Calculate Deforestation and Afforestation
Deforestation and Afforestation predictions are necessary for further analysis, hence running the following command calculates the deforestation and afforestation regions for the three different periods.

`python ./scripts/FC_change.py`

# Step 4: Clustering
For the region of interest inside the district, for which sampling plots have been measured, it can be clustered to estimate the biomass.

## 4.1: Estimating Biomass
A given sampling survey will contain the different trees recorded in the sample and the size of the region. Each tree species has an associated allometric equation, which can build allometric equation of the tree based on characteristic features of the tree. 

Upload the following spreadsheet containing the sampling survey for a `region` to the 
"./data/GEE_exports_<DISTRICT>" folder:
* REGION + "_allometric.csv (REGION should be in uppercase)

Run the following the command line to estimate the biomass:
`python ./scripts/parser.py <REGION = "Pangatira">`

## 4.2: Clustering
The clustering step creates different clusters for the sampled region. Run the following command to save the clusters as a GEOTIF:
`python ./scripts/KMeansClusters.py`

# 5: Calculating Additionality
Additionality is the biomass added or lost during the time period from the start of the modeling and prediction year. Run the following code to save the Additionality:
`python ./scripts/Additionality2.py`

# 6: Estimate the Biomass change in Mass of Carbon Dioxide in change
For the final step, run the following step to calculate the total change in the weight of CO2 and Carbon that occured during the period of modeling and prediction. Run the following command to estimate this change:
`python ./scripts/step2.py`

# 7: Compare the Results
The following command line will estimate the biomass estimated in Step 5 with the prediciton results produced from a Regression Model that is trained on the GEDI Dataset for each cluster.
`python ./scripts/Evaluator.py`