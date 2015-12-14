from django.shortcuts import render
from django.http import Http404
import urllib2
#from tethys_apps.base import TethysAppBase, SpatialDatasetService
from tethys_dataset_services.engines import GeoServerSpatialDatasetEngine
import zipfile
from oauthlib.oauth2 import TokenExpiredError
from hs_restclient import HydroShare, HydroShareAuthOAuth2, HydroShareNotAuthorized, HydroShareNotFound
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from social_auth.models import UserSocialAuth
from django.conf import settings
from django.http import JsonResponse


import tempfile
import shutil
import os
from django.contrib.sites.shortcuts import get_current_site
from utilities import *
from .model import engine, SessionMaker, RasterStatistics

###########
# geosvr_url_base='http://apps.hydroshare.org:8181'
# geosvr_url_base='http://appsdev.hydroshare.org:8181'
# geosvr_url_base = 'http://127.0.0.1:8181'
geosvr_url_base = getattr(settings, "GEOSERVER_URL_BASE", "http://127.0.0.1:8181")
# geosvr_user = 'admin'
geosvr_user = getattr(settings, "GEOSERVER_USER_NAME", "admin")
# geosvr_pw = 'geoserver'
geosvr_pw = getattr(settings, "GEOSERVER_USER_PASSWORD", "geoserver")

hs_instance_name = "www"

# tethys_url_base = "https://apps.hydroshare.org"
# tethys_url_base = "https://appsdev.hydroshare.org"
# tethys_url_base = "http://127.0.0.1:8000"

###########

hs_hostname = "{0}.hydroshare.org".format(hs_instance_name)
popup_title_WELCOME = "Welcome to the HydroShare Raster Viewer"
popup_title_ERROR = "Error"
popup_title_WARNING = "Warning"

popup_content_NOT_LAUNCHED_FROM_HYDROSHARE = "This app should be launched from <a href='https://{0}.hydroshare.org/my-resources/'>HydroShare</a>.".format(hs_instance_name)
popup_content_UNKNOWN_ERROR = "Sorry, we are having an internal error!"
popup_content_NO_PERMISSION = "Sorry, you have no permission on this resource."
popup_content_NOT_FOUND = "Sorry, we cannot find this resource on HydroShare."
popup_content_ANONYMOUS_USER = "Please <a href='https://{0}.hydroshare.org/accounts/login/'>sign in HydroShare</a> and then launch this app again.".format(hs_instance_name)
popup_content_TOKEN_EXPIRED = "Login timed out! Please <a href='/oauth2/login/hydroshare'>sign in with your HydroShare account</a> again."
popup_content_NOT_OAUTH_LOGIN = "Please sign out and re-sign in with your HydroShare account."
popup_content_NOT_RASTER_RESOURCE = "Sorry, this resource is not a HydroShare Raster Resource."
popup_content_NO_RESOURCEID_IN_SESSION = "Sorry, the resource id is missing."
popup_content_INVALID_GEOTIFF = "This resource file is not a valid GeoTIFF or has no projection information."

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


    popup_title = popup_title_WELCOME
    popup_content = popup_content_NOT_LAUNCHED_FROM_HYDROSHARE
    success_flag = "true"
    resource_title = None

    if request.GET:
        res_id = request.GET.get("res_id", None)
        src = request.GET.get('src', None)
        usr = request.GET.get('usr', None)

        if res_id is None or src is None or src != "hs" or usr is None:
            success_flag = "welcome"
        elif usr.lower() == "anonymous":
            popup_title = popup_title_ERROR
            popup_content = popup_content_ANONYMOUS_USER
            success_flag = "false"
        else:
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

                if resource_type.lower() != "rasterresource":
                    popup_title = popup_title_ERROR
                    popup_content = popup_content_NOT_RASTER_RESOURCE
                    success_flag = "false"
                    #raise Http404("Not RasterResource")
            except ObjectDoesNotExist as e:
                print str(e)
                popup_title = popup_title_ERROR
                popup_content = popup_content_NOT_OAUTH_LOGIN
                success_flag = "false"
            except TokenExpiredError as e:
                print str(e)
                popup_title = popup_title_WARNING
                popup_content = popup_content_TOKEN_EXPIRED
                success_flag = "false"
                # raise Http404("Token Expired")
            except HydroShareNotAuthorized as e:
                print str(e)
                popup_title = popup_title_ERROR
                popup_content = popup_content_NO_PERMISSION
                success_flag = "false"
                # raise Http404("Your have no permission on this resource")
            except HydroShareNotFound as e:
                print str(e)
                popup_title = popup_title_ERROR
                popup_content = popup_content_NOT_FOUND
                success_flag = "false"
            except Exception as e:
                print "unknown error"
                print str(e)
                popup_title = popup_title_ERROR
                popup_content = popup_content_UNKNOWN_ERROR
                success_flag = "false"
                # raise
    else:
        success_flag = "welcome"

    context = {"popup_title": popup_title,
               "popup_content": popup_content,
               "success_flag": success_flag,
               'resource_title': resource_title,
            }

    return render(request, 'raster_viewer/home.html', context)


