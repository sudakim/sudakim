# modules/github_store.py
from __future__ import annotations
import os, json, base64, requests

def _get(name: str, default=None):
    """st.secrets 우선, 없으면 환경변수 조회"""
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

# -------- Gist --------
def gist_load():
    gist_id = _get("gist_id")
    if not gist_id:
        return None
    r = requests.get(f"https://api.github.com/gists/{gist_id}", headers=_auth_headers(), timeout=20)
    r.raise_for_status()
    data = r.json()
    files = data.get("files") or {}

    # 파일명 선택: secrets.gist_filename > youtube_data.json > data_store.json > 첫 파일
    prefer = _get("gist_filename")
    fname = (prefer if prefer and prefer in files else
             "youtube_data.json" if "youtube_data.json" in files else
             "data_store.json" if "data_store.json" in files else
             (next(iter(files.keys()), None) if files else None))
    if not fname:
        return None

    meta = files[fname]
    # 큰 파일이면 raw_url로 다시 읽기
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

# -------- Repo (옵션: 사용 안 하면 스텁) --------
def repo_load():
    return None

def repo_save(payload: dict):
    return False
