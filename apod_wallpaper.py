"""
APOD Wallpaper Setter
======================
Fetches NASA's Astronomy Picture of the Day (APOD) and sets it as the
Windows desktop wallpaper. Designed to be run once a day via Windows
Task Scheduler (see install_task.ps1).

Author: generated for user
"""

import ctypes
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

APP_NAME = "APODWallpaper"

# Where we store downloaded images, logs, and state.
APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / APP_NAME
IMAGE_DIR = APP_DATA_DIR / "images"
LOG_FILE = APP_DATA_DIR / "apod_wallpaper.log"
STATE_FILE = APP_DATA_DIR / "state.json"
CONFIG_FILE = APP_DATA_DIR / "config.json"

# NASA APOD API. Get a free key (instant, no approval wait) at
# https://api.nasa.gov -- DEMO_KEY works too but is rate-limited to
# ~30 requests/hour/IP and ~50/day, which is fine for a once-a-day job
# but you should still get your own key if you can.
NASA_APOD_API = "https://api.nasa.gov/planetary/apod"
DEFAULT_API_KEY = "DEMO_KEY"

# How many days back to try if today's APOD is a video / unavailable.
FALLBACK_DAYS = 5

# Prefer the high-definition image when available.
PREFER_HD = True

# How many days of old images to keep on disk.
KEEP_DAYS = 14

DEFAULT_CONFIG = {
    "api_key": DEFAULT_API_KEY,
    "prefer_hd": PREFER_HD,
    "keep_days": KEEP_DAYS,
    "wallpaper_style": "fill",  # fill | fit | stretch | tile | center | span
}

SPI_SETDESKWALLPAPER = 20
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE = 0x02

# --------------------------------------------------------------------------
# Setup
# --------------------------------------------------------------------------


def ensure_dirs():
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging():
    ensure_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_config():
    ensure_dirs()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            merged = dict(DEFAULT_CONFIG)
            merged.update(cfg)
            return merged
        except Exception:
            logging.warning("Could not parse config.json, using defaults.")
    else:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
    return dict(DEFAULT_CONFIG)


def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# --------------------------------------------------------------------------
# NASA APOD fetching
# --------------------------------------------------------------------------


def fetch_apod_metadata(api_key, target_date=None, retries=3, timeout=15):
    """Fetch APOD JSON metadata for a given date (default: today)."""
    params = f"?api_key={api_key}"
    if target_date:
        params += f"&date={target_date.isoformat()}"

    url = NASA_APOD_API + params
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "APODWallpaper/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code == 429:
                logging.warning("Rate limited by NASA API, retry %s/%s...", attempt, retries)
                time.sleep(5 * attempt)
                continue
            logging.warning("HTTP error fetching APOD metadata: %s", e)
            break
        except Exception as e:
            last_err = e
            logging.warning("Error fetching APOD metadata (attempt %s/%s): %s", attempt, retries, e)
            time.sleep(3 * attempt)
    raise RuntimeError(f"Failed to fetch APOD metadata: {last_err}")


def find_usable_apod(api_key, days_back=FALLBACK_DAYS):
    """
    Try today's APOD; if it's a video (no static image) or fails,
    walk backwards day by day up to `days_back` times.
    """
    d = date.today()
    for i in range(days_back + 1):
        try:
            meta = fetch_apod_metadata(api_key, target_date=d if i > 0 else None)
        except RuntimeError as e:
            logging.warning("Could not fetch APOD for %s: %s", d, e)
            d -= timedelta(days=1)
            continue

        if meta.get("media_type") == "image":
            return meta
        else:
            logging.info(
                "APOD for %s is media_type=%s (not a static image), trying previous day.",
                meta.get("date", d), meta.get("media_type"),
            )
            d = date.today() - timedelta(days=i + 1)

    raise RuntimeError(f"No usable APOD image found in the last {days_back} days.")


