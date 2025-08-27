import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import json
from google.cloud import firestore
import webbrowser

# ==============================================================================
# 1. Firebase 인증 및 연결
# ==============================================================================
def connect_firestore():
    """Streamlit Secrets를 사용하여 Firestore에 연결합니다."""
    # st.secrets에서 JSON 키 정보를 가져옵니다.
    key_dict = json.loads(st.secrets["textkey"])
    # Firestore 클라이언트를 초기화하고 반환합니다.
    creds = firestore.Client.from_service_account_info(key_dict)
    return creds

# Firestore 클라이언트 초기화
try:
    db = connect_firestore()
except Exception as e:
    # 로컬에서 실행 시 secrets가 없으면 이 메시지가 뜰 수 있습니다.
    # 배포 시에는 secrets를 설정해야 합니다.
    st.error("Firestore 연결에 실패했습니다. Streamlit Secrets 설정이 올바른지 확인하세요.")
    st.stop()


# ==============================================================================
# 2. 비밀번호 인증 기능
# ==============================================================================
def check_password():
    """비밀번호가 맞으면 True를, 틀리면 False를 반환합니다."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    correct_password = st.secrets.get("PASSWORD", "1234") # 로컬 테스트용 기본 비밀번호

    if st.session_state.password_correct:
        return True

    with st.form("login"):
        st.title("🎬 유튜브 콘텐츠 통합 매니저 (Firebase Ver.)")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인")
        if submitted:
            if password == correct_password:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
    return False

if not check_password():
    st.stop()

# ==============================================================================
# 3. 데이터 로드 및 저장 함수 (Firestore 연동)
# ==============================================================================
def load_data():
    """Firestore에서 데이터를 불러와 session_state를 채웁니다."""
    with st.spinner("데이터를 불러오는 중..."):
        # 콘텐츠 데이터 로드
        contents_ref = db.collection("contents").stream()
        daily_contents = {}
        for doc in contents_ref:
            content = doc.to_dict()
            date_key = content.pop('date', None)
            if date_key:
                if date_key not in daily_contents:
                    daily_contents[date_key] = []
                # Firestore는 순서를 보장하지 않으므로 ID로 정렬
                daily_contents[date_key].append(content)
        # 날짜별로 콘텐츠를 ID 순서로 정렬
        for date_key in daily_contents:
            daily_contents[date_key] = sorted(daily_contents[date_key], key=lambda x: x['id'])
        st.session_state.daily_contents = daily_contents

        # 소품 데이터 로드
        props_ref = db.collection("props").stream()
        content_props = {}
        for doc in props_ref:
            prop = doc.to_dict()
            content_id = prop.pop('content_id', None)
            if content_id:
                if content_id not in content_props:
                    content_props[content_id] = []
                content_props[content_id].append(prop)
        st.session_state.content_props = content_props
        
        # 스케줄 데이터 로드 (필요 시)
        # schedules_ref = db.collection("schedules").stream() ...

def save_data():
    """session_state의 데이터를 Firestore에 저장합니다."""
    with st.spinner("데이터를 저장하는 중..."):
        # 기존 데이터 삭제 (단순화를 위해 전체 덮어쓰기)
        for doc in db.collection("contents").stream():
            doc.reference.delete()
        for doc in db.collection("props").stream():
            doc.reference.delete()

        # 새 데이터 저장
        for date_key, contents in st.session_state.daily_contents.items():
            for content in contents:
                # Firestore에 저장할 데이터에서 None 값을 제거
                clean_content = {k: v for k, v in content.items() if v is not None}
                doc_ref = db.collection("contents").document(clean_content['id'])
                doc_ref.set({'date': date_key, **clean_content})

        for content_id, props in st.session_state.content_props.items():
            for i, prop in enumerate(props):
                prop_id = f"{content_id}_prop_{i}"
                clean_prop = {k: v for k, v in prop.items() if v is not None}
                doc_ref = db.collection("props").document(prop_id)
                doc_ref.set({'content_id': content_id, **clean_prop})
    st.sidebar.success("✅ 데이터가 실시간으로 저장되었습니다!")


# ==============================================================================
# 4. 페이지 기본 설정 및 초기화
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

# 앱 시작 시 데이터 로드
if 'data_loaded' not in st.session_state:
    load_data()
    st.session_state.data_loaded = True

# 세션 상태 초기화 (필요한 경우)
if 'schedules' not in st.session_state:
    st.session_state.schedules = {}

# ==============================================================================
# 5. 사이드바 UI
# ==============================================================================

with st.sidebar:
    st.header("💾 데이터 관리")
    if st.button("🔄 저장 및 동기화", type="primary"):
        save_data()
        load_data() # 저장 후 바로 다시 로드하여 최신 상태 유지
        st.rerun()
    st.info("변경 사항은 '저장 및 동기화' 버튼을 눌러야 중앙 서버에 반영됩니다.")

    st.divider()
    st.subheader("📊 요약")
    total_contents = sum(len(c) for c in st.session_state.daily_contents.values())
    total_props = sum(len(p) for p in st.session_state.content_props.values())
    st.metric("총 콘텐츠", f"{total_contents}개")
    st.metric("총 소품", f"{total_props}개")

# ==============================================================================
# 6. 메인 화면 UI
# ==============================================================================

# 헤더
st.title("🎬 유튜브 콘텐츠 통합 매니저")

# 탭 메뉴
tab1, tab2, tab3 = st.tabs(["📝 콘텐츠 기획", "🛍️ 소품 구매", "⏰ 타임테이블"])

with tab1:
    st.subheader("📝 콘텐츠 기획")
    
    # 날짜 선택
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
            
            # 기존 콘텐츠 개수만큼 추가
            current_count = len(st.session_state.daily_contents.get(date_key, []))
            for i in range(num_contents):
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
    
    # 콘텐츠 표시
    if date_key in st.session_state.daily_contents and st.session_state.daily_contents[date_key]:
        st.subheader(f"📋 {selected_date.strftime('%Y년 %m월 %d일')} 콘텐츠")
        
        contents = st.session_state.daily_contents[date_key]
        
        for idx, content in enumerate(contents):
            with st.expander(f"콘텐츠 #{idx+1} - {content.get('title', '제목 없음')}", expanded=True):
                # 삭제 버튼
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
                if content.get('reference'):
                    st.video(content['reference'])

                # 4단계 프로세스
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown("**1️⃣ 초안**")
                    content['draft'] = st.text_area("초안", value=content.get('draft', ''), height=120, key=f"{date_key}_draft_{idx}", label_visibility="collapsed")
                with col2:
                    st.markdown("**2️⃣ 목사님 피드백**")
                    content['feedback'] = st.text_area("피드백", value=content.get('feedback', ''), height=120, key=f"{date_key}_feedback_{idx}", label_visibility="collapsed")
                with col3:
                    st.markdown("**3️⃣ 추가 의견**")
                    content['revision'] = st.text_area("추가의견", value=content.get('revision', ''), height=120, key=f"{date_key}_revision_{idx}", label_visibility="collapsed")
                with col4:
                    st.markdown("**4️⃣ 최종 픽스**")
                    content['final'] = st.text_area("최종", value=content.get('final', ''), height=120, key=f"{date_key}_final_{idx}", label_visibility="collapsed")
                
                # 진행률
                progress = sum(1 for field in ['draft', 'feedback', 'revision', 'final'] if content.get(field)) * 25
                st.progress(progress / 100, text=f"진행률: {progress}%")
    else:
        st.info("👆 '양식 생성' 버튼을 클릭하여 콘텐츠를 추가하세요.")

with tab2:
    st.subheader("🛍️ 소품 구매 관리")
    
    prop_date = st.date_input("📅 날짜 선택", datetime.now(), key="prop_date")
    prop_date_key = prop_date.strftime('%Y-%m-%d')
    
    if prop_date_key in st.session_state.daily_contents and st.session_state.daily_contents[prop_date_key]:
        contents = st.session_state.daily_contents[prop_date_key]
        st.markdown(f"### 📋 {prop_date.strftime('%Y년 %m월 %d일')} 콘텐츠별 소품")
        
        for idx, content in enumerate(contents):
            content_id = content.get('id', f"{prop_date_key}_{idx}")
            if content_id not in st.session_state.content_props:
                st.session_state.content_props[content_id] = []
            
            props = st.session_state.content_props[content_id]
            content_total = sum(p.get('price', 0) for p in props if isinstance(p.get('price'), (int, float)))

            with st.expander(f"📦 #{idx+1}. {content.get('title', '제목 없음')} ({len(props)}개 소품 / {content_total:,}원)", expanded=False):
                st.markdown("**➕ 새 소품 추가**")
                c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
                with c1: new_name = st.text_input("소품명", key=f"new_name_{content_id}", placeholder="소품명")
                with c2: new_vendor = st.selectbox("구매처", ["쿠팡", "네이버", "다이소", "오프라인", "기타"], key=f"new_vendor_{content_id}")
                with c3: new_price = st.number_input("금액", min_value=0, step=1000, key=f"new_price_{content_id}")
                with c4: new_status = st.selectbox("상태", ["예정", "주문완료", "배송중", "수령완료"], key=f"new_status_{content_id}")
                with c5:
                    st.write(" ")
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
                        vendor_options = ["쿠팡", "네이버", "다이소", "오프라인", "기타"]
                        status_options = ["예정", "주문완료", "배송중", "수령완료"]
                        
                        with c1: prop['name'] = st.text_input("이름", prop.get('name', ''), key=f"{key_base}_name", label_visibility="collapsed")
                        with c2: prop['vendor'] = st.selectbox("구매처", vendor_options, index=vendor_options.index(prop['vendor']) if prop.get('vendor') in vendor_options else 0, key=f"{key_base}_vendor", label_visibility="collapsed")
                        with c3: prop['price'] = st.number_input("금액", value=prop.get('price', 0), key=f"{key_base}_price", label_visibility="collapsed")
                        with c4: prop['status'] = st.selectbox("상태", status_options, index=status_options.index(prop['status']) if prop.get('status') in status_options else 0, key=f"{key_base}_status", label_visibility="collapsed")
                        with c5:
                           if st.button("🗑️", key=f"del_prop_{key_base}", help="삭제"):
                                props.pop(p_idx)
                                st.rerun()
    else:
        st.warning(f"⚠️ {prop_date.strftime('%Y년 %m월 %d일')}에 생성된 콘텐츠가 없습니다. [콘텐츠 기획] 탭에서 먼저 콘텐츠를 생성하세요.")

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
