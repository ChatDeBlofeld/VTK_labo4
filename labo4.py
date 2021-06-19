import vtk
import glider_path
import map_structure
import interactor
from constants import GLIDER_GPS_DATA_FILE_PATH

mapActor = map_structure.getActor()

renderer = vtk.vtkRenderer()
renderer.SetBackground(1,1,1)
renderer.AddActor(mapActor)
renderer.AddActor(glider_path.getActor(GLIDER_GPS_DATA_FILE_PATH))
# renderer.GetActiveCamera().SetFocalPoint(0,0,0)
# renderer.GetActiveCamera().SetPosition(1297250.771172846, 2864648.7209518966, 5541501.618572724)
# renderer.GetActiveCamera().SetClippingRange(0, 1_000_0000_0) 

renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(renderer)
renWin.SetSize(800, 800)

style = interactor.LevelLineTrackballCamera(mapActor)
style.SetDefaultRenderer(renderer)
style.lateInit()

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)
iren.SetInteractorStyle(style)

iren.Initialize()
iren.Render()
iren.Start()
