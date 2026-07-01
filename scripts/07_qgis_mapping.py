# =============================================================================
# Script 07 - Pembuatan Peta Mean NDVI, Total Rainfall, dan Peta Komparasi
# Project  : Rainfall–Vegetation Relationship Analysis - Kab. Sleman 2025
#
# Revisi v2: peta sekarang merepresentasikan agregat TAHUNAN (bukan satu bulan
#            acak), perbandingan apple-to-apple (periode sama), dan
#            menampilkan ringkasan korelasi (r, R², p) dari merged_chirps_ndvi.csv
#
# Cara run : QGIS 3.x -> Plugins -> Python Console -> Show Editor
#            -> Open Script -> pilih file ini -> Run Script
# =============================================================================

import os
import re
import csv
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

from qgis.core import (
    QgsProject, QgsRasterLayer, QgsVectorLayer,
    QgsSingleBandPseudoColorRenderer,
    QgsColorRampShader, QgsRasterShader,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutItemScaleBar, QgsLayoutItemLegend, QgsLayoutItemShape,
    QgsLayoutSize, QgsLayoutPoint, QgsUnitTypes,
    QgsLayoutExporter, QgsRectangle, QgsLegendStyle,
    QgsRasterFileWriter, QgsRasterPipe
)
from qgis.PyQt.QtCore import Qt, QRectF
from qgis.PyQt.QtGui import QColor, QFont

# =============================================================================
# 1. KONFIGURASI PATH
# =============================================================================

PROJECT_DIR   = r"D:\Dummy Project\Rainfall–Vegetation_relationship"
RAW_DIR       = os.path.join(PROJECT_DIR, "data", "raw")
BOUNDARY_SHP  = os.path.join(RAW_DIR, "boundary", "Sleman.shp")
NDVI_DIR      = os.path.join(RAW_DIR, "ndvi", "extracted")
CHIRPS_DIR    = os.path.join(RAW_DIR, "chirps", "clipped_raster")
TABLES_DIR    = os.path.join(PROJECT_DIR, "data", "outputs", "tables")
MAPS_DIR      = os.path.join(PROJECT_DIR, "data", "outputs", "maps")
TEMP_DIR      = os.path.join(PROJECT_DIR, "data", "outputs", "_temp_rasters")

