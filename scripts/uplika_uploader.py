#!/usr/bin/env python3
"""Uplika publisher. Never embeds credentials; only returns verified Instagram permalinks."""
import os,json,time,urllib.request,urllib.error,sys
BASE='https://api.uplika.com'
def _credentials():
    key=os.environ.get('UPLIKA_API_KEY','').strip(); account=os.environ.get('UPLIKA_ACCOUNT_ID','').strip()
    if not key or not account: raise RuntimeError('UPLIKA_API_KEY and UPLIKA_ACCOUNT_ID must be configured as environment secrets.')
    return key,account
def _request(path,method='GET',payload=None):
    key,_=_credentials(); data=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(BASE+path,data=data,headers={'Authorization':f'Bearer {key}','Content-Type':'application/json','User-Agent':'DragonStudios-CloudAutomator/2.0'},method=method)
    try:
        with urllib.request.urlopen(req,timeout=60) as resp:
            raw=resp.read().decode(); return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        print(f'[!] Uplika HTTP {e.code} on {path}; response redacted.',file=sys.stderr); return None
    except (urllib.error.URLError,TimeoutError,ValueError) as e:
        print(f'[!] Uplika request failed: {type(e).__name__}',file=sys.stderr); return None
def _find_post_id(data):
    if not isinstance(data,dict): return None
    for k in ('id','postId','post_id'):
        if data.get(k) is not None: return str(data[k])
    for k in ('data','result','post','response'):
        value=data.get(k)
        if isinstance(value,dict):
            found=_find_post_id(value)
            if found: return found
        if isinstance(value,list):
            for item in value:
                found=_find_post_id(item)
                if found: return found
    return None
def _verified_permalink(data):
    """Accept only a public Instagram URL, never a CDN/upload URL."""
    if isinstance(data,dict):
        for k in ('permalink','permalink_url','instagramUrl','instagram_url','postUrl','url','link'):
            v=data.get(k)
            if isinstance(v,str) and (v.startswith('https://www.instagram.com/') or v.startswith('https://instagram.com/')) and '/reel/' in v: return v
        for k in ('data','result','post','response','media'):
            v=data.get(k)
            if isinstance(v,dict):
                found=_verified_permalink(v)
                if found:return found
            if isinstance(v,list):
                for item in v:
                    found=_verified_permalink(item)
                    if found:return found
    return None
def publish_reel(file_path,caption,account_id=None):
    key,default_account=_credentials(); account=account_id or default_account
    if not os.path.isfile(file_path): print('[!] Video file not found.',file=sys.stderr); return None
    size=os.path.getsize(file_path); name=os.path.basename(file_path)
    presign=_request('/v1/media/presign','POST',{'fileName':name,'contentType':'video/mp4','bytes':size})
    if not isinstance(presign,dict) or not presign.get('uploadUrl') or not presign.get('id'): print('[!] Uplika did not return a valid upload URL/media ID.',file=sys.stderr); return None
    try:
        with open(file_path,'rb') as f: body=f.read()
        req=urllib.request.Request(presign['uploadUrl'],data=body,headers={'Content-Type':'video/mp4'},method='PUT')
        with urllib.request.urlopen(req,timeout=180) as r:
            if r.status not in (200,201,204): return None
    except (OSError,urllib.error.URLError,TimeoutError) as e:
        print(f'[!] Media upload failed: {type(e).__name__}',file=sys.stderr); return None
    completed=_request(f"/v1/media/{presign['id']}/complete",'POST',{})
    if completed is None: print('[!] Media completion could not be confirmed.',file=sys.stderr); return None
    result=_request('/v1/posts','POST',{'accountIds':[account],'content':caption,'mediaIds':[presign['id']],'options':{'instagram':{'contentType':'reel','shareToFeed':True}},'wait':False})
    if isinstance(result,dict): result['_post_id']=_find_post_id(result)
    return result
def poll_publish_status(post_id=None,timeout_seconds=180,interval=5):
    if not post_id: print('[!] No provider post ID; cannot verify publication.',file=sys.stderr); return None
    start=time.time()
    while time.time()-start<timeout_seconds:
        time.sleep(interval); result=_request('/v1/posts/'+str(post_id))
        if not isinstance(result,dict): continue
        link=_verified_permalink(result)
        if link:return link
        status=str(result.get('status') or result.get('state') or result.get('publishStatus') or '').lower()
        if status in ('failed','rejected','error','cancelled'): print('[!] Provider reports publication failure.',file=sys.stderr); return None
    return None
if __name__=='__main__':
    if len(sys.argv)<3: raise SystemExit('Usage: python uplika_uploader.py <video_path> <caption>')
    print(json.dumps(publish_reel(sys.argv[1],sys.argv[2]),indent=2))
