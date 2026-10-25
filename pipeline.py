#!/usr/bin/env python3
"""
Autonomous Cloud Reel Pipeline Orchestrator.
Coordinates Video Editing (FFmpeg) -> AI Copywriting (Gemini) -> Social Media Publishing (Uplika).
Can run locally or in GitHub Actions / Cloud Cron.
"""

import os
import sys
import json
import random
import argparse
from datetime import datetime

# Local imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "scripts"))

from video_engine import render_smooth_reel
from gemini_copywriter import generate_caption
from uplika_uploader import publish_reel, poll_publish_status
from gdrive_downloader import download_file as gdrive_download

DEFAULT_VIDEO_DIR = "/home/001268796482_0/Videos/3000+ Anime reel bundle"
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "outputs")
HISTORY_FILE = os.path.join(SCRIPT_DIR, "publish_history.json")


def load_themes():
    themes_path = os.path.join(SCRIPT_DIR, "config", "themes.json")
    if not os.path.exists(themes_path):
        raise FileNotFoundError(f"Themes config missing: {themes_path}")
    with open(themes_path, "r", encoding="utf-8") as f:
        return json.load(f).get("themes", [])


def resolve_video_path(candidate_base_dirs, rel_dir, filename):
    cleaned_dir = rel_dir.replace("Digiproducthub.in ", "").replace("(", "").replace(")", "").strip()
    subpaths = [
        rel_dir,
        cleaned_dir,
        os.path.join("clips", rel_dir),
        os.path.join("clips", cleaned_dir),
        ""
    ]
    for base in candidate_base_dirs:
        for sub in subpaths:
            full = os.path.normpath(os.path.join(base, sub, filename) if sub else os.path.join(base, filename))
            if os.path.exists(full):
                return full
    return None


def main():
    parser = argparse.ArgumentParser(description="Autonomous Anime Reel Cloud Pipeline")
    parser.add_argument("--theme", type=str, default="random", help="Theme ID to render or 'random'")
    parser.add_argument("--dry-run", action="store_true", help="Render video & caption without uploading to Instagram")
    parser.add_argument("--video-dir", type=str, default="", help="Custom root directory for video bundle")
    parser.add_argument("--output", type=str, default="", help="Custom output MP4 path")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    themes = load_themes()
    if not themes:
        print("[!] No themes defined in themes.json", file=sys.stderr)
        sys.exit(1)

    # 1. Select Theme
    if args.theme == "random":
        chosen_theme = random.choice(themes)
    else:
        matched = [t for t in themes if t.get("id") == args.theme]
        chosen_theme = matched[0] if matched else random.choice(themes)

    print("=" * 60)
    print(f"🎬 SELECTED THEME: {chosen_theme['name']} ({chosen_theme['id']})")
    print(f"⚡ CHARACTERS: {', '.join(chosen_theme.get('characters', []))}")
    print("=" * 60)

    # 2. Locate Source Videos
    candidate_dirs = [
        args.video_dir,
        os.environ.get("VIDEO_BUNDLE_ROOT", ""),
        DEFAULT_VIDEO_DIR,
        os.path.join(SCRIPT_DIR, "clips"),
        "/tmp/clips"
    ]
    candidate_dirs = [d for d in candidate_dirs if d and os.path.exists(d)]

    segments_to_render = []
    for seg in chosen_theme.get("relative_segments", []):
        filename = seg.get("file", "")
        vpath = resolve_video_path(candidate_dirs, seg.get("dir", ""), filename)
        if not vpath:
            print(f"[*] Clip '{filename}' not found locally; streaming from Google Drive...")
            vpath = gdrive_download(filename, destination_dir="/tmp/clips", rel_dir=seg.get("dir", ""))

        if not vpath or not os.path.exists(vpath):
            print(f"[!] Source video not found for {filename}; searched in {candidate_dirs} and Google Drive", file=sys.stderr)
            sys.exit(1)
        segments_to_render.append((vpath, seg.get("start", 0.0), seg.get("duration", 3.0)))

    # 3. Render High-Retention Reel
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = args.output or os.path.join(OUTPUT_DIR, f"reel_{chosen_theme['id']}_{timestamp_str}.mp4")

    print(f"[*] Rendering vertical reel to: {out_file}")
    render_smooth_reel(
        segments=segments_to_render,
        output_path=out_file,
        hook_title=chosen_theme.get("hook_title", "HONORED ONE vs KING OF CURSES"),
        hook_subtitle=chosen_theme.get("hook_subtitle", "WHO HAS MORE AURA?"),
        watermark="@dragon.studios.india"
    )

    # 4. Generate AI Caption & Tags
    print("\n[*] Generating high-engagement viral caption...")
    caption = generate_caption(
        theme_name=chosen_theme.get("name"),
        characters=chosen_theme.get("characters")
    )
    print("\n" + "-" * 50)
    print(caption)
    print("-" * 50 + "\n")

    # 5. Instagram Publishing via Uplika
    publish_result = None
    permalink = None
    if args.dry_run:
        print("[!] DRY-RUN ENABLED: Skipping Instagram upload.")
    else:
        print("[*] Uploading & Publishing Reel to Instagram via Uplika API...")
        publish_result = publish_reel(out_file, caption)
        if publish_result:
            post_id = publish_result.get("id")
            permalink = poll_publish_status(post_id=post_id, timeout_seconds=120, interval=5)
            if permalink:
                print("\n" + "=" * 60)
                print(f"🎉 REEL IS LIVE ON INSTAGRAM: {permalink}")
                print("=" * 60 + "\n")

    # 6. Record to History
    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "theme_id": chosen_theme["id"],
        "video_file": out_file,
        "caption": caption,
        "dry_run": args.dry_run,
        "permalink": permalink,
        "publish_response": publish_result
    }

    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    history.append(history_entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    print(f"[✓] Automation cycle completed successfully! History logged to {HISTORY_FILE}")


if __name__ == "__main__":
    main()
