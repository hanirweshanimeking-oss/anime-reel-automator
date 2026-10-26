#!/usr/bin/env python3
"""
Autonomous Cloud Reel Pipeline Orchestrator.
Coordinates video editing (FFmpeg), AI copywriting (Gemini), and Uplika publishing.
"""

import os
import sys
import json
import random
import argparse
from datetime import datetime

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
    with open(themes_path, "r", encoding="utf-8") as file:
        return json.load(file).get("themes", [])


def resolve_video_path(candidate_base_dirs, rel_dir, filename):
    cleaned_dir = rel_dir.replace("Digiproducthub.in ", "").replace("(", "").replace(")", "").strip()
    subpaths = [
        rel_dir,
        cleaned_dir,
        os.path.join("clips", rel_dir),
        os.path.join("clips", cleaned_dir),
        "",
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
    parser.add_argument("--dry-run", action="store_true", help="Render video and caption without uploading")
    parser.add_argument("--video-dir", type=str, default="", help="Custom root directory for video bundle")
    parser.add_argument("--output", type=str, default="", help="Custom output MP4 path")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    themes = load_themes()
    if not themes:
        print("[!] No themes defined in themes.json", file=sys.stderr)
        sys.exit(1)

    if args.theme == "random":
        chosen_theme = random.choice(themes)
    else:
        matched = [theme for theme in themes if theme.get("id") == args.theme]
        if not matched:
            print(f"[!] Unknown theme '{args.theme}'. Choose 'random' or a theme ID from config/themes.json.", file=sys.stderr)
            sys.exit(2)
        chosen_theme = matched[0]

    print("=" * 60)
    print(f"SELECTED THEME: {chosen_theme['name']} ({chosen_theme['id']})")
    print(f"CHARACTERS: {', '.join(chosen_theme.get('characters', []))}")
    print("=" * 60)

    candidate_dirs = [
        args.video_dir,
        os.environ.get("VIDEO_BUNDLE_ROOT", ""),
        DEFAULT_VIDEO_DIR,
        os.path.join(SCRIPT_DIR, "clips"),
        "/tmp/clips",
    ]
    candidate_dirs = [directory for directory in candidate_dirs if directory and os.path.exists(directory)]

    segments_to_render = []
    for segment in chosen_theme.get("relative_segments", []):
        filename = segment.get("file", "")
        video_path = resolve_video_path(candidate_dirs, segment.get("dir", ""), filename)
        if not video_path:
            print(f"[*] Clip '{filename}' not found locally; downloading from Google Drive...")
            video_path = gdrive_download(
                filename,
                destination_dir="/tmp/clips",
                rel_dir=segment.get("dir", ""),
            )

        if not video_path or not os.path.exists(video_path):
            print(f"[!] Source video not found for {filename}; searched local paths and Google Drive.", file=sys.stderr)
            sys.exit(1)
        segments_to_render.append((
            video_path,
            segment.get("start", 0.0),
            segment.get("duration", 3.0),
        ))

    if not segments_to_render:
        print("[!] Selected theme contains no video segments.", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = args.output or os.path.join(OUTPUT_DIR, f"reel_{chosen_theme['id']}_{timestamp}.mp4")

    print(f"[*] Rendering vertical Reel to: {output_file}")
    render_smooth_reel(
        segments=segments_to_render,
        output_path=output_file,
        hook_title=chosen_theme.get("hook_title", "HONORED ONE vs KING OF CURSES"),
        hook_subtitle=chosen_theme.get("hook_subtitle", "WHO HAS MORE AURA?"),
        watermark="@dragon.studios.india",
    )

    if not os.path.isfile(output_file) or os.path.getsize(output_file) <= 0:
        print("[!] Render did not produce a valid MP4 file.", file=sys.stderr)
        sys.exit(1)

    print("\n[*] Generating caption...")
    caption = generate_caption(
        theme_name=chosen_theme.get("name"),
        characters=chosen_theme.get("characters"),
    )
    print("\n" + "-" * 50)
    print(caption)
    print("-" * 50 + "\n")

    publish_result = None
    permalink = None
    if args.dry_run:
        print("[!] DRY-RUN ENABLED: skipping Instagram upload.")
    else:
        print("[*] Uploading and publishing Reel via Uplika...")
        publish_result = publish_reel(output_file, caption)
        if not publish_result:
            print("[!] Publish request failed. Marking this workflow run as failed.", file=sys.stderr)
            sys.exit(1)

        post_id = publish_result.get("id") if isinstance(publish_result, dict) else None
        permalink = (
            publish_result.get("permalink")
            or publish_result.get("url")
            or publish_result.get("link")
        ) if isinstance(publish_result, dict) else None

        if not permalink:
            permalink = poll_publish_status(post_id=post_id, timeout_seconds=120, interval=5)

        if permalink:
            print("\n" + "=" * 60)
            print(f"REEL LIVE URL: {permalink}")
            print("=" * 60 + "\n")
        else:
            print(
                "[!] Uplika did not provide a confirmed public permalink. "
                "Check Uplika and Instagram before manually retrying to avoid duplicate posts.",
                file=sys.stderr,
            )
            sys.exit(1)

    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "theme_id": chosen_theme["id"],
        "video_file": output_file,
        "caption": caption,
        "dry_run": args.dry_run,
        "permalink": permalink,
        "publish_response": publish_result,
    }

    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as file:
                history = json.load(file)
        except (OSError, json.JSONDecodeError):
            history = []
    history.append(history_entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=2)

    print(f"[✓] Automation cycle completed. History logged to {HISTORY_FILE}")


if __name__ == "__main__":
    main()
