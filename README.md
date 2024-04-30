# MBTiles Utilities

## Installation: 
- Using pip install (Windows/ Linux):
    ``` bash 
    pip install mbtiles-util
    ```
- Visit mbtiles-util on [PyPI](https://pypi.org/project/mbtiles-util/)

## Usage:
### mbtilesinfo:
- Display MBTiles metadata info:  
    ``` bash 
    mbtilesinfo <file_path>
    ```
### mbtiles2folder: 
- Convert MBTiles file to folder:  
    ``` bash 
    mbtiles2folder -i <file_path> -o [output_folder (optinal)] -tms [TMS scheme (optinal 0 or 1, default is 0)]
    ```
### folder2S3: 
- Uplpad folder to Amazon S3 Bucket:  
    ``` bash 
    folder2s3 -i <input_folder> -b <bucket_name> -p [s3_prefix (optional)]  -r [region_name (optional)]
    ```
 
 