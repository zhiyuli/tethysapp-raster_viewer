import os
from tethys_apps.base.persistent_store import get_persistent_store_engine as gpse

from django.shortcuts import render
from django.http import Http404
import urllib2
#from tethys_apps.base import TethysAppBase, SpatialDatasetService
from tethys_dataset_services.engines import GeoServerSpatialDatasetEngine
import zipfile
try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO
import tempfile
import shutil
import os
from django.contrib.sites.shortcuts import get_current_site
import sys

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
        print ("zip size 1: " + str(sys.getsizeof(in_memory_zip)))
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
        print ("zip size 2: " + str(sys.getsizeof(in_memory_zip)))
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

            store_id = ws_name+":"+store_name

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
            raise Exception("addZippedTif2Geoserver() error")

def getMapParas(geosvr_url_base, wsName, layerName):

    try:
        geosvr_ulr_wms = geosvr_url_base+"/geoserver/wms/"
        layer = wsName + ":" + layerName
        print geosvr_ulr_wms
        print layer
        map_view_options = {'height': '400px',
                    'width': '100%',
                    'controls': ['ZoomSlider',
                                 'Rotate',
                                 'FullScreen',
                                 'ScaleLine',
                                 {'ZoomToExtent': {'projection': 'EPSG:4326',
                                                   'extent': [-135, 22, -55, 54]
                                                  }},
                                 {'MousePosition': {'projection': 'EPSG:4326'}},
                    ],
                    'layers': [{'TiledWMS': {'url': geosvr_ulr_wms,
                                        'params': {'LAYERS': layer, 'TILED': True},
                                        'serverType': 'geoserver'}
                                },
                    ],
                    'view': {'projection': 'EPSG:4326',
                             'center': [-100, 40], 'zoom': 3.5,
                             'maxZoom': 18, 'minZoom': 1},
                    'base_map': 'OpenStreetMap'
        }


        return map_view_options
    except:
        print ("getMapParas() error")
        raise Exception("getMapParas() error")

def getGeoSvrUrlBase(request):

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