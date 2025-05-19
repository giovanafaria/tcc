# src/utils/obstacle_mask.py
import numpy as np, geopandas as gpd
from rasterio.transform import Affine
import rasterio

GRID_W, GRID_H = 220, 180           # same as model

def build_mask(shp, transform):
    mask = np.zeros((GRID_H, GRID_W), dtype=bool)
    gdf  = gpd.read_file(shp)

    inv = ~transform                 # metres  ➜  (col,row)

    for geom in gdf.geometry:
        # bounding box in grid coordinates → iterate only necessary cells
        minx, miny, maxx, maxy = geom.bounds
        c0, r0 = map(int, inv * (minx, maxy))      # top-left
        c1, r1 = map(int, inv * (maxx, miny))      # bottom-right
        c0 = max(c0, 0); r0 = max(r0, 0)
        c1 = min(c1, GRID_W-1); r1 = min(r1, GRID_H-1)

        for row in range(r0, r1+1):
            for col in range(c0, c1+1):
                # centre of that cell in map coordinates
                x, y = transform * (col + 0.5, row + 0.5)
                if geom.contains(gpd.points_from_xy([x], [y])[0]):
                    mask[row, col] = True
    return mask


if __name__ == "__main__":
    print("building obstacle_mask.npy …")
    with rasterio.open("data/raw/satellite_georeferenced.tif") as src:

        bounds = src.bounds  # bounding box in map coordinates
        width_m  = bounds.right - bounds.left
        height_m = bounds.top - bounds.bottom

        cell_width  = width_m / GRID_W
        cell_height = height_m / GRID_H

        transform = Affine.translation(bounds.left, bounds.top) * Affine.scale(cell_width, -cell_height)

    m = build_mask("data/raw/corte_edificacoes.shp", transform)
    np.save("data/processed/obstacle_mask.npy", m)
    print("saved to data/processed/obstacle_mask.npy")
