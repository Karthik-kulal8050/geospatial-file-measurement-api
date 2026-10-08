from typing import Any

import geopandas as gpd


def calculate_measurements(
    gdf: gpd.GeoDataFrame,
) -> list[dict[str, Any]]:

    results = []

    for index, row in gdf.iterrows():

        geometry = row.geometry
        geometry_type = geometry.geom_type

        result = {
            "feature_id": index,
            "geometry_type": geometry_type,
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