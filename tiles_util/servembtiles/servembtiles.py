#!/usr/bin/env python3
"""
mbtiles WSGI application

MBTiles is a specification for storing tiled map data in SQLite databases for immediate usage and for transfer.
From:
https://github.com/mapbox/mbtiles-spec
"""
import os
import json
import sqlite3
import mimetypes
import logging
from wsgiref.util import shift_path_info


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

try:
    from settings import MBTILES_ABSPATH, MBTILES_TILE_EXT, MBTILES_ZOOM_OFFSET, MBTILES_HOST, MBTILES_PORT, MBTILES_SERVE, USE_OSGEO_TMS_TILE_ADDRESSING
except ImportError:
    logger.warn("settings.py not set, may not be able to run via a web server (apache, nginx, etc)!")
    MBTILES_ABSPATH = None
    MBTILES_TILE_EXT = '.png'
    MBTILES_ZOOM_OFFSET = 0
    MBTILES_HOST = 'localhost'
    MBTILES_PORT = 8005
    MBTILES_SERVE = False
    USE_OSGEO_TMS_TILE_ADDRESSING = True

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")


class MBTilesFileNotFound(Exception):
    pass


class InvalidImageExtension(Exception):
    pass


class MBTilesApplication:
    """
    Serves rendered tiles within the given .mbtiles (sqlite3) file defined in settings.MBTILES_ABSPATH

    Refer to the MBTiles specification at:
    https://github.com/mapbox/mbtiles-spec
    """

    def __init__(self, mbtiles_filepath, tile_image_ext='.png', zoom_offset=0):
        if mbtiles_filepath is None or not os.path.exists(mbtiles_filepath):
            raise MBTilesFileNotFound(mbtiles_filepath)

        if tile_image_ext not in SUPPORTED_IMAGE_EXTENSIONS:
            raise InvalidImageExtension("{} not in {}!".format(tile_image_ext, SUPPORTED_IMAGE_EXTENSIONS))

        self.mbtiles_db = sqlite3.connect(
            "file:{}?mode=ro".format(mbtiles_filepath),
            check_same_thread=False, uri=True)
        self.tile_image_ext = tile_image_ext
        self.tile_content_type = mimetypes.types_map[tile_image_ext.lower()]
        self.zoom_offset = zoom_offset
        self.maxzoom = None
        self.minzoom = None

        self._populate_supported_zoom_levels()

    def _populate_supported_zoom_levels(self):
        """
        Query the metadata table and obtain max/min zoom levels,
        setting to self.minzoom, self.maxzoom as integers
        :return: None
        """
        query = 'SELECT name, value FROM metadata WHERE name="minzoom" OR name="maxzoom";'
        # add maxzoom, minzoom to instance
        for name, value in self.mbtiles_db.execute(query):
            setattr(self, name.lower(), max(int(value) - self.zoom_offset, 0))

    def __call__(self, environ, start_response):
        if environ['REQUEST_METHOD'] == 'GET':
            uri_field_count = len(environ['PATH_INFO'].split('/'))
            base_uri = shift_path_info(environ)

            # handle 'metadata' requests
            if base_uri == 'metadata':
                query = 'SELECT * FROM metadata;'
                metadata_results = self.mbtiles_db.execute(query).fetchall()
                if metadata_results:
                    status = '200 OK'
                    response_headers = [('Content-type', 'application/json')]
                    start_response(status, response_headers)
                    json_result = json.dumps(metadata_results, ensure_ascii=False)
                    return [json_result.encode("utf8"),]
                else:
                    status = '404 NOT FOUND'
                    response_headers = [('Content-type', 'text/plain; charset=utf-8')]
                    start_response(status, response_headers)
                    return ['"metadata" not found in configured .mbtiles file!'.encode('utf8'), ]

            # handle tile request
            elif uri_field_count >= 3:  # expect:  zoom, x & y
                try:
                    zoom = int(base_uri)
                    if None not in (self.minzoom, self.maxzoom) and not (self.minzoom <= zoom <= self.maxzoom):
                        status = "404 Not Found"
                        response_headers = [('Content-type', 'text/plain; charset=utf-8')]
                        start_response(status, response_headers)
                        return ['Requested zoomlevel({}) Not Available! Valid range minzoom({}) maxzoom({}) PATH_INFO: {}'.format(zoom,
                                                                                                                                   self.minzoom,
                                                                                                                                   self.maxzoom,
                                                                                                                                   environ['PATH_INFO']).encode('utf8')]
                    zoom += self.zoom_offset
                    x = int(shift_path_info(environ))
                    y, ext = shift_path_info(environ).split('.')
                    y = int(y)
                except ValueError as e:
                    status = "400 Bad Request"
                    response_headers = [('Content-type', 'text/plain; charset=utf-8')]
                    start_response(status, response_headers)
                    return ['Unable to parse PATH_INFO({}), expecting "z/x/y.(png|jpg)"'.format(environ['PATH_INFO']).encode('utf8'), ' '.join(i for i in e.args).encode('utf8')]

                query = 'SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?;'
                if not USE_OSGEO_TMS_TILE_ADDRESSING:
                    # adjust y to use XYZ google addressing
                    ymax = 1 << zoom
                    y = ymax - y - 1
                values = (zoom, x, y)
                tile_results = self.mbtiles_db.execute(query, values).fetchone()

                if tile_results:
                    tile_result = tile_results[0]
                    status = '200 OK'
                    response_headers = [('Content-type', self.tile_content_type)]
                    start_response(status, response_headers)
                    return [tile_result,]
                else:
                    status = '404 NOT FOUND'
                    response_headers = [('Content-type', 'text/plain; charset=utf-8')]
                    start_response(status, response_headers)
                    return ['No data found for request location: {}'.format(environ['PATH_INFO']).encode('utf8')]

        status = "400 Bad Request"
        response_headers = [('Content-type', 'text/plain; charset=utf-8')]
        start_response(status, response_headers)
        return ['request URI not in expected: ("metadata", "/z/x/y.png")'.encode('utf8'), ]


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve",
                        default=MBTILES_SERVE,
                        action='store_true',
                        help="Start test server[DEFAULT={}]\n(Defaults to enviornment variable, 'MBTILES_SERVE')".format(MBTILES_SERVE))
    parser.add_argument('-p', '--port',
                        default=MBTILES_PORT,
                        type=int,
                        help="Test server port [DEFAULT={}]\n(Defaults to enviornment variable, 'MBTILES_PORT')".format(MBTILES_PORT))
    parser.add_argument('-a', '--address',
                        default=MBTILES_HOST,
                        help="Test address to serve on [DEFAULT=\"{}\"]\n(Defaults to enviornment variable, 'MBTILES_HOST')".format(MBTILES_HOST))
    parser.add_argument('-f', '--filepath',
                        default=MBTILES_ABSPATH,
                        help="mbtiles filepath [DEFAULT={}]\n(Defaults to enviornment variable, 'MBTILES_ABSFILEPATH')".format(MBTILES_ABSPATH))
    parser.add_argument('-e', '--ext',
                        default=MBTILES_TILE_EXT,
                        help="mbtiles image file extention [DEFAULT={}]\n(Defaults to enviornment variable, 'MBTILES_TILE_EXT')".format(MBTILES_TILE_EXT))
    parser.add_argument('-z', '--zoom-offset',
                        default=MBTILES_ZOOM_OFFSET,
                        type=int,
                        help="mbtiles zoom offset [DEFAULT={}]\n(Defaults to enviornment variable, 'MBTILES_ZOOM_OFFSET')".format(MBTILES_ZOOM_OFFSET))
    args = parser.parse_args()
    args.filepath = os.path.abspath(args.filepath)
    if args.serve:
        # create console handler and set level to debug
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        logger.addHandler(console)
        logger.setLevel(logging.DEBUG)

        logger.info("FILEPATH: {}".format(args.filepath))
        logger.info("TILE EXT: {}".format(args.ext))
        logger.info("ADDRESS : {}".format(args.address))
        logger.info("PORT    : {}".format(args.port))

        from wsgiref.simple_server import make_server, WSGIServer
        from socketserver import ThreadingMixIn
        class ThreadingWSGIServer(ThreadingMixIn, WSGIServer): pass

        mbtiles_app = MBTilesApplication(mbtiles_filepath=args.filepath, tile_image_ext=args.ext, zoom_offset=args.zoom_offset)
        server = make_server(args.address, args.port, mbtiles_app, ThreadingWSGIServer)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("stopped.")
    else:
        logger.warn("'--serve' option not given!")
        logger.warn("\tRun with the '--serve' option to serve tiles with the test server.")
else:
    application = MBTilesApplication(mbtiles_filepath=MBTILES_ABSPATH, tile_image_ext=MBTILES_TILE_EXT, zoom_offset=MBTILES_ZOOM_OFFSET)
