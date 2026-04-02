"""
build_linux.py
Packages Python files inside .deb with improved launcher.
"""

import os
import sys
import shutil
import subprocess
import py_compile

APP_NAME    = "ResultAnalyzer"
DEB_NAME    = "result-analyzer"
VERSION     = "1.0.0"
MAINTAINER  = "Developer <dev@email.com>"
DESCRIPTION = "College Result Analyzer"

PY_FILES = ["app.py", "pdf_parser.py", "license_client.py"]


# ── Step 1: Compile .py to .pyc ──
print("\n[1/3] Compiling Python files...")
os.makedirs("compiled", exist_ok=True)
for pyfile in PY_FILES:
    if not os.path.exists(pyfile):
        print(f"  ERROR: {pyfile} not found!")
        sys.exit(1)
    out = f"compiled/{pyfile}c"
    py_compile.compile(pyfile, cfile=out, optimize=2, doraise=True)
    print(f"  Compiled: {pyfile} -> {out}")
print("  Done!")


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

# Copy compiled files
for pyfile in PY_FILES:
    shutil.copy(f"compiled/{pyfile}c", f"pkg/opt/result-analyzer/{pyfile}c")
    print(f"  Copied: {pyfile}c")

if os.path.exists("logo.png"):
    shutil.copy("logo.png", "pkg/opt/result-analyzer/logo.png")

# ── Launcher script — installs venv + deps automatically ──
launcher = """#!/bin/bash
# College Result Analyzer Launcher

APP_DIR="/opt/result-analyzer"
VENV_DIR="$HOME/.result-analyzer-env"
LIBS="customtkinter pdfplumber pandas matplotlib requests openpyxl pillow"

setup_environment() {
    echo "Setting up environment (first time only, please wait)..."

    # Install python3-venv if missing
    if ! python3 -m venv --help > /dev/null 2>&1; then
        echo "Installing python3-venv..."
        sudo apt-get install -y python3-venv python3-pip 2>/dev/null || true
    fi

    # Try creating venv
    if python3 -m venv "$VENV_DIR" 2>/dev/null; then
        echo "Virtual environment created."
        source "$VENV_DIR/bin/activate"
        pip install --quiet --upgrade pip
        pip install --quiet $LIBS
        echo "Libraries installed!"
    else
        # venv failed — install system-wide with pip
        echo "Installing libraries system-wide..."
        pip3 install --user --quiet $LIBS 2>/dev/null || \
        pip3 install --quiet $LIBS 2>/dev/null || \
        sudo pip3 install --quiet $LIBS 2>/dev/null || true
        echo "Libraries installed!"
    fi
}

activate_environment() {
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    # Also add user local bin to PATH
    export PATH="$HOME/.local/bin:$PATH"
    export PYTHONPATH="$HOME/.local/lib/python3/dist-packages:$PYTHONPATH"
}

check_libs() {
    python3 -c "import customtkinter" 2>/dev/null
    return $?
}

# Setup if needed
if ! check_libs; then
    setup_environment
fi

# Activate environment
activate_environment

# Check again
if ! check_libs; then
    echo ""
    echo "ERROR: Could not install required libraries."
    echo "Please run manually:"
    echo "  sudo apt-get install python3-pip python3-venv python3-tk"
    echo "  pip3 install customtkinter pdfplumber pandas matplotlib requests openpyxl pillow"
    echo ""
    exit 1
fi

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

# Control file — now depends on python3-pip too
control = f"""Package: {DEB_NAME}
Version: {VERSION}
Architecture: all
Maintainer: {MAINTAINER}
Depends: python3, python3-pip, python3-tk
Description: {DESCRIPTION}
 Professional result analysis software for colleges.
"""
with open("pkg/DEBIAN/control", "w") as f:
    f.write(control)

# Postinst — installs python3-venv and all libraries after .deb install
postinst = """#!/bin/bash
set -e

echo "Installing required Python packages..."

# Install venv
apt-get install -y python3-venv python3-pip 2>/dev/null || true

# Install Python libraries for all users
pip3 install --quiet customtkinter pdfplumber pandas matplotlib requests openpyxl pillow 2>/dev/null || \
pip3 install customtkinter pdfplumber pandas matplotlib requests openpyxl pillow 2>/dev/null || true

# Update desktop
update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

echo "Installation complete!"
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
print(f"\nDeb: {deb_path} ({os.path.getsize(deb_path)//1024} KB)")
print("Build complete!")
