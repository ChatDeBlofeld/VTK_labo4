from utils import toCartesian
import vtk
import glider_path
import map_structure
import interactor
from constants import CAMERA_ALTITUDE, CAMERA_POSITION, CAMERA_ROLL, EARTH_RADIUS, GLIDER_GPS_DATA_FILE_PATH

mapActor = map_structure.getActor()
gliderPathActor = glider_path.getActor(GLIDER_GPS_DATA_FILE_PATH)

renderer = vtk.vtkRenderer()
renderer.SetBackground(1,1,1)
renderer.AddActor(mapActor)
renderer.AddActor(gliderPathActor)
renderer.GetActiveCamera().SetFocalPoint(toCartesian(*CAMERA_POSITION, EARTH_RADIUS))
renderer.GetActiveCamera().SetPosition(toCartesian(*CAMERA_POSITION, EARTH_RADIUS + CAMERA_ALTITUDE))
renderer.GetActiveCamera().Roll(CAMERA_ROLL)
renderer.GetActiveCamera().SetClippingRange(1, 2 * CAMERA_ALTITUDE)


renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(renderer)
renWin.SetSize(1200, 800)

style = interactor.LevelLineTrackballCamera(mapActor)
style.SetDefaultRenderer(renderer)
style.lateInit()

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)
iren.SetInteractorStyle(style)

iren.Initialize()
iren.Render()
iren.Start()
