import vtk
import numpy as np
import pandas as pd

from constants import EARTH_RADIUS, GLIDER_PATH_TUBE_RADIUS, GLIDER_PATH_LUT_RANGE, GLIDER_PATH_WEIGHTED_SEGMENTS
from utils import RT90ToWGS84, toCartesian

def prepareData(file):
    '''
    Read and transforme glider path data to be usable
    '''

    # Read coordinates and elevations
    df = pd.read_table(file, header=None, skiprows=[0], usecols=[1,2,3,4,5], delim_whitespace=True, dtype={1:np.int32, 2:np.int32, 3:np.float64})
    # Compute time interval between two measures
    df[5] = pd.to_datetime((df[4] + "T" + df[5]).astype("str"), format="%m/%d/%yT%H:%M:%S")
    df[5] = df[5].diff().dt.seconds
    # Compute elevation difference between two position
    df[4] = df[3].diff() / df[5] * 2 if GLIDER_PATH_WEIGHTED_SEGMENTS else df[3].diff()
    df[4] = df[4].fillna(0) # Remove NaN
    df[4] = - df[4] # Inverse max and min to fit LUT colors
    # Transform data to WGS84
    df[1], df[2] = RT90ToWGS84(df[1], df[2])
    # Transform to Spherical coords
    df[6] = df.apply(lambda x: toCartesian(x[1], x[2], x[3] + EARTH_RADIUS), axis=1)

    return df[6], df[4]

def getActor(file):
    '''
    Return an actor showing the glider path with elevation differences highlighted
    '''

    # Retrieve data
    coords, diffs = prepareData(file)

    # Geometry
    points = vtk.vtkPoints()
    # Scalar attributes
    elevationDiffs = vtk.vtkFloatArray()

    for coord, diff in zip(coords, diffs):
        points.InsertNextPoint(coord)
        elevationDiffs.InsertNextValue(diff)

    # Create the path as lines in a polydata
    source = vtk.vtkLineSource()
    source.SetPoints(points)
    source.Update()

    # Settings scalars to the generated polydata
    polydata = source.GetOutput()
    polydata.GetPointData().SetScalars(elevationDiffs)

    # To have something nice to display
    mesh = vtk.vtkTubeFilter()
    mesh.SetRadius(GLIDER_PATH_TUBE_RADIUS)
    mesh.SetInputConnection(source.GetOutputPort())

    # Need to use a custom range and not to compute it
    # since some big diffs can quickly make hard to really
    # highlight the average diffs which will be all green
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(mesh.GetOutputPort())
    mapper.SetScalarRange(GLIDER_PATH_LUT_RANGE)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    return actor