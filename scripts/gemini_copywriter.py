#!/usr/bin/env python3
"""Gemini caption writer. API credentials must be supplied through environment variables."""
import os,json,random,urllib.request,urllib.error
BRAND='@dragon.studios.india'
TEMPLATES=[('PURE UNMATCHED AURA 🥶✨','Some scenes hit different when the beat drops. High-energy anime mastery at its peak.','Name your #1 favorite anime below! 👇','#animeedits #animereels #amv #otaku #dragonstudiosindia #animecommunity'),('WHO WINS THIS CLASH? ⚡🔥','Two iconic rivals. One unforgettable moment. The debate belongs to you.','Choose your fighter in the comments! 👇','#anime #animeedit #animebattle #animereels #dragonstudiosindia')]
def generate_caption(theme_name='Anime Clash',characters=None):
    chars=', '.join(characters or []) or 'Anime legends'; key=os.environ.get('GEMINI_API_KEY','').strip()
    if key:
        prompt=f"Write an original Instagram Reel caption for {BRAND}. Theme: {theme_name}. Characters: {chars}. Start with a punchy hook, add two short sentences, a respectful debate question, a follow CTA, and 8-12 relevant hashtags. Return only caption text."
        for model in ('gemini-2.5-flash','gemini-2.0-flash'):
            req=urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}',data=json.dumps({'contents':[{'parts':[{'text':prompt}]}],'generationConfig':{'temperature':0.75,'maxOutputTokens':500}}).encode(),headers={'Content-Type':'application/json'},method='POST')
            try:
                with urllib.request.urlopen(req,timeout=20) as r: data=json.loads(r.read().decode())
                parts=data.get('candidates',[{}])[0].get('content',{}).get('parts',[]); text='\n'.join(x.get('text','') for x in parts if x.get('text') and not x.get('thought')).strip()
                if text: return text
            except (urllib.error.URLError,urllib.error.HTTPError,ValueError,IndexError,KeyError): continue
    hook,body,cta,tags=random.choice(TEMPLATES)
    return f'{hook}\n\n{theme_name}: {body}\n\n{cta}\n\nFollow {BRAND} for anime edits and phonk reels. 🐉\n\n{tags}'