os.makedirs(MAPS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

MERGED_CSV = os.path.join(TABLES_DIR, "merged_chirps_ndvi.csv")

# Bulan yang dipakai untuk Figure_07 (apple-to-apple comparison)
COMPARISON_MONTH = 1   # Januari — bisa diganti 6 (Juni) atau 12 (Desember)

SLEMAN_AREA_KM2 = 574  # Luas administratif Kab. Sleman (referensi umum)

# =============================================================================
# 2. FUNGSI HELPER - TANGGAL
# =============================================================================

def doy_to_date(year, doy):
    return datetime(year, 1, 1) + timedelta(days=int(doy) - 1)


def list_ndvi_files(ndvi_dir, year=2025):
    """Daftar semua file NDVI MOD13Q1 tahun tertentu beserta tanggalnya."""
    pattern = re.compile(r"doy(\d{4})(\d{3})")
    result = []
    for f in os.listdir(ndvi_dir):
        if not f.lower().endswith(".tif"):
            continue
        m = pattern.search(f)
        if not m:
            continue
        y, doy = int(m.group(1)), int(m.group(2))
        date = doy_to_date(y, doy)
        if date.year == year:
            result.append((date, os.path.join(ndvi_dir, f)))
    return sorted(result, key=lambda x: x[0])


def find_ndvi_for_month(ndvi_dir, target_month, target_year=2025):
    """Cari file NDVI dengan tanggal terdekat ke pertengahan bulan target."""
    candidates = list_ndvi_files(ndvi_dir, target_year)
    if not candidates:
        return None
    target_date = datetime(target_year, target_month, 15)
    best = min(candidates, key=lambda c: abs((c[0] - target_date).days))
    return best[1], best[0]


def find_chirps_for_month(chirps_dir, month, year=2025):
    files = []
    for f in sorted(os.listdir(chirps_dir)):
        if f.endswith(".tif") and f"{year}.{month:02d}." in f:
            files.append(os.path.join(chirps_dir, f))
    return files


def list_chirps_all(chirps_dir, year=2025):
    files = []
    for f in sorted(os.listdir(chirps_dir)):
        if f.endswith(".tif") and str(year) in f:
            files.append(os.path.join(chirps_dir, f))
    return files

# =============================================================================
# 3. FUNGSI HELPER - AGREGASI RASTER (NUMPY) -> TULIS GEOTIFF BARU
# =============================================================================

def read_raster_array(path):
    """Baca band 1 raster sebagai numpy array float, NoData -> NaN."""
    lyr = QgsRasterLayer(path, "tmp")
    if not lyr.isValid():
        return None, None
    provider = lyr.dataProvider()
    w, h = lyr.width(), lyr.height()
    block = provider.block(1, lyr.extent(), w, h)
    arr = np.array(
        [[block.value(r, c) for c in range(w)] for r in range(h)],
        dtype=float
    )
    nodata = provider.sourceNoDataValue(1)
    if nodata is not None:
        arr[arr == nodata] = np.nan
    return arr, lyr


def write_array_as_geotiff(template_path, array, output_path):
    """
    Tulis ulang sebuah array numpy ke GeoTIFF baru memakai georeferensi
    dari template_path (raster contoh yang sudah benar extent/crs-nya).
    """
    template_lyr = QgsRasterLayer(template_path, "template")
    provider = template_lyr.dataProvider()

    writer = QgsRasterFileWriter(output_path)
    writer.setOutputFormat("GTiff")

    w, h = template_lyr.width(), template_lyr.height()
    extent = template_lyr.extent()
    crs = template_lyr.crs()

    # Gunakan GDAL langsung lewat osgeo jika tersedia, fallback ke metode provider
    try:
        from osgeo import gdal, osr
        driver = gdal.GetDriverByName("GTiff")
        out_ds = driver.Create(output_path, w, h, 1, gdal.GDT_Float32)

        gt = (extent.xMinimum(), extent.width()/w, 0,
              extent.yMaximum(), 0, -extent.height()/h)
        out_ds.SetGeoTransform(gt)

        srs = osr.SpatialReference()
        srs.ImportFromWkt(crs.toWkt())
        out_ds.SetProjection(srs.ExportToWkt())

        band = out_ds.GetRasterBand(1)
        nan_mask = np.isnan(array)
        out_array = np.where(nan_mask, -9999, array).astype(np.float32)
        band.WriteArray(out_array)
        band.SetNoDataValue(-9999)
        band.FlushCache()
        out_ds = None
        return True
    except ImportError:
        print("  [WARNING] Modul osgeo/gdal tidak tersedia di Python QGIS environment ini.")
        print("  Menggunakan layer pertama sebagai representasi visual (fallback).")
        return False


def build_mean_raster(file_list, output_path, label="raster"):
    """Hitung rata-rata piksel dari sekumpulan raster, tulis ke output_path."""
    print(f"  Menghitung rata-rata {len(file_list)} raster ({label})...")
    arrays = []
    template = file_list[0]
    for f in file_list:
        arr, _ = read_raster_array(f)
        if arr is not None:
            arrays.append(arr)
    if not arrays:
        return None
    mean_arr = np.nanmean(np.stack(arrays, axis=0), axis=0)
    ok = write_array_as_geotiff(template, mean_arr, output_path)
    return output_path if ok else template  # fallback: pakai raster pertama


def build_sum_raster(file_list, output_path, label="raster"):
    """Hitung total (sum) piksel dari sekumpulan raster, tulis ke output_path."""
    print(f"  Menghitung total {len(file_list)} raster ({label})...")
    arrays = []
    template = file_list[0]
    for f in file_list:
        arr, _ = read_raster_array(f)
        if arr is not None:
            arrays.append(arr)
    if not arrays:
        return None
    sum_arr = np.nansum(np.stack(arrays, axis=0), axis=0)
    ok = write_array_as_geotiff(template, sum_arr, output_path)
    return output_path if ok else template

# =============================================================================
# 4. FUNGSI HELPER - BACA KORELASI DARI CSV / HITUNG ULANG
# =============================================================================

def get_correlation_stats(csv_path):
    """
    Baca merged_chirps_ndvi.csv lalu hitung Pearson r, R^2, p-value
    antara total_mm dan mean_ndvi (tanpa scipy, pakai numpy murni
    supaya tidak bergantung pada library tambahan di Python QGIS).
    """
    if not os.path.exists(csv_path):
        return None

    rainfall, ndvi = [], []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rainfall.append(float(row["total_mm"]))
                ndvi.append(float(row["mean_ndvi"]))
            except (KeyError, ValueError):
                continue

    if len(rainfall) < 3:
        return None

    x = np.array(rainfall)
    y = np.array(ndvi)
    n = len(x)

    r = np.corrcoef(x, y)[0, 1]
    r2 = r ** 2

    # p-value via t-distribution approksimasi (two-tailed)
    if abs(r) >= 1.0:
        p = 0.0
    else:
        t_stat = r * np.sqrt((n - 2) / (1 - r2))
        # Pendekatan p-value memakai survival function distribusi normal
        # (cukup akurat untuk n > 10; dipakai agar tak perlu scipy)
        from math import erf, sqrt
        p = 2 * (1 - 0.5 * (1 + erf(abs(t_stat) / sqrt(2))))

    return {"n": n, "r": r, "r2": r2, "p": p}

# =============================================================================
# 5. FUNGSI HELPER - RENDERER WARNA
# =============================================================================

def build_renderer_ndvi(layer):
    items = [
        QgsColorRampShader.ColorRampItem(-0.2, QColor("#a50026"), "< 0 (Non-veg/Air)"),
        QgsColorRampShader.ColorRampItem(0.0,  QColor("#d73027"), "0.0"),
        QgsColorRampShader.ColorRampItem(0.2,  QColor("#fee08b"), "0.2"),
        QgsColorRampShader.ColorRampItem(0.4,  QColor("#d9ef8b"), "0.4"),
        QgsColorRampShader.ColorRampItem(0.6,  QColor("#66bd63"), "0.6"),
        QgsColorRampShader.ColorRampItem(0.8,  QColor("#1a9850"), "0.8"),
        QgsColorRampShader.ColorRampItem(1.0,  QColor("#006837"), "1.0 (Veg. Lebat)"),
    ]
    ramp = QgsColorRampShader()
    ramp.setColorRampType(QgsColorRampShader.Interpolated)
    ramp.setColorRampItemList(items)
    shader = QgsRasterShader()
    shader.setRasterShaderFunction(ramp)
    return QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)


