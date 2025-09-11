# modules/ui.py
from __future__ import annotations
import streamlit as st
from datetime import date, datetime
from typing import List, Dict

DOT = {"예정":"🔴","주문완료":"🟡","수령완료":"🟢"}
STATE_DOT = {"촬영전":"🔵","촬영완료":"🟡","편집완료":"🟠","업로드완료":"🟢"}

def to_datestr(d: date) -> str:
    return d.strftime("%Y-%m-%d")

def parse_date_str(ds: str) -> date | None:
    try:
        return datetime.strptime(ds, "%Y-%m-%d").date()
    except Exception:
        return None

def collect_content_dates() -> List[date]:
    """세션의 daily_contents에서 콘텐츠가 '있는' 날짜 리스트 수집"""
    res = []
    contents = st.session_state.get("daily_contents", {})
    for k, items in contents.items():
        if not items: 
            continue
        d = parse_date_str(k)
        if d: res.append(d)
    return sorted(set(res))

def nearest_anchor_date_today() -> date:
    """오늘 기준 가장 가까운 날짜 (미래/오늘 우선, 없으면 과거 최신, 없으면 오늘)"""
    days = collect_content_dates()
    if not days:
        return date.today()
    today = date.today()
    future_or_today = [d for d in days if d >= today]
    return future_or_today[0] if future_or_today else days[-1]

def pick_date_with_markers(selected: date, key: str) -> date:
    """
    FullCalendar로 마커가 보이는 캘린더 선택기.
    라이브러리가 없으면 st.date_input로 폴백.
    """
    content_days = collect_content_dates()
    try:
        from streamlit_calendar import calendar
    except Exception:
        return st.date_input("날짜 선택", value=selected, key=f"{key}_fallback")

    events = [{
        "start": to_datestr(d),
        "end": to_datestr(d),
        "display": "background",
        "color": "rgba(255, 76, 76, 0.35)"
    } for d in content_days]

    options = {
        "locale": "ko",
        "initialView": "dayGridMonth",
        "initialDate": to_datestr(selected),
        "height": 520,
        "events": events,
        "selectable": True,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,listWeek"
        },
        "firstDay": 0
    }
    cal = calendar(options=options, key=key)
    if isinstance(cal, dict) and cal.get("dateClick"):
        ds = cal["dateClick"].get("dateStr")
        picked = parse_date_str(ds) if ds else None
        if picked: 
            return picked
    return selected
