import vtk
import numpy as np
from constants import EARTH_RADIUS, ELEVATION_LABEL_POSITION, CONTOUR_LINE_TUBE_COLOR, \
    CONTOUR_LINE_TUBE_RADIUS, ELEVATION_LABEL_FONT_SIZE, ELEVATION_LABEL_CONTENT

# https://kitware.github.io/vtk-examples/site/Python/Picking/HighlightPickedActor/
class ContourLineTrackballCamera(vtk.vtkInteractorStyleTrackballCamera):
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

        # Actor displaying our countour lines
        self.contourLineActor = vtk.vtkActor()
        self.contourLineActor.GetProperty().SetColor(CONTOUR_LINE_TUBE_COLOR)

        # Pickers to select the hovered cell on our map.
        self.cellPicker = vtk.vtkCellPicker()
        self.cellPicker.PickFromListOn()
        self.cellPicker.AddPickList(mapActor)
        self.cellPicker.SetTolerance(0)

        # Pipeline for creating contour lines
        self.cutFunction = vtk.vtkSphere()

        self.cutter = vtk.vtkCutter()

        self.stripper = vtk.vtkStripper()

        self.filter = vtk.vtkTubeFilter()
        self.filter.SetRadius(CONTOUR_LINE_TUBE_RADIUS)

        self.mapper = vtk.vtkDataSetMapper()
        self.mapper.ScalarVisibilityOff()

        self.cutter.SetCutFunction(self.cutFunction)
        self.cutter.SetInputData(self.mapActor.GetMapper().GetInput())

        self.stripper.SetInputConnection(self.cutter.GetOutputPort())
        self.filter.SetInputConnection(self.stripper.GetOutputPort())
        self.mapper.SetInputConnection(self.filter.GetOutputPort())

        # Add mapper to our actor
        self.contourLineActor.SetMapper(self.mapper)

    def lateInit(self):
        self.GetDefaultRenderer().AddActor(self.elevationLabelActor)
        self.GetDefaultRenderer().AddActor(self.contourLineActor)

    def mouseMoveEvent(self, obj, event):
        # Get the hovered actor
        x,y = self.GetInteractor().GetEventPosition()
        self.cellPicker.Pick(x, y, 0, self.GetDefaultRenderer())
        actor = self.cellPicker.GetActor()

        if actor == self.mapActor:
            # Get points defining the hovered cell
            points = vtk.vtkIdList()
            self.mapActor.GetMapper().GetInput().GetCellPoints(self.cellPicker.GetCellId(), points)

            # Get elevation for each point
            elevations = [self.elevations.GetValue(points.GetId(i)) for i in range(points.GetNumberOfIds())]       

            # Interpolate elevation depending on the mouse position in the cell
            elevation = 0
            x,y,_ = self.cellPicker.GetPCoords()
            for i, e in enumerate(elevations):
                a = 1 - x if i % 3 == 0 else x
                b = 1 - y if i < 2 else y
                elevation += a * b * e

            # Update elevation in the cut function
            self.cutFunction.SetRadius(EARTH_RADIUS + elevation)
            self.cutter.Update()

            # Update elevation label
            self.elevationLabelActor.SetInput(ELEVATION_LABEL_CONTENT.format(elevation))

            self.elevationLabelActor.VisibilityOn()
            self.contourLineActor.VisibilityOn()
            
        else:
            # Hiding actors when not hovering the map
            self.elevationLabelActor.VisibilityOff()
            self.contourLineActor.VisibilityOff()

        # Force rendering
        self.GetInteractor().Render()

        self.OnMouseMove()
        return