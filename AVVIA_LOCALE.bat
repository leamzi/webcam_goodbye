@echo off
setlocal
cd /d "%~dp0"
if errorlevel 1 (
  echo [Vanish Lab] Impossibile accedere alla cartella del progetto.
  goto :error
)

set "VENV_DIR=%CD%\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "FOUND_PYTHON_313=0"

if exist "%VENV_PY%" goto :venv_ready

echo [Vanish Lab] Creo l'ambiente Python locale...
call :try_py_launcher
if not exist "%VENV_PY%" call :try_python_command
if exist "%VENV_PY%" goto :venv_ready

if "%FOUND_PYTHON_313%"=="0" (
  echo [Vanish Lab] Python 3.13 non trovato. VanishCam richiede Python 3.13.
) else (
  echo [Vanish Lab] Impossibile creare l'ambiente virtuale in "%VENV_DIR%".
)
goto :error

:venv_ready
"%VENV_PY%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 13) else 1)" >nul 2>nul
if errorlevel 1 (
  echo [Vanish Lab] L'ambiente virtuale deve usare Python 3.13: "%VENV_PY%".
  echo [Vanish Lab] Elimina la cartella .venv e riavvia dopo aver installato Python 3.13.
  goto :error
)

"%VENV_PY%" -c "import cv2, mediapipe, numpy, pyvirtualcam, pygame" >nul 2>nul
if errorlevel 1 (
  echo [Vanish Lab] Installo i componenti necessari. Serve internet solo questa volta...
  "%VENV_PY%" -m pip install -r "requirements.txt"
  if errorlevel 1 goto :error
)

echo [Vanish Lab] Avvio la webcam...
"%VENV_PY%" "vanish_cam.py" %*
if errorlevel 1 goto :error
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
echo Impossibile avviare Vanish Lab. Controlla i messaggi qui sopra.
pause
exit /b 1
