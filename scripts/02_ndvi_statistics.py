"""
===========================================================
Project 02 : Rainfall–Vegetation Relationship Analysis

Script 02 : NDVI Statistics

Author   : Shaffwan Aulia Hamidy
Software : Python (Spyder)

Description
-----------
Menghitung statistik NDVI dari seluruh raster MODIS
tahun 2025 berdasarkan dataset_inventory.csv.

Output
------
ndvi_statistics.csv
===========================================================
"""

from pathlib import Path
import rasterio
import numpy as np
import pandas as pd

# ==========================================================
# KONSTANTA
# ==========================================================

SCALE_FACTOR = 0.0001

# ==========================================================
# FOLDER PROJECT
# ==========================================================

project_folder = Path(
    r"D:\Dummy Project\Rainfall–Vegetation_relationship"
)

inventory_file = (
    project_folder /
    "data" /
    "outputs" /
    "tables" /
    "dataset_inventory.csv"
)

raw_folder = (
    project_folder /
    "data" /
    "raw" /
    "ndvi" /
    "extracted"
)

output_folder = (
    project_folder /
    "data" /
    "outputs" /
    "tables"
)

output_folder.mkdir(parents=True, exist_ok=True)

# ==========================================================
# MEMBACA DATASET INVENTORY
# ==========================================================

inventory = pd.read_csv(inventory_file)

print("=" * 50)
print("NDVI STATISTICS")
print("=" * 50)
print(f"Raster yang akan diproses : {len(inventory)}")
print()

# ==========================================================
# PROSES STATISTIK
# ==========================================================

results = []

for i, (_, row) in enumerate(inventory.iterrows(), start=1):

    raster_path = raw_folder / row["filename"]

    with rasterio.open(raster_path) as src:

        ndvi = src.read(1).astype(np.float32)

        # Menghapus NoData
        ndvi[ndvi == src.nodata] = np.nan

        # Scale Factor MODIS
        ndvi *= SCALE_FACTOR

        results.append({

            "filename": row["filename"],
            "date": row["date"],
            "mean_ndvi": np.nanmean(ndvi),
            "min_ndvi": np.nanmin(ndvi),
            "max_ndvi": np.nanmax(ndvi),
            "std_ndvi": np.nanstd(ndvi)

        })

    print(f"[{i:02d}/{len(inventory)}] {row['date']} ✓")

# ==========================================================
# MEMBUAT DATAFRAME
# ==========================================================

ndvi_stats = pd.DataFrame(results)

ndvi_stats = ndvi_stats.round({
    "mean_ndvi": 4,
    "min_ndvi": 4,
    "max_ndvi": 4,
    "std_ndvi": 4
})

# ==========================================================
# SIMPAN CSV
# ==========================================================

output_file = output_folder / "ndvi_statistics.csv"

ndvi_stats.to_csv(output_file, index=False)

# ==========================================================
# SUMMARY
# ==========================================================

print()
print("=" * 50)
print("PROSES SELESAI")
print("=" * 50)

print(f"Jumlah raster diproses : {len(ndvi_stats)}")
print(f"Output                 : {output_file}")

print()
print("Preview hasil:")

print(ndvi_stats.head())

print("=" * 50)