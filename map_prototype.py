import vtk
import numpy as np
import pyproj
import glider

from keypressInteractorStyle import KeyPressInteractorStyle

RT90_MAP_MIN_X = 1349340
RT90_MAP_MAX_X = 1371835
RT90_MAP_MIN_Y = 7005969
RT90_MAP_MAX_Y = 7022967

def mapCoordinatesToTexture(lat, longitude):
  """ This function maps (latitude, longitude) coordinates (wgs84) to 
  the image texture coordinates (x: [0, 1] and y: [0, 1]). 
  It first converts the 
  given latitude and longitude to a RT90 point. Then if the point is inside 
  the map texture rectange (delimited by known and provided RT90 coordinates for this lab)
  it returns its relative position inside this rectangle (x: [0, 1], y: [0, 1]) corresponding
  to the texture coordinates for this point. If the point is outside, it returns a
  (-1, -1) point.
  Args:
    lat: latitude
    longitude: longitude
  Returns: 
    A tuple containing the texture coordinate inside the map image or (-1, -1) if the given point
    is outside of the map.
  """
  # Convert the wgs84 point to RT90
  rt90Proj = pyproj.Proj(init='epsg:3021')
  wgs84 = pyproj.Proj(init="epsg:4326")
  (tx, ty) = pyproj.transform(wgs84, rt90Proj, longitude, lat)

  # Check if the point is inside the map area
  if (tx > RT90_MAP_MIN_X and tx < RT90_MAP_MAX_X and ty > RT90_MAP_MIN_Y and ty < RT90_MAP_MAX_Y):
    # Compute the relative texture coordinates
    cx = (tx - RT90_MAP_MIN_X) / (RT90_MAP_MAX_X - RT90_MAP_MIN_X)
    cy = (ty - RT90_MAP_MIN_Y) / (RT90_MAP_MAX_Y - RT90_MAP_MIN_Y)

    return (cx, cy)

  else:
    return (-1, -1)


