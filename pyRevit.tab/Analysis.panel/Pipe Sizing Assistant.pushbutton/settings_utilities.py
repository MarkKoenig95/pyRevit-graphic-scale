from pyrevit import forms
from pyrevit.framework import wpf
import os.path as op
import os
from pipe_data_utilities import get_pipe_data
from pipe_sizing_utilities import register_pipe_graphics_updater, colorize_all_pipes, SizingWindow

dirname = op.dirname(__file__)

class DirectoryComboBoxValue:
    def __init__(self, name):
        self.name = name

def get_pipe_materials():
    material_directorys = os.listdir(op.join(dirname, "fixture_unit_values", "Wisconsin", "Domestic-Water"))
    materials = []

    for material_directory in material_directorys:
        material_name = " ".join(material_directory.split("_"))
        materials.append(DirectoryComboBoxValue(material_name))
    return materials

def get_codes():
    code_directories = os.listdir(op.join(dirname, "fixture_unit_values"))
    codes = []

    for code_directory in code_directories:
        code_name = " ".join(code_directory.split("_"))
        codes.append(DirectoryComboBoxValue(code_name))
    return codes

class SettingsWindow(forms.WPFWindow):
    def __init__(self, doc):
        wpf.LoadComponent(self, op.join(dirname,'settings_window.xaml'))
        self.doc = doc
        self.material_cmb.DisplayMemberPath = "name"
        self.material_cmb.SelectedValuePath = "name"
        self.material_cmb.ItemsSource = get_pipe_materials()
        self.material_cmb.Text = "Copper Type-L"

        self.code_cmb.DisplayMemberPath = "name"
        self.code_cmb.SelectedValuePath = "name"
        self.code_cmb.ItemsSource = get_codes()
        self.code_cmb.Text = "Wisconsin"

    def start_sizing(self, sender, args):
        pressure_loss = 0.5
        try:
            pressure_loss = int(self.pressure_loss_input.Text)
        except:
            forms.alert("Please Enter a Valid Pressure Loss Value")
            return

        is_flush_tank = self.flush_tank_rb.IsChecked

        if not is_flush_tank and not self.flush_valve_rb.IsChecked:
            forms.alert("Something went wrong with the flush valve settings")

        material = self.material_cmb.SelectedValue

        if material is None:
            forms.alert("Please choose a material from the list")
            return
        
        code = self.code_cmb.SelectedValue

        if code is None:
            forms.alert("Please choose a code from the list")
            return

        material_directory = "_".join(material.split(" "))
        code_directory = "_".join(code.split(" "))

        pipe_data = get_pipe_data(pressure_loss, is_flush_tank, material_directory, code_directory)
        register_pipe_graphics_updater(pipe_data)
        colorize_all_pipes(self.doc, pipe_data)
        sizing_window = SizingWindow(pipe_data)
        sizing_window.show(modal=False)
        self.Close()

