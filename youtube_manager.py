import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
from st_gsheets_connection import GSheetsConnection

# ==============================================================================
# 1. 비밀번호 인증 기능
# ==============================================================================
def check_password():
    """비밀번호가 맞으면 True를, 틀리면 False를 반환합니다."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    # Streamlit Secrets에 설정된 비밀번호를 가져옵니다.
    # 로컬 테스트를 위해 기본값 "1234"를 설정할 수 있습니다.
    correct_password = st.secrets.get("PASSWORD", "1234")

    if st.session_state.password_correct:
        return True

    # 로그인 폼
    with st.form("login"):
        st.title("🎬 유튜브 콘텐츠 통합 매니저")
        st.write("비밀번호를 입력하세요.")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인")

        if submitted:
            if password == correct_password:
                st.session_state.password_correct = True
                st.rerun()  # 비밀번호가 맞으면 앱을 다시 실행
            else:
                st.error("비밀번호가 틀렸습니다.")
    return False

# 비밀번호 확인 로직 실행
if not check_password():
    st.stop()  # 비밀번호가 틀리면 앱 실행 중지

# ==============================================================================
# 2. 페이지 기본 설정 및 Google Sheets 연결
# ==============================================================================

# 페이지 설정
st.set_page_config(
    page_title="유튜브 콘텐츠 매니저",
    page_icon="🎬",
    layout="wide"
)

# 스타일 설정
st.markdown("""
    <style>
    .stTextArea textarea {
        font-size: 12px;
    }
    div[data-testid="column"] {
        padding: 0px 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Google Sheets 연결
# Streamlit Secrets에 저장된 URL과 인증 정보를 사용합니다.
SPREADSHEET_URL = st.secrets.get("SPREADSHEET_URL", "YOUR_GOOGLE_SHEET_URL")
conn = st.connection("gsheets", type=GSheetsConnection)

# ==============================================================================
# 3. 데이터 로드 및 저장 함수 (Google Sheets 연동)
# ==============================================================================

def load_data():
    """Google Sheets에서 데이터를 읽어와 세션 상태(session_state)에 저장합니다."""
    try:
        # 콘텐츠 데이터 로드
        contents_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="contents", ttl=5)
        contents_df = contents_df.dropna(how="all").astype(str) # 빈 행 제거 및 문자열로 타입 통일
        
        daily_contents = {}
        for _, row in contents_df.iterrows():
            date_key = row['date']
            if date_key not in daily_contents:
                daily_contents[date_key] = []
            daily_contents[date_key].append(row.to_dict())
        st.session_state.daily_contents = daily_contents

        # 소품 데이터 로드
        props_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="props", ttl=5)
        props_df = props_df.dropna(how="all").astype(str) # 빈 행 제거 및 문자열로 타입 통일
        
        # 가격(price) 컬럼은 숫자로 변환
        if 'price' in props_df.columns:
            props_df['price'] = pd.to_numeric(props_df['price'], errors='coerce').fillna(0).astype(int)

        content_props = {}
        for _, row in props_df.iterrows():
            content_id = row['content_id']
            if content_id not in content_props:
                content_props[content_id] = []
            content_props[content_id].append(row.to_dict())
        st.session_state.content_props = content_props

    except Exception as e:
        # 시트가 비어있거나 처음 만들었을 때 오류가 날 수 있으므로 초기화
        if 'worksheet not found' in str(e).lower():
            st.warning("'contents' 또는 'props' 시트를 찾을 수 없습니다. 빈 데이터로 시작합니다.")
        else:
            st.error(f"데이터 로딩 중 오류 발생: {e}")
        st.session_state.daily_contents = {}
        st.session_state.content_props = {}

def save_data():
    """세션 상태(session_state)의 데이터를 Google Sheets에 저장(덮어쓰기)합니다."""
    with st.spinner("Google Sheets에 저장 중..."):
        try:
            # 콘텐츠 데이터를 DataFrame으로 변환
            contents_list = []
            for date_key, contents in st.session_state.daily_contents.items():
                for content in contents:
                    content_with_date = {'date': date_key, **content}
                    contents_list.append(content_with_date)
            
            if contents_list:
                contents_df = pd.DataFrame(contents_list)
                cols = ['date', 'id', 'title', 'reference', 'draft', 'feedback', 'revision', 'final']
                contents_df = contents_df.reindex(columns=[c for c in cols if c in contents_df.columns])
                conn.update(spreadsheet=SPREADSHEET_URL, worksheet="contents", data=contents_df)
            else: 
                 conn.clear(spreadsheet=SPREADSHEET_URL, worksheet="contents")

            # 소품 데이터를 DataFrame으로 변환
            props_list = []
            for content_id, props in st.session_state.content_props.items():
                for prop in props:
                    prop_with_id = {'content_id': content_id, **prop}
                    props_list.append(prop_with_id)
            
            if props_list:
                props_df = pd.DataFrame(props_list)
                cols = ['content_id', 'name', 'vendor', 'price', 'status']
                props_df = props_df.reindex(columns=[c for c in cols if c in props_df.columns])
                conn.update(spreadsheet=SPREADSHEET_URL, worksheet="props", data=props_df)
            else:
                conn.clear(spreadsheet=SPREADSHEET_URL, worksheet="props")
            
            st.sidebar.success("✅ Google Sheets에 저장 완료!")
        except Exception as e:
            st.sidebar.error(f"저장 중 오류 발생: {e}")

