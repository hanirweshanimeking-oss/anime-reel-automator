# Dragon Studios — Anime Reel Automation

Generates vertical anime reels with FFmpeg, original captions, a `@dragon.studios.india` watermark, and an optional psychology explainer mode. GitHub Actions supports scheduled render-only runs and manual workflow dispatch.

## Modes

- **Anime**: uses `config/themes.json` for known anime edits and Gemini-generated captions when `GEMINI_API_KEY` is configured.
- **Psychology**: chooses an educational topic such as *Overthinker vs Manipulator*, adds the topic title/subtitle to the Reel, and generates a nuanced caption. It uses existing anime clips as visuals; it does not infer personality from a person's face or diagnose anyone.
- **Performance feedback**: `analytics/instagram_metrics.csv` accepts real post insights (`topic_id,post_url,date,views,likes,comments,shares,saves`). Topic selection uses this file as a lightweight engagement signal. Metrics are descriptive, not proof of causation. The project does not claim to fetch Instagram insights automatically.
- **Publishing verification**: a run is only reported as verified when the provider returns a public Instagram Reel permalink. CDN/media URLs and generic `publishing` statuses are not proof. If verification fails, the workflow exits non-zero; check the provider dashboard before retrying to avoid duplicate posts.

## Run locally

```bash
pip install -r requirements.txt
python3 pipeline.py --mode anime --theme random --dry-run
python3 pipeline.py --mode psychology --theme jjk_honored_one --dry-run
python3 scripts/performance_learner.py
python3 -m pytest -q
```

## GitHub Actions secrets

Add these under **Settings → Secrets and variables → Actions**. Never put their values in source code, README files, logs, or commits.

- `GEMINI_API_KEY` — optional; offline captions are used when absent.
- `UPLIKA_API_KEY` — required only for live publishing.
- `UPLIKA_ACCOUNT_ID` — required only for live publishing.
- `GDRIVE_CLIENT_ID`, `GDRIVE_CLIENT_SECRET`, `GDRIVE_REFRESH_TOKEN` — needed if clips must be fetched from Google Drive.

The manual workflow defaults to a dry run. Scheduled executions also render only; to publish, manually run the workflow and explicitly turn off `dry_run` after checking the rendered artifact and confirming your provider setup.

## Credential safety

Credentials were previously present in repository text/source. They have been removed from the current source in this change, but this does **not** invalidate them or erase Git history. Rotate/revoke exposed Gemini, Uplika, and Google Drive credentials; review the repository's commit history and replace any affected secrets. Keep the repository private if its bundled media requires it.

## Metrics format

Add one row per Reel after collecting genuine Instagram insights:

```csv
topic_id,post_url,date,views,likes,comments,shares,saves
psychopath-vs-mastermind,https://www.instagram.com/reel/EXAMPLE/,2026-10-27,1200,95,14,8,11
```
