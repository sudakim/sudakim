# modules/dashboard.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from .ui import date_picker_with_toggle, nearest_anchor_date_today, to_datestr

DOT = {"예정": "🔴", "주문완료": "🟡", "수령완료": "🟢"}

def _props_summary_for_content(cid: str) -> str:
    """콘텐츠별 소품 요약 문자열 생성"""
    items = st.session_state.get("content_props", {}).get(cid, []) or []
    if not items:
        return "소품 0개"
    parts = [
        f"{DOT.get(p.get('status','예정'),'🔴')}{p.get('name','')}({p.get('quantity',1)}개)"
        for p in items
    ]
    return f"소품 {len(items)}개 · " + ", ".join(parts)

def _final_preview(final_text: str, max_lines: int = 3) -> str:
    """최대 N줄까지 줄바꿈 유지해 미리보기"""
    if not final_text:
        return ""
    lines = [ln.strip() for ln in str(final_text).splitlines()]
    lines = [ln for ln in lines if ln][:max_lines]  # 공백라인 제거 후 앞 N줄
    return "\n".join(lines)

def render():
    st.subheader("🧭 대시보드 (요약)")

    # 기준 날짜: 토글형 달력(기본 OFF) + 오늘 기준 가장 가까운 날짜
    sel = date_picker_with_toggle("기준 날짜", key="dash", default=nearest_anchor_date_today())
    dkey = to_datestr(sel)

    daily = st.session_state.get("daily_contents", {}).get(dkey, []) or []
    scheds = st.session_state.get("schedules", {}).get(dkey, []) or []

    # content id -> content 매핑 (최종안/출연자 조회용)
    by_id: Dict[str, Dict[str, Any]] = {c.get("id",""): c for c in daily}

    rows: List[Dict[str, Any]] = []

    if scheds:  # 타임테이블 기준 요약
        for s in scheds:
            cid = s.get("cid")
            title = s.get("title") or ""
            perf = ""
            final_text = ""
            if cid and cid in by_id:
                c = by_id[cid]
                title = c.get("title", title)
                perf = ", ".join(c.get("performers", []))
                final_text = _final_preview(c.get("final", ""))
            else:
                # cid가 없으면 제목 매칭으로 performers만 추정
                for c in daily:
                    if c.get("title") == title:
                        perf = ", ".join(c.get("performers", []))
                        final_text = _final_preview(c.get("final", ""))
                        cid = c.get("id")
                        break

            rows.append({
                "시간": f"{s.get('start','')}~{s.get('end','')}",
                "유형": s.get("type", ""),
                "제목": title or "(제목 없음)",
                "출연": perf,
                "소품현황": _props_summary_for_content(cid) if cid else "소품 0개",
                "최종안": final_text,
            })
    else:  # 일정이 없으면 콘텐츠만으로 요약
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

# 열 길이를 글자 수에 맞게 자동 조정
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
    }
)

