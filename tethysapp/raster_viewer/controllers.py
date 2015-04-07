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
from utilities import *

#Base_Url_HydroShare REST API
url_base='http://{0}.hydroshare.org/hsapi/resource/{1}/files/{2}'
geosvr_url_base='http://127.0.0.1:8181'

##Call in Rest style
def restcall(request, branch, res_id, filename):
    # make a temp dir
    temp_dir = tempfile.mkdtemp()
    print "temp folder created at " + temp_dir

    try:
        print "restcall", branch, res_id, filename
        url_wml = url_base.format(branch, res_id, filename)
        print "HS_REST_API: " + url_wml

        response = urllib2.urlopen(url_wml)
        print "downloading " + url_wml
        tif_obj = response.read()
        print "download complete"

        rslt_dic= zipSaveAs(filename, tif_obj, temp_dir, "zip_file.zip")
        zip_file_full_path = rslt_dic['zip_file_full_path']
        zip_crc = rslt_dic['crc']

        geosvr_url_base = getGeoSvrUrlBase(request)
        rslt = False
        rslt = addZippedTif2Geoserver(geosvr_url_base, 'admin', 'geoserver', res_id, zip_crc, zip_file_full_path, url_wml)

        if(rslt):
            map_view_options = getMapParas(geosvr_url_base, res_id, filename[:-4])
            context = {"map_view_options": map_view_options, "filename": filename}
        else:
            context = {}

        context = {"map_view_options": map_view_options, "filename": filename}

    except:
        print ("REST call error")
        raise Http404("Cannot locate this resource file")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print temp_dir + " deleted"
            temp_dir=None

    return render(request, 'raster_viewer/home.html', context)

#Normal Get or Post Request
#http://dev.hydroshare.org/hsapi/resource/72b1d67d415b4d949293b1e46d02367d/files/referencetimeseries-2_23_2015-wml_2_0.wml/

# geotiff Name: geotiff.tif
# zip File Name: zipFile.zip
# workspace Name: ws
# storeName: store
# store_id="ws:store"
#
# spatial_dataset_engine.create_coverage_resource(store_id=store_id, coverage_file=zipFile.zip, coverage_type='geotiff')
#
# Create 1:
# /var/lib/geoserver/data/data/ws/store/geotiff.tif
#
# Create 2:
# /var/lib/geoserver/data/workspaces/ws/store/coveragestore.xml
# /var/lib/geoserver/data/workspaces/ws/store/geotiff/coverage.xml
# /var/lib/geoserver/data/workspaces/ws/store/geotiff/layer.xml
#
# Create 3:
# geoserver layer resource name: geotiff
#
# Conclusion:
# 1)Zip file name 'zipFile.zip' does not matter.But the embed tif file name (without extension) 'geotiffwill' be used for Layer Name.
# 2)Store name 'store' should be unique in one workspace. Ex. same store names with different zipfile or geotif cannot cannot be used for creating new layer resource
def home(request):

    filename = None
    res_id = None
    url_wml = None
    branch = None

    # make a temp dir
    temp_dir = tempfile.mkdtemp()
    print "temp folder created at " + temp_dir

    try:
        if request.method == 'POST' and 'res_id' in request.POST and 'filename' in request.POST:
           #print request.POST
           filename = request.POST['filename']
           res_id =  request.POST['res_id']
           branch = request.POST['branch']

        elif request.method == 'GET' and 'res_id' in request.GET and 'filename' in request.GET:
            #print request.GET
            filename = request.GET['filename']
            res_id = request.GET['res_id']
            branch= request.GET['branch']
        else:
            res_id = "6e3ffe34505e4510990e48c25ce0609b"
            branch = "alpha"
            filename = 'logan.tif'

        url_wml = url_base.format(branch,res_id,filename)
        print "HS_REST_API: " + url_wml

        response = urllib2.urlopen(url_wml)
        print "downloading " + url_wml
        tif_obj = response.read()
        print "download complete"

        rslt_dic= zipSaveAs(filename, tif_obj, temp_dir, "zip_file.zip")
        zip_file_full_path = rslt_dic['zip_file_full_path']
        zip_crc = rslt_dic['crc']

        geosvr_url_base = getGeoSvrUrlBase(request)
        rslt = False
        rslt = addZippedTif2Geoserver(geosvr_url_base, 'admin', 'geoserver', res_id, zip_crc, zip_file_full_path, url_wml)

        if(rslt):
            map_view_options = getMapParas(geosvr_url_base, res_id, filename[:-4])
            context = {"map_view_options": map_view_options, "filename": filename}
        else:
            context = {}

        return render(request, 'raster_viewer/home.html', context)
    except:
        raise Http404("Cannot locate this raster file!")
    #finally:
        #if os.path.exists(temp_dir):
        #    shutil.rmtree(temp_dir)
        #    print temp_dir + " deleted"
        #    temp_dir=None


def request_demo(request):

    name = ''

    # Define Gizmo Options
    text_input_options_res_id = {'display_text': 'Res ID',
                          'name': 'res_id',
                            'initial': '6e3ffe34505e4510990e48c25ce0609b'}

    text_input_options_filename = {'display_text': 'Filename',
                          'name': 'filename',
                          'initial': 'logan.tif'
                          }


    # Create template context dictionary
    context = {'name': name,
               'text_input_options_res_id': text_input_options_res_id,
               'text_input_options_filename':text_input_options_filename
               }

    return render(request, 'raster_viewer/request_demo.html',context)