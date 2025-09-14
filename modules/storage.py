# modules/storage.py
from __future__ import annotations
import streamlit as st
import json, os
from datetime import datetime
from . import github_store

STORE_PATH = "data_store.json"
CURRENT_KEYS = ["daily_contents", "content_props", "schedules", "upload_status"]
LEGACY_MAP = {
    "contents": "daily_contents",
    "props": "content_props",
    "schedules": "schedules",
    "upload_status": "upload_status",
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
    # 최초 1회만 외부 저장소에서 로드하도록 가드 플래그
    st.session_state.setdefault("_loaded_once", False)
    # 마지막 스냅샷(변경 감지용)
    st.session_state.setdefault("_last_snapshot", None)
    # 주기 저장 타임스탬프(초)
    st.session_state.setdefault("_last_autosave_ts", 0.0)

def _hydrate(data: dict):
    if not isinstance(data, dict):
        return
    for k in CURRENT_KEYS:
        if k in data:
            st.session_state[k] = data[k]
    for old, new in LEGACY_MAP.items():
        if old in data and not st.session_state.get(new):
            st.session_state[new] = data[old]
    st.session_state["_last_saved"] = data.get("_last_saved")

def load_state():
    _ensure_defaults()

    # 이미 한 번 로드했다면 외부로부터 다시 덮어쓰지 않음(사용자 입력 보존)
    if st.session_state.get("_loaded_once"):
        return

    # A. Gist
    try:
        if hasattr(github_store, "gist_load"):
            g = github_store.gist_load()
            if g:
                _hydrate(g)
                st.session_state["_storage_source"] = "gist"
                st.session_state["_loaded_once"] = True
                return
    except Exception as e:
        try:
            st.sidebar.warning(f"Gist 로드 실패: {e}")
        except Exception:
            pass

    # B. Local
    if os.path.exists(STORE_PATH):
        try:
            with open(STORE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            _hydrate(data)
            st.session_state["_storage_source"] = "local"
            st.session_state["_loaded_once"] = True
            return
        except Exception as e:
            try:
                st.sidebar.warning(f"Local 로드 실패: {e}")
            except Exception:
                pass

    # 외부에서 불러올 데이터가 없어도 중복 로드를 막기 위해 True로 설정
    st.session_state["_loaded_once"] = True

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

    ok = False
    if st.session_state.get("_storage_source") == "gist" and hasattr(github_store, "gist_save"):
        try:
            ok = github_store.gist_save(payload)
        except Exception as e:
            st.sidebar.error(f"Gist 저장 실패: {e}")

    if not ok and hasattr(github_store, "gist_save"):
        try:
            if github_store.gist_save(payload):
                ok = True
                st.session_state["_storage_source"] = "gist"
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

def _snapshot_str() -> str:
    """현재 핵심 상태를 정렬된 JSON 문자열로 반환(변경 감지용)"""
    core = {
        "daily_contents": st.session_state.get("daily_contents", {}),
        "content_props": st.session_state.get("content_props", {}),
        "schedules": st.session_state.get("schedules", {}),
        "upload_status": st.session_state.get("upload_status", {}),
    }
    try:
        return json.dumps(core, ensure_ascii=False, sort_keys=True)
    except Exception:
        # 직렬화 실패 시에도 안전하게 문자열화
        return str(core)

def autosave_on_diff():
    """상태가 변경되었으면 자동 저장"""
    try:
        snap = _snapshot_str()
        if snap != st.session_state.get("_last_snapshot"):
            if st.session_state.get("_autosave", True):
                save_state()
            st.session_state["_last_snapshot"] = snap
    except Exception:
        pass

def autosave_interval_maybe(seconds: int = 20):
    """주기적으로 자동 저장(실행 주기 내에서만 작동, 실제 타이머 아님)"""
    try:
        import time
        now = time.time()
        prev = float(st.session_state.get("_last_autosave_ts") or 0.0)
        if now - prev >= max(1, seconds):
            if st.session_state.get("_autosave", True):
                save_state()
            st.session_state["_last_autosave_ts"] = now
    except Exception:
        pass
