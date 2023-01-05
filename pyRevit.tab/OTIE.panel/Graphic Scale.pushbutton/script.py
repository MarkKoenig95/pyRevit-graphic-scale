from pyrevit import DB
import os
from graphic_scale_utilities import update_all_scale_values, register_graphic_scale_updater

__title__ = "Graphic\nScale"

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document
sel = __revit__.ActiveUIDocument.Selection

update_all_scale_values(app, doc, None)
register_graphic_scale_updater()