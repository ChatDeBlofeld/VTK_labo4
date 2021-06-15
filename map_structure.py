import numpy as np
from matplotlib.path import Path
import math
import vtk

from constants import *
from utils import quadInterpolation, toCartesian, RT90ToWGS84


def MapAreaToWGS84():
    # Compute map aera in WGS84
    a = np.array(MAP_AREA_RT90)
    a = a.T
    return np.vstack(RT90ToWGS84(a[0], a[1])).T

MAP_AREA_WGS84 = MapAreaToWGS84()
QUAD_INTERPOLATION_ALPHAS = QUAD_INTERPOLATION_MATRIX.dot(MAP_AREA_WGS84[:,0])
QUAD_INTERPOLATION_BETAS = QUAD_INTERPOLATION_MATRIX.dot(MAP_AREA_WGS84[:,1])

# Read elevations from a dataset
elevations = np.fromfile(RAW_ELEVATIONS_FILE_PATH, dtype=np.int16)

# Create a latitudes and longitudes list based on the size of the elevation matrix
longitudes, latitudes = np.meshgrid(np.linspace(RAW_ELEVATIONS_AREA[0][1], RAW_ELEVATIONS_AREA[1][1], RAW_ELEVATIONS_MATRIX_SIZE[0]), 
    np.linspace(RAW_ELEVATIONS_AREA[1][0], RAW_ELEVATIONS_AREA[0][0], RAW_ELEVATIONS_MATRIX_SIZE[1]))
latitudes, longitudes = latitudes.flatten(), longitudes.flatten()

# Define bounds to select points to display. We chose to keep the bounding box of the map area
lowerBoundMask = latitudes >= MAP_AREA_WGS84[:,0].min()
upperBoundMask = latitudes <= MAP_AREA_WGS84[:,0].max()
leftBoundMask = longitudes >= MAP_AREA_WGS84[:,1].min()
rightBoundMask = longitudes <= MAP_AREA_WGS84[:,1].max()

# Compute the shape of the area to display
rows = latitudes[upperBoundMask & lowerBoundMask].size // RAW_ELEVATIONS_MATRIX_SIZE[0]
cols = longitudes[leftBoundMask & rightBoundMask].size // RAW_ELEVATIONS_MATRIX_SIZE[1]

# Filter values
latitudes = latitudes[upperBoundMask & lowerBoundMask & leftBoundMask & rightBoundMask]
longitudes = longitudes[upperBoundMask & lowerBoundMask & leftBoundMask & rightBoundMask]
elevations = elevations[upperBoundMask & lowerBoundMask & leftBoundMask & rightBoundMask]

# Create a coord list of each coord in the area to display
coordsList = np.vstack((latitudes, longitudes)).T

# Create a polygon defined by the map area
mapArea = Path(MAP_AREA_WGS84)

# Compute a list to know if the point will be visible or hidden, i.e
# it belongs to the map area.
# Why? Because we use a StructuredGrid to simplify the way we set topology
# (well this way we basically set nothing, it's auto-computed).
# Or it needs to be strictly defined in terms of dimensions. That's why
# we display a larger (rectangle) area and then manipulate it.
toDisplay = mapArea.contains_points(coordsList)

# Will store the points of the geometry
points = vtk.vtkPoints()
# Will store the elevations of the above points
pointElevations = vtk.vtkIntArray()
# Will store the texture coords of the above points
pointTextureCoords = vtk.vtkFloatArray()
pointTextureCoords.SetNumberOfComponents(2)

# Add data to the above structures
for lat, lon, alt in zip(latitudes, longitudes, elevations):
    p = toCartesian(lat, lon, EARTH_RADIUS + alt)
    points.InsertNextPoint(p)
    pointElevations.InsertNextValue(alt)
    x,y = quadInterpolation(lat, lon, QUAD_INTERPOLATION_ALPHAS, QUAD_INTERPOLATION_BETAS)
    if x < 0 or x > 1 or y < 0 or y > 1:
        pointTextureCoords.InsertNextTuple((0,0))
    else:
        pointTextureCoords.InsertNextTuple((x, y))
    # pointTextureCoords.InsertNextTuple(quadInterpolation(lat, lon, QUAD_INTERPOLATION_ALPHAS, QUAD_INTERPOLATION_BETAS))

# Create grid
grid = vtk.vtkStructuredGrid()
grid.SetDimensions(cols, rows, 1)
grid.SetPoints(points)
grid.GetPointData().SetScalars(pointElevations)
grid.GetPointData().SetTCoords(pointTextureCoords)
# for id, display in enumerate(toDisplay):
#     if not display:
#         grid.BlankPoint(id)

# Export grid
# writer = vtk.vtkStructuredGridWriter()
# writer = vtk.vtkPolyDataWriter()
# writer.SetFileName(PRE_COMPUTED_MESH_FILE_PATH)
# writer.SetFileTypeToASCII()
# writer.SetInputData(grid)
# writer.Write()

# ctf = vtk.vtkColorTransferFunction()
# ctf.AddRGBPoint(0, 0.514, 0.49, 1)
# ctf.AddRGBPoint(1, 0.157, 0.325, 0.141)
# ctf.AddRGBPoint(300, 0.392, 0.725, 0.357)
# ctf.AddRGBPoint(700, 0.898, 0.784, 0.537)
# ctf.AddRGBPoint(1300, 1, 1, 1)

reader = vtk.vtkJPEGReader()
reader.SetFileName(MAP_TEXTURE_FILE_PATH)

texture = vtk.vtkTexture()
texture.SetInputConnection(reader.GetOutputPort())

mapper = vtk.vtkDataSetMapper()
mapper.SetInputData(grid)
mapper.ScalarVisibilityOff()
# mapper.SetLookupTable(ctf)
# mapper.SetScalarRange(397,967)

gridActor = vtk.vtkActor()
gridActor.SetMapper(mapper)
gridActor.SetTexture(texture)

renderer = vtk.vtkRenderer()
renderer.AddActor(gridActor)
# renderer.GetActiveCamera().SetFocalPoint(0,0,0)
# renderer.GetActiveCamera().SetPosition(1297250.771172846, 2864648.7209518966, 5541501.618572724)
# renderer.GetActiveCamera().SetClippingRange(0, 1_000_0000_0) 

renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(renderer)
renWin.SetSize(800, 800)

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

style = vtk.vtkInteractorStyleTrackballCamera()
iren.SetInteractorStyle(style)

iren.Initialize()
iren.Render()
iren.Start()