#!/usr/bin/env python3
"""Psychology-themed short-form content with evidence-aware, non-diagnostic framing."""
import csv, json, os, random, urllib.request, urllib.error

TOPICS = [
 {"id":"psychopath-vs-mastermind","title":"PSYCHOPATH vs MASTERMIND","subtitle":"CHARISMA IS NOT PROOF OF INTELLIGENCE","question":"Is strategic thinking the same as lacking empathy?", "lesson":"A fictional label is not a diagnosis. Psychopathy is a complex research construct; intelligence, empathy, and planning are separate dimensions."},
 {"id":"overthinker-vs-manipulator","title":"OVERTHINKER vs MANIPULATOR","subtitle":"ANXIETY IS NOT CONTROL","question":"What separates rumination from deliberate influence?", "lesson":"Overthinking is repetitive worry; manipulation involves intentional influence. One behavior alone cannot establish a person's motives."},
 {"id":"confidence-vs-arrogance","title":"CONFIDENCE vs ARROGANCE","subtitle":"THE DIFFERENCE IS HOW YOU TREAT OTHERS","question":"Can someone be confident and still admit mistakes?", "lesson":"Confidence can coexist with humility and feedback. Arrogance tends to dismiss other people or overstate certainty."},
 {"id":"introvert-vs-social-anxiety","title":"INTROVERSION vs SOCIAL ANXIETY","subtitle":"PREFERENCE IS NOT THE SAME AS FEAR","question":"Do you recharge alone, or avoid situations because they feel frightening?", "lesson":"Introversion is a temperament preference; social anxiety involves distress or fear. Only a qualified professional can assess a disorder."},
 {"id":"discipline-vs-motivation","title":"DISCIPLINE vs MOTIVATION","subtitle":"SYSTEMS OUTLAST MOODS","question":"What small system helps you keep a promise to yourself?", "lesson":"Motivation fluctuates. Clear cues, realistic goals, and repeatable routines can make action more consistent."},
 {"id":"emotional-control-vs-suppression","title":"EMOTIONAL CONTROL vs SUPPRESSION","subtitle":"NOTICE IT. NAME IT. CHOOSE YOUR RESPONSE.", "question":"Is calmness always the same as emotional health?", "lesson":"Regulation means noticing and responding constructively; suppression means hiding or pushing feelings away. Context matters."},
 {"id":"influence-vs-manipulation","title":"INFLUENCE vs MANIPULATION","subtitle":"TRANSPARENCY CHANGES EVERYTHING","question":"Does the other person have enough information and a real choice?", "lesson":"Ethical influence is transparent and respects autonomy. Deception, coercion, and exploiting vulnerabilities are warning signs."},
 {"id":"memory-vs-attention","title":"MEMORY vs ATTENTION","subtitle":"WHAT YOU NOTICE SHAPES WHAT YOU REMEMBER","question":"Can you remember something accurately if you barely noticed it?", "lesson":"Memory is reconstructive and attention is selective; confidence in a memory does not guarantee accuracy."}
]

def _metric_scores(csv_path):
    scores = {}
    if not csv_path or not os.path.isfile(csv_path): return scores
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                topic = (row.get('topic_id') or '').strip()
                if not topic: continue
                vals = [float(row.get(k) or 0) for k in ('views','likes','comments','shares','saves')]
                views, likes, comments, shares, saves = vals
                if views > 0:
                    # Engagement rate with a small smoothing floor; never treat this as causal evidence.
                    rate = (likes + 2*comments + 3*shares + 3*saves) / views
                    scores[topic] = scores.get(topic, []) + [rate]
    except (OSError, ValueError, csv.Error):
        return {}
    return {k: sum(v)/len(v) for k,v in scores.items() if v}

def choose_topic(metrics_csv='analytics/instagram_metrics.csv', rng=None):
    rng = rng or random
    scores = _metric_scores(metrics_csv)
    if not scores: return rng.choice(TOPICS)
    # Gentle exploitation: metrics influence selection but every topic retains a chance.
    weights = [1.0 + min(max(scores.get(t['id'], 0.0) * 10, 0.0), 3.0) for t in TOPICS]
    return rng.choices(TOPICS, weights=weights, k=1)[0]

def generate_psychology_caption(topic, characters=None):
    key = os.environ.get('GEMINI_API_KEY', '').strip()
    chars = ', '.join(characters or []) or 'anime characters'
    if key:
        prompt = f'''Write an original Instagram Reel caption for {topic['title']} for @dragon.studios.india. Related visual theme: {chars}. Topic lesson: {topic['lesson']} Question: {topic['question']}. Use a strong but non-stigmatizing hook, 2 short educational sentences, one debate question, a follow CTA, and 8-12 relevant hashtags. Do not diagnose real people, present pop-psychology as settled science, encourage manipulation, or claim a personality label can be inferred from appearance. Return only caption text.'''
        models = ('gemini-2.5-flash','gemini-2.0-flash')
        for model in models:
            req = urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}', data=json.dumps({'contents':[{'parts':[{'text':prompt}]}], 'generationConfig':{'temperature':0.7,'maxOutputTokens':500}}).encode(), headers={'Content-Type':'application/json'}, method='POST')
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    data=json.loads(r.read().decode())
                parts=data.get('candidates',[{}])[0].get('content',{}).get('parts',[])
                text='\n'.join(p.get('text','') for p in parts if p.get('text') and not p.get('thought')).strip()
                if text: return text
            except (urllib.error.URLError, urllib.error.HTTPError, ValueError, IndexError, KeyError):
                continue
    return (f"{topic['title']} 🧠\n\n{topic['lesson']}\n\n{topic['question']}\n\nFollow @dragon.studios.india for more anime edits and psychology explainers.\n\n#psychology #criticalthinking #humanbehavior #mindset #animeedit #dragonstudiosindia #selfawareness")

if __name__ == '__main__':
    print(json.dumps(choose_topic(), ensure_ascii=False, indent=2))
