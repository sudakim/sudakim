# modules/props.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from .ui import date_picker_with_toggle, nearest_anchor_date_today, to_datestr, DOT
from modules import storage

# 간단한 상태 정보 (아이콘만)
STATUS_ICONS = {
    "예정": "⏳",
    "주문완료": "📦", 
    "수령완료": "✅"
}

def render():
    """
    간단하고 깔끔한 소품 관리 인터페이스
    """
    # 간단한 헤더
    st.title("🛍️ 소품 구매 관리")
    st.markdown("---")

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
                        st.success("소품이 추가되었습니다!")
                        st.rerun()

                # 등록된 소품 목록
                if items:
                    st.markdown("#### 📋 등록된 소품")
                    for j, p in enumerate(items):
                        status_icon = STATUS_ICONS.get(p.get('status', '예정'), '⏳')
                        st.markdown(f"**{j+1}.** {p.get('name', '')} | {p.get('vendor', '')} | {p.get('quantity', 1)}개 | {status_icon} {p.get('status', '예정')}")
                else:
                    st.info("등록된 소품이 없습니다.")

    # 소품 요약 섹션
    st.markdown("---")
    st.header(f"📊 {d.strftime('%m월 %d일')} 소품 현황")
    
    # 전체 소품 데이터를 한 번에 수집하여 간단한 표로 표시
    all_props = []
    total_count = 0
    completed_count = 0
    
    for i, c in enumerate(contents):
        cid = c.get("id")
        items = st.session_state.get("content_props", {}).get(cid, [])
        content_title = c.get('title', f'콘텐츠 #{i+1}')
        
        for p in items:
            name = str(p.get('name', '')).strip()
            vendor = str(p.get('vendor', '')).strip()
            quantity = p.get('quantity', 1)
            status = p.get('status', '예정')
            
            # 유효한 데이터만 포함
            if name and name not in ['ㅇ', 'ㅇㅇ', ''] and len(name.strip()) >= 1:
                # 특수문자 정리
                name = name.replace(']', '').replace('[', '').strip()
                vendor = vendor.replace(']', '').replace('[', '').strip() or '기타'
                
                # 상태 아이콘 추가
                status_icon = STATUS_ICONS.get(status, '⏳')
                
                all_props.append({
                    '콘텐츠': content_title,
                    '소품명': name,
                    '구매처': vendor,
                    '수량': quantity,
                    '상태': f"{status_icon} {status}"
                })
                
                total_count += quantity
                if status == '수령완료':
                    completed_count += quantity
    
    if all_props:
        # 요약 통계
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체 소품", f"{total_count}개")
        with col2:
            st.metric("수령완료", f"{completed_count}개")
        with col3:
            progress = (completed_count / total_count * 100) if total_count > 0 else 0
            st.metric("완료율", f"{progress:.1f}%")
        
        # 간단한 테이블로 모든 소품 표시
        df = pd.DataFrame(all_props)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
    else:
        st.info("📌 등록된 소품이 없습니다.")
