#!/usr/bin/env python3
"""Small, transparent offline analytics helper; no fabricated metrics or API scraping."""
import csv, os
FIELDS = ('topic_id','post_url','date','views','likes','comments','shares','saves')
def ensure_template(path='analytics/instagram_metrics.csv'):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    if not os.path.exists(path):
        with open(path,'w',newline='',encoding='utf-8') as f: csv.DictWriter(f,fieldnames=FIELDS).writeheader()
def summarize(path='analytics/instagram_metrics.csv'):
    if not os.path.isfile(path): return {'posts':0,'note':'No metrics file yet; add real Instagram insights rows.'}
    totals={'views':0,'likes':0,'comments':0,'shares':0,'saves':0}; count=0
    with open(path,newline='',encoding='utf-8') as f:
        for row in csv.DictReader(f):
            count+=1
            for k in totals:
                try: totals[k]+=max(0,int(float(row.get(k) or 0)))
                except ValueError: pass
    views=totals['views']
    return {'posts':count,**totals,'engagement_rate':round((totals['likes']+2*totals['comments']+3*totals['shares']+3*totals['saves'])/views,4) if views else None,'note':'Descriptive engagement proxy only; not a causal measure.'}
if __name__=='__main__':
    ensure_template(); print(summarize())
