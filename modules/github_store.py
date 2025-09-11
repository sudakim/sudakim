# modules/github_store.py
from __future__ import annotations
import os, json, base64, requests

def _get(name: str, default=None):
    # st.secrets가 없을 수도 있으니 환경변수도 함께 확인
    try:
        import streamlit as st
        if name in st.secrets: return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name.upper(), default)

def _auth_headers():
    tok = _get("gh_token")
    if not tok: raise RuntimeError("gh_token이 설정되어 있지 않습니다.")
    return {"Authorization": f"token {tok}", "Accept": "application/vnd.github+json"}

# ---------- Gist ----------
def gist_load():
    gist_id = _get("gist_id")
    if not gist_id: return None
    filename = _get("gist_filename", "data_store.json")
    r = requests.get(f"https://api.github.com/gists/{gist_id}", headers=_auth_headers(), timeout=20)
    r.raise_for_status()
    data = r.json()
    files = data.get("files") or {}
    if filename not in files:  # 파일명이 다르면 그냥 첫 파일을 사용
        if files:
            content = next(iter(files.values())).get("content", "")
        else:
            return None
    else:
        content = files[filename].get("content", "")
    try:
        return json.loads(content) if content else None
    except Exception:
        return None

def gist_save(payload: dict):
    gist_id = _get("gist_id")
    if not gist_id: return False
    filename = _get("gist_filename", "data_store.json")
    body = {"files": {filename: {"content": json.dumps(payload, ensure_ascii=False, indent=2)}}}
    r = requests.patch(f"https://api.github.com/gists/{gist_id}", headers=_auth_headers(), json=body, timeout=20)
    r.raise_for_status()
    return True

# ---------- Repo file ----------
def repo_load():
    repo = _get("gh_repo")
    if not repo: return None
    branch = _get("gh_branch", "main")
    path = _get("gh_file", "data_store.json")
    r = requests.get(f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}",
                     headers=_auth_headers(), timeout=20)
    if r.status_code == 404: return None
    r.raise_for_status()
    b64 = r.json().get("content")
    if not b64: return None
    raw = base64.b64decode(b64).decode("utf-8", "ignore")
    try:
        return json.loads(raw)
    except Exception:
        return None

def repo_save(payload: dict):
    repo = _get("gh_repo")
    if not repo: return False
    branch = _get("gh_branch", "main")
    path = _get("gh_file", "data_store.json")

    # 파일의 sha 필요
    get = requests.get(f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}",
                       headers=_auth_headers(), timeout=20)
    sha = get.json().get("sha") if get.status_code == 200 else None
    body = {
        "message": "auto: update data_store.json",
        "content": base64.b64encode(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")).decode("ascii"),
        "branch": branch
    }
    if sha: body["sha"] = sha
    put = requests.put(f"https://api.github.com/repos/{repo}/contents/{path}",
                       headers=_auth_headers(), json=body, timeout=20)
    put.raise_for_status()
    return True
