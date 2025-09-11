# modules/dashboard.py
from datetime import datetime, date
import streamlit as st
import pandas as pd

UPLOAD_STATUS_OPTIONS = ["촬영전", "촬영완료", "편집완료", "업로드완료"]
UPLOAD_STATUS_EMOJI   = {"촬영전":"🔵","촬영완료":"🟡","편집완료":"🟠","업로드완료":"🟢"}
PROP_STATUS_EMOJI     = {"예정":"🔴", "주문완료":"🟡", "수령완료":"🟢"}

def _nearest_content_anchor_date():
    """오늘(현지) 기준, 콘텐츠가 존재하는 '가장 최근 날짜'를 anchor로 선택
    - 오늘(>= today) 중 가장 가까운 날짜 우선
    - 없으면 과거 중 가장 최신 날짜
    - 없으면 오늘
    """
    contents = st.session_state.get('daily_contents', {})
    if not contents:
        return date.today()
    dates = sorted([datetime.strptime(d, "%Y-%m-%d").date() for d, items in contents.items() if items])
    if not dates:
        return date.today()
    today = date.today()
    future_or_today = [d for d in dates if d >= today]
    return (future_or_today[0] if future_or_today else dates[-1])

def _count_upload_status_for_date(dkey: str):
    us = st.session_state.get('upload_status', {})
    rows = []
    for idx, content in enumerate(st.session_state.get('daily_contents', {}).get(dkey, [])):
        cid = content.get('id', f"{dkey}_{idx}")
        status = us.get(cid, '촬영전')
        rows.append(status)
    return {s: rows.count(s) for s in UPLOAD_STATUS_OPTIONS}

def _props_breakdown_for_date(dkey: str):
    props = st.session_state.get('content_props', {})
    total = red = yel = grn = 0
    for idx, content in enumerate(st.session_state.get('daily_contents', {}).get(dkey, [])):
        cid = content.get('id', f"{dkey}_{idx}")
        items = props.get(cid, []) or []
        total += len(items)
        for p in items:
            s = p.get('status', '예정')
            if s == '예정': red += 1
            elif s == '주문완료': yel += 1
            elif s == '수령완료': grn += 1
    return total, red, yel, grn

def _schedule_span_for_date(dkey: str):
    scheds = st.session_state.get('schedules', {}).get(dkey, [])
    if not scheds:
        return None
    try:
        starts = sorted([s['start'] for s in scheds])
        ends   = sorted([s['end']   for s in scheds])
        if starts and ends:
            return f"{starts[0]} ~ {ends[-1]}"
    except Exception:
        pass
    return None

def render():
    st.subheader("📊 메인 대시보드")

    # 1) 앵커 날짜 계산
    anchor = _nearest_content_anchor_date()
    dkey = anchor.strftime("%Y-%m-%d")

    # 선택 UI (필요 시 수동 변경도 가능)
    c1, c2, c3 = st.columns([2,1.2,1.2])
    with c1:
        st.caption("오늘 기준 가장 가까운 콘텐츠 날짜를 자동 선택합니다.")
        picked = st.date_input("기준 날짜", value=anchor, key="dashboard_anchor_date")
        dkey = picked.strftime("%Y-%m-%d")
    with c2:
        contents_today = st.session_state.get('daily_contents', {}).get(dkey, [])
        st.metric("콘텐츠 개수", f"{len(contents_today)}개")
    with c3:
        scheds_today = st.session_state.get('schedules', {}).get(dkey, [])
        st.metric("일정(타임테이블)", f"{len(scheds_today)}개")

    st.divider()

    # 2) 업로드 상태 요약
    status_counts = _count_upload_status_for_date(dkey)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("촬영 전",     f"{status_counts.get('촬영전', 0)}개", help="업로드 상태: 촬영전")
    with m2: st.metric("촬영 완료",   f"{status_counts.get('촬영완료', 0)}개", help="업로드 상태: 촬영완료")
    with m3: st.metric("편집 완료",   f"{status_counts.get('편집완료', 0)}개", help="업로드 상태: 편집완료")
    with m4: st.metric("업로드 완료", f"{status_counts.get('업로드완료', 0)}개", help="업로드 상태: 업로드완료")

    # 3) 소품 요약
    st.markdown("### 🛍️ 소품 현황")
    total, red, yel, grn = _props_breakdown_for_date(dkey)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("전체 소품", f"{total}개")
    with c2: st.metric("예정(🔴)", f"{red}개")
    with c3: st.metric("주문완료(🟡)", f"{yel}개")
    with c4: st.metric("수령완료(🟢)", f"{grn}개")

    # 4) 타임테이블 요약
    st.markdown("### ⏰ 타임테이블")
    span = _schedule_span_for_date(dkey)
    if span:
        st.info(f"전체 시간 범위: **{span}**")
    else:
        st.info("해당 날짜의 일정이 없습니다.")

    # 5) 콘텐츠 리스트(핵심만)
    st.markdown("### 📝 콘텐츠 개요")
    contents = st.session_state.get('daily_contents', {}).get(dkey, [])
    if not contents:
        st.write("등록된 콘텐츠가 없습니다.")
        return

    rows = []
    us = st.session_state.get('upload_status', {})
    for idx, c in enumerate(contents):
        cid = c.get('id', f"{dkey}_{idx}")
        status = us.get(cid, '촬영전')
        rows.append({
            "No.": idx+1,
            "제목": c.get('title', '(제목 없음)'),
            "출연": ", ".join(c.get('performers', [])),
            "업로드상태": f"{UPLOAD_STATUS_EMOJI.get(status,'')} {status}"
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # 6) 소품/타임테이블 빠른 스내핑
    with st.expander("🔎 빠른 스냅샷: 소품 & 타임테이블"):
        snap_cols = st.columns(2)

        # 좌: 소품
        with snap_cols[0]:
            prop_rows = []
            props = st.session_state.get('content_props', {})
            for idx, c in enumerate(contents):
                cid = c.get('id', f"{dkey}_{idx}")
                for p in props.get(cid, []):
                    prop_rows.append({
                        "콘텐츠": f"#{idx+1}. {c.get('title', '(제목 없음)')}",
                        "소품명": p.get("name",""),
                        "구매처": p.get("vendor",""),
                        "개수":   p.get("quantity",1),
                        "상태":   p.get("status","예정"),
                        "표시":   PROP_STATUS_EMOJI.get(p.get("status","예정"), "🔴"),
                    })
            st.markdown("**소품 요약**")
            if prop_rows:
                st.dataframe(pd.DataFrame(prop_rows), use_container_width=True, hide_index=True)
            else:
                st.caption("이 날짜에 등록된 소품이 없습니다.")

        # 우: 타임테이블
        with snap_cols[1]:
            scheds = st.session_state.get('schedules', {}).get(dkey, [])
            sched_rows = [{"시간": f"{s['start']}~{s['end']}", "유형": s.get("type",""), "제목": s.get("title","")} for s in scheds]
            st.markdown("**타임테이블 요약**")
            if sched_rows:
                st.dataframe(pd.DataFrame(sched_rows), use_container_width=True, hide_index=True)
            else:
                st.caption("이 날짜의 타임테이블이 비어있습니다.")

