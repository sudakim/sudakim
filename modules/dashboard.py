# modules/dashboard.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from .ui import date_picker_with_toggle, nearest_anchor_date_today, to_datestr, DOT

def _props_summary_for_content(cid: str) -> str:
    items = st.session_state.get("content_props", {}).get(cid, []) or []
    if not items: return "소품 0개"
    parts=[f"{DOT.get(p.get('status','예정'),'🔴')}{p.get('name','')}({p.get('quantity',1)}개)" for p in items]
    return f"소품 {len(items)}개 · " + ", ".join(parts)

def render():
    st.subheader("🧭 대시보드 (요약)")
    sel = date_picker_with_toggle("기준 날짜", key="dash", default=nearest_anchor_date_today())
    dkey = to_datestr(sel)

    daily = st.session_state.get("daily_contents", {}).get(dkey, [])
    scheds = st.session_state.get("schedules", {}).get(dkey, [])

    rows=[]
    if scheds:
        for s in scheds:
            title = s.get("title","")
            cid = s.get("cid")
            perf = ""
            if cid:
                for c in daily:
                    if c.get("id")==cid:
                        perf = ", ".join(c.get("performers", [])); break
            else:
                for c in daily:
                    if c.get("title")==title:
                        perf = ", ".join(c.get("performers", [])); cid=c.get("id"); break
            rows.append({
                "시간": f"{s.get('start','')}~{s.get('end','')}",
                "유형": s.get("type",""),
                "제목": title or "(제목 없음)",
                "출연": perf,
                "소품현황": _props_summary_for_content(cid) if cid else "소품 0개"
            })
    else:
        for c in daily:
            cid = c.get("id")
            rows.append({
                "시간":"-","유형":"-",
                "제목": c.get("title","(제목 없음)"),
                "출연": ", ".join(c.get("performers", [])),
                "소품현황": _props_summary_for_content(cid)
            })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
