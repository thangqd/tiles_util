from urllib.parse import urlparse

from vtiles.utils.mapbox_vector_tile import decode

from .features import Layer


def _is_url(uri: str) -> bool:
    """
    Checks if the uri is actually an url.
    :param uri: the string to check.
    :return: a boolean.
    """
    return urlparse(uri).scheme != ""


def vt_bytes_to_geojson(b_content: bytes, x: int, y: int, z: int, layer=None) -> dict:
    """
    Make a GeoJSON from bytes in the vector tiles format.
    :param b_content: the bytes to convert.
    :param x: tile x coordinate.
    :param y: tile y coordinate.
    :param z: tile z coordinate.
    :param layer: include only the specified layer.
    :return: a features collection (GeoJSON).
    """
    data = decode(b_content, y_coord_down=True)

    features_collections = [Layer(x=x, y=y, z=z, name=layer_name, obj=layer_obj).toGeoJSON()
                            for layer_name, layer_obj in data.items() if layer is None or layer_name == layer]

    geojson = {fc["name"]: {"type": fc["type"], "features": fc["features"]} for fc in features_collections}

     
    return geojson
    
