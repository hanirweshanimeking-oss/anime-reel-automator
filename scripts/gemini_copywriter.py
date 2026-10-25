#!/usr/bin/env python3
"""
AI Virality Copywriter for Anime Reels using Google Gemini API.
Generates retention-focused hooks, psychological debate questions, and high-rank SEO hashtags.
Includes offline template fallback so execution never fails without an API key.
"""

import os
import sys
import json
import random
import urllib.request
import urllib.error

BRAND = "@dragon.studios.india"

FALLBACK_TEMPLATES = {
    "jjk": [
        {
            "hook": "HONORED ONE vs KING OF CURSES 🥶⚡",
            "body": "Infinite Void or Malevolent Shrine? When these two clash, reality shatters and peak fiction begins.",
            "cta": "Who has more aura in your opinion? Gojo or Sukuna? Drop your answer below! 👇",
            "tags": "#jujutsukaisen #gojosatoru #sukuna #itadoriyuuji #jjk #jjkedit #animereels #amvedit #otaku #dragonstudiosindia #explorepage #viralreels #animecommunity"
        },
        {
            "hook": "THE DEFINITION OF UNTOUCHABLE ♾️👁️",
            "body": "Six Eyes awakened. The moment Gojo took off his blindfold, anime history was written.",
            "cta": "Rate Gojo's aura from 1 to 10 in the comments! 👇",
            "tags": "#gojo #gojoedit #jujutsukaisenseason2 #satorugojo #jjkanime #animehype #viralreels #animetrend #dragonstudiosindia #amv"
        },
        {
            "hook": "HE PULLED UP AND TOOK OVER 💀🔥",
            "body": "Ryomen Sukuna doesn't negotiate. When the King of Curses awakens, everyone kneels.",
            "cta": "What was Sukuna's most brutal moment? Let us know below! 👇",
            "tags": "#sukunaedit #ryomensukuna #jjkcurse #domainexpansion #animereel #foryouanime #animestatus #dragonstudiosindia"
        }
    ],
    "naruto": [
        {
            "hook": "THE TALE OF TWO BROTHERS ⚡🔥",
            "body": "Chidori vs Rasengan. The bond that was tested through fire, blood, and destiny.",
            "cta": "Sasuke or Naruto — who won this clash in your heart? Comment below! 👇",
            "tags": "#narutoshippuden #naruto #sasuke #uchihasasuke #rasengan #chidori #animereels #animeedits #dragonstudiosindia #explorepage"
        }
    ],
    "general": [
        {
            "hook": "PURE UNMATCHED AURA 🥶✨",
            "body": "Some scenes just hit different when the beat drops. High-energy anime mastery at its peak.",
            "cta": "Name your #1 favorite anime of all time in the comments! 👇",
            "tags": "#animeedits #animereels #animebadass #amvcommunity #otakulife #dragonstudiosindia #trendinganime #explorepage #viral"
        }
    ]
}


DEFAULT_GEMINI_KEY = "AQ.Ab8RN6J34lm1ATksX4a9ZWTxGj5VHalpV_EVbWba63LxxiQwBw"

def call_gemini_rest(prompt, api_key):
    """Calls Gemini REST API directly using standard Python urllib (zero dependencies)."""
    # Active current Google Gemini models
    models = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]
    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 800
            }
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    # Filter out internal thoughts and extract final text
                    content_parts = [
                        p["text"] for p in parts
                        if "text" in p and not p.get("thought", False) and not p.get("thoughtSignature")
                    ]
                    if not content_parts:
                        # Fallback to last text part if all had thought metadata
                        content_parts = [p["text"] for p in parts if "text" in p]
                    if content_parts:
                        return "\n".join(content_parts).strip()
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8")
            print(f"[*] Gemini {model_name} HTTP {e.code}: {err[:120]}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"[*] Gemini {model_name} attempt failed: {e}", file=sys.stderr)
            continue
    return None


def generate_caption(theme_name="JJK Clash", characters=None):
    """Generates an optimized Instagram Reel caption via Gemini or fallback template."""
    chars_str = ", ".join(characters) if characters else "Anime Legends"
    api_key = os.environ.get("GEMINI_API_KEY", "").strip() or DEFAULT_GEMINI_KEY

    if api_key:
        prompt = f"""
You are an expert anime social media growth strategist for the Instagram page '{BRAND}'.
Write a high-converting, high-retention viral caption for a vertical anime reel edit.

Video Theme: {theme_name}
Featured Characters / Show: {chars_str}
Watermark / Page handle: {BRAND}

Requirements:
1. Start with an aggressive, capitalized 1-line psychological hook with 2-3 relevant emojis.
2. Follow with 2 short sentences describing the immense aura, power, or iconic clash.
3. Include an engaging question asking viewers to choose or debate in the comments (drives viral comments algorithm).
4. Add a clean follow CTA: 'Follow {BRAND} for daily high-definition anime edits & phonk reels! 🐉✨'
5. End with 15-20 highly relevant, trending hashtags (e.g. #jujutsukaisen #animeedits #viralreels, etc.).
Do not include markdown headers like '### Caption:'. Return only the final ready-to-post caption text.
"""
        print("[*] Requesting AI caption from Google Gemini API (gemini-2.5-flash)...")
        ai_caption = call_gemini_rest(prompt, api_key)
        if ai_caption:
            print("[*] Successfully generated AI caption via Gemini!")
            return ai_caption
        print("[!] Gemini API request failed; switching to built-in viral templates.")

    # Fallback to curated templates
    key = "jjk" if "jjk" in theme_name.lower() or any("gojo" in c.lower() or "sukuna" in c.lower() for c in (characters or [])) else "general"
    tpl = random.choice(FALLBACK_TEMPLATES.get(key, FALLBACK_TEMPLATES["general"]))
    
    caption = f"""{tpl['hook']}

{tpl['body']}

{tpl['cta']}

Follow {BRAND} for daily high-definition anime edits & reels! 🐉✨

{tpl['tags']}"""
    return caption


if __name__ == "__main__":
    test_theme = "Honored One vs King of Curses"
    test_chars = ["Gojo Satoru", "Ryomen Sukuna"]
    res = generate_caption(test_theme, test_chars)
    print("\n--- Generated Caption ---\n")
    print(res)
