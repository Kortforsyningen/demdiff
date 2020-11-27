from osgeo import gdal
import numpy as np
import argparse

gdal.UseExceptions()

# Same choices as for gdal_translate (TODO: use those for gdalwarp?)
RESAMPLE_ALGS = {
    "nearest": gdal.GRA_NearestNeighbour,
    "bilinear": gdal.GRA_Bilinear,
    "cubic": gdal.GRA_Cubic,
    "cubicspline": gdal.GRA_CubicSpline,
    "lanczos": gdal.GRA_Lanczos,
    "average": gdal.GRA_Average,
    "mode": gdal.GRA_Mode,
}

arg_parser = argparse.ArgumentParser(
    description="Calculate raster difference between two raster datasets.",
    epilog='Generates a GeoTIFF raster file determined as the "new" raster minus the "old" raster. The output raster will take its data type, nodata value, spatial extent, resolution and spatial reference system from the "new" dataset. Prior to taking the difference, the "old" dataset is resampled using the algorithm provided in `resample_alg` to match that of the "new" dataset.',
)
arg_parser.add_argument("old_raster", type=str, help="path to old raster input file")
arg_parser.add_argument("new_raster", type=str, help="path to new raster input file")
arg_parser.add_argument(
    "output_raster",
    type=str,
    help="path to output (difference) raster file (GeoTIFF format)",
)
arg_parser.add_argument(
    "--resample_alg",
    type=str,
    choices=RESAMPLE_ALGS.keys(),
    default="bilinear",
    help="resampling algorithm to use on old raster (default: 'bilinear')",
)

input_args = arg_parser.parse_args()

old_raster_filename = input_args.old_raster
new_raster_filename = input_args.new_raster
output_raster_filename = input_args.output_raster

resample_alg = RESAMPLE_ALGS[input_args.resample_alg]

old_datasrc = gdal.Open(old_raster_filename)
new_datasrc = gdal.Open(new_raster_filename)

new_srs = new_datasrc.GetProjectionRef()
new_geotransform = new_datasrc.GetGeoTransform()
new_num_cols = new_datasrc.RasterXSize
new_num_rows = new_datasrc.RasterYSize

if new_geotransform[2] != 0.0 or new_geotransform[4] != 0.0:
    raise ValueError("Rotation in geotransform is not supported")

# obtain extent from input dataset
new_x_1 = new_geotransform[0]
new_x_2 = new_geotransform[0] + new_geotransform[1] * new_num_cols
new_y_1 = new_geotransform[3]
new_y_2 = new_geotransform[3] + new_geotransform[5] * new_num_rows

x_min = min(new_x_1, new_x_2)
x_max = max(new_x_1, new_x_2)
y_min = min(new_y_1, new_y_2)
y_max = max(new_y_1, new_y_2)

new_band = new_datasrc.GetRasterBand(1)
new_datatype = new_band.DataType
new_nodata_value = new_band.GetNoDataValue()

old_warp_options = gdal.WarpOptions(
    format="MEM",
    outputBounds=[x_min, y_min, x_max, y_max],
    width=new_num_cols,  # force raster dimensions to match those of the "input" window
    height=new_num_rows,
    workingType=new_datatype,
    outputType=new_datatype,
    dstSRS=new_srs,
    resampleAlg=resample_alg,
)

old_window = gdal.Warp("", old_datasrc, options=old_warp_options)
old_window_band = old_window.GetRasterBand(1)

old_window_num_cols = old_window.RasterXSize
old_window_num_rows = old_window.RasterYSize
old_nodata_value = old_window_band.GetNoDataValue()

# read new and old rasters as NumPy arrays, converting the NODATA values to NaN
old_array = old_window_band.ReadAsArray()
old_array[old_array == old_nodata_value] = np.nan

new_array = new_band.ReadAsArray()
new_array[new_array == new_nodata_value] = np.nan

# compute difference and use NODATA value from new dataset
output_array = new_array - old_array
output_array[~np.isfinite(output_array)] = new_nodata_value

output_driver = gdal.GetDriverByName("GTiff")
output_datasrc = output_driver.Create(
    output_raster_filename,
    new_num_cols,
    new_num_rows,
    1,  # number of bands
    new_datatype,
)
output_datasrc.SetProjection(new_srs)
output_datasrc.SetGeoTransform(new_geotransform)
output_band = output_datasrc.GetRasterBand(1)
output_band.SetNoDataValue(new_nodata_value)
output_band.WriteArray(output_array)
output_datasrc.FlushCache()