# ==============================================================================
# 4. 앱 시작 시 데이터 로드 및 세션 초기화
# ==============================================================================

# 'data_loaded' 플래그를 사용하여 앱 새로고침 시 데이터가 초기화되는 것을 방지
if 'data_loaded' not in st.session_state:
    load_data()
    st.session_state.data_loaded = True

# 다른 세션 상태 초기화
if 'schedules' not in st.session_state:
    st.session_state.schedules = {}

# ==============================================================================
# 5. 사이드바 UI
# ==============================================================================
with st.sidebar:
    st.header("💾 데이터 관리")
    if st.button("🔄 Google Sheets에 저장", type="primary", help="현재 내용을 구글 시트에 저장합니다."):
        save_data()
    if st.button("🔃 새로고침", help="구글 시트에서 최신 데이터를 다시 불러옵니다."):
        load_data()
        st.rerun()

    st.divider()
    st.subheader("📊 요약")
    total_contents = sum(len(c) for c in st.session_state.daily_contents.values())
    total_props = sum(len(p) for p in st.session_state.content_props.values())
    st.metric("총 콘텐츠", f"{total_contents}개")
    st.metric("총 소품", f"{total_props}개")

# ==============================================================================
# 6. 메인 화면 UI (탭)
# ==============================================================================
st.title("🎬 유튜브 콘텐츠 통합 매니저 (Google Sheets 연동)")
tab1, tab2, tab3 = st.tabs(["📝 콘텐츠 기획", "🛍️ 소품 구매", "⏰ 타임테이블"])

