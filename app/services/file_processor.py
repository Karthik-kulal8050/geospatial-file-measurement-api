import zipfile
from pathlib import Path

import geopandas as gpd


def read_geospatial_file(file_path: str) -> gpd.GeoDataFrame:
    """
    Read a KML file or a ZIP containing a Shapefile.
    """

    path = Path(file_path)

    if path.suffix.lower() == ".kml":
        gdf = gpd.read_file(path)

    elif path.suffix.lower() == ".zip":
        gdf = read_shapefile_zip(path)

    else:
        raise ValueError("Unsupported file format.")

    if gdf.empty:
        raise ValueError("The uploaded file contains no features.")

    return gdf


def read_shapefile_zip(zip_path: Path) -> gpd.GeoDataFrame:
    """
    Safely extract a ZIP containing a Shapefile
    and read the .shp file.
    """

    extract_dir = zip_path.parent / zip_path.stem

    extract_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for member in zip_ref.infolist():
                member_path = extract_dir / member.filename

                if not member_path.resolve().is_relative_to(
                    extract_dir.resolve()
                ):
                    raise ValueError("ZIP file contains an unsafe path.")

            zip_ref.extractall(extract_dir)

    except zipfile.BadZipFile:
        raise ValueError(
            "The uploaded ZIP file is invalid or corrupted."
        )

    shapefiles = list(extract_dir.rglob("*.shp"))

    if not shapefiles:
        raise ValueError(
            "ZIP file does not contain a Shapefile."
        )

    if len(shapefiles) > 1:
        raise ValueError(
            "ZIP file contains multiple Shapefiles."
        )

    return gpd.read_file(shapefiles[0])


def prepare_projected_gdf(
    gdf: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, str]:

    if gdf.crs is None:
        raise ValueError(
            "The uploaded file does not contain a CRS."
        )

    original_crs = str(gdf.crs)

    if gdf.crs.is_geographic:

        projected_crs = gdf.estimate_utm_crs()

        if projected_crs is None:
            raise ValueError(
                "Could not determine a suitable projected CRS."
            )

        gdf = gdf.to_crs(projected_crs)

    return gdf, original_crs