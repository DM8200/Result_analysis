"""
build_linux.py
Uses Python 3.11 which fixes customtkinter segfault on Ubuntu 22.04
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

# ── Launcher — tries Python 3.11 first, falls back to 3.10/3 ──
launcher = r"""#!/bin/bash
# College Result Analyzer Launcher

APP_DIR="/opt/result-analyzer"
LIBS="customtkinter pdfplumber pandas matplotlib requests openpyxl pillow"

# Find best Python version (3.11 fixes customtkinter segfault)
find_python() {
    for py in python3.11 python3.12 python3.10 python3; do
        if command -v "$py" > /dev/null 2>&1; then
            # Test if customtkinter works with this Python
            if "$py" -c "import customtkinter" 2>/dev/null; then
                echo "$py"
                return 0
            fi
        fi
    done
    # Return first available Python even if customtkinter not yet installed
    for py in python3.11 python3.12 python3.10 python3; do
        if command -v "$py" > /dev/null 2>&1; then
            echo "$py"
            return 0
        fi
    done
    echo "python3"
}

install_libs() {
    local PYTHON="$1"
    echo "Installing required libraries (first time only)..."

    # Try pip install
    "$PYTHON" -m pip install --user --quiet $LIBS 2>/dev/null || \
    "$PYTHON" -m pip install --quiet $LIBS 2>/dev/null || \
    sudo "$PYTHON" -m pip install --quiet $LIBS 2>/dev/null || true

    echo "Libraries installed!"
}

install_python311() {
    echo "Installing Python 3.11 (fixes display issues)..."
    sudo add-apt-repository ppa:deadsnakes/ppa -y 2>/dev/null || true
    sudo apt-get update -qq 2>/dev/null || true
    sudo apt-get install -y python3.11 python3.11-tk python3.11-venv 2>/dev/null || true
    curl -s https://bootstrap.pypa.io/get-pip.py | python3.11 2>/dev/null || true
}

# Find Python
PYTHON=$(find_python)
echo "Using: $PYTHON"

# Check if libs installed
if ! "$PYTHON" -c "import customtkinter" 2>/dev/null; then
    # Try installing libs with current Python
    install_libs "$PYTHON"

    # If still failing and python3.11 not available, install it
    if ! "$PYTHON" -c "import customtkinter" 2>/dev/null; then
        if ! command -v python3.11 > /dev/null 2>&1; then
            install_python311
        fi
        PYTHON=$(find_python)
        install_libs "$PYTHON"
    fi
fi

# Final check
if ! "$PYTHON" -c "import customtkinter" 2>/dev/null; then
    echo ""
    echo "ERROR: Could not set up required libraries."
    echo "Please run manually:"
    echo "  sudo add-apt-repository ppa:deadsnakes/ppa -y"
    echo "  sudo apt-get install python3.11 python3.11-tk"
    echo "  python3.11 -m pip install customtkinter pdfplumber pandas matplotlib requests openpyxl pillow"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Run app
cd "$APP_DIR"
exec "$PYTHON" app.pyc "$@"
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
Depends: python3, python3-tk
Description: {DESCRIPTION}
 Professional result analysis software for colleges.
"""
with open("pkg/DEBIAN/control", "w") as f:
    f.write(control)

# Postinst — runs after .deb install
postinst = r"""#!/bin/bash
set -e

LIBS="customtkinter pdfplumber pandas matplotlib requests openpyxl pillow"

echo "Setting up College Result Analyzer..."

# Install Python 3.11 (fixes segfault with customtkinter on Ubuntu 22.04)
if ! command -v python3.11 > /dev/null 2>&1; then
    echo "Installing Python 3.11..."
    add-apt-repository ppa:deadsnakes/ppa -y 2>/dev/null || true
    apt-get update -qq 2>/dev/null || true
    apt-get install -y python3.11 python3.11-tk python3.11-distutils 2>/dev/null || true
fi

# Install pip for python3.11
if ! python3.11 -m pip --version > /dev/null 2>&1; then
    curl -s https://bootstrap.pypa.io/get-pip.py | python3.11 2>/dev/null || true
fi

# Install libraries
if command -v python3.11 > /dev/null 2>&1; then
    echo "Installing Python libraries with Python 3.11..."
    python3.11 -m pip install --quiet $LIBS 2>/dev/null || true
else
    echo "Installing Python libraries..."
    pip3 install --quiet $LIBS 2>/dev/null || \
    python3 -m pip install --quiet $LIBS 2>/dev/null || true
fi

# Update desktop
update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

echo "Setup complete!"
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