# ------------------------------------------------------------------------------
# 탭 1: 콘텐츠 기획
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("📝 콘텐츠 기획")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        selected_date = st.date_input("📅 날짜 선택", datetime.now(), key="content_date")
        date_key = selected_date.strftime('%Y-%m-%d')
    with col2:
        num_contents = st.number_input("콘텐츠 개수", min_value=1, max_value=10, value=3)
    with col3:
        if st.button("✨ 양식 생성", type="primary"):
            if date_key not in st.session_state.daily_contents:
                st.session_state.daily_contents[date_key] = []
            
            current_count = len(st.session_state.daily_contents[date_key])
            for i in range(num_contents):
                st.session_state.daily_contents[date_key].append({
                    'id': f"{date_key}_{current_count + i}", 'title': '', 'draft': '',
                    'feedback': '', 'revision': '', 'final': '', 'reference': ''
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
                    content['title'] = st.text_input("제목", value=content.get('title', ''), key=f"{date_key}_title_{idx}", placeholder="콘텐츠 제목 입력")
                
                content['reference'] = st.text_input("📎 레퍼런스 링크", value=content.get('reference', ''), key=f"{date_key}_ref_{idx}", placeholder="YouTube 링크 입력")
                if content.get('reference'):
                    st.video(content['reference'])

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown("**1️⃣ 초안**")
                    content['draft'] = st.text_area("초안", value=content.get('draft', ''), height=120, key=f"{date_key}_draft_{idx}", label_visibility="collapsed")
                with col2:
                    st.markdown("**2️⃣ 피드백**")
                    content['feedback'] = st.text_area("피드백", value=content.get('feedback', ''), height=120, key=f"{date_key}_feedback_{idx}", label_visibility="collapsed")
                with col3:
                    st.markdown("**3️⃣ 추가 의견**")
                    content['revision'] = st.text_area("추가의견", value=content.get('revision', ''), height=120, key=f"{date_key}_revision_{idx}", label_visibility="collapsed")
                with col4:
                    st.markdown("**4️⃣ 최종 픽스**")
                    content['final'] = st.text_area("최종", value=content.get('final', ''), height=120, key=f"{date_key}_final_{idx}", label_visibility="collapsed")
                
                progress = sum(1 for field in ['draft', 'feedback', 'revision', 'final'] if content.get(field)) * 25
                st.progress(progress / 100, text=f"진행률: {progress}%")
    else:
        st.info("👆 '양식 생성' 버튼을 클릭하여 콘텐츠를 추가하세요.")

# ------------------------------------------------------------------------------
# 탭 2: 소품 구매
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("🛍️ 소품 구매 관리")
    
    prop_date = st.date_input("📅 날짜 선택", datetime.now(), key="prop_date")
    prop_date_key = prop_date.strftime('%Y-%m-%d')
    
    if prop_date_key in st.session_state.daily_contents and st.session_state.daily_contents[prop_date_key]:
        contents = st.session_state.daily_contents[prop_date_key]
        st.markdown(f"### 📋 {prop_date.strftime('%Y년 %m월 %d일')} 콘텐츠별 소품")
        
        total_all_props = 0
        
        for idx, content in enumerate(contents):
            content_id = content.get('id', f"{prop_date_key}_{idx}")
            if content_id not in st.session_state.content_props:
                st.session_state.content_props[content_id] = []
            
            props = st.session_state.content_props[content_id]
            content_total = sum(p.get('price', 0) for p in props)
            total_all_props += content_total

            with st.expander(f"📦 #{idx+1}. {content.get('title', '제목 없음')} ({len(props)}개 소품 / {content_total:,}원)", expanded=False):
                st.markdown("**➕ 새 소품 추가**")
                c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
                with c1: new_name = st.text_input("소품명", key=f"new_name_{content_id}", placeholder="소품명")
                with c2: new_vendor = st.selectbox("구매처", ["쿠팡", "네이버", "다이소", "오프라인", "기타"], key=f"new_vendor_{content_id}")
                with c3: new_price = st.number_input("금액", min_value=0, step=1000, key=f"new_price_{content_id}")
                with c4: new_status = st.selectbox("상태", ["예정", "주문완료", "배송중", "수령완료"], key=f"new_status_{content_id}")
                with c5:
                    st.write(" ") # 버튼 정렬용
                    if st.button("추가", key=f"add_{content_id}", type="primary"):
                        if new_name:
                            props.append({'name': new_name, 'vendor': new_vendor, 'price': new_price, 'status': new_status})
                            st.rerun()
                
                st.divider()
                
                if props:
                    st.markdown("**📦 소품 목록**")
                    for p_idx, prop in enumerate(props):
                        key_base = f"prop_{content_id}_{p_idx}"
                        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
                        with c1: prop['name'] = st.text_input("이름", prop['name'], key=f"{key_base}_name", label_visibility="collapsed")
                        with c2: prop['vendor'] = st.selectbox("구매처", ["쿠팡", "네이버", "다이소", "오프라인", "기타"], index=["쿠팡", "네이버", "다이소", "오프라인", "기타"].index(prop['vendor']), key=f"{key_base}_vendor", label_visibility="collapsed")
                        with c3: prop['price'] = st.number_input("금액", prop.get('price',0), key=f"{key_base}_price", label_visibility="collapsed")
                        with c4: prop['status'] = st.selectbox("상태", ["예정", "주문완료", "배송중", "수령완료"], index=["예정", "주문완료", "배송중", "수령완료"].index(prop['status']), key=f"{key_base}_status", label_visibility="collapsed")
                        with c5:
                           if st.button("🗑️", key=f"del_prop_{key_base}"):
                                props.pop(p_idx)
                                st.rerun()
    else:
        st.warning(f"⚠️ {prop_date.strftime('%Y년 %m월 %d일')}에 생성된 콘텐츠가 없습니다. [콘텐츠 기획] 탭에서 먼저 콘텐츠를 생성하세요.")

# ------------------------------------------------------------------------------
# 탭 3: 타임테이블
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("⏰ 타임테이블")
    
    schedule_date = st.date_input("📅 날짜 선택", datetime.now(), key="schedule_date")
    schedule_date_key = schedule_date.strftime('%Y-%m-%d')
    
    if schedule_date_key in st.session_state.daily_contents and st.session_state.daily_contents[schedule_date_key]:
        contents = [c for c in st.session_state.daily_contents[schedule_date_key] if c.get('title')]
        
        st.markdown(f"### 📅 {schedule_date.strftime('%Y년 %m월 %d일')} 촬영 일정")
        default_start = st.time_input("🕐 촬영 시작 시간", time(12, 40))
        current_time = datetime.combine(schedule_date, default_start)
        
        for idx, content in enumerate(contents):
            with st.expander(f"📺 {content['title']}", expanded=True):
                col1, col2, col3 = st.columns([2, 2, 4])
                with col1:
                    duration_options = ["50분", "1시간", "1시간 30분", "2시간"]
                    duration = st.selectbox("촬영 시간", duration_options, key=f"duration_{schedule_date_key}_{idx}")
                    duration_map = {"50분": 50, "1시간": 60, "1시간 30분": 90, "2시간": 120}
                    duration_mins = duration_map[duration]
                    end_time = current_time + timedelta(minutes=duration_mins)
                    st.write(f"**{current_time.strftime('%H:%M')} ~ {end_time.strftime('%H:%M')}**")
                    current_time = end_time + timedelta(minutes=10)
                with col2:
                    st.text_area("최종 내용", value=content.get('final', '최종 픽스 미완료'), height=100, disabled=True, key=f"final_view_{schedule_date_key}_{idx}")
                with col3:
                    content_id = content.get('id', f"{schedule_date_key}_{idx}")
                    props = st.session_state.content_props.get(content_id, [])
                    completed_props = [p['name'] for p in props if p.get('status') == '수령완료']
                    if completed_props:
                        st.success(f"✅ 준비 완료 소품: {', '.join(completed_props)}")
                    else:
                        st.warning("⚠️ 수령 완료된 소품 없음")
        
        st.divider()
        st.info(f"📌 **예상 종료 시간 (정리 포함)**: {(current_time + timedelta(minutes=50)).strftime('%H:%M')}")
    else:
        st.warning(f"⚠️ {schedule_date.strftime('%Y년 %m월 %d일')}에 생성된 콘텐츠가 없습니다.")