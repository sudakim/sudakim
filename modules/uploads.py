# modules/uploads.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from .ui import pick_date_with_markers, nearest_anchor_date_today, to_datestr
from modules import storage
# ... 데이터 수정 직후에:
storage.autosave_maybe()

STATES = ["촬영전","촬영완료","편집완료","업로드완료"]
EMOJI  = {"촬영전":"🔵","촬영완료":"🟡","편집완료":"🟠","업로드완료":"🟢"}

def render():
    st.subheader("📹 영상 업로드 현황")

    anchor = nearest_anchor_date_today()
    d = pick_date_with_markers(selected=anchor, key="up_calendar")
    dkey = to_datestr(d)

    contents = st.session_state.get("daily_contents", {}).get(dkey, [])
    us = st.session_state.setdefault("upload_status", {})

    if not contents:
        st.info("이 날짜에 콘텐츠가 없습니다.")
        return

    with st.expander("⚙️ 상태 일괄 변경", expanded=False):
        bulk_to = st.selectbox("모두를 다음 상태로", STATES)
        if st.button("일괄 적용"):
            for c in contents:
                us[c["id"]] = bulk_to
            st.rerun()

    filt = st.multiselect("표시할 상태", STATES, default=STATES)
    rows=[]
    for i, c in enumerate(contents):
        state = us.get(c["id"], "촬영전")
        if state not in filt: 
            continue
        rows.append({
            "No.": i+1,
            "제목": c.get("title",""),
            "출연": ", ".join(c.get("performers", [])),
            "상태": f"{EMOJI.get(state,'')} {state}"
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("### ✍️ 개별 수정")
    for i, c in enumerate(contents):
        cur = us.get(c["id"], "촬영전")
        new = st.selectbox(f"#{i+1} {c.get('title','')}", STATES, index=STATES.index(cur), key=f"sel_{c['id']}")
        if new != cur:
            us[c["id"]] = new
