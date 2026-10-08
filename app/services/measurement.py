import json
from typing import Any
import geopandas as gpd


def calculate_measurements(
    gdf: gpd.GeoDataFrame,
) -> list[dict[str, Any]]:

    results = []

    for index, row in gdf.iterrows():

        geometry = row.geometry
        geometry_type = geometry.geom_type

        # Convert geometry to GeoJSON-style dictionary
        geometry_data = geometry.__geo_interface__

        # Extract feature properties/attributes
        properties = {
            str(key): value
            for key, value in row.drop(labels="geometry").items()
        }

        result = {
            "feature_id": int(index),
            "geometry_type": geometry_type,
            "geometry": geometry_data,
            "properties": properties,
            "measurement": None,
            "unit": None,
            "status": "NOT_REQUIRED",
        }

        if geometry_type == "Polygon":
            result["measurement"] = geometry.area
            result["unit"] = "m²"
            result["status"] = "COMPLETED"

        elif geometry_type == "LineString":
            result["measurement"] = geometry.length
            result["unit"] = "m"
            result["status"] = "COMPLETED"

        elif geometry_type == "Point":
            result["status"] = "NOT_REQUIRED"

        else:
            result["status"] = "UNSUPPORTED"

        results.append(result)

    return results