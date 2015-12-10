
var popupDiv = $('#error-popup');
var popupDiv_welcome = $('#welcome-popup');

var map_zoom = 8;
var openstreet_layer = new ol.layer.Tile({
          source: new ol.source.OSM()
        });

var mapQuest_layer = new ol.layer.Tile({
        source: new ol.source.MapQuest({layer: 'sat'}),
        visibility: false
                 });
var hs_layer_tiled;
var hs_layer_single_tile;
var sld_body_temple = '<?xml version="1.0" encoding="ISO-8859-1"?><StyledLayerDescriptor version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
      + "<NamedLayer><Name>_WS_AND_LAYER_NAME_</Name><UserStyle><Name>mysld</Name><Title>Two color gradient</Title><FeatureTypeStyle><Rule><RasterSymbolizer><ColorMap>"
      + '<ColorMapEntry color="#_MIN_COLOR_" quantity="_MIN_VAL_" /><ColorMapEntry color="#_MAX_COLOR_" quantity="_MAX_VAL_" /></ColorMap></RasterSymbolizer></Rule></FeatureTypeStyle></UserStyle></NamedLayer></StyledLayerDescriptor>'

var layer_id;
var min_val=0;
var max_val=5000;
var min_2nd_val=0;
var max_2nd_val=5000;

slc_lonlat = [-111.8833, 40.75];
san_fran_lonlat = [-122.4167, 37.7833];
slc_3857 = ol.proj.transform(slc_lonlat, 'EPSG:4326', 'EPSG:3857');
san_fran_3857 = ol.proj.transform(san_fran_lonlat, 'EPSG:4326', 'EPSG:3857');

function refreshmap()
{
    if (map!=null && hs_layer_single_tile!=null)
    {
        var min_color = $('#min-color').val();
        var max_color = $('#max-color').val();

        sld_body = sld_body_temple.replace("_MIN_COLOR_", min_color);
        sld_body = sld_body.replace("_MAX_COLOR_", max_color);
        sld_body = sld_body.replace("_WS_AND_LAYER_NAME_", layer_id);
        if (min_2nd_val < min_val)
        {
            sld_body = sld_body.replace("_MIN_VAL_", min_val);
        }
        else
        {
            sld_body = sld_body.replace("_MIN_VAL_", min_2nd_val);
        }
        if (max_2nd_val < max_val)
        {
            sld_body = sld_body.replace("_MAX_VAL_", max_2nd_val);
        }
        else
        {
            sld_body = sld_body.replace("_MAX_VAL_", max_val);
        }

        console.log(sld_body)


        var oseamNew = hs_layer_single_tile.getSource();
	    oseamNew.updateParams({'sld_body': sld_body});
	    map.render();
    }
}

function resetmap()
{
    if (map!=null && hs_layer_single_tile!=null)
    {
        var oseamNew = hs_layer_single_tile.getSource();
	    oseamNew.updateParams({'styles': 'raster', 'sld_body': null});
	    map.render();
    }
}

function format_coord(coord)
{
    func1 = ol.coordinate.createStringXY(4)
    lon_lat_str = func1(coord)
    var lon_lat_array = lon_lat_str.split(",");
    output = "Lon = " + lon_lat_array[0] + ", Lat = " + lon_lat_array[1]

    return output
}


var mousePositionControl = new ol.control.MousePosition({
        className: 'custom-mouse-position',
        projection: 'EPSG:4326',
        target: document.getElementById('location'),
        coordinateFormat: format_coord,
        undefinedHTML: 'Lon = NaN, Lat = NaN'
      });

var map = new ol.Map({
	layers: [ openstreet_layer],
    controls: ol.control.defaults({
          attribution: false
        }).extend([mousePositionControl]),
	target: 'map',
	view: new ol.View({
		center: san_fran_3857,
		zoom: map_zoom,
        projection: "EPSG:3857"
	})
});

map.getView().on('change:resolution', function(evt) {
        var resolution = evt.target.get('resolution');
        var units = map.getView().getProjection().getUnits();
        var dpi = 25.4 / 0.28;
        var mpu = ol.proj.METERS_PER_UNIT[units];
        var scale = resolution * mpu * 39.37 * dpi;
        if (scale >= 9500 && scale <= 950000) {
          scale = Math.round(scale / 1000) + "K";
        } else if (scale >= 950000) {
          scale = Math.round(scale / 1000000) + "M";
        } else {
          scale = Math.round(scale);
        }
        document.getElementById('scale').innerHTML = "Scale = 1 : " + scale;
      });