def build_renderer_chirps(layer, raster_path):
    """
    Renderer warna biru untuk curah hujan.
    Nilai maksimum legenda mengikuti nilai aktual raster yang dipetakan
    (bukan angka tetap), sesuai review: legenda harus representatif.
    """
    arr, _ = read_raster_array(raster_path)
    if arr is not None and np.any(~np.isnan(arr)):
        actual_max = float(np.nanmax(arr))
    else:
        actual_max = 150.0
    # Bulatkan ke kelipatan 10 terdekat ke atas, minimal 20
    max_val = max(20, int(np.ceil(actual_max / 10.0) * 10))

    stops = [0, max_val*0.1, max_val*0.3, max_val*0.6, max_val]
    colors = ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"]
    items = [
        QgsColorRampShader.ColorRampItem(stops[i], QColor(colors[i]), f"{stops[i]:.0f} mm")
        for i in range(len(stops))
    ]
    ramp = QgsColorRampShader()
    ramp.setColorRampType(QgsColorRampShader.Interpolated)
    ramp.setColorRampItemList(items)
    shader = QgsRasterShader()
    shader.setRasterShaderFunction(ramp)
    return QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader), max_val

# =============================================================================
# 6. FUNGSI HELPER - LAYOUT & EXPORT
# =============================================================================

def export_layout_as_png(layout, output_path, dpi=200):
    exporter = QgsLayoutExporter(layout)
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = dpi
    result = exporter.exportToImage(output_path, settings)
    if result == QgsLayoutExporter.Success:
        print(f"  ✓ Tersimpan: {output_path}")
    else:
        print(f"  ✗ Gagal export: {output_path}")


def style_boundary(layer):
    sym = layer.renderer().symbol()
    sym.setColor(QColor(0, 0, 0, 0))
    sym.symbolLayer(0).setStrokeColor(QColor("#2c3e50"))
    sym.symbolLayer(0).setStrokeWidth(0.6)
    layer.triggerRepaint()


def get_padded_extent(boundary_layer, pad_ratio=0.2):
    extent = boundary_layer.extent()
    pad_x = extent.width()  * pad_ratio
    pad_y = extent.height() * pad_ratio
    return QgsRectangle(
        extent.xMinimum() - pad_x, extent.yMinimum() - pad_y,
        extent.xMaximum() + pad_x, extent.yMaximum() + pad_y
    )


