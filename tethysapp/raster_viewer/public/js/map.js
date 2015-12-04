

$(document).ready(function () {

     $.ajax({
         type: 'GET',
         url: 'draw-raster',
         dataType: 'json',
         data: {
             'ok': 'ok'
         },
         success: function (data) {
             geosvr_url_base = data["geosvr_url_base"]
             ws_name = data["ws_name"]
             store_name = data["store_name"]
             layer_name = data["layer_name"]
             minx = data["minx"]
             miny = data["miny"]
             maxx = data["maxx"]
             maxy = data["maxy"]
             draw_raster (geosvr_url_base, ws_name, store_name, layer_name, minx, miny, maxx, maxy)
         },
         error: function (jqXHR, textStatus, errorThrown) {
             alert("Error");
         }
     }); //$.ajax




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
    map.getView().setZoom(10)
}



var map_zoom = 6;
var openstreet_layer = new ol.layer.Tile({
          source: new ol.source.OSM()
        });

var mapQuest_layer = new ol.layer.Tile({
        source: new ol.source.MapQuest({layer: 'sat'}),
        visibility: false
                 });

slc_lonlat = [-111.8833, 40.75]
slc_3857 = ol.proj.transform(slc_lonlat, 'EPSG:4326', 'EPSG:3857');
map = new ol.Map({
	layers: [ openstreet_layer],
	controls: ol.control.defaults(),
	target: 'map',
	view: new ol.View({
		center: slc_3857,
		zoom: map_zoom,
        projection: "EPSG:3857"
	})
});