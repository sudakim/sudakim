import streamlit as st
import pandas as pd

def render_dashboard(contents_df, props_df, timetable_df):
    st.header("📑 콘텐츠 개요")

    # 콘텐츠 개요 테이블
    st.dataframe(
        contents_df,
        use_container_width=True,
        hide_index=True
    )

    # 소품 & 타임테이블 요약
    with st.expander("📌 빠른 스냅샷: 소품 & 타임테이블", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("소품 요약")
            st.dataframe(
                props_df,
                use_container_width=True,
                hide_index=True
            )

        with col2:
            st.subheader("타임테이블 요약")
            st.dataframe(
                timetable_df,
                use_container_width=True,
                hide_index=True
            )
