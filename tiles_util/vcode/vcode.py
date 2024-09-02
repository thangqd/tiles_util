import tiles_util.utils.mercantile as mercantile
import re
import geojson
from shapely.geometry import Polygon
from shapely.ops import transform
import pyproj
from shapely.geometry import box, shape
import argparse

# from tiles_util.vcode import *
# vcode2quadkey('z2x3y3')
# from tiles_util import vcode as v
# v.vcode2quadkey('z2x3y3')

def vcode2geojson(vcode):
    """
    Converts a vcode (e.g., 'z8x11y14') to a GeoJSON Feature with a Polygon geometry
    representing the tile's bounds and includes the original vcode as a property.

    Args:
        vcode (str): The tile code in the format 'zXxYyZ'.

    Returns:
        dict: A GeoJSON Feature with a Polygon geometry and vcode as a property.
    """
    # Extract z, x, y from the vcode using regex
    match = re.match(r'z(\d+)x(\d+)y(\d+)', vcode)
    if not match:
        raise ValueError("Invalid vcode format. Expected format: 'zXxYyZ'")

    # Convert matched groups to integers
    z = int(match.group(1))
    x = int(match.group(2))
    y = int(match.group(3))

    # Get the bounds of the tile in (west, south, east, north)
    bounds = mercantile.bounds(x, y, z)

    # Create the coordinates of the polygon using the bounds
    polygon_coords = [
        [bounds.west, bounds.south],  # Bottom-left
        [bounds.east, bounds.south],  # Bottom-right
        [bounds.east, bounds.north],  # Top-right
        [bounds.west, bounds.north],  # Top-left
        [bounds.west, bounds.south]   # Closing the polygon
    ]

    # Create a GeoJSON Feature with a Polygon geometry and vcode as a property
    geojson_feature = geojson.Feature(
        geometry=geojson.Polygon([polygon_coords]),
        properties={
            "vcode": vcode
        }
    )

    return geojson_feature

def vcode2geojson_cli():
    """
    Command-line interface for vcode2geojson.
    """
    parser = argparse.ArgumentParser(description="Convert vcode to GeoJSON")
    parser.add_argument("vcode", help="Input vcode, e.g. z0x0y0")
    parser.add_argument("-o", "--output", help="Output file path to save GeoJSON", default=None)
    args = parser.parse_args()

    # Generate the GeoJSON feature
    feature = vcode2geojson(args.vcode)

    # Convert feature to a GeoJSON string
    geojson_data = geojson.dumps(feature, indent=2)

    # Check if an output file path is specified
    if args.output:
        # Write the GeoJSON to the specified output file
        with open(args.output, 'w') as f:
            f.write(geojson_data)
        print(f"GeoJSON saved to {args.output}")
    else:
        # Print the GeoJSON to the console
        print(geojson_data)

def zxy2vcode(z, x, y):
    """
    Converts z, x, and y values to a string formatted as 'zXxYyZ'.

    Args:
        z (int): The zoom level.
        x (int): The x coordinate.
        y (int): The y coordinate.

    Returns:
        str: A string formatted as 'zXxYyZ'.
    """
    return f'z{z}x{x}y{y}'

def vcode2zxy(vcode):
    """
    Parses a string formatted as 'zXxYyZ' to extract z, x, and y values.

    Args:
        vcode (str): A string formatted like 'z8x11y14'.

    Returns:
        tuple: A tuple containing (z, x, y) as integers.
    """
    # Regular expression to capture numbers after z, x, and y
    match = re.match(r'z(\d+)x(\d+)y(\d+)', vcode)
    
    if match:
        # Extract and convert matched groups to integers
        z = int(match.group(1))
        x = int(match.group(2))
        y = int(match.group(3))
        return z, x, y
    else:
        # Raise an error if the format does not match
        raise ValueError("Invalid format. Expected format: 'zXxYyZ'")

