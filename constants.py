import numpy as np

# Raw elevations
RAW_ELEVATIONS_FILE_PATH = "EarthEnv-DEM90_N60E010.bil"

# Size of elevation matrix
RAW_ELEVATIONS_MATRIX_SIZE = (6000, 6000)

# Area of elevation matrix (WGS84)
RAW_ELEVATIONS_AREA = [(60, 10), (65, 15)]

# in [m]
EARTH_RADIUS: int = 6371009

# Geometry and topology of the map, intermediate file
PRE_COMPUTED_MESH_FILE_PATH = "raw_mesh.vtk"

# Map texture
MAP_TEXTURE_FILE_PATH = "glider_map.png"

# Glider travel
GLIDER_GPS_DATA_FILE_PATH = "vtkgps.txt"

# Value range of the LUT for the glider path for a smooth display
GLIDER_PATH_LUT_RANGE = (-5, 5)

# Map area, RT90 (SW, SE, NE, NW)
MAP_AREA_RT90 = [(1349602, 7005969), (1371835, 7006362), (1371573, 7022967), (1349340, 7022573)]

# Radius of the tubes defining the glider path [m]
GLIDER_PATH_TUBE_RADIUS = 30

# Matrix used to computed the interpolation of a quadrilateral
# https://www.particleincell.com/2012/quad-interpolation/
QUAD_INTERPOLATION_MATRIX = np.array([[1,0,0,0], [-1,1,0,0], [-1,0,0,1], [1,-1,1,-1]])
