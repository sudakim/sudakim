# modules/timetable.py
from __future__ import annotations
import streamlit as st
from datetime import datetime, date, time
from typing import List, Dict, Any, Optional

from modules import storage
from .ui import date_picker_with_toggle, nearest_anchor_date_today, to_datestr

# ========== 내부 유틸 ==========

def _ensure_state():
    st.session_state.setdefault("daily_contents", {})
    st.session_state.setdefault("schedules", {})

def _collect_days_for_nav() -> List[date]:
    """컨텐츠/스케줄 중 하나라도 있는 날짜만 정렬"""
    days = set()
    for k, v in (st.session_state.get("daily_contents") or {}).items():
        if v:
            try: days.add(datetime.strptime(k, "%Y-%m-%d").date())
            except: pass
    for k, v in (st.session_state.get("schedules") or {}).items():
        if v:
            try: days.add(datetime.strptime(k, "%Y-%m-%d").date())
            except: pass
    return sorted(days)

def _final_or_draft_preview(content: Dict[str, Any], max_lines: int = 3) -> str:
    """기획안 요약: 최종안 or (초안) + 3줄 제한"""
    def _preview(s: str) -> str:
        if not s: return ""
        lines = [ln.rstrip() for ln in str(s).splitlines()]
        return "\n".join(lines[:max_lines])
    final = (content.get("final") or "").strip()
    if final:
        return _preview(final)
    draft = (content.get("draft") or "").strip()
    if draft:
        return "(초안) " + _preview(draft)
    return ""

def _sync_schedule_details_from_planning(dkey: str) -> bool:
    """
    스케줄(details)을 기획안 내용으로 동기화.
    cid가 있는 항목만 대상. 변경이 있으면 저장 필요 True.
    """
    changed = False
    day_sched = st.session_state.get("schedules", {}).get(dkey, []) or []
    contents = st.session_state.get("daily_contents", {}).get(dkey, []) or []
    by_id = {c.get("id"): c for c in contents}
    for s in day_sched:
        cid = s.get("cid")
        if cid and cid in by_id:
            want = _final_or_draft_preview(by_id[cid])
            if (s.get("details") or "") != want:
                s["details"] = want
                if by_id[cid].get("title"):
                    s["title"] = by_id[cid]["title"]
                changed = True
    return changed

def _sort_schedules_inplace(dkey: str):
    """시작시간 오름차순 정렬"""
    def _to_minutes(t: str) -> int:
        try:
            hh, mm = t.split(":")
            return int(hh)*60 + int(mm)
        except:
            return 0
    st.session_state["schedules"][dkey].sort(key=lambda r: _to_minutes(r.get("start","00:00")))

def _time_to_str(t: time) -> str:
    return f"{t.hour:02d}:{t.minute:02d}"

def _parse_time(s: str) -> time:
    try:
        hh, mm = [int(x) for x in s.split(":")]
        return time(hh, mm)
    except:
        return time(0,0)

# ========== 메인 렌더 ==========

