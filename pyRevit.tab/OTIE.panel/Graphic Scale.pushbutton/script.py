from pyrevit import DB, forms
from graphic_scale_utilities import add_view_title_family, update_all_scale_values, register_graphic_scale_updater, check_if_has_shared_parameters

__title__ = "Graphic\nScale"

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document

should_set_up = True

view_collector = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Views).WhereElementIsNotElementType()
has_shared_parameters = check_if_has_shared_parameters(view_collector)
if not has_shared_parameters:
    should_set_up = forms.alert("Would you like to set up this project to use an automatic view title graphic scale updater? "
                    "This add-in only works if users have it installed, otherwise graphic scales may not be updated "
                    "when a user changes a view's scale.\n\n"

                    "Do you still want to set up this extension?",
                    ok=False, yes=True, no=True)

if should_set_up:
    add_view_title_family(doc)
    update_all_scale_values(app, doc, view_collector)
    register_graphic_scale_updater()
    forms.alert("This project is now set up to use the automatic view title graphic scale updater. "
                "Please make sure to use the correct family for your view titles and feel free to "
                "edit the view title family to your project specific needs.")