@echo off
REM Run this on a Windows machine with Python 3.10+ installed.
REM Produces dist\APODWallpaper-1.0.0-*.msi

echo Installing build dependency (cx_Freeze)...
pip install --upgrade cx_Freeze

echo Building MSI...
python setup.py bdist_msi

echo.
echo Done. Look inside the "dist" folder for the .msi file.
pause
