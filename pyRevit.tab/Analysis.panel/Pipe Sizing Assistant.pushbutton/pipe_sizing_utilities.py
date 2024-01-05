from pyrevit import HOST_APP, DB, UI, forms
from System import Guid
from pyrevit.framework import wpf
import os.path as op
from  System.Windows import Media

white = DB.Color(255,255,255)

def set_line_color_for_element(element_id, document, color):
    ogs = DB.OverrideGraphicSettings()
    ogs.SetProjectionLineColor(color)
    document.ActiveView.SetElementOverrides(element_id, ogs)
    
def reset_line_color_for_element(element_id, document):
    ogs = DB.OverrideGraphicSettings()
    document.ActiveView.SetElementOverrides(element_id, ogs)
    
def colorize_one_pipe(pipe, document, pipe_data):
    fixture_units = pipe.get_Parameter(DB.BuiltInParameter.RBS_PIPE_FIXTURE_UNITS_PARAM).AsDouble()
    diameter = pipe.get_Parameter(DB.BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).AsDouble()
    
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
        
def colorize_all_pipes(document, pipe_data):
    pipe_collector = DB.FilteredElementCollector(document).OfCategory(DB.BuiltInCategory.OST_PipeCurves).WhereElementIsNotElementType()
        
    t = DB.Transaction(document, 'Pipe Colorizing')
    t.Start()

    for pipe in pipe_collector:
        colorize_one_pipe(pipe, document, pipe_data)

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
    def __init__(self, application_id, pipe_data):
        self.app_id = application_id
        self.pipe_data = pipe_data
        self.updater_id = DB.UpdaterId(application_id, Guid("d8e9b0e5-fd6f-40b6-9924-601a3b447787"))

    def Execute(self, data):
        document = data.GetDocument()
        
        pipe_ids = data.GetModifiedElementIds()
        
        for pipe_id in pipe_ids:
            pipe = document.GetElement(pipe_id)
            
            colorize_one_pipe(pipe, document, self.pipe_data)
            
            
    def GetAdditionalInformation(self):
        return "Pipe graphics updater: updates display color for pipes to help with sizing"

    def GetChangePriority(self):
        return DB.ChangePriority.MEPAccessoriesFittingsSegmentsWires

    def GetUpdaterId(self):
        return self.updater_id

    def GetUpdaterName(self):
        return "Pipe Graphics Updater"

def register_pipe_graphics_updater(pipe_data):
    pipe_filter = DB.ElementCategoryFilter(DB.BuiltInCategory.OST_PipeCurves)
    pipe_updater = PipeGraphicsUpdater(HOST_APP.app.ActiveAddInId, pipe_data)
    parameter_id = DB.ElementId(DB.BuiltInParameter.RBS_PIPE_DIAMETER_PARAM)
    # Make sure we're not trying to reregister the same updater
    u_r = DB.UpdaterRegistry
    if u_r.IsUpdaterRegistered(pipe_updater.GetUpdaterId()):
        u_r.UnregisterUpdater(pipe_updater.GetUpdaterId())
    u_r.RegisterUpdater(pipe_updater)
    u_r.SetIsUpdaterOptional(pipe_updater.GetUpdaterId(), True)
    u_r.AddTrigger(pipe_updater.GetUpdaterId(), pipe_filter, DB.Element.GetChangeTypeParameter(parameter_id))

def unregister_pipe_graphics_updater():
    pipe_updater = PipeGraphicsUpdater(HOST_APP.app.ActiveAddInId, [])
    
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

class Size:
    def __init__(self, color, name, max_fu):
        self.name = name
        self.color = color
        self.max_fu = max_fu

class SizingWindow(forms.WPFWindow):
    def __init__(self, pipe_data):
        wpf.LoadComponent(self, op.join(op.dirname(__file__),'pipe_sizing_window.xaml'))
        self.pipe_data = pipe_data
        self.set_size_list()
        
    def set_size_list(self):
        sizes = [Size(white, 'Size', 'Max FU')]
        
        for data in self.pipe_data:
            color = Media.SolidColorBrush(Media.Color.FromArgb(0xFF, data.color.Red, data.color.Green, data.color.Blue))
            max_fu_value =  int(data.max_fu) if data.max_fu < 99999 else "Infinity"
            max_fu_display = '({})'.format(max_fu_value)
            sizes.append(Size(color, data.name, max_fu_display))

        self.SizeListBox.ItemsSource = sizes

    def window_closing(self, sender, args):
        turn_off_assistant_event.Raise()