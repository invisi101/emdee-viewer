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

        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.set_title('EmDee Viewer')
        self.set_titlebar(header)

        open_btn = Gtk.Button(label='Open')
        open_btn.connect('clicked', self.on_open_clicked)
        header.pack_start(open_btn)

        self.header = header

    def on_open_clicked(self, button):
        dialog = Gtk.FileChooserDialog(
            title='Open Markdown File',
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
        )
        md_filter = Gtk.FileFilter()
        md_filter.set_name('Markdown files')
        md_filter.add_pattern('*.md')
        dialog.add_filter(md_filter)
        all_filter = Gtk.FileFilter()
        all_filter.set_name('All files')
        all_filter.add_pattern('*')
        dialog.add_filter(all_filter)

        if dialog.run() == Gtk.ResponseType.OK:
            self.load_file(dialog.get_filename())
        dialog.destroy()

app = EmDeeViewer()
app.run(sys.argv)