def main():
  FILENAME = "data/EarthEnv-DEM90_N60E010.bil"

  EARTH_RADIUS = 6371009

  # Map (Rectangular) coordinates
  MAP_LEFT_TOP_COORD = (63.282190416278205, 12.804928280214138)
  MAP_RIGHT_TOP_COORD =   (63.29437070004316, 13.247244781368963)
  MAP_LEFT_BOTTOM_COORD = (63.133525618051515, 12.825512878974331)
  MAP_RIGHT_BOTTOM_COORD = (63.14562556295812, 13.26557520635262)
  MAP_MIN_X = min(MAP_LEFT_TOP_COORD[1], MAP_LEFT_BOTTOM_COORD[1])
  MAP_MAX_X = max(MAP_RIGHT_TOP_COORD[1], MAP_RIGHT_BOTTOM_COORD[1])
  MAP_MIN_Y = min(MAP_LEFT_BOTTOM_COORD[0], MAP_RIGHT_BOTTOM_COORD[0])
  MAP_MAX_Y = max(MAP_LEFT_TOP_COORD[0], MAP_RIGHT_TOP_COORD[0])

  # Elevation model coordinates
  ELEVATION_LEFT_TOP_COORD = (65, 10)
  ELEVATION_RIGHT_TOP_COORD = (65, 15)
  ELEVATION_LEFT_BOTTOM_COORD = (60, 10)
  ELEVATION_RIGHT_BOTTOM_COORD = (60, 15)
  ELEVATION_MIN_X = ELEVATION_LEFT_TOP_COORD[1]
  ELEVATION_MAX_X = ELEVATION_RIGHT_TOP_COORD[1]
  ELEVATION_MIN_Y = ELEVATION_LEFT_BOTTOM_COORD[0]
  ELEVATION_MAX_Y = ELEVATION_LEFT_TOP_COORD[0]

  # Elevation model size (Square map)
  rows = 6000
  cols = 6000

  # Unit per cell
  longitudeDelta = (ELEVATION_MAX_X - ELEVATION_MIN_X) / rows
  latitudeDelta = (ELEVATION_MAX_Y - ELEVATION_MIN_Y) / cols

  # Cutted square coordinates
  minLongitude = int((MAP_MIN_X - ELEVATION_MIN_X) / longitudeDelta)
  maxLongitude = int((MAP_MAX_X - ELEVATION_MIN_X) / longitudeDelta)
  midLongitude = minLongitude + ((maxLongitude - minLongitude) / 2)

  print(minLongitude)
  print(maxLongitude)

  minLatitude = int((MAP_MIN_Y - ELEVATION_MIN_Y) / latitudeDelta)
  maxLatitude = int((MAP_MAX_Y - ELEVATION_MIN_Y) / latitudeDelta)
  midLatitude = minLatitude + ((maxLatitude - minLatitude) / 2)

  # Load the elevation model
  elevationModel = np.fromfile(FILENAME, dtype=np.int16)

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
  textureCoordinates.SetName("TextureCoordinates")

  for y in range(cols - maxLatitude, cols - minLatitude):
    transform2 = vtk.vtkTransform()
    transform2.RotateZ(ELEVATION_MAX_Y - y * latitudeDelta)#MAP_MIN_Y)

    transform1 = vtk.vtkTransform()
    transform1.RotateY(MAP_MIN_X)

    for x in range(minLongitude, maxLongitude):
      p = [EARTH_RADIUS + elevationModel[y * rows + x], 0, 0]


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
      (cx, cy) = mapCoordinatesToTexture(
          ELEVATION_MAX_Y - (y + 1) * latitudeDelta,
          ELEVATION_MIN_X + (x - 1) * longitudeDelta
          )

      textureCoordinates.InsertNextTuple((cx, cy))
  print("Done.")

  # Reader for JPEG image
  jPEGReader = vtk.vtkJPEGReader()
  jPEGReader.SetFileName("data/glider_map.jpg")


  print("Building structuredGrid")
  sg = vtk.vtkStructuredGrid()
  sg.SetDimensions(maxLongitude-minLongitude, maxLatitude-minLatitude, 1)
  sg.SetPoints(points)
  print("Done.")

  gf = vtk.vtkStructuredGridGeometryFilter()
  gf.SetInputData(sg)
  gf.Update()

  # Set texture coordinates
  sg.GetPointData().SetTCoords(textureCoordinates)
  texture = vtk.vtkTexture()
  texture.SetInputConnection(jPEGReader.GetOutputPort())


  mapper = vtk.vtkPolyDataMapper()
  mapper.SetInputConnection(gf.GetOutputPort())
  actor = vtk.vtkActor()
  actor.SetMapper(mapper)
  actor.GetProperty().SetPointSize(3)
  actor.SetTexture(texture)

  gliderData = glider.loadGliderTrajectory("data/vtkgps.txt")
  colors = glider.computeGliderTrajectoryColors(gliderData.gliderTrajectory, gliderData.minVerticalSpeed, gliderData.maxVerticalSpeed)
  glidersActors = glider.createActors(gliderData.vtkPoints, colors)

  renderer = vtk.vtkRenderer()
  renderer.AddActor(actor)
  renderer.AddActor(glidersActors[0])
  renderer.AddActor(glidersActors[1])

  renderWindow = vtk.vtkRenderWindow()
  renderWindow.SetSize(1200, 720)
  renderWindow.AddRenderer(renderer)
  renderWindowInteractor = vtk.vtkRenderWindowInteractor()
  renderWindowInteractor.SetRenderWindow(renderWindow)

  # Positionning the camera
  renderer.SetBackground(0, 0, 0)
  #renderer.GetActiveCamera().SetPosition(EARTH_RADIUS + 1000, 0, 0)
  #renderer.GetActiveCamera().Elevation(midLatitude)
  #renderer.GetActiveCamera().Azimuth(midLongitude)
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
