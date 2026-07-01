"""
===========================================================
Project 02 : Rainfall–Vegetation Relationship Analysis

Script 06 : Visualization

Author   : Shaffwan Aulia Hamidy

Description
-----------
Membuat visualisasi curah hujan dan NDVI.

Output
------
Figure_01_Rainfall.png
Figure_02_NDVI.png
Figure_03_Rainfall_vs_NDVI.png
Figure_04_Project_Dashboard.png
===========================================================
"""

# ==========================================================
# IMPORT LIBRARY
# ==========================================================

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from scipy.stats import linregress

# ==========================================================
# PROJECT FOLDER
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

figure_folder = (
    project_folder /
    "data" /
    "outputs" /
    "figures"
)

figure_folder.mkdir(parents=True, exist_ok=True)

# ==========================================================
# MEMBACA DATA
# ==========================================================

merged = pd.read_csv(
    tables_folder / "merged_chirps_ndvi.csv"
)

# Hitung regresi sekali di awal supaya bisa dipakai
# di Figure 3 maupun Figure 4 (dashboard)
slope, intercept, r, p, std = linregress(
    merged["total_mm"],
    merged["mean_ndvi"]
)

x_reg = merged["total_mm"]
y_reg = slope * x_reg + intercept

# ==========================================================
# FIGURE 1 : MONTHLY RAINFALL
# ==========================================================

plt.figure(figsize=(10, 5))

plt.plot(
    merged["month_name"],
    merged["total_mm"],
    color="royalblue",
    marker="o",
    linewidth=2.5,
    markersize=8
)

plt.title("Monthly Rainfall in Sleman (2025)")
plt.xlabel("Month")
plt.ylabel("Rainfall (mm)")

plt.xticks(rotation=45)

plt.grid(
    linestyle="--",
    alpha=0.4
)

plt.figtext(
    0.99,
    0.01,
    "Source: CHIRPS",
    ha="right",
    fontsize=8
)

plt.tight_layout()

plt.savefig(
    figure_folder /
    "Figure_01_Rainfall.png",
    dpi=600
)

plt.close()

# ==========================================================
# FIGURE 2 : MONTHLY NDVI
# ==========================================================

plt.figure(figsize=(10, 5))

plt.plot(
    merged["month_name"],
    merged["mean_ndvi"],
    color="forestgreen",
    marker="o",
    linewidth=2.5,
    markersize=8
)

plt.title("Monthly Mean NDVI in Sleman (2025)")
plt.xlabel("Month")
plt.ylabel("Mean NDVI")

plt.xticks(rotation=45)

plt.grid(
    linestyle="--",
    alpha=0.4
)

plt.figtext(
    0.99,
    0.01,
    "Source: MODIS MOD13Q1",
    ha="right",
    fontsize=8
)

plt.tight_layout()

plt.savefig(
    figure_folder /
    "Figure_02_NDVI.png",
    dpi=600
)

plt.close()

# ==========================================================
# FIGURE 3 : SCATTER PLOT
# ==========================================================

plt.figure(figsize=(7, 6))

plt.scatter(
    merged["total_mm"],
    merged["mean_ndvi"],
    s=80
)

plt.plot(
    x_reg,
    y_reg,
    color="crimson",
    linewidth=2,
    label="Regression Line"
)

plt.legend()

plt.xlabel("Monthly Rainfall (mm)")
plt.ylabel("Mean NDVI")

plt.title(
    f"Rainfall vs NDVI\n"
    f"r = {r:.2f} | "
    f"R\u00b2 = {r**2:.2f} | "
    f"p = {p:.3f}"
)

plt.grid(
    linestyle="--",
    alpha=0.4
)

plt.figtext(
    0.99,
    0.01,
    "Source: CHIRPS & MODIS MOD13Q1",
    ha="right",
    fontsize=8
)

plt.tight_layout()

plt.savefig(
    figure_folder /
    "Figure_03_Rainfall_vs_NDVI.png",
    dpi=600
)

plt.close()

# ==========================================================
# FIGURE 4 : PROJECT DASHBOARD
# ==========================================================
# Gabungan Figure 1 + 2 + 3 dalam satu gambar.
# Ditujukan agar README GitHub cukup menampilkan
# satu gambar untuk merepresentasikan seluruh proyek.

fig, axes = plt.subplots(
    nrows=3,
    ncols=1,
    figsize=(10, 14)
)

# --- Panel A : Rainfall ---
axes[0].plot(
    merged["month_name"],
    merged["total_mm"],
    color="royalblue",
    marker="o",
    linewidth=2.5,
    markersize=8
)
axes[0].set_title("A. Monthly Rainfall in Sleman (2025)")
axes[0].set_xlabel("Month")
axes[0].set_ylabel("Rainfall (mm)")
axes[0].tick_params(axis="x", rotation=45)
axes[0].grid(linestyle="--", alpha=0.4)

# --- Panel B : NDVI ---
axes[1].plot(
    merged["month_name"],
    merged["mean_ndvi"],
    color="forestgreen",
    marker="o",
    linewidth=2.5,
    markersize=8
)
axes[1].set_title("B. Monthly Mean NDVI in Sleman (2025)")
axes[1].set_xlabel("Month")
axes[1].set_ylabel("Mean NDVI")
axes[1].tick_params(axis="x", rotation=45)
axes[1].grid(linestyle="--", alpha=0.4)

# --- Panel C : Scatter + Regression ---
axes[2].scatter(
    merged["total_mm"],
    merged["mean_ndvi"],
    s=80
)
axes[2].plot(
    x_reg,
    y_reg,
    color="crimson",
    linewidth=2,
    label="Regression Line"
)
axes[2].legend()
axes[2].set_title(
    f"C. Rainfall vs NDVI "
    f"(r = {r:.2f} | R\u00b2 = {r**2:.2f} | p = {p:.3f})"
)
axes[2].set_xlabel("Monthly Rainfall (mm)")
axes[2].set_ylabel("Mean NDVI")
axes[2].grid(linestyle="--", alpha=0.4)

fig.suptitle(
    "Rainfall–Vegetation Relationship Analysis — Sleman 2025",
    fontsize=14,
    fontweight="bold"
)

plt.figtext(
    0.99,
    0.005,
    "Source: CHIRPS & MODIS MOD13Q1",
    ha="right",
    fontsize=8
)

plt.tight_layout(rect=[0, 0, 1, 0.97])

plt.savefig(
    figure_folder /
    "Figure_04_Project_Dashboard.png",
    dpi=600
)

plt.close()

# ==========================================================
# FINISH
# ==========================================================

print("="*50)

print("SEMUA GRAFIK BERHASIL DIBUAT")

print("="*50)

print()

print(figure_folder)