# Dragon Studios — Anime Reel Automation

Generates vertical anime Reels with FFmpeg, original captions, a `@dragon.studios.india` watermark, an optional psychology explainer mode, and optional character-inspired AI voiceover profiles.

## Voiceover profiles

Voice profiles give different Reels distinct narration styles. They are **inspired-by delivery presets**, not exact copies or clones of an anime character or voice actor.

- **Ayanokoji-inspired** — calm, restrained, analytical.
- **Johan-inspired** — soft-spoken, composed, eerie.
- **Deep narrator** — cinematic and authoritative.
- **Bright narrator** — energetic and expressive.
- **Auto** — randomly chooses from profiles whose voice IDs are configured, so consecutive Reels can use different styles.

The audio is generated through ElevenLabs, then mixed over the existing soundtrack with narration louder than the background music. Set these GitHub Actions secrets (or local environment variables); never commit values:

- `ELEVENLABS_API_KEY`
- `VOICE_ID_AYANOKOJI_INSPIRED`
- `VOICE_ID_JOHAN_INSPIRED`
- Optional: `VOICE_ID_DEEP_NARRATOR`, `VOICE_ID_BRIGHT_NARRATOR`

Each `VOICE_ID_*` must be a voice ID available in your own ElevenLabs account. Pick licensed/authorized voices; do not clone or impersonate a real voice actor without permission. Voice generation consumes provider credits.

Run one Reel with a fixed profile:

```bash
python3 pipeline.py --mode anime --theme random --voice-profile ayanokoji-inspired --dry-run
python3 pipeline.py --mode anime --theme random --voice-profile johan-inspired --dry-run
```

Let each Reel randomly choose among configured voices:

```bash
python3 pipeline.py --mode anime --theme random --voice-profile auto --dry-run
```

Voiceover is off by default. Omitting `--voice-profile` or using `--voice-profile off` keeps the original music-only behavior. `--dry-run` renders the Reel but does not publish it.

## Content modes

- **Anime**: uses `config/themes.json` for known anime edits and Gemini-generated captions when `GEMINI_API_KEY` is configured.
- **Psychology**: chooses an educational topic, adds the topic title/subtitle, and generates a nuanced caption. It does not infer personality from faces or diagnose anyone.
- **Performance feedback**: `analytics/instagram_metrics.csv` accepts real post insights; metrics are descriptive, not proof of causation.
- **Publishing verification**: a run is only reported as verified when the provider returns a public Instagram Reel permalink. If verification fails, check the provider dashboard before retrying to avoid duplicate posts.

## Run locally

```bash
pip install -r requirements.txt
python3 pipeline.py --mode anime --theme random --dry-run
python3 -m unittest discover -s tests -v
```

## GitHub Actions secrets

Add required values under **Settings → Secrets and variables → Actions**. Never put secrets in source code, README files, logs, or commits.

- `GEMINI_API_KEY` — optional for captions.
- `UPLIKA_API_KEY`, `UPLIKA_ACCOUNT_ID` — live publishing only.
- `GDRIVE_CLIENT_ID`, `GDRIVE_CLIENT_SECRET`, `GDRIVE_REFRESH_TOKEN` — Google Drive clip retrieval.
- `ELEVENLABS_API_KEY` and one or more `VOICE_ID_*` secrets — voiceover generation.

Scheduled executions render only; publishing requires explicit manual opt-in after verifying the rendered artifact and provider configuration.

## Credential safety

Credentials were previously present in repository text/source. Current source cleanup does not invalidate them or erase Git history. Rotate/revoke exposed Gemini, Uplika, and Google Drive credentials, review commit history, and replace affected secrets. Keep the repository private if bundled media requires it.
