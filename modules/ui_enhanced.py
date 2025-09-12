# modules/ui_enhanced.py
"""
고급 UI 컴포넌트 및 테마 시스템
Modern UI components and theme system for YouTube Content Manager
"""

from __future__ import annotations
import streamlit as st
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Callable
import time

# 🎨 색상 테마 정의
COLOR_THEMES = {
    "modern": {
        "primary": "#DC2626",      # 더 진한 빨강으로 대비 향상
        "secondary": "#059669",    # 더 진한 초록으로 가독성 향상
        "accent": "#1D4ED8",       # 더 진한 파랑으로 명확한 강조
        "background": "#F9FAFB",   # 더 밝은 배경
        "surface": "#FFFFFF",
        "text_primary": "#111827", # 매우 진한 텍스트로 최대 대비
        "text_secondary": "#4B5563", # 충분히 진한 보조 텍스트
        "success": "#059669",
        "warning": "#D97706", 
        "error": "#DC2626",
        "border": "#D1D5DB"        # 명확한 테두리
    },
    "dark": {
        "primary": "#FF6B6B",
        "secondary": "#4ECDC4",
        "accent": "#A29BFE",       
        "background": "#1E293B",   # 더 부드러운 다크 배경
        "surface": "#334155",      # 더 밝은 서페이스로 대비 향상
        "text_primary": "#FFFFFF", # 순백색으로 최대 대비
        "text_secondary": "#E2E8F0", # 매우 밝은 보조 텍스트
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "border": "#475569"        # 더 명확한 테두리
    }
}

# 🎯 상태 아이콘 및 색상
STATUS_STYLES = {
    "촬영전": {"icon": "🎬", "color": "#3498DB", "bg_color": "#EBF5FB"},
    "촬영완료": {"icon": "✅", "color": "#F39C12", "bg_color": "#FEF9E7"},
    "편집완료": {"icon": "✂️", "color": "#E67E22", "bg_color": "#FAE5D3"},
    "업로드완료": {"icon": "🚀", "color": "#27AE60", "bg_color": "#D5F4E6"},
    "예정": {"icon": "⏳", "color": "#E74C3C", "bg_color": "#FADBD8"},
    "주문완료": {"icon": "📦", "color": "#F39C12", "bg_color": "#FEF9E7"},
    "수령완료": {"icon": "📋", "color": "#27AE60", "bg_color": "#D5F4E6"}
}

class ThemeManager:
    """테마 관리 및 적용"""
    
    def __init__(self):
        self.current_theme = st.session_state.get("theme", "modern")
        self.colors = COLOR_THEMES[self.current_theme]
    
    def apply_theme(self):
        """현재 테마를 Streamlit에 적용 - 강제 색상 적용"""
        theme_css = f"""
        <style>
        /* 전체 페이지 스타일 - 브라우저 설정 무시 */
        .stApp {{
            background-color: {self.colors["background"]} !important;
            color: {self.colors["text_primary"]} !important;
        }}
        
        /* 모든 텍스트 요소 강제 가시성 보장 */
        .main .block-container * {{
            color: {self.colors["text_primary"]} !important;
        }}
        
        /* Streamlit 기본 텍스트 강제 스타일링 */
        .stMarkdown, .stMarkdown p, .stMarkdown div, .stMarkdown span {{
            color: {self.colors["text_primary"]} !important;
        }}
        
        /* 정보 박스 텍스트 강제 스타일링 */
        .stInfo, .stInfo p, .stInfo div {{
            color: {self.colors["text_primary"]} !important;
            background-color: {self.colors["surface"]} !important;
            border: 1px solid {self.colors["primary"]} !important;
        }}
        
        .stSuccess, .stSuccess p, .stSuccess div {{
            color: {self.colors["text_primary"]} !important;
            background-color: {self.colors["surface"]} !important;
            border: 1px solid {self.colors["success"]} !important;
        }}
        
        .stWarning, .stWarning p, .stWarning div {{
            color: {self.colors["text_primary"]} !important;
            background-color: {self.colors["surface"]} !important;
            border: 1px solid {self.colors["warning"]} !important;
        }}
        
        .stError, .stError p, .stError div {{
            color: {self.colors["text_primary"]} !important;
            background-color: {self.colors["surface"]} !important;
            border: 1px solid {self.colors["error"]} !important;
        }}
        
        /* 캡션 및 보조 텍스트 */
        .caption, .stCaption {{
            color: {self.colors["text_secondary"]} !important;
        }}
        
        /* 카드 스타일 */
        .content-card {{
            background-color: {self.colors["surface"]} !important;
            color: {self.colors["text_primary"]} !important;
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border: 1px solid {self.colors["border"]};
            transition: all 0.3s ease;
        }}
        
        .content-card * {{
            color: {self.colors["text_primary"]} !important;
        }}
        
        .content-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}
        
        /* 버튼 스타일 */
        .stButton > button {{
            background-color: {self.colors["primary"]} !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 8px 16px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }}
        
        .stButton > button:hover {{
            background-color: {self.colors["secondary"]} !important;
            transform: translateY(-1px) !important;
        }}
        
        /* 상태 뱃지 */
        .status-badge {{
            display: inline-block !important;
            padding: 4px 12px !important;
            border-radius: 20px !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            margin: 2px !important;
            color: white !important;
        }}
        
        /* 헤더 스타일 */
        .section-header {{
            color: {self.colors["primary"]} !important;
            font-size: 24px !important;
            font-weight: 600 !important;
            margin-bottom: 20px !important;
            padding-bottom: 10px !important;
            border-bottom: 2px solid {self.colors["primary"]} !important;
        }}
        
        /* 데이터프레임 텍스트 가시성 */
        .stDataFrame {{
            background-color: {self.colors["surface"]} !important;
            color: {self.colors["text_primary"]} !important;
        }}
        
        .stDataFrame * {{
            color: {self.colors["text_primary"]} !important;
        }}
        </style>
        """
        st.markdown(theme_css, unsafe_allow_html=True)

