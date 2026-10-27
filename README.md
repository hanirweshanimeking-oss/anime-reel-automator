# Dragon Studios — Anime Reel Automation

Generates vertical anime Reels with FFmpeg, original captions, a `@dragon.studios.india` watermark, an optional psychology mode, and optional **free offline voiceover**.

## Free offline voiceover

Voice generation uses **espeak-ng** installed on the GitHub Actions runner. It needs no paid voice service, API key, account, credits, or network access for speech generation. FFmpeg mixes narration over the existing soundtrack.

- **Ayanokoji-inspired** — calm, restrained, analytical delivery.
- **Johan-inspired** — soft-spoken, composed, eerie delivery.
- **Deep narrator** — lower-pitched cinematic narration.
- **Bright narrator** — faster, energetic narration.
- **Auto** — randomly chooses one of the local voice profiles per run.

These are basic synthesized voices with different voice variants, speed, and pitch; they are **style presets, not exact anime character or voice-actor imitations**. Offline TTS may sound more robotic than paid neural TTS.

Run a Reel with a fixed voice profile:

```bash
python3 pipeline.py --mode anime --theme random --voice-profile ayanokoji-inspired --dry-run
python3 pipeline.py --mode anime --theme random --voice-profile johan-inspired --dry-run
```

Randomly choose a style:

```bash
python3 pipeline.py --mode anime --theme random --voice-profile auto --dry-run
```

Voiceover remains off by default. `--dry-run` renders the Reel without publishing it.

## Content modes

- **Anime**: uses `config/themes.json` for anime edits and Gemini-generated captions when `GEMINI_API_KEY` is configured.
- **Psychology**: chooses an educational topic and generates a nuanced caption; it does not infer personality from faces or diagnose anyone.
- **Performance feedback**: `analytics/instagram_metrics.csv` accepts real post insights; metrics are descriptive, not proof of causation.
- **Publishing verification**: a run is only reported as verified when the provider returns a public Instagram Reel permalink. If verification fails, check the provider dashboard before retrying to avoid duplicate posts.

## Run locally

Install the free system tools and Python requirements:

```bash
sudo apt-get install ffmpeg espeak-ng
pip install -r requirements.txt
python3 pipeline.py --mode anime --theme random --voice-profile auto --dry-run
python3 -m unittest discover -s tests -v
```

## GitHub Actions secrets

Configure under **Settings → Secrets and variables → Actions**. Never put secrets in source code, README files, logs, or commits.

- `GEMINI_API_KEY` — optional for caption generation.
- `UPLIKA_API_KEY`, `UPLIKA_ACCOUNT_ID` — for publishing.
- `GDRIVE_CLIENT_ID`, `GDRIVE_CLIENT_SECRET`, `GDRIVE_REFRESH_TOKEN` — for Google Drive clip retrieval.

**No ElevenLabs secret or voice-ID secrets are required.** Scheduled runs render only; manual publishing should be done only after reviewing the rendered artifact and confirming provider configuration.

## Credential safety

If credentials were previously exposed in repository text or source, rotating them is still necessary; deleting them from current source does not erase Git history. Keep provider secrets in GitHub Actions settings and keep bundled media private if required.
