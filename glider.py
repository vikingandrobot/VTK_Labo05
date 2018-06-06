import vtk
import datetime as dt
import pyproj

LONGITUDE_INDEX = 0
LATITUDE_INDEX = 1
ALTITUDE_INDEX = 2
DATE_TIME_INDEX = 3

EARTH_RADIUS = 6371009

class GliderTrajectory(object):
    pass


def computeVerticalSpeed(gliderTrajectory, index):
    lastDateTime = gliderTrajectory[index - 1][DATE_TIME_INDEX]
    dateTime = gliderTrajectory[index][DATE_TIME_INDEX]
    lastAltitude = gliderTrajectory[index - 1][ALTITUDE_INDEX]
    altitude = gliderTrajectory[index][ALTITUDE_INDEX]
    return (altitude - lastAltitude) / (dateTime - lastDateTime).total_seconds()


def loadGliderTrajectory(filename):
    vtkPoints = vtk.vtkPoints()
    gliderTrajectory = []
    minVerticalSpeed = 0
    maxVerticalSpeed = 0
    lineCount = -1

    with open(filename) as fileIn:
        for line in fileIn:
            # Ignore first line
            if (lineCount == -1):
                lineCount += 1
                continue
            lineCount += 1

            # Get values of a line as an array of String
            values = line.split()
            # Read position and time coordinates
            coordinates = []
            coordinates.append(int(values[1]))
            coordinates.append(int(values[2]))
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

            # Add the coordinates
            gliderTrajectory.append(coordinates)

            # VTK points
            rt90Proj = pyproj.Proj(init='epsg:3021')
            wgs84 = pyproj.Proj(init="epsg:4326")
            longlat = pyproj.transform(rt90Proj, wgs84, int(values[1]), int(values[2]))
            #print(longlat)
            p = [EARTH_RADIUS + coordinates[ALTITUDE_INDEX], 0, 0]
            transform1 = vtk.vtkTransform()
            transform1.RotateY(longlat[0])
            transform2 = vtk.vtkTransform()
            transform2.RotateZ(longlat[1])
            vtkPoints.InsertNextPoint(transform1.TransformPoint(transform2.TransformPoint(p)))

            # Min / Max delta
            index = lineCount - 1
            if (index > 0):
                verticalSpeed = computeVerticalSpeed(gliderTrajectory, index)

                if (verticalSpeed < minVerticalSpeed):
                    minVerticalSpeed = verticalSpeed
                if (verticalSpeed > maxVerticalSpeed):
                    maxVerticalSpeed = verticalSpeed

    result = GliderTrajectory()
    result.vtkPoints = vtkPoints
    result.gliderTrajectory = gliderTrajectory
    result.minVerticalSpeed = minVerticalSpeed
    result.maxVerticalSpeed = maxVerticalSpeed
    return result


def computeGliderTrajectoryColors(gliderTrajectory, minVerticalSpeed, maxVerticalSpeed):
    lutAsc = vtk.vtkLookupTable()
    lutAsc.SetTableRange(0, maxVerticalSpeed)
    lutAsc.SetHueRange(1/6, 0)
    lutAsc.Build()

    lutDesc = vtk.vtkLookupTable()
    lutDesc.SetTableRange(minVerticalSpeed, 0)
    lutDesc.SetHueRange(3/6, 2/6)
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
            if (verticalSpeed >= 0):
                lutAsc.GetColor(verticalSpeed, dcolor)
            else:
                lutDesc.GetColor(verticalSpeed, dcolor)
        color = [0, 0, 0]
        for k in range(0, 3):
            color[k] = 255 * dcolor[k]

        colors.InsertNextTuple(color)
    return colors


def createActors(vtkPoints, colors, gliderTrajectory):
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

    return (actor, tubeActor)