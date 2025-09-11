# modules/props.py
from __future__ import annotations
import streamlit as st
from .ui import date_picker_with_toggle, nearest_anchor_date_today, to_datestr, DOT
from modules import storage

def render():
    st.subheader("🛍️ 소품 구매")

    d = date_picker_with_toggle("날짜 선택", key="props", default=nearest_anchor_date_today())
    dkey = to_datestr(d)

    contents = st.session_state.get("daily_contents", {}).get(dkey, [])
    if not contents:
        st.info("이 날짜에 콘텐츠가 없습니다."); return

    with st.expander("➕ 소품 추가/수정", expanded=False):
        for i,c in enumerate(contents):
            cid=c.get("id")
            with st.expander(f"#{i+1}. {c.get('title','(제목 없음)')}", expanded=False):
                items = st.session_state.setdefault("content_props", {}).setdefault(cid, [])
                col1,col2,col3,col4=st.columns([2,2,1,1.2])
                with col1: name=st.text_input("소품명", key=f"pn_{cid}")
                with col2: vendor=st.text_input("구매처", key=f"pv_{cid}")
                with col3: qty=st.number_input("개수",min_value=1,value=1,step=1,key=f"pq_{cid}")
                with col4: status=st.selectbox("상태",["예정","주문완료","수령완료"],key=f"ps_{cid}")
                if st.button("추가", key=f"pa_{cid}"):
                    items.append({"name":name,"vendor":vendor,"quantity":qty,"status":status})
                    storage.autosave_maybe(); st.rerun()

                for p in items:
                    st.write(f"- {p.get('name','')}/{p.get('vendor','')}/{p.get('quantity',1)}개/{DOT.get(p.get('status','예정'),'🔴')}")

    st.markdown("---")
    st.markdown(f"### 📦 {d.strftime('%m월 %d일')} 소품 요약")
    for i,c in enumerate(contents):
        cid=c.get("id")
        left,right=st.columns([0.9,2.1])
        with left: st.markdown(f"**#{i+1}. {c.get('title','(제목 없음)')}**")
        with right:
            lines=[]
            for p in st.session_state.get("content_props", {}).get(cid, []):
                lines.append(f"{p.get('name','')}/{p.get('vendor','')}/{p.get('quantity',1)}개/{DOT.get(p.get('status','예정'),'🔴')}")
            (st.markdown("  \n".join(lines)) if lines else st.caption("소품 없음"))
