from pyrevit import forms
from pyrevit.framework import wpf
import os.path as op
from pipe_data_utilities import get_pipe_data
from pipe_sizing_utilities import register_pipe_graphics_updater, colorize_all_pipes, SizingWindow

class SettingsWindow(forms.WPFWindow):
    def __init__(self, doc):
        wpf.LoadComponent(self, op.join(op.dirname(__file__),'settings_window.xaml'))
        self.pressure_loss = 0.5
        self.doc = doc

    def start_sizing(self, sender, args):
        try:
            self.pressure_loss = int(self.pressure_loss_input.Text)
        except:
            forms.alert("Please Enter a Valid Pressure Loss Value")

        is_flush_tank = self.flush_tank_rb.IsChecked

        if not is_flush_tank and not self.flush_valve_rb.IsChecked:
            forms.alert("Something went wrong with the flush valve settings")

        pipe_data = get_pipe_data(self.pressure_loss)
        register_pipe_graphics_updater(pipe_data)
        colorize_all_pipes(self.doc, pipe_data)
        sizing_window = SizingWindow(pipe_data)
        sizing_window.show(modal=False)
        self.Close()

