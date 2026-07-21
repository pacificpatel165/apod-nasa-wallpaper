# APOD Wallpaper

Automatically downloads NASA's [Astronomy Picture of the Day](https://apod.nasa.gov/apod/astropix.html)
and sets it as your Windows 11 desktop wallpaper, once a day.

## "Today's Astronomy Picture" info shortcut

A desktop shortcut named **"Today's Astronomy Picture"** shows the current
image's title, date, credit, and full NASA description, plus two buttons:

- **Open on NASA website** — opens the real APOD page for that image
  (e.g. `https://apod.nasa.gov/apod/ap260721.html`) in your default browser.
- **Open full-size image** — opens the downloaded image file directly.

It reads from `%LOCALAPPDATA%\APODWallpaper\state.json`, which gets updated
every time the wallpaper changes, so it always reflects the current wallpaper.

- **Option A install**: the shortcut is created automatically on your Desktop
  by `install_task.ps1`.
- **Option B (MSI) install**: the shortcut is created automatically on your
  Desktop as part of installing the MSI — no extra step needed for this one.

## How it works

- `apod_wallpaper.py` calls NASA's official APOD JSON API (the same data
  that powers the page you linked), downloads that day's image to
  `%LOCALAPPDATA%\APODWallpaper\images\`, and sets it as your wallpaper
  using the Windows API.
- If a given day's APOD is a video instead of an image, it automatically
  falls back to the most recent day that *is* an image.
- Old cached images older than 14 days are auto-deleted (configurable).
- A Windows Task Scheduler entry runs it once daily (8:00 AM) and once at
  every logon, so it stays current even if the laptop was off/asleep at
  8 AM.
- Nothing is admin-only — everything installs and runs per-user.

## Get a free NASA API key (recommended, takes 30 seconds)

The script works out of the box with NASA's shared `DEMO_KEY`, but that
key is rate-limited across *everyone* using it (~30 requests/hour,
~50/day) so it can occasionally fail. Get your own free key:

1. Go to https://api.nasa.gov
2. Fill in the form — you get the key instantly by email, no approval wait.
3. After first running the app once, edit
   `%LOCALAPPDATA%\APODWallpaper\config.json` and replace `"DEMO_KEY"`
   with your key.

## Option A — Quick install (recommended, no build step)

Requires Python 3.9+ to already be on the machine
(https://www.python.org/downloads/ — check "Add python.exe to PATH"
during install). This is the easiest path and what most people should use.

1. Copy this whole folder to the target machine.
2. Right-click `install_task.ps1` → **Run with PowerShell**
   (or open PowerShell in this folder and run:
   `powershell -ExecutionPolicy Bypass -File install_task.ps1`)
3. That's it. It registers the daily task and sets today's wallpaper
   immediately so you see it working.

To remove it later: run `uninstall_task.ps1` the same way.

## Option B — Build a real .msi installer (no Python needed by end users)

This produces a standalone `.msi` that anyone can double-click to install
— it bundles its own Python runtime, so end users don't need Python
installed at all. **The build step itself must be done on a Windows
machine** (Windows Installer packages can't be built from Linux/Mac);
if you don't have a Windows box handy, a free GitHub Actions
`windows-latest` runner works fine too.

1. On a Windows machine, install Python 3.10+.
2. Copy this folder there.
3. Double-click `build_msi.bat` (or run `pip install cx_Freeze` then
   `python setup.py bdist_msi`).
4. Find the installer in the `dist\` folder, e.g.
   `APODWallpaper-1.0.0-win64.msi`.
5. Distribute that `.msi` — anyone can double-click it to install to
   `Program Files\APODWallpaper`.
6. After installing, the user runs the **"setup_task"** shortcut created
   in the Start Menu once — this registers the daily scheduled task and
   sets the wallpaper immediately. (MSI custom actions that auto-run
   post-install reliably require the WiX toolset rather than cx_Freeze;
   this one extra click keeps the build simple and dependable. Say the
   word if you'd like the more involved WiX version that skips even
   that click.)

## Configuration

Edit `%LOCALAPPDATA%\APODWallpaper\config.json` (created on first run):

```json
{
  "api_key": "DEMO_KEY",
  "prefer_hd": true,
  "keep_days": 14,
  "wallpaper_style": "fill"
}
```

- `wallpaper_style`: `fill` | `fit` | `stretch` | `tile` | `center` | `span`
- `prefer_hd`: use the high-resolution image when NASA provides one
  (larger download, sharper on big/4K screens)
- `keep_days`: how many days of old wallpapers to keep cached locally

## Logs & troubleshooting

- Log file: `%LOCALAPPDATA%\APODWallpaper\apod_wallpaper.log`
- To run it manually and watch output:
  `python "%LOCALAPPDATA%\APODWallpaper\apod_wallpaper.py"`
- To check/edit the scheduled task: open **Task Scheduler** →
  look for **"APOD Daily Wallpaper"**.
- Common cause of failure: no internet at the scheduled time — the
  logon trigger covers most of these cases, or just wait for the next
  day's run.

## Files in this package

| File | Purpose |
|---|---|
| `apod_wallpaper.py` | Core logic: fetch APOD, download image, set wallpaper |
| `apod_info.py` | Desktop info window: shows today's title/description, links to NASA page |
| `install_task.ps1` | Quick installer (Option A) |
| `uninstall_task.ps1` | Removes the scheduled task / files |
| `setup.py` | cx_Freeze build script → produces the .msi (Option B) |
| `setup_task.py` | Compiled into `setup_task.exe`; registers the task post-install |
| `build_msi.bat` | One-click MSI build wrapper for Option B |

---

![msi_build_and_runtime_flow](msi_build_and_runtime_flow.png)
## Two completely separate phases

**Build phase** (happens once, on a Windows dev machine, by you): turns Python source into a distributable installer.

**Install + runtime phase** (happens on any user's machine, including yours): what that installer actually does once double-clicked, and what runs automatically afterward.

## What each file does

| File | Phase | Purpose |
|---|---|---|
| `apod_wallpaper.py` | Runtime | The actual worker. Calls NASA's API, downloads the image, sets it as wallpaper, saves metadata to `state.json`. Compiled into `apod_wallpaper.exe`. |
| `apod_info.py` | Runtime | The info window. Reads `state.json`, shows title/description, opens the NASA page or image on click. Compiled into `apod_info.exe`. |
| `setup_task.py` | Runtime (one-time) | Registers the Task Scheduler job pointing at `apod_wallpaper.exe`, then runs it once immediately. Compiled into `setup_task.exe`. |
| `setup.py` | **Build** | The recipe cx_Freeze follows: which `.py` files to compile into `.exe`, what to name them, what shortcuts to create, where to install to. This is what you run `python setup.py bdist_msi` against. |
| `build_msi.bat` | Build | One-click wrapper: installs cx_Freeze, then runs `setup.py`. |
| `install_task.ps1` / `uninstall_task.ps1` | Alternate runtime path | The non-MSI installer (Option A) — same end result as the MSI, but via a script instead of a compiled installer. |

## Why `setup.py` exists — the actual build mechanics

cx_Freeze does two jobs when you run `python setup.py bdist_msi`:

1. **Freezes** each `.py` file into a standalone `.exe` — bundling a private copy of the Python interpreter plus every imported module (this is why we had to fix the `tkinter` exclusion earlier: whatever a script imports must be explicitly included or it's missing at runtime).
2. **Packages** those `.exe` files, using the Windows Installer APIs, into a single `.msi`, including instructions for where to copy files (`Program Files\APODWallpaper`) and which shortcuts to create (the `shortcut_table` in `setup.py` — that's the exact code that was originally missing, then broken, and is now fixed).

The output lands in `dist\APODWallpaper-1.0.0-win64.msi` — that one file is the entire deliverable; anyone can double-click it with no Python installed.

## What happens after someone double-clicks the .msi

Windows Installer reads the package and: copies the three `.exe` files to `Program Files\APODWallpaper`, creates the "Setup APOD Wallpaper" Start Menu shortcut and the "Today's Astronomy Picture" Desktop shortcut. Nothing runs automatically yet — that's why there's a manual "run this once" step (the cx_Freeze limitation we discussed; true zero-click would need WiX instead).

From there, the diagram's two branches are independent and permanent:
- **Automatic path**: Task Scheduler fires `apod_wallpaper.exe` daily at 8 AM and at every logon, silently.
- **Manual path**: whenever you click the desktop icon, `apod_info.exe` opens and shows whatever `apod_wallpaper.exe` most recently wrote to `state.json`.