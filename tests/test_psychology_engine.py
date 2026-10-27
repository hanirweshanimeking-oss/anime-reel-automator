import csv
from scripts.psychology_engine import TOPICS, choose_topic, generate_psychology_caption
from scripts.performance_learner import ensure_template, summarize

def test_topics_are_unique_and_have_safe_framing():
    ids=[t['id'] for t in TOPICS]
    assert len(ids)==len(set(ids))
    assert all(t.get('lesson') and t.get('question') for t in TOPICS)
    assert any('not a diagnosis' in t['lesson'].lower() for t in TOPICS)

def test_fallback_caption_contains_lesson_and_question(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    topic=TOPICS[0]; caption=generate_psychology_caption(topic,['Gojo'])
    assert topic['lesson'] in caption and topic['question'] in caption

def test_metrics_template_and_summary(tmp_path):
    path=tmp_path/'analytics'/'instagram_metrics.csv'
    ensure_template(str(path)); assert summarize(str(path))['posts']==0
    with path.open('a',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow([TOPICS[0]['id'],'https://www.instagram.com/reel/example/','2026-10-27',100,10,2,1,3])
    report=summarize(str(path)); assert report['posts']==1 and report['views']==100

def test_choose_topic_from_bank_without_metrics(tmp_path):
    topic=choose_topic(str(tmp_path/'missing.csv'))
    assert topic in TOPICS
