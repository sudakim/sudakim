# modules/ui.py
from __future__ import annotations
import streamlit as st
from datetime import date, datetime
from typing import List
from .ui_enhanced import (
    ThemeManager, modern_card, modern_grid, modern_sidebar,
    loading_animation, success_animation, error_animation, STATUS_STYLES
)

# 기존 UI 유틸리티 유지 (하위호환성)
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
    개선된 날짜 선택기 with 토글
    모던한 디자인과 함께 개선된 사용자 경험 제공
    """
    # 테마 적용
    theme = ThemeManager()
    theme.apply_theme()
    
    days = collect_content_dates()
    anchor = default or nearest_anchor_date_today()
    sel_key = f"{key}_selected"

    st.session_state.setdefault(sel_key, anchor)
    selected = st.session_state[sel_key]

    # 모던한 헤더 스타일
    st.markdown(f"""
    <div style="background-color: {theme.colors['surface']}; 
                padding: 15px; border-radius: 12px; 
                border: 1px solid {theme.colors['border']}; 
                margin: 10px 0;">
        <h4 style="color: {theme.colors['primary']}; margin: 0 0 10px 0;">{title}</h4>
    """, unsafe_allow_html=True)
    
    # 모던한 버튼 레이아웃
    c1, c2, c3, c4 = st.columns([0.3, 0.4, 0.15, 0.15])
    with c1:
        show = st.toggle("📅 달력", value=False, key=f"{key}_toggle")
    with c2:
        st.caption(f"📅 {selected.strftime('%Y년 %m월 %d일')}")
    with c3:
        if st.button("◀", key=f"{key}_prev", use_container_width=True, disabled=not days):
            if days:
                i = max(0, next((idx for idx,d in enumerate(days) if d>=selected), len(days))-1)
                st.session_state[sel_key] = days[i-1] if i>0 else days[0]
                selected = st.session_state[sel_key]
    with c4:
        if st.button("▶", key=f"{key}_next", use_container_width=True, disabled=not days):
            if days:
                i = next((idx for idx,d in enumerate(days) if d>selected), None)
                st.session_state[sel_key] = days[i] if i is not None else days[-1]
                selected = st.session_state[sel_key]

    if show:
        selected = _fullcalendar(selected, key)

    st.session_state[sel_key] = selected
    
    # 닫는 태그
    st.markdown("</div>", unsafe_allow_html=True)
    
    return selected
