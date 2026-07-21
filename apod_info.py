"""
apod_info.py
-------------
Small desktop utility: shows the title, date, and description of the
currently-set wallpaper (today's NASA APOD), plus a button to open the
actual NASA APOD page for that image in the default web browser.

Reads %LOCALAPPDATA%\\APODWallpaper\\state.json, which apod_wallpaper.py
updates every time it sets a new wallpaper.

Meant to be launched from a Desktop / Start Menu shortcut (see
install_task.ps1 / setup.py). Double-click to open.
"""

import json
import os
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import font as tkfont

APP_NAME = "APODWallpaper"
APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / APP_NAME
STATE_FILE = APP_DATA_DIR / "state.json"

FALLBACK_URL = "https://apod.nasa.gov/apod/astropix.html"


def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def main():
    state = load_state()

    title = state.get("last_title") or "No wallpaper set yet"
    apod_date = state.get("last_apod_date") or ""
    explanation = state.get("last_explanation") or (
        "Run the wallpaper update at least once to see details here."
    )
    credit = state.get("last_copyright")
    page_url = state.get("last_page_url") or FALLBACK_URL
    image_path = state.get("last_image")

    root = tk.Tk()
    root.title("Today's Astronomy Picture")
    root.configure(bg="#0b0e14")
    root.geometry("560x460")
    root.minsize(420, 360)

    title_font = tkfont.Font(family="Segoe UI", size=16, weight="bold")
    meta_font = tkfont.Font(family="Segoe UI", size=9)
    body_font = tkfont.Font(family="Segoe UI", size=10)
    btn_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")

    FG = "#e8ecf1"
    MUTED = "#9aa4b2"
    ACCENT = "#3a86ff"

    pad = tk.Frame(root, bg="#0b0e14")
    pad.pack(fill="both", expand=True, padx=20, pady=18)

    tk.Label(pad, text=title, font=title_font, fg=FG, bg="#0b0e14",
              wraplength=520, justify="left", anchor="w").pack(fill="x")

    meta_text = apod_date
    if credit:
        meta_text += f"   \u00b7   Image: {credit}"
    tk.Label(pad, text=meta_text, font=meta_font, fg=MUTED, bg="#0b0e14",
              anchor="w").pack(fill="x", pady=(4, 12))

    text_frame = tk.Frame(pad, bg="#0b0e14")
    text_frame.pack(fill="both", expand=True)

    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")

    body = tk.Text(
        text_frame, wrap="word", bg="#131720", fg=FG, font=body_font,
        relief="flat", padx=12, pady=12, yscrollcommand=scrollbar.set,
        highlightthickness=0, borderwidth=0,
    )
    body.insert("1.0", explanation)
    body.config(state="disabled")
    body.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=body.yview)

    btn_row = tk.Frame(pad, bg="#0b0e14")
    btn_row.pack(fill="x", pady=(16, 0))

    def open_nasa_page():
        webbrowser.open(page_url)

    def open_local_image():
        if image_path and Path(image_path).exists():
            os.startfile(image_path)

    nasa_btn = tk.Button(
        btn_row, text="Open on NASA website", font=btn_font,
        bg=ACCENT, fg="white", activebackground="#2c6fd6", activeforeground="white",
        relief="flat", padx=14, pady=8, cursor="hand2", command=open_nasa_page,
    )
    nasa_btn.pack(side="left")

    if image_path and Path(image_path).exists():
        img_btn = tk.Button(
            btn_row, text="Open full-size image", font=btn_font,
            bg="#232838", fg=FG, activebackground="#2c3245", activeforeground=FG,
            relief="flat", padx=14, pady=8, cursor="hand2", command=open_local_image,
        )
        img_btn.pack(side="left", padx=(10, 0))

    close_btn = tk.Button(
        btn_row, text="Close", font=btn_font,
        bg="#0b0e14", fg=MUTED, activebackground="#0b0e14", activeforeground=FG,
        relief="flat", padx=14, pady=8, cursor="hand2", command=root.destroy,
    )
    close_btn.pack(side="right")

    root.mainloop()


if __name__ == "__main__":
    main()