//
//map.on('singleclick', function(evt) {
//        document.getElementById('nodelist').innerHTML = "Loading... please wait...";
//        var view = map.getView();
//        var viewResolution = view.getResolution();
//        var source = hs_layer_single_tile.get('visible') ? hs_layer_single_tile.getSource() : null;
//        if (source != null)
//        {
//            var url = source.getGetFeatureInfoUrl(
//          evt.coordinate, viewResolution, view.getProjection(),
//          {'INFO_FORMAT': 'application/json', 'FEATURE_COUNT': 50});
//            console.log(url)
//            if (url) {
//
//
//              document.getElementById('nodelist').innerHTML = '<iframe seamless src="' + url + '"></iframe>';
//            }
//        }
//      });


$('#btn-testing-url').on('click', function () {
        res_id = $('#res-id').val()
        window.location = "/apps/raster-viewer/?src=hs&usr=demo&res_id=" + res_id
});

$(document).ready(function () {

    //$('#welcome-info').html('<p>This app redirects from either the <a href="../nfie-irods-explorer">Tethys NFIE iRODS Explorer</a> or ' +
    //        '<a href="https://www.hydroshare.org">HydroShare</a> and is ' +
    //        'used to view RAPID Output NetCDF files in an interactive way. Without being redirected from one ' +
    //        'of those sites, this app has little practical use since you cannot currently upload your own ' +
    //        'RAPID Output NetCDF file. Please click the links to the resources above to browse their ' +
    //        'file repositories. When locating an applicable NetCDF file, you will be given a "Open File ' +
    //        'in Tethys Viewer" link that will redirect you here to view the chosen file. Good luck!');

    chkbox = create_check_box("basemap", "basemap", "Base Map", true, chkbox_callback)
    document.getElementById('layer_control_div').appendChild(chkbox);
    var br = document.createElement('br');
    document.getElementById('layer_control_div').appendChild(br);

    if ($('#success_flag').text().indexOf("true") > -1)
    {
        var wait_text = "<br><strong>Loading data...</strong><br>" +
        "<img src='/static/raster_viewer/images/globe_spinning_small.gif'>";
        document.getElementById('data_loading_div').innerHTML = wait_text;

        $.ajax({
            type: 'GET',
            url: 'draw-raster',
            dataType: 'json',
            data: {
                'ok': 'ok'
            },
            success: function (data) {

                if (data["success"])
                {
                    document.getElementById('data_loading_div').innerHTML = "";
                    geosvr_url_base = data["geosvr_url_base"]
                    ws_name = data["ws_name"]
                    store_name = data["store_name"]
                    layer_name = data["layer_name"]
                    minx = data["minx"]
                    miny = data["miny"]
                    maxx = data["maxx"]
                    maxy = data["maxy"]
                    band_stat_info_array = data["band_stat_info_array"]
                    json_response = data["json_response"]
                    draw_raster(geosvr_url_base, ws_name, store_name, layer_name, minx, miny, maxx, maxy, band_stat_info_array, json_response)
                    chkbox = create_check_box("raster", "raster", "Raster Resource Layer", true, chkbox_callback)
                    document.getElementById('layer_control_div').appendChild(chkbox);
                    var br = document.createElement('br');
                    document.getElementById('layer_control_div').appendChild(br);
                }
                else
                {
                    popup_title = data["popup_title"]
                    popup_content = data["popup_content"]
                    $('#error-title').html(popup_title)
                    $('#error-info').html(popup_content)
                    popupDiv.modal("show")

                    //alert(popup_content)
                    document.getElementById('data_loading_div').innerHTML = "";
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                $('#error-title').html("Error")
                $('#error-info').html("Looks like this is a large size raster resource. Please try refreshing this page later.")
                popupDiv.modal("show")
                console.log(textStatus, errorThrown);
                document.getElementById('data_loading_div').innerHTML = "";
            }
        }); //$.ajax
    } // if
    else if ($('#success_flag').text().indexOf("welcome") > -1)
    {
        popupDiv_welcome.modal('show');
    }
    else // false
    {
        popupDiv.modal('show');
    }

}) // $(document).ready(function ()


function create_check_box(name, vaule, text, check_state, fn_callback)
{
    // styling of this checkbox control is at raster_viewer/public/css/main.css
    var label= document.createElement("label");
    var description = document.createTextNode(text);
    var checkbox = document.createElement("input");

    checkbox.type = "checkbox";    // make the element a checkbox
    checkbox.name = name;      // give it a name we can check on the server side
    checkbox.value = vaule;         // make its value "pair"
    checkbox.checked = check_state;
    checkbox.addEventListener('change', fn_callback);

    label.appendChild(checkbox);   // add the box to the element
    label.appendChild(description);// add the description to the element
    return label
}

function chkbox_callback(evt){

    var checkbox = evt.target;
    if (checkbox.name == "basemap")
    {
        openstreet_layer.setVisible(checkbox.checked)
    }
    else if (checkbox.name == "raster") {
        if (hs_layer_single_tile != null) {
            hs_layer_single_tile.setVisible(checkbox.checked)
        }
    }
}


function draw_raster (geosvr_url_base, ws_name, store_name, layer_name, minx, miny, maxx, maxy, band_stat_info_array, json_response)
{

    if (band_stat_info_array!=null && band_stat_info_array instanceof Array)
    {
        if (band_stat_info_array.length != 1)
        {
            $('#color-picker').css('visibility', 'hidden');
            console.log("multiple bands or 0 brand", band_stat_info_array.length)
        }
        else
        {
            $('#color-picker').css('visibility', 'visible');
            band_info = band_stat_info_array[0]
            min_val = band_info["min_val"]
            max_val = band_info["max_val"]
            mean_val = band_info["mean_val"]
            std_val = band_info["std_val"]
            min_2nd_val = band_info["min_2nd_val"]
            max_2nd_val = band_info["max_2nd_val"]
            no_data_val =  band_info["no_data_val"]

            console.log("min_val: ",min_val)
            console.log("max_val: ", max_val)
            console.log("mean_val: ",mean_val)
            console.log("std_val: ", std_val)
            console.log("min_2nd_val: ",min_2nd_val)
            console.log("max_2nd_val: ", max_2nd_val)
            console.log("no_data_val: ", no_data_val)

            if (json_response != null)
            {
                var band_count = json_response["coverage"]["dimensions"]["coverageDimension"].length;
                if ( band_count> 1)
                 {
                     console.log('json_response["coverage"]["dimensions"]["coverageDimension"].length: ', band_count)
                     $('#color-picker').css('visibility', 'hidden');
                 }
            }
        }
    }
    else
    {
        $('#color-picker').css('visibility', 'hidden');
    }


    geo_server_wms = geosvr_url_base + '/geoserver/wms'
    layer_id = ws_name + ':' + layer_name
    extent_4326 = [minx, miny, maxx, maxy]
    extent_3857 = ol.proj.transformExtent(extent_4326, 'EPSG:4326', 'EPSG:3857')
    center_3857 =[(extent_3857[0]+extent_3857[2])/2, (extent_3857[1]+extent_3857[3])/2]

    hs_layer_tiled = new ol.layer.Tile({
      source: new ol.source.TileWMS({
      url: geo_server_wms,
      params: {'LAYERS': layer_id, 'TILED': true},
      serverType: 'geoserver' }) })

    sld_content = "<StyledLayerDescriptor xmlns='http://www.opengis.net/sld' xmlns:ogc='http://www.opengis.net/ogc' xmlns:xlink='http://www.w3.org/1999/xlink' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' version='1.0.0' xsi:schemaLocation='http://www.opengis.net/sld StyledLayerDescriptor.xsd'> <NamedLayer> <Name>www.hydroshare.org:e660640a7b084794aa2d70dc77cfa67b</Name> <UserStyle>     <Name>my_sld</Name> <Title>SLD Cook Book: Two color gradient</Title> <FeatureTypeStyle> <Rule> <RasterSymbolizer> <ColorMap> <ColorMapEntry color='#008000' quantity='70'/> <ColorMapEntry color='#663333' quantity='256'/> </ColorMap> </RasterSymbolizer> </Rule> </FeatureTypeStyle> </UserStyle> </NamedLayer> </StyledLayerDescriptor>"
    encode_sld_content = encodeURI(sld_content)

    hs_layer_single_tile = new ol.layer.Image({
        source: new ol.source.ImageWMS({
          ratio: 1,
          url: geo_server_wms,
          params: {
                LAYERS: layer_id,
                //STYLES: 'my_sld',
                //sld: 'http://127.0.0.1:8080/geoserver/www/styles/sld.sld'
                //"sld_body": sld_body
                  }
        })
      });

    map.addLayer(hs_layer_single_tile)
    //map.addLayer(hs_layer_tiled)
    map.getView().setCenter(center_3857)
    map.getView().setZoom(12)
}