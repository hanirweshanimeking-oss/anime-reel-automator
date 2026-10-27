#!/usr/bin/env python3
"""FFmpeg Reel renderer for cinematic anime edits and dark psychology quote reels."""
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
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg executable not found in PATH!")


def _escape_drawtext(value):
    """Escape text for FFmpeg drawtext filter syntax."""
    return (str(value).replace("\\", "\\\\").replace(":", "\\:")
            .replace("'", "\\'").replace("%", "\\%").replace("[", "\\[")
            .replace("]", "\\]").replace("\n", " "))


def render_smooth_reel(segments, output_path, hook_title="HONORED ONE vs KING OF CURSES",
                       hook_subtitle="WHO HAS MORE AURA?", watermark="@dragon.studios.india",
                       audio_track=None, temp_dir="/tmp/reel_build", psychology_topic=None):
    """Render 9:16 anime montage; psychology mode matches the supplied monochrome quote-reel reference."""
    check_ffmpeg()
    os.makedirs(temp_dir, exist_ok=True)
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    music_file = audio_track or AUDIO_FILE
    if not os.path.exists(music_file):
        raise FileNotFoundError(f"Audio file missing: {music_file}")
    font_path = FONT_FILE if os.path.exists(FONT_FILE) else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    serif_path = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"
    if not os.path.exists(serif_path):
        serif_path = font_path

    segment_files = []
    print(f"[*] Pre-processing {len(segments)} visual segments to 1080x1920...")
    for idx, (vpath, st, dur) in enumerate(segments):
        part_path = os.path.join(temp_dir, f"seg_{idx}.mp4")
        if psychology_topic:
            vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,unsharp=5:5:0.5:5:5:0.0,eq=contrast=1.13:saturation=0.0:brightness=-0.015"
        else:
            vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,unsharp=5:5:0.85:5:5:0.0,eq=contrast=1.18:saturation=1.28:brightness=0.01"
        cmd = ["ffmpeg", "-y", "-ss", str(st), "-t", str(dur), "-i", vpath,
               "-vf", vf, "-r", "30", "-c:v", "libx264", "-preset", "ultrafast",
               "-crf", "18", "-an", part_path]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[!] Error processing segment {idx}: {res.stderr}", file=sys.stderr)
            raise RuntimeError(f"FFmpeg failed on segment {idx}")
        segment_files.append(part_path)
        print(f"  [✓] Segment {idx+1}/{len(segments)} ready ({dur}s)")

    trans_dur = 0.30
    filter_parts = []
    prev_label = "[0:v]"
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

    clean_hook = _escape_drawtext(hook_title)
    clean_sub = _escape_drawtext(hook_subtitle)
    clean_brand = _escape_drawtext(watermark)
    if psychology_topic:
        points = psychology_topic.get("points", [
            "WATCH THE PATTERN — Notice repeated behavior, not one moment.",
            "MEASURE THE PAUSES — Give yourself time to think before reacting.",
            "STAY CURIOUS — Ask questions instead of assuming motives."
        ])
        # Match the reference structure: monochrome anime footage, white headings,
        # gold italic supporting text, numbered points, and a final follow card.
        point_titles = [str(p).split(" — ", 1)[0] for p in points]
        point_bodies = [str(p).split(" — ", 1)[1] if " — " in str(p) else str(p) for p in points]
        heading_font = font_path
        quote_font = serif_path
        intro_quote = _escape_drawtext(psychology_topic.get("question", "Observe carefully. Question assumptions. Choose your response."))
        filter_parts.append(
            f"[vraw]vignette=angle=PI/5,format=yuv420p,"
            f"drawtext=text='{clean_hook}':fontfile='{heading_font}':fontsize=43:fontcolor=white:bordercolor=black@0.85:borderw=2:x=(w-text_w)/2:y=h*0.36:enable='between(t,0,3.2)',"
            f"drawtext=text='{intro_quote}':fontfile='{quote_font}':fontsize=24:fontcolor=0xD9B96E:bordercolor=black@0.8:borderw=1:x=(w-text_w)/2:y=h*0.405:enable='between(t,0,3.2)',"
            f"drawtext=text='1. {_escape_drawtext(point_titles[0] if len(point_titles)>0 else 'WATCH THE PATTERN')}':fontfile='{heading_font}':fontsize=35:fontcolor=white:bordercolor=black@0.85:borderw=2:x=(w-text_w)/2:y=h*0.34:enable='between(t,3.2,7.0)',"
            f"drawtext=text='2. {_escape_drawtext(point_titles[1] if len(point_titles)>1 else 'MEASURE THE PAUSES')}':fontfile='{heading_font}':fontsize=35:fontcolor=white:bordercolor=black@0.85:borderw=2:x=(w-text_w)/2:y=h*0.34:enable='between(t,7.0,10.8)',"
            f"drawtext=text='3. {_escape_drawtext(point_titles[2] if len(point_titles)>2 else 'STAY CURIOUS')}':fontfile='{heading_font}':fontsize=35:fontcolor=white:bordercolor=black@0.85:borderw=2:x=(w-text_w)/2:y=h*0.34:enable='between(t,10.8,14.8)',"
            f"drawtext=text='{_escape_drawtext(point_bodies[0] if len(point_bodies)>0 else 'Notice the pattern')}':fontfile='{quote_font}':fontsize=27:fontcolor=0xD9B96E:bordercolor=black@0.8:borderw=1:x=(w-text_w)/2:y=h*0.39:enable='between(t,3.2,7.0)',"
            f"drawtext=text='{_escape_drawtext(point_bodies[1] if len(point_bodies)>1 else 'Give yourself time')}':fontfile='{quote_font}':fontsize=27:fontcolor=0xD9B96E:bordercolor=black@0.8:borderw=1:x=(w-text_w)/2:y=h*0.39:enable='between(t,7.0,10.8)',"
            f"drawtext=text='{_escape_drawtext(point_bodies[2] if len(point_bodies)>2 else 'Ask, do not assume')}':fontfile='{quote_font}':fontsize=27:fontcolor=0xD9B96E:bordercolor=black@0.8:borderw=1:x=(w-text_w)/2:y=h*0.39:enable='between(t,10.8,14.8)',"
            f"drawtext=text='FOLLOW FOR MORE':fontfile='{heading_font}':fontsize=47:fontcolor=white:bordercolor=black@0.85:borderw=3:x=(w-text_w)/2:y=h*0.42:enable='gte(t,14.8)',"
            f"drawtext=text='Daily psychology and anime mindset. Save this for later.':fontfile='{quote_font}':fontsize=27:fontcolor=0xD9B96E:bordercolor=black@0.8:borderw=1:x=(w-text_w)/2:y=h*0.47:enable='gte(t,14.8)',"
            f"drawtext=text='{clean_brand}':fontfile='{heading_font}':fontsize=28:fontcolor=white@0.82:bordercolor=black@0.7:borderw=1:x=(w-text_w)/2:y=h-150[vout]"
        )
    else:
        filter_parts.append(
            f"[vraw]vignette=angle=PI/50,"
            f"drawtext=text='{clean_hook}':fontfile='{font_path}':fontsize=44:fontcolor=white:bordercolor=black:borderw=4:shadowcolor=black@0.9:shadowx=3:shadowy=3:x=(w-text_w)/2:y=280:enable='between(t,0,3.2)',"
            f"drawtext=text='{clean_sub}':fontfile='{font_path}':fontsize=38:fontcolor=yellow:bordercolor=black:borderw=4:shadowcolor=black@0.9:shadowx=3:shadowy=3:x=(w-text_w)/2:y=340:enable='between(t,0,3.2)',"
            f"drawtext=text='{clean_brand}':fontfile='{font_path}':fontsize=32:fontcolor=white@0.85:bordercolor=black@0.8:borderw=2:x=(w-text_w)/2:y=h-220[vout]"
        )

    full_complex_filter = ";".join(filter_parts)
    audio_index = len(segment_files)
    cmd = ["ffmpeg", "-y"]
    for sf in segment_files:
        cmd.extend(["-i", sf])
    cmd.extend(["-i", music_file, "-filter_complex", full_complex_filter,
                "-map", "[vout]", "-map", f"{audio_index}:a", "-t", f"{total_duration:.2f}",
                "-af", f"loudnorm=I=-14:LRA=7:TP=-1.5,afade=t=in:st=0:d=0.2,afade=t=out:st={max(0,total_duration-0.8):.2f}:d=0.8",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output_path])
    print("[*] Assembling montage with continuous soundtrack...")
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"[!] FFmpeg Assembly Error: {res.stderr}", file=sys.stderr)
        raise RuntimeError("FFmpeg assembly failed")
    print(f"[✓] Final Reel Created: {output_path} ({os.path.getsize(output_path)/(1024*1024):.2f} MB)")
    return output_path
