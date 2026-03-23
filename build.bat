@echo off
echo ============================================
echo   College Result Analyzer - Build EXE
echo ============================================
echo.

REM ── Step 1: Install/upgrade PyInstaller ──
echo [1/4] Installing PyInstaller...
pip install --upgrade pyinstaller
echo.

REM ── Step 2: Clean ALL old build files including cache ──
echo [2/4] Cleaning old build and cache...
if exist "build"               rmdir /s /q build
if exist "dist"                rmdir /s /q dist
if exist "ResultAnalyzer.spec" del /f /q ResultAnalyzer.spec
if exist "__pycache__"         rmdir /s /q __pycache__

REM Clear PyInstaller cache
if exist "%APPDATA%\pyinstaller" rmdir /s /q "%APPDATA%\pyinstaller"

REM Clear Windows icon cache
ie4uinit.exe -show
taskkill /IM explorer.exe /F >nul 2>&1
del /f /q "%localappdata%\IconCache.db" >nul 2>&1
del /f /q "%localappdata%\Microsoft\Windows\Explorer\iconcache*" >nul 2>&1
start explorer.exe
echo.

REM ── Step 3: Verify icon file exists ──
echo [3/4] Checking icon...
if exist "icon.ico" (
    echo Found icon.ico
) else (
    echo WARNING: icon.ico not found in this folder!
    echo Place icon.ico here: %cd%
    pause
    exit /b 1
)
echo.

REM ── Step 4: Build EXE ──
echo [4/4] Building EXE... (this takes 2-5 minutes, please wait)
echo.

pyinstaller --onefile --windowed ^
  --name "ResultAnalyzer" ^
  --icon "icon.ico" ^
  --hidden-import=pdfplumber ^
  --hidden-import=pdfminer ^
  --hidden-import=pdfminer.high_level ^
  --hidden-import=pdfminer.layout ^
  --hidden-import=pdfminer.converter ^
  --hidden-import=pdfminer.pdfinterp ^
  --hidden-import=pdfminer.pdfdevice ^
  --hidden-import=customtkinter ^
  --hidden-import=openpyxl ^
  --hidden-import=openpyxl.styles ^
  --hidden-import=openpyxl.styles.fills ^
  --hidden-import=openpyxl.styles.fonts ^
  --hidden-import=openpyxl.styles.alignment ^
  --hidden-import=pandas ^
  --hidden-import=pandas.io.formats.excel ^
  --hidden-import=matplotlib ^
  --hidden-import=matplotlib.backends.backend_tkagg ^
  --hidden-import=matplotlib.figure ^
  --hidden-import=requests ^
  --hidden-import=charset_normalizer ^
  --hidden-import=PIL ^
  --collect-all customtkinter ^
  --collect-all pdfplumber ^
  --collect-all pdfminer ^
  app.py

echo.

if exist "dist\ResultAnalyzer.exe" (
    echo ============================================
    echo   BUILD SUCCESSFUL!
    echo   Your EXE is ready at:
    echo   dist\ResultAnalyzer.exe
    echo ============================================
    echo.
    ie4uinit.exe -show
    taskkill /IM explorer.exe /F >nul 2>&1
    del /f /q "%localappdata%\IconCache.db" >nul 2>&1
    del /f /q "%localappdata%\Microsoft\Windows\Explorer\iconcache*" >nul 2>&1
    start explorer.exe
    timeout /t 2 /nobreak >nul
    explorer dist
) else (
    echo ============================================
    echo   BUILD FAILED!
    echo   Check the error messages above.
    echo ============================================
)

pause
