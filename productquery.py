import pprint
import shapely
import urllib3
import heapq
import json

http = urllib3.PoolManager()

def queryProducts(
    year: int,
    month: int,
    day: int,
    tile: str,
    shape: shapely.Polygon,
    maxCloudCover=20,
    minIntersection: float = 0.8,
):
    assert month >= 1 and month <= 12

    DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    if day is not None:
        start_date = f"{year}-{month:02}-{day:02}T00:00:00.000Z"
        print(start_date)
        print("\n")
        print("\n")
        end_date = f"{year}-{month:02}-{day:02}T23:59:59.999Z"
        # Use inclusive operators for a single day query
        date_filter = f"ContentDate/Start ge {start_date} and ContentDate/Start le {end_date}"
    else:
        start_date = f"{year}-{month:02}-01T00:00:00.000Z"

        print(start_date)
        print("\n")
        print("\n")

        end_date = f"{year}-{month:02}-{DAYS_IN_MONTH[month - 1]}T00:00:00.000Z"
        # Retain the original strict operators for full-month queries
        date_filter = f"ContentDate/Start gt {start_date} and ContentDate/Start lt {end_date}"

    queryURL = (
        f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?"
        f"$filter=Collection/Name eq 'SENTINEL-2' and "
        f"{date_filter} and "
        f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'tileId' and "
        f"att/OData.CSC.StringAttribute/Value eq '{tile}') and "
        f"contains(Name,'L2A') and "
        f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and "
        f"att/OData.CSC.DoubleAttribute/Value le {maxCloudCover})&"
        f"$top=1000&$expand=Attributes"
    )

    response = http.request("GET", queryURL, timeout=30)
    data = json.loads(response.data.decode('utf-8'))

    candidate = None
    candidateScore = None
    candidateInfo = None
    if "value" not in data:
        pprint.pp(data)
        return None

    for val in data["value"]:
        geom = shapely.from_wkt(val["Footprint"].split(";")[1])
        percentIntersect = shape.intersection(geom).area / shape.area

        if percentIntersect >= minIntersection:
            cloudCover = None
            for attribute in val["Attributes"]:
                if attribute["Name"] == "cloudCover":
                    cloudCover = float(attribute["Value"])
                    break

            if cloudCover is not None and cloudCover <= maxCloudCover:
                score = (1.0 - (cloudCover / 100)) * percentIntersect
                if candidateScore is None or candidateScore < score:
                    candidate = val
                    candidateScore = score
                    candidateInfo = {
                        "score": score,
                        "cloudCover": cloudCover,
                        "percentIntersect": percentIntersect,
                    }

    return candidate, candidateInfo

