"""
===========================================================
Project 02 : Rainfall–Vegetation Relationship Analysis

Script 03 : Monthly NDVI Statistics

Author   : Shaffwan Aulia Hamidy

Description
-----------
Mengubah statistik NDVI 16-harian menjadi statistik bulanan.

Output
------
monthly_ndvi.csv
===========================================================
"""

from pathlib import Path
import pandas as pd

project_folder = Path(
    r"D:\Dummy Project\Rainfall–Vegetation_relationship"
)

input_file = (
    project_folder /
    "data" /
    "outputs" /
    "tables" /
    "ndvi_statistics.csv"
)

output_file = (
    project_folder /
    "data" /
    "outputs" /
    "tables" /
    "monthly_ndvi.csv"
)
ndvi = pd.read_csv(input_file)

# ==========================================================
# KONVERSI TIPE TANGGAL
# ==========================================================

ndvi["date"] = pd.to_datetime(ndvi["date"])

ndvi["year"] = ndvi["date"].dt.year
ndvi["month"] = ndvi["date"].dt.month
ndvi["month_name"] = ndvi["date"].dt.month_name()

# ==========================================================
# STATISTIK BULANAN
# ==========================================================

monthly_ndvi = (
    ndvi
    .groupby(["year", "month", "month_name"], as_index=False)
    .agg(
        mean_ndvi=("mean_ndvi", "mean"),
        max_ndvi=("mean_ndvi", "max"),
        min_ndvi=("mean_ndvi", "min"),
        std_ndvi=("mean_ndvi", "std"),
        observation=("mean_ndvi", "count")
    )
)
monthly_ndvi["std_ndvi"] = monthly_ndvi["std_ndvi"].fillna(0)
monthly_ndvi = monthly_ndvi.round({
    "mean_ndvi":4,
    "max_ndvi":4,
    "min_ndvi":4,
    "std_ndvi":4
})

monthly_ndvi.to_csv(output_file, index=False)

print()
print("="*50)
print("MONTHLY NDVI BERHASIL DIBUAT")
print("="*50)

print(monthly_ndvi)