def download_image(meta, prefer_hd=True):
    image_url = meta.get("hdurl") if prefer_hd and meta.get("hdurl") else meta.get("url")
    if not image_url:
        raise RuntimeError("APOD metadata contained no image URL.")

    ext = Path(image_url.split("?")[0]).suffix or ".jpg"
    if ext.lower() not in (".jpg", ".jpeg", ".png", ".bmp"):
        ext = ".jpg"

    apod_date = meta.get("date", date.today().isoformat())
    dest = IMAGE_DIR / f"apod_{apod_date}{ext}"

    if dest.exists() and dest.stat().st_size > 0:
        logging.info("Image for %s already downloaded, reusing %s", apod_date, dest)
        return dest

    logging.info("Downloading APOD image (%s): %s", apod_date, image_url)
    req = urllib.request.Request(image_url, headers={"User-Agent": "APODWallpaper/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
        f.write(resp.read())

    if dest.stat().st_size == 0:
        dest.unlink(missing_ok=True)
        raise RuntimeError("Downloaded image was empty.")

    return dest


def cleanup_old_images(keep_days):
    cutoff = datetime.now().timestamp() - keep_days * 86400
    for f in IMAGE_DIR.glob("apod_*"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
                logging.info("Removed old cached image: %s", f.name)
        except Exception as e:
            logging.warning("Could not remove old image %s: %s", f, e)


# --------------------------------------------------------------------------
# Windows wallpaper setting
# --------------------------------------------------------------------------

WALLPAPER_STYLE_MAP = {
    # (WallpaperStyle, TileWallpaper) registry values
    "fill": ("10", "0"),
    "fit": ("6", "0"),
    "stretch": ("2", "0"),
    "tile": ("0", "1"),
    "center": ("0", "0"),
    "span": ("22", "0"),
}


def set_wallpaper_style(style):
    if os.name != "nt":
        return
    import winreg  # only available on Windows

    style_val, tile_val = WALLPAPER_STYLE_MAP.get(style, WALLPAPER_STYLE_MAP["fill"])
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Control Panel\\Desktop", 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, style_val)
    winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, tile_val)
    winreg.CloseKey(key)


def set_wallpaper(image_path: Path, style="fill"):
    if os.name != "nt":
        logging.info("[non-Windows OS detected] Would set wallpaper to: %s", image_path)
        return

    set_wallpaper_style(style)

    # SystemParametersInfoW requires an absolute path with backslashes.
    abs_path = str(image_path.resolve())
    result = ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, abs_path, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
    )
    if not result:
        raise RuntimeError("SystemParametersInfoW failed to set wallpaper.")
    logging.info("Wallpaper set to: %s", abs_path)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main():
    setup_logging()
    cfg = load_config()
    state = load_state()

    today_str = date.today().isoformat()
    if state.get("last_success_date") == today_str:
        logging.info("Wallpaper already updated today (%s). Nothing to do.", today_str)
        return 0

    try:
        meta = find_usable_apod(cfg["api_key"])
        image_path = download_image(meta, prefer_hd=cfg.get("prefer_hd", True))
        set_wallpaper(image_path, style=cfg.get("wallpaper_style", "fill"))
        cleanup_old_images(cfg.get("keep_days", KEEP_DAYS))

        apod_date = meta.get("date", today_str)
        # NASA's page URL uses YYMMDD e.g. 2026-07-21 -> ap260721.html
        try:
            y, m, d = apod_date.split("-")
            page_url = f"https://apod.nasa.gov/apod/ap{y[2:]}{m}{d}.html"
        except Exception:
            page_url = "https://apod.nasa.gov/apod/astropix.html"

        state["last_success_date"] = today_str
        state["last_image"] = str(image_path)
        state["last_title"] = meta.get("title", "")
        state["last_apod_date"] = apod_date
        state["last_explanation"] = meta.get("explanation", "")
        state["last_copyright"] = meta.get("copyright", "").strip()
        state["last_page_url"] = page_url
        save_state(state)

        logging.info("Done. Today's wallpaper: '%s' (%s)", meta.get("title"), meta.get("date"))
        return 0
    except Exception as e:
        logging.error("Failed to update wallpaper: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
