# EmDee Viewer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a standalone GTK markdown viewer app with dark theme, TOC sidebar, and recent files.

**Architecture:** Single Python script using GTK3 + WebKit2 (4.1) + python-markdown with pygments for syntax highlighting. Markdown is converted to styled HTML and rendered in a WebKit web view. TOC is auto-generated from headings and displayed in a sidebar TreeView.

**Tech Stack:** Python 3.14, GTK3 (gi), WebKit2 4.1, python-markdown (with toc + codehilite + tables + fenced_code extensions), pygments

---

### Task 1: Project scaffold and basic window

**Files:**
- Create: `~/dev/emdee-viewer/emdee-viewer.py`

**Step 1: Create the basic GTK3 app skeleton**

```python
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
```

**Step 2: Make it executable and run**

```bash
chmod +x ~/dev/emdee-viewer/emdee-viewer.py
python3 ~/dev/emdee-viewer/emdee-viewer.py
```

Expected: Empty GTK window titled "EmDee Viewer" appears.

**Step 3: Commit**

```bash
cd ~/dev/emdee-viewer && git init && git add emdee-viewer.py
git commit -m "feat: basic GTK3 app scaffold"
```

---

### Task 2: Header bar with Open button

**Files:**
- Modify: `~/dev/emdee-viewer/emdee-viewer.py`

**Step 1: Add header bar to EmDeeWindow.__init__**

Add a `Gtk.HeaderBar` with an "Open" button that triggers a file chooser dialog filtered to `*.md` files. Set the header bar title to "EmDee Viewer" and update subtitle to the filename when a file is opened.

```python
# In EmDeeWindow.__init__:
header = Gtk.HeaderBar()
header.set_show_close_button(True)
header.set_title('EmDee Viewer')
self.set_titlebar(header)

open_btn = Gtk.Button(label='Open')
open_btn.connect('clicked', self.on_open_clicked)
header.pack_start(open_btn)

self.header = header
```

```python
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
```

**Step 2: Run and verify Open dialog works**

```bash
python3 ~/dev/emdee-viewer/emdee-viewer.py
```

Expected: Window with header bar and Open button. Clicking Open shows a file chooser.

**Step 3: Commit**

```bash
cd ~/dev/emdee-viewer && git add -A && git commit -m "feat: add header bar with Open file dialog"
```

---

### Task 3: WebKit markdown rendering with dark theme

**Files:**
- Modify: `~/dev/emdee-viewer/emdee-viewer.py`

**Step 1: Add WebKit web view and markdown rendering**

Add imports at top:
```python
from gi.repository import Gtk, WebKit2, Gio, GLib
import markdown
from pygments.formatters import HtmlFormatter
```

Add the web view to the window layout and implement `load_file`:

```python
# In EmDeeWindow.__init__:
self.webview = WebKit2.WebView()
self.webview.set_background_color(Gdk.RGBA(0.11, 0.11, 0.14, 1.0))
self.add(self.webview)  # temporary, will be replaced by paned layout in Task 4

self.current_file = None
```

```python
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
    toc_html = md.toc

    html = f"""<!DOCTYPE html>
<html><head>
<style>{DARK_CSS}\n{pygments_css}</style>
</head><body>{html_body}</body></html>"""

    self.webview.load_html(html, f'file://{filepath}')
    self.header.set_subtitle(GLib.path_get_basename(filepath))
    self.current_file = filepath
```

**Step 2: Run and test with a real markdown file**

```bash
python3 ~/dev/emdee-viewer/emdee-viewer.py
```

Open `~/dev/How to/trufflehog-cheatsheet.md` — should see dark-themed rendered markdown with syntax-highlighted code blocks.

**Step 3: Commit**

```bash
cd ~/dev/emdee-viewer && git add -A && git commit -m "feat: WebKit markdown rendering with dark theme and syntax highlighting"
```

---

### Task 4: TOC sidebar

**Files:**
- Modify: `~/dev/emdee-viewer/emdee-viewer.py`

**Step 1: Replace simple layout with paned view + TOC sidebar**

Replace `self.add(self.webview)` with a horizontal paned layout:

```python
# In EmDeeWindow.__init__:
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

# Web view
self.webview = WebKit2.WebView()

paned.pack1(toc_scroll, resize=False, shrink=False)
paned.pack2(self.webview, resize=True, shrink=False)
paned.set_position(220)
self.add(paned)
```

**Step 2: Parse TOC from markdown and populate tree**

In `load_file`, after `md.convert()`, parse `md.toc_tokens` to populate the tree store:

