from pyrevit import DB
import os
#from graphic_scale.utilities import add_shared_parameters

__title__ = "Graphic\nScale"

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document
sel = __revit__.ActiveUIDocument.Selection
print('adding shared parameters')
add_shared_parameters(app,doc)