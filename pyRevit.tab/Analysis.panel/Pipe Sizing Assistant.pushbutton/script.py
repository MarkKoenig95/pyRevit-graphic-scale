from settings_utilities import SettingsWindow
__title__ = "Pipe Sizing\nAssistant"

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document

ui = SettingsWindow(doc)
ui.show(modal=True)
