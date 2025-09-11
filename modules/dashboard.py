# modules/dashboard.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from datetime import date
from .ui import pick_date_with_markers, nearest_anchor_date_today, to_datestr, DOT


def _props_summary_for_content(cid: str) -> str:
    items = st.session_state.get("content_props", {}).get(cid, []) or []
    if not items:
        return "소품 0개"
    parts = []
    for p in items:
        name = p.get("name","")
        qty  = p.get("quantity", 1)
        stt  = p.get("status", "예정")
        parts.append(f"{DOT.get(stt,'🔴')}{name}({qty}개)")
    return f"소품 {len(items)}개 · " + ", ".join(parts)

def render():
    st.subheader("🧭 대시보드 (요약)")
    anchor = nearest_anchor_date_today()
    sel = pick_date_with_markers(selected=anchor, key="dash_calendar")
    dkey = to_datestr(sel)

    daily = st.session_state.get("daily_contents", {}).get(dkey, [])
    scheds = st.session_state.get("schedules", {}).get(dkey, [])

    # 스케줄 표 생성 (시간, 유형, 제목, 출연, 소품현황)
    rows = []
    # 스케줄이 없으면 콘텐츠 기준으로라도 보여줌
    if scheds:
        for s in scheds:
            title = s.get("title","")
            cid   = s.get("cid")
            # cid가 없을 수도 있으니 제목으로 매칭 보조
            perf = ""
            if cid:
                for c in daily:
                    if c.get("id")==cid:
                        perf = ", ".join(c.get("performers", []))
                        break
            else:
                for c in daily:
                    if c.get("title")==title:
                        perf = ", ".join(c.get("performers", []))
                        cid = c.get("id")
                        break
            props_info = _props_summary_for_content(cid) if cid else "소품 0개"
            rows.append({
                "시간": f"{s.get('start','')}~{s.get('end','')}",
                "유형": s.get("type",""),
                "제목": title or "(제목 없음)",
                "출연": perf,
                "소품현황": props_info
            })
    else:
        # 스케줄이 없을 때: 콘텐츠만 한 줄씩
        for idx, c in enumerate(daily, start=1):
            cid = c.get("id")
            rows.append({
                "시간": "-",
                "유형": "-",
                "제목": c.get("title","(제목 없음)"),
                "출연": ", ".join(c.get("performers", [])),
                "소품현황": _props_summary_for_content(cid)
            })

    df = pd.DataFrame(rows)
    st.markdown(f"### 📅 {sel.strftime('%m월 %d일')} 요약")
    st.dataframe(df, use_container_width=True, hide_index=True)
