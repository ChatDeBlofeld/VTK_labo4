import vtk
from constants import EARTH_RADIUS, ELEVATION_LABEL_POSITION, LEVEL_LINE_TUBE_COLOR, LEVEL_LINE_TUBE_RADIUS, ELEVATION_LABEL_FONT_SIZE

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
        self.elevationLabelActor.GetTextProperty().SetBackgroundColor(1, 1, 1)
        self.elevationLabelActor.GetTextProperty().SetBackgroundOpacity(1)
        self.elevationLabelActor.GetTextProperty().SetFontSize(ELEVATION_LABEL_FONT_SIZE)
        self.elevationLabelActor.GetTextProperty().BoldOn()
        self.elevationLabelActor.SetPosition(ELEVATION_LABEL_POSITION)
        self.elevationLabelActor.VisibilityOff()

        # Actor displaying our line level
        self.levelLineActor = vtk.vtkActor()
        self.levelLineActor.GetProperty().SetColor(LEVEL_LINE_TUBE_COLOR)

        # Pickers to select the hovered point on our map.
        # We need the two since PointPicker needs tolerance
        # thus detects the mouse outside the Prop.
        # So PropPicker provides us a reliable way to
        # trigger events only if the mouse really is
        # on the Prop, but does not provide the dataset.
        self.pointPicker = vtk.vtkPointPicker()
        self.pointPicker.PickFromListOn()
        self.pointPicker.AddPickList(mapActor)
        self.propPicker = vtk.vtkPropPicker()
        self.propPicker.PickFromListOn()
        self.propPicker.AddPickList(mapActor)

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
        self.pointPicker.Pick(x, y, 0, self.GetDefaultRenderer())
        self.propPicker.Pick(x, y, 0, self.GetDefaultRenderer())
        actor = self.propPicker.GetActor()

        if actor == self.mapActor:
            # Updating level line with the new elevation
            elevation = self.elevations.GetValue(self.pointPicker.GetPointId())
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