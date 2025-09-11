# modules/props.py
from __future__ import annotations
import streamlit as st
from datetime import date, datetime
from .ui import pick_date_with_markers, nearest_anchor_date_today, to_datestr, DOT

def render():
    st.subheader("🛍️ 소품 구매")

    anchor = nearest_anchor_date_today()
    d = pick_date_with_markers(selected=anchor, key="props_calendar")
    dkey = to_datestr(d)

    contents = st.session_state.get("daily_contents", {}).get(dkey, [])
    if not contents:
        st.info("이 날짜에 콘텐츠가 없습니다.")
        return

    # 입력/수정 (원하면 유지)
    with st.expander("➕ 소품 추가/수정", expanded=False):
        for i, c in enumerate(contents):
            cid = c.get("id")
            with st.expander(f"#{i+1}. {c.get('title','(제목 없음)')}", expanded=False):
                items = st.session_state.setdefault("content_props", {}).setdefault(cid, [])
                col1, col2, col3, col4 = st.columns([2,2,1,1.2])
                with col1:
                    name = st.text_input("소품명", key=f"pn_{cid}")
                with col2:
                    vendor = st.text_input("구매처", key=f"pv_{cid}")
                with col3:
                    qty = st.number_input("개수", min_value=1, value=1, step=1, key=f"pq_{cid}")
                with col4:
                    status = st.selectbox("상태", ["예정","주문완료","수령완료"], key=f"ps_{cid}")
                if st.button("추가", key=f"pa_{cid}"):
                    items.append({"name":name,"vendor":vendor,"quantity":qty,"status":status})
                    st.rerun()

                # 간단 목록
                for j, p in enumerate(items):
                    st.write(f"- {p.get('name','')} / {p.get('vendor','')} / {p.get('quantity',1)}개 / {DOT.get(p.get('status','예정'),'🔴')}")

    st.markdown("---")

    # 요청 포맷: 콘텐츠별 묶어서 오른쪽에 라인들
    st.markdown(f"### 📦 {d.strftime('%m월 %d일')} 소품 요약")
    for i, c in enumerate(contents):
        cid = c.get("id")
        left, right = st.columns([0.9, 2.1])
        with left:
            st.markdown(f"**#{i+1}. {c.get('title','(제목 없음)')}**")
        with right:
            lines = []
            for p in st.session_state.get("content_props", {}).get(cid, []):
                lines.append(f"{p.get('name','')}/{p.get('vendor','')}/{p.get('quantity',1)}개/{DOT.get(p.get('status','예정'),'🔴')}")
            if lines:
                st.markdown("  \n".join(lines))
            else:
                st.caption("소품 없음")
