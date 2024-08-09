# Reference: https://geohash.softeng.co/uekkn, https://github.com/vinsci/geohash, https://www.movable-type.co.uk/scripts/geohash.html?geohash=dp3
import argparse
import  tiles_util.utils.geocode.geohash as geohash
from shapely.geometry import Polygon, mapping
import geojson
from tqdm import tqdm
# import geohash

def geohash_to_bbox(gh):
    """Convert geohash to bounding box coordinates."""
    lat, lon = geohash.decode(gh)
    lat_err, lon_err = geohash.decode_exactly(gh)[2:]
    
    bbox = {
        'w': max(lon - lon_err, -180),
        'e': min(lon + lon_err, 180),
        's': max(lat - lat_err, -85.051129),
        'n': min(lat + lat_err, 85.051129)
    }
    
    return bbox

def geohash_to_polygon(gh):
    """Convert geohash to a Shapely Polygon."""
    bbox = geohash_to_bbox(gh)
    polygon = Polygon([
        (bbox['w'], bbox['s']),
        (bbox['w'], bbox['n']),
        (bbox['e'], bbox['n']),
        (bbox['e'], bbox['s']),
        (bbox['w'], bbox['s'])
    ])
    
    return polygon

def generate_geohashes(precision):
    """Generate geohashes at a given precision level."""
    if precision < 1 or precision > 12:
        raise ValueError("Precision level must be between 1 and 12.")
    
    geohashes = set()
    initial_geohashes = ["b", "c", "f", "g", "u", "v", "y", "z", "8", "9", "d", "e", "s", "t", "w", "x", "0", "1", "2", "3", "p", "q", "r", "k", "m", "n", "h", "j", "4", "5", "6", "7"]
    
    def expand_geohash(gh, target_length):
        if len(gh) == target_length:
            geohashes.add(gh)
            return
        for char in "0123456789bcdefghjkmnpqrstuvwxyz":
            expand_geohash(gh + char, target_length)
    
    for gh in initial_geohashes:
        expand_geohash(gh, precision)
    
    return geohashes

def create_world_polygons_at_precision(precision):
    """Create a GeoJSON FeatureCollection of polygons at a given precision level."""
    geohash_polygons = []
    geohashes = generate_geohashes(precision)
    
    for gh in tqdm(geohashes, desc='Generating Polygons'):
        polygon = geohash_to_polygon(gh)
        geohash_polygons.append(geojson.Feature(
            geometry=mapping(polygon),
            properties={"geohash": gh}
        ))
    
    feature_collection = geojson.FeatureCollection(geohash_polygons)
    return feature_collection

def save_to_geojson(feature_collection, filename):
    """Save the FeatureCollection to a GeoJSON file."""
    with open(filename, 'w') as f:
        geojson.dump(feature_collection, f)

def main():
    parser = argparse.ArgumentParser(description='Generate world polygons based on geohashes.')
    parser.add_argument('-p', '--precision', type=int, required=True, help='Precision level for the geohashes (1-12)')
    args = parser.parse_args()
    
    try:
        precision = args.precision
        world_polygons = create_world_polygons_at_precision(precision)
        output_filename = f'./geohash_{precision}.geojson'
        save_to_geojson(world_polygons, output_filename)
        print(f"GeoJSON file saved as: {output_filename}")
        # p=1 --> zoom level: 0-4
        # p=2 --> zoom level: 5-6
        # p=3 --> zoom level: 7-9
        # p=4 --> zoom leve: 10-11
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
