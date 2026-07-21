"""
setup_task.py
--------------
Registers the daily Task Scheduler job that runs apod_wallpaper.exe.
This is compiled into setup_task.exe by setup.py (cx_Freeze) and lives
next to apod_wallpaper.exe in the install directory. The MSI creates a
Start Menu shortcut to it; the user runs it once after installing
(or the .msi's Start Menu entry can be launched automatically by
checking "Launch APOD Wallpaper Setup" if you add that UI, see README).

Run manually any time to (re)create the task, e.g. if it gets deleted.
"""

import subprocess
import sys
from pathlib import Path

TASK_NAME = "APOD Daily Wallpaper"


def main():
    exe_dir = Path(sys.argv[0]).resolve().parent
    target_exe = exe_dir / "apod_wallpaper.exe"

    if not target_exe.exists():
        print(f"ERROR: could not find {target_exe}")
        input("Press Enter to exit...")
        return 1

    # Remove any existing task with the same name first (idempotent re-run).
    subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
        capture_output=True,
    )

    # Daily trigger at 8:00 AM, current user, no elevated privileges needed.
    result = subprocess.run(
        [
            "schtasks", "/Create",
            "/TN", TASK_NAME,
            "/TR", f'"{target_exe}"',
            "/SC", "DAILY",
            "/ST", "08:00",
            "/RL", "LIMITED",
            "/F",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(f"Success: '{TASK_NAME}' scheduled to run daily at 8:00 AM.")
        print("Running it once now to set today's wallpaper...")
        subprocess.run([str(target_exe)])
        print("Done! Your wallpaper has been updated.")
    else:
        print("Failed to create scheduled task:")
        print(result.stdout)
        print(result.stderr)

    input("Press Enter to close...")
    return 0 if result.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
