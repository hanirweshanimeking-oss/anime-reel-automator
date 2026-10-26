#!/usr/bin/env python3
"""
Uplika Instagram API Integration for Autonomous Reel Publishing.
Supports direct binary streaming to presigned S3/storage and Instagram Graph API publishing.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error

# Configurable via environment variables or default fallback
DEFAULT_API_KEY = "sk_6e85888ae9c16610bd87c90e34a7290818636b55cde49d2c37f9be2e7717b5d5"
DEFAULT_ACCOUNT_ID = "conn_8fe3721242166de7"

API_KEY = os.environ.get("UPLIKA_API_KEY", DEFAULT_API_KEY)
ACCOUNT_ID = os.environ.get("UPLIKA_ACCOUNT_ID", DEFAULT_ACCOUNT_ID)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "DragonStudios-CloudAutomator/1.0"
}


def extract_permalink(data):
    """Extract a public URL from a nested Uplika response payload."""
    if isinstance(data, str):
        return data if data.startswith("http") else None

    if not isinstance(data, dict):
        return None

    for key in ("permalink", "permalink_url", "url", "link", "webUrl", "shareUrl", "postUrl", "instagramUrl"):
        value = data.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value

    for key in ("data", "result", "post", "response", "media"):
        nested = data.get(key)
        if nested is not None:
            if isinstance(nested, list):
                for item in nested:
                    permalink = extract_permalink(item)
                    if permalink:
                        return permalink
            elif isinstance(nested, dict):
                permalink = extract_permalink(nested)
                if permalink:
                    return permalink

    return None


def uplika_request(path, method="GET", payload=None):
    """Makes an authenticated JSON request to the Uplika REST API."""
    url = f"https://api.uplika.com{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"[!] Uplika HTTP Error {e.code} on {path}: {err_msg}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[!] Uplika Network Error on {path}: {e}", file=sys.stderr)
        return None


def presign_and_upload(file_path):
    """Requests presigned URL and uploads the local MP4 video file."""
    if not os.path.exists(file_path):
        print(f"[!] Video file not found: {file_path}", file=sys.stderr)
        return None

    size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)
    mime = "video/mp4"

    print(f"[*] Requesting presigned URL for {filename} ({size / (1024 * 1024):.2f} MB)...")
    res = uplika_request("/v1/media/presign", method="POST", payload={
        "fileName": filename,
        "contentType": mime,
        "bytes": size
    })

    if not res or "uploadUrl" not in res:
        print("[!] Failed to obtain presigned upload URL from Uplika", file=sys.stderr)
        return None

    upload_url = res.get("uploadUrl")
    media_id = res.get("id")
    print(f"[*] Uplika Media ID: {media_id}")

    print("[*] Uploading video binary directly to cloud storage...")
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        put_req = urllib.request.Request(
            upload_url,
            data=file_bytes,
            headers={"Content-Type": mime},
            method="PUT"
        )
        with urllib.request.urlopen(put_req, timeout=120) as resp:
            if resp.status not in (200, 201, 204):
                print(f"[!] S3 storage PUT returned status: {resp.status}", file=sys.stderr)
                return None
            print(f"[*] Video binary uploaded successfully (Status: {resp.status})")
    except Exception as e:
        print(f"[!] Upload binary failed: {e}", file=sys.stderr)
        return None

    print(f"[*] Confirming media upload completion via /v1/media/{media_id}/complete...")
    comp_res = uplika_request(f"/v1/media/{media_id}/complete", method="POST", payload={})
    print(f"[*] Completion confirmed: {comp_res}")
    return media_id


def publish_reel(file_path, caption, account_id=None):
    """Uploads video and creates a live published Instagram Reel."""
    target_account = account_id or ACCOUNT_ID
    media_id = presign_and_upload(file_path)
    if not media_id:
        print("[!] Media upload failed; aborting publish.", file=sys.stderr)
        return None

    print(f"[*] Dispatching Reel publish to Instagram (Account: {target_account})...")
    post_payload = {
        "accountIds": [target_account],
        "content": caption,
        "mediaIds": [media_id],
        "options": {
            "instagram": {
                "contentType": "reel",
                "shareToFeed": True
            }
        },
        "wait": False
    }

    pub_res = uplika_request("/v1/posts", method="POST", payload=post_payload)
    if isinstance(pub_res, dict):
        direct_link = extract_permalink(pub_res)
        if direct_link:
            print(f"[*] Instagram reel URL returned immediately: {direct_link}")
    return pub_res


def poll_publish_status(post_id=None, timeout_seconds=120, interval=5):
    """Polls post until Instagram completes publishing."""
    print(f"[*] Polling Instagram post status (Target: {post_id or 'latest'})...")
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        time.sleep(interval)
        if post_id:
            res = uplika_request(f"/v1/posts/{post_id}")
            if res:
                status = res.get("status") or res.get("state") or res.get("publishStatus") or "unknown"
                permalink = extract_permalink(res)
                print(f"[*] Status: {status} | Link: {permalink or 'Processing on Instagram...'}")
                if permalink:
                    return permalink
                if str(status).lower() in ("failed", "rejected", "error", "cancelled"):
                    print(f"[!] Post status failed: {res.get('error') or res.get('message') or res}", file=sys.stderr)
                    return None
                if str(status).lower() in ("published", "posted", "live", "completed"):
                    print(f"[!] Post marked as published, but no public permalink was returned by the API: {res}", file=sys.stderr)
                    return None
        else:
            res = uplika_request("/v1/posts")
            if res and "data" in res and len(res["data"]) > 0:
                latest = res["data"][0]
                status = latest.get("status") or latest.get("state") or latest.get("publishStatus") or "unknown"
                permalink = extract_permalink(latest)
                print(f"[*] Status: {status} | Link: {permalink or 'Processing on Instagram...'}")
                if permalink:
                    return permalink
                if str(status).lower() in ("failed", "rejected", "error", "cancelled"):
                    print(f"[!] Post status failed: {latest.get('error') or latest.get('message') or latest}", file=sys.stderr)
                    return None
    return None


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python uplika_uploader.py <video_path> <caption>")
        sys.exit(1)
    v_path = sys.argv[1]
    cap = sys.argv[2]
    res = publish_reel(v_path, cap)
    print(json.dumps(res, indent=2))
