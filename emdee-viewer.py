#!/usr/bin/env python3
"""EmDee Viewer — A lightweight markdown viewer."""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')

import sys
from gi.repository import Gtk, Gio

class EmDeeViewer(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id='com.neil.emdee-viewer',
            flags=Gio.ApplicationFlags.HANDLES_OPEN
        )

    def do_activate(self):
        win = EmDeeWindow(application=self)
        win.present()

    def do_open(self, files, n_files, hint):
        win = EmDeeWindow(application=self)
        win.load_file(files[0].get_path())
        win.present()

class EmDeeWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(title='EmDee Viewer', default_width=900, default_height=700, **kwargs)

app = EmDeeViewer()
app.run(sys.argv)