def latlon2vcode(lat, lon, zoom):
    """
    Converts latitude, longitude, and zoom level to a tile code ('vcode') of the format 'zXxYyZ'.

    Args:
        lat (float): Latitude of the point.
        lon (float): Longitude of the point.
        zoom (int): Zoom level.

    Returns:
        str: A string representing the tile code in the format 'zXxYyZ'.
    """
    # Get the tile coordinates (x, y) for the given lat, lon, and zoom level
    tile = mercantile.tile(lon, lat, zoom)
    
    # Format the tile coordinates into the vcode string
    vcode = f"z{tile.z}x{tile.x}y{tile.y}"
    
    return vcode

def vcode2latlon(vcode):
    """
    Calculates the center latitude and longitude of a tile given its vcode.

    Args:
        vcode (str): The tile code in the format 'zXxYyZ'.

    Returns:
        tuple: A tuple containing the latitude and longitude of the tile's center.
    """
    # Extract z, x, y from the vcode using regex
    match = re.match(r'z(\d+)x(\d+)y(\d+)', vcode)
    if not match:
        raise ValueError("Invalid vcode format. Expected format: 'zXxYyZ'")

    # Convert matched groups to integers
    z = int(match.group(1))
    x = int(match.group(2))
    y = int(match.group(3))

    # Get the bounds of the tile
    bounds = mercantile.bounds(x, y, z)

    # Calculate the center of the tile
    center_longitude = (bounds.west + bounds.east) / 2
    center_latitude = (bounds.south + bounds.north) / 2

    return [center_latitude, center_longitude]

def vcode2quadkey(vcode):
    """
    Converts a vcode (e.g., 'z23x6668288y3948543') to a quadkey using mercantile.

    Args:
        vcode (str): The tile code in the format 'zXxYyZ'.

    Returns:
        str: Quadkey corresponding to the vcode.
    """
    # Extract z, x, y from the vcode using regex
    match = re.match(r'z(\d+)x(\d+)y(\d+)', vcode)
    if not match:
        raise ValueError("Invalid vcode format. Expected format: 'zXxYyZ'")

    z = int(match.group(1))
    x = int(match.group(2))
    y = int(match.group(3))

    # Use mercantile to get the quadkey
    tile = mercantile.Tile(x, y, z)
    quadkey = mercantile.quadkey(tile)

    return quadkey

def quadkey2vcode(quadkey):
    """
    Converts a quadkey to a vcode (e.g., 'z23x6668288y3948543') using mercantile.

    Args:
        quadkey (str): The quadkey string.

    Returns:
        str: vcode in the format 'zXxYyZ'.
    """
    # Decode the quadkey to get the tile coordinates and zoom level
    tile = mercantile.quadkey_to_tile(quadkey)
    
    # Format as vcode
    vcode = f"z{tile.z}x{tile.x}y{tile.y}"

    return vcode

def vcode_area(vcode):
    """
    Calculates the area in square meters of a tile given its vcode.

    Args:
        vcode (str): The tile code in the format 'zXxYyZ'.

    Returns:
        float: The area of the tile in square meters.
    """
    # Extract z, x, y from the vcode using regex
    match = re.match(r'z(\d+)x(\d+)y(\d+)', vcode)
    if not match:
        raise ValueError("Invalid vcode format. Expected format: 'zXxYyZ'")

    # Convert matched groups to integers
    z = int(match.group(1))
    x = int(match.group(2))
    y = int(match.group(3))

    # Get the bounds of the tile
    bounds = mercantile.bounds(x, y, z)

    # Define the polygon from the bounds
    polygon_coords = [
        [bounds.west, bounds.south],  # Bottom-left
        [bounds.east, bounds.south],  # Bottom-right
        [bounds.east, bounds.north],  # Top-right
        [bounds.west, bounds.north],  # Top-left
        [bounds.west, bounds.south]   # Closing the polygon
    ]
    polygon = Polygon(polygon_coords)

    # Project the polygon to a metric CRS (e.g., EPSG:3857) to calculate area in square meters
    project = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform
    metric_polygon = transform(project, polygon)

    # Calculate the area in square meters
    area = metric_polygon.area

    return area

