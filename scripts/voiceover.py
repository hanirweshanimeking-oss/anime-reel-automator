"""Configurable ElevenLabs voiceover profiles for Dragon Studios Reels.

Profiles are character-inspired styles, not exact impersonations or voice clones.
Set ELEVENLABS_API_KEY and one or more VOICE_ID_* environment variables.
"""
import os
import random
import subprocess
from pathlib import Path

PROFILES = {
    "ayanokoji-inspired": {
        "env": "VOICE_ID_AYANOKOJI_INSPIRED",
        "description": "calm, restrained, analytical, low-emotion delivery",
        "settings": {"stability": 0.78, "similarity_boost": 0.72, "style": 0.18, "use_speaker_boost": True},
    },
    "johan-inspired": {
        "env": "VOICE_ID_JOHAN_INSPIRED",
        "description": "soft-spoken, composed, eerie, persuasive delivery",
        "settings": {"stability": 0.62, "similarity_boost": 0.72, "style": 0.32, "use_speaker_boost": True},
    },
    "deep-narrator": {
        "env": "VOICE_ID_DEEP_NARRATOR",
        "description": "deep, cinematic, authoritative narration",
        "settings": {"stability": 0.68, "similarity_boost": 0.72, "style": 0.25, "use_speaker_boost": True},
    },
    "bright-narrator": {
        "env": "VOICE_ID_BRIGHT_NARRATOR",
        "description": "energetic, clear, expressive narration",
        "settings": {"stability": 0.48, "similarity_boost": 0.72, "style": 0.38, "use_speaker_boost": True},
    },
}


def configured_profiles():
    return [name for name, item in PROFILES.items() if os.environ.get(item["env"], "").strip()]


def choose_voice_profile(name="auto"):
    available = configured_profiles()
    if name == "auto":
        if not available:
            raise RuntimeError("No voice profiles configured. Set at least one VOICE_ID_* secret.")
        return random.choice(available)
    if name not in PROFILES:
        raise ValueError(f"Unknown voice profile: {name}")
    if not os.environ.get(PROFILES[name]["env"], "").strip():
        raise RuntimeError(f"Voice profile '{name}' needs its {PROFILES[name]['env']} environment variable.")
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
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is required for voiceover generation.")
    if profile_name not in PROFILES:
        raise ValueError(f"Unknown voice profile: {profile_name}")
    profile = PROFILES[profile_name]
    voice_id = os.environ.get(profile["env"], "").strip()
    if not voice_id:
        raise RuntimeError(f"Missing configured voice ID: {profile['env']}")
    text = " ".join(str(text or "").split()).strip()
    if not text:
        raise ValueError("Narration text cannot be empty")

    # Import at call-time so local unit tests do not require network dependencies.
    import requests
    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": api_key, "Accept": "audio/mpeg", "Content-Type": "application/json"},
        json={"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": profile["settings"]},
        timeout=90,
    )
    if not response.ok:
        raise RuntimeError(f"ElevenLabs TTS failed ({response.status_code}): {response.text[:500]}")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(response.content)
    if target.stat().st_size == 0:
        raise RuntimeError("ElevenLabs returned an empty audio file")
    return str(target)


def mix_voiceover(video_path, voice_path, narration_volume=1.0, music_volume=0.22):
    """Mix narration clearly over the Reel's existing soundtrack in-place."""
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
