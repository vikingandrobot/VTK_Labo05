# VTK - Labo 5 - Planeur
# Author : Sathiya Kirushnapillai, Mathieu Monteverde

import vtk


class KeyPressInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    """
    An interactor style class extending vtkInteractorStyleTrackballCamera
    that saves a screenshot of the window when the 's' or Return key are 
    pressed.
    """

    def __init__(self, renWin, parent=None):
        self.parent = parent
        self.AddObserver("KeyPressEvent", self.keyPressEvent)
        self.OUTPUT_FILE_NAME = "map_output.png"
        self.renWin = renWin


    def keyPressEvent(self, obj, event):
        key = self.parent.GetKeySym()
        if (key == "Return" or key == "s"):
            # Resources to save the scene to a PDF file
            w2if = vtk.vtkWindowToImageFilter()
            w2if.SetInput(self.renWin)
            w2if.Update()

            writer = vtk.vtkPNGWriter()
            writer.SetFileName(self.OUTPUT_FILE_NAME)
            writer.SetInputConnection(w2if.GetOutputPort())
            writer.Write()