def add_north_arrow(layout, x=265, y=30, size=12):
    arrow = QgsLayoutItemLabel(layout)
    arrow.setText("N\n\u25B2")
    arrow.setFont(QFont("Arial", size, QFont.Bold))
    arrow.setHAlign(Qt.AlignHCenter)
    arrow.attemptSetSceneRect(QRectF(x, y, 20, 20))
    layout.addLayoutItem(arrow)


def add_legend(layout, map_item, title, x, y, w, h):
    legend = QgsLayoutItemLegend(layout)
    legend.setLinkedMap(map_item)
    legend.setAutoUpdateModel(True)
    legend.setTitle(title)
    try:
        legend.rstyle(QgsLegendStyle.Title).setFont(QFont("Arial", 8, QFont.Bold))
        legend.rstyle(QgsLegendStyle.SymbolLabel).setFont(QFont("Arial", 7))
    except Exception:
        pass
    legend.attemptSetSceneRect(QRectF(x, y, w, h))
    layout.addLayoutItem(legend)
    legend.updateLegend()
    return legend


def add_title(layout, text, x=10, y=5, w=277, h=18, size=14):
    title = QgsLayoutItemLabel(layout)
    title.setText(text)
    title.setFont(QFont("Arial", size, QFont.Bold))
    title.attemptSetSceneRect(QRectF(x, y, w, h))
    title.setHAlign(Qt.AlignHCenter)
    layout.addLayoutItem(title)
    return title


def add_source(layout, text, x=10, y=198, w=200, h=8):
    lbl = QgsLayoutItemLabel(layout)
    lbl.setText(text)
    lbl.setFont(QFont("Arial", 7))
    lbl.attemptSetSceneRect(QRectF(x, y, w, h))
    layout.addLayoutItem(lbl)
    return lbl


