# modules/storage.py
from __future__ import annotations
import streamlit as st
import json, os
from datetime import datetime
from . import github_store

STORE_PATH = "data_store.json"
CURRENT_KEYS = ["daily_contents", "content_props", "schedules", "upload_status"]
LEGACY_MAP = {
    # 원래 코드 호환
    "contents": "daily_contents",
    "props": "content_props",
    "schedules": "schedules",
    "upload_status": "upload_status",
    # 과거 다른 이름들까지 커버 가능
    "contents_by_date": "daily_contents",
    "props_by_content": "content_props",
    "timeline_by_date": "schedules",
    "status_by_content": "upload_status",
}

def _ensure_defaults():
    st.session_state.setdefault("daily_contents", {})
    st.session_state.setdefault("content_props", {})
    st.session_state.setdefault("schedules", {})
    st.session_state.setdefault("upload_status", {})
    st.session_state.setdefault("_autosave", True)
    st.session_state.setdefault("_last_saved", None)
    st.session_state.setdefault("_storage_source", None)

def _hydrate(data: dict):
    """레거시 키를 현재 키로 매핑하여 세션에 주입"""
    if not isinstance(data, dict):
        return
    # 현재 키 우선 주입
    for k in CURRENT_KEYS:
        if k in data:
            st.session_state[k] = data[k]
    # 레거시 → 현재 매핑
    for old, new in LEGACY_MAP.items():
        if old in data and not st.session_state.get(new):
            st.session_state[new] = data[old]
    st.session_state["_last_saved"] = data.get("_last_saved")

def load_state():
    _ensure_defaults()

    # A. Gist
    try:
        if hasattr(github_store, "gist_load"):
            g = github_store.gist_load()
            if g:
                _hydrate(g)
                st.session_state["_storage_source"] = "gist"
                return
    except Exception as e:
        st.sidebar.warning(f"Gist 로드 실패: {e}")

    # B. Repo (함수 있을 때만)
    try:
        if hasattr(github_store, "repo_load"):
            r = github_store.repo_load()
            if r:
                _hydrate(r)
                st.session_state["_storage_source"] = "repo"
                return
    except Exception as e:
        st.sidebar.warning(f"Repo 로드 실패: {e}")

    # C. Local
    if os.path.exists(STORE_PATH):
        try:
            with open(STORE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            _hydrate(data)
            st.session_state["_storage_source"] = "local"
            return
        except Exception as e:
            st.sidebar.warning(f"Local 로드 실패: {e}")

def _collect_payload() -> dict:
    return {
        "daily_contents": st.session_state.get("daily_contents", {}),
        "content_props": st.session_state.get("content_props", {}),
        "schedules": st.session_state.get("schedules", {}),
        "upload_status": st.session_state.get("upload_status", {}),
        "_last_saved": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

def save_state():
    _ensure_defaults()
    payload = _collect_payload()

    src = st.session_state.get("_storage_source")
    ok = False
    if src == "gist" and hasattr(github_store, "gist_save"):
        try:
            ok = github_store.gist_save(payload)
        except Exception as e:
            st.sidebar.error(f"Gist 저장 실패: {e}")
    elif src == "repo" and hasattr(github_store, "repo_save"):
        try:
            ok = github_store.repo_save(payload)
        except Exception as e:
            st.sidebar.error(f"Repo 저장 실패: {e}")

    # 출처 없거나 실패 → Gist → Repo → Local 순 재시도
    if not ok and hasattr(github_store, "gist_save"):
        try:
            if github_store.gist_save(payload):
                ok = True
                st.session_state["_storage_source"] = "gist"
        except Exception:
            pass
    if not ok and hasattr(github_store, "repo_save"):
        try:
            if github_store.repo_save(payload):
                ok = True
                st.session_state["_storage_source"] = "repo"
        except Exception:
            pass
    if not ok:
        try:
            with open(STORE_PATH, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            ok = True
            st.session_state["_storage_source"] = "local"
        except Exception as e:
            st.sidebar.error(f"Local 저장 실패: {e}")

    if ok:
        st.session_state["_last_saved"] = payload["_last_saved"]

def autosave_maybe():
    if st.session_state.get("_autosave", True):
        save_state()
