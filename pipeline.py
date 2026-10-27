#!/usr/bin/env python3
"""Dragon Studios Reel pipeline with optional character-inspired voice profiles."""
import os
import sys
import json
import random
import argparse
import subprocess
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "scripts"))

from video_engine import render_smooth_reel
from gemini_copywriter import generate_caption
from psychology_engine import choose_topic, generate_psychology_caption
from uplika_uploader import publish_reel, poll_publish_status
from gdrive_downloader import download_file as gdrive_download
from voiceover import generate_voiceover, mix_voiceover, build_narration, choose_voice_profile

DEFAULT_VIDEO_DIR = "/home/001268796482_0/Videos/3000+ Anime reel bundle"
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "outputs")
HISTORY_FILE = os.path.join(SCRIPT_DIR, "publish_history.json")


def load_themes():
    path = os.path.join(SCRIPT_DIR, "config", "themes.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("themes", [])


def resolve_video_path(bases, rel_dir, filename):
    cleaned = rel_dir.replace("Digiproducthub.in ", "").replace("(", "").replace(")", "").strip()
    for base in bases:
        for sub in (rel_dir, cleaned, os.path.join("clips", rel_dir), os.path.join("clips", cleaned), ""):
            full = os.path.normpath(os.path.join(base, sub, filename) if sub else os.path.join(base, filename))
            if os.path.isfile(full):
                return full
    return None


def save_history(entry):
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            data = json.load(f) if os.path.exists(HISTORY_FILE) else []
        if not isinstance(data, list):
            data = []
    except (OSError, ValueError):
        data = []
    data.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    p = argparse.ArgumentParser(description="Dragon Studios Reel automation")
    p.add_argument("--theme", default="random", help="Anime theme ID or random")
    p.add_argument("--mode", choices=("anime", "psychology"), default=os.environ.get("CONTENT_MODE", "anime"))
    p.add_argument("--dry-run", action="store_true", help="Render without publishing")
    p.add_argument("--video-dir", default="")
    p.add_argument("--output", default="")
    p.add_argument("--voice-profile", choices=("off", "auto", "ayanokoji-inspired", "johan-inspired", "deep-narrator", "bright-narrator"), default="off",
                   help="Optional voiceover profile; auto randomly chooses among configured profiles")
    args = p.parse_args()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    themes = load_themes()
    if not themes:
        raise SystemExit("No themes defined in config/themes.json")
    if args.theme == "random":
        base_theme = random.choice(themes)
    else:
        matches = [t for t in themes if t.get("id") == args.theme]
        if not matches:
            raise SystemExit(f"Unknown theme ID: {args.theme}")
        base_theme = matches[0]

    topic = choose_topic(os.path.join(SCRIPT_DIR, "analytics", "instagram_metrics.csv")) if args.mode == "psychology" else None
    title = topic["title"] if topic else base_theme.get("hook_title", "ANIME CLASH")
    subtitle = topic["subtitle"] if topic else base_theme.get("hook_subtitle", "CHOOSE YOUR FIGHTER")
    print(f"MODE: {args.mode} | SOURCE THEME: {base_theme['name']}" + (f" | TOPIC: {topic['id']}" if topic else ""))

    bases = [args.video_dir, os.environ.get("VIDEO_BUNDLE_ROOT", ""), DEFAULT_VIDEO_DIR,
             os.path.join(SCRIPT_DIR, "clips"), "/tmp/clips"]
    bases = [x for x in bases if x and os.path.exists(x)]
    segments = []
    for seg in base_theme.get("relative_segments", []):
        filename = seg.get("file", "")
        path = resolve_video_path(bases, seg.get("dir", ""), filename)
        if not path:
            path = gdrive_download(filename, destination_dir="/tmp/clips", rel_dir=seg.get("dir", ""))
        if not path or not os.path.isfile(path):
            raise SystemExit(f"Source clip unavailable: {filename}")
        segments.append((path, seg.get("start", 0.0), seg.get("duration", 3.0)))
    if not segments:
        raise SystemExit("Selected theme has no usable segments")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = args.output or os.path.join(OUTPUT_DIR, f"reel_{args.mode}_{base_theme['id']}_{stamp}.mp4")
    render_smooth_reel(segments=segments, output_path=out, hook_title=title, hook_subtitle=subtitle,
                       watermark="@dragon.studios.india", psychology_topic=topic)

    caption = (generate_psychology_caption(topic, base_theme.get("characters")) if topic
               else generate_caption(base_theme.get("name"), base_theme.get("characters")))
    print("\n" + caption + "\n")

    selected_profile = None
    voice_file = None
    if args.voice_profile != "off":
        selected_profile = choose_voice_profile(args.voice_profile)
        narration = build_narration(title, subtitle, mode=args.mode, characters=base_theme.get("characters"))
        voice_file = os.path.splitext(out)[0] + "_voice.mp3"
        generate_voiceover(narration, voice_file, profile_name=selected_profile)
        mix_voiceover(out, voice_file)
        print(f"VOICEOVER_PROFILE: {selected_profile}")

    publish_result = None
    permalink = None
    status = "dry_run" if args.dry_run else "not_attempted"
    if args.dry_run:
        print("DRY RUN: publishing skipped.")
    else:
        publish_result = publish_reel(out, caption)
        if publish_result:
            post_id = publish_result.get("_post_id") or publish_result.get("id") or publish_result.get("postId")
            permalink = poll_publish_status(post_id=post_id, timeout_seconds=180, interval=5)
            status = "published_verified" if permalink else "unverified_or_pending"
        else:
            status = "publish_failed"
        if permalink:
            print(f"INSTAGRAM_PERMALINK_VERIFIED: {permalink}")
        else:
            print("Publication is NOT verified: no public Instagram Reel permalink was confirmed. Check provider dashboard before retrying to avoid duplicate posts.")

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(), "mode": args.mode,
        "theme_id": base_theme["id"], "topic_id": topic["id"] if topic else None,
        "video_file": out, "caption": caption, "dry_run": args.dry_run,
        "voice_profile": selected_profile, "voice_file": voice_file,
        "publish_status": status, "permalink": permalink
    }
    save_history(entry)
    print(f"History recorded ({status}).")
    if not args.dry_run and status != "published_verified":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
