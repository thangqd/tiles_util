import sqlite3, json
import os, sys, datetime

# Check if mbtiles is vector or raster
def check_vector(input_filename):    
    connection = sqlite3.connect(input_filename)
    cursor = connection.cursor()
    cursor.execute("SELECT value FROM metadata WHERE name='format'")
    format_info = cursor.fetchone()
    # Close the database connection
    cursor.close()
    connection.close()    

    # Check if format_info is not None
    if format_info:
        format_value = format_info[0].lower()
        if 'pbf' in format_value or 'vector' in format_value:
            return 1
        elif 'png' in format_value or 'jpg' in format_value or 'webp' in format_value or 'raster' in format_value:
            return 0
        else:
            return -1

# Read vector metadata
def read_vector_metadata(input_filename):
    """Read metadata from vector MBTiles file."""
    connection = sqlite3.connect(input_filename)
    cursor = connection.cursor()
    
    # Extract metadata
    # cursor.execute("SELECT name, value FROM metadata where name <>'json'")
    cursor.execute("SELECT name, value FROM metadata where name <> 'json'")
    metadata = dict(cursor.fetchall())
    
    cursor.close()
    connection.close()
    
    return metadata

# Read raster metadata
def read_raster_metadata(input_filename):
    """Read metadata from raster MBTiles file."""
    connection = sqlite3.connect(input_filename)
    cursor = connection.cursor()
    
    # Extract metadata
    cursor.execute("SELECT name, value FROM metadata")
    metadata = dict(cursor.fetchall())
    
    cursor.close()
    connection.close()
    
    return metadata

def count_tiles(input_filename):
    """Count the number of tiles in the MBTiles file."""
    num_tiles = None
    connection = sqlite3.connect(input_filename)
    cursor = connection.cursor()
    
    cursor.execute("SELECT type FROM sqlite_master WHERE name='tiles'")
    # Fetch the result
    table_or_view = cursor.fetchone()[0]
    if table_or_view == 'table':
        # Count the number of tiles
        cursor.execute("SELECT COUNT(*) FROM tiles")
        num_tiles = cursor.fetchone()[0]
   
    # in case the tiles view join 2 tables 'images' and 'map' may have greater number of tiles than actual
    elif table_or_view == 'view':
        cursor.execute("""SELECT COUNT(DISTINCT CONCAT(
			CAST(zoom_level  AS TEXT), '|', 
			CAST(tile_column  AS TEXT) , '|', CAST(tile_row  AS TEXT)
			))
            FROM tiles""")
        num_tiles = cursor.fetchone()[0]
    
    cursor.close()
    connection.close()
    
    return num_tiles

# list all vector layers
def read_vector_layers_old(input_filename):    
    connection = sqlite3.connect(input_filename)
    cursor = connection.cursor()
    cursor.execute("SELECT name, value FROM metadata where name = 'json'")
    row = cursor.fetchone()
    if row is not None:
        json_content = row[1]
        layers_json = json.loads(json_content)
        if "vector_layers" in layers_json:
            vector_layers = layers_json["vector_layers"]
            print("######:")
            print("Vector layers:")
            for index, layer in enumerate(vector_layers):
                row_index = index + 1
                layer_id = layer["id"]
                print(f"{row_index}: {layer_id}")
                # Additional information printing here if needed
        else:
            print("######:")
            print("No 'vector_layers' found in metadata.")
    else:
        return

def read_vector_layers(input_filename):    
    connection = sqlite3.connect(input_filename)
    cursor = connection.cursor()
    
    # Fetch the JSON from the metadata
    cursor.execute("SELECT value FROM metadata WHERE name = 'json'")
    row = cursor.fetchone()
    
    if row is not None:
        json_content = row[0]
        layers_json = json.loads(json_content)
        
        # Print vector layers information
        if "vector_layers" in layers_json:
            vector_layers = layers_json["vector_layers"]
            print("######:")
            print("Vector layers:")
            for index, layer in enumerate(vector_layers):
                row_index = index + 1
                layer_id = layer["id"]
                description = layer.get("description", "")
                minzoom = layer.get("minzoom", "")
                maxzoom = layer.get("maxzoom", "")
                fields = layer.get("fields", {})
                
                print(f"{row_index}: {layer_id}")
                # print(f"  Description: {description}")
                # print(f"  Min Zoom: {minzoom}")
                # print(f"  Max Zoom: {maxzoom}")
                # print(f"  Fields: {fields}")
                # print(" ")
        
        # Print tilestats information
        # if "tilestats" in layers_json:
        #     tilestats = layers_json["tilestats"]
        #     print("######:")
        #     print("Tile Stats:")
        #     layer_count = tilestats.get("layerCount", 0)
        #     print(f"  Layer Count: {layer_count}")
            
        #     if "layers" in tilestats:
        #         for index, layer in enumerate(tilestats["layers"]):
        #             row_index = index + 1
        #             layer_name = layer.get("layer", "")
        #             count = layer.get("count", "")
        #             geometry = layer.get("geometry", "")
        #             attribute_count = layer.get("attributeCount", 0)
                    
        #             print(f"{row_index}: {layer_name}")
        #             print(f"  Count: {count}")
        #             print(f"  Geometry: {geometry}")
        #             print(f"  Attribute Count: {attribute_count}")
                    
        #             if "attributes" in layer:
        #                 for attr_index, attribute in enumerate(layer["attributes"]):
        #                     attr_name = attribute.get("attribute", "")
        #                     attr_count = attribute.get("count", 0)
        #                     attr_type = attribute.get("type", "")
        #                     attr_values = attribute.get("values", [])
                            
        #                     print(f"    Attribute {attr_index + 1}: {attr_name}")
        #                     print(f"      Count: {attr_count}")
        #                     print(f"      Type: {attr_type}")
        #                     print(f"      Values: {attr_values}")
        #                     print(" ")            
    connection.close()

   
def main():
    if len(sys.argv) != 2:
      print("Please provide the mbtiles input filename.")
      return
    input_filename = sys.argv[1]
    file_stat = os.stat(input_filename)
    file_size_mb = round(file_stat.st_size / (1024 * 1024),2)
    # file_created = datetime.datetime.fromtimestamp(file_stat.st_ctime).strftime("%Y-%m-%d %I:%M:%S %p")
    file_last_modified = datetime.datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %I:%M:%S %p")
    # file_size = os.path.getsize(input_filename)
    # file_size_mb = round(file_size / (1024 * 1024),2)
    print('######')
    print("File size: ", file_size_mb, 'MB')
    # print("Date created: ", file_created)
    print("Last modified: ", file_last_modified)
    if (os.path.exists(input_filename)):
        if check_vector(input_filename) == 1: # vector
            metadata = read_vector_metadata(input_filename)
            num_tiles = count_tiles(input_filename)
            print("######")
            print("Metadata:")
            for key, value in metadata.items():
                print(f"{key}: {value}")
            print('######')
            print(f"Total number of tiles: {num_tiles}")
            read_vector_layers(input_filename)
        
        else:
            metadata = read_raster_metadata(input_filename)
            num_tiles = count_tiles(input_filename)
            print("###### Metadata:")
            for key, value in metadata.items():
                print(f"{key}: {value}")
            print(f"Total number of tiles: {num_tiles}")
    else: 
        print ('MBTiles file does not exist!. Please recheck and input a correct file path.')
        return

if __name__ == "__main__":
    main()
