# modules/ui.py
from __future__ import annotations
import streamlit as st
from datetime import date, datetime
from typing import List

DOT = {"예정":"🔴","주문완료":"🟡","수령완료":"🟢"}
STATE_DOT = {"촬영전":"🔵","촬영완료":"🟡","편집완료":"🟠","업로드완료":"🟢"}

def to_datestr(d: date) -> str:
    return d.strftime("%Y-%m-%d")

def parse_date(ds: str) -> date | None:
    try:
        return datetime.strptime(ds, "%Y-%m-%d").date()
    except Exception:
        return None

def collect_content_dates() -> List[date]:
    dc = st.session_state.get("daily_contents", {}) or {}
    out=[]
    for k,v in dc.items():
        if v:
            d = parse_date(k)
            if d: out.append(d)
    return sorted(set(out))

def nearest_anchor_date_today() -> date:
    days = collect_content_dates()
    if not days:
        return date.today()
    today = date.today()
    future = [d for d in days if d>=today]
    return future[0] if future else days[-1]

def _fullcalendar(selected: date, key: str) -> date:
    # 있는 경우에만 사용, 없으면 date_input로 폴백
    try:
        from streamlit_calendar import calendar
    except Exception:
        return st.date_input("날짜", value=selected, key=f"{key}_di")
    events=[{"start": to_datestr(d),"end": to_datestr(d),"display":"background","color":"rgba(255,76,76,.35)"} for d in collect_content_dates()]
    options={
        "locale":"ko","initialView":"dayGridMonth","initialDate":to_datestr(selected),
        "height":520,"events":events,"headerToolbar":{"left":"prev,next today","center":"title","right":"dayGridMonth,listWeek"}
    }
    ret = calendar(options=options, key=f"{key}_cal")
    if isinstance(ret, dict) and ret.get("dateClick"):
        ds = ret["dateClick"].get("dateStr")
        d  = parse_date(ds) if ds else None
        if d: return d
    return selected

def date_picker_with_toggle(title: str, key: str, default: date | None = None) -> date:
    """
    - 기본은 숨김(토글 OFF)
    - 오늘 기준 가장 가까운 날짜를 기본 선택
    - 이전/다음 버튼으로 콘텐츠 있는 날짜만 이동
    """
    days = collect_content_dates()
    anchor = default or nearest_anchor_date_today()
    sel_key = f"{key}_selected"

    st.session_state.setdefault(sel_key, anchor)
    selected = st.session_state[sel_key]

    st.markdown(f"**{title}**")
    c1, c2, c3, c4 = st.columns([0.25,0.25,0.25,0.25])
    with c1:
        show = st.toggle("📅 달력 표시", value=False, key=f"{key}_toggle")
    with c2:
        st.caption(selected.strftime("%Y/%m/%d"))
    with c3:
        if st.button("◀ 이전", key=f"{key}_prev", use_container_width=True, disabled=not days):
            if days:
                i = max(0, next((idx for idx,d in enumerate(days) if d>=selected), len(days))-1)
                st.session_state[sel_key] = days[i-1] if i>0 else days[0]
                selected = st.session_state[sel_key]
    with c4:
        if st.button("다음 ▶", key=f"{key}_next", use_container_width=True, disabled=not days):
            if days:
                i = next((idx for idx,d in enumerate(days) if d>selected), None)
                st.session_state[sel_key] = days[i] if i is not None else days[-1]
                selected = st.session_state[sel_key]

    if show:
        selected = _fullcalendar(selected, key)

    st.session_state[sel_key] = selected
    return selected
