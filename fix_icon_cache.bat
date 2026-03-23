@echo off
echo ============================================
echo   Fixing Windows Icon Cache...
echo ============================================
echo.
echo Please wait, do not close this window...
echo.

REM Kill explorer
taskkill /f /im explorer.exe >nul 2>&1

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Delete all icon cache files
del /f /q "%localappdata%\IconCache.db" >nul 2>&1
del /f /a "%localappdata%\Microsoft\Windows\Explorer\iconcache_*.db" >nul 2>&1
del /f /a "%localappdata%\Microsoft\Windows\Explorer\iconcache.db" >nul 2>&1
del /f /a "%localappdata%\Microsoft\Windows\Explorer\thumbcache_*.db" >nul 2>&1

REM Rebuild icon cache
ie4uinit.exe -show >nul 2>&1

REM Restart explorer
start explorer.exe

timeout /t 2 /nobreak >nul

echo ============================================
echo   Icon cache cleared successfully!
echo   Please RESTART YOUR PC now for
echo   the new icon to show correctly.
echo ============================================
echo.
pause
