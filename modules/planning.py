# modules/planning.py
from __future__ import annotations
import streamlit as st
from datetime import datetime
import uuid
from .ui import date_picker_with_toggle, nearest_anchor_date_today, to_datestr
from modules import storage

def _ensure():
    st.session_state.setdefault("daily_contents", {})
    st.session_state.setdefault("upload_status", {})
    st.session_state.setdefault("content_props", {})
    st.session_state.setdefault("schedules", {})

def render():
    _ensure()
    st.subheader("📝 콘텐츠 기획")

    d = date_picker_with_toggle("날짜 선택", key="plan", default=nearest_anchor_date_today())
    dkey = to_datestr(d)

    # 상단: 양식 추가(한 줄)
    c1, c2, c3 = st.columns([1.2,0.7,0.6])
    with c1:
        st.caption("선택 날짜"); st.write(d.strftime("%Y/%m/%d"))
    with c2:
        count = st.number_input("개수", min_value=1, max_value=20, value=3, step=1, key="plan_new_count")
    with c3:
        if st.button("✨ 양식 추가", use_container_width=True):
            st.session_state["daily_contents"].setdefault(dkey, [])
            for _ in range(int(count)):
                cid = str(uuid.uuid4())[:8]
                st.session_state["daily_contents"][dkey].append({"id":cid,"title":"(제목 없음)","performers":[],"draft":"","links":[]})
                st.session_state["upload_status"][cid]="촬영전"
            storage.autosave_maybe(); st.rerun()

    st.markdown("---")

    contents = st.session_state["daily_contents"].get(dkey, [])
    if not contents:
        st.info("이 날짜에 콘텐츠가 없습니다."); return

    st.markdown(f"### 🗓️ {d.strftime('%m월 %d일')} 콘텐츠")
    for i,c in enumerate(contents):
        cid = c.get("id")
        state = st.session_state["upload_status"].get(cid,"촬영전")
        dot = {"촬영전":"🔵","촬영완료":"🟡","편집완료":"🟠","업로드완료":"🟢"}.get(state,"🔵")
        with st.expander(f"{dot} #{i+1}. {c.get('title','(제목 없음)')}", expanded=False):
            col_title, col_date, col_move, col_del = st.columns([3,1.2,0.8,0.2])
            with col_title:
                c["title"]=st.text_input("제목", value=c.get("title",""), key=f"title_{cid}")
            with col_date:
                move_to = st.date_input("이동 날짜", value=d, key=f"mv_date_{cid}", format="YYYY/MM/DD")
            with col_move:
                if st.button("이동", key=f"btn_move_{cid}"):
                    st.session_state["daily_contents"][dkey].pop(i)
                    new_key = to_datestr(move_to)
                    st.session_state["daily_contents"].setdefault(new_key, []).append(c)
                    old = st.session_state["schedules"].get(dkey, [])
                    keep, mv = [], []
                    for s in old:
                        (mv if s.get("cid")==cid else keep).append(s)
                    st.session_state["schedules"][dkey]=keep
                    if mv: st.session_state["schedules"].setdefault(new_key, []).extend(mv)
                    storage.autosave_maybe(); st.rerun()
            with col_del:
                st.markdown(" ")
                if st.button("🗑️", key=f"btn_del_{cid}"):
                    st.session_state["daily_contents"][dkey].pop(i)
                    storage.autosave_maybe(); st.rerun()

            colA,colB = st.columns([1.5,2])
            with colA:
                perf = st.text_input("출연자(콤마)", value=", ".join(c.get("performers", [])), key=f"perf_{cid}")
                c["performers"]=[x.strip() for x in perf.split(",") if x.strip()]
                links_raw = st.text_area("참고 링크(줄바꿈)", value="\n".join(c.get("links", [])), height=120, key=f"links_{cid}")
                c["links"]=[x.strip() for x in links_raw.splitlines() if x.strip()]
            with colB:
                c["draft"]=st.text_area("초안", value=c.get("draft",""), height=240, key=f"draft_{cid}")
