# Source-level security review (DPI-aware rebuild)

Reviewed source files: `app.py`, `vision.py`, `solver.py`, `calibrate.py`, `dpi_awareness.py`, `build.bat`, and `requirements.txt`.

- `dpi_awareness.py`: attempts Windows per-monitor DPI awareness setup; no networking, persistence, or input injection.
- `vision.py`: captures the configured screen rectangle and computes local image features.
- `solver.py`: performs local board simulations and scoring.
- `app.py`: displays the UI/overlay, reads/writes `config.json`, and checks hotkey state. It does not synthesize input.
- `calibrate.py`: edits local board geometry in `config.json`.
- `build.bat`: creates a virtual environment, downloads declared Python build dependencies via pip, and runs PyInstaller.

This is a source review, not a guarantee that a separately obtained EXE is safe. For the strongest practical assurance, build locally from this source and scan the resulting EXE with Windows Security.
