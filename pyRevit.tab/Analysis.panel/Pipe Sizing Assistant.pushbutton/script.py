from pipe_sizing_utilities import register_pipe_graphics_updater, colorize_all_pipes, Window

__title__ = "Pipe Sizing\nAssistant"

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document

register_pipe_graphics_updater()
colorize_all_pipes(doc)

ui = Window()
ui.show(modal=False)