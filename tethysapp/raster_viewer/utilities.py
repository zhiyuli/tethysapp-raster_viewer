import os
from tethys_apps.base.persistent_store import get_persistent_store_engine as gpse

from django.shortcuts import render
from django.http import Http404
#from tethys_apps.base import TethysAppBase, SpatialDatasetService
from tethys_dataset_services.engines import GeoServerSpatialDatasetEngine
import zipfile
import urllib2, json, base64

try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO
import tempfile
import shutil
import os
from django.contrib.sites.shortcuts import get_current_site
import sys
from osgeo import gdal, gdalconst
import math

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
        print "CRC: " + zip_crc
        zip_helper.close()

        return {'zipped_obj': in_memory_zip, 'crc': zip_crc}

    except:
        print ("zippedInMem() error")
        raise Exception("zippedInMem() error")


def zipSaveAs(content_fn, content_obj, save_path, zip_fn):
    try:
        print "tif name: " + content_fn
        print "save path:  " + save_path
        print "zip name: " + zip_fn
        rslt_dic = zipInMem(content_fn, content_obj)
        in_memory_zip = rslt_dic['zipped_obj']

        zip_crc = rslt_dic['crc']
        zip_filename = zip_fn
        zip_file_full_path = save_path+'/'+zip_filename
        f = file(zip_file_full_path, "w")
        #Writes the mem space 'in_memory_zip' to a file.
        f.write(in_memory_zip.getvalue())
        f.close()
        print ("zip file saved at : " + zip_file_full_path)
        return {'zip_file_full_path': zip_file_full_path, 'crc': zip_crc}

    except:
        print ("zipSaveAs() error")
        raise Exception("zipSaveAs() error")

def addZippedTif2Geoserver(geosvr_url_base, uname, upwd, ws_name, store_name, zippedTif_full_path, res_url):

        try:
            geosvr_url_full = geosvr_url_base+"/geoserver/rest/"
            print "GeoServer REST Full URL: "+geosvr_url_full
            coverage_file = zippedTif_full_path

            print "Connect to Geoserver"
            spatial_dataset_engine = GeoServerSpatialDatasetEngine(endpoint=geosvr_url_full, username=uname, password=upwd)
            print "Connected"

            response = None
            result = spatial_dataset_engine.create_workspace(workspace_id=ws_name, uri=res_url)
            if result['success']:
                print "Create workspace " + ws_name + " successfully"
            else:
                print "Create workspace " + ws_name + " failed"
            print result

            store_id = ws_name + ":" + store_name

            result = None
            result = spatial_dataset_engine.create_coverage_resource(store_id=store_id, coverage_file=coverage_file, coverage_type='geotiff')
            if result['success']:
                print "Create store " + store_name + " successfully"
            else:
                print "Create store " + store_name + " failed"
            print result

            spatial_dataset_engine.list_layers(debug=True)

            return True
        except:
            print ("addZippedTif2Geoserver() error")
            return False

def getMapParas(geosvr_url_base, wsName, store_id, layerName, un, pw):

    rslt = {}

    geosvr_ulr_wms = geosvr_url_base + "/geoserver/wms/"
    layer = wsName + ":" + layerName
    print geosvr_ulr_wms
    print layer

    #manually create a http query to get Rater bounding box
    #not a good practice, consider using tethys geoserver api or gisconfig
    import urllib2, json, base64
    url = '/geoserver/rest/workspaces/{0}/coveragestores/{1}/coverages/{2}.json'
    url = geosvr_url_base + url.format(wsName, store_id, layerName)
    print "Geo Auth: " + url

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
        print j
        if "EPSG:404000" in str(j):
            print ("The resouce has EPSG:404000 local crs")
            raise
        bounding= j['coverage']['latLonBoundingBox']
        extent=[bounding['minx'], bounding['maxx'], bounding['miny'], bounding['maxy']]
        print "extent:"
        print extent

        rslt['minx'] = bounding['minx']
        rslt['miny'] = bounding['miny']
        rslt['maxx'] = bounding['maxx']
        rslt['maxy'] = bounding['maxy']
        rslt['json_response'] = j
        rslt['success'] = True
        return rslt

    except urllib2.HTTPError as e:
        print e
        print ("The resource is not on Geoserver!")
        return {"success": False}
    except Exception as e:
        print e
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
    print ("GDAL read:")
    print tif_full_path
    band_stat_info_array = []
    try:
        # str(tif_full_path): add str() to tif_full_path to workaround a GDAL 1.7 bug
        src_ds = gdal.Open(str(tif_full_path), gdalconst.GA_ReadOnly)
        for band in range(src_ds.RasterCount):
            band_id = band+1
            band_info = {}
            print ("Begin get GetRasterBand for band {0}".format(str(band_id)))
            srcband = src_ds.GetRasterBand(band_id)
            if srcband is not None:
                # handle noDataValue and MinValue
                # http://gis.stackexchange.com/questions/54150/gdal-does-not-ignore-nodata-value
                # GetNoDataValue() only return currently stored NoDataValue
                # ComputeStatistics(0) will scan the file and recalculate real Stat values (Min, Max...)
                # The Min returnd by ComputeStatistics(0) may be the real NoDataValue or real Min value

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
            print "End get GetRasterBand for band {0}".format(str(band_id))
    except Exception as e:
        print ("extract_geotiff_stat_info Error")
        print e
    return band_stat_info_array

def getGeoSvrUrlBase(request, base_url):

    print "geoserver domain: " + base_url
    return base_url

    current_site = get_current_site(request);
    domain_with_port = current_site.domain
    print "original domain: " + domain_with_port
    idx_cut = domain_with_port.find(':')
    if idx_cut != -1:
        domain_name = domain_with_port[:idx_cut]
    else:
        domain_name = domain_with_port
    print "domain: " + domain_name
    geosvr_url_base = 'http://' + domain_name + ":8181"
    print "geoserver domain: " + geosvr_url_base
    return geosvr_url_base