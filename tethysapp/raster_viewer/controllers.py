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


#Base_Url_HydroShare REST API
url_base='http://{0}.hydroshare.org/hsapi/resource/{1}/files/{2}'
geosvr_url_base='http://127.0.0.1:8181'
##Call in Rest style
def restcall(request,branch,res_id,filename):
    try:
        print "restcall", branch, res_id, filename
        url_wml = url_base.format(branch, res_id, filename)

        response = urllib2.urlopen(url_wml)

        html = response.read()

        #timeseries_plot = chartPara(html, filename)
        timeseries_plot = {}

        context = {"timeseries_plot": timeseries_plot}
    except:
        raise Http404("Cannot locate this resource file")

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

    filename= None
    res_id = None
    url_wml = None
    branch = None
    # make a temp dir
    temp_dir = tempfile.mkdtemp()

    current_site=get_current_site(request);

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


        if url_wml is None:
            res_id = "6e3ffe34505e4510990e48c25ce0609b"
            branch = "alpha"
            filename = 'logan.tif'

        url_wml = url_base.format(branch,res_id,filename)

        print "HS_REST_API: " + url_wml

        response = urllib2.urlopen(url_wml)

        print "downloading " + url_wml
        tif_obj = response.read()
        print "download complete"

        #init a mem space
        in_memory_zip = StringIO()
        # Create a Zip Helper Obj initialed with existing mem space
        zip_helper = zipfile.ZipFile(in_memory_zip, "a", zipfile.ZIP_DEFLATED, False)
        # zip content file name
        zip_content_fn = filename
        # path to the file will be zipped
        zip_content_full_path = tif_obj
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

        zip_filename = "zip_file.zip"
        zip_file_full_path = temp_dir+'/'+zip_filename
        f = file(zip_file_full_path, "w")
        #Writes the mem space 'in_memory_zip' to a file.
        f.write(in_memory_zip.getvalue())
        f.close()
        print ("zip file saved at : " + zip_file_full_path)

        geosvr_url_full = geosvr_url_base+"/geoserver/rest/"

        print "Connect to Geoserver"
        spatial_dataset_engine = GeoServerSpatialDatasetEngine(endpoint=geosvr_url_full, username='admin', password='geoserver')
        print "Connected"

        ws_name = res_id
        response = None
        result = spatial_dataset_engine.create_workspace(workspace_id=ws_name, uri=url_wml)
        if result['success']:
            print "Create workspace " + res_id + " successfully"
        else:
            print "Create workspace " + res_id + " failed"
        print result

        store_name = zip_crc
        store_id = ws_name+":"+store_name
        coverage_file=zip_file_full_path
        result = None
        result = spatial_dataset_engine.create_coverage_resource(store_id=store_id, coverage_file=coverage_file, coverage_type='geotiff')
        if result['success']:
            print "Create store " + store_name + " successfully"
        else:
            print "Create store " + store_name + " failed"
        print result

        spatial_dataset_engine.list_layers(debug=True)



        geosvr_ulr_wms = geosvr_url_base+"/geoserver/wms/"
        layer = res_id + ":" + filename[:-4]
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
#'http://demo.opengeo.org:80/geoserver/maps/wms'
#dark

        # map_view_options = {'height': '400px',
        #             'width': '100%',
        #             'controls': ['ZoomSlider',
        #                          'Rotate',
        #                          'FullScreen',
        #                          'ScaleLine',
        #                          {'ZoomToExtent': {'projection': 'EPSG:4326',
        #                                            'extent': [-135, 22, -55, 54]}},
        #                          {'MousePosition': {'projection': 'EPSG:4326'}},
        #             ],
        #             'layers': [{'WMS': {'url': 'http://demo.opengeo.org/geoserver/wms',
        #                                 'params': {'LAYERS': 'topp:states'},
        #                                 'serverType': 'geoserver'}
        #                         },
        #             ],
        #             'view': {'projection': 'EPSG:4326',
        #                      'center': [-100, 40], 'zoom': 3.5,
        #                      'maxZoom': 18, 'minZoom': 3},
        #             'base_map': 'OpenStreetMap'
        #}

        context = {"map_view_options": map_view_options}
        return render(request, 'raster_viewer/home.html', context)
    except:
        return render(request, 'raster_viewer/home.html', context)
        raise Http404("Cannot locate this raster file!")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print temp_dir+ " deleted"
            temp_dir=None
