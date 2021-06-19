import vtk
from constants import EARTH_RADIUS, ELEVATION_LABEL_POSITION, LEVEL_LINE_TUBE_COLOR, LEVEL_LINE_TUBE_RADIUS

# https://kitware.github.io/vtk-examples/site/Python/Picking/HighlightPickedActor/
class LevelLineTrackballCamera(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, mapActor):
        self.AddObserver("MouseMoveEvent", self.mouseMoveEvent)
        self.mapActor = mapActor

        # Keep a quick reference to the elevations
        self.elevations = self.mapActor.GetMapper().GetInput().GetPointData().GetScalars()

        # Text label displaying the elevation
        self.elevationLabelActor = vtk.vtkTextActor()
        self.elevationLabelActor.GetTextProperty().SetColor(0, 0, 0)
        self.elevationLabelActor.SetPosition(ELEVATION_LABEL_POSITION)
        self.elevationLabelActor.VisibilityOff()

        # Actor displaying our line level
        self.levelLineActor = vtk.vtkActor()
        self.levelLineActor.GetProperty().SetColor(LEVEL_LINE_TUBE_COLOR)

        # Picker to select the hovered point on our map
        self.mapPicker = vtk.vtkPointPicker()
        self.mapPicker.PickFromListOn()
        self.mapPicker.AddPickList(mapActor)

        # Pipeline for creating level lines
        self.cuttingFunction = vtk.vtkSphere()

        self.cutter = vtk.vtkCutter()

        self.stripper = vtk.vtkStripper()

        self.filter = vtk.vtkTubeFilter()
        self.filter.SetRadius(LEVEL_LINE_TUBE_RADIUS)

        self.mapper = vtk.vtkDataSetMapper()
        self.mapper.ScalarVisibilityOff()

        self.cutter.SetCutFunction(self.cuttingFunction)
        self.cutter.SetInputData(self.mapActor.GetMapper().GetInput())

        self.stripper.SetInputConnection(self.cutter.GetOutputPort())
        self.filter.SetInputConnection(self.stripper.GetOutputPort())
        self.mapper.SetInputConnection(self.filter.GetOutputPort())

        # Add mapper to our actor
        self.levelLineActor.SetMapper(self.mapper)

    def lateInit(self):
        self.GetDefaultRenderer().AddActor(self.elevationLabelActor)
        self.GetDefaultRenderer().AddActor(self.levelLineActor)

    def mouseMoveEvent(self, obj, event):
        # Get the hovered actor
        x,y = self.GetInteractor().GetEventPosition()
        self.mapPicker.Pick(x, y, 0, self.GetDefaultRenderer())
        actor = self.mapPicker.GetActor()

        if actor == self.mapActor:
            # Updating level line with the new elevation
            elevation = self.elevations.GetValue(self.mapPicker.GetPointId())
            self.cuttingFunction.SetRadius(EARTH_RADIUS + elevation)
            self.cutter.Update()

            # Updating elevation label
            self.elevationLabelActor.SetInput("Altitude : {} m".format(elevation))

            self.elevationLabelActor.VisibilityOn()
            self.levelLineActor.VisibilityOn()
            
        else:
            # Hiding actors when not hovering the map
            self.elevationLabelActor.VisibilityOff()
            self.levelLineActor.VisibilityOff()

        # Force rendering
        self.GetInteractor().Render()

        self.OnMouseMove()
        return