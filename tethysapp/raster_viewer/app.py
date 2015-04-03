from tethys_apps.base import TethysAppBase, url_map_maker


class HydroShareRasterViewer(TethysAppBase):
    """
    Tethys app class for HydroShare Raster Viewer.
    """

    name = 'HydroShare Raster Viewer'
    index = 'raster_viewer:home'
    icon = 'raster_viewer/images/icon.gif'
    package = 'raster_viewer'
    root_url = 'raster-viewer'
    color = '#e74c3c'
        
    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (UrlMap(name='home',
                           url='raster-viewer',
                           controller='raster_viewer.controllers.home'),
        )

        return url_maps