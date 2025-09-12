# youtube_manager.py - 유튜브 콘텐츠 매니저 (UI 개선 버전)
import streamlit as st
from modules import storage
from modules import dashboard, planning, props, timetable, uploads
import requests, json
from modules.github_store import _get, _auth_headers

# ===== 🆘 강제 가져오기(원클릭 복구) =====
# 사이드바 어딘가에 붙이세요 (imports는 블록 안에 포함됨)
with st.sidebar.expander("🆘 강제 가져오기 (Gist)", expanded=False):
    import json, requests
    from datetime import date, datetime

    # secrets 기본값 읽기
    def _get_secret(name, default=None):
        try:
            return st.secrets.get(name, default)
        except Exception:
            return default

    # (1) 입력값
    _def_gist_id   = _get_secret("gist_id", "")
    _def_token     = _get_secret("github_token", _get_secret("gh_token", ""))
    _def_filename  = _get_secret("gist_filename", "youtube_data.json")

    gi = st.text_input("Gist ID", value=_def_gist_id, key="rescue_gist_id")
    tk = st.text_input("GitHub Token", value=_def_token, type="password", key="rescue_token")
    fn = st.text_input("파일명", value=_def_filename, key="rescue_filename")

    # (2) 오늘 기준 가장 가까운 날짜 계산(원래 함수가 있으면 그걸 사용, 없으면 로컬 계산)
    def _nearest_date_from_state():
        # 앱에 같은 기능 함수가 있으면 우선 사용
        try:
            return nearest_content_date_from_today()  # 기존 코드에 있을 때
        except Exception:
            pass
        # Fallback 계산
        dc = st.session_state.get("daily_contents", {}) or {}
        days = []
        for k, items in dc.items():
            if not items:
                continue
            try:
                days.append(datetime.strptime(k, "%Y-%m-%d").date())
            except Exception:
                continue
        if not days:
            return date.today()
        today = date.today()
        fut = [d for d in sorted(days) if d >= today]
        return fut[0] if fut else sorted(days)[-1]

    # (3) Gist에서 파일 읽기
    def _fetch_gist_json(gist_id: str, token: str, filename: str):
        if not gist_id:
            raise RuntimeError("Gist ID가 비어 있습니다.")
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"token {token}"

        meta = requests.get(f"https://api.github.com/gists/{gist_id}",
                            headers=headers, timeout=20)
        meta.raise_for_status()
        files = (meta.json() or {}).get("files", {}) or {}

        # 파일명 우선 고정: 입력값 → youtube_data.json → data_store.json
        pick = None
        for want in [filename, "youtube_data.json", "data_store.json"]:
            for k in files.keys():
                if k.lower() == want.lower():
                    pick = k
                    break
            if pick:
                break
        if not pick:
            raise RuntimeError("지정한 파일을 Gist에서 찾을 수 없습니다.")

        info = files[pick]
        if info.get("truncated") and info.get("raw_url"):
            raw = requests.get(info["raw_url"], timeout=20).text
            return json.loads(raw)
        return json.loads(info.get("content", "") or "{}")

    # (4) 세션으로 주입(레거시 키 자동 매핑)
    def _inject_to_session(payload: dict):
        st.session_state.setdefault("daily_contents", {})
        st.session_state.setdefault("content_props", {})
        st.session_state.setdefault("schedules", {})
        st.session_state.setdefault("upload_status", {})

        # 레거시 → 현재
        if "contents" in payload:
            st.session_state["daily_contents"] = payload["contents"]
        if "props" in payload:
            st.session_state["content_props"] = payload["props"]
        if "schedules" in payload:
            st.session_state["schedules"] = payload["schedules"]
        if "upload_status" in payload:
            st.session_state["upload_status"] = payload["upload_status"]

    # (5) 실행 버튼
    if st.button("🔧 Gist에서 불러와 적용", use_container_width=True):
        try:
            data = _fetch_gist_json(gi.strip(), tk.strip(), fn.strip())
            if not isinstance(data, dict):
                st.error("가져온 JSON 형식이 올바르지 않습니다.")
            else:
                _inject_to_session(data)

                # 기준 날짜 리셋 + 위젯 동기화
                anchor = _nearest_date_from_state()
                st.session_state["selected_date"] = anchor
                # 위젯 키를 쓰는 경우들 동기화(있을 때만)
                for k in ["content_date_widget", "dashboard_anchor_date", "plan_date", "props_date", "tt_date", "up_date"]:
                    if k in st.session_state:
                        st.session_state[k] = anchor

                # 자동 저장(있으면 사용)
                try:
                    from modules import storage
                    storage.autosave_maybe()
                except Exception:
                    pass

                st.success("강제가져오기 → 주입 → 날짜리셋 → 저장 완료!")
                st.rerun()
        except Exception as e:
            st.error(f"실패: {e}")

    # (6) 현재 상태 간단 확인용
    dc = st.session_state.get("daily_contents", {})
    st.caption(f"dates: {len(dc)} | first: {list(dc.keys())[:3] if dc else 'None'}")


