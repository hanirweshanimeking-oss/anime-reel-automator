#!/usr/bin/env python3
"""
Autonomous Google Drive Streamer & Downloader for Cloud Automation.
Uses OAuth2 Refresh Token to authenticate and download video clips on-demand.
Standard library only (urllib) - zero external dependencies required.
"""

import os
import sys
import json
import re
import urllib.request
import urllib.parse

# Default OAuth Client & Refresh Token credentials
DEFAULT_CLIENT_ID = ""
DEFAULT_CLIENT_SECRET = ""
DEFAULT_REFRESH_TOKEN = ""

CLIENT_ID = os.environ.get("GDRIVE_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("GDRIVE_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.environ.get("GDRIVE_REFRESH_TOKEN", "").strip()

# Google Drive folder IDs for the 3000+ Anime Reel Bundle
BUNDLE_FOLDERS = {
    "1001-1500": "1OGB_O-clSTEEgCiLUA7-DCcXhqUZ8lWr",
    "1501-2000": "1PwXygAShizDABbVY38aQhoUKEE2r4pop",
    "2001-2500": "1Vtwqe6dgclx5c6wYGTLtObooapHsbLkp",
    "2501-3000": "14hWYMcdjPa2F0cMeE0ZcarBM-Wqrr0rQ"
}

_CACHED_ACCESS_TOKEN = None


def get_access_token():
    """Exchanges persistent refresh token for an active Google Drive API access token."""
    global _CACHED_ACCESS_TOKEN
    if _CACHED_ACCESS_TOKEN:
        return _CACHED_ACCESS_TOKEN

    token_url = "https://oauth2.googleapis.com/token"
    data = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }).encode("utf-8")

    req = urllib.request.Request(token_url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            _CACHED_ACCESS_TOKEN = res.get("access_token")
            return _CACHED_ACCESS_TOKEN
    except Exception as e:
        print(f"[!] Google Drive OAuth token refresh failed: {e}", file=sys.stderr)
        return None


def resolve_folder_id(filename, rel_dir=""):
    """Determines which Google Drive folder holds the clip."""
    # Check rel_dir first
    for key, fid in BUNDLE_FOLDERS.items():
        if key in rel_dir:
            return fid

    # Extract number from filename (e.g. 2518 from Digiproducthub.in (2518).mp4)
    nums = re.findall(r"\d+", filename)
    if nums:
        n = int(nums[0])
        if 1001 <= n <= 1500:
            return BUNDLE_FOLDERS["1001-1500"]
        elif 1501 <= n <= 2000:
            return BUNDLE_FOLDERS["1501-2000"]
        elif 2001 <= n <= 2500:
            return BUNDLE_FOLDERS["2001-2500"]
        elif 2501 <= n <= 3000:
            return BUNDLE_FOLDERS["2501-3000"]

    return None


def search_file(filename, rel_dir=""):
    """Finds file metadata from Google Drive."""
    token = get_access_token()
    if not token:
        return None

    target_folder_id = resolve_folder_id(filename, rel_dir)
    nums = re.findall(r"\d+", filename)
    num_str = nums[0] if nums else ""

    candidate_queries = []
    if target_folder_id and num_str:
        candidate_queries.append(f"'{target_folder_id}' in parents and name contains '{num_str}' and trashed = false")
    if target_folder_id:
        candidate_queries.append(f"'{target_folder_id}' in parents and trashed = false")
    if num_str:
        parents_clause = " or ".join([f"'{fid}' in parents" for fid in BUNDLE_FOLDERS.values()])
        candidate_queries.append(f"({parents_clause}) and name contains '{num_str}' and trashed = false")

    for q in candidate_queries:
        url = f"https://www.googleapis.com/drive/v3/files?q={urllib.parse.quote(q)}&fields=files(id,name,size,mimeType)"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                files = data.get("files", [])
                for f in files:
                    # Match filename or number
                    if f["name"] == filename or (num_str and f"({num_str})" in f["name"]):
                        return f
                if files and num_str:
                    return files[0]
        except Exception as e:
            print(f"[!] Error querying Google Drive ({q}): {e}", file=sys.stderr)
            continue

    return None


def download_file(filename, destination_dir, rel_dir=""):
    """Downloads a video file from Google Drive into destination_dir."""
    dest_path = os.path.join(destination_dir, filename)
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
        return dest_path

    os.makedirs(destination_dir, exist_ok=True)
    file_info = search_file(filename, rel_dir)
    if not file_info:
        print(f"[!] File '{filename}' not found in Google Drive.", file=sys.stderr)
        return None

    file_id = file_info["id"]
    size_mb = int(file_info.get("size", 0)) / (1024 * 1024)
    print(f"[*] Downloading '{filename}' ({size_mb:.2f} MB) from Google Drive (ID: {file_id})...")

    token = get_access_token()
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

    try:
        with urllib.request.urlopen(req, timeout=60) as resp, open(dest_path, "wb") as out_f:
            while True:
                chunk = resp.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                out_f.write(chunk)
        print(f"[✓] Downloaded '{filename}' successfully to {dest_path}")
        return dest_path
    except Exception as e:
        print(f"[!] Failed to download '{filename}' from Google Drive: {e}", file=sys.stderr)
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return None


if __name__ == "__main__":
    test_file = "Digiproducthub.in (2501).mp4"
    out_dir = "/tmp/gdrive_test"
    p = download_file(test_file, out_dir)
    print("Result path:", p)
    if p and os.path.exists(p):
        print(f"File verified: {os.path.getsize(p)} bytes")
