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

# ========== GitHub Gist 설정 (자동 동기화) ==========
# Streamlit Secrets 사용 (배포시)
try:
    GITHUB_TOKEN = st.secrets["github_token"]
    GIST_ID = st.secrets["gist_id"]
except:
    # 로컬 테스트용 (실제 값으로 변경 필요)
    GITHUB_TOKEN = "ghp_YOUR_GITHUB_TOKEN_HERE"  # GitHub 토큰
    GIST_ID = "YOUR_GIST_ID_HERE"  # Gist ID

# GitHub Gist 함수들
def save_to_gist(data):
    """GitHub Gist에 자동 저장"""
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        payload = {
            "files": {
                "youtube_data.json": {
                    "content": json.dumps(data, ensure_ascii=False, indent=2)
                }
            }
        }
        
        response = requests.patch(url, json=payload, headers=headers)
        return response.status_code == 200
    except:
        return False

def load_from_gist():
    """GitHub Gist에서 자동 불러오기"""
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()["files"]["youtube_data.json"]["content"]
            return json.loads(content)
        return None
    except:
        return None

# ========== 비밀번호 체크 ==========
def check_password():
    """비밀번호 확인"""
    
    # Secrets에서 비밀번호 가져오기
    try:
        PASSWORD = st.secrets["app_password"]
    except:
        PASSWORD = "youtube1234"  # 로컬 테스트용 기본값
    
    def password_entered():
        if st.session_state["password"] == PASSWORD:
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

# ========== 세션 초기화 (자동으로 Gist에서 불러오기) ==========
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

if not st.session_state.initialized:
    # Gist에서 데이터 불러오기
    data = load_from_gist()
    if data:
        st.session_state.daily_contents = data.get('contents', {})
        st.session_state.content_props = data.get('props', {})
        st.session_state.schedules = data.get('schedules', {})
        st.toast("☁️ 클라우드에서 데이터를 불러왔습니다", icon='✅')
    else:
        st.session_state.daily_contents = {}
        st.session_state.content_props = {}
        st.session_state.schedules = {}
    st.session_state.initialized = True

# 자동 저장 함수
def auto_save():
    """변경사항을 GitHub Gist에 자동 저장"""
    data = {
        'contents': st.session_state.daily_contents,
        'props': st.session_state.content_props,
        'schedules': st.session_state.schedules,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'updated_by': st.session_state.get('user_name', 'Unknown')
    }
    
    if save_to_gist(data):
        st.session_state.last_save = datetime.now().strftime('%H:%M:%S')
        return True
    return False

# 데이터 새로고침
def refresh_data():
    """최신 데이터 불러오기"""
    data = load_from_gist()
    if data:
        st.session_state.daily_contents = data.get('contents', {})
        st.session_state.content_props = data.get('props', {})
        st.session_state.schedules = data.get('schedules', {})
        st.session_state.initialized = True
        st.toast("🔄 최신 데이터를 불러왔습니다", icon='✅')
        st.rerun()

# ========== 메인 UI ==========
# 헤더
col1, col2, col3, col4 = st.columns([5, 1, 1, 1])
with col1:
    st.title("🎬 유튜브 콘텐츠 통합 매니저")
with col2:
    if st.button("🔄 새로고침"):
        refresh_data()
with col3:
    if st.button("💾 저장"):
        if auto_save():
            st.toast("☁️ 클라우드에 저장되었습니다", icon='✅')
        else:
            st.error("저장 실패")
with col4:
    # 사용자 이름 (선택사항)
    name = st.text_input("이름", key="user_name", placeholder="홍길동", label_visibility="collapsed")

# 상태 표시
status_col1, status_col2 = st.columns([3, 1])
with status_col1:
    if 'last_save' in st.session_state:
        st.caption(f"☁️ 자동 저장 ON | 마지막 저장: {st.session_state.last_save}")
    else:
        st.caption("☁️ 자동 저장 ON | GitHub Gist 동기화 중")
with status_col2:
    st.caption("💡 모든 변경사항이 자동 저장됩니다")

