# src/utils/landslide_masks.py
import numpy as np
import geopandas as gpd
from rasterio.transform import Affine
import rasterio

GRID_W, GRID_H = 220, 180

def build_mask(shp, transform):
    mask = np.zeros((GRID_H, GRID_W), dtype=bool)
    gdf  = gpd.read_file(shp)
    inv = ~transform
    for geom in gdf.geometry:
        minx, miny, maxx, maxy = geom.bounds
        c0, r0 = map(int, inv * (minx, maxy))
        c1, r1 = map(int, inv * (maxx, miny))
        c0, r0 = max(c0, 0), max(r0, 0)
        c1, r1 = min(c1, GRID_W-1), min(r1, GRID_H-1)
        for row in range(r0, r1+1):
            for col in range(c0, c1+1):
                x, y = transform * (col+0.5, row+0.5)
                if geom.contains(gpd.points_from_xy([x],[y])[0]):
                    mask[row, col] = True
    return mask

if __name__ == "__main__":
    with rasterio.open("data/raw/satellite_georeferenced.tif") as src:
        b = src.bounds
        cw, ch = (b.right - b.left)/GRID_W, (b.top - b.bottom)/GRID_H
        transform = Affine.translation(b.left, b.top) * Affine.scale(cw, -ch)

    shapefiles = [
        "data/raw/area_risco1.shp",
        "data/raw/area_risco2.shp",
        "data/raw/area_risco3.shp",
    ]
    for i, shp in enumerate(shapefiles, start=1):
        m = build_mask(shp, transform)
        np.save(f"data/processed/landslide_mask_{i}.npy", m)
        print(f"wrote data/processed/landslide_mask_{i}.npy")
