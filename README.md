# VanishCam

VanishCam applies local disappearance effects to a live webcam feed. The main
application currently supports two modes: **Normal Vanish** and
**Naruto Vanish**.

## Requirements

- Windows 10 or newer.
- Python 3.13.
- A webcam.
- Optional: OBS Studio or Unity Capture for virtual-camera output.

All Python packages are installed into the repository-local `.venv`. The
launch and build scripts do not install packages globally and do not upgrade
pip automatically.

## Installation

Clone the repository and open PowerShell in its root directory:

```powershell
git clone <repository-url>
cd webcam_goodbye
```

Create the Python 3.13 environment and install the pinned dependencies:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Download and verify the required MediaPipe models explicitly:

```powershell
.\.venv\Scripts\python.exe prepare_models.py
```

`prepare_models.py` is the only project component that downloads models. It
accepts only HTTPS URLs on `storage.googleapis.com`, restricts redirects,
downloads through temporary `.part` files, and verifies both size and SHA-256
before replacing a destination file.

## Model verification and offline runtime

The downloaded models are stored under `models/`, which is intentionally not
tracked by Git. `hand_landmarker.task` is tracked because Naruto mode requires
it directly.

Before MediaPipe is initialized, `vanish_cam.py` verifies every required model
against the size and SHA-256 recorded in `models_manifest.py`. If a model is
missing or altered, startup stops and instructs you to run:

```powershell
.\.venv\Scripts\python.exe prepare_models.py
```

To verify existing files without downloading anything:

```powershell
.\.venv\Scripts\python.exe prepare_models.py --verify-only
```

The main application does not download models or make project-defined network
requests during normal runtime.

## Running VanishCam

Double-click `AVVIA_LOCALE.bat`, or run it from a terminal:

```powershell
.\AVVIA_LOCALE.bat
```

The launcher stays in the repository root, requires Python 3.13, creates or
reuses `.venv`, and installs `requirements.txt` only inside that environment.
It rejects an existing `.venv` created with another Python version.

To skip the menu:

```powershell
.\AVVIA_LOCALE.bat --mode normal
.\AVVIA_LOCALE.bat --mode naruto
```

Camera and output settings can be changed from the command line:

```powershell
.\AVVIA_LOCALE.bat --camera 1 --width 1280 --height 720 --fps 30
```

Use `--gesture-debug` to print recognition diagnostics in the terminal without
adding text to the video.

## Modes

### Normal Vanish

Raise your index and middle fingers in a V sign. The recognized gesture starts
a dissolve effect lasting approximately 3.6 seconds.

### Naruto Vanish

Bring both palms together in front of the webcam with fingers side by side.
The effect replaces the detected person with smoke and a wooden log.
`assets/vanish.MP3` plays through the local audio output. Press `R` before
triggering the effect again.

For either mode, step out of the camera frame during the initial four-second
background capture.

## Controls

- `SPACE`: capture a new background.
- `R`: make the person reappear.
- `V`: trigger the selected effect manually.
- `F`: toggle fullscreen.
- `Q` or `ESC`: quit and release camera resources.

## Virtual camera and OBS

VanishCam automatically attempts to use an available virtual-camera backend.
Use `AVVIA_VIRTUAL.bat` to require virtual-camera output:

```powershell
.\AVVIA_VIRTUAL.bat
.\AVVIA_VIRTUAL.bat --virtual-backend unitycapture
```

Use `AVVIA_OBS.bat` to disable direct virtual-camera output and capture the
preview window in OBS instead. OBS Virtual Camera must not already be active
when VanishCam is using it as its output device.

## Offline self-test

The self-test verifies model hashes, model initialization, image assets and
audio decoding without opening the webcam:

```powershell
.\.venv\Scripts\python.exe vanish_cam.py --self-test
```

## Windows build

After dependencies and models have been prepared, run:

```powershell
.\BUILD_WINDOWS.bat
```

The build script:

- requires Python 3.13 and uses only `.venv`;
- installs pinned runtime dependencies and PyInstaller 6.22.3 inside `.venv`;
- runs `prepare_models.py --verify-only` and never downloads models;
- builds `dist\VanishCam.exe` from `VanishCam.spec`;
- runs the executable's offline self-test after building.

If verification fails, prepare the models explicitly before retrying the
build.

## Security and privacy scope

- Webcam frames and generated images are processed locally by project code.
- Project code does not upload, record or send webcam frames to a server.
- Model assets are loaded from verified local files.
- Normal application runtime performs no project-defined model downloads.
- `prepare_models.py` performs the explicit, user-initiated model downloads.
- MediaPipe and the other Python packages are third-party dependencies. The
  installed MediaPipe wheel contains internal networking and telemetry-capable
  components that are not configurable through its supported Python API.
- This fork does not patch MediaPipe DLLs or claim to disable unsupported
  MediaPipe internals. It therefore does not claim to be completely free of
  third-party telemetry.

## Assets

`assets/substitution_log.png` is an original transparent-background asset.
Smoke is rendered procedurally by `naruto_effect.py`, allowing it to follow the
detected person without additional downloaded artwork.
