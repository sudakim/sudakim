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
/* 🔥 기본 테마 설정 (JavaScript와 함께 동작) 🔥 */

/* 🌞 라이트모드 (기본) */
:root {
    --bg-color: #FFFFFF;
    --text-color: #000000;
    --surface-color: #F3F4F6;
    --border-color: #D1D5DB;
}

[data-theme="dark"] {
    --bg-color: #1F2937;
    --text-color: #FFFFFF;
    --surface-color: #374151;
    --border-color: #6B7280;
}

/* 🔥 강력한 CSS 적용 - JavaScript 백업용 🔥 */
html, body, .stApp {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
}

/* 메인 콘텐츠 영역 강제 스타일 */
.main, .main .block-container {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
}

/* 모든 텍스트 요소 강제 색상 */
* {
    color: var(--text-color) !important;
}

/* 사이드바 강제 스타일 */
section[data-testid="stSidebar"], 
section[data-testid="stSidebar"] * {
    background-color: var(--surface-color) !important;
    color: var(--text-color) !important;
}

/* 정보박스 강제 스타일 */
.stInfo, .stInfo *, 
.stSuccess, .stSuccess *, 
.stWarning, .stWarning *, 
.stError, .stError * {
    color: var(--text-color) !important;
    background-color: var(--surface-color) !important;
}

/* 버튼 스타일 유지 */
.stButton > button {
    color: #FFFFFF !important;
    background-color: #DC2626 !important;
}

/* 입력 필드 */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    color: var(--text-color) !important;
    background-color: var(--surface-color) !important;
    border: 1px solid var(--border-color) !important;
}

/* 🔥 Media Query 백업 (이중 보장) 🔥 */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-color: #1F2937;
        --text-color: #FFFFFF;
        --surface-color: #374151;
        --border-color: #6B7280;
    }
    
    html, body, .stApp, .main, .main .block-container {
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
    }
    
    * {
        color: #FFFFFF !important;
    }
    
    section[data-testid="stSidebar"], 
    section[data-testid="stSidebar"] * {
        background-color: #374151 !important;
        color: #FFFFFF !important;
    }
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