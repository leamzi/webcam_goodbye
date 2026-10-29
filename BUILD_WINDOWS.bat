@echo off
setlocal
cd /d "%~dp0"
if errorlevel 1 (
  echo [VanishCam] Unable to access the project directory.
  goto :error
)

set "VENV_DIR=%CD%\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "PYINSTALLER_VERSION=6.22.3"
set "FOUND_PYTHON_313=0"

if exist "%VENV_PY%" goto :venv_ready

echo [VanishCam] Creating local Python environment...
call :try_py_launcher
if not exist "%VENV_PY%" call :try_python_command
if exist "%VENV_PY%" goto :venv_ready

if "%FOUND_PYTHON_313%"=="0" (
  echo [VanishCam] Python 3.13 was not found. VanishCam requires Python 3.13.
) else (
  echo [VanishCam] Unable to create the virtual environment at "%VENV_DIR%".
)
goto :error

:venv_ready
"%VENV_PY%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 13) else 1)" >nul 2>nul
if errorlevel 1 (
  echo [VanishCam] The virtual environment must use Python 3.13: "%VENV_PY%".
  echo [VanishCam] Delete .venv and restart after installing Python 3.13.
  goto :error
)

"%VENV_PY%" -c "import importlib.metadata as metadata; import cv2, mediapipe, numpy, pygame, pyvirtualcam; raise SystemExit(0 if metadata.version('pyinstaller') == '%PYINSTALLER_VERSION%' else 1)" >nul 2>nul
if errorlevel 1 (
  echo [VanishCam] Installing reproducible build dependencies...
  "%VENV_PY%" -m pip install -r "requirements.txt" "pyinstaller==%PYINSTALLER_VERSION%"
  if errorlevel 1 goto :error
)

echo [VanishCam] Verifying local models...
"%VENV_PY%" "prepare_models.py" --verify-only
if errorlevel 1 (
  echo.
  echo [VanishCam] Required models are missing or failed verification.
  echo [VanishCam] Prepare them explicitly before building:
  echo   .\.venv\Scripts\python.exe prepare_models.py
  goto :error
)

:build
"%VENV_PY%" -m PyInstaller --noconfirm --distpath dist --workpath build VanishCam.spec
if errorlevel 1 goto :error

"dist\VanishCam.exe" --self-test
if errorlevel 1 goto :error

echo.
echo [VanishCam] Build ready: dist\VanishCam.exe
exit /b 0

:try_py_launcher
where py >nul 2>nul
if errorlevel 1 exit /b 0
py -3.13 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 13) else 1)" >nul 2>nul
if errorlevel 1 exit /b 0
set "FOUND_PYTHON_313=1"
py -3.13 -m venv "%VENV_DIR%"
exit /b 0

:try_python_command
where python >nul 2>nul
if errorlevel 1 exit /b 0
python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 13) else 1)" >nul 2>nul
if errorlevel 1 exit /b 0
set "FOUND_PYTHON_313=1"
python -m venv "%VENV_DIR%"
exit /b 0

:error
echo.
echo Unable to build VanishCam. Review the messages above for details.
pause
exit /b 1
