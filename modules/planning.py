# modules/planning.py
from __future__ import annotations
import streamlit as st
from datetime import datetime, date
import uuid
from typing import List, Dict, Any

from modules import storage
# 최신 토글 달력 + 오늘 기준 최근 날짜 + 날짜 문자열 변환
from .ui import date_picker_with_toggle, nearest_anchor_date_today, to_datestr


# ---------- 내부 유틸 ----------

def _collect_days() -> List[date]:
    """콘텐츠가 하나라도 있는 날짜만 수집해 정렬"""
    dc = st.session_state.get("daily_contents", {}) or {}
    days: List[date] = []
    for k, v in dc.items():
        if not v:
            continue
        try:
            days.append(datetime.strptime(k, "%Y-%m-%d").date())
        except Exception:
            pass
    return sorted(set(days))


def _ensure_state():
    st.session_state.setdefault("daily_contents", {})
    st.session_state.setdefault("upload_status", {})
    st.session_state.setdefault("content_props", {})
    st.session_state.setdefault("schedules", {})
    # 선택 날짜 초기화: 오늘 기준 가장 가까운 날짜
    if "plan_selected" not in st.session_state:
        st.session_state.plan_selected = nearest_anchor_date_today()


# ---------- 메인 렌더 ----------

def render():
    _ensure_state()
    st.subheader("📝 콘텐츠 기획")

    # ===== 상단: 최신 토글 달력(마커) =====
    # ❗ 여기 수정: label= 키워드 사용하지 말고 첫 번째 인자로 문자열 전달
    sel = date_picker_with_toggle(
        "날짜 선택",                 # ← 포지셔널 인자로 라벨 전달
        key="planning",
        default=st.session_state.plan_selected,
    )
    # 선택값 유지
    st.session_state.plan_selected = sel

    d = st.session_state.plan_selected
    dkey = to_datestr(d)

    st.markdown("---")

    # ===== 양식 추가 라인: 한 줄 정렬(개수 박스 폭 ↓ + 버튼 컴팩트) =====
    a1, a2, a3 = st.columns([1.2, 0.4, 0.6], gap="small")

    with a1:
        st.caption("선택 날짜")
        st.write(d.strftime("%Y/%m/%d"))

    with a2:
        count = st.number_input(
            label="개수",
            min_value=1,
            max_value=20,
            value=3,
            step=1,
            key="plan_new_count",
            label_visibility="collapsed",
        )

    with a3:
        if st.button("✨ 양식 추가", use_container_width=True, key="btn_add_templates"):
            st.session_state["daily_contents"].setdefault(dkey, [])
            base = len(st.session_state["daily_contents"][dkey])
            for i in range(int(count)):
                cid = str(uuid.uuid4())[:8]
                st.session_state["daily_contents"][dkey].append({
                    "id": cid,
                    "title": "",
                    "performers": [],
                    # 본문 탭 필드
                    "draft": "",
                    "revision": "",
                    "feedback": "",
                    "final": "",
                    # 참고 링크(줄바꿈 구분)
                    "reference": "",
                })
                st.session_state["upload_status"][cid] = "촬영전"
            storage.autosave_maybe()
            st.rerun()

    st.divider()

    # ===== 콘텐츠 카드들 =====
    contents: List[Dict[str, Any]] = st.session_state["daily_contents"].get(dkey, [])
    if not contents:
        st.info("이 날짜에 콘텐츠가 없습니다.")
        return

    st.subheader(f"📋 {d.strftime('%m월 %d일')} 콘텐츠")
    for idx, c in enumerate(contents):
        cid = c.get("id", f"{dkey}_{idx}")
        with st.expander(f"#{idx+1}. {c.get('title','제목 없음')}", expanded=False):

            # 상단 한 줄: 제목 / 이동 날짜 / 이동 / 삭제
            r1c1, r1c2, r1c3, r1c4 = st.columns([3, 1.3, 0.8, 0.2])

            with r1c1:
                c["title"] = st.text_input("제목", value=c.get("title", ""), key=f"title_{cid}")

            with r1c2:
                mv_date = st.date_input("이동 날짜", value=d, key=f"mv_date_{cid}", format="YYYY/MM/DD")

            with r1c3:
                st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
                if st.button("이동", key=f"btn_move_{cid}"):
                    # 현재 날짜 리스트에서 제거
                    st.session_state["daily_contents"][dkey].pop(idx)
                    new_key = to_datestr(mv_date)
                    # 대상 날짜로 추가
                    st.session_state["daily_contents"].setdefault(new_key, []).append(c)
                    # 타임테이블 연동 함께 이동
                    old = st.session_state.get("schedules", {}).get(dkey, [])
                    keep, mv = [], []
                    for s in old:
                        (mv if s.get("cid") == cid else keep).append(s)
                    st.session_state["schedules"][dkey] = keep
                    if mv:
                        st.session_state["schedules"].setdefault(new_key, []).extend(mv)
                    storage.autosave_maybe()
                    st.rerun()

            with r1c4:
                st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"btn_del_{cid}"):
                    st.session_state["daily_contents"][dkey].pop(idx)
                    storage.autosave_maybe()
                    st.rerun()

            # 출연자 / 참고 링크
            b1, b2 = st.columns([1.2, 2.8])
            with b1:
                perf_raw = st.text_input(
                    "출연자(콤마)",
                    value=", ".join(c.get("performers", [])),
                    key=f"perf_{cid}",
                )
                c["performers"] = [x.strip() for x in perf_raw.split(",") if x.strip()]
            with b2:
                c["reference"] = st.text_area(
                    "참고 링크(줄바꿈)",
                    value=c.get("reference", ""),
                    height=100,
                    key=f"ref_{cid}",
                )

            # 본문 탭: 초안/의견/피드백/최종안
            tab1, tab2, tab3, tab4 = st.tabs(["초안", "의견", "피드백", "최종안"])
            with tab1:
                c["draft"] = st.text_area("초안", value=c.get("draft", ""), height=300, key=f"draft_{cid}")
            with tab2:
                c["revision"] = st.text_area("의견", value=c.get("revision", ""), height=160, key=f"rev_{cid}")
            with tab3:
                c["feedback"] = st.text_area("피드백", value=c.get("feedback", ""), height=160, key=f"fb_{cid}")
            with tab4:
                c["final"] = st.text_area("최종안", value=c.get("final", ""), height=160, key=f"final_{cid}")

            st.caption("텍스트 변경은 주기 저장으로 자동 반영됩니다.")