def render():
    _ensure_state()
    st.subheader("🧭 타임테이블")

    # 날짜 선택 (토글 달력, 기본 OFF)
    sel = date_picker_with_toggle("날짜 선택", key="tt", default=nearest_anchor_date_today())
    dkey = to_datestr(sel)

    # 이전/다음 (콘텐츠 or 스케줄 있는 날만)
    days = _collect_days_for_nav()
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        pass
    with c1:
        if st.button("◀ 이전", use_container_width=True, disabled=not days):
            prev = [d for d in days if d < sel]
            st.session_state["tt_nav"] = prev[-1] if prev else (days[0] if days else sel)
            st.rerun()
    with c3:
        if st.button("다음 ▶", use_container_width=True, disabled=not days):
            nxt = [d for d in days if d > sel]
            st.session_state["tt_nav"] = nxt[0] if nxt else (days[-1] if days else sel)
            st.rerun()

    # 동기화: content 변경 시 details 업데이트
    if _sync_schedule_details_from_planning(dkey):
        storage.autosave_maybe()

    st.markdown("")

    # ====== 일정 추가 ======
    with st.expander("➕ 일정 추가", expanded=True):
        mode = st.radio("콘텐츠 선택 방식", ["콘텐츠에서 선택", "직접 입력"], horizontal=True, key="tt_add_mode")

        # 공통: 시간/유형
        t1, t2 = st.columns(2)
        with t1:
            start_t = st.time_input("시작", value=_parse_time("12:40"), key="tt_add_start")
        with t2:
            end_t   = st.time_input("종료", value=_parse_time("13:30"), key="tt_add_end")

        type_options = ["촬영", "회의", "이동", "기타"]
        typ = st.selectbox("유형", type_options, index=0, key="tt_add_type")

        cid: Optional[str] = None
        title: str = ""
        details: str = ""

        if mode == "콘텐츠에서 선택":
            contents = st.session_state.get("daily_contents", {}).get(dkey, []) or []
            options = [f"#{i+1}. {c.get('title','제목없음')}" for i, c in enumerate(contents)]
            idx = st.selectbox("콘텐츠", options=options if options else ["(없음)"], index=0 if options else None, key="tt_add_select")
            if options:
                c = contents[options.index(idx)]
                cid = c.get("id")
                title = c.get("title","")
                details = _final_or_draft_preview(c)
            disp_title = st.text_input("표시 제목(비우면 콘텐츠 제목 사용)", value=title, key="tt_add_title_from_content")
            if disp_title.strip():
                title = disp_title.strip()
        else:
            title = st.text_input("표시 제목(직접 입력)", key="tt_add_title_direct")
            details = st.text_area("세부 내용(선택)", key="tt_add_details_direct")

        if st.button("추가", type="primary", key="tt_add_btn"):
            st.session_state["schedules"].setdefault(dkey, [])
            st.session_state["schedules"][dkey].append({
                "start": _time_to_str(start_t),
                "end": _time_to_str(end_t),
                "type": typ,
                "title": title or "(제목없음)",
                "cid": cid,
                "details": details,
            })
            _sort_schedules_inplace(dkey)
            storage.autosave_maybe()
            st.success("일정이 추가되었습니다.")
            st.rerun()

    st.markdown("---")

    # ====== 일정 목록(수정 가능) ======
    schedules: List[Dict[str, Any]] = st.session_state.get("schedules", {}).get(dkey, []) or []
    if not schedules:
        st.info("이 날짜의 일정이 없습니다.")
        return

    st.caption("🔁 항목을 수정하면 즉시 저장되고, 시간 수정 시 자동으로 순서가 재정렬됩니다.")
    type_options = ["촬영", "회의", "이동", "기타"]

    for i, s in enumerate(list(schedules)):  # copy for safe iteration
        with st.expander(f"{s.get('start','--:--')}~{s.get('end','--:--')} · {s.get('title','(제목없음)')}", expanded=False):
            r1c1, r1c2, r1c3, r1c4 = st.columns([1,1,1.2,0.6])
            with r1c1:
                new_start = st.time_input("시작", value=_parse_time(s.get("start","00:00")), key=f"tt_start_{i}")
            with r1c2:
                new_end = st.time_input("종료", value=_parse_time(s.get("end","00:00")), key=f"tt_end_{i}")
            with r1c3:
                cur_type = s.get("type", "촬영")
                try:
                    idx_type = type_options.index(cur_type)
                except ValueError:
                    idx_type = 0  # 옵션에 없으면 기본 '촬영'
                new_type = st.selectbox("유형", type_options, index=idx_type, key=f"tt_type_{i}")
            with r1c4:
                # 삭제
                st.write("")
                if st.button("🗑️ 삭제", key=f"tt_del_{i}"):
                    st.session_state["schedules"][dkey].pop(i)
                    storage.autosave_maybe()
                    st.rerun()

            # 제목 / 세부
            t1, t2 = st.columns([1.2, 2.0])
            with t1:
                new_title = st.text_input("표시 제목", value=s.get("title",""), key=f"tt_title_{i}")
            with t2:
                link_info = " (기획안 연동)" if s.get("cid") else ""
                new_details = st.text_area(f"세부{link_info}", value=s.get("details",""), height=110, key=f"tt_details_{i}")

            # 변경 감지 → 저장 및 정렬
            changed = (
                _time_to_str(new_start) != s.get("start") or
                _time_to_str(new_end)   != s.get("end") or
                new_type                != s.get("type") or
                new_title               != s.get("title") or
                new_details             != s.get("details")
            )
            if changed:
                s["start"]   = _time_to_str(new_start)
                s["end"]     = _time_to_str(new_end)
                s["type"]    = new_type
                s["title"]   = new_title
                s["details"] = new_details
                _sort_schedules_inplace(dkey)
                storage.autosave_maybe()
                st.rerun()

    # 하단 요약 테이블(읽기용)
    st.markdown("---")
    import pandas as pd
    df = pd.DataFrame(st.session_state["schedules"][dkey])
    if "cid" in df.columns:
        df.rename(columns={"cid":"content_id"}, inplace=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
