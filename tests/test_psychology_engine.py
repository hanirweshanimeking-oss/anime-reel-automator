import csv
import tempfile
import unittest
from pathlib import Path
from scripts.psychology_engine import TOPICS, choose_topic, generate_psychology_caption
from scripts.performance_learner import ensure_template, summarize
from scripts.uplika_uploader import _verified_permalink

class PsychologyEngineTests(unittest.TestCase):
    def test_topics_are_unique_and_safely_framed(self):
        ids=[t['id'] for t in TOPICS]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertTrue(all(t.get('lesson') and t.get('question') for t in TOPICS))
        self.assertTrue(any('not a diagnosis' in t['lesson'].lower() for t in TOPICS))
    def test_fallback_caption_contains_lesson_and_question(self):
        import os
        old=os.environ.pop('GEMINI_API_KEY',None)
        try:
            topic=TOPICS[0]; caption=generate_psychology_caption(topic,['Gojo'])
            self.assertIn(topic['lesson'],caption); self.assertIn(topic['question'],caption)
        finally:
            if old is not None: os.environ['GEMINI_API_KEY']=old
    def test_metrics_template_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'analytics'/'instagram_metrics.csv'
            ensure_template(str(path)); self.assertEqual(summarize(str(path))['posts'],0)
            with path.open('a',newline='',encoding='utf-8') as f:
                w=csv.writer(f); w.writerow([TOPICS[0]['id'],'https://www.instagram.com/reel/example/','2026-10-27',100,10,2,1,3])
            report=summarize(str(path)); self.assertEqual(report['posts'],1); self.assertEqual(report['views'],100)
    def test_permalink_verification_rejects_cdn_urls(self):
        self.assertEqual(_verified_permalink({'url':'https://www.instagram.com/reel/ABC123/'}),'https://www.instagram.com/reel/ABC123/')
        self.assertIsNone(_verified_permalink({'url':'https://cdn.example.com/video.mp4'}))
    def test_choose_topic_without_metrics(self):
        with tempfile.TemporaryDirectory() as tmp: self.assertIn(choose_topic(str(Path(tmp)/'missing.csv')),TOPICS)

if __name__=='__main__': unittest.main()
