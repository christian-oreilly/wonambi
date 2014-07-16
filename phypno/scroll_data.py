#!/usr/bin/env python3
VERSION = 9.1

""" ------ START APPLICATION ------ """
from PyQt4.QtGui import QApplication

if __name__ == '__main__':
    try:
        app = QApplication([])
        standalone = True
    except RuntimeError:
        standalone = False

""" ------ KEEP LOG ------ """
from logging import getLogger, DEBUG, StreamHandler, Formatter

lg = getLogger('phypno')  # when called by itself, __name__ is __main__
FORMAT = '%(asctime)s %(filename)s/%(funcName)s (%(levelname)s): %(message)s'
DATE_FORMAT = '%H:%M:%S'

formatter = Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
handler = StreamHandler()
handler.setFormatter(formatter)

lg.handlers = []
lg.addHandler(handler)

lg.setLevel(DEBUG)

""" ------ IMPORT ------ """
from os.path import splitext
from types import MethodType

from numpy import arange
from PyQt4.QtCore import QSettings
from PyQt4.QtGui import (QFileDialog,
                         QInputDialog,
                         QMainWindow,
                         )

from phypno.widgets.creation import (create_menubar, create_toolbar,
                                     create_actions, create_widgets)
from phypno.widgets.settings import DEFAULTS
from phypno.widgets.utils import keep_recent_datasets

settings = QSettings("phypno", "scroll_data")


