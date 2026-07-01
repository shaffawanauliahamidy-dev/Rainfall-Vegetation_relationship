"""
===========================================================
Project 02 : Rainfall–Vegetation Relationship Analysis

Script 05 : Correlation Analysis

Author   : Shaffwan Aulia Hamidy

Description
-----------
Analisis hubungan antara curah hujan dan NDVI.

Output
------
correlation_results.txt
===========================================================
"""

from pathlib import Path
import pandas as pd

from scipy.stats import pearsonr
from scipy.stats import linregress

project_folder = Path(
    r"D:\Dummy Project\Rainfall–Vegetation_relationship"
)

tables_folder = (
    project_folder /
    "data" /
    "outputs" /
    "tables"
)

input_file = tables_folder / "merged_chirps_ndvi.csv"

merged = pd.read_csv(input_file)

print(merged.head())

project_folder = Path(
    r"D:\Dummy Project\Rainfall–Vegetation_relationship"
)

tables_folder = (
    project_folder /
    "data" /
    "outputs" /
    "tables"
)

input_file = tables_folder / "merged_chirps_ndvi.csv"

merged = pd.read_csv(input_file)

print(merged.head())

rainfall = merged["total_mm"]

ndvi = merged["mean_ndvi"]

r, p = pearsonr(rainfall, ndvi)

print()

print("="*50)

print("PEARSON CORRELATION")

print("="*50)

print(f"Correlation (r) : {r:.4f}")

print(f"P-value         : {p:.4f}")

slope, intercept, r_value, p_value, std_err = linregress(
    rainfall,
    ndvi
)

print()

print("="*50)

print("LINEAR REGRESSION")

print("="*50)

print(f"Slope      : {slope:.6f}")

print(f"Intercept  : {intercept:.4f}")

print(f"R²         : {r_value**2:.4f}")

print()

print("="*50)

print("INTERPRETATION")

print("="*50)

if abs(r) < 0.2:
    strength = "Very Weak"

elif abs(r) < 0.4:
    strength = "Weak"

elif abs(r) < 0.6:
    strength = "Moderate"

elif abs(r) < 0.8:
    strength = "Strong"

else:
    strength = "Very Strong"

direction = "Positive" if r > 0 else "Negative"

print(f"Relationship : {strength} {direction}")

if p < 0.05:
    print("Statistically Significant")

else:
    print("Not Statistically Significant")