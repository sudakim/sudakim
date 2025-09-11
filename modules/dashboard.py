# modules/dashboard.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from .ui import pick_date_with_markers, nearest_anchor_date_today, to_datestr

# 상태 → 마커 (소품)
DOT = {"예정": "🔴", "주문완료": "🟡", "수령완료": "🟢"}

def _props_summary_for_content(cid: str | None) -> str:
    """콘텐츠 ID로 소품 요약 (🔴이름(개수), …)"""
    if not cid:
        return "소품 0개"
    items = st.session_state.get("content_props", {}).get(cid, []) or []
    if not items:
        return "소품 0개"
    parts = [
        f"{DOT.get(p.get('status','예정'),'🔴')}{p.get('name','')}({p.get('quantity',1)}개)"
        for p in items
    ]
    return f"소품 {len(items)}개 · " + ", ".join(parts)

def _final_preview(text: str, max_lines: int = 3) -> str:
    """최대 N줄까지 줄바꿈 유지하여 미리보기"""
    if not text:
        return ""
    lines = [ln.strip() for ln in str(text).splitlines()]
    lines = [ln for ln in lines if ln][:max_lines]
    return "\n".join(lines)

def render():
    st.subheader("🧭 대시보드 (요약)")

    # 기준 날짜 선택 (토글형 달력, 기본 OFF) — 오늘 기준 가장 가까운 날짜로 기본
    anchor = nearest_anchor_date_today()
    sel = pick_date_with_markers(selected=anchor, key="dash_calendar")
    dkey = to_datestr(sel)

    daily: List[Dict[str, Any]] = st.session_state.get("daily_contents", {}).get(dkey, []) or []
    scheds: List[Dict[str, Any]] = st.session_state.get("schedules", {}).get(dkey, []) or []

    # 빠른 조회용 인덱스
    by_id: Dict[str, Dict[str, Any]] = {c.get("id", ""): c for c in daily}

    rows: List[Dict[str, Any]] = []

    if scheds:
        # 타임테이블 순서대로 요약
        for s in scheds:
            cid = s.get("cid")
            title = s.get("title", "")
            perf = ""
            final_txt = ""

            if cid and cid in by_id:
                c = by_id[cid]
                title = c.get("title", title)
                perf = ", ".join(c.get("performers", []))
                final_txt = _final_preview(c.get("final", ""))
            else:
                # cid 없으면 제목으로 보조 매칭
                for c in daily:
                    if c.get("title") == title:
                        cid = c.get("id")
                        perf = ", ".join(c.get("performers", []))
                        final_txt = _final_preview(c.get("final", ""))
                        break

            rows.append({
                "시간": f"{s.get('start','')}~{s.get('end','')}",
                "유형": s.get("type", ""),
                "제목": title or "(제목 없음)",
                "출연": perf,
                "소품현황": _props_summary_for_content(cid),
                "최종안": final_txt,
            })
    else:
        # 스케줄이 없으면 콘텐츠만으로 요약
        for c in daily:
            cid = c.get("id")
            rows.append({
                "시간": "-",
                "유형": "-",
                "제목": c.get("title", "(제목 없음)"),
                "출연": ", ".join(c.get("performers", [])),
                "소품현황": _props_summary_for_content(cid),
                "최종안": _final_preview(c.get("final", "")),
            })

    df = pd.DataFrame(rows)

    # 표 표시 — 여백 최소화(열 폭을 작게 지정)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "시간": st.column_config.TextColumn("시간", width="small"),
            "유형": st.column_config.TextColumn("유형", width="small"),
            "제목": st.column_config.TextColumn("제목", width="medium"),
            "출연": st.column_config.TextColumn("출연", width="medium"),
            "소품현황": st.column_config.TextColumn("소품현황", width="large"),
            "최종안": st.column_config.TextColumn("최종안", width="large"),
        },
    )
