"""
===========================================================
Project 02 : Rainfall–Vegetation Relationship Analysis

Script 01 : Dataset Inventory

Author   : Shaffwan Aulia Hamidy
Software : Python (Spyder)
Dataset  : MODIS MOD13Q1 Version 6.1
===========================================================
"""

from pathlib import Path
import re
import pandas as pd
from datetime import datetime, timedelta


# ==========================
# Folder dataset NDVI
# ==========================

ndvi_folder = Path(
    r"D:\Dummy Project\Rainfall–Vegetation_relationship\data\raw\ndvi\extracted"
)

# ==========================
# Membaca seluruh file TIFF
# ==========================

tif_files = sorted(ndvi_folder.glob("*.tif"))

print(f"Jumlah raster ditemukan : {len(tif_files)}")

print("\nDaftar file:\n")

valid_files = []

for i, file in enumerate(tif_files, start=1):

    # Mencari pola doyYYYYDDD
    match = re.search(r"doy(\d{4})(\d{3})", file.name)

    if match:

        year = int(match.group(1))
        doy = int(match.group(2))

        print(f"{i:02d}. {file.name}")
        print(f"     Tahun : {year}")
        print(f"     DOY   : {doy}")

        # Hanya menyimpan raster tahun 2025
    if year == 2025:

        # Mengubah DOY menjadi tanggal kalender
        date = datetime(year, 1, 1) + timedelta(days=doy - 1)

        print(f"     Tanggal : {date.strftime('%Y-%m-%d')}")

        valid_files.append({
            "filename": file.name,
            "year": year,
            "doy": doy,
            "date": date
        })
# ==========================
# Membuat DataFrame
# ==========================

inventory = pd.DataFrame(valid_files)

# Mengurutkan berdasarkan tanggal
inventory = inventory.sort_values("date")

# Menambahkan nomor urut
inventory.insert(0, "No", range(1, len(inventory) + 1))

# Format tanggal
inventory["date"] = inventory["date"].dt.strftime("%Y-%m-%d")

# Folder output
output_folder = Path(
    r"D:\Dummy Project\Rainfall–Vegetation_relationship\data\outputs\tables"
)

output_folder.mkdir(parents=True, exist_ok=True)

output_file = output_folder / "dataset_inventory.csv"

inventory.to_csv(output_file, index=False)

print("\nDataset inventory berhasil disimpan!")
print(output_file)