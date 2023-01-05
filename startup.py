from pyrevit import HOST_APP, framework, DB
import os
from System import Guid

absolute_path = os.path.dirname(os.path.abspath(__file__))
relative_path = "Supporting Files\Graphic Scale Shared Parameters.txt"
mySPFN = os.path.join(absolute_path, relative_path)

shared_parameters_group_name = "Graphic Scale"

one_inch = 0.083333333334

imperial_sizes = [(one_inch * 0.25, "o_0.25in Scale Text"),
				 (one_inch * 0.375, "o_0.375in Scale Text"),
				 (one_inch * 0.5, "o_0.5in Scale Text"),
				 (one_inch * 0.75, "o_0.75in Scale Text"),
				 (one_inch * 1, "o_1.0in Scale Text"),
				 (one_inch * 1.5, "o_1.5in Scale Text"),
				 (one_inch * 2, "o_2.0in Scale Text"),
				 (one_inch * 2.25, "o_2.25in Scale Text")]

def get_parameter_names():
	parameter_names = []
	for size in imperial_sizes:
		parameter_name = size[1]
		parameter_names.append(parameter_name)
	return parameter_names

def add_shared_parameters(app, doc):
	cat = doc.Settings.Categories.get_Item(DB.BuiltInCategory.OST_Views)
	
	previous_SPFN = app.SharedParametersFilename

	app.SharedParametersFilename = mySPFN

	shared_params_file = app.OpenSharedParameterFile()

	#app.SharedParametersFilename = previous_SPFN

	shared_params_group = shared_params_file.Groups.get_Item(shared_parameters_group_name)

	parameter_names = get_parameter_names()

	t = DB.Transaction(doc, 'Add Graphic Scale Shared Parameters')
 
	t.Start()

	for param in parameter_names:
		definition = shared_params_group.Definitions.get_Item(param)

		cat_set = app.Create.NewCategorySet()

		cat_set.Insert(cat)
 
		binding = app.Create.NewInstanceBinding(cat_set)

		doc.ParameterBindings.Insert(definition, binding)
 
	t.Commit()
	t.Dispose()

def GetSegmentLengthTextFromScaleValue(scaleValue, sheetSegmentLength):
	segmentLengthText = ''
	
	drawingSegmentLength = (scaleValue * sheetSegmentLength)
	drawingSegmentLengthFeet = drawingSegmentLength - (drawingSegmentLength % 1)
	drawingSegmentLengthRoughInches = (drawingSegmentLength % 1) * 12
	drawingSegmentLengthInches = round(drawingSegmentLengthRoughInches)

	if drawingSegmentLengthFeet > 0:
		segmentLengthText += drawingSegmentLengthFeet.ToString() + "'"

	if drawingSegmentLengthInches > 0:
		if segmentLengthText:
			segmentLengthText += "-"
		if drawingSegmentLengthRoughInches >= 1:
			segmentLengthText += drawingSegmentLengthInches.ToString() + '"'

	return segmentLengthText

def UpdateOneScaleValue(view):
	scaleValue = view.LookupParameter("View Scale").AsInteger()

	for sizeIndex in range(0,len(imperial_sizes)):
		segmentLength = imperial_sizes[sizeIndex][0]
		parameterName = imperial_sizes[sizeIndex][1]

		segmentLengthText = GetSegmentLengthTextFromScaleValue(scaleValue, segmentLength)
			
		oScaleValueParam = view.LookupParameter(parameterName)
			
		oScaleValueParam.Set(segmentLengthText)

def UpdateAllScaleValues(app, doc):
	viewCollector = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Views).WhereElementIsNotElementType()

	hasSharedParameterOnFirstView = True
	parameter_names = get_parameter_names()
	for param in parameter_names:
		firstView = viewCollector.FirstElement()
		for param in parameter_names:
			sharedParameterOnFirstView = firstView.LookupParameter(param)
			if not sharedParameterOnFirstView:
				hasSharedParameterOnFirstView = False

	if not hasSharedParameterOnFirstView:
		add_shared_parameters(app, doc)

	t = DB.Transaction(doc, 'Update Graphic Scale Values')
 
	t.Start()

	for view in viewCollector:
		UpdateOneScaleValue(view)
	t.Commit()
	t.Dispose()

class GraphicScaleUpdater(DB.IUpdater):
	def __init__(self, applicationId):
		self.appId = applicationId
		self.updaterId = DB.UpdaterId(applicationId, Guid("9f80a6d6-2a6d-4414-9f31-3b1bf01d542c"))

	def Execute(self, data):
		doc = data.GetDocument()
		
		viewIds = data.GetModifiedElementIds()

		for viewId in viewIds:
			
			view = doc.GetElement(viewId)

			UpdateOneScaleValue(view)
			
			
	def GetAdditionalInformation(self):
		return "View Title Graphic Scale Updater: updates graphic scale values to match view scale"

	def GetChangePriority(self):
		return DB.ChangePriority.Views

	def GetUpdaterId(self):
		return self.updaterId

	def GetUpdaterName(self):
		return "View Title Graphic Scale Updater"

def RegisterViewUpdater(updater, thisFilter, parameterId):
	# Make sure we're not trying to reregister the same updater
	if DB.UpdaterRegistry.IsUpdaterRegistered(updater.GetUpdaterId()):
		DB.UpdaterRegistry.UnregisterUpdater(updater.GetUpdaterId())
	DB.UpdaterRegistry.RegisterUpdater(updater)
	DB.UpdaterRegistry.AddTrigger(updater.GetUpdaterId(), thisFilter, DB.Element.GetChangeTypeParameter(parameterId))

def docopen_eventhandler(sender, args):
	doc = args.Document
	UpdateAllScaleValues(HOST_APP.app, doc)
	# Add Parameter Change Updaters and Corresponding Triggers
	viewFilter = DB.ElementCategoryFilter(DB.BuiltInCategory.OST_Views)
	viewScaleUpdater = GraphicScaleUpdater(HOST_APP.app.ActiveAddInId)
	RegisterViewUpdater(viewScaleUpdater, viewFilter, DB.ElementId(DB.BuiltInParameter.VIEW_SCALE))

HOST_APP.app.DocumentOpened += \
    framework.EventHandler[DB.Events.DocumentOpenedEventArgs](
        docopen_eventhandler
	)

