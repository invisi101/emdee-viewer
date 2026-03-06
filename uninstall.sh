#!/bin/bash
set -e

echo "Uninstalling EmDee Viewer..."

sudo rm -f /usr/local/bin/emdee-viewer
sudo rm -f /usr/share/icons/hicolor/scalable/apps/emdee-viewer.svg
rm -f "$HOME/.local/share/applications/emdee-viewer.desktop"
rm -rf "$HOME/.config/emdee-viewer"

echo "Done!"