class MainWindow(QMainWindow):
    """Create an instance of the main window.

    Attributes
    ----------

    notes : instance of phypno.widgets.Notes

    channels : instance of phypno.widgets.Channels

    detect : instance of phypno.widgets.Detect

    info : instance of phypno.widgets.Info

    overview : instance of phypno.widgets.Overview

    spectrum : instance of phypno.widgets.Spectrum

    traces : instance of phypno.widgets.Traces

    video : instance of phypno.widgets.Video

    action : dict
        names of all the actions to perform

    menu_window : instance of menuBar.menu
        menu about the windows (to know which ones are shown or hidden)

    """
    def __init__(self):
        super().__init__()

        self.info = None
        self.channels = None
        self.spectrum = None
        self.overview = None
        self.notes = None
        self.detect = None
        self.video = None
        self.traces = None
        self.settings = None

        self.action = {}  # actions was already taken
        self.menu_window = None

        # I prefer to have these functions in a separate module, for clarify
        self.create_widgets = MethodType(create_widgets, self)
        self.create_actions = MethodType(create_actions, self)
        self.create_menubar = MethodType(create_menubar, self)
        self.create_toolbar = MethodType(create_toolbar, self)

        self.create_widgets()
        self.create_actions()
        self.create_menubar()
        self.create_toolbar()

        self.statusBar()

        self.setWindowTitle('PHYPNO v' + str(VERSION))
        self.set_geometry()
        window_state = settings.value('window/state')
        if window_state is not None:
            self.restoreState(window_state, VERSION)
        self.show()

    def update_mainwindow(self):
        """Functions to re-run once settings have been changed."""
        lg.debug('Updating main window')
        self.set_geometry()
        create_menubar(self)

    def set_geometry(self):
        """Simply set the geometry of the main window."""
        self.setGeometry(self.value('window_x'),
                         self.value('window_y'),
                         self.value('window_width'),
                         self.value('window_height'))

    def value(self, parameter, new_value=None):
        for widget_name, values in DEFAULTS.items():
            if parameter in values.keys():
                widget = getattr(self, widget_name)
                if new_value is None:
                    return widget.config.value[parameter]
                else:
                    widget.config.value[parameter] = new_value

    def reset_dataset(self):
        """Remove all the information from previous dataset before loading a
        new one.

        """
        # store current dataset
        max_dataset_history = self.value('max_dataset_history')
        keep_recent_datasets(max_dataset_history, self.info.filename)

        # main
        if self.traces.scene is not None:
            self.traces.scene.clear()
            self.traces.scene = None

        # overview
        if self.overview.scene is not None:
            self.overview.scene.clear()
            self.overview.scene = None

        self.info.reset()
        self.notes.reset()
        self.channels.reset()

        # spectrum
        self.spectrum.idx_chan.clear()
        if self.spectrum.scene is not None:
            self.spectrum.scene.clear()

    def action_download(self, length=None):
        """Start the download of the dataset."""
        dataset = self.info.dataset
        if length is None or length > self.overview.maximum:
            length = self.overview.maximum

        steps = arange(self.overview.config.value['window_start'],
                       self.overview.config.value['window_start'] + length,
                       self.value('read_intervals'))
        one_chan = dataset.header['chan_name'][0]
        for begtime, endtime in zip(steps[:-1], steps[1:]):
            dataset.read_data(chan=[one_chan],
                              begtime=begtime,
                              endtime=endtime)
            self.overview.mark_downloaded(begtime, endtime)

    def action_show_settings(self):
        """Open the Setting windows, after updating the values in GUI.
        """
        self.config.set_values()
        self.overview.config.set_values()
        self.traces.config.set_values()
        self.spectrum.config.set_values()
        self.notes.config.set_values()
        self.detect.config.set_values()
        self.video.config.set_values()
        self.settings.show()

    def action_step_prev(self):
        """Go to the previous step."""
        window_start = (self.overview.config.value['window_start'] -
                        self.overview.config.value['window_length'] /
                        self.overview.config.value['window_step'])
        self.overview.update_position(window_start)

    def action_step_next(self):
        """Go to the next step."""
        window_start = (self.overview.config.value['window_start'] +
                        self.overview.config.value['window_length'] /
                        self.overview.config.value['window_step'])
        self.overview.update_position(window_start)

    def action_page_prev(self):
        """Go to the previous page."""
        window_start = (self.overview.config.value['window_start'] -
                        self.overview.config.value['window_length'])
        self.overview.update_position(window_start)

    def action_page_next(self):
        """Go to the next page."""
        window_start = (self.overview.config.value['window_start'] +
                        self.overview.config.value['window_length'])
        self.overview.update_position(window_start)

    def action_add_time(self, extra_time):
        """Go to the predefined time forward."""
        window_start = self.overview.config.value['window_start'] + extra_time
        self.overview.update_position(window_start)

    def action_X_more(self):
        """Zoom in on the x-axis."""
        self.overview.config.value['window_length'] *= 2
        self.overview.update_position()

    def action_X_less(self):
        """Zoom out on the x-axis."""
        self.overview.config.value['window_length'] /= 2
        self.overview.update_position()

    def action_X_length(self, new_window_length):
        """Use presets for length of the window."""
        self.overview.config.value['window_length'] = new_window_length
        self.overview.update_position()

    def action_Y_more(self):
        """Increase the amplitude."""
        self.traces.config.value['y_scale'] *= 2
        self.traces.display_traces()

    def action_Y_less(self):
        """Decrease the amplitude."""
        self.traces.config.value['y_scale'] /= 2
        self.traces.display_traces()

    def action_Y_ampl(self, new_y_scale):
        """Make amplitude on Y axis using predefined values"""
        self.traces.config.value['y_scale'] = new_y_scale
        self.traces.display_traces()

    def action_Y_wider(self):
        """Increase the distance of the lines."""
        self.traces.config.value['y_distance'] *= 1.4
        self.traces.display_traces()

    def action_Y_tighter(self):
        """Decrease the distance of the lines."""
        self.traces.config.value['y_distance'] /= 1.4
        self.traces.display_traces()

    def action_Y_dist(self, new_y_distance):
        """Use preset values for the distance between lines."""
        self.traces.config.value['y_distance'] = new_y_distance
        self.traces.display_traces()

    def action_new_annot(self):
        """Action: create a new file for annotations.

        It should be gray-ed out when no dataset
        """
        if self.info.filename is None:
            self.statusBar().showMessage('No dataset loaded')
            return

        filename = splitext(self.info.filename)[0] + '_scores.xml'
        filename = QFileDialog.getSaveFileName(self, 'Create annotation file',
                                               filename,
                                               'Annotation File (*.xml)')
        if filename == '':
            return

        self.notes.update_notes(filename, True)

    def action_load_annot(self):
        """Action: load a file for annotations."""
        if self.info.filename is not None:
            filename = splitext(self.info.filename)[0] + '_scores.xml'
        else:
            filename = None

        filename = QFileDialog.getOpenFileName(self, 'Load annotation file',
                                               filename,
                                               'Annotation File (*.xml)')

        if filename == '':
            return

        self.notes.update_notes(filename, False)

    def action_select_rater(self, rater=False):
        """
        First argument, if not specified, is a bool/False:
        http://pyqt.sourceforge.net/Docs/PyQt4/qaction.html#triggered

        """
        if rater:
            self.notes.annot.get_rater(rater)

        else:
            answer = QInputDialog.getText(self, 'New Rater',
                                          'Enter rater\'s name')
            if answer[1]:
                self.notes.annot.add_rater(answer[0])
                self.create_menubar()  # refresh list ot raters

        self.notes.display_notes()

    def action_delete_rater(self):
        """
        First argument, if not specified, is a bool/False:
        http://pyqt.sourceforge.net/Docs/PyQt4/qaction.html#triggered

        """
        answer = QInputDialog.getText(self, 'Delete Rater',
                                      'Enter rater\'s name')
        if answer[1]:
            self.notes.annot.remove_rater(answer[0])

        self.notes.display_notes()
        self.create_menubar()  # refresh list ot raters

    def action_new_event_type(self):
        answer = QInputDialog.getText(self, 'New Event Type',
                                      'Enter new event\'s name')
        if answer[1]:
            self.notes.annot.remove_rater(answer[0])

    def moveEvent(self, event):
        """Main window is already resized."""
        self.value('window_x', self.geometry().x())
        self.value('window_y', self.geometry().y())
        self.value('window_width', self.geometry().width())
        self.value('window_height', self.geometry().height())
        self.settings.config.set_values()  # save the values in GUI

    def resizeEvent(self, event):
        """Main window is already resized."""
        self.value('window_x', self.geometry().x())
        self.value('window_y', self.geometry().y())
        self.value('window_width', self.geometry().width())
        self.value('window_height', self.geometry().height())
        self.settings.config.set_values()  # save the values in GUI

    def closeEvent(self, event):
        """save the name of the last open dataset."""
        self.settings.config.get_values()  # get geometry and store it in preferences

        max_dataset_history = self.value('max_dataset_history')
        keep_recent_datasets(max_dataset_history, self.info.filename)

        settings.setValue('window/state', self.saveState(VERSION))

        event.accept()


if __name__ == '__main__':

    q = MainWindow()
    q.show()

    if standalone:
        app.exec_()
        app.deleteLater()  # so that it kills the figure in the right order
