"""
===========================================================
Project 02 : Rainfall–Vegetation Relationship Analysis

Script 04 : Merge CHIRPS and NDVI

Author   : Shaffwan Aulia Hamidy

Description
-----------
Menggabungkan data curah hujan CHIRPS dengan
statistik NDVI bulanan.

Output
------
merged_chirps_ndvi.csv
===========================================================
"""

from pathlib import Path
import pandas as pd

# ==========================================================
# FOLDER PROJECT
# ==========================================================

project_folder = Path(
    r"D:\Dummy Project\Rainfall–Vegetation_relationship"
)

tables_folder = (
    project_folder /
    "data" /
    "outputs" /
    "tables"
)

chirps_file = tables_folder / "monthly_summary_sleman_2025.csv"

ndvi_file = tables_folder / "monthly_ndvi.csv"

output_file = tables_folder / "merged_chirps_ndvi.csv"

# ==========================================================
# MEMBACA DATA
# ==========================================================

chirps = pd.read_csv(chirps_file)

ndvi = pd.read_csv(ndvi_file)

print("CHIRPS :", len(chirps), "baris")
print("NDVI   :", len(ndvi), "baris")

# ==========================================================
# MERGE
# ==========================================================

merged = pd.merge(
    chirps,
    ndvi,
    on=["year", "month", "month_name"],
    how="inner"
)

# ==========================================================
# SIMPAN
# ==========================================================

merged.to_csv(output_file, index=False)

print()
print("=" * 50)
print("MERGE BERHASIL")
print("=" * 50)

print(f"Jumlah data : {len(merged)}")

print()
print(merged.head())