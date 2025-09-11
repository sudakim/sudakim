# modules/dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime, date

UPLOAD_STATUS_EMOJI = {"촬영전":"🔵","촬영완료":"🟡","편집완료":"🟠","업로드완료":"🟢"}
PROP_STATUS_EMOJI   = {"예정":"🔴","주문완료":"🟡","수령완료":"🟢"}

def _anchor_date():
    contents = st.session_state.get('daily_contents', {})
    if not contents:
        return date.today()
    days = []
    for d, items in contents.items():
        if not items: 
            continue
        try: days.append(datetime.strptime(d, "%Y-%m-%d").date())
        except: pass
    if not days:
        return date.today()
    today = date.today()
    fut = [d for d in sorted(days) if d >= today]
    return fut[0] if fut else sorted(days)[-1]

def _make_tables(dkey: str):
    # 콘텐츠 개요
    rows = []
    contents = st.session_state.get('daily_contents', {}).get(dkey, [])
    us = st.session_state.get('upload_status', {})
    for i, c in enumerate(contents):
        cid = c.get("id", f"{dkey}_{i}")
        status = us.get(cid, "촬영전")
        rows.append({
            "No.": i+1,
            "제목": c.get("title","(제목 없음)"),
            "출연": ", ".join(c.get("performers", [])),
            "업로드상태": f"{UPLOAD_STATUS_EMOJI.get(status,'')} {status}",
        })
    contents_df = pd.DataFrame(rows)

    # 소품 요약
    props_rows = []
    props = st.session_state.get('content_props', {})
    for i, c in enumerate(contents):
        cid = c.get("id", f"{dkey}_{i}")
        for p in props.get(cid, []) or []:
            props_rows.append({
                "콘텐츠": f"#{i+1}. {c.get('title','(제목 없음)')}",
                "소품명": p.get("name",""),
                "구매처": p.get("vendor",""),
                "개수":   p.get("quantity",1),
                "상태":   p.get("status","예정"),
                "표시":   PROP_STATUS_EMOJI.get(p.get("status","예정"), "🔴"),
            })
    props_df = pd.DataFrame(props_rows)

    # 타임테이블 요약
    scheds = st.session_state.get('schedules', {}).get(dkey, [])
    sch_rows = [{"시간": f"{s.get('start','')}~{s.get('end','')}",
                 "유형": s.get('type',''),
                 "제목": s.get('title','')} for s in scheds]
    timetable_df = pd.DataFrame(sch_rows)

    return contents_df, props_df, timetable_df

def render():
    """인자 없이 호출하는 간단 대시보드"""
    anchor = _anchor_date()
    dkey = anchor.strftime("%Y-%m-%d")

    st.header("📑 콘텐츠 개요")
    # 기준 날짜는 자동 선택되지만, 바꾸고 싶으면 여기서 바꾸도록 함
    picked = st.date_input("기준 날짜", value=anchor, key="dashboard_anchor")
    dkey = picked.strftime("%Y-%m-%d")

    contents_df, props_df, timetable_df = _make_tables(dkey)

    st.dataframe(contents_df, use_container_width=True, hide_index=True)

    with st.expander("📌 빠른 스냅샷: 소품 & 타임테이블", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("소품 요약")
            if len(props_df):
                st.dataframe(props_df, use_container_width=True, hide_index=True)
            else:
                st.caption("소품 데이터가 없습니다.")
        with c2:
            st.subheader("타임테이블 요약")
            if len(timetable_df):
                st.dataframe(timetable_df, use_container_width=True, hide_index=True)
            else:
                st.caption("타임테이블이 없습니다.")