# 페이지 설정 (한 번만 설정)
st.set_page_config(
    page_title="🎬 유튜브 콘텐츠 매니저", 
    page_icon="🎬", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/help',
        'Report a bug': 'https://github.com/your-repo/bug',
        'About': '# 유튜브 콘텐츠 매니저\n모던한 UI로 개선된 콘텐츠 관리 시스템'
    }
)

# ★ 앱 시작 시: GitHub/Gist/Local에서 자동 로드
storage.load_state()

# 간단한 사이드바 적용 (테마 시스템 제거)
from modules.ui_enhanced import simple_sidebar
simple_sidebar()

# 기존 저장 섹션을 사이드바에 추가
with st.sidebar:
    st.markdown("---")
    st.markdown("### 💾 데이터 저장")
    st.toggle("자동 저장", key="_autosave", value=st.session_state.get("_autosave", True))
    if st.button("수동 저장", use_container_width=True):
        storage.save_state()
        st.success("저장 완료")
    src = st.session_state.get("_storage_source") or "unknown"
    when = st.session_state.get("_last_saved") or "-"
    st.caption(f"💾 소스: {src}")
    st.caption(f"🕒 최종 저장: {when}")

# 크롬 다크모드에 반응하는 간단한 색상 시스템
st.markdown("""
<style>
/* 기본 라이트 모드 스타일 */
.stApp {
    background-color: #FFFFFF;
    color: #1F2937;
}

/* 모든 텍스트 요소 기본 스타일 */
.main .block-container {
    color: #1F2937;
}

.stMarkdown, .stMarkdown p, .stMarkdown div, .stMarkdown span {
    color: #1F2937;
}

.stInfo, .stSuccess, .stWarning, .stError {
    color: #1F2937;
}

.caption, .stCaption {
    color: #6B7280;
}

/* 입력 필드 기본 스타일 */
.stTextInput > div > div > input {
    background-color: white;
    border: 1px solid #D1D5DB;
    color: #1F2937;
}

.stTextInput label {
    color: #1F2937;
    font-weight: 500;
}

/* 날짜 선택기 스타일 */
.stDateInput > div > div > input {
    background-color: white;
    border: 1px solid #D1D5DB;
    color: #1F2937;
}

.stDateInput label {
    color: #1F2937;
    font-weight: 500;
}

/* 선택박스 스타일 */
.stSelectbox > div > div > div {
    background-color: white;
    border: 1px solid #D1D5DB;
    color: #1F2937;
}

.stSelectbox label {
    color: #1F2937;
    font-weight: 500;
}

/* 체크박스 및 토글 스타일 */
.stCheckbox label, .stToggle label {
    color: #1F2937;
    font-weight: 500;
}

/* 사이드바 스타일 개선 - 다크 테마 적용 */
section[data-testid="stSidebar"] {
    background-color: #2C3E50 !important;
}

section[data-testid="stSidebar"] .stMarkdown {
    color: white !important;
}

section[data-testid="stSidebar"] .stSelectbox label {
    color: white !important;
}

section[data-testid="stSidebar"] .stTextInput label {
    color: white !important;
}

section[data-testid="stSidebar"] .stButton button {
    background-color: #DC2626 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
}

section[data-testid="stSidebar"] .stToggle label {
    color: white !important;
}

section[data-testid="stSidebar"] .stCheckbox label {
    color: white !important;
}

/* 크롬 다크모드 감지 및 자동 대응 */
@media (prefers-color-scheme: dark) {
    .stApp {
        background-color: #1F2937;
        color: #F9FAFB;
    }
    
    .main .block-container {
        background-color: #1F2937;
        color: #F9FAFB;
    }
    
    .stMarkdown, .stMarkdown p, .stMarkdown div, .stMarkdown span {
        color: #F9FAFB;
    }
    
    .stInfo, .stSuccess, .stWarning, .stError {
        color: #F9FAFB;
        background-color: #374151;
    }
    
    .caption, .stCaption {
        color: #D1D5DB;
    }
    
    /* 다크모드 입력 필드 */
    .stTextInput > div > div > input,
    .stDateInput > div > div > input,
    .stSelectbox > div > div > div {
        background-color: #374151;
        border: 1px solid #4B5563;
        color: #F9FAFB;
    }
    
    .stTextInput label,
    .stDateInput label,
    .stSelectbox label,
    .stCheckbox label,
    .stToggle label {
        color: #F9FAFB;
    }
    
    /* 다크모드 카드 스타일 */
    .content-card {
        background-color: #374151;
        color: #F9FAFB;
        border-color: #4B5563;
    }
}

/* 탭 스타일 개선 */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: white;
    border-radius: 12px;
    padding: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 12px 20px;
    font-weight: 500;
    border: none;
    font-size: 16px;
    transition: all 0.3s ease;
}

.stTabs [aria-selected="true"] {
    background-color: #FF6B6B;
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(255, 107, 107, 0.3);
}

.stTabs [aria-selected="false"] {
    background-color: #f8f9fa;
    color: #666;
}

.stTabs [aria-selected="false"]:hover {
    background-color: #e9ecef;
    transform: translateY(-1px);
}

/* 데이터프레임 스타일 개선 */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* 메인 콘텐츠 영역 */
.main .block-container {
    padding-top: 2rem;
    max-width: 100%;
}

/* 카드 스타일 */
.element-container div[data-stale="false"] {
    background-color: white;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
}

/* 메트릭 카드 개선 */
[data-testid="metric-container"] {
    background-color: white;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    border: 1px solid #e9ecef;
}

/* 달력 스타일 개선 */
.fc {
    background-color: white !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    border: 1px solid #D1D5DB !important;
    overflow: hidden !important;
}

.fc-header-toolbar {
    background-color: #F9FAFB !important;
    padding: 16px !important;
    border-bottom: 1px solid #D1D5DB !important;
}

.fc-button-primary {
    background-color: #DC2626 !important;
    border-color: #DC2626 !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}

.fc-button-primary:hover {
    background-color: #B91C1C !important;
    border-color: #B91C1C !important;
}

.fc-day-today {
    background-color: rgba(220, 38, 38, 0.1) !important;
}

.fc-daygrid-day-number {
    color: #111827 !important;
    font-weight: 500 !important;
}

.fc-col-header-cell {
    background-color: #F3F4F6 !important;
    color: #374151 !important;
    font-weight: 600 !important;
}

/* 콘텐츠가 있는 날짜 마커 스타일 */
.fc-event {
    border-radius: 4px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
}

.fc-event-title {
    font-weight: bold !important;
}

/* 더 명확한 마커 표시 */
.fc-daygrid-event {
    margin: 1px !important;
    border-radius: 3px !important;
}
</style>
""", unsafe_allow_html=True)

# 탭 구성
dash_tab, tab1, tab2, tab3, tab4 = st.tabs(
    ["🏠 대시보드", "📝 콘텐츠 기획", "🛍️ 소품 구매", "⏰ 타임테이블", "📹 영상 업로드 현황"]
)

with dash_tab:
    dashboard.render()
with tab1:
    planning.render()
with tab2:
    props.render()
with tab3:
    timetable.render()
with tab4:
    uploads.render()