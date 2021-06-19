import vtk
import numpy as np
import pandas as pd

from constants import EARTH_RADIUS, GLIDER_PATH_TUBE_RADIUS, GLIDER_PATH_LUT_RANGE, GLIDER_GPS_DATA_FILE_PATH
from utils import RT90ToWGS84, toCartesian

def prepareData(file):
    # Read coordinates and elevations
    df = pd.read_table(file, header=None, skiprows=[0], usecols=[1,2,3], delim_whitespace=True, dtype={1:np.int32, 2:np.int32, 3:np.float64})
    # Compute elevation difference between two position
    df[4] = df[3].diff()
    df[4] = df[4].fillna(0) # Remove NaN
    df[4] = - df[4] # Inverse max and min to fit LUT
    # Transform data to WGS84
    df[1], df[2] = RT90ToWGS84(df[1], df[2])
    # Transform to Spherical coords
    df[5] = df.apply(lambda x: toCartesian(x[1], x[2], x[3] + EARTH_RADIUS), axis=1)

    return df[5], df[4]

def getActor(file):
    coords, diffs = prepareData(file)
    points = vtk.vtkPoints()
    elevationDiffs = vtk.vtkFloatArray()

    for coord, diff in zip(coords, diffs):
        points.InsertNextPoint(coord)
        elevationDiffs.InsertNextValue(diff)

    source = vtk.vtkLineSource()
    source.SetPoints(points)
    source.Update()

    polydata = source.GetOutput()
    polydata.GetPointData().SetScalars(elevationDiffs)

    mesh = vtk.vtkTubeFilter()
    mesh.SetRadius(GLIDER_PATH_TUBE_RADIUS)
    mesh.SetInputConnection(source.GetOutputPort())

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(mesh.GetOutputPort())
    mapper.SetScalarRange(GLIDER_PATH_LUT_RANGE)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    return actor