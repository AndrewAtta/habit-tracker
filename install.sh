#!/usr/bin/env bash
set -e

echo "Habit Tracker — dependency installer"
echo "======================================"

# Absolute path to this repo (works wherever the script is run from)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── 1. Install PyQt5 ──────────────────────────────────────────────────────────
if command -v apt-get &>/dev/null; then
    echo "Detected: Debian/Ubuntu (apt)"
    sudo apt-get update -qq
    sudo apt-get install -y python3-pyqt5

elif command -v dnf &>/dev/null; then
    echo "Detected: Fedora/RHEL (dnf)"
    sudo dnf install -y python3-qt5

elif command -v pacman &>/dev/null; then
    echo "Detected: Arch Linux (pacman)"
    sudo pacman -Sy --noconfirm python-pyqt5

elif command -v zypper &>/dev/null; then
    echo "Detected: openSUSE (zypper)"
    sudo zypper install -y python3-qt5

else
    echo "ERROR: Could not detect a supported package manager."
    echo "Please install PyQt5 for Python 3 manually, then re-run."
    exit 1
fi

# Verify PyQt5 import works
if ! python3 -c "from PyQt5.QtWidgets import QApplication" 2>/dev/null; then
    echo "ERROR: PyQt5 still not importable after install. Check the output above."
    exit 1
fi
echo "PyQt5 OK"

# ── 2. Install desktop launcher ───────────────────────────────────────────────
echo ""
echo "Installing desktop launcher..."

APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
mkdir -p "$APPS_DIR" "$ICONS_DIR"

# Copy icon (SVGs belong in scalable/apps)
cp "$SCRIPT_DIR/icon.svg" "$ICONS_DIR/habit-tracker.svg"

# Write .desktop file with the real path baked in
cat > "$APPS_DIR/habit-tracker.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Habit Tracker
Comment=Track your daily habits
Exec=python3 $SCRIPT_DIR/habit_tracker.py
Icon=habit-tracker
Terminal=false
Categories=Utility;
StartupNotify=true
StartupWMClass=habit-tracker
EOF

chmod +x "$APPS_DIR/habit-tracker.desktop"

# Refresh the desktop database so the launcher appears immediately
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo ""
echo "Done! Habit Tracker is now in your application menu."
echo ""
echo "To pin to your taskbar:"
echo "  GNOME  — open Activities, search 'Habit Tracker', right-click → Add to Favorites"
echo "  KDE    — find it in the app launcher, right-click → Pin to Taskbar"
echo "  XFCE   — right-click the desktop → create launcher, or drag from the menu"
echo ""
echo "To run directly:  python3 $SCRIPT_DIR/habit_tracker.py"
