@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python is not installed. You can still get a standalone EXE by using the GitHub Actions workflow.
  echo See README.md for the no-local-Python build steps.
  pause
  exit /b 1
)
echo Building standalone EXE. Python is required only for this build step, not to run the resulting EXE.
py -3 -m venv .venv
if errorlevel 1 goto fail
call .venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto fail
call .venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
call .venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name BilgeOverlay --add-data "config.json;." app.py
if errorlevel 1 goto fail
echo.
echo DONE: %CD%\dist\BilgeOverlay.exe
echo This EXE does not require Python on the computer that runs it.
pause
exit /b 0
:fail
echo Build failed. Check the error above.
pause
exit /b 1