def getOAuthHS(request):

    client_id = getattr(settings, "SOCIAL_AUTH_HYDROSHARE_KEY", None)
    client_secret = getattr(settings, "SOCIAL_AUTH_HYDROSHARE_SECRET", None)

    # this line will throw out from django.core.exceptions.ObjectDoesNotExist if current user is not signed in via HydroShare OAuth
    token = request.user.social_auth.get(provider='hydroshare').extra_data['token_dict']

    auth = HydroShareAuthOAuth2(client_id, client_secret, token=token)
    hs = HydroShare(auth=auth, hostname=hs_hostname)
    return hs

def draw_raster(request):

    res_id = request.session.get("res_id", None)
    temp_res_extracted_dir = None
    temp_dir = None
    map_dict = {}
    map_dict["success"] = False
    band_stat_info_array = []

    try:
        if res_id is not None:

            map_dict = getMapParas(geosvr_url_base=geosvr_url_base, wsName=hs_hostname, store_id=res_id, \
                        layerName=res_id, un=geosvr_user, pw=geosvr_pw)

            if map_dict["success"]: # find cached raster
                session = SessionMaker()
                # res_1 = RasterStatistics(res_id="res_id_1",
                #            min_val=1,
                #            max_val=10)
                # session.add(res_1)
                # session.commit()
                band_stat_info_array = []
                raster_stat_array = session.query(RasterStatistics).all()
                for r_stat in raster_stat_array:
                    if r_stat.res_id == res_id:
                        band_min_val = r_stat.min_val
                        band_max_val = r_stat.max_val
                        band_min_2nd_val = r_stat.min_2nd_val
                        band_max_2nd_val = r_stat.max_2nd_val
                        band_mean_val = r_stat.mean_val
                        band_std_val = r_stat.std_val
                        band_id = r_stat.band_id
                        band_name = r_stat.band_name
                        band_no_data_val = r_stat.no_data_val

                        band_stat_info={}
                        band_stat_info["min_val"] = band_min_val
                        band_stat_info["max_val"] = band_max_val
                        band_stat_info["min_2nd_val"] = band_min_2nd_val
                        band_stat_info["max_2nd_val"] = band_max_2nd_val
                        band_stat_info["mean_val"] = band_mean_val
                        band_stat_info["std_val"] = band_std_val
                        band_stat_info["band_id"] = band_id
                        band_stat_info["band_name"] = band_name
                        band_stat_info["no_data_val"] = band_no_data_val
                        band_stat_info_array.append(band_stat_info)
                print("---------------------Load band_stat_info from DB-------------------------------")
                print band_stat_info_array

            else: # no cached raster or raster has no projection

                session = SessionMaker()
                raster_stat_array = session.query(RasterStatistics).all()
                for r_stat in raster_stat_array:
                    if r_stat.res_id == res_id:
                        session.delete(r_stat)
                        print("---------------------Delete leftover band_stat_info from DB-------------------------------")
                session.commit()

                hs = getOAuthHS(request)
                print ("Begin download res: {0}".format(res_id))
                hs.getResource(res_id, destination=extract_base_path, unzip=True)
                print ("End download res")
                temp_res_extracted_dir = extract_base_path + '/' + res_id
                print temp_res_extracted_dir
                contents_folder = extract_base_path + '/' + res_id + '/' + res_id +'/data/contents/'
                print contents_folder
                file_list = os.listdir(contents_folder)

                tif_fn = file_list[0] # tif full name
                for fn in file_list:
                    if fn.endswith(".tif"):
                        tif_fn = fn
                        break

                tif_fp = contents_folder + tif_fn # tif full path
                band_stat_info_array = extract_geotiff_stat_info(tif_fp)

                print band_stat_info_array
                if len(band_stat_info_array) > 0:
                    session = SessionMaker()
                    for band_info in band_stat_info_array:
                        band_info_db = RasterStatistics(res_id=res_id,
                                                    min_val=band_info["min_val"],
                                                    max_val=band_info["max_val"],
                                                    mean_val=band_info["mean_val"],
                                                    std_val=band_info["std_val"],
                                                    min_2nd_val=band_info["min_2nd_val"],
                                                    max_2nd_val=band_info["max_2nd_val"],
                                                    band_id=band_info["band_id"],
                                                    band_name=str(band_info["band_id"]),
                                                    hs_branch=hs_instance_name,
                                                    no_data_val=band_info["no_data_val"])
                        session.add(band_info_db)
                    session.commit()
                    print("--------------- Save to DB : band_stat_info  ------------")

                tif_hdl = open(tif_fp, 'rb')
                tif_obj = tif_hdl.read()
                temp_dir = tempfile.mkdtemp()
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
            map_dict['band_stat_info_array'] = band_stat_info_array
            if map_dict["success"] == False:
                map_dict['popup_title'] = popup_title_ERROR
                map_dict['popup_content'] = popup_content_INVALID_GEOTIFF

        else:
            map_dict["success"] = False
            map_dict['popup_title'] = popup_title_ERROR
            map_dict['popup_content'] = popup_content_NO_RESOURCEID_IN_SESSION


    except ObjectDoesNotExist as e:
        print str(e)
        popup_title = popup_title_ERROR
        popup_content = popup_content_NOT_OAUTH_LOGIN
        map_dict["success"] = False
        map_dict['popup_title'] = popup_title
        map_dict['popup_content'] = popup_content
    except TokenExpiredError as e:
        print str(e)
        popup_title = popup_title_WARNING
        popup_content = popup_content_TOKEN_EXPIRED
        map_dict["success"] = False
        map_dict['popup_title'] = popup_title
        map_dict['popup_content'] = popup_content
        # raise Http404("Token Expired")
    except HydroShareNotAuthorized as e:
        print str(e)
        popup_title = popup_title_ERROR
        popup_content = popup_content_NO_PERMISSION
        map_dict["success"] = False
        map_dict['popup_title'] = popup_title
        map_dict['popup_content'] = popup_content
        # raise Http404("Your have no permission on this resource")
    except HydroShareNotFound as e:
        print str(e)
        popup_title = popup_title_ERROR
        popup_content = popup_content_NOT_FOUND
        map_dict["success"] = False
        map_dict['popup_title'] = popup_title
        map_dict['popup_content'] = popup_content
    except Exception as e:
        print "unknown error"
        print str(e)
        popup_title = popup_title_ERROR
        popup_content = popup_content_UNKNOWN_ERROR
        map_dict["success"] = False
        map_dict['popup_title'] = popup_title
        map_dict['popup_content'] = popup_content
        # raise
    finally:
        if temp_dir is not None:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print temp_dir + " deleted"
        if temp_res_extracted_dir is not None:
            if os.path.exists(temp_res_extracted_dir):
                shutil.rmtree(temp_res_extracted_dir)
                print temp_res_extracted_dir + " deleted"
        return JsonResponse(map_dict)
