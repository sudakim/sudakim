import streamlit as st
from modules import dashboard, planning, props, timetable, uploads

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
