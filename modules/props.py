# modules/props.py
from __future__ import annotations
import streamlit as st
from .ui import date_picker_with_toggle, nearest_anchor_date_today, to_datestr, DOT
from modules import storage
from .ui_enhanced import ThemeManager, modern_card, STATUS_STYLES, success_animation

def render():
    """
    개선된 소품 관리 인터페이스
    모던한 카드 디자인과 함께 개선된 사용자 경험 제공
    """
    # 테마 적용
    theme = ThemeManager()
    theme.apply_theme()
    
    # 모던한 헤더
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {theme.colors['secondary']}, {theme.colors['accent']}); 
                padding: 20px; border-radius: 12px; margin-bottom: 20px; text-align: center;">
        <h2 style="color: white; margin: 0;">🛍️ 소품 구매 관리</h2>
        <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">콘텐츠별 소품 현황</p>
    </div>
    """, unsafe_allow_html=True)

    d = date_picker_with_toggle("📅 날짜 선택", key="props", default=nearest_anchor_date_today())
    dkey = to_datestr(d)

    contents = st.session_state.get("daily_contents", {}).get(dkey, [])
    if not contents:
        st.info("📌 이 날짜에 등록된 콘텐츠가 없습니다.")
        return

    # 소품 추가 섹션
    with st.expander("➕ 소품 추가하기", expanded=False):
        st.markdown("### 🛒 새 소품 등록")
        for i, c in enumerate(contents):
            cid = c.get("id")
            with st.expander(f"📋 #{i+1}. {c.get('title','(제목 없음)')}", expanded=False):
                items = st.session_state.setdefault("content_props", {}).setdefault(cid, [])
                
                # 모던한 입력 폼 레이아웃
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1.2])
                with col1: 
                    name = st.text_input("소품명", placeholder="예: 카메라 거치대", key=f"pn_{cid}")
                with col2: 
                    vendor = st.text_input("구매처", placeholder="예: 쿠팡", key=f"pv_{cid}")
                with col3: 
                    qty = st.number_input("개수", min_value=1, value=1, step=1, key=f"pq_{cid}")
                with col4: 
                    status = st.selectbox("상태", ["예정", "주문완료", "수령완료"], key=f"ps_{cid}")
                
                if st.button("✅ 추가하기", key=f"pa_{cid}", use_container_width=True):
                    if name.strip():  # 소품명이 비어있지 않은 경우만
                        items.append({"name": name, "vendor": vendor, "quantity": qty, "status": status})
                        storage.autosave_maybe()
                        success_animation("소품이 추가되었습니다!")
                        st.rerun()

                # 등록된 소품 목록
                if items:
                    st.markdown("#### 📋 등록된 소품")
                    for j, p in enumerate(items):
                        status_info = STATUS_STYLES.get(p.get('status', '예정'), {})
                        status_badge = f"""
                        <span class="status-badge" style="background-color: {status_info.get('bg_color', '#EBF5FB')}; 
                              color: {status_info.get('color', '#E74C3C')}; 
                              border: 1px solid {status_info.get('color', '#E74C3C')}; margin: 2px;">
                            {status_info.get('icon', '🔴')} {p.get('status', '예정')}
                        </span>
                        """
                        st.markdown(f"**{j+1}.** {p.get('name', '')} | {p.get('vendor', '')} | {p.get('quantity', 1)}개 | {status_badge}", unsafe_allow_html=True)
                else:
                    st.info("등록된 소품이 없습니다.")

    # 소품 요약 섹션
    st.markdown("---")
    st.markdown(f"### 📊 {d.strftime('%m월 %d일')} 소품 현황")
    
    # 모던한 카드 레이아웃으로 개선
    for i, c in enumerate(contents):
        cid = c.get("id")
        items = st.session_state.get("content_props", {}).get(cid, [])
        
        # 콘텐츠별 소품 요약 카드
        card_content = '''
        <div style="margin: 10px 0;">
        '''
        
        if items:
            total_items = sum(p.get('quantity', 1) for p in items)
            completed_items = len([p for p in items if p.get('status') == '수령완료'])
            
            card_content += '''
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <span>총 {total}개</span>
                <span style="color: {success_color};">완료: {completed}개</span>
            </div>
            '''.format(total=total_items, completed=completed_items, success_color=theme.colors['success'])
            for p in items:
                status_info = STATUS_STYLES.get(p.get('status', '예정'), {})
                card_content += f"""
                <div style="padding: 8px; margin: 4px 0; background-color: rgba(0,0,0,0.05); border-radius: 6px;">
                    <strong>{p.get('name', '')}</strong> | {p.get('vendor', '')} | {p.get('quantity', 1)}개
                    <span class="status-badge" style="background-color: {status_info.get('bg_color', '#EBF5FB')}; 
                          color: {status_info.get('color', '#E74C3C')}; 
                          border: 1px solid {status_info.get('color', '#E74C3C')}; margin-left: 8px;">
                        {status_info.get('icon', '🔴')} {p.get('status', '예정')}
                    </span>
                </div>
                """
        else:
            card_content += "<div style='text-align: center; color: #7F8C8D; padding: 20px;'>소품이 등록되지 않았습니다.</div>"
        
        card_content += "</div>"
        
        modern_card(
            title=f"#{i+1}. {c.get('title', '(제목 없음)')}",
            content=card_content,
            status=None,
            expandable=False
        )
