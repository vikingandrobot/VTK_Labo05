# VTK - Labo 5 - Planeur
# Author : Sathiya Kirushnapillai, Mathieu Monteverde

import vtk
import numpy as np
import pyproj
import glider

from keypressInteractorStyle import KeyPressInteractorStyle


# The Map RT90 coordinates (Given data)
RT90_MAP_TOP_LEFT = (1349340, 7022573)
RT90_MAP_TOP_RIGHT = (1371573, 7022967)
RT90_MAP_BOTTOM_RIGHT = (1371835, 7006362)
RT90_MAP_BOTTOM_LEFT = (1349602, 7005969 )

# The min and max on x and y axis of the Map
RT90_MAP_MIN_X = min(RT90_MAP_TOP_LEFT[0], RT90_MAP_BOTTOM_LEFT[0])
RT90_MAP_MAX_X = max(RT90_MAP_TOP_RIGHT[0], RT90_MAP_BOTTOM_RIGHT[0])
RT90_MAP_MIN_Y = min(RT90_MAP_BOTTOM_RIGHT[1], RT90_MAP_BOTTOM_LEFT[1])
RT90_MAP_MAX_Y = max(RT90_MAP_TOP_RIGHT[1], RT90_MAP_TOP_LEFT[1])


def convertRT90ToWGS84(x, y):
  """ Convert the RT90 to Longitude/Latitude coordinates
  
  Args:
    x: meters
    y: meters

  Returns:
    A tuple (longitude, latitude)
  """

  rt90Proj = pyproj.Proj(init='epsg:3021')
  wgs84 = pyproj.Proj(init="epsg:4326")

  return pyproj.transform(rt90Proj, wgs84, x, y)


def mapCoordinatesToTexture(lat, longitude):
  """ This function maps (latitude, longitude) coordinates (wgs84) to the image 
  texture coordinates (x: [0, 1] and y: [0, 1]). 

  It first converts the given latitude and longitude to a RT90 point. Then if 
  the point is inside the map texture rectange (delimited by known and provided 
  RT90 coordinates for this lab) it returns its relative position inside this 
  rectangle (x: [0, 1], y: [0, 1]) corresponding to the texture coordinates for 
  this point. If the point is outside, it returns a (-1, -1) point.

  Args:
    lat: latitude
    longitude: longitude

  Returns: 
    A tuple containing the texture coordinate inside the map image or (-1, -1) 
    if the given point is outside of the map.
  """

  # Convert the wgs84 point to RT90
  rt90Proj = pyproj.Proj(init='epsg:3021')
  wgs84 = pyproj.Proj(init="epsg:4326")
  (tx, ty) = pyproj.transform(wgs84, rt90Proj, longitude, lat)

  # Check if the point is inside the map area
  if (tx > RT90_MAP_MIN_X and 
      tx < RT90_MAP_MAX_X and 
      ty > RT90_MAP_MIN_Y and 
      ty < RT90_MAP_MAX_Y):

    # Compute the relative texture coordinates
    cx = (tx - RT90_MAP_MIN_X) / (RT90_MAP_MAX_X - RT90_MAP_MIN_X)
    cy = (ty - RT90_MAP_MIN_Y) / (RT90_MAP_MAX_Y - RT90_MAP_MIN_Y)

    return (cx, cy)

  else:
    return (-1, -1)