def add_scalebar(layout, map_item, x=12, y=183, w=80, h=12):
    scalebar = QgsLayoutItemScaleBar(layout)
    scalebar.setStyle("Single Box")
    scalebar.setLinkedMap(map_item)
    scalebar.setUnits(QgsUnitTypes.DistanceKilometers)
    scalebar.setNumberOfSegments(4)
    scalebar.setNumberOfSegmentsLeft(0)
    scalebar.setUnitsPerSegment(5)
    scalebar.setUnitLabel("km")
    scalebar.setFont(QFont("Arial", 8))
    scalebar.attemptSetSceneRect(QRectF(x, y, w, h))
    scalebar.applyDefaultSize()
    scalebar.attemptMove(QgsLayoutPoint(x, y, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(scalebar)
    return scalebar


def add_info_box(layout, x, y, w, h, title, lines, bg_color="F5F8FA"):
    """
    Kotak informasi kecil (dipakai untuk Study Area panel & Correlation summary).
    `lines` adalah list of (label, value) tuples.
    """
    box = QgsLayoutItemShape(layout)
    box.setShapeType(QgsLayoutItemShape.Rectangle)
    box.attemptSetSceneRect(QRectF(x, y, w, h))
    box.setSymbol(None)  # default symbol; warna diatur lewat properti simple fill di bawah
    layout.addLayoutItem(box)

    # Set fill via simple fill symbol
    from qgis.core import QgsFillSymbol
    fill_symbol = QgsFillSymbol.createSimple({
        "color": bg_color,
        "outline_color": "#B8C4CC",
        "outline_width": "0.3"
    })
    box.setSymbol(fill_symbol)

    title_lbl = QgsLayoutItemLabel(layout)
    title_lbl.setText(title)
    title_lbl.setFont(QFont("Arial", 9, QFont.Bold))
    title_lbl.attemptSetSceneRect(QRectF(x+4, y+3, w-8, 6))
    layout.addLayoutItem(title_lbl)

    text_lines = "\n".join([f"{lbl} : {val}" for lbl, val in lines])
    body_lbl = QgsLayoutItemLabel(layout)
    body_lbl.setText(text_lines)
    body_lbl.setFont(QFont("Arial", 8))
    body_lbl.attemptSetSceneRect(QRectF(x+4, y+10, w-8, h-12))
    layout.addLayoutItem(body_lbl)


def new_layout(project, name):
    mgr = project.layoutManager()
    existing = mgr.layoutByName(name)
    if existing:
        mgr.removeLayout(existing)
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(name)
    layout.setUnits(QgsUnitTypes.LayoutMillimeters)
    page = layout.pageCollection().pages()[0]
    page.setPageSize(QgsLayoutSize(297, 210, QgsUnitTypes.LayoutMillimeters))
    return layout, mgr

# =============================================================================
# 7. LOAD BOUNDARY SLEMAN
# =============================================================================

if not os.path.exists(BOUNDARY_SHP):
    raise FileNotFoundError(f"File tidak ditemukan:\n{BOUNDARY_SHP}")

boundary_layer = QgsVectorLayer(BOUNDARY_SHP, "Batas Sleman", "ogr")
if not boundary_layer.isValid():
    raise ValueError("Layer boundary Sleman tidak valid!")
style_boundary(boundary_layer)

print(f"✓ Boundary Sleman loaded: {boundary_layer.featureCount()} fitur")

padded_extent = get_padded_extent(boundary_layer)

# Baca statistik korelasi dari CSV hasil Script 04/05
corr_stats = get_correlation_stats(MERGED_CSV)
if corr_stats:
    print(f"✓ Korelasi dimuat dari CSV: r={corr_stats['r']:.2f}, "
          f"R²={corr_stats['r2']:.2f}, p={corr_stats['p']:.3f}")
else:
    print("  [WARNING] File merged_chirps_ndvi.csv tidak ditemukan/valid — "
          "kotak ringkasan korelasi akan dilewati.")

# =============================================================================
# 8. LAYOUT 1 - PETA MEAN NDVI TAHUNAN 2025
# =============================================================================

print("\n📍 Membuat Layout 1: Peta Mean NDVI Tahunan 2025...")

ndvi_files_2025 = list_ndvi_files(NDVI_DIR, year=2025)

if not ndvi_files_2025:
    print("  [SKIP] Tidak ada file NDVI tahun 2025 ditemukan")
    ndvi_mean_path = None
else:
    ndvi_paths = [p for _, p in ndvi_files_2025]
    ndvi_mean_path = os.path.join(TEMP_DIR, "ndvi_mean_2025.tif")
    ndvi_mean_path = build_mean_raster(ndvi_paths, ndvi_mean_path, label="NDVI")

if ndvi_mean_path is None:
    ndvi_layer = None
else:
    ndvi_layer = QgsRasterLayer(ndvi_mean_path, "Mean NDVI 2025")
    if not ndvi_layer.isValid():
        print(f"  [SKIP] Raster NDVI mean tidak valid: {ndvi_mean_path}")
        ndvi_layer = None
    else:
        renderer = build_renderer_ndvi(ndvi_layer)
        ndvi_layer.setRenderer(renderer)

        layout1, mgr = new_layout(QgsProject.instance(), "Layout_NDVI")

        map_item = QgsLayoutItemMap(layout1)
        map_item.attemptSetSceneRect(QRectF(10, 25, 210, 165))
        map_item.setExtent(padded_extent)
        map_item.setLayers([ndvi_layer, boundary_layer])
        layout1.addLayoutItem(map_item)

        add_title(layout1, "Peta Rata-rata NDVI Kabupaten Sleman — Tahun 2025")
        add_source(layout1, "Sumber: MODIS MOD13Q1 (NASA AppEEARS), rata-rata seluruh komposit 16-harian 2025 | "
                             "Batas Admin: GADM/BIG | Proyeksi: WGS84")
        add_scalebar(layout1, map_item, x=15, y=183, w=80, h=14)
        add_north_arrow(layout1, x=225, y=30, size=12)
        add_legend(layout1, map_item, "NDVI (Mean 2025)", 227, 50, 65, 120)

        out1 = os.path.join(MAPS_DIR, "Figure_05_NDVI_Map.png")
        export_layout_as_png(layout1, out1)
        mgr.removeLayout(layout1)

# =============================================================================
# 9. LAYOUT 2 - PETA TOTAL CURAH HUJAN TAHUNAN 2025
# =============================================================================

print("\n📍 Membuat Layout 2: Peta Total Curah Hujan Tahunan 2025...")

chirps_files_2025 = list_chirps_all(CHIRPS_DIR, year=2025)

if not chirps_files_2025:
    print("  [SKIP] Tidak ada data CHIRPS tahun 2025")
    chirps_sum_path = None
else:
    chirps_sum_path = os.path.join(TEMP_DIR, "chirps_sum_2025.tif")
    chirps_sum_path = build_sum_raster(chirps_files_2025, chirps_sum_path, label="CHIRPS")

if chirps_sum_path is None:
    chirps_layer_main = None
else:
    chirps_layer_main = QgsRasterLayer(chirps_sum_path, "Total Rainfall 2025")
    if not chirps_layer_main.isValid():
        print(f"  [SKIP] Raster CHIRPS total tidak valid: {chirps_sum_path}")
        chirps_layer_main = None
    else:
        renderer, max_val_annual = build_renderer_chirps(chirps_layer_main, chirps_sum_path)
        chirps_layer_main.setRenderer(renderer)

        layout2, mgr = new_layout(QgsProject.instance(), "Layout_CHIRPS")

        map_item2 = QgsLayoutItemMap(layout2)
        map_item2.attemptSetSceneRect(QRectF(10, 25, 210, 165))
        map_item2.setExtent(padded_extent)
        map_item2.setLayers([chirps_layer_main, boundary_layer])
        layout2.addLayoutItem(map_item2)

        add_title(layout2, "Peta Total Curah Hujan Kabupaten Sleman — Tahun 2025")
        add_source(layout2, "Sumber: CHIRPS v2.0 Daily, total akumulasi 365 hari 2025 | "
                             "Batas Admin: GADM/BIG | Proyeksi: WGS84")
        add_scalebar(layout2, map_item2, x=15, y=183, w=80, h=14)
        add_north_arrow(layout2, x=225, y=30, size=12)
        add_legend(layout2, map_item2, "Curah Hujan (mm/tahun)", 227, 50, 65, 110)

        out2 = os.path.join(MAPS_DIR, "Figure_06_Rainfall_Map.png")
        export_layout_as_png(layout2, out2)
        mgr.removeLayout(layout2)

# =============================================================================
# 10. LAYOUT 3 - PETA KOMPARASI (apple-to-apple: bulan sama) + RINGKASAN KORELASI
# =============================================================================

print(f"\n📍 Membuat Layout 3: Peta Komparasi NDVI vs Rainfall (bulan {COMPARISON_MONTH}, apple-to-apple)...")

ndvi_comp = find_ndvi_for_month(NDVI_DIR, target_month=COMPARISON_MONTH, target_year=2025)
chirps_comp_files = find_chirps_for_month(CHIRPS_DIR, month=COMPARISON_MONTH, year=2025)

if ndvi_comp and chirps_comp_files:
    ndvi_comp_path, ndvi_comp_date = ndvi_comp

    # Sum CHIRPS untuk bulan yang sama (total bulanan, lebih representatif
    # daripada satu hari acak dalam bulan tsb)
    chirps_month_sum_path = os.path.join(TEMP_DIR, f"chirps_sum_month{COMPARISON_MONTH:02d}.tif")
    chirps_month_sum_path = build_sum_raster(
        chirps_comp_files, chirps_month_sum_path, label=f"CHIRPS bulan {COMPARISON_MONTH}"
    )

    ndvi_comp_layer = QgsRasterLayer(ndvi_comp_path, "NDVI Comparison")
    chirps_comp_layer = QgsRasterLayer(chirps_month_sum_path, "Rainfall Comparison")

    if ndvi_comp_layer.isValid() and chirps_comp_layer.isValid():
        ndvi_comp_layer.setRenderer(build_renderer_ndvi(ndvi_comp_layer))
        chirps_renderer, chirps_comp_max = build_renderer_chirps(chirps_comp_layer, chirps_month_sum_path)
        chirps_comp_layer.setRenderer(chirps_renderer)

        layout3, mgr = new_layout(QgsProject.instance(), "Layout_Comparison")

        month_names = {1:"Januari", 2:"Februari", 3:"Maret", 4:"April", 5:"Mei", 6:"Juni",
                       7:"Juli", 8:"Agustus", 9:"September", 10:"Oktober", 11:"November", 12:"Desember"}
        comp_month_name = month_names.get(COMPARISON_MONTH, str(COMPARISON_MONTH))

        # --- Map kiri: NDVI ---
        map_left = QgsLayoutItemMap(layout3)
        map_left.attemptSetSceneRect(QRectF(8, 22, 138, 128))
        map_left.setExtent(padded_extent)
        map_left.setLayers([ndvi_comp_layer, boundary_layer])
        layout3.addLayoutItem(map_left)

        label_left = QgsLayoutItemLabel(layout3)
        label_left.setText(f"NDVI — {comp_month_name} 2025")
        label_left.setFont(QFont("Arial", 11, QFont.Bold))
        label_left.setHAlign(Qt.AlignHCenter)
        label_left.attemptSetSceneRect(QRectF(8, 151, 138, 9))
        layout3.addLayoutItem(label_left)

        # --- Map kanan: Rainfall (bulan sama) ---
        map_right = QgsLayoutItemMap(layout3)
        map_right.attemptSetSceneRect(QRectF(151, 22, 138, 128))
        map_right.setExtent(padded_extent)
        map_right.setLayers([chirps_comp_layer, boundary_layer])
        layout3.addLayoutItem(map_right)

        label_right = QgsLayoutItemLabel(layout3)
        label_right.setText(f"Total Curah Hujan — {comp_month_name} 2025")
        label_right.setFont(QFont("Arial", 11, QFont.Bold))
        label_right.setHAlign(Qt.AlignHCenter)
        label_right.attemptSetSceneRect(QRectF(151, 151, 138, 9))
        layout3.addLayoutItem(label_right)

        # --- Judul utama ---
        add_title(layout3,
                  f"Perbandingan Spasial NDVI dan Curah Hujan — {comp_month_name} 2025 (Kab. Sleman)",
                  x=8, y=4, w=281, h=14, size=13)

        # --- Legend kiri (NDVI) & kanan (Rainfall) ---
        add_legend(layout3, map_left,  "NDVI",                       8,   163, 138, 24)
        add_legend(layout3, map_right, "Curah Hujan (mm/bulan)",     151, 163, 138, 24)

        # --- Scale bar & north arrow ---
        add_scalebar(layout3, map_left, x=8, y=190, w=60, h=9)
        add_north_arrow(layout3, x=275, y=186, size=9)

        # --- Source ---
        add_source(layout3, "Sumber: CHIRPS v2.0 Daily & MODIS MOD13Q1 | Batas Admin: GADM/BIG | Proyeksi: WGS84",
                   x=72, y=191, w=200, h=6)

        # --- Study Area info box (kiri bawah) ---
        add_info_box(
            layout3, x=8, y=199, w=70, h=9,
            title="",
            lines=[("Kab. Sleman", f"{SLEMAN_AREA_KM2} km² | EPSG:4326")],
            bg_color="EFF4F7"
        )

        # --- Correlation summary box (kanan bawah) ---
        if corr_stats:
            sig = "Signifikan" if corr_stats["p"] < 0.05 else "Tidak signifikan"
            add_info_box(
                layout3, x=151, y=199, w=138, h=9,
                title="",
                lines=[(
                    "Korelasi Rainfall–NDVI (Tahunan)",
                    f"r = {corr_stats['r']:.2f}  |  R\u00b2 = {corr_stats['r2']:.2f}  |  "
                    f"p = {corr_stats['p']:.3f}  ({sig}, n={corr_stats['n']})"
                )],
                bg_color="EFF4F7"
            )

        out3 = os.path.join(MAPS_DIR, "Figure_07_Comparison_Map.png")
        export_layout_as_png(layout3, out3)
        mgr.removeLayout(layout3)
    else:
        print("  [SKIP] Salah satu raster (NDVI/CHIRPS) untuk komparasi tidak valid")
else:
    print("  [SKIP] Data NDVI atau CHIRPS untuk bulan komparasi tidak ditemukan")

# =============================================================================
# SELESAI
# =============================================================================

print("\n" + "="*60)
print("  ✅ Script 07 (v2) selesai!")
print(f"  📁 Peta tersimpan di:\n     {MAPS_DIR}")
print("="*60)
print("\n  Output:")
print("  Figure_05_NDVI_Map.png        -> Mean NDVI tahunan 2025")
print("  Figure_06_Rainfall_Map.png    -> Total curah hujan tahunan 2025")
print("  Figure_07_Comparison_Map.png  -> NDVI vs Rainfall (bulan sama,")
print("                                   + ringkasan korelasi r/R²/p)")
print(f"\n  Catatan: file raster sementara (mean/sum) disimpan di:")
print(f"  {TEMP_DIR}")
print("  Folder ini bisa dihapus setelah peta selesai, atau dibiarkan")
print("  sebagai cache supaya re-run berikutnya lebih cepat.")