# modules/storage.py
from __future__ import annotations
import streamlit as st
import json, os
from datetime import datetime
from . import github_store

STORE_PATH = "data_store.json"

# 현재 앱에서 쓰는 표준 키
CURRENT_KEYS = ["daily_contents", "content_props", "schedules", "upload_status"]

# 레거시 키 이름들(가능성 높은 후보들을 매핑)
LEGACY_MAP = {
    "contents_by_date": "daily_contents",
    "contentsByDate": "daily_contents",
    "props_by_content": "content_props",
    "propsByContent": "content_props",
    "timeline_by_date": "schedules",
    "timelineByDate": "schedules",
    "status_by_content": "upload_status",
    "statusByContent": "upload_status",
}

def _ensure_defaults():
    st.session_state.setdefault("daily_contents", {})
    st.session_state.setdefault("content_props", {})
    st.session_state.setdefault("schedules", {})
    st.session_state.setdefault("upload_status", {})
    st.session_state.setdefault("_autosave", True)
    st.session_state.setdefault("_last_saved", None)
    st.session_state.setdefault("_storage_source", None)  # 어디서 로드했는지

def _hydrate_from_dict(data: dict):
    """레거시 키를 현재 키로 매핑하여 세션에 주입"""
    if not isinstance(data, dict): return
    # 1) 정확히 같은 키면 그대로
    for k in CURRENT_KEYS:
        if k in data: st.session_state[k] = data[k]
    # 2) 레거시 키 매핑
    for old, new in LEGACY_MAP.items():
        if new in st.session_state and st.session_state[new]:  # 이미 채워졌으면 스킵
            continue
        if old in data:
            st.session_state[new] = data[old]

# modules/storage.py (load_state만 교체)
def load_state():
    _ensure_defaults()
    # A. Gist
    try:
        g = github_store.gist_load()
        if g:
            _hydrate(g)
            st.session_state["_storage_source"] = "gist"
            return
    except Exception as e:
        st.sidebar.warning(f"Gist 로드 실패: {e}")

    # B. Repo (함수 존재할 때만 시도)
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

    # 1) 우선 저장 대상: 로드 출처 우선 → Gist/Repo 설정값 우선 → Local
    target = st.session_state.get("_storage_source")

    ok = False
    if target == "gist":
        try:
            ok = github_store.gist_save(payload)
        except Exception as e:
            st.sidebar.error(f"Gist 저장 실패: {e}")
    elif target == "repo":
        try:
            ok = github_store.repo_save(payload)
        except Exception as e:
            st.sidebar.error(f"Repo 저장 실패: {e}")

    # 출처가 없거나 실패하면 설정값을 기준으로 다시 시도
    if not ok:
        # Gist 우선
        try:
            if github_store.gist_save(payload):
                ok = True
                st.session_state["_storage_source"] = "gist"
        except Exception:
            pass
    if not ok:
        try:
            if github_store.repo_save(payload):
                ok = True
                st.session_state["_storage_source"] = "repo"
        except Exception:
            pass

    # 그래도 안되면 로컬 파일
    if not ok:
        try:
            with open(STORE_PATH, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            st.session_state["_storage_source"] = "local"
            ok = True
        except Exception as e:
            st.sidebar.error(f"Local 저장 실패: {e}")

    if ok:
        st.session_state["_last_saved"] = payload["_last_saved"]

def autosave_maybe():
    if st.session_state.get("_autosave", True):
        save_state()
