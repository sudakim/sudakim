# modules/props.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from .ui import date_picker_with_toggle, nearest_anchor_date_today, to_datestr, DOT
from modules import storage
from .ui_enhanced import ThemeManager, STATUS_STYLES, success_animation

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
    
    # 간단한 테이블 형태로 소품 현황 표시
    for i, c in enumerate(contents):
        cid = c.get("id")
        items = st.session_state.get("content_props", {}).get(cid, [])
        
        # 콘텐츠 제목과 요약 정보
        st.subheader(f"📋 #{i+1}. {c.get('title', '(제목 없음)')}")
        
        if items:
            # 데이터 검증 및 정리
            clean_items = []
            for p in items:
                name = str(p.get('name', '')).strip()
                vendor = str(p.get('vendor', '')).strip()
                quantity = p.get('quantity', 1)
                status = p.get('status', '예정')
                
                # 빈 값이나 이상한 문자 필터링
                if not name or name in ['ㅇ', 'ㅇㅇ', ''] or len(name.strip()) < 1:
                    continue
                    
                # 특수문자 정리
                name = name.replace(']', '').replace('[', '').strip()
                vendor = vendor.replace(']', '').replace('[', '').strip()
                
                # 빈 vendor는 '기타'로 설정
                if not vendor:
                    vendor = '기타'
                
                # 상태 아이콘 추가
                status_info = STATUS_STYLES.get(status, {})
                status_display = f"{status_info.get('icon', '🔴')} {status}"
                
                clean_items.append({
                    '소품명': name,
                    '구매처': vendor,
                    '수량': f"{quantity}개",
                    '상태': status_display
                })
            
            if clean_items:
                # 요약 정보
                total_items = sum(int(item['수량'].replace('개', '')) for item in clean_items)
                completed_items = len([item for item in clean_items if '수령완료' in item['상태']])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("전체 소품", f"{total_items}개")
                with col2:
                    st.metric("수령완료", f"{completed_items}개")
                
                # 간단한 테이블로 표시
                df = pd.DataFrame(clean_items)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("유효한 소품 정보가 없습니다.")
        else:
            st.info("등록된 소품이 없습니다.")
        
        st.markdown("---")
