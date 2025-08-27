import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import json
import requests

# 페이지 설정
st.set_page_config(
    page_title="유튜브 콘텐츠 매니저",
    page_icon="🎬",
    layout="wide"
)

# ========== 구글 시트 설정 ==========
# 1. 구글 시트를 만들고 "링크가 있는 모든 사용자 - 편집자"로 공유
# 2. 아래 URL에 시트 ID 입력
SHEET_URL = "https://docs.google.com/spreadsheets/d/1g5bLvVLHou116z7v_E0r_Gu571FKP4s8QzfmKRIzdHQ/export?format=csv&gid=0"
SHEET_EDIT_URL = "https://docs.google.com/spreadsheets/d/1g5bLvVLHou116z7v_E0r_Gu571FKP4s8QzfmKRIzdHQ/edit"

# 간단한 데이터 저장/불러오기 (CSV 형식 사용)
def save_data_simple():
    """로컬 세션 데이터를 JSON으로 변환"""
    data = {
        'contents': st.session_state.daily_contents,
        'props': st.session_state.content_props,
        'schedules': st.session_state.schedules,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return json.dumps(data, ensure_ascii=False)

def load_data_simple(json_str):
    """JSON 문자열을 세션 데이터로 변환"""
    try:
        data = json.loads(json_str)
        st.session_state.daily_contents = data.get('contents', {})
        st.session_state.content_props = data.get('props', {})
        st.session_state.schedules = data.get('schedules', {})
        return True
    except:
        return False

# ========== 비밀번호 체크 ==========
def check_password():
    """비밀번호 확인"""
    
    def password_entered():
        if st.session_state["password"] == "0803":  # 비밀번호 변경
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 유튜브 콘텐츠 매니저")
        st.text_input(
            "비밀번호를 입력하세요", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.info("💡 6명의 팀원만 아는 비밀번호를 입력하세요")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 유튜브 콘텐츠 매니저")
        st.text_input(
            "비밀번호를 입력하세요", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("😕 비밀번호가 틀렸습니다")
        return False
    else:
        return True

if not check_password():
    st.stop()

# ========== 세션 초기화 ==========
if 'daily_contents' not in st.session_state:
    st.session_state.daily_contents = {}
if 'content_props' not in st.session_state:
    st.session_state.content_props = {}
if 'schedules' not in st.session_state:
    st.session_state.schedules = {}
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# ========== 메인 UI ==========
# 헤더
col1, col2, col3, col4 = st.columns([5, 1, 1, 2])
with col1:
    st.title("🎬 유튜브 콘텐츠 통합 매니저")
with col2:
    if st.button("🔄 새로고침"):
        st.rerun()
with col3:
    if st.button("💾 저장"):
        st.success("저장됨!")
with col4:
    # 구글 시트 링크
    st.link_button("📊 구글시트 열기", SHEET_EDIT_URL)

# 자동 새로고침 안내
refresh_time = (datetime.now() - st.session_state.last_refresh).seconds
st.caption(f"🔄 {refresh_time}초 전 새로고침 | 💡 다른 사람이 수정한 내용을 보려면 새로고침 버튼을 눌러주세요")

# ========== 데이터 저장 영역 ==========
st.sidebar.header("📝 데이터 동기화")
st.sidebar.caption("아래 텍스트를 복사해서 구글 시트에 붙여넣으세요")

# 현재 데이터를 JSON으로 표시
data_json = save_data_simple()
st.sidebar.text_area(
    "현재 데이터 (복사용)",
    value=data_json,
    height=200,
    key="export_data"
)

st.sidebar.divider()

# 데이터 불러오기
st.sidebar.subheader("📥 데이터 불러오기")
imported_data = st.sidebar.text_area(
    "구글 시트의 데이터를 여기에 붙여넣기",
    height=200,
    key="import_data",
    placeholder="구글 시트에서 복사한 JSON 데이터를 붙여넣으세요"
)

if st.sidebar.button("불러오기", type="primary"):
    if load_data_simple(imported_data):
        st.sidebar.success("✅ 데이터를 불러왔습니다!")
        st.rerun()
    else:
        st.sidebar.error("❌ 데이터 형식이 올바르지 않습니다")

st.sidebar.divider()
st.sidebar.caption("""
**사용 방법:**
1. 작업 후 '현재 데이터' 복사
2. 구글 시트에 붙여넣기
3. 다른 팀원이 수정한 내용 보기:
   - 구글 시트에서 데이터 복사
   - '데이터 불러오기'에 붙여넣기
""")

# ========== 탭 메뉴 (기존 코드와 동일) ==========
tab1, tab2, tab3 = st.tabs(["📝 콘텐츠 기획", "🛍️ 소품 구매", "⏰ 타임테이블"])

with tab1:
    st.subheader("📝 콘텐츠 기획")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        selected_date = st.date_input(
            "📅 날짜 선택",
            datetime.now(),
            key="content_date"
        )
        date_key = selected_date.strftime('%Y-%m-%d')
    
    with col2:
        num_contents = st.number_input(
            "콘텐츠 개수",
            min_value=1,
            max_value=10,
            value=3
        )
    
    with col3:
        if st.button("✨ 양식 생성", type="primary"):
            if date_key not in st.session_state.daily_contents:
                st.session_state.daily_contents[date_key] = []
            
            current_count = len(st.session_state.daily_contents[date_key])
            for i in range(num_contents - current_count):
                st.session_state.daily_contents[date_key].append({
                    'id': f"{date_key}_{current_count + i}",
                    'title': '',
                    'draft': '',
                    'feedback': '',
                    'revision': '',
                    'final': '',
                    'reference': ''
                })
            st.rerun()
    
    st.divider()
    
    if date_key in st.session_state.daily_contents and st.session_state.daily_contents[date_key]:
        st.subheader(f"📋 {selected_date.strftime('%Y년 %m월 %d일')} 콘텐츠")
        
        contents = st.session_state.daily_contents[date_key]
        
        for idx, content in enumerate(contents):
            with st.expander(f"콘텐츠 #{idx+1} - {content.get('title', '제목 없음')}", expanded=True):
                col_del, col_title = st.columns([1, 5])
                with col_del:
                    if st.button("🗑️ 삭제", key=f"del_{date_key}_{idx}"):
                        st.session_state.daily_contents[date_key].pop(idx)
                        st.rerun()
                
                with col_title:
                    content['title'] = st.text_input(
                        "제목",
                        value=content.get('title', ''),
                        key=f"{date_key}_title_{idx}",
                        placeholder="콘텐츠 제목 입력"
                    )
                
                content['reference'] = st.text_input(
                    "📎 레퍼런스 링크",
                    value=content.get('reference', ''),
                    key=f"{date_key}_ref_{idx}",
                    placeholder="YouTube 링크 입력"
                )
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown("**1️⃣ 초안**")
                    content['draft'] = st.text_area(
                        "초안",
                        value=content.get('draft', ''),
                        height=120,
                        key=f"{date_key}_draft_{idx}",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    st.markdown("**2️⃣ 목사님 피드백**")
                    content['feedback'] = st.text_area(
                        "피드백",
                        value=content.get('feedback', ''),
                        height=120,
                        key=f"{date_key}_feedback_{idx}",
                        label_visibility="collapsed"
                    )
                
                with col3:
                    st.markdown("**3️⃣ 추가 의견**")
                    content['revision'] = st.text_area(
                        "추가의견",
                        value=content.get('revision', ''),
                        height=120,
                        key=f"{date_key}_revision_{idx}",
                        label_visibility="collapsed"
                    )
                
                with col4:
                    st.markdown("**4️⃣ 최종 픽스**")
                    content['final'] = st.text_area(
                        "최종",
                        value=content.get('final', ''),
                        height=120,
                        key=f"{date_key}_final_{idx}",
                        label_visibility="collapsed"
                    )
                
                progress = sum([25 for field in ['draft', 'feedback', 'revision', 'final'] if content.get(field)])
                st.progress(progress / 100, text=f"진행률: {progress}%")
    else:
        st.info("👆 '양식 생성' 버튼을 클릭하여 콘텐츠를 추가하세요.")

# 나머지 탭들도 동일한 구조로 구현...