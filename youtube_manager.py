# youtube_manager.py (상단)
import streamlit as st
from modules import storage
from modules import dashboard, planning, props, timetable, uploads
import requests, json
from modules.github_store import _get, _auth_headers

with st.sidebar.expander("🆘 강제 가져오기"):
    if st.button("youtube_data.json RAW 강제로드"):
        try:
            gid = _get("gist_id")
            hdr = _auth_headers()
            # Gist 메타
            meta = requests.get(f"https://api.github.com/gists/{gid}", headers=hdr, timeout=20).json()
            # youtube_data.json의 raw_url 찾기
            files = meta.get("files", {})
            target = None
            for k,v in files.items():
                if k.lower() == "youtube_data.json":
                    target = v
                    break
            if not target:
                st.error("youtube_data.json 파일을 찾을 수 없습니다.")
            else:
                raw = requests.get(target["raw_url"], timeout=20).text
                data = json.loads(raw)
                # 레거시 키 -> 세션 주입
                st.session_state["daily_contents"] = data.get("contents", {})
                st.session_state["content_props"]  = data.get("props", {})
                st.session_state["schedules"]      = data.get("schedules", {})
                st.session_state["upload_status"]  = data.get("upload_status", {})
                st.success("세션 주입 완료")
                storage.autosave_maybe()
                st.rerun()
        except Exception as e:
            st.error(f"실패: {e}")


st.set_page_config(page_title="유튜브 콘텐츠 매니저", page_icon="🎬", layout="wide")

# ★ 앱 시작 시: GitHub/Gist/Local에서 자동 로드
storage.load_state()

with st.sidebar:
    st.markdown("### 💾 저장")
    st.toggle("자동 저장", key="_autosave", value=st.session_state.get("_autosave", True))
    if st.button("수동 저장"):
        storage.save_state()
        st.success("저장 완료")
    src = st.session_state.get("_storage_source") or "unknown"
    when = st.session_state.get("_last_saved") or "-"
    st.caption(f"source: {src} / last saved: {when}")

# ... 탭 구성은 기존 그대로 ...
st.set_page_config(page_title="유튜브 콘텐츠 매니저", page_icon="🎬", layout="wide")

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


