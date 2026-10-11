"""Enable per-monitor DPI awareness before creating windows or capturing pixels.

The overlay and ImageGrab use physical desktop pixels. This avoids Windows bitmap
virtualization shifting/scaling capture and overlay coordinates at 125%, 150%, etc.
"""
import ctypes
import os

_DPI_SET = False

def enable_dpi_awareness() -> bool:
    """Best-effort Per-Monitor-V2 awareness; safe to call more than once."""
    global _DPI_SET
    if _DPI_SET or os.name != "nt":
        return _DPI_SET
    user32 = ctypes.windll.user32
    # Windows 10 1703+: DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = (HANDLE)-4
    try:
        fn = user32.SetProcessDpiAwarenessContext
        fn.argtypes = [ctypes.c_void_p]
        fn.restype = ctypes.c_bool
        if fn(ctypes.c_void_p(-4)):
            _DPI_SET = True
            return True
    except (AttributeError, OSError):
        pass
    # Windows 8.1+: PROCESS_PER_MONITOR_DPI_AWARE = 2
    try:
        shcore = ctypes.windll.shcore
        fn = shcore.SetProcessDpiAwareness
        fn.argtypes = [ctypes.c_int]
        fn.restype = ctypes.c_long
        hr = fn(2)
        if hr == 0 or hr == 0x80070005:  # S_OK or E_ACCESSDENIED (already set)
            _DPI_SET = True
            return True
    except (AttributeError, OSError):
        pass
    # Vista+: system-DPI aware fallback (less robust for mixed-DPI monitors).
    try:
        if user32.SetProcessDPIAware():
            _DPI_SET = True
            return True
    except (AttributeError, OSError):
        pass
    return _DPI_SET

# Run on import, before Tkinter/Pillow creates a window or reads the screen.
DPI_AWARE = enable_dpi_awareness()
