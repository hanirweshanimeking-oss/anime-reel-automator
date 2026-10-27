"""Free offline voiceover profiles for Dragon Studios Reels using espeak-ng.

No paid API, API key, account, or network request is required. Profiles are
delivery styles inspired by fictional characters, not exact voice imitations.
"""
import random
import shutil
import subprocess
from pathlib import Path

PROFILES = {
    "ayanokoji-inspired": {
        "description": "calm, restrained, analytical delivery",
        "voice": "en-us+m3",
        "speed": 138,
        "pitch": 28,
        "amplitude": 165,
    },
    "johan-inspired": {
        "description": "soft-spoken, measured, unsettling delivery",
        "voice": "en-us+f3",
        "speed": 126,
        "pitch": 43,
        "amplitude": 145,
    },
    "deep-narrator": {
        "description": "lower-pitched, cinematic narration",
        "voice": "en-us+m2",
        "speed": 132,
        "pitch": 20,
        "amplitude": 175,
    },
    "bright-narrator": {
        "description": "brisk, energetic, expressive narration",
        "voice": "en-us+m4",
        "speed": 165,
        "pitch": 48,
        "amplitude": 175,
    },
}


def configured_profiles():
    """Profiles are available when the offline espeak-ng binary is installed."""
    return list(PROFILES) if shutil.which("espeak-ng") else []


def choose_voice_profile(name="auto"):
    available = configured_profiles()
    if not available:
        raise RuntimeError("espeak-ng is not installed. Install it with: sudo apt-get install espeak-ng")
    if name == "auto":
        return random.choice(available)
    if name not in PROFILES:
        raise ValueError(f"Unknown voice profile: {name}")
    return name


def build_narration(title, subtitle, mode="anime", characters=None):
    title = " ".join(str(title or "").split()).strip()
    subtitle = " ".join(str(subtitle or "").split()).strip()
    if mode == "psychology":
        return f"Let's examine this carefully. {title}. {subtitle}. A single behavior never defines an entire person."
    if characters:
        names = ", ".join(str(c) for c in characters[:2])
        return f"{title}. {subtitle}. {names} — who takes this round?"
    return f"{title}. {subtitle}."


def generate_voiceover(text, output_path, profile_name):
    if profile_name not in PROFILES:
        raise ValueError(f"Unknown voice profile: {profile_name}")
    executable = shutil.which("espeak-ng")
    if not executable:
        raise RuntimeError("espeak-ng is not installed. Install it with: sudo apt-get install espeak-ng")
    text = " ".join(str(text or "").split()).strip()
    if not text:
        raise ValueError("Narration text cannot be empty")

    profile = PROFILES[profile_name]
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        executable, "-v", profile["voice"], "-s", str(profile["speed"]),
        "-p", str(profile["pitch"]), "-a", str(profile["amplitude"]),
        "-w", str(target), text,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0 or not target.exists() or target.stat().st_size == 0:
        raise RuntimeError("Offline espeak-ng voice generation failed: " + (result.stderr or "unknown error")[-1000:])
    return str(target)


def mix_voiceover(video_path, voice_path, narration_volume=1.0, music_volume=0.22):
    """Mix narration over the Reel soundtrack and replace the rendered video."""
    video = Path(video_path)
    voice = Path(voice_path)
    temp = video.with_name(video.stem + "_mixed_tmp.mp4")
    filt = (
        f"[0:a]volume={music_volume}[music];"
        f"[1:a]volume={narration_volume}[voice];"
        "[music][voice]amix=inputs=2:duration=first:dropout_transition=2,"
        "loudnorm=I=-14:LRA=7:TP=-1.5[a]"
    )
    cmd = [
        "ffmpeg", "-y", "-i", str(video), "-i", str(voice),
        "-filter_complex", filt, "-map", "0:v:0", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", str(temp),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0 or not temp.exists() or temp.stat().st_size == 0:
        if temp.exists():
            temp.unlink()
        raise RuntimeError("FFmpeg voice mixing failed: " + (result.stderr or "unknown error")[-1000:])
    temp.replace(video)
    return str(video)
