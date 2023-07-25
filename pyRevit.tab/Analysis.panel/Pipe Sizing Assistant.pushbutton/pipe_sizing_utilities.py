from pyrevit import HOST_APP, DB, UI, forms
from System import Guid
from pyrevit.framework import wpf
import os.path as op
from  System.Windows import Media

black = DB.Color(0,0,0)
white = DB.Color(255,255,255)

class PipeSize:
    def __init__(self, name, value, color):
        self.name = name
        self.value = value
        self.color = color

pipe_sizes = [
    PipeSize("1/2",   0.042, DB.Color(255, 0, 0)),
    PipeSize("3/4",   0.063, DB.Color(0, 255, 0)),
    PipeSize("1",     0.084, DB.Color(0, 170, 221)),
    PipeSize("1 1/4", 0.105, DB.Color(255, 255, 0)),
    PipeSize("1 1/2", 0.126, DB.Color(255, 0, 255)),
    PipeSize("2",     0.167, DB.Color(0, 255, 255)),
    PipeSize("2 1/2", 0.209, DB.Color(255, 130, 0)),
    PipeSize("3",     0.251, DB.Color(130, 0, 255)),
    PipeSize("4",     0.334, DB.Color(130, 130, 0)),
    PipeSize("6",     0.501, DB.Color(119, 187, 17)),
    PipeSize("8",     0.667, DB.Color(238, 0, 102)),
    PipeSize("10",    0.834, DB.Color(0, 66, 130 )),
    PipeSize("12",    1.001, DB.Color(192, 192, 192)),
]

class PipeData:
    def __init__(self, size, max_fu, color):
        self.size = size
        self.max_fu = max_fu
        self.color = color

pipe_data = [
        PipeData(pipe_sizes[0].value, 4, pipe_sizes[0].color),
        PipeData(pipe_sizes[1].value, 8, pipe_sizes[1].color),
        PipeData(pipe_sizes[2].value, 12, pipe_sizes[2].color),
        PipeData(pipe_sizes[3].value, 17, pipe_sizes[3].color),
        PipeData(pipe_sizes[4].value, 22, pipe_sizes[4].color),
        PipeData(pipe_sizes[5].value, 37, pipe_sizes[5].color),
        PipeData(pipe_sizes[6].value, 86, pipe_sizes[6].color),
        PipeData(pipe_sizes[7].value, 200, pipe_sizes[7].color),
        PipeData(pipe_sizes[8].value, 561, pipe_sizes[8].color),
]

def set_line_color_for_element(element_id, document, color):
    ogs = DB.OverrideGraphicSettings()
    ogs.SetProjectionLineColor(color)
    document.ActiveView.SetElementOverrides(element_id, ogs)
    
def reset_line_color_for_element(element_id, document):
    ogs = DB.OverrideGraphicSettings()
    document.ActiveView.SetElementOverrides(element_id, ogs)
    
def colorize_one_pipe(pipe, document):
    fixture_units = pipe.get_Parameter(DB.BuiltInParameter.RBS_PIPE_FIXTURE_UNITS_PARAM).AsDouble()
    diameter = pipe.get_Parameter(DB.BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).AsDouble()
    
    if fixture_units == 0:
        set_line_color_for_element(pipe.Id, document, black)
        return
    
    min_size = 0

    for data in pipe_data:
        if fixture_units > data.max_fu:
            min_size = data.size
            continue
        
        if (diameter <= data.size) and (diameter > min_size):
            set_line_color_for_element(pipe.Id, document, white)
            break
            
        set_line_color_for_element(pipe.Id, document, data.color)
        break
        
def colorize_all_pipes(document):
    pipe_collector = DB.FilteredElementCollector(document).OfCategory(DB.BuiltInCategory.OST_PipeCurves).WhereElementIsNotElementType()
        
    t = DB.Transaction(document, 'Pipe Colorizing')
    t.Start()

    for pipe in pipe_collector:
        colorize_one_pipe(pipe, document)

    t.Commit()
    t.Dispose()

