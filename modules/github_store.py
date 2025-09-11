# modules/github_store.py
from __future__ import annotations
import os, json, requests

def _get(name: str, default=None):
    try:
        import streamlit as st
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name.upper(), default)

def _auth_headers():
    tok = _get("gh_token") or _get("github_token")
    if not tok:
        raise RuntimeError("GitHub 토큰(gh_token/github_token)이 설정되어 있지 않습니다.")
    return {"Authorization": f"token {tok}", "Accept": "application/vnd.github+json"}

def gist_load():
    gist_id = _get("gist_id")
    if not gist_id:
        return None

    r = requests.get(f"https://api.github.com/gists/{gist_id}", headers=_auth_headers(), timeout=20)
    r.raise_for_status()
    data = r.json()
    files = data.get("files") or {}

    # 파일명 우선순위: secrets.gist_filename > youtube_data.json > data_store.json > (그 외 무시)
    prefer = _get("gist_filename")
    candidates = []
    if prefer: candidates.append(prefer)
    candidates += ["youtube_data.json", "data_store.json"]

    target = None
    for name in candidates:
        # 대소문자 안전 비교
        for k in files.keys():
            if k.lower() == name.lower():
                target = k
                break
        if target: break

    if not target:
        # 일치 파일 못 찾으면 실패 (gistfile1.txt 같은 건 무시)
        return None

    meta = files[target]
    if meta.get("truncated") and meta.get("raw_url"):
        raw = requests.get(meta["raw_url"], timeout=20).text
        return json.loads(raw)
    content = meta.get("content", "")
    return json.loads(content) if content else None

def gist_save(payload: dict):
    gist_id = _get("gist_id")
    if not gist_id:
        return False
    fname = _get("gist_filename", "youtube_data.json")
    body = {"files": {fname: {"content": json.dumps(payload, ensure_ascii=False, indent=2)}}}
    r = requests.patch(f"https://api.github.com/gists/{gist_id}", headers=_auth_headers(), json=body, timeout=20)
    r.raise_for_status()
    return True

# Repo는 안 쓰면 스텁
def repo_load():
    return None
def repo_save(payload: dict):
    return False
