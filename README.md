# BilgeOverlay — DPI-aware Windows build

This is a source project for a Puzzle Pirates Bilging move-suggestion overlay. It recommends moves only; it does not click or send input to the game.

## Run it without Python installed

The intended end-user deliverable is the **standalone `BilgeOverlay.exe`**. Python is needed only on the build machine, not on the Windows PC that runs the EXE. This source ZIP does not itself contain a compiled EXE.

### Build a standalone EXE without installing Python on your own PC

1. Create a GitHub repository and upload the contents of this folder, including the `.github/workflows/build-windows.yml` file.
2. Open the repository's **Actions** tab.
3. Select **Build standalone Windows EXE**, click **Run workflow**, then run it on the default branch.
4. When the run completes successfully, open the run and download the `BilgeOverlay-Windows` artifact.
5. Extract that artifact and double-click `BilgeOverlay.exe`. The target PC does not need Python installed.

GitHub Actions runs the build on a Windows runner and packages Python and required runtime dependencies into a single-file EXE. The build runner needs internet access to download dependencies.

### Build locally (optional)

If Python 3.11+ is installed, double-click `build.bat`. The output is `dist\BilgeOverlay.exe`. Python is not required to run that EXE.

## DPI/scaling behavior

- Enables **Per-Monitor DPI Awareness V2** at process startup, before Tkinter or Pillow initializes; falls back to older Windows DPI-awareness APIs where available.
- Screen capture uses an explicit rectangle in physical desktop pixels and validates the captured dimensions.
- Settings are stored in `%APPDATA%\BilgeOverlay\config.json`, so they persist across launches and are not written into PyInstaller's temporary extraction folder.
- Coordinates are physical screen pixels. If a display scaling, game resolution, game UI scale, or monitor arrangement change moves/resizes the board, use F10 to recalibrate the rectangle.

## Controls

- **F8**: pause/resume scanning
- **F9**: show/hide the guide
- **F10**: calibration/settings
- **Esc**: quit

## Board model limitations

The solver models a 6×12 grid, horizontal swaps, match clears, and heuristic special pieces. Recognition is image-based rather than a direct read of game state. Verify suggestions visually; this is a move advisor, not an automated player.

## Security notes

Runtime behavior is local-only: screen capture, image classification, in-memory move scoring, and local configuration. The application does not include a network client, credential collection, persistence mechanism, or automated mouse/keyboard input. The GitHub Actions build downloads Pillow and PyInstaller from pip during the build. Review the source and workflow before running or building it.
