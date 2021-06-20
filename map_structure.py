import numpy as np
import vtk

from constants import *
from utils import quadInterpolation, toCartesian, RT90ListToWGS84

# Area to display in WGS84 coords
MAP_AREA_WGS84 = RT90ListToWGS84(MAP_AREA_RT90)
# Alpha coefficients for quad interpolation with the map area 
QUAD_INTERPOLATION_ALPHAS = QUAD_INTERPOLATION_MATRIX.dot(MAP_AREA_WGS84[:,0])
# Beta coefficients for quad interpolation with the map area
QUAD_INTERPOLATION_BETAS = QUAD_INTERPOLATION_MATRIX.dot(MAP_AREA_WGS84[:,1])

def prepareData():
    '''
    Define all latitudes, longitudes and elevations used in the further mesh.
    The size of the area is returned as an extra parameter.
    '''
    # Read elevations from a dataset
    elevations = np.fromfile(RAW_ELEVATIONS_FILE_PATH, dtype=np.int16)

    # Create a latitudes and longitudes list based on the size of the elevation matrix
    longitudes, latitudes = np.meshgrid(
        np.linspace(RAW_ELEVATIONS_AREA[0][1], RAW_ELEVATIONS_AREA[1][1], RAW_ELEVATIONS_MATRIX_SIZE[1]), 
        np.linspace(RAW_ELEVATIONS_AREA[1][0], RAW_ELEVATIONS_AREA[0][0], RAW_ELEVATIONS_MATRIX_SIZE[0]))
    latitudes, longitudes = latitudes.flatten(), longitudes.flatten()

    # Define bounds to select points to display. We chose to keep the bounding box of the map area
    lowerBoundMask = latitudes >= MAP_AREA_WGS84[:,0].min()
    upperBoundMask = latitudes <= MAP_AREA_WGS84[:,0].max()
    leftBoundMask = longitudes >= MAP_AREA_WGS84[:,1].min()
    rightBoundMask = longitudes <= MAP_AREA_WGS84[:,1].max()

    # Compute the shape of the area to display
    rows = latitudes[upperBoundMask & lowerBoundMask].size // RAW_ELEVATIONS_MATRIX_SIZE[0]
    cols = longitudes[leftBoundMask & rightBoundMask].size // RAW_ELEVATIONS_MATRIX_SIZE[1]

    # Filter useful values
    latitudes = latitudes[upperBoundMask & lowerBoundMask & leftBoundMask & rightBoundMask]
    longitudes = longitudes[upperBoundMask & lowerBoundMask & leftBoundMask & rightBoundMask]
    elevations = elevations[upperBoundMask & lowerBoundMask & leftBoundMask & rightBoundMask]

    return (latitudes, longitudes, elevations), (rows, cols)


def getActor():
    '''
    Return an actor for the map area.
    Geometry + Topology + Texture included
    '''
    # Get raw data
    (latitudes, longitudes, elevations), (rows, cols) = prepareData()

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
        pointTextureCoords.InsertNextTuple(
            quadInterpolation(lat, lon, QUAD_INTERPOLATION_ALPHAS, QUAD_INTERPOLATION_BETAS)
        )

    # Create grid
    grid = vtk.vtkStructuredGrid()
    grid.SetDimensions(cols, rows, 1)
    grid.SetPoints(points)
    grid.GetPointData().SetScalars(pointElevations)
    grid.GetPointData().SetTCoords(pointTextureCoords)

    # Clip mesh to the map area
    areaClipFunction = vtk.vtkImplicitBoolean()
    areaClipFunction.SetOperationTypeToIntersection()

    p0 = np.array([0,0,0])
    for p1, p2 in zip(MAP_AREA_WGS84, np.roll(MAP_AREA_WGS84, -10)):
        p1 = np.array(toCartesian(*p1, 1))
        p2 = np.array(toCartesian(*p2, 1))
        n = -np.cross(p1 - p0, p2 - p0)
        plane = vtk.vtkPlane()
        plane.SetNormal(n)
        areaClipFunction.AddFunction(plane)

    clipper = vtk.vtkClipDataSet()
    clipper.SetInputData(grid)
    clipper.SetClipFunction(areaClipFunction)
    clipper.InsideOutOn()
    clipper.Update()

    # Load texture
    reader = vtk.vtkJPEGReader()
    reader.SetFileName(MAP_TEXTURE_FILE_PATH)

    texture = vtk.vtkTexture()
    texture.RepeatOff()
    texture.SetInputConnection(reader.GetOutputPort())

    # Create mapper
    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputConnection(clipper.GetOutputPort())
    mapper.ScalarVisibilityOff()

    # Create actor
    gridActor = vtk.vtkActor()
    gridActor.SetMapper(mapper)
    gridActor.SetTexture(texture)

    return gridActor