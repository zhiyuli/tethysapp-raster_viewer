
from tethys_apps.base.persistent_store import get_persistent_store_engine as gpse
from tethys_dataset_services.engines import GeoServerSpatialDatasetEngine
import zipfile

try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO

import os
from osgeo import gdal, gdalconst
import logging
logger = logging.getLogger(__name__)

def get_persistent_store_engine(persistent_store_name):
    """
    Returns an SQLAlchemy engine object for the persistent store name provided.
    """
    # Derive app name
    app_name = os.path.split(os.path.dirname(__file__))[1]

    # Get engine
    return gpse(app_name, persistent_store_name)

def zipInMem(content_fn, content_obj):
    try:
        #init a mem space
        in_memory_zip = StringIO()
        # Create a Zip Helper Obj initialed with existing mem space
        zip_helper = zipfile.ZipFile(in_memory_zip, "a", zipfile.ZIP_DEFLATED, False)
        # zip content file name
        zip_content_fn = content_fn
        # path to the file will be zipped
        zip_content_full_path = content_obj
        # zip helper zips local file into mem space "in_memory_zip"
        zip_helper.writestr(zip_content_fn, zip_content_full_path)
        zip_helper.debug = 3

        # Mark the files as having been created on Windows so that
        # Unix permissions are not inferred as 0000
        for zfile in zip_helper.filelist:
            zfile.create_system = 0
        zip_info = zip_helper.getinfo(zip_content_fn)
        zip_crc = str(zip_info.CRC)
        logger.debug("CRC: " + zip_crc)
        zip_helper.close()

        return {'zipped_obj': in_memory_zip, 'crc': zip_crc}

    except:
        logger.exception("zippedInMem() error")
        raise Exception("zippedInMem() error")


def zipSaveAs(content_fn, content_obj, save_path, zip_fn):
    try:
        logger.debug ("tif name: " + content_fn)
        logger.debug ("save path:  " + save_path)
        logger.debug ("zip name: " + zip_fn)
        rslt_dic = zipInMem(content_fn, content_obj)
        in_memory_zip = rslt_dic['zipped_obj']

        zip_crc = rslt_dic['crc']
        zip_filename = zip_fn
        zip_file_full_path = save_path+'/'+zip_filename
        f = file(zip_file_full_path, "w")
        #Writes the mem space 'in_memory_zip' to a file.
        f.write(in_memory_zip.getvalue())
        f.close()
        logger.debug ("zip file saved at : " + zip_file_full_path)
        return {'zip_file_full_path': zip_file_full_path, 'crc': zip_crc}

    except:
        logger.exception ("zipSaveAs() error")
        raise Exception("zipSaveAs() error")

def addZippedTif2Geoserver(geosvr_url_base, uname, upwd, ws_name, store_name, zippedTif_full_path, res_url):

        try:
            geosvr_url_full = geosvr_url_base+"/geoserver/rest/"
            logger.debug("GeoServer REST Full URL: "+geosvr_url_full)
            coverage_file = zippedTif_full_path

            logger.debug("Connect to Geoserver")
            spatial_dataset_engine = GeoServerSpatialDatasetEngine(endpoint=geosvr_url_full, username=uname, password=upwd)
            logger.debug("Connected")

            response = None
            result = spatial_dataset_engine.create_workspace(workspace_id=ws_name, uri=res_url)
            if result['success']:
                logger.debug("Create workspace " + ws_name + " successfully")
            else:
                logger.debug("Create workspace " + ws_name + " failed")
            logger.debug (result)

            store_id = ws_name + ":" + store_name

            result = None
            result = spatial_dataset_engine.create_coverage_resource(store_id=store_id, coverage_file=coverage_file, coverage_type='geotiff')
            if result['success']:
                logger.debug("Create store " + store_name + " successfully")
            else:
                logger.debug("Create store " + store_name + " failed")
                logger.debug(result)

            spatial_dataset_engine.list_layers(debug=True)

            return True
        except:
            logger.exception("addZippedTif2Geoserver() error")
            return False

