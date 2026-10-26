#!/usr/bin/env python3
"""Uplika API integration for uploading and publishing Instagram Reels."""

import json
import os
import sys
import time
import urllib.error
import urllib.request


API_KEY = os.environ.get("UPLIKA_API_KEY", "").strip()
ACCOUNT_ID = os.environ.get("UPLIKA_ACCOUNT_ID", "").strip()
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "DragonStudios-CloudAutomator/1.1",
}


def extract_permalink(data):
    """Extract a public URL from a nested Uplika response payload."""
    if isinstance(data, str):
        return data if data.startswith("http") else None
    if not isinstance(data, dict):
        return None

    for key in ("permalink", "permalink_url", "url", "link", "webUrl",
                "shareUrl", "postUrl", "instagramUrl"):
        value = data.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value

    for key in ("data", "result", "post", "response", "media"):
        nested = data.get(key)
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
    """Make an authenticated JSON request to the Uplika REST API."""
    if not API_KEY:
        print("[!] UPLIKA_API_KEY is not configured.", file=sys.stderr)
        return None

    url = f"https://api.uplika.com{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            if not raw.strip():
                return {"http_status": resp.status}
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                print(f"[!] Uplika returned non-JSON content on {path}.", file=sys.stderr)
                return None
    except urllib.error.HTTPError as exc:
        # Do not print request headers or credentials.
        body = exc.read().decode("utf-8", errors="replace")
        print(f"[!] Uplika HTTP Error {exc.code} on {path}: {body}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"[!] Uplika network error on {path}: {exc}", file=sys.stderr)
        return None


def presign_and_upload(file_path):
    """Request a presigned URL, upload the MP4 bytes, and confirm completion."""
    if not os.path.isfile(file_path):
        print(f"[!] Video file not found: {file_path}", file=sys.stderr)
        return None

    size = os.path.getsize(file_path)
    if size <= 0:
        print("[!] Video file is empty; refusing to upload.", file=sys.stderr)
        return None

    filename = os.path.basename(file_path)
    mime = "video/mp4"
    print(f"[*] Requesting presigned URL for {filename} ({size / (1024 * 1024):.2f} MB)...")
    res = uplika_request("/v1/media/presign", method="POST", payload={
        "fileName": filename,
        "contentType": mime,
        "bytes": size,
    })

    if not isinstance(res, dict) or not res.get("uploadUrl") or not res.get("id"):
        print("[!] Uplika did not return both uploadUrl and media id; stopping.", file=sys.stderr)
        return None

    upload_url = res["uploadUrl"]
    media_id = res["id"]
    print(f"[*] Received Uplika media ID: {media_id}")

    print("[*] Uploading MP4 binary to the presigned storage URL...")
    try:
        with open(file_path, "rb") as video_file:
            request = urllib.request.Request(
                upload_url,
                data=video_file.read(),
                headers={"Content-Type": mime},
                method="PUT",
            )
        with urllib.request.urlopen(request, timeout=180) as response:
            if response.status not in (200, 201, 204):
                print(f"[!] Storage upload returned HTTP {response.status}.", file=sys.stderr)
                return None
            print(f"[*] Binary upload completed (HTTP {response.status}).")
    except Exception as exc:
        print(f"[!] Binary upload failed: {exc}", file=sys.stderr)
        return None

    print(f"[*] Confirming media upload completion for media ID {media_id}...")
    completion = uplika_request(f"/v1/media/{media_id}/complete", method="POST", payload={})
    if not isinstance(completion, dict):
        print("[!] Uplika did not confirm media completion; publish aborted.", file=sys.stderr)
        return None
    if completion.get("success") is False or completion.get("error"):
        print("[!] Uplika reported media completion failure; publish aborted.", file=sys.stderr)
        return None

    print("[*] Uplika returned a completion response.")
    return media_id


def publish_reel(file_path, caption, account_id=None):
    """Upload the video and request publication of an Instagram Reel."""
    target_account = account_id or ACCOUNT_ID
    if not target_account:
        print("[!] UPLIKA_ACCOUNT_ID is not configured.", file=sys.stderr)
        return None

    media_id = presign_and_upload(file_path)
    if not media_id:
        print("[!] Media upload was not confirmed; aborting publish.", file=sys.stderr)
        return None

    payload = {
        "accountIds": [target_account],
        "content": caption,
        "mediaIds": [media_id],
        "options": {
            "instagram": {
                "contentType": "reel",
                "shareToFeed": True,
            }
        },
        "wait": False,
    }
    print("[*] Sending Reel publish request to Uplika...")
    result = uplika_request("/v1/posts", method="POST", payload=payload)
    if not isinstance(result, dict):
        print("[!] Uplika did not return a valid post response.", file=sys.stderr)
        return None
    link = extract_permalink(result)
    if link:
        print(f"[*] Instagram Reel URL returned: {link}")
    return result


def poll_publish_status(post_id=None, timeout_seconds=120, interval=5):
    """Poll Uplika until a public permalink or terminal failure is reported."""
    print(f"[*] Polling Instagram post status (Target: {post_id or 'latest'})...")
    start = time.time()
    while time.time() - start < timeout_seconds:
        time.sleep(interval)
        path = f"/v1/posts/{post_id}" if post_id else "/v1/posts"
        result = uplika_request(path)
        if not isinstance(result, dict):
            continue

        candidate = result
        if not post_id:
            items = result.get("data")
            if not isinstance(items, list) or not items or not isinstance(items[0], dict):
                continue
            candidate = items[0]

        status = (candidate.get("status") or candidate.get("state")
                  or candidate.get("publishStatus") or "unknown")
        permalink = extract_permalink(candidate)
        print(f"[*] Status: {status} | Link: {permalink or 'not returned yet'}")
        if permalink:
            return permalink
        if str(status).lower() in ("failed", "rejected", "error", "cancelled"):
            print("[!] Uplika reports a terminal publish failure.", file=sys.stderr)
            return None
    return None


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python uplika_uploader.py <video_path> <caption>")
        sys.exit(2)
    result = publish_reel(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result else 1)