def modern_card(title: str, content: str, status: str = None, actions: List[Dict] = None, 
                key: str = None, expandable: bool = True) -> bool:
    """
    모던한 카드 컴포넌트
    
    Args:
        title: 카드 제목
        content: 카드 내용
        status: 상태 (촬영전, 촬영완료, 편집완료, 업로드완료)
        actions: 액션 버튼 리스트 [{"label": "버튼명", "callback": 함수}]
        key: 고유 키
        expandable: 확장 가능 여부
    
    Returns:
        확장 상태 (expandable=True인 경우)
    """
    theme = ThemeManager()
    
    if expandable:
        with st.expander(f"**{title}**", expanded=False):
            return _render_card_content(content, status, actions, theme)
    else:
        st.markdown(f'<div class="content-card">', unsafe_allow_html=True)
        _render_card_content(content, status, actions, theme)
        st.markdown('</div>', unsafe_allow_html=True)
        return False

def _render_card_content(content: str, status: str, actions: List[Dict], theme: ThemeManager):
    """카드 내용 렌더링"""
    # 상태 표시
    if status and status in STATUS_STYLES:
        status_info = STATUS_STYLES[status]
        status_html = f"""
        <div class="status-badge" style="background-color: {status_info['bg_color']}; 
             color: {status_info['color']}; border: 1px solid {status_info['color']}; ">
            {status_info['icon']} {status}
        </div>
        """
        st.markdown(status_html, unsafe_allow_html=True)
    
    # 내용 표시
    st.markdown(content)
    
    # 액션 버튼
    if actions:
        cols = st.columns(len(actions))
        for i, action in enumerate(actions):
            with cols[i]:
                if st.button(action["label"], key=f"{action.get('key', '')}_{i}"):
                    if action.get("callback"):
                        action["callback"]()

def modern_grid(items: List[Dict], columns: int = 3, card_type: str = "basic"):
    """
    모던한 그리드 레이아웃
    
    Args:
        items: 아이템 리스트
        columns: 열 개수
        card_type: 카드 타입 ("basic", "detailed", "compact")
    """
    if not items:
        st.info("표시할 내용이 없습니다.")
        return
    
    # 반응형 그리드
    if st.session_state.get('screen_width', 1200) < 768:
        columns = 1
    elif st.session_state.get('screen_width', 1200) < 1024:
        columns = min(columns, 2)
    
    grid_cols = st.columns(columns)
    
    for i, item in enumerate(items):
        col_idx = i % columns
        with grid_cols[col_idx]:
            if card_type == "basic":
                modern_card(
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    status=item.get("status"),
                    actions=item.get("actions"),
                    key=f"grid_item_{i}"
                )
            elif card_type == "detailed":
                _render_detailed_card(item)
            elif card_type == "compact":
                _render_compact_card(item)