def vcode_edge_length(vcode):
    """
    Calculates the length of the edge of a square tile given its vcode.

    Args:
        vcode (str): The tile code in the format 'zXxYyZ'.

    Returns:
        float: The length of the edge of the tile in meters.
    """
    # Extract z, x, y from the vcode using regex
    match = re.match(r'z(\d+)x(\d+)y(\d+)', vcode)
    if not match:
        raise ValueError("Invalid vcode format. Expected format: 'zXxYyZ'")

    # Convert matched groups to integers
    z = int(match.group(1))
    x = int(match.group(2))
    y = int(match.group(3))

    # Get the bounds of the tile
    bounds = mercantile.bounds(x, y, z)

    # Define the coordinates of the polygon
    polygon_coords = [
        [bounds.west, bounds.south],  # Bottom-left
        [bounds.east, bounds.south],  # Bottom-right
        [bounds.east, bounds.north],  # Top-right
        [bounds.west, bounds.north],  # Top-left
        [bounds.west, bounds.south]   # Closing the polygon
    ]
    polygon = Polygon(polygon_coords)

    # Project the polygon to a metric CRS (e.g., EPSG:3857) to calculate edge length in meters
    project = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform
    metric_polygon = transform(project, polygon)

    # Calculate the length of the edge of the square
    edge_length = metric_polygon.exterior.length / 4  # Divide by 4 for the length of one edge

    return edge_length

def vcode2tilebound(vcode):
    """
    Converts a vcode (e.g., 'z23x6668288y3948543') to its bounding box using mercantile.

    Args:
        vcode (str): The tile code in the format 'zXxYyZ'.

    Returns:
        dict: Bounding box with 'west', 'south', 'east', 'north' coordinates.
    """
    # Extract z, x, y from the vcode using regex
    match = re.match(r'z(\d+)x(\d+)y(\d+)', vcode)
    if not match:
        raise ValueError("Invalid vcode format. Expected format: 'zXxYyZ'")

    z = int(match.group(1))
    x = int(match.group(2))
    y = int(match.group(3))

    # Use mercantile to get the bounds
    tile = mercantile.Tile(x, y, z)
    bounds = mercantile.bounds(tile)

    # Convert bounds to a dictionary
    bounds_dict = {
        'west': bounds[0],
        'south': bounds[1],
        'east': bounds[2],
        'north': bounds[3]
    }

    return bounds_dict

def vcode2bound(vcode):
    """
    Converts a vcode (e.g., 'z23x6668288y3948543') to its bounding box using mercantile.

    Args:
        vcode (str): The tile code in the format 'zXxYyZ'.

    Returns:
        list: Bounding box in the format [left, bottom, right, top].
    """
    # Extract z, x, y from the vcode using regex
    match = re.match(r'z(\d+)x(\d+)y(\d+)', vcode)
    if not match:
        raise ValueError("Invalid vcode format. Expected format: 'zXxYyZ'")

    z = int(match.group(1))
    x = int(match.group(2))
    y = int(match.group(3))

    # Convert tile coordinates to Mercator bounds
    bounds = mercantile.bounds(mercantile.Tile(x, y, z))

    # Return bounds as a list in [left, bottom, right, top] format
    return [bounds[0], bounds[1], bounds[2], bounds[3]]

def vcode2wktbound(vcode):
    """
    Converts a vcode (e.g., 'z23x6668288y3948543') to its bounding box in OGC WKT format using mercantile.

    Args:
        vcode (str): The tile code in the format 'zXxYyZ'.

    Returns:
        str: Bounding box in OGC WKT format.
    """
    # Extract z, x, y from the vcode using regex
    match = re.match(r'z(\d+)x(\d+)y(\d+)', vcode)
    if not match:
        raise ValueError("Invalid vcode format. Expected format: 'zXxYyZ'")

    z = int(match.group(1))
    x = int(match.group(2))
    y = int(match.group(3))

    # Use mercantile to get the bounds
    tile = mercantile.Tile(x, y, z)
    bounds = mercantile.bounds(tile)

    # Convert bounds to WKT POLYGON format
    wkt = f"POLYGON(({bounds[0]} {bounds[1]}, {bounds[0]} {bounds[3]}, {bounds[2]} {bounds[3]}, {bounds[2]} {bounds[1]}, {bounds[0]} {bounds[1]}))"

    return wkt

