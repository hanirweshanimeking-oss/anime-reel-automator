#!/usr/bin/env python3
"""
Dynamic High-Retention Anime Reel Assembly Engine using FFmpeg.
- Handles vertical 1080x1920 9:16 cropping and sharpening
- Calculates dynamic xfade transition offsets
- Applies on-screen hook titles and @dragon.studios.india watermark
- Integrates continuous phonk audio with loudnorm broadcast mastering
"""

import os
import sys
import subprocess
import shutil

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
FONT_FILE = os.path.join(ASSETS_DIR, "fonts", "font.ttf")
AUDIO_FILE = os.path.join(ASSETS_DIR, "audio", "master_phonk_track.mp3")

TRANSITIONS_POOL = ["fadewhite", "circlecrop", "smoothleft", "fade", "wipeleft", "slideup"]


def check_ffmpeg():
    """Ensures ffmpeg and ffprobe are available."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg executable not found in PATH!")


def render_smooth_reel(
    segments,
    output_path,
    hook_title="HONORED ONE vs KING OF CURSES",
    hook_subtitle="WHO HAS MORE AURA?",
    watermark="@dragon.studios.india",
    audio_track=None,
    temp_dir="/tmp/reel_build"
):
    """
    Renders a multi-clip montage with smooth xfade transitions, dynamic typography,
    and a continuous phonk audio track.
    
    segments: list of tuples -> (video_file_path, start_time_seconds, duration_seconds)
    output_path: path to final MP4 output
    """
    check_ffmpeg()
    os.makedirs(temp_dir, exist_ok=True)
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    music_file = audio_track or AUDIO_FILE
    if not os.path.exists(music_file):
        raise FileNotFoundError(f"Audio file missing: {music_file}")

    font_path = FONT_FILE if os.path.exists(FONT_FILE) else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    print(f"[*] Pre-processing {len(segments)} visual segments to 1080x1920...")
    segment_files = []
    
    for idx, (vpath, st, dur) in enumerate(segments):
        part_path = os.path.join(temp_dir, f"seg_{idx}.mp4")
        vf = (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "unsharp=5:5:0.85:5:5:0.0,"
            "eq=contrast=1.18:saturation=1.28:brightness=0.01"
        )
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(st),
            "-t", str(dur),
            "-i", vpath,
            "-vf", vf,
            "-r", "30",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
            "-an",
            part_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[!] Error processing segment {idx}: {res.stderr}", file=sys.stderr)
            raise RuntimeError(f"FFmpeg failed on segment {idx}")
        segment_files.append(part_path)
        print(f"  [✓] Segment {idx+1}/{len(segments)} ready ({dur}s)")

    # Dynamic xfade calculation
    trans_dur = 0.30
    current_time = 0.0
    filter_parts = []
    prev_label = "[0:v]"
    
    # Calculate transitions
    running_offset = segments[0][2] - trans_dur
    for i in range(1, len(segments)):
        next_input = f"[{i}:v]"
        out_label = f"[v0{i}]" if i < len(segments) - 1 else "[vraw]"
        trans_name = TRANSITIONS_POOL[(i - 1) % len(TRANSITIONS_POOL)]
        filter_parts.append(
            f"{prev_label}{next_input}xfade=transition={trans_name}:duration={trans_dur:.2f}:offset={running_offset:.2f}{out_label}"
        )
        prev_label = out_label
        running_offset += segments[i][2] - trans_dur

    total_duration = running_offset + trans_dur
    print(f"[*] Computed total visual duration: {total_duration:.2f} seconds")

    # Typography & Watermark layer
    clean_hook = hook_title.replace("'", "").replace(":", "-")
    clean_sub = hook_subtitle.replace("'", "").replace(":", "-")
    clean_brand = watermark.replace("'", "")

    text_filters = (
        f"[vraw]vignette=angle=PI/50,"
        f"drawtext=text='{clean_hook}':fontfile='{font_path}':fontsize=44:fontcolor=white:bordercolor=black:borderw=4:shadowcolor=black@0.9:shadowx=3:shadowy=3:x=(w-text_w)/2:y=280:enable='between(t,0,3.2)',"
        f"drawtext=text='{clean_sub}':fontfile='{font_path}':fontsize=38:fontcolor=yellow:bordercolor=black:borderw=4:shadowcolor=black@0.9:shadowx=3:shadowy=3:x=(w-text_w)/2:y=340:enable='between(t,0,3.2)',"
        f"drawtext=text='{clean_brand}':fontfile='{font_path}':fontsize=32:fontcolor=white@0.85:bordercolor=black@0.8:borderw=2:x=(w-text_w)/2:y=h-220[vout]"
    )
    filter_parts.append(text_filters)
    full_complex_filter = ";".join(filter_parts)

    # Final assembly command
    audio_index = len(segment_files)
    cmd = ["ffmpeg", "-y"]
    for sf in segment_files:
        cmd.extend(["-i", sf])
    cmd.extend(["-i", music_file])
    cmd.extend([
        "-filter_complex", full_complex_filter,
        "-map", "[vout]",
        "-map", f"{audio_index}:a",
        "-t", f"{total_duration:.2f}",
        "-af", f"loudnorm=I=-14:LRA=7:TP=-1.5,afade=t=in:st=0:d=0.2,afade=t=out:st={total_duration-0.8:.2f}:d=0.8",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        output_path
    ])

    print("[*] Assembling full smooth montage with continuous single phonk soundtrack...")
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"[!] FFmpeg Assembly Error: {res.stderr}", file=sys.stderr)
        raise RuntimeError("FFmpeg assembly failed")

    print(f"[✓] Final High-Retention Reel Created: {output_path} ({os.path.getsize(output_path)/(1024*1024):.2f} MB)")
    return output_path
