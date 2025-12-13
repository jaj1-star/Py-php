#!/usr/bin/env python3
import sys
import os
import subprocess
import threading
import time
import shutil

DOWNLOAD_PATH = "./downloads"
REQUIRED_PACKAGES = ["yt-dlp"]

# ألوان
G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
C = "\033[96m"
W = "\033[0m"

loading = True

def clean_downloads():
    if os.path.exists(DOWNLOAD_PATH):
        shutil.rmtree(DOWNLOAD_PATH)
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)
    print(f"{Y}🧹 Upload folder cleaned up{W}")

def spinner():
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    i = 0
    while loading:
        print(f"\r{C}{frames[i % len(frames)]} Loading...{W}", end="")
        i += 1
        time.sleep(0.1)

def install_packages():
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            print(f"{Y}📦 تثبيت {pkg} ...{W}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

def progress_hook(d):
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "")
        eta = d.get("_eta_str", "")
        print(f"\r{G}⬇️ {percent} | ⚡ {speed} | ⏱ {eta}{W}", end="")

    elif d["status"] == "finished":
        print(f"\n{C}🔧 Audio and video are being merged..{W}")

def main():
    if len(sys.argv) < 2:
        print(f"{R}❌ استخدم:{W} python3 in.py <URL>")
        sys.exit(1)

    url = sys.argv[1].strip()

    install_packages()
    clean_downloads()

    import yt_dlp

    global loading
    spinner_thread = threading.Thread(target=spinner)
    spinner_thread.start()

    ydl_opts = {
        "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "progress_hooks": [progress_hook],
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        loading = False
        spinner_thread.join()

        print(f"\n{G}✅ Successfully uploaded{W}")
        print(f"{C}📁 Folder: {DOWNLOAD_PATH}{W}")

    except Exception as e:
        loading = False
        spinner_thread.join()
        print(f"\n{R}❌ Loading Failed : {W}")
        print(e)

if __name__ == "__main__":
    main()