# ========== 탭 메뉴 ==========
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
            auto_save()  # 자동 저장
            st.rerun()
    
    st.divider()
    
    if date_key in st.session_state.daily_contents and st.session_state.daily_contents[date_key]:
        st.subheader(f"📋 {selected_date.strftime('%Y년 %m월 %d일')} 콘텐츠")
        
        contents = st.session_state.daily_contents[date_key]
        
        for idx, content in enumerate(contents):
            with st.expander(f"콘텐츠 #{idx+1} - {content.get('title', '제목 없음')}", expanded=True):
                
                # 변경 감지를 위한 이전 값 저장
                old_values = content.copy()
                
                col_del, col_title = st.columns([1, 5])
                with col_del:
                    if st.button("🗑️ 삭제", key=f"del_{date_key}_{idx}"):
                        st.session_state.daily_contents[date_key].pop(idx)
                        auto_save()
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
                
                # 값이 변경되면 자동 저장
                if old_values != content:
                    auto_save()
                
                progress = sum([25 for field in ['draft', 'feedback', 'revision', 'final'] if content.get(field)])
                st.progress(progress / 100, text=f"진행률: {progress}%")
    else:
        st.info("👆 '양식 생성' 버튼을 클릭하여 콘텐츠를 추가하세요.")

with tab2:
    st.subheader("🛍️ 소품 구매 관리")
    
    # 날짜 선택
    prop_date = st.date_input("📅 날짜 선택", datetime.now(), key="prop_date")
    prop_date_key = prop_date.strftime('%Y-%m-%d')
    
    # 해당 날짜의 콘텐츠 가져오기
    if prop_date_key in st.session_state.daily_contents and st.session_state.daily_contents[prop_date_key]:
        contents = st.session_state.daily_contents[prop_date_key]
        
        st.markdown(f"### 📋 {prop_date.strftime('%Y년 %m월 %d일')} 콘텐츠별 소품")
        
        # 전체 통계
        total_all_props = 0
        total_all_completed = 0
        
        # 모든 콘텐츠를 토글로 표시
        for idx, content in enumerate(contents):
            content_id = content.get('id', f"{prop_date_key}_{idx}")
            
            # 소품 초기화
            if content_id not in st.session_state.content_props:
                st.session_state.content_props[content_id] = []
            
            props = st.session_state.content_props[content_id]
            
            # 콘텐츠별 통계
            content_total = sum(p['price'] for p in props)
            content_completed = len([p for p in props if p['status'] == '수령완료'])
            
            total_all_props += content_total
            total_all_completed += content_completed
            
            # 토글 expander로 각 콘텐츠 표시
            with st.expander(
                f"📦 #{idx+1}. {content.get('title', '제목 없음')} "
                f"({len(props)}개 소품 / {content_total:,}원)",
                expanded=False
            ):
                # 소품 추가 섹션
                st.markdown("**➕ 새 소품 추가**")
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
                
                with col1:
                    new_prop_name = st.text_input("소품명", key=f"new_name_{content_id}", placeholder="소품명")
                with col2:
                    new_vendor = st.selectbox("구매처", ["쿠팡", "네이버", "다이소", "오프라인", "기타"], 
                                             key=f"new_vendor_{content_id}")
                with col3:
                    new_price = st.number_input("금액", min_value=0, step=1000, 
                                               key=f"new_price_{content_id}")
                with col4:
                    new_status = st.selectbox("상태", ["예정", "주문완료", "배송중", "수령완료"],
                                             key=f"new_status_{content_id}")
                with col5:
                    if st.button("추가", key=f"add_{content_id}", type="primary"):
                        if new_prop_name:
                            props.append({
                                'name': new_prop_name,
                                'vendor': new_vendor,
                                'price': new_price,
                                'status': new_status
                            })
                            st.session_state.content_props[content_id] = props
                            auto_save()
                            st.rerun()
                
                st.divider()
                
                # 소품 목록
                if props:
                    st.markdown("**📦 소품 목록**")
                    for prop_idx, prop in enumerate(props):
                        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
                        
                        with col1:
                            st.text_input("이름", value=prop['name'], 
                                        key=f"prop_name_{content_id}_{prop_idx}", 
                                        label_visibility="collapsed",
                                        disabled=True)
                        with col2:
                            st.text_input("구매처", value=prop['vendor'],
                                        key=f"prop_vendor_{content_id}_{prop_idx}", 
                                        label_visibility="collapsed",
                                        disabled=True)
                        with col3:
                            st.text_input("금액", value=f"{prop['price']:,}원",
                                        key=f"prop_price_{content_id}_{prop_idx}", 
                                        label_visibility="collapsed",
                                        disabled=True)
                        with col4:
                            status_emoji = {"예정": "🔵", "주문완료": "🟡", "배송중": "🟠", "수령완료": "🟢"}
                            st.text_input("상태", 
                                        value=f"{status_emoji.get(prop['status'], '')} {prop['status']}",
                                        key=f"prop_status_{content_id}_{prop_idx}", 
                                        label_visibility="collapsed",
                                        disabled=True)
                        with col5:
                            if st.button("🗑️", key=f"del_prop_{content_id}_{prop_idx}"):
                                props.pop(prop_idx)
                                st.session_state.content_props[content_id] = props
                                auto_save()
                                st.rerun()
                    
                    # 콘텐츠별 소계
                    st.info(f"**소계: {len(props)}개 | 완료: {content_completed}개 | {content_total:,}원**")
                else:
                    st.write("아직 등록된 소품이 없습니다.")
        
        # 전체 통계 표시
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체 콘텐츠", f"{len(contents)}개")
        with col2:
            st.metric("전체 소품 수", f"{sum(len(st.session_state.content_props.get(c.get('id', f'{prop_date_key}_{i}'), [])) for i, c in enumerate(contents))}개")
        with col3:
            st.metric("총 구매 금액", f"{total_all_props:,}원")
        
    else:
        st.warning(f"⚠️ {prop_date.strftime('%Y년 %m월 %d일')}에 생성된 콘텐츠가 없습니다.")

