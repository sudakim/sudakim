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
        "primary": "#FF6B6B",
        "secondary": "#4ECDC4", 
        "accent": "#45B7D1",
        "background": "#F8F9FA",
        "surface": "#FFFFFF",
        "text_primary": "#2C3E50",
        "text_secondary": "#7F8C8D",
        "success": "#27AE60",
        "warning": "#F39C12",
        "error": "#E74C3C",
        "border": "#E9ECEF"
    },
    "dark": {
        "primary": "#FF6B6B",
        "secondary": "#4ECDC4",
        "accent": "#45B7D1", 
        "background": "#1A1A2E",
        "surface": "#16213E",
        "text_primary": "#FFFFFF",
        "text_secondary": "#B0B0B0",
        "success": "#2ECC71",
        "warning": "#F39C12",
        "error": "#E74C3C",
        "border": "#2C3E50"
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
        """현재 테마를 Streamlit에 적용"""
        theme_css = f"""
        <style>
        /* 전체 페이지 스타일 */
        .stApp {{
            background-color: {self.colors["background"]};
            color: {self.colors["text_primary"]};
        }}
        
        /* 카드 스타일 */
        .content-card {{
            background-color: {self.colors["surface"]};
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border: 1px solid {self.colors["border"]};
            transition: all 0.3s ease;
        }}
        
        .content-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}
        
        /* 버튼 스타일 */
        .stButton > button {{
            background-color: {self.colors["primary"]};
            color: white;
            border-radius: 8px;
            border: none;
            padding: 8px 16px;
            font-weight: 500;
            transition: all 0.2s ease;
        }}
        
        .stButton > button:hover {{
            background-color: {self.colors["secondary"]};
            transform: translateY(-1px);
        }}
        
        /* 상태 뱃지 */
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            margin: 2px;
        }}
        
        /* 헤더 스타일 */
        .section-header {{
            color: {self.colors["primary"]};
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid {self.colors["primary"]};
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

def modern_sidebar():
    """모던한 사이드바"""
    theme = ThemeManager()
    
    with st.sidebar:
        # 헤더
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, 
                    {theme.colors['primary']}, {theme.colors['secondary']});
                    border-radius: 12px; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0;">🎬 유튜브 관리</h2>
            <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">콘텐츠 매니저</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 테마 선택
        theme_choice = st.selectbox(
            "🎨 테마 선택",
            ["modern", "dark"],
            index=0 if theme.current_theme == "modern" else 1,
            key="theme_selector"
        )
        
        if theme_choice != theme.current_theme:
            st.session_state.theme = theme_choice
            st.rerun()
        
        # 네비게이션
        st.markdown("### 🧭 네비게이션")
        
        # 통계 카드
        stats = _get_dashboard_stats()
        st.markdown(f"""
        <div style="background-color: {theme.colors['surface']}; padding: 15px; 
                    border-radius: 8px; border: 1px solid {theme.colors['border']}; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                <span>전체 콘텐츠</span>
                <span style="font-weight: bold; color: {theme.colors['primary']};">{stats['total']}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                <span>완료됨</span>
                <span style="font-weight: bold; color: {theme.colors['success']};">{stats['completed']}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                <span>진행중</span>
                <span style="font-weight: bold; color: {theme.colors['warning']};">{stats['in_progress']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

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