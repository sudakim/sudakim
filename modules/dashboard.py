# modules/dashboard.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from .ui import date_picker_with_toggle, nearest_anchor_date_today, to_datestr

DOT = {"예정": "🔴", "주문완료": "🟡", "수령완료": "🟢"}


def _props_summary_for_content(cid: str | None) -> str:
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
    if not text:
        return ""
    lines = [ln.strip() for ln in str(text).splitlines()]
    lines = [ln for ln in lines if ln][:max_lines]
    return "\n".join(lines)


def _str_len(x: Any) -> int:
    """문자열 길이(이모지/마커 포함). None은 0."""
    if x is None:
        return 0
    s = str(x)
    return len(s)


def _autosize_column_widths(
    df: pd.DataFrame,
    base_px: int = 10,          # 문자 1개 당 대략 px(폰트/테마에 따라 8~10px 정도)
    padding_px: int = 32,       # 좌우 패딩/여백 보정
    min_px_map: Dict[str, int] | None = None,
    max_px_map: Dict[str, int] | None = None,
) -> Dict[str, st.column_config.TextColumn]:
    """
    DataFrame 내용을 훑어 각 열의 최대 문자열 길이로 픽셀 폭을 추정해서
    st.dataframe column_config(TextColumn(width=px))을 만들어 준다.
    """
    if min_px_map is None:
        min_px_map = {
            "시간": 90,
            "유형": 80,
            "제목": 140,
            "출연": 100,
            "소품현황": 220,
            "최종안": 220,
        }
    if max_px_map is None:
        max_px_map = {
            "시간": 90,
            "유형": 80,
            "제목": 360,
            "출연": 140,
            "소품현황": 500,
            "최종안": 820,
        }

    cfg: Dict[str, st.column_config.TextColumn] = {}
    for col in df.columns:
        # 최대 길이 계산 (헤더/내용 모두 고려)
        header_len = _str_len(col)
        body_len = max([_str_len(v) for v in df[col].tolist()] + [0])
        max_chars = max(header_len, body_len)

        # 픽셀 폭 추정
        width_px = max_chars * base_px + padding_px
        width_px = max(width_px, min_px_map.get(col, 100))
        width_px = min(width_px, max_px_map.get(col, 600))

        cfg[col] = st.column_config.TextColumn(col, width=width_px)

    return cfg


def render():
    st.subheader("🧭 대시보드 (요약)")

    # 기준 날짜(토글 달력, 기본 OFF)
    sel = date_picker_with_toggle("기준 날짜", key="dash", default=nearest_anchor_date_today())
    dkey = to_datestr(sel)

    daily: List[Dict[str, Any]] = st.session_state.get("daily_contents", {}).get(dkey, []) or []
    scheds: List[Dict[str, Any]] = st.session_state.get("schedules", {}).get(dkey, []) or []

    by_id: Dict[str, Dict[str, Any]] = {c.get("id", ""): c for c in daily}

    rows: List[Dict[str, Any]] = []
    if scheds:
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
                for c in daily:
                    if c.get("title") == title:
                        cid = c.get("id")
                        perf = ", ".join(c.get("performers", []))
                        final_txt = _final_preview(c.get("final", ""))
                        break

            rows.append(
                {
                    "시간": f"{s.get('start','')}~{s.get('end','')}",
                    "유형": s.get("type", ""),
                    "제목": title or "(제목 없음)",
                    "출연": perf,
                    "소품현황": _props_summary_for_content(cid),
                    "최종안": final_txt,
                }
            )
    else:
        for c in daily:
            cid = c.get("id")
            rows.append(
                {
                    "시간": "-",
                    "유형": "-",
                    "제목": c.get("title", "(제목 없음)"),
                    "출연": ", ".join(c.get("performers", [])),
                    "소품현황": _props_summary_for_content(cid),
                    "최종안": _final_preview(c.get("final", "")),
                }
            )

    df = pd.DataFrame(rows)

    # 👉 내용 기반 “오토사이즈” 효과: 열별 px 폭 자동 계산
    column_cfg = _autosize_column_widths(df)

    st.dataframe(
        df,
        use_container_width=True,   # 화면에 맞추되
        hide_index=True,
        column_config=column_cfg,   # 각 열을 내용 길이에 맞춰 픽셀 폭으로 지정
    )