def decolorize_all_pipes(document):
    pipe_collector = DB.FilteredElementCollector(document).OfCategory(DB.BuiltInCategory.OST_PipeCurves).WhereElementIsNotElementType()
        
    t = DB.Transaction(document, 'Reseting Pipe Colors')
    t.Start()

    for pipe in pipe_collector:
        reset_line_color_for_element(pipe.Id, document)

    t.Commit()
    t.Dispose()

class PipeGraphicsUpdater(DB.IUpdater):
    def __init__(self, application_id):
        self.app_id = application_id
        self.updater_id = DB.UpdaterId(application_id, Guid("d8e9b0e5-fd6f-40b6-9924-601a3b447787"))

    def Execute(self, data):
        document = data.GetDocument()
        
        pipe_ids = data.GetModifiedElementIds()
        
        for pipe_id in pipe_ids:
            pipe = document.GetElement(pipe_id)
            
            colorize_one_pipe(pipe, document)
            
            
    def GetAdditionalInformation(self):
        return "Pipe graphics updater: updates display color for pipes to help with sizing"

    def GetChangePriority(self):
        return DB.ChangePriority.MEPAccessoriesFittingsSegmentsWires

    def GetUpdaterId(self):
        return self.updater_id

    def GetUpdaterName(self):
        return "Pipe Graphics Updater"

def register_pipe_graphics_updater():
    pipe_filter = DB.ElementCategoryFilter(DB.BuiltInCategory.OST_PipeCurves)
    pipe_updater = PipeGraphicsUpdater(HOST_APP.app.ActiveAddInId)
    parameter_id = DB.ElementId(DB.BuiltInParameter.RBS_PIPE_DIAMETER_PARAM)
    # Make sure we're not trying to reregister the same updater
    if DB.UpdaterRegistry.IsUpdaterRegistered(pipe_updater.GetUpdaterId()):
        DB.UpdaterRegistry.UnregisterUpdater(pipe_updater.GetUpdaterId())
    DB.UpdaterRegistry.RegisterUpdater(pipe_updater)
    DB.UpdaterRegistry.SetIsUpdaterOptional(pipe_updater.GetUpdaterId(), True)
    DB.UpdaterRegistry.AddTrigger(pipe_updater.GetUpdaterId(), pipe_filter, DB.Element.GetChangeTypeParameter(parameter_id))

def unregister_pipe_graphics_updater():
    pipe_updater = PipeGraphicsUpdater(HOST_APP.app.ActiveAddInId)
    if DB.UpdaterRegistry.IsUpdaterRegistered(pipe_updater.GetUpdaterId()):
        DB.UpdaterRegistry.UnregisterUpdater(pipe_updater.GetUpdaterId())

class TurnOffAssistant(UI.IExternalEventHandler):
    def Execute(self, uiapp):
            uidoc = uiapp.ActiveUIDocument
            document = uidoc.Document
            unregister_pipe_graphics_updater()
            decolorize_all_pipes(document)
        
    def GetName(self):
        return "Turn Off Pipe Sizing Assistant Event"

turn_off_assistant_event = UI.ExternalEvent.Create(TurnOffAssistant())

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

class Field:
    def __init__(self, name, length, color):
        self.name = name
        self.length = length
        self.color = color

class Window(forms.WPFWindow):
    def __init__(self):
        wpf.LoadComponent(self, op.join(op.dirname(__file__),'ui.xaml'))

        fields = []
        
        for pipe_size in pipe_sizes:
            color = Media.SolidColorBrush(Media.Color.FromArgb(0xFF, pipe_size.color.Red, pipe_size.color.Green, pipe_size.color.Blue))
            fields.append(Field(pipe_size.name, 100, color))

        self.FieldsListBox.ItemsSource = fields

    def window_closing(self, sender, args):
            turn_off_assistant_event.Raise()

    def something_click(self, sender, args):
            turn_off_assistant_event.Raise()