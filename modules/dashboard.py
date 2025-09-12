# modules/dashboard.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from typing import Dict, Any, List

# UI 유틸: 달력 토글(기본 OFF), 오늘 기준 가장 가까운 날짜, 날짜 문자열 변환, 소품 상태 마커
from .ui import date_picker_with_toggle, nearest_anchor_date_today, to_datestr, DOT
from .ui_enhanced import (
    ThemeManager, modern_card, modern_grid, 
    loading_animation, success_animation, STATUS_STYLES
)


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
    """
    개선된 대시보드 렌더링
    모던한 카드 디자인과 향상된 사용자 경험 제공
    """
    # 테마 적용
    theme = ThemeManager()
    theme.apply_theme()
    
    # 모던한 헤더
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {theme.colors['primary']}, {theme.colors['secondary']}); 
                padding: 30px; border-radius: 16px; margin-bottom: 30px; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 2.5em;">🧭 대시보드</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 1.2em;">
            콘텐츠 현황 요약
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 기준 날짜 선택 (개선된 디자인)
    sel = date_picker_with_toggle("📅 기준 날짜", key="dash", default=nearest_anchor_date_today())
    dkey = to_datestr(sel)

    # 상태 읽기
    daily: List[Dict[str, Any]] = st.session_state.get("daily_contents", {}).get(dkey, []) or []
    scheds: List[Dict[str, Any]] = st.session_state.get("schedules", {}).get(dkey, []) or []
    by_id: Dict[str, Dict[str, Any]] = {c.get("id", ""): c for c in daily}

    if not daily and not scheds:
        st.info("📌 이 날짜에는 등록된 콘텐츠가 없습니다.")
        return

    # 콘텐츠 요약 카드
    st.markdown(f"### 📊 {sel.strftime('%Y년 %m월 %d일')} 콘텐츠 요약")
    
    # 통계 정보
    total_content = len(daily)
    completed_count = sum(1 for c in daily 
                         if st.session_state.get("upload_status", {}).get(c.get("id")) == "업로드완료")
    
    # 통계 카드
    col1, col2, col3 = st.columns(3)
    with col1:
        modern_card(
            title="총 콘텐츠",
            content=f"**{total_content}**개",
            status=None,
            expandable=False
        )
    with col2:
        modern_card(
            title="완료됨",
            content=f"**{completed_count}**개",
            status="업로드완료",
            expandable=False
        )
    with col3:
        completion_rate = f"{(completed_count/total_content*100):.1f}%" if total_content > 0 else "0%"
        modern_card(
            title="완료율",
            content=f"**{completion_rate}**",
            status=None,
            expandable=False
        )

    # 표 데이터 빌드
    rows: List[Dict[str, Any]] = []
    if scheds:
        # 타임테이블 기준
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
                for c in daily:
                    if c.get("title") == title:
                        cid = c.get("id")
                        perf = ", ".join(c.get("performers", []))
                        final_like = _final_or_draft_preview(c)
                        break

            # 상태 뱃지
            upload_status = st.session_state.get("upload_status", {}).get(cid, "촬영전")
            status_info = STATUS_STYLES.get(upload_status, {})
            status_badge = f"""
            <span class="status-badge" style="background-color: {status_info.get('bg_color', '#EBF5FB')}; 
                  color: {status_info.get('color', '#3498DB')}; 
                  border: 1px solid {status_info.get('color', '#3498DB')}; margin: 2px;">
                {status_info.get('icon', '🔵')} {upload_status}
            </span>
            """.strip()

            rows.append(
                {
                    "시간": f"{s.get('start','')}~{s.get('end','')}",
                    "유형": s.get("type", ""),
                    "제목": title or "(제목 없음)",
                    "출연": perf,
                    "상태": status_badge,
                    "소품현황": _props_summary_for_content(cid),
                    "최종안": final_like,
                }
            )
    else:
        # 콘텐츠만 있는 경우
        for c in daily:
            cid = c.get("id")
            upload_status = st.session_state.get("upload_status", {}).get(cid, "촬영전")
            status_info = STATUS_STYLES.get(upload_status, {})
            status_badge = f"""
            <span class="status-badge" style="background-color: {status_info.get('bg_color', '#EBF5FB')}; 
                  color: {status_info.get('color', '#3498DB')}; 
                  border: 1px solid {status_info.get('color', '#3498DB')}; margin: 2px;">
                {status_info.get('icon', '🔵')} {upload_status}
            </span>
            """.strip()
            
            rows.append(
                {
                    "시간": "-",
                    "유형": "-",
                    "제목": c.get("title", "(제목 없음)"),
                    "출연": ", ".join(c.get("performers", [])),
                    "상태": status_badge,
                    "소품현황": _props_summary_for_content(cid),
                    "최종안": _final_or_draft_preview(c),
                }
            )

    if not rows:
        st.warning("📋 표시할 콘텐츠가 없습니다.")
        return

    df = pd.DataFrame(rows)

    # 모던한 테이블 스타일
    st.markdown("### 📋 콘텐츠 목록")
    
    # 반응형 컬럼 너비 설정
    is_mobile = st.session_state.get('screen_width', 1200) < 768
    
    if is_mobile:
        # 모바일에서는 중요한 정보만 표시
        display_df = df[["제목", "상태", "최종안"]].copy()
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "제목": st.column_config.TextColumn("제목", width=200),
                "상태": st.column_config.TextColumn("상태", width=100),
                "최종안": st.column_config.TextColumn("최종안", width=150),
            },
        )
    else:
        # 데스크탑에서는 전체 정보 표시
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "시간": st.column_config.TextColumn("⏰ 시간", width=80),
                "유형": st.column_config.TextColumn("📋 유형", width=70),
                "제목": st.column_config.TextColumn("📝 제목", width=150),
                "출연": st.column_config.TextColumn("👥 출연", width=100),
                "상태": st.column_config.TextColumn("📊 상태", width=100),
                "소품현황": st.column_config.TextColumn("🛍️ 소품현황", width=200),
                "최종안": st.column_config.TextColumn("📝 최종안", width=150),
            },
        )

    # 추가 정보 (선택 사항)
    with st.expander("📊 상세 정보", expanded=False):
        st.markdown("### 📈 오늘의 통계")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="촬영 예정", value=len([r for r in rows if "촬영전" in r["상태"]]))
        with col2:
            st.metric(label="촬영 완료", value=len([r for r in rows if "촬영완료" in r["상태"]]))
        with col3:
            st.metric(label="편집 완료", value=len([r for r in rows if "편집완료" in r["상태"]]))
        with col4:
            st.metric(label="업로드 완료", value=len([r for r in rows if "업로드완료" in r["상태"]]))
