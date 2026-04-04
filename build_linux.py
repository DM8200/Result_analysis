"""
build_linux.py - Final stable version
- Uses Python 3.11 (fixes customtkinter segfault on Ubuntu 22.04)
- Ships .py files directly (no .pyc magic number issues)
- Auto installs Python 3.11 on customer PC
"""

import os, sys, shutil, subprocess

APP_NAME  = "ResultAnalyzer"
DEB_NAME  = "result-analyzer"
VERSION   = "1.0.0"
PY_FILES  = ["app.py", "pdf_parser.py", "license_client.py"]

print("\n[1/3] Checking files...")
for f in PY_FILES:
    if not os.path.exists(f):
        print(f"  ERROR: {f} not found!"); sys.exit(1)
    print(f"  Found: {f}")

print("\n[2/3] Creating icons...")
try:
    from PIL import Image
    if os.path.exists("logo.png"):
        img = Image.open("logo.png")
        for size in [256, 128, 64, 48, 32]:
            folder = f"icons/{size}x{size}"
            os.makedirs(folder, exist_ok=True)
            img.resize((size, size), Image.LANCZOS).save(f"{folder}/result-analyzer.png")
        print("  Icons created!")
except Exception as e:
    print(f"  Icon error: {e}")

print("\n[3/3] Creating .deb...")

for d in ["pkg/DEBIAN","pkg/usr/local/bin","pkg/opt/result-analyzer",
          "pkg/usr/share/applications","pkg/usr/share/pixmaps",
          "pkg/usr/share/icons/hicolor/256x256/apps",
          "pkg/usr/share/icons/hicolor/128x128/apps",
          "pkg/usr/share/icons/hicolor/64x64/apps",
          "pkg/usr/share/icons/hicolor/48x48/apps"]:
    os.makedirs(d, exist_ok=True)

# Copy .py files
for f in PY_FILES:
    shutil.copy(f, f"pkg/opt/result-analyzer/{f}")
    print(f"  Copied: {f}")

if os.path.exists("logo.png"):
    shutil.copy("logo.png", "pkg/opt/result-analyzer/logo.png")

# ── Launcher — always uses python3.11 ──
launcher = r"""#!/bin/bash
APP_DIR="/opt/result-analyzer"
LIBS="customtkinter pdfplumber pandas matplotlib requests openpyxl pillow"

# Fix display authorization
xhost +local: 2>/dev/null || true
export DISPLAY=${DISPLAY:-:1}
export XAUTHORITY=${XAUTHORITY:-$HOME/.Xauthority}

# Check python3.11 available
if ! command -v python3.11 > /dev/null 2>&1; then
    echo "Python 3.11 not found. Please ask admin to install:"
    echo "  sudo apt-get install python3.11 python3.11-tk"
    read -p "Press Enter to exit..."
    exit 1
fi

# Install libs if needed
if ! python3.11 -c "import customtkinter" 2>/dev/null; then
    echo "Installing libraries..."
    python3.11 -m pip install --user $LIBS 2>/dev/null || \
    python3.11 -m pip install $LIBS 2>/dev/null || true
fi

# Run with python3.11 (stable, no segfault)
cd "$APP_DIR"
exec python3.11 app.py "$@"
"""
with open("pkg/usr/local/bin/ResultAnalyzer","w") as f:
    f.write(launcher)
os.chmod("pkg/usr/local/bin/ResultAnalyzer", 0o755)

# Icons
if os.path.exists("logo.png"):
    shutil.copy("logo.png","pkg/usr/share/pixmaps/result-analyzer.png")
for size in ["256x256","128x128","64x64","48x48"]:
    src = f"icons/{size}/result-analyzer.png"
    dst = f"pkg/usr/share/icons/hicolor/{size}/apps/result-analyzer.png"
    if os.path.exists(src): shutil.copy(src, dst)

# Desktop file
with open("pkg/usr/share/applications/result-analyzer.desktop","w") as f:
    f.write("[Desktop Entry]\nVersion=1.0\nType=Application\n"
            "Name=College Result Analyzer\nComment=Professional result analysis\n"
            "Exec=ResultAnalyzer\nIcon=result-analyzer\nTerminal=false\n"
            "Categories=Education;Office;\nStartupNotify=true\n")

# Control file
with open("pkg/DEBIAN/control","w") as f:
    f.write(f"Package: {DEB_NAME}\nVersion: {VERSION}\nArchitecture: all\n"
            "Maintainer: Developer <dev@email.com>\n"
            "Depends: python3, python3-tk\n"
            f"Description: College Result Analyzer\n Professional software.\n")

# Postinst — installs Python 3.11 + libraries automatically
postinst = r"""#!/bin/bash
set -e
LIBS="customtkinter pdfplumber pandas matplotlib requests openpyxl pillow"

echo "Setting up College Result Analyzer..."

# Install Python 3.11
if ! command -v python3.11 > /dev/null 2>&1; then
    echo "Installing Python 3.11..."
    add-apt-repository ppa:deadsnakes/ppa -y 2>/dev/null || true
    apt-get update -qq 2>/dev/null || true
    apt-get install -y python3.11 python3.11-tk 2>/dev/null || true
fi

# Install pip for python3.11
if ! python3.11 -m pip --version > /dev/null 2>&1; then
    apt-get install -y python3.11-distutils 2>/dev/null || true
    curl -s https://bootstrap.pypa.io/get-pip.py | python3.11 2>/dev/null || true
fi

# Install libraries with python3.11
if command -v python3.11 > /dev/null 2>&1; then
    echo "Installing Python libraries..."
    python3.11 -m pip install --quiet $LIBS 2>/dev/null || true
fi

# Update desktop
update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

echo "Setup complete! Run: ResultAnalyzer --activate"
exit 0
"""
with open("pkg/DEBIAN/postinst","w") as f:
    f.write(postinst)
os.chmod("pkg/DEBIAN/postinst", 0o755)

result = subprocess.run(["dpkg-deb","--build","pkg",f"{DEB_NAME}_{VERSION}.deb"])
if result.returncode != 0:
    print("dpkg-deb failed!"); sys.exit(1)

deb_path = f"{DEB_NAME}_{VERSION}.deb"
print(f"\nDeb: {deb_path} ({os.path.getsize(deb_path)//1024} KB)")
print("Build complete!")