with tab3:
    st.subheader("⏰ 타임테이블")
    
    # 날짜 선택
    schedule_date = st.date_input("📅 날짜 선택", datetime.now(), key="schedule_date")
    schedule_date_key = schedule_date.strftime('%Y-%m-%d')
    
    # 해당 날짜의 콘텐츠 가져오기
    if schedule_date_key in st.session_state.daily_contents and st.session_state.daily_contents[schedule_date_key]:
        contents = st.session_state.daily_contents[schedule_date_key]
        
        st.markdown(f"### 📅 {schedule_date.strftime('%Y년 %m월 %d일')} 촬영 일정")
        
        # 시작 시간 설정
        default_start = st.time_input("🕐 촬영 시작 시간", time(12, 40))
        
        # 콘텐츠별 타임테이블 생성
        current_time = datetime.combine(schedule_date, default_start)
        
        for idx, content in enumerate(contents):
            if not content.get('title'):
                continue
                
            with st.expander(f"📺 {content['title']}", expanded=True):
                col1, col2, col3 = st.columns([2, 2, 4])
                
                with col1:
                    # 시간 설정
                    duration_options = ["50분", "1시간", "1시간 30분", "2시간"]
                    duration = st.selectbox(
                        "촬영 시간",
                        duration_options,
                        key=f"duration_{schedule_date_key}_{idx}"
                    )
                    
                    # 시간 계산
                    duration_map = {"50분": 50, "1시간": 60, "1시간 30분": 90, "2시간": 120}
                    duration_mins = duration_map[duration]
                    end_time = current_time + timedelta(minutes=duration_mins)
                    
                    st.write(f"**{current_time.strftime('%H:%M')} ~ {end_time.strftime('%H:%M')}**")
                    current_time = end_time + timedelta(minutes=10)  # 10분 휴식
                
                with col2:
                    # 최종 픽스 내용
                    if content.get('final'):
                        st.text_area(
                            "최종 내용",
                            value=content['final'][:100] + "...",
                            height=100,
                            disabled=True,
                            key=f"final_view_{schedule_date_key}_{idx}"
                        )
                    else:
                        st.warning("최종 픽스 미완료")
                
                with col3:
                    # 수령 완료된 소품 표시
                    content_id = content.get('id', f"{schedule_date_key}_{idx}")
                    if content_id in st.session_state.content_props:
                        props = st.session_state.content_props[content_id]
                        completed_props = [p for p in props if p['status'] == '수령완료']
                        
                        if completed_props:
                            st.write("**✅ 준비 완료 소품:**")
                            props_text = ", ".join([f"{p['name']} ({p['vendor']})" for p in completed_props])
                            st.success(props_text)
                        else:
                            st.warning("⚠️ 수령 완료된 소품 없음")
                    else:
                        st.info("등록된 소품 없음")
        
        # 전체 일정 요약
        st.divider()
        st.info(f"📌 **전체 촬영 시간**: {default_start.strftime('%H:%M')} ~ {current_time.strftime('%H:%M')}")
        
    else:
        st.warning(f"⚠️ {schedule_date.strftime('%Y년 %m월 %d일')}에 생성된 콘텐츠가 없습니다.")

# 사이드바
with st.sidebar:
    st.header("💾 상태")
    
    # 마지막 저장 시간
    if 'last_save' in st.session_state:
        st.caption(f"마지막 저장: {st.session_state.last_save}")
    
    # 현재 사용자 수 (더미 데이터)
    st.metric("🟢 온라인", "3명")
    
    st.divider()
    st.caption("💡 Tip: 모든 변경사항은 자동 저장됩니다")
