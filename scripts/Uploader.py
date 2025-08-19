import subprocess
import os

def upload_tif_to_ee(local_file, asset_id):
    """
    Uploads a GeoTIFF to Google Earth Engine assets.

    Parameters:
    -----------
    local_file : str
        Path to the .tif file on your computer.
    asset_id : str
        Destination asset ID in Earth Engine (e.g. "users/username/my_asset").
    """
    if not os.path.exists(local_file):
        raise FileNotFoundError(f"File not found: {local_file}")

    print(f"Uploading {local_file} to Earth Engine as {asset_id} ...")

    # Call the earthengine CLI
    result = subprocess.run([
        "earthengine", "upload", "image",
        "--asset_id=" + asset_id,
        local_file
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Upload failed:")
        print(result.stderr)
    else:
        print("✅ Upload started successfully.")
        print(result.stdout)
        print("Check progress with: earthengine tasks list")



local_file = r"C:\Users\Jayesh Tripathi\Desktop\BECC\data\GEE_exports_Dhenkanal\Acre_Adjucted_Density_Map_VP.tif"
asset_id   = "projects/cogent-range-308518/assets/Acre_Adjucted_Density_Map_VP"

upload_tif_to_ee(local_file, asset_id)
