from django.shortcuts import render
from django.http import Http404
import urllib2
#from tethys_apps.base import TethysAppBase, SpatialDatasetService
from tethys_dataset_services.engines import GeoServerSpatialDatasetEngine
import zipfile
from oauthlib.oauth2 import TokenExpiredError
from hs_restclient import HydroShare, HydroShareAuthOAuth2, HydroShareNotAuthorized
from django.contrib.auth.decorators import login_required
from social_auth.models import UserSocialAuth
from django.conf import settings
from django.http import JsonResponse


import tempfile
import shutil
import os
from django.contrib.sites.shortcuts import get_current_site
from utilities import *

hs_instance_name = "www"
hs_hostname = "{0}.hydroshare.org".format(hs_instance_name)

#geosvr_url_base='https://appsdev.hydroshare.org:8181'
#geosvr_url_base='https://apps.hydroshare.org:8181'
geosvr_url_base='http://127.0.0.1:8181'

geosvr_user='admin'
geosvr_pw='geoserver'

extract_base_path = '/tmp'

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

@login_required()
def home(request):

    # import sys
    # sys.path.append("/home/drew/pycharm-debug")
    # import pydevd
    # pydevd.settrace('172.17.42.1', port=21000, suspend=False)

    if request.GET:
        res_id = request.GET["res_id"]
        src = request.GET['src']
        usr = request.GET['usr']

        request.session['res_id'] = res_id
        request.session['src'] = src
        request.session['usr'] = usr
    try:
        # res_id = "b7822782896143ca8712395f6814c44b"
        # res_id = "877bf9ed9e66468cadddb229838a9ced"
        # res_id = "e660640a7b084794aa2d70dc77cfa67b"
        # private res
        # res_id = "a4a4bca8369e4c1e88a1b35b9487e731"
        # request.session['res_id'] = res_id

        hs = getOAuthHS(request)
        res_landing_page = "https://{0}.hydroshare.org/resource/{1}/".format(hs_instance_name, res_id)
        resource_md = hs.getSystemMetadata(res_id)
        resource_type = resource_md.get("resource_type", "")
        resource_title = resource_md.get("resource_title", "")
        hs_hostname = "{0}.hydroshare.org".format(hs_instance_name)
        if resource_type.lower() != "rasterresource":
            raise Http404("Not RasterResource")

        context = {}

        return render(request, 'raster_viewer/home.html', context)
    except TokenExpiredError as e:
        # TODO: redirect back to login view, giving this view as the view to return to
        #logger.error("TokenExpiredError: TODO: redirect to login view")
        raise Http404("Token Expired")
    except HydroShareNotAuthorized as e:
        raise Http404("Your have no permission on this resource")
    except:
        raise


def getOAuthHS(request):
    try:
        client_id = getattr(settings, "SOCIAL_AUTH_HYDROSHARE_KEY", "None")
        client_secret = getattr(settings, "SOCIAL_AUTH_HYDROSHARE_SECRET", "None")
        token = request.user.social_auth.get(provider='hydroshare').extra_data['token_dict']
        auth = HydroShareAuthOAuth2(client_id, client_secret, token=token)
        hs = HydroShare(auth=auth, hostname=hs_hostname)
        return hs
    except:
        return None


def draw_raster(request):

    res_id = request.session.get("res_id", None)
    temp_res_extracted_dir = None
    temp_dir = None
    map_dict = {}
    map_dict["success"] = False

    try:
        if res_id is not None:
            hs = getOAuthHS(request)
            map_dict = getMapParas(geosvr_url_base=geosvr_url_base, wsName=hs_hostname, store_id=res_id, \
                        layerName=res_id, un=geosvr_user, pw=geosvr_pw)

            if map_dict["success"] == False:

                temp_dir = tempfile.mkdtemp()
                hs.getResource(res_id, destination=extract_base_path, unzip=True)
                temp_res_extracted_dir = extract_base_path + '/' + res_id
                contents_folder = extract_base_path + '/' + res_id + '/' + res_id +'/data/contents/'
                file_list = os.listdir(contents_folder)

                tif_fn = file_list[0] # tif full name
                tif_fp = contents_folder + tif_fn # tif full path
                tif_hdl = open(tif_fp, 'rb')
                tif_obj = tif_hdl.read()
                rslt_dic = zipSaveAs(res_id + ".tif", tif_obj, temp_dir, "zip_file.zip")

                zip_file_full_path = rslt_dic['zip_file_full_path']
                zip_crc = rslt_dic['crc']

                rslt = addZippedTif2Geoserver(geosvr_url_base=geosvr_url_base, uname=geosvr_user, upwd=geosvr_pw, ws_name=hs_hostname, \
                                              store_name=res_id, zippedTif_full_path=zip_file_full_path, res_url=hs_hostname)
                if(rslt):
                    map_dict = getMapParas(geosvr_url_base=geosvr_url_base, wsName=hs_hostname, store_id=res_id, \
                                                   layerName=res_id, un=geosvr_user, pw=geosvr_pw)

            map_dict['geosvr_url_base'] = geosvr_url_base
            map_dict['ws_name'] = hs_hostname
            map_dict['store_name'] = res_id
            map_dict['layer_name'] = res_id

        return JsonResponse(map_dict)

    except TokenExpiredError as e:
        # TODO: redirect back to login view, giving this view as the view to return to
        #logger.error("TokenExpiredError: TODO: redirect to login view")
        raise Http404("Token Expired")
    except HydroShareNotAuthorized as e:
        raise Http404("Your have no permission on this resource")
    except:
        raise
    finally:
        if temp_dir is not None:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print temp_dir + " deleted"
        if temp_res_extracted_dir is not None:
            if os.path.exists(temp_res_extracted_dir):
                shutil.rmtree(temp_res_extracted_dir)
                print temp_res_extracted_dir + " deleted"
