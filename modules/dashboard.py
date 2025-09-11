# modules/dashboard.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from typing import Dict, Any, List

# UI 유틸: 달력 토글(기본 OFF), 오늘 기준 가장 가까운 날짜, 날짜 문자열 변환, 소품 상태 마커
from .ui import date_picker_with_toggle, nearest_anchor_date_today, to_datestr, DOT


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


def _preview(text: str, max_lines: int = 3) -> str:
    """최대 N줄까지 줄바꿈 유지하여 미리보기"""
    if not text:
        return ""
    lines = [ln.strip() for ln in str(text).splitlines()]
    lines = [ln for ln in lines if ln][:max_lines]
    return "\n".join(lines)


def _final_or_draft_preview(content: Dict[str, Any]) -> str:
    """
    최종안이 있으면 최종안, 없으면 (초안) + 초안 미리보기 반환.
    """
    final_txt = content.get("final", "") or ""
    if final_txt.strip():
        return _preview(final_txt)

    draft_txt = content.get("draft", "") or ""
    if draft_txt.strip():
        return "(초안) " + _preview(draft_txt)
    return ""


def render():
    st.subheader("🧭 대시보드 (요약)")

    # 기준 날짜: 토글 달력(기본 OFF) + 오늘 기준 가장 가까운 날짜
    sel = date_picker_with_toggle("기준 날짜", key="dash", default=nearest_anchor_date_today())
    dkey = to_datestr(sel)

    # 상태 읽기
    daily: List[Dict[str, Any]] = st.session_state.get("daily_contents", {}).get(dkey, []) or []
    scheds: List[Dict[str, Any]] = st.session_state.get("schedules", {}).get(dkey, []) or []
    by_id: Dict[str, Dict[str, Any]] = {c.get("id", ""): c for c in daily}

    # 표 데이터 빌드
    rows: List[Dict[str, Any]] = []
    if scheds:
        # 타임테이블 순서 기준
        for s in scheds:
            cid = s.get("cid")
            title = s.get("title", "")
            perf = ""
            final_like = ""

            if cid and cid in by_id:
                c = by_id[cid]
                title = c.get("title", title)
                perf = ", ".join(c.get("performers", []))
                final_like = _final_or_draft_preview(c)
            else:
                # cid 없으면 제목 매칭으로 보조
                for c in daily:
                    if c.get("title") == title:
                        cid = c.get("id")
                        perf = ", ".join(c.get("performers", []))
                        final_like = _final_or_draft_preview(c)
                        break

            rows.append(
                {
                    "시간": f"{s.get('start','')}~{s.get('end','')}",
                    "유형": s.get("type", ""),
                    "제목": title or "(제목 없음)",
                    "출연": perf,
                    "소품현황": _props_summary_for_content(cid),
                    "최종안": final_like,   # ← 최종안이 없으면 (초안)으로 대체
                }
            )
    else:
        # 스케줄 없으면 콘텐츠만 요약
        for c in daily:
            cid = c.get("id")
            rows.append(
                {
                    "시간": "-",
                    "유형": "-",
                    "제목": c.get("title", "(제목 없음)"),
                    "출연": ", ".join(c.get("performers", [])),
                    "소품현황": _props_summary_for_content(cid),
                    "최종안": _final_or_draft_preview(c),  # ← 최종안/초안 표시
                }
            )

    df = pd.DataFrame(rows)

    # ===== 화면 비율 기반 열 너비 =====
    # 컨테이너 가로폭 추정(px) — 화면 느낌에 맞게 1200~1500 사이 조정 가능
    CONTAINER_PX = 1300

    # 열 비율(합이 1.0 근처): 요청한 느낌에 맞춘 기본값
    ratios = {
        "시간": 0.08,
        "유형": 0.07,
        "제목": 0.17,
        "출연": 0.12,
        "소품현황": 0.36,
        "최종안": 0.20,
    }

    def _w(col: str, default_px: int = 120, min_px: int = 80, max_px: int = 900) -> int:
        px = int(ratios.get(col, 0.15) * CONTAINER_PX)
        return max(min_px, min(px, max_px))

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "시간":      st.column_config.TextColumn("시간",      width=_w("시간")),
            "유형":      st.column_config.TextColumn("유형",      width=_w("유형")),
            "제목":      st.column_config.TextColumn("제목",      width=_w("제목")),
            "출연":      st.column_config.TextColumn("출연",      width=_w("출연")),
            "소품현황":  st.column_config.TextColumn("소품현황",  width=_w("소품현황")),
            "최종안":    st.column_config.TextColumn("최종안",    width=_w("최종안")),
        },
    )
