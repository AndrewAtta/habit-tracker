#!/usr/bin/env bash
set -e

echo "Habit Tracker — dependency installer"
echo "======================================"

# Detect package manager and install python3-tk
if command -v apt-get &>/dev/null; then
    echo "Detected: Debian/Ubuntu (apt)"
    sudo apt-get update -qq
    sudo apt-get install -y python3-tk

elif command -v dnf &>/dev/null; then
    echo "Detected: Fedora/RHEL (dnf)"
    sudo dnf install -y python3-tkinter

elif command -v pacman &>/dev/null; then
    echo "Detected: Arch Linux (pacman)"
    sudo pacman -Sy --noconfirm tk

elif command -v zypper &>/dev/null; then
    echo "Detected: openSUSE (zypper)"
    sudo zypper install -y python3-tk

else
    echo "ERROR: Could not detect a supported package manager."
    echo "Please install the tkinter package for Python 3 manually, then re-run."
    exit 1
fi

# Verify import works
if python3 -c "import tkinter" 2>/dev/null; then
    echo ""
    echo "All dependencies installed. Run the app with:"
    echo "  python3 habit_tracker.py"
else
    echo ""
    echo "ERROR: tkinter still not importable after install. Check the output above."
    exit 1
fi