def main():
  """ Main function """

  EARTH_RADIUS = 6371009


  # Map's coordinates converted to WGS84
  lo, la = convertRT90ToWGS84(RT90_MAP_TOP_LEFT[0], RT90_MAP_TOP_LEFT[1])
  MAP_LEFT_TOP_COORD = (la, lo)

  lo, la = convertRT90ToWGS84(RT90_MAP_TOP_RIGHT[0], RT90_MAP_TOP_RIGHT[1])
  MAP_RIGHT_TOP_COORD =   (la, lo)

  lo, la = convertRT90ToWGS84(RT90_MAP_BOTTOM_LEFT[0], RT90_MAP_BOTTOM_LEFT[1])
  MAP_LEFT_BOTTOM_COORD = (la, lo)

  lo, la = convertRT90ToWGS84(RT90_MAP_BOTTOM_RIGHT[0], RT90_MAP_BOTTOM_RIGHT[1])
  MAP_RIGHT_BOTTOM_COORD = (la, lo)

  MAP_MIN_X = min(MAP_LEFT_TOP_COORD[1], MAP_LEFT_BOTTOM_COORD[1])
  MAP_MAX_X = max(MAP_RIGHT_TOP_COORD[1], MAP_RIGHT_BOTTOM_COORD[1])
  MAP_MIN_Y = min(MAP_LEFT_BOTTOM_COORD[0], MAP_RIGHT_BOTTOM_COORD[0])
  MAP_MAX_Y = max(MAP_LEFT_TOP_COORD[0], MAP_RIGHT_TOP_COORD[0])


  # Elevation model coordinates (Given data)
  ELEVATION_MIN_X = 10
  ELEVATION_MAX_X = 15
  ELEVATION_MIN_Y = 60
  ELEVATION_MAX_Y = 65


  # Elevation model size (Square map)
  ROWS = 6000
  COLS = 6000


  # Delta unit per cell
  longitudeDelta = (ELEVATION_MAX_X - ELEVATION_MIN_X) / ROWS
  latitudeDelta = (ELEVATION_MAX_Y - ELEVATION_MIN_Y) / COLS


  # Cutted square coordinates
  minLongitude = int((MAP_MIN_X - ELEVATION_MIN_X) / longitudeDelta)
  maxLongitude = int((MAP_MAX_X - ELEVATION_MIN_X) / longitudeDelta)
  midLongitude = minLongitude + ((maxLongitude - minLongitude) / 2)

  minLatitude = int((MAP_MIN_Y - ELEVATION_MIN_Y) / latitudeDelta)
  maxLatitude = int((MAP_MAX_Y - ELEVATION_MIN_Y) / latitudeDelta)
  midLatitude = minLatitude + ((maxLatitude - minLatitude) / 2)


  # Load the elevation model
  elevationModel = np.fromfile("data/EarthEnv-DEM90_N60E010.bil", dtype=np.int16)

  # Create a point in the middle of the map, 500 m above the radius of the Earth
  middlePoint = [EARTH_RADIUS + 500, 0, 0]
  rotate1 = vtk.vtkTransform()
  rotate1.RotateZ(midLatitude)
  rotate2 = vtk.vtkTransform()
  rotate2.RotateY(-midLongitude)
  focalPoint = rotate2.TransformPoint(
    rotate1.TransformPoint(
      middlePoint
    )
  )

  # Create points
  print("Building points...")
  points = vtk.vtkPoints()

  # Texture coordinates values
  textureCoordinates = vtk.vtkFloatArray()
  textureCoordinates.SetNumberOfComponents(2)

  for y in range(COLS - maxLatitude, COLS - minLatitude):
    transform2 = vtk.vtkTransform()
    transform2.RotateZ(ELEVATION_MAX_Y - y * latitudeDelta)

    transform1 = vtk.vtkTransform()
    transform1.RotateY(MAP_MIN_X)

    for x in range(minLongitude, maxLongitude):
      p = [EARTH_RADIUS + elevationModel[y * ROWS + x], 0, 0]


      transform1.RotateY(longitudeDelta)

      # Apply tranformation
      points.InsertNextPoint(
          transform1.TransformPoint(
              transform2.TransformPoint(
                  p
              )
          )
      )

      # Compute texture coordinates
      cx, cy = mapCoordinatesToTexture(
        ELEVATION_MAX_Y - (y + 1) * latitudeDelta,
        ELEVATION_MIN_X + (x - 1) * longitudeDelta
      )

      textureCoordinates.InsertNextTuple((cx, cy))
  print("Done.")

  # Build the structured grid with the points
  print("Building structuredGrid")
  sg = vtk.vtkStructuredGrid()
  sg.SetDimensions(maxLongitude-minLongitude, maxLatitude-minLatitude, 1)
  sg.SetPoints(points)
  sg.GetPointData().SetTCoords(textureCoordinates) # Set texture coordinates
  print("Done.")

  # Load texture from JPEG
  JPEGReader = vtk.vtkJPEGReader()
  JPEGReader.SetFileName("data/glider_map.jpg")
  texture = vtk.vtkTexture()
  texture.SetInputConnection(JPEGReader.GetOutputPort())

  # Create an actor from the grid and texture
  mapper = vtk.vtkDataSetMapper()
  mapper.SetInputData(sg)
  actor = vtk.vtkActor()
  actor.SetMapper(mapper)
  actor.SetTexture(texture)
  actor.GetProperty().SetPointSize(3)

  # Load the glider
  gliderData = glider.loadGliderTrajectory("data/vtkgps.txt")
  colors = glider.computeGliderTrajectoryColors(
    gliderData.gliderTrajectory, 
    gliderData.minVerticalSpeed, 
    gliderData.maxVerticalSpeed
  )
  glidersActors = glider.createActors(gliderData.vtkPoints, colors)

  # Add actors to render
  renderer = vtk.vtkRenderer()
  renderer.AddActor(actor)
  renderer.AddActor(glidersActors[0])
  renderer.AddActor(glidersActors[1])

  # Create a Render Window
  renderWindow = vtk.vtkRenderWindow()
  renderWindow.SetSize(1200, 720)
  renderWindow.AddRenderer(renderer)
  renderWindowInteractor = vtk.vtkRenderWindowInteractor()
  renderWindowInteractor.SetRenderWindow(renderWindow)

  # Positionning the camera
  renderer.SetBackground(0, 0, 0)
  renderer.GetActiveCamera().SetFocalPoint(focalPoint)
  renderer.GetActiveCamera().SetRoll(-50)
  renderer.GetActiveCamera().Elevation(-60)
  renderer.GetActiveCamera().Dolly(0.1)
  renderer.ResetCamera()

  # Here we specify a particular interactor style.
  style = KeyPressInteractorStyle(renderWindow, renderWindowInteractor)
  renderWindowInteractor.SetInteractorStyle(style)

  renderWindow.Render()
  renderWindowInteractor.Start()


if __name__ == "__main__":
	main()