def vcode_list(zoom):
    """
    Lists all vcodes at a specific zoom level using mercantile.

    Args:
        zoom (int): The zoom level.

    Returns:
        list: A list of vcodes for the specified zoom level.
    """
    # Get the maximum number of tiles at the given zoom level
    num_tiles = 2 ** zoom

    vcodes = []
    for x in range(num_tiles):
        for y in range(num_tiles):
            # Create a tile object
            tile = mercantile.Tile(x, y, zoom)
            # Convert tile to vcode
            vcode = f"z{tile.z}x{tile.x}y{tile.y}"
            vcodes.append(vcode)
    
    return vcodes


def vcode_children(vcode):
    """
    Lists all child tiles of a given vcode at the next zoom level.

    Args:
        vcode (str): The tile code in the format 'zXxYyZ'.

    Returns:
        list: A list of vcodes representing the four child tiles.
    """
    # Extract z, x, y from the vcode
    match = re.match(r'z(\d+)x(\d+)y(\d+)', vcode)
    if not match:
        raise ValueError("Invalid vcode format. Expected format: 'zXxYyZ'")

    # Convert matched groups to integers
    z = int(match.group(1))
    x = int(match.group(2))
    y = int(match.group(3))

    # Calculate the next zoom level
    z_next = z + 1

    # Calculate the coordinates of the four child tiles
    children = [
        f"z{z_next}x{2*x}y{2*y}",       # Top-left child
        f"z{z_next}x{2*x+1}y{2*y}",     # Top-right child
        f"z{z_next}x{2*x}y{2*y+1}",     # Bottom-left child
        f"z{z_next}x{2*x+1}y{2*y+1}"    # Bottom-right child
    ]

    return children

def children2geojson(vcode):
    """
    Save the four children of a given vcode to separate GeoJSON files.

    Args:
        vcode (str): The parent vcode.
    """
    # Get the child vcodes
    children = vcode_children(vcode)

    # Save each child as a GeoJSON file
    for i, child_vcode in enumerate(children):
        geojson_feature = vcode2geojson(child_vcode)
        
        # Create a filename for each child based on its vcode
        filename = f"{child_vcode}.geojson"
        
        # Save the GeoJSON feature to a file
        with open(filename, 'w') as file:
            geojson.dump(geojson_feature, file, indent=2)
        print(f"Saved {child_vcode} to {filename}")

def vcode_neighbors(vcode):
    """
    Finds the neighboring vcodes of a given vcode.

    Args:
        vcode (str): The tile code in the format 'zXxYyZ'.

    Returns:
        list: A list of neighboring vcodes.
    """
    # Extract z, x, y from the vcode using regex
    match = re.match(r'z(\d+)x(\d+)y(\d+)', vcode)
    if not match:
        raise ValueError("Invalid vcode format. Expected format: 'zXxYyZ'")

    # Convert matched groups to integers
    z = int(match.group(1))
    x = int(match.group(2))
    y = int(match.group(3))

    # Calculate the neighboring tiles (including the tile itself)
    neighbors = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            # Skip the center tile (the original vcode)
            if dx == 0 and dy == 0:
                continue
            # Calculate the new x and y
            nx = x + dx
            ny = y + dy
            # Ignore tiles with negative coordinates
            if nx >= 0 and ny >= 0:
                # Add the neighbor's vcode to the list
                neighbors.append(f"z{z}x{nx}y{ny}")

    return neighbors

def neighbors2geojson(vcode):
    """
    Save the neighbors of a given vcode to separate GeoJSON files.

    Args:
        vcode (str): The parent vcode.
    """
    # Get the neighbor vcodes
    neighbors = vcode_neighbors(vcode)

    # Save each neighbor as a GeoJSON file
    for neighbor_vcode in neighbors:
        geojson_feature = vcode2geojson(neighbor_vcode)
        
        # Create a filename for each neighbor based on its vcode
        filename = f"{neighbor_vcode}.geojson"
        
        # Save the GeoJSON feature to a file
        with open(filename, 'w') as file:
            geojson.dump(geojson_feature, file, indent=2)
        print(f"Saved {neighbor_vcode} to {filename}")


