"""
build_linux.py
This script is run by GitHub Actions to:
1. Build Linux binary with PyInstaller
2. Create .deb package with icon
Run: python3 build_linux.py
"""

import os
import sys
import shutil
import subprocess

# ── Config ──
APP_NAME    = "ResultAnalyzer"
DEB_NAME    = "result-analyzer"
VERSION     = "1.0.0"
MAINTAINER  = "Developer <dev@email.com>"
DESCRIPTION = "College Result Analyzer"

# ── Step 1: Build with PyInstaller ──
print("\n[1/3] Building with PyInstaller...")

cmd = [
    "pyinstaller",
    "--onefile",
    "--name", APP_NAME,
    "--hidden-import=pdfplumber",
    "--hidden-import=pdfminer",
    "--hidden-import=pdfminer.high_level",
    "--hidden-import=pdfminer.layout",
    "--hidden-import=pdfminer.converter",
    "--hidden-import=pdfminer.pdfinterp",
    "--hidden-import=pdfminer.pdfdevice",
    "--hidden-import=customtkinter",
    "--hidden-import=openpyxl",
    "--hidden-import=openpyxl.styles",
    "--hidden-import=pandas",
    "--hidden-import=pandas.io.formats.excel",
    "--hidden-import=matplotlib",
    "--hidden-import=matplotlib.backends.backend_tkagg",
    "--hidden-import=matplotlib.backends.backend_agg",
    "--hidden-import=requests",
    "--hidden-import=charset_normalizer",
    "--hidden-import=PIL",
    "--hidden-import=tkinter",
    "--hidden-import=tkinter.ttk",
    "--hidden-import=tkinter.messagebox",
    "--hidden-import=tkinter.filedialog",
    "--hidden-import=_tkinter",
    "--collect-all", "customtkinter",
    "--collect-all", "pdfplumber",
    "--collect-all", "pdfminer",
    "--collect-all", "matplotlib",
    "app.py"
]

result = subprocess.run(cmd)
if result.returncode != 0:
    print("PyInstaller failed!")
    sys.exit(1)

binary_path = f"dist/{APP_NAME}"
if not os.path.exists(binary_path):
    print(f"Binary not found: {binary_path}")
    sys.exit(1)

print(f"Binary created: {binary_path}")
print(f"Binary size: {os.path.getsize(binary_path) // (1024*1024)} MB")


# ── Step 2: Resize icons ──
print("\n[2/3] Creating icons...")

try:
    from PIL import Image
    if os.path.exists("logo.png"):
        img = Image.open("logo.png")
        for size in [256, 128, 64, 48, 32]:
            folder = f"icons/{size}x{size}"
            os.makedirs(folder, exist_ok=True)
            img.resize((size, size), Image.LANCZOS).save(f"{folder}/result-analyzer.png")
        print("Icons created!")
    else:
        print("logo.png not found - skipping icons")
except Exception as e:
    print(f"Icon creation failed: {e} - continuing anyway")


# ── Step 3: Create .deb package ──
print("\n[3/3] Creating .deb package...")

# Create folder structure
dirs = [
    "pkg/DEBIAN",
    "pkg/usr/local/bin",
    "pkg/usr/share/applications",
    "pkg/usr/share/pixmaps",
    "pkg/usr/share/icons/hicolor/256x256/apps",
    "pkg/usr/share/icons/hicolor/128x128/apps",
    "pkg/usr/share/icons/hicolor/64x64/apps",
    "pkg/usr/share/icons/hicolor/48x48/apps",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Copy binary
shutil.copy(binary_path, f"pkg/usr/local/bin/result-analyzer-bin")
os.chmod(f"pkg/usr/local/bin/result-analyzer-bin", 0o755)

# Create wrapper script
wrapper = """#!/bin/bash
export DISPLAY=${DISPLAY:-:0}
export GDK_BACKEND=x11
export LIBGL_ALWAYS_SOFTWARE=1
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
if [ -d /usr/share/tcltk/tcl8.6 ]; then
  export TCL_LIBRARY=/usr/share/tcltk/tcl8.6
fi
if [ -d /usr/share/tcltk/tk8.6 ]; then
  export TK_LIBRARY=/usr/share/tcltk/tk8.6
fi
exec /usr/local/bin/result-analyzer-bin "$@"
"""
with open("pkg/usr/local/bin/ResultAnalyzer", "w") as f:
    f.write(wrapper)
os.chmod("pkg/usr/local/bin/ResultAnalyzer", 0o755)

# Copy icons
if os.path.exists("logo.png"):
    shutil.copy("logo.png", "pkg/usr/share/pixmaps/result-analyzer.png")
for size in ["256x256", "128x128", "64x64", "48x48"]:
    src = f"icons/{size}/result-analyzer.png"
    dst = f"pkg/usr/share/icons/hicolor/{size}/apps/result-analyzer.png"
    if os.path.exists(src):
        shutil.copy(src, dst)

# Create desktop file
desktop = """[Desktop Entry]
Version=1.0
Type=Application
Name=College Result Analyzer
Comment=Professional result analysis software
Exec=ResultAnalyzer
Icon=result-analyzer
Terminal=false
Categories=Education;Office;
StartupNotify=true
"""
with open("pkg/usr/share/applications/result-analyzer.desktop", "w") as f:
    f.write(desktop)

# Create control file
control = f"""Package: {DEB_NAME}
Version: {VERSION}
Architecture: amd64
Maintainer: {MAINTAINER}
Depends: libx11-6, libglib2.0-0, libgl1-mesa-glx, python3-tk, libfreetype6, libfontconfig1, libxcb1
Description: {DESCRIPTION}
 Professional result analysis software for colleges.
"""
with open("pkg/DEBIAN/control", "w") as f:
    f.write(control)

# Create postinst
postinst = """#!/bin/bash
set -e
update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
exit 0
"""
with open("pkg/DEBIAN/postinst", "w") as f:
    f.write(postinst)
os.chmod("pkg/DEBIAN/postinst", 0o755)

# Build deb
result = subprocess.run(["dpkg-deb", "--build", "pkg", f"{DEB_NAME}_{VERSION}.deb"])
if result.returncode != 0:
    print("dpkg-deb failed!")
    sys.exit(1)

deb_path = f"{DEB_NAME}_{VERSION}.deb"
print(f"Deb package created: {deb_path}")
print(f"Deb size: {os.path.getsize(deb_path) // (1024*1024)} MB")
print("\nBuild complete!")
