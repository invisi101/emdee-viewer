#!/bin/bash
set -e

echo "Installing EmDee Viewer..."

# Detect distro and install dependencies
install_deps() {
    if command -v pacman &>/dev/null; then
        echo "Detected Arch Linux"
        sudo pacman -S --needed --noconfirm python gtk3 webkit2gtk-4.1 python-gobject python-markdown python-pygments
    elif command -v apt &>/dev/null; then
        echo "Detected Debian/Ubuntu"
        sudo apt install -y python3 gir1.2-gtk-3.0 gir1.2-webkit2-4.1 python3-gi python3-markdown python3-pygments
    elif command -v dnf &>/dev/null; then
        echo "Detected Fedora"
        sudo dnf install -y python3 gtk3 webkit2gtk4.1 python3-gobject python3-markdown python3-pygments
    else
        echo "Could not detect package manager. Please install these manually:"
        echo "  python3, gtk3, webkit2gtk-4.1, python-gobject, python-markdown, pygments"
        exit 1
    fi
}

install_deps

# Install the app
sudo install -Dm755 emdee-viewer.py /usr/local/bin/emdee-viewer
install -Dm644 emdee-viewer.desktop "$HOME/.local/share/applications/emdee-viewer.desktop"
sudo install -Dm644 emdee-viewer.svg /usr/share/icons/hicolor/scalable/apps/emdee-viewer.svg
gtk-update-icon-cache -f /usr/share/icons/hicolor/ 2>/dev/null || true

echo "Done! Launch 'EmDee Viewer' from your app launcher or run: emdee-viewer"
