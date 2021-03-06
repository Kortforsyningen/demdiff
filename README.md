# demdiff
Tool to compute raster difference of DEMs

## Prerequisites
A Python environment with [GDAL](https://gdal.org/) and [NumPy](https://numpy.org/) available.

## Usage
Typical intended usage involves the following _input_ datasets:

* A [VRT](https://gdal.org/drivers/raster/vrt.html) of "old" raster data
* One tile of "new" raster data

This will _output_:

* One tile of the "new minus old" raster difference

With a VRT of "old" input data, a GeoTIFF file of "new" input data, and writing to an output GeoTIFF file, a command could look like this:

```python demdiff.py old.vrt new_1km_NNNN_EEE.tif diff_1km_NNNN_EEE.tif```

For further details, see the script help using ```python demdiff.py -h```.

For computing raster differences of large areas, it is intended that this script be called on a per-tile basis (retaining the same "old" VRT for each call). Batch processing of tiles may be implemented by calling this script from [GNU Parallel](https://www.gnu.org/software/parallel/) or similar.
