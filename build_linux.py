"""
build_linux.py
Ships .py files inside .deb
Compiles to .pyc ON CUSTOMER PC using their Python version
This avoids the "Bad magic number" error completely
"""

import os
import sys
import shutil
import subprocess

APP_NAME    = "ResultAnalyzer"
DEB_NAME    = "result-analyzer"
VERSION     = "1.0.0"
MAINTAINER  = "Developer <dev@email.com>"
DESCRIPTION = "College Result Analyzer"

PY_FILES = ["app.py", "pdf_parser.py", "license_client.py"]


# ── Step 1: Verify all py files exist ──
print("\n[1/3] Checking Python files...")
for pyfile in PY_FILES:
    if not os.path.exists(pyfile):
        print(f"  ERROR: {pyfile} not found!")
        sys.exit(1)
    print(f"  Found: {pyfile}")
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

# Copy .py files (will be compiled on customer PC)
for pyfile in PY_FILES:
    shutil.copy(pyfile, f"pkg/opt/result-analyzer/{pyfile}")
    print(f"  Copied: {pyfile}")

if os.path.exists("logo.png"):
    shutil.copy("logo.png", "pkg/opt/result-analyzer/logo.png")

# ── Launcher script ──
launcher = r"""#!/bin/bash
# College Result Analyzer Launcher

APP_DIR="/opt/result-analyzer"
LIBS="customtkinter pdfplumber pandas matplotlib requests openpyxl pillow"
COMPILED_FLAG="$APP_DIR/.compiled_ok"

# Find Python 3.11 first (fixes segfault), then fallback
find_python() {
    for py in python3.11 python3.12 python3.10 python3; do
        if command -v "$py" > /dev/null 2>&1; then
            if "$py" -c "import tkinter" 2>/dev/null; then
                echo "$py"
                return 0
            fi
        fi
    done
    echo "python3"
}

PYTHON=$(find_python)

# Install libraries if needed
if ! "$PYTHON" -c "import customtkinter" 2>/dev/null; then
    echo "Installing required libraries..."
    "$PYTHON" -m pip install --user $LIBS 2>/dev/null || \
    "$PYTHON" -m pip install $LIBS 2>/dev/null || \
    sudo "$PYTHON" -m pip install $LIBS 2>/dev/null || true
fi

# Compile .py to .pyc using customer's Python (avoids magic number error)
if [ ! -f "$COMPILED_FLAG" ] || [ ! -f "$APP_DIR/app.pyc" ]; then
    echo "Optimizing for your system..."
    "$PYTHON" -m compileall -b -q "$APP_DIR/" 2>/dev/null || true
    touch "$COMPILED_FLAG"
fi

# Run app — use .pyc if exists, else .py
cd "$APP_DIR"
if [ -f "app.pyc" ]; then
    exec "$PYTHON" app.pyc "$@"
else
    exec "$PYTHON" app.py "$@"
fi
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

# Postinst
postinst = r"""#!/bin/bash
set -e

LIBS="customtkinter pdfplumber pandas matplotlib requests openpyxl pillow"

echo "Setting up College Result Analyzer..."

# Install Python 3.11 if not available
if ! command -v python3.11 > /dev/null 2>&1; then
    add-apt-repository ppa:deadsnakes/ppa -y 2>/dev/null || true
    apt-get update -qq 2>/dev/null || true
    apt-get install -y python3.11 python3.11-tk 2>/dev/null || true
fi

# Install pip
for py in python3.11 python3.10 python3; do
    if command -v "$py" > /dev/null 2>&1; then
        if ! "$py" -m pip --version > /dev/null 2>&1; then
            curl -s https://bootstrap.pypa.io/get-pip.py | "$py" 2>/dev/null || true
        fi
        echo "Installing libraries with $py..."
        "$py" -m pip install --quiet $LIBS 2>/dev/null && break || true
    fi
done

# Compile .py files for this system's Python
for py in python3.11 python3.10 python3; do
    if command -v "$py" > /dev/null 2>&1; then
        echo "Compiling for $py..."
        "$py" -m compileall -b -q /opt/result-analyzer/ 2>/dev/null || true
        touch /opt/result-analyzer/.compiled_ok
        break
    fi
done

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
