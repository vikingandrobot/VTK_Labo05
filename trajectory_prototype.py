import numpy as np

LONGITUDE_INDEX = 0
LATITUDE_INDEX = 1
ALTITUDE_INDEX = 2

gliderTrajectory = []
lineCount = 0
with open("data/vtkgps_small.txt") as fileIn:
    for line in fileIn:
        if (lineCount == 0):
            lineCount += 1
            continue

        values = line.split()
        coordinates = []
        coordinates.append(int(values[1]))
        coordinates.append(int(values[2]))
        coordinates.append(float(values[3]))
        gliderTrajectory.append(coordinates)
