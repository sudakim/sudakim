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
        try:
            # 스냅샷 갱신으로 이후 변경 감지 정확도 향상
            st.session_state["_last_snapshot"] = storage._snapshot_str()
        except Exception:
            pass
        st.success("저장 완료")
    src = st.session_state.get("_storage_source") or "unknown"
    when = st.session_state.get("_last_saved") or "-"
    st.caption(f"💾 소스: {src}")
    st.caption(f"🕒 최종 저장: {when}")

# 🔥 JavaScript + CSS 강력한 다크모드 감지 및 강제 적용 🔥
st.markdown("""
<script>
// 🔥 강력한 다크모드 감지 및 실시간 적용 🔥
function applyTheme() {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // 🎯 모든 가능한 메인 영역 선택자들
    const selectors = [
        '.stApp',
        '.main', 
        '.main .block-container',
        'section[data-testid="main"]',
        '[data-testid="stAppViewContainer"]',
        '.element-container'
    ];
    
    if (isDark) {
        // 🌙 다크모드 강제 적용
        document.documentElement.setAttribute('data-theme', 'dark');
        document.body.style.setProperty('background-color', '#1F2937', 'important');
        
        // 모든 메인 영역에 다크모드 적용
        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                el.style.setProperty('background-color', '#1F2937', 'important');
                el.style.setProperty('color', '#FFFFFF', 'important');
            });
        });
        
        // 🔥 모든 요소 강제 흰색 텍스트
        document.querySelectorAll('*').forEach(el => {
            if (!el.tagName.match(/^(BUTTON|INPUT|SELECT|TEXTAREA)$/)) {
                el.style.setProperty('color', '#FFFFFF', 'important');
            }
        });
        
    } else {
        // 🌞 라이트모드 강제 적용  
        document.documentElement.setAttribute('data-theme', 'light');
        document.body.style.setProperty('background-color', '#FFFFFF', 'important');
        
        // 모든 메인 영역에 라이트모드 적용
        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                el.style.setProperty('background-color', '#FFFFFF', 'important');
                el.style.setProperty('color', '#000000', 'important');
            });
        });
        
        // 🔥 모든 요소 강제 검은색 텍스트
        document.querySelectorAll('*').forEach(el => {
            if (!el.tagName.match(/^(BUTTON|INPUT|SELECT|TEXTAREA)$/)) {
                el.style.setProperty('color', '#000000', 'important');
            }
        });
    }
}

// 페이지 로드 시 즉시 적용
applyTheme();

// 다크모드 변경 감지하여 실시간 적용
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyTheme);

// DOM 변경 감지하여 새로운 요소에도 적용
const observer = new MutationObserver(applyTheme);
observer.observe(document.body, { childList: true, subtree: true });

// 주기적으로도 체크 (보험용)
setInterval(applyTheme, 1000);
</script>

<style>
/* 🔥 스마트 CSS - 버튼/배너 색상 보존 🔥 */

/* 라이트모드 기본값 */
html, body, #root, .stApp, .main, .main > div, .block-container,
section[data-testid="main"], [data-testid="stAppViewContainer"], 
.element-container {
    background-color: #FFFFFF !important;
    color: #000000 !important;
}

/* 일반 텍스트만 색상 변경 */
.stMarkdown:not(.stButton *):not([style*="gradient"]) p,
.stMarkdown:not(.stButton *):not([style*="gradient"]) div,
.stMarkdown:not(.stButton *):not([style*="gradient"]) span,
h1:not(.stButton *), h2:not(.stButton *), h3:not(.stButton *), 
h4:not(.stButton *), h5:not(.stButton *), h6:not(.stButton *) {
    color: #000000 !important;
}

/* 🔥 다크모드 스마트 적용 🔥 */
@media (prefers-color-scheme: dark) {
    html, body, #root, .stApp, .main, .main > div, .block-container,
    section[data-testid="main"], [data-testid="stAppViewContainer"], 
    .element-container {
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
    }
    
    /* 일반 텍스트만 흰색으로 (버튼/배너 제외) */
    .stMarkdown:not(.stButton *):not([style*="gradient"]) p,
    .stMarkdown:not(.stButton *):not([style*="gradient"]) div,
    .stMarkdown:not(.stButton *):not([style*="gradient"]) span,
    h1:not(.stButton *), h2:not(.stButton *), h3:not(.stButton *), 
    h4:not(.stButton *), h5:not(.stButton *), h6:not(.stButton *) {
        color: #FFFFFF !important;
    }
    
    /* 사이드바 */
    section[data-testid="stSidebar"], 
    section[data-testid="stSidebar"] * {
        background-color: #374151 !important;
        color: #FFFFFF !important;
    }
    
    /* 정보박스들 */
    .stInfo, .stSuccess, .stWarning, .stError {
        background-color: #374151 !important;
        color: #FFFFFF !important;
    }
}

/* 🎨 버튼 스타일 보존 (라이트/다크 모드 공통) */
.stButton > button {
    background-color: #DC2626 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}

/* 🎯 배너/그라데이션 스타일 보존 */
[style*="gradient"] {
    color: white !important; /* 그라데이션 배경에는 항상 흰 글씨 */
}

[style*="background-color: #DC2626"],
[style*="background-color: rgb(220, 38, 38)"],
[style*="background: linear-gradient"] {
    color: white !important; /* 빨간색/그라데이션 배경에는 항상 흰 글씨 */
}

/* 🔥 달력 토글 스타일 개선 🔥 */
.stCheckbox, .stToggle {
    padding: 8px !important;
    border-radius: 8px !important;
}

.stCheckbox label, .stToggle label {
    font-weight: 500 !important;
    padding: 4px 8px !important;
}

/* 토글 버튼 자체 스타일 */
.stCheckbox input[type="checkbox"], 
.stToggle input[type="checkbox"] {
    accent-color: #DC2626 !important;
    transform: scale(1.2) !important;
}

/* 달력 아이콘 버튼 스타일 */
button[title*="달력"], 
button[aria-label*="calendar"],
.stButton button:contains("📅") {
    background-color: #DC2626 !important;
    color: #FFFFFF !important;
    border: 2px solid #DC2626 !important;
    border-radius: 8px !important;
    font-size: 16px !important;
    min-height: 40px !important;
}

/* 🔥 추가 강화: 탭 및 기타 컴포넌트 색상 보장 🔥 */
.stTabs [data-baseweb="tab-list"] button {
    color: #000000 !important;
}

@media (prefers-color-scheme: dark) {
    .stTabs [data-baseweb="tab-list"] button {
        color: #FFFFFF !important;
    }
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

# ===== 전역 자동 저장 트리거 =====
# 1) 상태 변경 감지 → 즉시 저장
try:
    storage.autosave_on_diff()
except Exception:
    pass
# 2) 20초 주기 저장(사용자 토글이 켜져 있을 때만)
try:
    storage.autosave_interval_maybe(seconds=20)
except Exception:
    pass
# 3) 가능하면 주기적 리프레시로 저장 보장
try:
    try:
        from streamlit_autorefresh import st_autorefresh
    except Exception:
        st_autorefresh = None
    if st_autorefresh:
        _tick = st_autorefresh(interval=20000, limit=None, key="_autosave_tick")
        # tick 마다 한 번 더 저장
        storage.autosave_interval_maybe(seconds=1)
except Exception:
    pass