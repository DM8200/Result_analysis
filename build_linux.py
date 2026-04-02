"""
build_linux.py
Packages the Python source files inside .deb
Runs with system Python (no PyInstaller = no segfault)
Code is protected by compiling to .pyc bytecode
"""

import os
import sys
import shutil
import subprocess
import py_compile
import compileall

APP_NAME    = "ResultAnalyzer"
DEB_NAME    = "result-analyzer"
VERSION     = "1.0.0"
MAINTAINER  = "Developer <dev@email.com>"
DESCRIPTION = "College Result Analyzer"

# Python files to compile and package
PY_FILES = ["app.py", "pdf_parser.py", "license_client.py"]


# ── Step 1: Compile .py to .pyc ──
print("\n[1/3] Compiling Python files to bytecode...")

os.makedirs("compiled", exist_ok=True)

for pyfile in PY_FILES:
    if not os.path.exists(pyfile):
        print(f"  ERROR: {pyfile} not found!")
        sys.exit(1)
    
    out = f"compiled/{pyfile}c"
    py_compile.compile(pyfile, cfile=out, optimize=2, doraise=True)
    size = os.path.getsize(out)
    print(f"  Compiled: {pyfile} -> {out} ({size} bytes)")

print("  Compilation complete!")


# ── Step 2: Resize icons ──
print("\n[2/3] Creating icons...")
try:
    from PIL import Image
    if os.path.exists("logo.png"):
        img = Image.open("logo.png")
        for size in [256, 128, 64, 48, 32]:
            folder = f"icons/{size}x{size}"
            os.makedirs(folder, exist_ok=True)
            img.resize((size, size), Image.LANCZOS).save(
                f"{folder}/result-analyzer.png"
            )
        print("  Icons created!")
    else:
        print("  logo.png not found - skipping")
except Exception as e:
    print(f"  Icon error: {e}")


# ── Step 3: Create .deb package ──
print("\n[3/3] Creating .deb package...")

dirs = [
    "pkg/DEBIAN",
    "pkg/usr/local/bin",
    "pkg/opt/result-analyzer",
    "pkg/usr/share/applications",
    "pkg/usr/share/pixmaps",
    "pkg/usr/share/icons/hicolor/256x256/apps",
    "pkg/usr/share/icons/hicolor/128x128/apps",
    "pkg/usr/share/icons/hicolor/64x64/apps",
    "pkg/usr/share/icons/hicolor/48x48/apps",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Copy compiled .pyc files to /opt/result-analyzer/
for pyfile in PY_FILES:
    src = f"compiled/{pyfile}c"
    dst = f"pkg/opt/result-analyzer/{pyfile}c"
    shutil.copy(src, dst)
    print(f"  Copied: {dst}")

# Copy logo to app folder
if os.path.exists("logo.png"):
    shutil.copy("logo.png", "pkg/opt/result-analyzer/logo.png")

# Main launcher script
launcher = """#!/bin/bash
# College Result Analyzer - Launcher
# Runs with system Python (stable, no segfault)

APP_DIR="/opt/result-analyzer"
VENV_DIR="$HOME/.result-analyzer-env"

# Create virtual environment if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Setting up environment (first time only)..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --quiet --upgrade pip
    pip install --quiet customtkinter pdfplumber pandas matplotlib requests openpyxl pillow
    echo "Setup complete!"
fi

source "$VENV_DIR/bin/activate"

# Run the app
cd "$APP_DIR"
exec python3 app.pyc "$@"
"""
with open("pkg/usr/local/bin/ResultAnalyzer", "w") as f:
    f.write(launcher)
os.chmod("pkg/usr/local/bin/ResultAnalyzer", 0o755)

# Icons
if os.path.exists("logo.png"):
    shutil.copy("logo.png", "pkg/usr/share/pixmaps/result-analyzer.png")
for size in ["256x256", "128x128", "64x64", "48x48"]:
    src = f"icons/{size}/result-analyzer.png"
    dst = f"pkg/usr/share/icons/hicolor/{size}/apps/result-analyzer.png"
    if os.path.exists(src):
        shutil.copy(src, dst)

# Desktop file
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

# Control file
control = f"""Package: {DEB_NAME}
Version: {VERSION}
Architecture: all
Maintainer: {MAINTAINER}
Depends: python3, python3-pip, python3-tk, python3-venv
Description: {DESCRIPTION}
 Professional result analysis software for colleges.
"""
with open("pkg/DEBIAN/control", "w") as f:
    f.write(control)

# Postinst — installs Python packages on customer PC
postinst = """#!/bin/bash
set -e

# Update desktop database
update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

exit 0
"""
with open("pkg/DEBIAN/postinst", "w") as f:
    f.write(postinst)
os.chmod("pkg/DEBIAN/postinst", 0o755)

# Build deb
result = subprocess.run(
    ["dpkg-deb", "--build", "pkg", f"{DEB_NAME}_{VERSION}.deb"]
)
if result.returncode != 0:
    print("dpkg-deb failed!")
    sys.exit(1)

deb_path = f"{DEB_NAME}_{VERSION}.deb"
deb_size = os.path.getsize(deb_path) // (1024)
print(f"\nDeb package: {deb_path} ({deb_size} KB)")
print("Build complete!")