def _render_detailed_card(item: Dict):
    """상세 카드 렌더링"""
    theme = ThemeManager()
    st.markdown(f"""
    <div class="content-card" style="border-left: 4px solid {theme.colors['primary']}; ">
        <h4 style="color: {theme.colors['primary']}; margin: 0;">{item.get('title', '')}</h4>
        <p style="color: {theme.colors['text_secondary']}; margin: 8px 0;">{item.get('subtitle', '')}</p>
        <div style="background-color: {theme.colors['background']}; padding: 12px; 
                    border-radius: 8px; margin: 12px 0;">
            {item.get('content', '')}
        </div>
    </div>
    """, unsafe_allow_html=True)

def _render_compact_card(item: Dict):
    """컴팩트 카드 렌더링"""
    st.markdown(f"""
    <div class="content-card" style="padding: 12px; margin: 6px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 500;">{item.get('title', '')}</span>
            <span class="status-badge">{item.get('status', '')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def simple_sidebar():
    """크롬 다크모드에 반응하는 간단한 사이드바"""
    
    with st.sidebar:
        # 헤더 - 크롬 다크모드에 반응하는 디자인
        st.markdown("""
        <div style="text-align: center; padding: 24px; 
                    background: linear-gradient(135deg, #DC2626, #1D4ED8);
                    border-radius: 16px; margin-bottom: 24px; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
            <h2 style="color: white; margin: 0; font-weight: 700; font-size: 1.5em;">🎬 유튜브 관리</h2>
            <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 0.9em;">콘텐츠 매니저</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 간단한 안내 메시지
        st.info("💡 이 앱은 크롬의 라이트/다크 모드 설정에 자동으로 반응합니다.")
        
        # 네비게이션 섹션
        st.markdown("### 🧭 빠른 네비게이션")
        
        # 퀵 액션 버튼들
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 통계", use_container_width=True, type="secondary"):
                st.session_state.selected_tab = "dashboard"
        with col2:
            if st.button("📝 기획", use_container_width=True, type="secondary"):
                st.session_state.selected_tab = "planning"
                
        # 통계 카드
        stats = _get_dashboard_stats()
        
        st.markdown("### 📊 현황 통계")
        
        # 간단한 메트릭 표시
        col1, col2 = st.columns(2)
        with col1:
            st.metric("전체", stats['total'])
            st.metric("완료", stats['completed'])
        with col2:
            completion_rate = (stats['completed'] / max(stats['total'], 1)) * 100
            st.metric("완료율", f"{completion_rate:.1f}%")
            st.metric("진행중", stats['in_progress'])
        
        # 도움말 섹션
        with st.expander("💡 도움말", expanded=False):
            st.markdown("""
            **사용법:**
            - 📝 **콘텐츠 기획**: 새로운 콘텐츠 아이디어 추가
            - 🛍️ **소품 구매**: 필요한 소품 관리
            - ⏰ **타임테이블**: 촬영 일정 관리
            - 📹 **업로드 현황**: 진행 상황 추적
            
            **테마 설정:**
            크롬 → 설정 → 모양 → 테마에서 라이트/다크 모드를 변경할 수 있습니다.
            """)
            
        st.markdown("---")
        st.caption("🎨 크롬 다크모드 설정에 따라 자동으로 테마가 변경됩니다")

def _get_dashboard_stats() -> Dict[str, int]:
    """대시보드 통계 계산"""
    total = 0
    completed = 0
    in_progress = 0
    
    contents = st.session_state.get("daily_contents", {})
    upload_status = st.session_state.get("upload_status", {})
    
    for date_key, day_contents in contents.items():
        for content in day_contents:
            total += 1
            status = upload_status.get(content.get("id", ""), "촬영전")
            if status == "업로드완료":
                completed += 1
            elif status in ["촬영완료", "편집완료"]:
                in_progress += 1
    
    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress
    }

def loading_animation(text: str = "처리 중..."):
    """로딩 애니메이션"""
    with st.spinner(text):
        time.sleep(0.5)  # 실제 로딩 시간 대체

def success_animation(message: str = "완료되었습니다!"):
    """성공 애니메이션"""
    st.success(message)
    time.sleep(1.5)

def error_animation(message: str = "오류가 발생했습니다."):
    """오류 애니메이션"""
    st.error(message)
    time.sleep(2)