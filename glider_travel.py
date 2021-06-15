import vtk
import numpy as np
import pandas as pd

from constants import *
from utils import RT90ToWGS84, toCartesian

# Read coordinates and elevations
df = pd.read_table(GLIDER_GPS_DATA_FILE_PATH, header=None, skiprows=[0], usecols=[1,2,3,4,5], delim_whitespace=True, dtype={1:np.int32, 2:np.int32, 3:np.float64})
# Compute time interval between two measures
df[5] = pd.to_datetime((df[4] + "T" + df[5]).astype("str"), format="%m/%d/%yT%H:%M:%S")
df[5] = df[5].diff().dt.seconds
df[5] = df[5].fillna(0)
# Compute elevation difference between two position
df[4] = df[3].diff()
df[4] = df[4].fillna(0)
df[4] = df[4].max() - df[4]
df[4] = df[4] * 100
df[4] = df[4].astype(np.int32)
# Transform data to WGS84
df[1], df[2] = RT90ToWGS84(df[1], df[2])
# Transform to Spherical coords
df[6] = df.apply(lambda x: toCartesian(x[1], x[2], x[3] + EARTH_RADIUS), axis=1)
# Remove NaN

print(df)
print(df[4])

points = vtk.vtkPoints()
elevationDiffs = vtk.vtkIntArray()

for coord, diff, weight in zip(df[6], df[4], df[5]):
    if weight != 0:
        diff = int(diff / weight)
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
print(elevationDiffs.GetValueRange())
mapper.SetScalarRange(elevationDiffs.GetValueRange())
# mapper.GetLookupTable().SetScaleToLog10()

actor = vtk.vtkActor()
actor.SetMapper(mapper)

renderer = vtk.vtkRenderer()
renderer.AddActor(actor)
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