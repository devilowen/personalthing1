# Security notes

The program is a local screen-capture and move-suggestion overlay. It does not automate mouse clicks or keyboard input, and does not intentionally contact a server at runtime, collect credentials, or install persistence.

`dpi_awareness.py` calls Windows DPI-awareness APIs only to establish process coordinate behavior. `vision.py` captures the configured screen rectangle and classifies pixels. `solver.py` calculates candidate moves in memory. `app.py` reads/writes `config.json` and polls hotkeys. `build.bat` installs the declared build dependencies through pip at build time and invokes PyInstaller.

Build the EXE yourself from the included source if you want to verify exactly what is packaged. Run it without Administrator privileges.
