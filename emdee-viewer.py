#!/usr/bin/env python3
"""EmDee Viewer — A lightweight markdown viewer."""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')

import json
import os
import re
import sys
from gi.repository import Gtk, WebKit2, Gio, GLib, Gdk
import markdown
from pygments.formatters import HtmlFormatter

RECENT_FILE = os.path.expanduser('~/.config/emdee-viewer/recent.json')
THEME_CSS_FILE = os.path.expanduser('~/.config/omarchy/current/theme/emdee-viewer.css')

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
pre code { background: none; padding: 0; font-size: 1rem; }
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

def _load_css():
    try:
        with open(THEME_CSS_FILE, 'r') as f:
            return f.read()
    except (FileNotFoundError, PermissionError, OSError):
        return DARK_CSS

class EmDeeViewer(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id='com.neil.emdee-viewer',
            flags=Gio.ApplicationFlags.HANDLES_OPEN
        )

    def do_startup(self):
        Gtk.Application.do_startup(self)
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property('gtk-application-prefer-dark-theme', True)

    def do_activate(self):
        win = self.get_active_window()
        if not win:
            win = EmDeeWindow(application=self)
        win.present()

    def do_open(self, files, n_files, hint):
        win = self.get_active_window()
        if not win:
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

        toc_btn = Gtk.ToggleButton(label='TOC')
        toc_btn.set_active(True)
        toc_btn.connect('toggled', self.on_toc_toggled)
        header.pack_end(toc_btn)

        zoom_out_btn = Gtk.Button(label='A−')
        zoom_out_btn.connect('clicked', self.on_zoom_out)
        header.pack_end(zoom_out_btn)

        zoom_in_btn = Gtk.Button(label='A+')
        zoom_in_btn.connect('clicked', self.on_zoom_in)
        header.pack_end(zoom_in_btn)

        self.font_size = 1.0
        self.header = header

        self.webview = WebKit2.WebView()
        self.css = _load_css()
        bg_hex = self._parse_bg_color(self.css)
        self.webview.set_background_color(bg_hex)
        self._apply_gtk_theme(self.css)
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
        self.toc_scroll = toc_scroll
        self.paned = paned

        paned.pack1(toc_scroll, resize=False, shrink=False)
        paned.pack2(self.webview, resize=True, shrink=False)
        paned.set_position(220)
        self.add(paned)

        welcome = f"""<!DOCTYPE html><html><head><style>
{self.css}
body {{ display: flex; align-items: center; justify-content: center; height: 90vh; }}
.msg {{ text-align: center; }}
h1 {{ font-size: 1.5rem; }}
p {{ font-size: 1rem; }}
</style></head><body><div class="msg">
<h1>EmDee Viewer</h1>
<p>Click <b>Open</b> to view a markdown file</p>
</div></body></html>"""
        self.webview.load_html(welcome, 'file:///')

        self.current_file = None
        self.file_monitor = None

        self.show_all()

    @staticmethod
    def _parse_bg_color(css):
        match = re.search(r'background:\s*(#[0-9a-fA-F]{6})', css)
        if match:
            h = match.group(1)
            r, g, b = int(h[1:3], 16) / 255, int(h[3:5], 16) / 255, int(h[5:7], 16) / 255
            return Gdk.RGBA(r, g, b, 1.0)
        return Gdk.RGBA(0.11, 0.11, 0.14, 1.0)

    def _apply_gtk_theme(self, css):
        bg = re.search(r'background:\s*(#[0-9a-fA-F]{6})', css)
        fg = re.search(r'color:\s*(#[0-9a-fA-F]{6})', css)
        accent = re.search(r'a \{ color:\s*(#[0-9a-fA-F]{6})', css)
        bg_color = bg.group(1) if bg else '#1c1c22'
        fg_color = fg.group(1) if fg else '#d4d4d8'
        accent_color = accent.group(1) if accent else '#60a5fa'
        gtk_css = f"""
            treeview {{
                background-color: {bg_color};
                color: {fg_color};
            }}
            treeview:selected {{
                background-color: {accent_color};
                color: {bg_color};
            }}
            scrolledwindow {{
                background-color: {bg_color};
            }}
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(gtk_css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_toc_toggled(self, button):
        if button.get_active():
            self.toc_scroll.show()
            self.paned.set_position(220)
        else:
            self.toc_scroll.hide()

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
        try:
            with open(filepath, 'r') as f:
                md_text = f.read()
        except (FileNotFoundError, PermissionError, OSError):
            return

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
<style>{self.css}\n{pygments_css}</style>
</head><body>{html_body}</body></html>"""

        base_uri = GLib.filename_to_uri(os.path.dirname(filepath), None) + '/'
        self.webview.load_html(html, base_uri)
        self.webview.connect('load-changed', self._on_load_finished)
        self.header.set_subtitle(GLib.path_get_basename(filepath))
        self.current_file = filepath

        self._save_recent(filepath)
        child = self.recent_popover.get_child()
        if child:
            self.recent_popover.remove(child)
        self._update_recent_menu()

        if self.file_monitor:
            self.file_monitor.cancel()
        gfile = Gio.File.new_for_path(filepath)
        self.file_monitor = gfile.monitor_file(Gio.FileMonitorFlags.NONE, None)
        self.file_monitor.connect('changed', self.on_file_changed)

    def _on_load_finished(self, webview, event):
        if event == WebKit2.LoadEvent.FINISHED:
            self._apply_font_size()
            webview.disconnect_by_func(self._on_load_finished)

    def _apply_font_size(self):
        js = f"document.body.style.fontSize='{self.font_size:.1f}rem';"
        self.webview.run_javascript(js, None, None, None)

    def on_zoom_in(self, button):
        self.font_size = min(self.font_size + 0.1, 3.0)
        self._apply_font_size()

    def on_zoom_out(self, button):
        self.font_size = max(self.font_size - 0.1, 0.5)
        self._apply_font_size()

    def on_file_changed(self, monitor, file, other_file, event):
        if event == Gio.FileMonitorEvent.CHANGES_DONE_HINT:
            if hasattr(self, '_reload_timeout') and self._reload_timeout:
                GLib.source_remove(self._reload_timeout)
            self._reload_timeout = GLib.timeout_add(300, self._do_reload)

    def _do_reload(self):
        self._reload_timeout = None
        self.load_file(self.current_file)
        return False

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
