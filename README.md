<p align="center">
  <img src="emdee-viewer.svg" width="128" height="128" alt="EmDee Viewer">
</p>

<h1 align="center">EmDee Viewer</h1>

<p align="center">A lightweight GTK markdown viewer with a dark theme.</p>

## Features

- Dark themed rendered markdown with syntax-highlighted code blocks
- Table of contents sidebar with clickable heading navigation
- Recent files menu (remembers last 10 files)
- Auto-reloads when the file changes on disk
- Opens `.md` files from app launcher or command line

## Install

```bash
git clone https://github.com/invisi101/emdee-viewer.git
cd emdee-viewer
chmod +x install.sh
./install.sh
```

This installs dependencies, copies the viewer to `/usr/local/bin/emdee-viewer`, and adds a `.desktop` file so it appears in your app launcher.

Supports Arch Linux, Debian/Ubuntu, and Fedora.

## Uninstall

```bash
./uninstall.sh
```

## Usage

Launch from your app launcher, or from the terminal:

```bash
emdee-viewer              # Opens with welcome screen
emdee-viewer file.md      # Opens a file directly
```

## Dependencies

- Python 3
- GTK 3
- WebKit2GTK 4.1
- python-gobject
- python-markdown
- pygments

## License

MIT
