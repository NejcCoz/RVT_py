"""
NAME:
    RVT Analytical hillshading, ESRI ArcGis Pro

DESCRIPTION:
    https://github.com/Esri/raster-functions/wiki/PythonRasterFunction#anatomy-of-a-python-raster-function
    Python raster function for ESRI ArcGis which computes hillshade.

INPUTS:
    input_DEM_arr   - input DEM numpy array
    resolution_x    - DEM resolution in X direction
    resolution_y    - DEM resolution in Y direction
    sun_azimuth     - solar azimuth angle (clockwise from North) in degrees
    sun_elevation   - solar vertical angle (above the horizon) in degrees

OUTPUTS:
    hillshade

KEYWORDS:
    /

DEPENDENCIES:
    RVT_vis_fn.slope_aspect
    RVT_vis_fn.analytical_hillshading

AUTHOR:
    RVT:
        Klemen Zaksek (klemen.zaksek@zmaw.de)
    RVT_py:
        Žiga Maroh (ziga.maroh@icloud.com)

MODIFICATION HISTORY:
    RVT:
        1.0     Written by Klemen Zaksek, 2013.
        1.1     September 2014: Suppress_output and cosi keywords added to the procedure
    RVT_py:
        1.0     Written by Žiga Maroh, 2020.
"""

import numpy as np
import RVT_vis_fn


class RVT_Hillshade():

    def __init(self):
        self.name = "RVT analytical hillshading"
        self.description = "Calculates hillshade."
        self.prepare()

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': "Input raster for which to create the hillshade map."
            },
            {
                'name': 'sun_azimuth',
                'dataType': 'numeric',
                'value': 315.,
                'required': False,
                'displayName': "Sun azimuth",
                'description': "Solar azimuth angle (clockwise from North) in degrees."
            },
            {
                'name': 'sun_elevation',
                'dataType': 'numeric',
                'value': 35.,
                'required': False,
                'displayName': "Sun elevation",
                'description': "Solar vertical angle (above the horizon) in degrees."
            }
        ]

    def getConfiguration(self, **scalars):
        return {
            'compositeRasters': False,
            'inheritProperties': 2 | 4 | 8,  # Inherit all but the pixel type and NoData from the input raster dataset.
            'invalidateProperties': 2 | 4 | 8,
            # Invalidate the statistics and histogram on the parent dataset because the pixel values are modified.
            'inputMask': True,
            'resampling': False,
            'padding': 1
            # An input raster mask is not needed in .updatePixels() because the inherited area of NoData are used instead.
        }

    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['bandCount'] = 1
        r = kwargs['raster_info']
        kwargs['output_info']['noData'] = self.assignNoData(r['pixelType']) if not (r['noData']) else r['noData']
        kwargs['output_info']['pixelType'] = 'f4'
        kwargs['output_info']['histogram'] = ()
        self.prepare(azimuth=kwargs.get('sun_azimuth'), elevation=kwargs.get("sun_elevation"))
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        dem = np.array(pixelBlocks['raster_pixels'], dtype='f4', copy=False)[0]  # Input pixel array.
        m = np.array(pixelBlocks['raster_mask'], dtype='u1', copy=False)[0]  # Input raster mask.
        self.noData = self.assignNoData(props['pixelType']) if not (props['noData']) else props['noData']
        dem = np.where(np.not_equal(dem, self.noData), dem, dem)

        pixel_size = props['cellSize']
        if (pixel_size[0] <= 0) | (pixel_size[1] <= 0):
            raise Exception("Input raster cell size is invalid.")

        hillshade = RVT_vis_fn.analytical_hillshading(input_DEM_arr=dem, resolution_x=pixel_size[0],
                                                      resolution_y=pixel_size[1], sun_azimuth=self.azimuth,
                                                      sun_elevation=self.elevation, is_padding_applied=True)

        pixelBlocks['output_pixels'] = hillshade.astype(props['pixelType'])
        pixelBlocks['output_mask'] = \
            m[:-2, :-2] & m[1:-1, :-2] & m[2:, :-2] \
            & m[:-2, 1:-1] & m[1:-1, 1:-1] & m[2:, 1:-1] \
            & m[:-2, 2:] & m[1:-1, 2:] & m[2:, 2:]

        return pixelBlocks

    def assignNoData(self, pixelType):
        # assign noData depending on input pixelType
        if pixelType == 'f4':
            return np.array([-3.4028235e+038, ])  # float 32 bit
        elif pixelType == 'i4':
            return np.array([-65536, ])  # signed integer 32 bit
        elif pixelType == 'i2':
            return np.array([-32768, ])  # signed integer 16 bit
        elif pixelType == 'i1':
            return np.array([-256, ])  # signed integer 8 bit
        elif pixelType == 'u4':
            return np.array([65535, ])  # unsigned integer 32 bit
        elif pixelType == 'u2':
            return np.array([32767, ])  # unsigned integer 16 bit
        elif pixelType == 'u1':
            return np.array([255, ])  # unsigned integer 8 bit

    def prepare(self, azimuth=315, elevation=35):
        self.azimuth = azimuth
        self.elevation = elevation
