
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


function chkbox_callback(evt)
{

    var checkbox = evt.target;
    if (checkbox.name == "basemap")
    {
        openstreet_layer.setVisible(checkbox.checked)
    }
    else if (checkbox.name == "raster") {
        if (hs_layer != null) {
            hs_layer.setVisible(checkbox.checked)
        }
    }
}
chkbox_array = null

$(document).ready(function () {

    //$('#welcome-info').html('<p>This app redirects from either the <a href="../nfie-irods-explorer">Tethys NFIE iRODS Explorer</a> or ' +
    //        '<a href="https://www.hydroshare.org">HydroShare</a> and is ' +
    //        'used to view RAPID Output NetCDF files in an interactive way. Without being redirected from one ' +
    //        'of those sites, this app has little practical use since you cannot currently upload your own ' +
    //        'RAPID Output NetCDF file. Please click the links to the resources above to browse their ' +
    //        'file repositories. When locating an applicable NetCDF file, you will be given a "Open File ' +
    //        'in Tethys Viewer" link that will redirect you here to view the chosen file. Good luck!');
    chkbox_array = []
    chkbox = create_check_box("basemap", "basemap", "Base Map", true, chkbox_callback)
    chkbox_array.push(chkbox)
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
                    draw_raster(geosvr_url_base, ws_name, store_name, layer_name, minx, miny, maxx, maxy)
                    chkbox = create_check_box("raster", "raster", "Raster Resource Layer", true, chkbox_callback)
                    chkbox_array.push(chkbox)
                    document.getElementById('layer_control_div').appendChild(chkbox);
                    var br = document.createElement('br');
                    document.getElementById('layer_control_div').appendChild(br);
                }
                else
                {
                    popup_title = data["popup_title"]
                    popup_content = data["popup_content"]
                    alert(popup_content)
                    document.getElementById('data_loading_div').innerHTML = "";
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert("Ajax call failed.");
                document.getElementById('data_loading_div').innerHTML = "";
            }
        }); //$.ajax
    } // if
    else
    {
        popupDiv.modal('show');
    }

}) // $(document).ready(function ()


function draw_raster (geosvr_url_base, ws_name, store_name, layer_name, minx, miny, maxx, maxy)
{
    geo_server_wms = geosvr_url_base + '/geoserver/wms'
    //ws_name = 'b7822782896143ca8712395f6814c44b'
    //layer_name = 'logan'
    //ws_name = 'www.hydroshare.org'
    //layer_name = '877bf9ed9e66468cadddb229838a9ced'
    layer_id = ws_name + ':' + layer_name
    //var minx = -111.81761887121907
    //var miny = 41.662220544974005
    //var maxx = -111.45699925047543
    //var maxy = 42.112706148730034

    extent_4326 = [minx, miny, maxx, maxy]
    extent_3857 = ol.proj.transformExtent(extent_4326, 'EPSG:4326', 'EPSG:3857')
    center_3857 =[(extent_3857[0]+extent_3857[2])/2, (extent_3857[1]+extent_3857[3])/2]

    hs_layer = new ol.layer.Tile({
      source: new ol.source.TileWMS({
      url: geo_server_wms,
      params: {'LAYERS': layer_id, 'TILED': true},
      serverType: 'geoserver' }) })

    map.addLayer(hs_layer)
    map.getView().setCenter(center_3857)
    map.getView().setZoom(12)
}


var popupDiv = $('#welcome-popup');
var map_zoom = 8;
var openstreet_layer = new ol.layer.Tile({
          source: new ol.source.OSM()
        });

var mapQuest_layer = new ol.layer.Tile({
        source: new ol.source.MapQuest({layer: 'sat'}),
        visibility: false
                 });
var hs_layer;

slc_lonlat = [-111.8833, 40.75]
san_fran_lonlat = [-122.4167, 37.7833]
slc_3857 = ol.proj.transform(slc_lonlat, 'EPSG:4326', 'EPSG:3857');
san_fran_3857 = ol.proj.transform(san_fran_lonlat, 'EPSG:4326', 'EPSG:3857');

map = new ol.Map({
	layers: [ openstreet_layer],
	controls: ol.control.defaults(),
	target: 'map',
	view: new ol.View({
		center: san_fran_3857,
		zoom: map_zoom,
        projection: "EPSG:3857"
	})
});