def getMapParas(geosvr_url_base, wsName, store_id, layerName, un, pw):

    rslt = {}

    geosvr_ulr_wms = geosvr_url_base + "/geoserver/wms/"
    layer = wsName + ":" + layerName
    logger.debug(geosvr_ulr_wms)
    logger.debug(layer)

    #manually create a http query to get Rater bounding box
    #not a good practice, consider using tethys geoserver api or gisconfig
    import urllib2, json, base64
    url = '/geoserver/rest/workspaces/{0}/coveragestores/{1}/coverages/{2}.json'
    url = geosvr_url_base + url.format(wsName, store_id, layerName)
    logger.debug("Geo Auth: " + url)

    authKey = base64.encodestring('%s:%s' % (un, pw)).replace('\n', '')
    request = urllib2.Request(url)
    headers = {'Authorization': "Basic " + authKey}
    for k in headers.keys():
        request.add_header(k, headers[k])

    try:
        response = urllib2.urlopen(request, timeout=30).read()
        if "no such" in str(response).lower():
            rslt["sucess"] = False
            return rslt

        j = json.loads(response)
        logger.debug(j)
        if "EPSG:404000" in str(j):
            logger.debug ("The resouce has EPSG:404000 local crs")
            raise
        bounding= j['coverage']['latLonBoundingBox']
        extent=[bounding['minx'], bounding['maxx'], bounding['miny'], bounding['maxy']]
        logger.debug ("extent:")
        logger.debug (extent)

        rslt['minx'] = bounding['minx']
        rslt['miny'] = bounding['miny']
        rslt['maxx'] = bounding['maxx']
        rslt['maxy'] = bounding['maxy']
        rslt['json_response'] = j
        rslt['success'] = True
        return rslt

    except urllib2.HTTPError as e:
        logger.debug(e.message)
        logger.debug ("The resource is not on Geoserver!")
        return {"success": False}
    except Exception as e:
        logger.debug(e.message)
        return {"success": False}

def extract_min_max_2nd_min_max(srcband):

    nvd_old = srcband.GetNoDataValue()

    stat_old = srcband.ComputeStatistics(0)
    min_val = stat_old[0]
    max_val = stat_old[1]
    mean_val = stat_old[2]
    std_val = stat_old[3]

    srcband.SetNoDataValue(min_val)
    stat_2nd_min = srcband.ComputeStatistics(0)
    min_2nd_val = stat_2nd_min[0]

    srcband.SetNoDataValue(max_val)
    stat_2nd_max = srcband.ComputeStatistics(0)
    max_2nd_val = stat_2nd_max[1]

    if nvd_old is not None:
        srcband.SetNoDataValue(nvd_old)

    return {
            "no_data_val": nvd_old,
            "min_val": min_val,
            "max_val": max_val,
            "mean_val":  mean_val,
            "std_val": std_val,
            "min_2nd_val": min_2nd_val,
            "max_2nd_val": max_2nd_val
            }


def extract_geotiff_stat_info(tif_full_path):
    logger.debug ("GDAL read:")
    logger.debug(tif_full_path)
    band_stat_info_array = []
    try:
        # str(tif_full_path): add str() to tif_full_path to workaround a GDAL 1.7 bug
        src_ds = gdal.Open(str(tif_full_path), gdalconst.GA_ReadOnly)
        for band in range(src_ds.RasterCount):
            band_id = band+1
            band_info = {}
            logger.debug ("Begin get GetRasterBand for band {0}".format(str(band_id)))
            srcband = src_ds.GetRasterBand(band_id)
            if srcband is not None:
                # handle noDataValue and MinValue
                # http://gis.stackexchange.com/questions/54150/gdal-does-not-ignore-nodata-value
                # GetNoDataValue() only return pre-stored NoDataValue
                # ComputeStatistics(0) will scan the file and recalculate real Stat values (Min, Max...) on the fly

                # Problem: If the NoDataValue is not set correctly and properly, it can cause trouble visualizing it.
                # As we need to assign color A to the min value and color B to max value. if current min value is actually the nodatavalue but has not been set as,
                # the color A will be assign to a very small value, all other raster data value are close to max value. So the whole picture will be in color B.
                # Case 1: no nodatavalue has been set
                # Case 2: nodatavalue has been set correctly
                # Case 3: nodatavalue has been set but it is wrong or inaccurate (like https://www.hydroshare.org/resource/101f746de3ca4896a6d0f05206483766/)

                # To aviod the above improper visualization and considering all possible cases of raster files, we extract the min_val, min_2nd_val, max_val, and max_2nd_val of a raster band
                # and select the larger val between min_val and min_2nd_val to assign color A; the smaller val between max_val and max_2nd_val to assign color B
                # this may cause some inaccuracy in visualization in some cases, like we may set color A to a real 2nd min value instead of the real min value.
                # But we believe the loss in visualization is ignorable.

               min_max_2nd_min_max_dict = extract_min_max_2nd_min_max(srcband)
               nvd= min_max_2nd_min_max_dict["no_data_val"]

               band_info["band_id"] = band_id
               band_info["min_val"] = min_max_2nd_min_max_dict["min_val"]
               band_info["max_val"] = min_max_2nd_min_max_dict["max_val"]
               band_info["mean_val"] = min_max_2nd_min_max_dict["mean_val"]
               band_info["std_val"] = min_max_2nd_min_max_dict["std_val"]
               band_info["min_2nd_val"] = min_max_2nd_min_max_dict["min_2nd_val"]
               band_info["max_2nd_val"] = min_max_2nd_min_max_dict["max_2nd_val"]
               band_info["no_data_val"] = nvd if nvd is not None else -987654321
               band_stat_info_array.append(band_info)
            logger.debug("End get GetRasterBand for band {0}".format(str(band_id)))
    except Exception as e:
        logger.error ("extract_geotiff_stat_info Error")
        logger.exception(e.message)
    return band_stat_info_array
