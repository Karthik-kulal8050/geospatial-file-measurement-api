import geopandas as gpd
import zipfile
from pathlib import Path
from shapely.affinity import translate

gdf = gpd.read_file("sample.kml")

# Get the polygon from the KML
polygon = gdf[gdf.geometry.geom_type == "Polygon"].iloc[0].geometry

# Create 3 polygon features
polygon_gdf = gpd.GeoDataFrame(
    {
        "name": ["Area 1", "Area 2", "Area 3"]
    },
    geometry=[
        polygon,
        translate(polygon, xoff=0.01, yoff=0),
        translate(polygon, xoff=0, yoff=0.01),
    ],
    crs=gdf.crs
)

output_dir = Path("test_shapefile")

# Remove old Shapefile files
if output_dir.exists():
    for file in output_dir.iterdir():
        file.unlink()
else:
    output_dir.mkdir()

shapefile_path = output_dir / "sample.shp"

polygon_gdf.to_file(
    shapefile_path,
    driver="ESRI Shapefile"
)

# Create ZIP
zip_path = Path("sample_shapefile.zip")

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    for file in output_dir.iterdir():
        zipf.write(file, arcname=file.name)

print("3-feature Shapefile created successfully.")
print(f"ZIP created: {zip_path}")