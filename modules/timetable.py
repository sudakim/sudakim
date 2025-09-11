# modules/timetable.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from datetime import time
from .ui import pick_date_with_markers, nearest_anchor_date_today, to_datestr
from modules import storage
# ... 데이터 수정 직후에:
storage.autosave_maybe()

def render():
    st.subheader("⏰ 타임테이블")

    anchor = nearest_anchor_date_today()
    d = pick_date_with_markers(selected=anchor, key="tt_calendar")
    dkey = to_datestr(d)

    contents = st.session_state.get("daily_contents", {}).get(dkey, [])
    schedules = st.session_state.setdefault("schedules", {}).setdefault(dkey, [])

    if not contents:
        st.info("이 날짜에 콘텐츠가 없습니다.")
        return

    with st.expander("➕ 일정 추가", expanded=True):
        options = {f"#{i+1}. {c.get('title','(제목 없음)')}": c["id"] for i, c in enumerate(contents)}
        label = st.selectbox("콘텐츠", list(options.keys()))
        start_t, end_t = st.slider("시간", value=(time(12,40), time(13,30)), format="HH:mm", key="tt_range")
        job = st.selectbox("유형", ["촬영","리허설","회의","편집"], key="tt_type")
        title_override = st.text_input("표시 제목(비우면 콘텐츠 제목 사용)")
        if st.button("추가", type="primary"):
            cid = options[label]
            title = title_override or label.split(". ",1)[1]
            schedules.append({
                "start": start_t.strftime("%H:%M"),
                "end": end_t.strftime("%H:%M"),
                "type": job,
                "title": title,
                "cid": cid
            })
            st.rerun()

    if schedules:
        st.markdown(f"### 📅 {d.strftime('%m월 %d일')} 일정")
        st.dataframe(pd.DataFrame(schedules), use_container_width=True, hide_index=True)
    else:
        st.caption("일정 없음")