def bbox_vcodes(bbox, zoom):
    """
    Lists all vcodes intersecting with the bounding box at a specific zoom level.

    Args:
        bbox (list): Bounding box in the format [left, bottom, right, top].
        zoom (int): Zoom level to check.

    Returns:
        list: List of intersecting vcodes.
    """
    west, south, east, north = bbox
    bbox_geom = box(west, south, east, north)
    
    intersecting_vcodes = []

    for tile in mercantile.tiles(west, south, east, north, zoom):
        tile_geom = box(*mercantile.bounds(tile))
        if bbox_geom.intersects(tile_geom):
            vcode = f'z{zoom}x{tile.x}y{tile.y}'
            intersecting_vcodes.append(vcode)

    return intersecting_vcodes


def feature_vcodes(geometry, zoom):
    """
    Lists all vcodes intersecting with the Shapely geometry at a specific zoom level.

    Args:
        geometry (shapely.geometry.base.BaseGeometry): The Shapely geometry to check for intersections.
        zoom (int): Zoom level to check.

    Returns:
        list: List of intersecting vcodes.
    """
    intersecting_vcodes = []

    for tile in mercantile.tiles(*geometry.bounds, zoom):
        tile_geom = box(*mercantile.bounds(tile))
        if geometry.intersects(tile_geom):
            vcode = f'z{zoom}x{tile.x}y{tile.y}'
            intersecting_vcodes.append(vcode)

    return intersecting_vcodes


# def zxy2geojson(z, x, y):
#     """
#     Converts a tile coordinate (z, x, y) to a GeoJSON Feature with a Polygon geometry
#     representing the tile's bounds and includes the z, x, and y as properties.

#     Args:
#         z (int): Zoom level.
#         x (int): Tile x coordinate.
#         y (int): Tile y coordinate.

#     Returns:
#         dict: A GeoJSON Feature with a Polygon geometry and z, x, y properties.
#     """
#     # Get the bounds of the tile in (west, south, east, north)
#     bounds = mercantile.bounds(x, y, z)

#     # Create the coordinates of the polygon using the bounds
#     polygon_coords = [
#         [bounds.west, bounds.south],  # Bottom-left
#         [bounds.east, bounds.south],  # Bottom-right
#         [bounds.east, bounds.north],  # Top-right
#         [bounds.west, bounds.north],  # Top-left
#         [bounds.west, bounds.south]   # Closing the polygon
#     ]

#     # Create a GeoJSON Feature with a Polygon geometry and properties z, x, y
#     geojson_feature = geojson.Feature(
#         geometry=geojson.Polygon([polygon_coords]),
#         properties={
#             "z": z,
#             "x": x,
#             "y": y
#         }
#     )
#     print (geojson_feature)
#     return geojson_feature

# from shapely.geometry import Polygon

# # Define a Shapely Polygon as the feature
# polygon = Polygon([[-120, 35], [-119, 35], [-119, 36], [-120, 36], [-120, 35]])

# zoom_level = 8  # Specify the zoom level
# print(feature_vcodes(polygon, zoom_level))


# bbox = [105.54985696549019,10.038145927846893,107.40441949178657,11.5147084487835]  # Example bounding box: [left, bottom, right, top]
# print(bbox_vcodes(bbox,8))

# # lat,long = 10.48781200, 106.17187500
# # vcode = latlong2vcode(lat,long,8)
# vcode= 'z9x407y240'
# print(vcode)
# print(len(vcode))
# quadkey = vcode2quadkey(vcode)
# print(quadkey)
# print(len(quadkey))
# print(vcode2latlon(vcode))
# area = vcode_area(vcode)
# print("Area of", vcode, "is:", area, "square meters")
# # vcode = 'z8x11y14'
# edge_length = vcode_edge_length(vcode)
# print(edge_length)
# tilebound = vcode2tilebound(vcode)
# print("Tile bound:", tilebound)

# bound = vcode2bound(vcode)
# print("Bound:", bound)


# wkt = vcode2wktbound(vcode)
# print("vcode:", vcode)
# print("Bounding box (WKT):", wkt)
# zoom = 5  # Specify the zoom level
# vcodes = vcode_list(zoom)
# print(len(vcodes))
# quadkey = vcode2quadkey(vcode)
# print("quadkey:", quadkey)

# vcode = quadkey2vcode(quadkey)
# print("vcode:", vcode)