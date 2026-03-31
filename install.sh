#!/usr/bin/env bash
set -e

echo "Habit Tracker — dependency installer"
echo "======================================"

# Detect package manager and install PyQt5
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

# Verify import works
if python3 -c "from PyQt5.QtWidgets import QApplication" 2>/dev/null; then
    echo ""
    echo "All dependencies installed. Run the app with:"
    echo "  python3 habit_tracker.py"
else
    echo ""
    echo "ERROR: PyQt5 still not importable after install. Check the output above."
    exit 1
fi
