import argparse
import os
import pathlib
import zipfile
import shutil
import requests
import boto3

import shapely
import urllib3
from dotenv import load_dotenv
import pprint

from productquery import queryProducts
from tiling import build_tiling_info

# Load environment variables
load_dotenv()

USERNAME = os.environ.get("CDSE_USERNAME")
PASSWORD = os.environ.get("CDSE_PASSWORD")

iowaPoly = shapely.Polygon(
    [
        [-95.734863, 40.597271],
        [-96.679687, 43.53262],
        [-91.362305, 43.500752],
        [-90.043945, 42.065607],
        [-91.318359, 40.563895],
        [-95.734863, 40.597271],
    ]
)

argparser = argparse.ArgumentParser(
    prog="python3 main.py",
    description="Downloads Sentinel data from the given region",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

argparser.add_argument(
    "-l",
    "--location",
    type=str,
    default=iowaPoly.wkt,
    help="The location (in wkt) to query copernicus for",
)

argparser.add_argument(
    "-m",
    "--months",
    type=int,
    nargs="*",
    choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    default=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    help="The months to query copernicus for",
)

argparser.add_argument(
    "-sy",
    "--start-year",
    type=int,
    help="The year to start looking for data on (inclusive)",
    required=True,
)

argparser.add_argument(
    "-ey",
    "--end-year",
    type=int,
    help="The year to end looking for data on (inclusive)",
    required=True,
)

argparser.add_argument(
    "-cc",
    "--max-cloud-cover",
    type=int,
    help="The maximum acceptable cloud cover (in %)",
    default=20,
)

argparser.add_argument(
    "-mti",
    "--minimum-tile-intersection",
    type=int,
    help="The minimum acceptable tile intersection with the shape (in %)",
    default=30,
)

argparser.add_argument(
    "-o",
    "--output-directory",
    type=pathlib.Path,
    help="The directory to output downloads to",
    default=pathlib.Path("./data"),
)

args = argparser.parse_args()

assert args.start_year <= args.end_year

loc = shapely.from_wkt(args.location)

tilingInfo = build_tiling_info(loc, minIntersect=args.minimum_tile_intersection / 100.0)

products = []

for year in range(args.start_year, args.end_year + 1):
    for month in range(1, 13):
        if month not in args.months:
            continue

        for tile in tilingInfo:
            product, info = queryProducts(
                year,
                month,
                tile["name"],
                tile["intersection"],
                maxCloudCover=args.max_cloud_cover,
            )

            tileName = tile["name"]
            print(f"{month}/{year}, tile={tileName}: ", end="")
            if product is None:
                print("None")
            else:
                print(product["Name"], info)
                products.append((product["Id"], (year, month, tileName, product["Name"])))

resp = input(
    f"found {len(products)} products between {args.start_year} and {args.end_year} for the months {args.months}. Download size is estimated to be {len(products)}GB. Continue? [Y/N]: "
)

if len(resp.lower()) == 0 or resp.lower()[0] != "y":
    exit(0)

# --- Get Access Token via OData API ---
token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
authResp = urllib3.request(
    "POST",
    token_url,
    body=f"client_id=cdse-public&username={USERNAME}&password={PASSWORD}&grant_type=password",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)

ACCESS_TOKEN = ""
try:
    data = authResp.json()

    if "access_token" not in data:
        print("data does not have an access token!", data)
        exit(1)

    ACCESS_TOKEN = data["access_token"]
except Exception as e:
    print("could not decode auth data as json!", e)
    exit(1)

# --- Helper function: Obtain temporary S3 credentials ---
def get_temporary_s3_credentials(headers):
    s3_keys_url = "https://s3-keys-manager.dataspace.copernicus.eu/api/user/credentials"
    resp = requests.post(s3_keys_url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        print("Failed to obtain temporary S3 credentials:", resp.text)
        exit(1)

# --- Helper function: Download product from S3 and zip it ---
def download_product_from_s3(s3_resource, bucket_name, s3_prefix, target_zip):
    bucket = s3_resource.Bucket(bucket_name)
    objects = list(bucket.objects.filter(Prefix=s3_prefix))
    if not objects:
        raise FileNotFoundError(f"No objects found for prefix {s3_prefix}")

    # Create a temporary directory for the product files (based on target_zip name without .zip)
    temp_dir = target_zip.with_suffix('')
    if not temp_dir.exists():
        os.makedirs(temp_dir)

    for obj in objects:
        # Calculate local path relative to the s3_prefix
        relative_path = os.path.relpath(obj.key, s3_prefix)
        local_file = temp_dir / relative_path
        os.makedirs(local_file.parent, exist_ok=True)
        bucket.download_file(obj.key, str(local_file))

    # Zip the downloaded product folder
    with zipfile.ZipFile(str(target_zip), 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)

    # Clean up temporary directory
    shutil.rmtree(temp_dir)

# --- Obtain temporary S3 credentials ---
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Accept": "application/json"}
s3_credentials = get_temporary_s3_credentials(headers)

# Set up boto3 S3 resource with the temporary credentials
s3 = boto3.resource(
    's3',
    endpoint_url='https://eodata.dataspace.copernicus.eu',
    aws_access_key_id=s3_credentials["access_id"],
    aws_secret_access_key=s3_credentials["secret"],
    region_name='default'
)

# --- Download products from S3 ---
for i, product in enumerate(products):
    # Unpack product info
    prod_id, info = product
    year_val, month_val, tile_name, prod_name = info
    d = args.output_directory / str(year_val) / str(month_val) / str(tile_name)
    os.makedirs(d, exist_ok=True)

    # Derive S3 key prefix from product name.
    # Expected product name format: S2A_MSIL2A_YYYYMMDDTHHMMSS_Nxxxx_Rxxx_Txxxxxx_YYYYMMDDTHHMMSS.SAFE
    try:
        parts = prod_name.split('_')
        acq = parts[2]  # e.g., "20240115T235221"
        s3_year = acq[0:4]
        s3_month = acq[4:6]
        s3_day = acq[6:8]
    except Exception as e:
        print("Error parsing product name for S3 path:", prod_name, e)
        continue

    # Build the S3 prefix (folder path) based on Sentinel-2 MSI L2A structure
    s3_prefix = f"Sentinel-2/MSI/L2A/{s3_year}/{s3_month}/{s3_day}/{prod_name}/"
    target_zip = d / f"{prod_name}.zip"
    print(f"Downloading product {prod_name} from S3...")
    try:
        download_product_from_s3(s3, "eodata", s3_prefix, target_zip)
        print(f"Downloaded {i+1}/{len(products)}")
    except Exception as e:
        print(f"Failed to download {prod_name}: {e}")

# --- Delete temporary S3 credentials ---
delete_url = f"https://s3-keys-manager.dataspace.copernicus.eu/api/user/credentials/access_id/{s3_credentials['access_id']}"
delete_resp = requests.delete(delete_url, headers=headers)
if delete_resp.status_code == 204:
    print("Temporary S3 credentials deleted successfully.")
else:
    print(f"Failed to delete temporary S3 credentials. Status code: {delete_resp.status_code}")
