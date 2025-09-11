# youtube_manager.py (상단)
import streamlit as st
from modules import storage
from modules import dashboard, planning, props, timetable, uploads

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
