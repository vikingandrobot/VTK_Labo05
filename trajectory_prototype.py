import numpy as np
import vtk
import datetime as dt


def computeVerticalSpeed(gliderTrajectory, index):
    lastDateTime = gliderTrajectory[index - 1][DATE_TIME_INDEX]
    dateTime = gliderTrajectory[index][DATE_TIME_INDEX]
    lastAltitude = gliderTrajectory[index - 1][ALTITUDE_INDEX]
    altitude = gliderTrajectory[index][ALTITUDE_INDEX]
    return (altitude - lastAltitude) / (dateTime - lastDateTime).total_seconds()


LONGITUDE_INDEX = 0
LATITUDE_INDEX = 1
ALTITUDE_INDEX = 2
DATE_TIME_INDEX = 3

vtkPoints = vtk.vtkPoints()

gliderTrajectory = []
lineCount = -1
minVerticalSpeed = 0
maxVerticalSpeed = 0
with open("data/vtkgps.txt") as fileIn:
    for line in fileIn:
        if (lineCount == -1):
            lineCount += 1
            continue

        lineCount += 1
        values = line.split()
        coordinates = []
        # Coordinates
        coordinates.append(int(values[1]) - 1361700)
        coordinates.append(int(values[2]) - 7013468)
        coordinates.append(float(values[3]))

        dateArray = values[4].split('/')
        timeArray = values[5].split(':')
        dateTime = dt.datetime(int(dateArray[0]),
            int(dateArray[2]),
            int(dateArray[1]),
            int(timeArray[0]),
            int(timeArray[1]),
            int(timeArray[2]))
        coordinates.append(dateTime)

        gliderTrajectory.append(coordinates)

        # VTK points
        vtkPoints.InsertNextPoint(coordinates[LONGITUDE_INDEX], coordinates[ALTITUDE_INDEX], coordinates[LATITUDE_INDEX])

        # Min / Max delta
        index = lineCount - 1
        if (index > 0):
            verticalSpeed = computeVerticalSpeed(gliderTrajectory, index)

            if (verticalSpeed < minVerticalSpeed):
                minVerticalSpeed = verticalSpeed
            if (verticalSpeed > maxVerticalSpeed):
                maxVerticalSpeed = verticalSpeed

lutAsc = vtk.vtkLookupTable()
lutAsc.SetTableRange(0, maxVerticalSpeed)
lutAsc.SetHueRange(1/6, 0)
lutAsc.Build()

lutDesc = vtk.vtkLookupTable()
lutDesc.SetTableRange(minVerticalSpeed, 0)
lutDesc.SetHueRange(1/3, 1/6)
lutDesc.Build()

colors = vtk.vtkUnsignedCharArray()
colors.SetNumberOfComponents(3)
colors.SetName("Colors")

for i in range(0, len(gliderTrajectory)):
    dcolor = [0, 0, 0]
    if (i == 0):
        lutDesc.GetColor(0, dcolor)
    else:
        verticalSpeed = computeVerticalSpeed(gliderTrajectory, i)
        if (verticalSpeed > 0):
            lutAsc.GetColor(verticalSpeed, dcolor)
        else:
            lutDesc.GetColor(verticalSpeed, dcolor)
    color = [0, 0, 0]
    for k in range(0, 3):
        color[k] = 255 * dcolor[k]

    colors.InsertNextTuple(color)




polyLine = vtk.vtkPolyLine()
polyLine.GetPointIds().SetNumberOfIds(len(gliderTrajectory))
for i in range(0, len(gliderTrajectory)):
    polyLine.GetPointIds().SetId(i, i)

cells = vtk.vtkCellArray()
cells.InsertNextCell(polyLine)

polyData = vtk.vtkPolyData()
polyData.SetPoints(vtkPoints)
polyData.SetLines(cells)
polyData.GetPointData().SetScalars(colors)

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputData(polyData)

actor = vtk.vtkActor()
actor.SetMapper(mapper)

# Create a tube (cylinder) around the line
tubeFilter = vtk.vtkTubeFilter()
tubeFilter.SetInputData(polyData)
tubeFilter.SetRadius(20)
tubeFilter.SetNumberOfSides(50)
tubeFilter.Update()

# Create a mapper and actor
tubeMapper = vtk.vtkPolyDataMapper()
tubeMapper.SetInputConnection(tubeFilter.GetOutputPort())
tubeActor = vtk.vtkActor()
tubeActor.SetMapper(tubeMapper)

renderer = vtk.vtkRenderer()
renderer.SetBackground(1, 1, 1)
renderWindow = vtk.vtkRenderWindow()

renderWindow.AddRenderer(renderer)
renderWindow.SetSize(1200, 720)

renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

# Here we specify a particular interactor style.
style = vtk.vtkInteractorStyleTrackballCamera()
renderWindowInteractor.SetInteractorStyle(style)

# axes = vtk.vtkAxesActor()
# widget = vtk.vtkOrientationMarkerWidget()
# widget.SetOutlineColor( 0.9300, 0.5700, 0.1300 );
# widget.SetOrientationMarker( axes );
# widget.SetInteractor( renderWindowInteractor );
# widget.SetEnabled( 1 );

renderer.AddActor(actor)
renderer.AddActor(tubeActor)
renderWindow.Render()
renderWindowInteractor.Start()
