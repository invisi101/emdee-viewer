#!/usr/bin/env python3
"""EmDee Viewer — A lightweight markdown viewer."""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')

import json
import os
import sys
from gi.repository import Gtk, WebKit2, Gio, GLib, Gdk
import markdown
from pygments.formatters import HtmlFormatter

RECENT_FILE = os.path.expanduser('~/.config/emdee-viewer/recent.json')

DARK_CSS = """
body {
    background: #1c1c22;
    color: #d4d4d8;
    font-family: system-ui, -apple-system, sans-serif;
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    line-height: 1.7;
}
h1, h2, h3, h4, h5, h6 { color: #e4e4e7; margin-top: 1.5em; }
h1 { border-bottom: 1px solid #3f3f46; padding-bottom: 0.3em; }
a { color: #60a5fa; }
code {
    background: #27272a;
    padding: 0.2em 0.4em;
    border-radius: 4px;
    font-size: 0.9em;
}
pre {
    background: #18181b;
    padding: 1rem;
    border-radius: 8px;
    overflow-x: auto;
    border: 1px solid #3f3f46;
}
pre code { background: none; padding: 0; }
blockquote {
    border-left: 3px solid #60a5fa;
    margin-left: 0;
    padding-left: 1rem;
    color: #a1a1aa;
}
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #3f3f46; padding: 0.5rem; }
th { background: #27272a; }
hr { border: none; border-top: 1px solid #3f3f46; }
img { max-width: 100%; }
"""

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

        recent_btn = Gtk.MenuButton(label='Recent')
        self.recent_popover = Gtk.Popover()
        recent_btn.set_popover(self.recent_popover)
        header.pack_start(recent_btn)
        self.recent_btn = recent_btn

        self._update_recent_menu()

        self.header = header

        self.webview = WebKit2.WebView()
        self.webview.set_background_color(Gdk.RGBA(0.11, 0.11, 0.14, 1.0))
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)

        # TOC sidebar
        self.toc_store = Gtk.TreeStore(str, str)  # display text, anchor id
        self.toc_view = Gtk.TreeView(model=self.toc_store)
        self.toc_view.set_headers_visible(False)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('', renderer, text=0)
        self.toc_view.append_column(column)
        self.toc_view.connect('row-activated', self.on_toc_clicked)

        toc_scroll = Gtk.ScrolledWindow()
        toc_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        toc_scroll.set_size_request(200, -1)
        toc_scroll.add(self.toc_view)

        paned.pack1(toc_scroll, resize=False, shrink=False)
        paned.pack2(self.webview, resize=True, shrink=False)
        paned.set_position(220)
        self.add(paned)

        self.current_file = None

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

    def load_file(self, filepath):
        with open(filepath, 'r') as f:
            md_text = f.read()

        pygments_css = HtmlFormatter(style='monokai').get_style_defs('.codehilite')

        md = markdown.Markdown(extensions=[
            'fenced_code', 'codehilite', 'tables', 'toc',
        ], extension_configs={
            'codehilite': {'css_class': 'codehilite', 'guess_lang': True},
            'toc': {'permalink': False},
        })
        html_body = md.convert(md_text)

        self.toc_store.clear()
        self._populate_toc(md.toc_tokens, None)
        self.toc_view.expand_all()

        html = f"""<!DOCTYPE html>
<html><head>
<style>{DARK_CSS}\n{pygments_css}</style>
</head><body>{html_body}</body></html>"""

        self.webview.load_html(html, f'file://{filepath}')
        self.header.set_subtitle(GLib.path_get_basename(filepath))
        self.current_file = filepath

        self._save_recent(filepath)
        child = self.recent_popover.get_child()
        if child:
            self.recent_popover.remove(child)
        self._update_recent_menu()

    def _populate_toc(self, tokens, parent):
        for token in tokens:
            row = self.toc_store.append(parent, [token['name'], token['id']])
            if token.get('children'):
                self._populate_toc(token['children'], row)

    def on_toc_clicked(self, treeview, path, column):
        model = treeview.get_model()
        iter_ = model.get_iter(path)
        anchor = model.get_value(iter_, 1)
        js = f"document.getElementById('{anchor}').scrollIntoView({{behavior:'smooth'}});"
        self.webview.run_javascript(js, None, None, None)

    def _load_recent(self):
        try:
            with open(RECENT_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_recent(self, filepath):
        os.makedirs(os.path.dirname(RECENT_FILE), exist_ok=True)
        recent = self._load_recent()
        if filepath in recent:
            recent.remove(filepath)
        recent.insert(0, filepath)
        recent = recent[:10]  # keep last 10
        with open(RECENT_FILE, 'w') as f:
            json.dump(recent, f)

    def _update_recent_menu(self):
        recent = self._load_recent()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(8)
        box.set_margin_end(8)

        if not recent:
            label = Gtk.Label(label='No recent files')
            box.pack_start(label, False, False, 0)
        else:
            for filepath in recent:
                btn = Gtk.ModelButton(label=GLib.path_get_basename(filepath))
                btn.connect('clicked', lambda b, p=filepath: self._open_recent(p))
                box.pack_start(btn, False, False, 0)

        box.show_all()
        self.recent_popover.add(box)

    def _open_recent(self, filepath):
        self.recent_popover.popdown()
        if os.path.exists(filepath):
            self.load_file(filepath)

app = EmDeeViewer()
app.run(sys.argv)
