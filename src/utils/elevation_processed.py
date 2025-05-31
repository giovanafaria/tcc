import rasterio
import numpy as np

# Path to your raster
with rasterio.open("data/raw/raster_elevacao.tif") as src:
    elevation = src.read(1)  # read the first band

np.save("data/processed/elevation.npy", elevation)