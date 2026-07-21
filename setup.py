"""
Build script for producing a real Windows .msi installer.

This MUST be run on a Windows machine (cx_Freeze compiles a native
Windows executable + bootstraps an MSI via the Windows Installer APIs,
neither of which can be cross-compiled from Linux/Mac).

Usage (on Windows, with Python 3.10+ installed):

    pip install cx_Freeze
    python setup.py bdist_msi

Output MSI will appear in the "dist" folder.

The MSI does two things on install:
  1. Copies apod_wallpaper.exe (a bundled, no-Python-required build of
     apod_wallpaper.py) to Program Files.
  2. Registers a per-user daily Scheduled Task via a post-install script
     (setup_task.py, run automatically as a custom action).
"""

import sys
from cx_Freeze import setup, Executable
from cx_Freeze.executable import Executable as _ExeCheck

build_exe_options = {
    "packages": ["tkinter"],
    "excludes": ["test", "unittest"],
    "include_files": [],
}


def gui_base():
    """
    cx_Freeze renamed the "no console window" base at some point:
    old versions call it "Win32GUI", newer versions call it "gui".
    Try both so this script works regardless of installed version.
    """
    if sys.platform != "win32":
        return None
    for candidate in ("gui", "Win32GUI"):
        try:
            _ExeCheck("apod_wallpaper.py", base=candidate)
            return candidate
        except Exception:
            continue
    # Fall back to a visible console rather than failing the build.
    return None


base = gui_base()

executables = [
    Executable(
        "apod_wallpaper.py",
        base=base,
        target_name="apod_wallpaper.exe",
        icon=None,
    ),
    Executable(
        "setup_task.py",
        base=None,  # keep console so install-time errors are visible
        target_name="setup_task.exe",
    ),
    Executable(
        "apod_info.py",
        base=base,  # no console window for the info viewer
        target_name="apod_info.exe",
        icon=None,
    ),
]

# cx_Freeze's bdist_msi does not easily support "run this exe
# automatically after install" custom actions without hand-editing
# MSI tables (that needs WiX for a clean implementation). Simpler,
# reliable approach: install a Start Menu shortcut the user clicks
# once to finish setup (registers the daily Scheduled Task).
#
# MSI "Shortcut" table columns, in order:
#   Shortcut, Directory_, Name, Component_, Target,
#   Arguments, Description, Hotkey, Icon_, IconIndex, ShowCmd, WkDir
shortcut_table = [
    (
        "SetupTaskShortcut",              # Shortcut
        "ProgramMenuFolder",              # Directory_ (Start Menu)
        "Setup APOD Wallpaper",           # Name shown to the user
        "TARGETDIR",                      # Component_
        "[TARGETDIR]setup_task.exe",      # Target
        None,                              # Arguments
        "Registers the daily wallpaper task and sets today's wallpaper",  # Description
        None,                              # Hotkey
        None,                              # Icon_
        None,                              # IconIndex
        None,                              # ShowCmd
        "TARGETDIR",                       # WkDir
    ),
    (
        "InfoDesktopShortcut",            # Shortcut
        "DesktopFolder",                  # Directory_ (Desktop)
        "Today's Astronomy Picture",      # Name shown to the user
        "TARGETDIR",                      # Component_
        "[TARGETDIR]apod_info.exe",       # Target
        None,                              # Arguments
        "Shows today's NASA APOD title and description, with a link to the NASA page",  # Description
        None,                              # Hotkey
        None,                              # Icon_
        None,                              # IconIndex
        None,                              # ShowCmd
        "TARGETDIR",                       # WkDir
    ),
]

bdist_msi_options = {
    "add_to_path": False,
    "install_icon": None,
    "initial_target_dir": r"[ProgramFilesFolder]\APODWallpaper",
    "data": {"Shortcut": shortcut_table},
}

setup(
    name="APODWallpaper",
    version="1.0.0",
    description="Sets NASA's Astronomy Picture of the Day as your Windows wallpaper, daily.",
    options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
    executables=executables,
)
