@echo off
echo Building AIImageGenerator executable...
python -m PyInstaller --clean --onefile --name AIImageGenerator --windowed main.py

echo Build complete. Executable is in the dist folder.
pause 