```python
# In load_file, after md.convert():
self.toc_store.clear()
self._populate_toc(md.toc_tokens, None)
self.toc_view.expand_all()
```

```python
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
```

**Step 3: Run and verify TOC appears and clicking scrolls**

```bash
python3 ~/dev/emdee-viewer/emdee-viewer.py
```

Open a markdown file with multiple headings. TOC should appear in sidebar. Clicking an entry scrolls the web view.

**Step 4: Commit**

```bash
cd ~/dev/emdee-viewer && git add -A && git commit -m "feat: add TOC sidebar with clickable heading navigation"
```

---

### Task 5: Recent files

**Files:**
- Modify: `~/dev/emdee-viewer/emdee-viewer.py`

**Step 1: Add recent files management**

Add imports:
```python
import json
import os
```

```python
RECENT_FILE = os.path.expanduser('~/.config/emdee-viewer/recent.json')

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
```

Call `self._save_recent(filepath)` at end of `load_file`.

**Step 2: Add Recent Files menu button to header bar**

```python
# In EmDeeWindow.__init__, after open_btn:
recent_btn = Gtk.MenuButton(label='Recent')
self.recent_popover = Gtk.Popover()
recent_btn.set_popover(self.recent_popover)
header.pack_start(recent_btn)
self.recent_btn = recent_btn

self._update_recent_menu()
```

```python
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
```

Also call `self._update_recent_menu()` at end of `load_file` (rebuild popover after each open — clear old child first):

```python
# At end of load_file:
child = self.recent_popover.get_child()
if child:
    self.recent_popover.remove(child)
self._update_recent_menu()
```

**Step 3: Run and verify recent files**

```bash
python3 ~/dev/emdee-viewer/emdee-viewer.py
```

Open a file, close app, reopen — Recent button should show the file.

**Step 4: Commit**

```bash
cd ~/dev/emdee-viewer && git add -A && git commit -m "feat: add recent files menu"
```

---

### Task 6: File watching (auto-reload)

**Files:**
- Modify: `~/dev/emdee-viewer/emdee-viewer.py`

**Step 1: Add GIO file monitor**

```python
# In EmDeeWindow.__init__:
self.file_monitor = None
```

```python
# At end of load_file:
if self.file_monitor:
    self.file_monitor.cancel()
gfile = Gio.File.new_for_path(filepath)
self.file_monitor = gfile.monitor_file(Gio.FileMonitorFlags.NONE, None)
self.file_monitor.connect('changed', self.on_file_changed)
```

```python
def on_file_changed(self, monitor, file, other_file, event):
    if event == Gio.FileMonitorEvent.CHANGES_DONE_HINT:
        self.load_file(self.current_file)
```

**Step 2: Test by editing a file while viewer is open**

```bash
python3 ~/dev/emdee-viewer/emdee-viewer.py &
# Open a file, then edit it in another editor — viewer should auto-update
```

**Step 3: Commit**

```bash
cd ~/dev/emdee-viewer && git add -A && git commit -m "feat: auto-reload on file changes"
```

---

### Task 7: Polish and CLI arg support

**Files:**
- Modify: `~/dev/emdee-viewer/emdee-viewer.py`

**Step 1: Add dark GTK theme preference**

```python
# Before app.run():
settings = Gtk.Settings.get_default()
settings.set_property('gtk-application-prefer-dark-theme', True)
```

**Step 2: Add welcome screen when no file is open**

In `EmDeeWindow.__init__`, load a welcome HTML into the webview:

```python
welcome = """<!DOCTYPE html><html><head><style>
body { background: #1c1c22; color: #71717a; display: flex;
       align-items: center; justify-content: center; height: 90vh;
       font-family: system-ui; }
.msg { text-align: center; }
h1 { color: #d4d4d8; font-size: 1.5rem; }
p { font-size: 1rem; }
</style></head><body><div class="msg">
<h1>EmDee Viewer</h1>
<p>Click <b>Open</b> to view a markdown file</p>
</div></body></html>"""
self.webview.load_html(welcome, 'file:///')
```

**Step 3: Create symlink for easy CLI access**

```bash
mkdir -p ~/bin
ln -sf ~/dev/emdee-viewer/emdee-viewer.py ~/bin/emdee
```

Ensure `~/bin` is in PATH (should be for most setups).

**Step 4: Run final test**

```bash
emdee  # Should show welcome screen
emdee ~/dev/How\ to/trufflehog-cheatsheet.md  # Should open file directly
```

**Step 5: Commit**

```bash
cd ~/dev/emdee-viewer && git add -A && git commit -m "feat: dark theme, welcome screen, CLI symlink"
```
