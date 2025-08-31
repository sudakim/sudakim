import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import json
import requests
import re

# 페이지 설정
st.set_page_config(
    page_title="유튜브 콘텐츠 매니저",
    page_icon="🎬",
    layout="wide"
)

# 모바일 최적화 CSS
st.markdown("""
    <style>
    /* 모바일 최적화 */
    @media (max-width: 768px) {
        .stTimeInput > div > div {
            width: 90px !important;
        }
        .row-widget.stButton {
            padding: 0.1rem !important;
        }
        .row-widget.stButton button {
            padding: 0.25rem 0.5rem !important;
            font-size: 0.9rem !important;
        }
        .streamlit-expanderHeader {
            padding: 0.5rem !important;
        }
    }
    /* 버튼 간격 축소 */
    div[data-testid="column"] > div {
        padding: 0 2px;
    }
    /* 영상 업로드 탭 공백 제거 */
    [data-testid="stVerticalBlock"] > [style*="gap"] {
        gap: 0.5rem !important;
    }
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    hr {
        margin: 0.5rem 0 !important;
    }
    </style>
""", unsafe_allow_html=True)
# ========== 유틸리티 함수 ==========
def get_youtube_id(url):
    """YouTube URL에서 비디오 ID 추출"""
    if not url:
        return None
    
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?]*)',
        r'youtube\.com\/watch\?.*v=([^&\n?]*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def show_youtube_player(video_id, key):
    """YouTube 플레이어 표시"""
    if video_id:
        st.markdown(f"""
            <iframe width="100%" height="315" 
            src="https://www.youtube.com/embed/{video_id}" 
            frameborder="0" allowfullscreen></iframe>
        """, unsafe_allow_html=True)

# ========== GitHub Gist 설정 ==========
try:
    GITHUB_TOKEN = st.secrets["github_token"]
    GIST_ID = st.secrets["gist_id"]
except:
    GITHUB_TOKEN = "ghp_YOUR_GITHUB_TOKEN_HERE"
    GIST_ID = "YOUR_GIST_ID_HERE"

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
    try:
        PASSWORD = st.secrets["app_password"]
    except:
        PASSWORD = "youtube1234"
    
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
        st.error("비밀번호가 틀렸습니다")
        return False
    else:
        return True

if not check_password():
    st.stop()

# ========== 세션 초기화 ==========
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

if not st.session_state.initialized:
    data = load_from_gist()
    if data:
        st.session_state.daily_contents = data.get('contents', {})
        st.session_state.content_props = data.get('props', {})
        st.session_state.schedules = data.get('schedules', {})
        st.session_state.upload_status = data.get('upload_status', {})
        st.toast("☁️ 데이터를 불러왔습니다", icon='✅')
    else:
        st.session_state.daily_contents = {}
        st.session_state.content_props = {}
        st.session_state.schedules = {}
        st.session_state.upload_status = {}
    st.session_state.initialized = True

def auto_save():
    """자동 저장"""
    data = {
        'contents': st.session_state.daily_contents,
        'props': st.session_state.content_props,
        'schedules': st.session_state.schedules,
        'upload_status': st.session_state.upload_status,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if save_to_gist(data):
        st.session_state.last_save = datetime.now().strftime('%H:%M:%S')
        return True
    return False

def refresh_data():
    """데이터 새로고침"""
    data = load_from_gist()
    if data:
        st.session_state.daily_contents = data.get('contents', {})
        st.session_state.content_props = data.get('props', {})
        st.session_state.schedules = data.get('schedules', {})
        st.session_state.upload_status = data.get('upload_status', {})
        st.toast("🔄 새로고침 완료", icon='✅')
        st.rerun()

# ========== 메인 UI ==========
col1, col2, col3 = st.columns([6, 1, 1])
with col1:
    st.title("🎬 유튜브 콘텐츠 매니저")
with col2:
    if st.button("🔄"):
        refresh_data()
with col3:
    if st.button("💾"):
        if auto_save():
            st.toast("저장 완료", icon='✅')

# ========== 탭 메뉴 ==========
tab1, tab2, tab3, tab4 = st.tabs(["📝 콘텐츠 기획", "🛍️ 소품 구매", "⏰ 타임테이블", "📹 영상 업로드 현황"])

with tab1:
    st.subheader("📝 콘텐츠 기획")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        selected_date = st.date_input("날짜 선택", datetime.now(), key="content_date")
        date_key = selected_date.strftime('%Y-%m-%d')
    
    with col2:
        num_contents = st.number_input("개수", min_value=1, max_value=10, value=3)
    
    with col3:
        if st.button("✨ 양식 생성", type="primary"):
            if date_key not in st.session_state.daily_contents:
                st.session_state.daily_contents[date_key] = []
            
            current_count = len(st.session_state.daily_contents[date_key])
            for i in range(num_contents - current_count):
                content_id = f"{date_key}_{current_count + i}"
                st.session_state.daily_contents[date_key].append({
                    'id': content_id,
                    'title': '',
                    'draft': '',
                    'feedback': '',
                    'revision': '',
                    'final': '',
                    'reference': '',
                    'performers': []
                })
                # 업로드 상태 초기화
                st.session_state.upload_status[content_id] = '촬영전'
            auto_save()
            st.rerun()
    
    st.divider()
    
    if date_key in st.session_state.daily_contents and st.session_state.daily_contents[date_key]:
        st.subheader(f"📋 {selected_date.strftime('%m월 %d일')} 콘텐츠")
        
        contents = st.session_state.daily_contents[date_key]
        
        for idx, content in enumerate(contents):
            # 제목이 있으면 제목 표시, 없으면 번호만 표시
            expander_title = f"#{idx+1}. {content.get('title', '')}" if content.get('title') else f"#{idx+1}"
            
            with st.expander(expander_title, expanded=True):
                
                # 상단 버튼들
                col_del, col_move, col_title = st.columns([1, 2, 3])
                with col_del:
                    if st.button("🗑️", key=f"del_{date_key}_{idx}"):
                        st.session_state.daily_contents[date_key].pop(idx)
                        auto_save()
                        st.rerun()
                
                with col_move:
                    # 날짜 이동
                    move_date = st.date_input(
                        "이동",
                        datetime.now(),
                        key=f"move_date_{date_key}_{idx}",
                        label_visibility="collapsed"
                    )
                    if st.button("→이동", key=f"move_{date_key}_{idx}"):
                        move_key = move_date.strftime('%Y-%m-%d')
                        if move_key != date_key:
                            if move_key not in st.session_state.daily_contents:
                                st.session_state.daily_contents[move_key] = []
                            st.session_state.daily_contents[move_key].append(content)
                            st.session_state.daily_contents[date_key].pop(idx)
                            auto_save()
                            st.success(f"{move_date.strftime('%m/%d')}로 이동됨")
                            st.rerun()
                
                with col_title:
                    content['title'] = st.text_input(
                        "제목",
                        value=content.get('title', ''),
                        key=f"{date_key}_title_{idx}",
                        placeholder="제목 입력",
                        label_visibility="collapsed"
                    )
                
                # 출연자 선택
                performers = ["전부", "다혜", "수빈", "예람", "보조"]
                selected_performers = st.multiselect(
                    "출연자",
                    performers,
                    default=content.get('performers', []),
                    key=f"{date_key}_performers_{idx}"
                )
                content['performers'] = selected_performers
                
                # 레퍼런스 링크
                col_ref, col_watch = st.columns([4, 1])
                with col_ref:
                    content['reference'] = st.text_input(
                        "링크",
                        value=content.get('reference', ''),
                        key=f"{date_key}_ref_{idx}",
                        placeholder="YouTube/Instagram 링크",
                        label_visibility="collapsed"
                    )
                with col_watch:
                    if content.get('reference'):
                        # YouTube
                        if 'youtube' in content['reference'] or 'youtu.be' in content['reference']:
                            if st.button("▶️", key=f"watch_{date_key}_{idx}"):
                                st.session_state[f"show_video_{date_key}_{idx}"] = True
                        # Instagram Reels
                        elif 'instagram.com/reel' in content['reference']:
                            st.link_button("📷", content['reference'], help="Instagram에서 보기")
                
                # 유튜브 플레이어
                if st.session_state.get(f"show_video_{date_key}_{idx}"):
                    video_id = get_youtube_id(content['reference'])
                    if video_id:
                        col_video, col_close = st.columns([10, 1])
                        with col_video:
                            show_youtube_player(video_id, f"player_{date_key}_{idx}")
                        with col_close:
                            if st.button("✕", key=f"close_{date_key}_{idx}"):
                                st.session_state[f"show_video_{date_key}_{idx}"] = False
                                st.rerun()
                
                # 4단계 프로세스
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown("**초안**")
                    content['draft'] = st.text_area(
                        "초안",
                        value=content.get('draft', ''),
                        height=120,
                        key=f"{date_key}_draft_{idx}",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    st.markdown("**피드백**")
                    content['feedback'] = st.text_area(
                        "피드백",
                        value=content.get('feedback', ''),
                        height=120,
                        key=f"{date_key}_feedback_{idx}",
                        label_visibility="collapsed"
                    )
                
                with col3:
                    st.markdown("**추가의견**")
                    content['revision'] = st.text_area(
                        "추가",
                        value=content.get('revision', ''),
                        height=120,
                        key=f"{date_key}_revision_{idx}",
                        label_visibility="collapsed"
                    )
                
                with col4:
                    st.markdown("**최종**")
                    content['final'] = st.text_area(
                        "최종",
                        value=content.get('final', ''),
                        height=120,
                        key=f"{date_key}_final_{idx}",
                        label_visibility="collapsed"
                    )
                
                progress = sum([25 for field in ['draft', 'feedback', 'revision', 'final'] if content.get(field)])
                st.progress(progress / 100)

with tab2:
    st.subheader("🛍️ 소품 구매")
    
    prop_date = st.date_input("날짜", datetime.now(), key="prop_date")
    prop_date_key = prop_date.strftime('%Y-%m-%d')
    
    if prop_date_key in st.session_state.daily_contents and st.session_state.daily_contents[prop_date_key]:
        contents = st.session_state.daily_contents[prop_date_key]
        
        total_props = 0
        
        for idx, content in enumerate(contents):
            content_id = content.get('id', f"{prop_date_key}_{idx}")
            
            if content_id not in st.session_state.content_props:
                st.session_state.content_props[content_id] = []
            
            props = st.session_state.content_props[content_id]
            total_quantity = sum(p.get('quantity', 1) for p in props)
            total_props += total_quantity
            
            # 제목이 있으면 제목 표시, 없으면 번호만 표시
            expander_title = f"#{idx+1}. {content.get('title')}" if content.get('title') else f"#{idx+1}"
            expander_title += f" ({len(props)}종 / 총 {total_quantity}개)"
            
            with st.expander(expander_title):
                
                # 레퍼런스 링크 표시
                if content.get('reference'):
                    col_ref, col_btn = st.columns([5, 1])
                    with col_ref:
                        st.caption(f"📎 {content['reference'][:50]}...")
                    with col_btn:
                        if st.button("▶️", key=f"prop_watch_{content_id}"):
                            st.session_state[f"show_prop_video_{content_id}"] = True
                    
                    if st.session_state.get(f"show_prop_video_{content_id}"):
                        video_id = get_youtube_id(content['reference'])
                        if video_id:
                            show_youtube_player(video_id, f"prop_player_{content_id}")
                            if st.button("✕ 닫기", key=f"close_prop_{content_id}"):
                                st.session_state[f"show_prop_video_{content_id}"] = False
                                st.rerun()
                
                # 소품 추가
                st.markdown("**➕ 추가**")
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
                
                with col1:
                    new_name = st.text_input("소품", key=f"new_n_{content_id}")
                with col2:
                    new_vendor = st.selectbox("구매처", 
                        ["쿠팡", "다이소", "세계과자", "개인(다혜)", "개인(예람)", "개인(수빈)", "테무", "알리", "마트", "기타"],
                        key=f"new_v_{content_id}")
                with col3:
                    new_quantity = st.number_input("개수", 1, step=1, key=f"new_q_{content_id}")
                with col4:
                    new_status = st.selectbox("상태",
                        ["예정", "주문완료", "배송중", "수령완료"],
                        key=f"new_s_{content_id}")
                with col5:
                    if st.button("추가", key=f"add_{content_id}", type="primary"):
                        if new_name:
                            props.append({
                                'name': new_name,
                                'vendor': new_vendor,
                                'quantity': new_quantity,
                                'status': new_status
                            })
                            auto_save()
                            st.rerun()
                
                # 소품 목록 (수정 가능)
                if props:
                    st.divider()
                    for p_idx, prop in enumerate(props):
                        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
                        
                        with col1:
                            prop['name'] = st.text_input("", value=prop['name'],
                                key=f"pn_{content_id}_{p_idx}", label_visibility="collapsed")
                        with col2:
                            vendor_list = ["쿠팡", "다이소", "세계과자", "개인(다혜)", "개인(예람)", "개인(수빈)", "테무", "알리", "마트", "기타"]
                            current_vendor = prop.get('vendor', '기타')
                            if current_vendor not in vendor_list:
                                current_vendor = '기타'
                            prop['vendor'] = st.selectbox("", 
                                vendor_list,
                                index=vendor_list.index(current_vendor),
                                key=f"pv_{content_id}_{p_idx}", label_visibility="collapsed")
                        with col3:
                            prop['quantity'] = st.number_input("", value=prop.get('quantity', 1),
                                min_value=1, key=f"pq_{content_id}_{p_idx}", label_visibility="collapsed")
                        with col4:
                            prop['status'] = st.selectbox("",
                                ["예정", "주문완료", "배송중", "수령완료"],
                                index=["예정", "주문완료", "배송중", "수령완료"].index(prop['status']),
                                key=f"ps_{content_id}_{p_idx}", label_visibility="collapsed")
                        with col5:
                            if st.button("🗑️", key=f"d_{content_id}_{p_idx}"):
                                props.pop(p_idx)
                                auto_save()
                                st.rerun()
                    
                    # 자동 저장
                    if st.button("💾 저장", key=f"save_{content_id}"):
                        auto_save()
                        st.success("저장됨")
        
        # 전체 소품 요약 테이블
        st.divider()
        st.subheader("📊 전체 소품 현황")
        
        summary_data = []
        for idx, content in enumerate(contents):
            content_id = content.get('id', f"{prop_date_key}_{idx}")
            if content_id in st.session_state.content_props:
                props = st.session_state.content_props[content_id]
                if props:
                    props_summary = []
                    for p in props:
                        status = {"예정":"🔵", "주문완료":"🟡", "배송중":"🟠", "수령완료":"🟢"}.get(p['status'], '')
                        props_summary.append(f"{p['name']}{status}({p.get('quantity', 1)}개)")
                    summary_data.append({
                        '콘텐츠': content.get('title', f'#{idx+1}'),
                        '소품': ', '.join(props_summary),
                        '총개수': f"{sum(p.get('quantity', 1) for p in props)}개"
                    })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.metric("전체 개수", f"{total_props}개")
    else:
        st.warning("이 날짜에 콘텐츠가 없습니다")

with tab3:
    st.subheader("⏰ 타임테이블")
    
    schedule_date = st.date_input("날짜", datetime.now(), key="schedule_date")
    schedule_date_key = schedule_date.strftime('%Y-%m-%d')
    
    if schedule_date_key not in st.session_state.schedules:
        st.session_state.schedules[schedule_date_key] = []
    
    schedule = st.session_state.schedules[schedule_date_key]
    
    # 새 일정 추가
    with st.expander("➕ 일정 추가", expanded=False):
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 2, 1])
        
        with col1:
            new_start = st.time_input("시작", time(12, 0), key="new_start")
        with col2:
            new_end = st.time_input("종료", time(13, 0), key="new_end")
        with col3:
            types = ["🎬촬영", "🍽️식사", "☕휴식", "📝회의", "🚗이동", "🎯기타"]
            new_type = st.selectbox("유형", types, key="new_type")
        with col4:
            new_title = st.text_input("제목", key="new_title")
        with col5:
            if st.button("추가", type="primary"):
                if new_title:
                    new_item = {
                        'start': new_start.strftime('%H:%M'),
                        'end': new_end.strftime('%H:%M'),
                        'type': new_type,
                        'title': new_title,
                        'content_id': None,
                        'details': ''
                    }
                    schedule.append(new_item)
                    # 시간순 정렬
                    schedule.sort(key=lambda x: x['start'])
                    st.session_state.schedules[schedule_date_key] = schedule
                    auto_save()
                    st.rerun()
    
    # 콘텐츠 일괄 추가
    if schedule_date_key in st.session_state.daily_contents:
        contents = st.session_state.daily_contents.get(schedule_date_key, [])
        if contents:
            with st.expander("📺 콘텐츠 일괄 추가"):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    batch_start = st.time_input("시작", time(12, 40), key="batch_start")
                with col2:
                    batch_dur = st.selectbox("시간", ["50분", "1시간", "1시간 30분"], key="batch_dur")
                with col3:
                    if st.button("일괄추가"):
                        dur_map = {"50분": 50, "1시간": 60, "1시간 30분": 90}
                        current = datetime.combine(schedule_date, batch_start)
                        
                        for c in contents:
                            if c.get('title'):
                                end = current + timedelta(minutes=dur_map[batch_dur])
                                schedule.append({
                                    'start': current.strftime('%H:%M'),
                                    'end': end.strftime('%H:%M'),
                                    'type': '🎬촬영',
                                    'title': c['title'],
                                    'content_id': c.get('id'),
                                    'details': ''
                                })
                                current = end + timedelta(minutes=10)
                        
                        schedule.sort(key=lambda x: x['start'])
                        st.session_state.schedules[schedule_date_key] = schedule
                        auto_save()
                        st.rerun()
    
    # 일정 목록
    if schedule:
        st.markdown("### 📋 일정 목록")
        
        for idx in range(len(schedule)):
            item = schedule[idx]
            
            # 출연자 정보 미리 가져오기
            performers_info = ""
            if item.get('content_id'):
                for date_contents in st.session_state.daily_contents.values():
                    for c in date_contents:
                        if c.get('id') == item['content_id']:
                            if c.get('performers'):
                                performers_info = " (" + ", ".join(c['performers']) + ")"
                            break
            
            # 요약 보기 - 모바일 최적화
            with st.container():
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    st.write(f"**{item['start']} - {item['end']}** {item['type']}")
                    st.write(f"{item['title']}{performers_info}")
                
                with col2:
                    # 버튼 3개를 세로로 컴팩트하게
                    btn_col = st.container()
                    with btn_col:
                        btn_cols = st.columns(3)
                        with btn_cols[0]:
                            if st.button("↑", key=f"up_{idx}", help="위로"):
                                if idx > 0:
                                    schedule[idx], schedule[idx-1] = schedule[idx-1], schedule[idx]
                                    auto_save()
                                    st.rerun()
                        with btn_cols[1]:
                            if st.button("↓", key=f"down_{idx}", help="아래"):
                                if idx < len(schedule) - 1:
                                    schedule[idx], schedule[idx+1] = schedule[idx+1], schedule[idx]
                                    auto_save()
                                    st.rerun()
                        with btn_cols[2]:
                            if st.button("🗑️", key=f"del_{idx}", help="삭제"):
                                schedule.pop(idx)
                                auto_save()
                                st.rerun()
            
            # 상세 보기 (토글)
            with st.expander("상세보기"):
                # 콘텐츠 정보 표시
                if item.get('content_id'):
                    # 레퍼런스 링크
                    for date_contents in st.session_state.daily_contents.values():
                        for c in date_contents:
                            if c.get('id') == item['content_id']:
                                if c.get('reference'):
                                    col_r, col_b = st.columns([5, 1])
                                    with col_r:
                                        st.caption(f"📎{c['reference'][:50]}...")
                                    with col_b:
                                        if st.button("▶️", key=f"tv_{idx}"):
                                            video_id = get_youtube_id(c['reference'])
                                            if video_id:
                                                show_youtube_player(video_id, f"tp_{idx}")
                                
                                # 픽스 내용
                                if c.get('final'):
                                    st.text_area("최종 픽스", c['final'], disabled=True, key=f"f_{idx}")
                                
                                break
                    
                    # 소품 정보
                    if item['content_id'] in st.session_state.content_props:
                        props = st.session_state.content_props[item['content_id']]
                        if props:
                            props_list = []
                            for p in props:
                                emoji = {"예정":"🔵", "주문완료":"🟡", "배송중":"🟠", "수령완료":"🟢"}.get(p['status'])
                                props_list.append(f"{p['name']}{emoji}")
                            st.success("소품: " + ", ".join(props_list))
                
                # 메모
                item['details'] = st.text_area("메모", value=item.get('details', ''), key=f"memo_{idx}")
        
        if st.button("💾 타임테이블 저장", type="primary"):
            auto_save()
            st.success("저장됨")
        
        # 전체 시간
        if schedule:
            st.info(f"📌 전체: {schedule[0]['start']} ~ {schedule[-1]['end']}")

with tab4:
    st.subheader("📹 영상 업로드 현황")
    
    # 전체 콘텐츠 수집
    all_contents = []
    for date_key, contents in st.session_state.daily_contents.items():
        for content in contents:
            content_copy = content.copy()
            content_copy['date'] = date_key
            all_contents.append(content_copy)
    
    # 날짜순 정렬
    all_contents.sort(key=lambda x: x['date'], reverse=True)
    
    if all_contents:
        # 필터링 옵션
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_status = st.multiselect(
                "상태 필터",
                ["촬영전", "촬영완료", "편집완료", "업로드완료"],
                key="filter_upload_status"
            )
        with col2:
            filter_date_from = st.date_input("시작일", datetime.now() - timedelta(days=30), key="filter_from")
        with col3:
            filter_date_to = st.date_input("종료일", datetime.now(), key="filter_to")
        
        # 필터링 적용
        filtered_contents = all_contents
        if filter_status:
            filtered_contents = [c for c in filtered_contents if st.session_state.upload_status.get(c['id'], '촬영전') in filter_status]
        
        filtered_contents = [c for c in filtered_contents 
                            if filter_date_from.strftime('%Y-%m-%d') <= c['date'] <= filter_date_to.strftime('%Y-%m-%d')]
        
        # 테이블 형식으로 표시
        if filtered_contents:  # filtered_contents가 있을 때만 전체 섹션 표시
            st.markdown("### 📊 전체 콘텐츠 현황")
            
            # 테이블 헤더
            col1, col2, col3, col4, col5, col6 = st.columns([0.8, 2.5, 1.2, 1, 0.7, 0.3])
            with col1:
                st.caption("**날짜**")
            with col2:
                st.caption("**제목**")
            with col3:
                st.caption("**상태**")
            with col4:
                st.caption("**이동날짜선택**")
            with col5:
                st.caption("")
            with col6:
                st.caption("")
            
        else:
            st.info("필터 조건에 맞는 콘텐츠가 없습니다.")
           
        for content in filtered_contents:
            col1, col2, col3, col4, col5, col6 = st.columns([0.8, 2.5, 1.2, 1, 0.7, 0.3])
                        
            with col1:
                st.write(content['date'][5:])  # MM-DD 형식
            
            with col2:
                title_text = content.get('title', '제목 없음')
                if content.get('performers'):
                    title_text += f" ({', '.join(content['performers'])})"
                st.write(title_text)
            
            with col3:
                # 상태 선택
                status_options = ["촬영전", "촬영완료", "편집완료", "업로드완료"]
                current_status = st.session_state.upload_status.get(content['id'], '촬영전')
                status_emoji = {"촬영전": "🔵", "촬영완료": "🟡", "편집완료": "🟠", "업로드완료": "🟢"}
                new_status = st.selectbox(
                    "",
                    status_options,
                    index=status_options.index(current_status),
                    key=f"status_{content['id']}",
                    label_visibility="collapsed",
                    format_func=lambda x: f"{status_emoji.get(x, '')} {x}"
                )
                if new_status != current_status:
                    st.session_state.upload_status[content['id']] = new_status
                    auto_save()
            
            with col4:
                # 날짜 이동
                new_date = st.date_input(
                    "",
                    datetime.strptime(content['date'], '%Y-%m-%d'),
                    key=f"move_upload_{content['id']}",
                    label_visibility="collapsed"
                )
            
            with col5:
                if st.button("이동", key=f"move_btn_{content['id']}"):
                    old_date = content['date']
                    new_date_key = new_date.strftime('%Y-%m-%d')
                    
                    if old_date != new_date_key:
                        for idx, c in enumerate(st.session_state.daily_contents[old_date]):
                            if c['id'] == content['id']:
                                moved_content = st.session_state.daily_contents[old_date].pop(idx)
                                break
                        
                        if new_date_key not in st.session_state.daily_contents:
                            st.session_state.daily_contents[new_date_key] = []
                        st.session_state.daily_contents[new_date_key].append(moved_content)
                        
                        auto_save()
                        st.toast(f"✅ {new_date_key}로 이동", icon='✅')
                        st.rerun()
            
            with col6:
                if st.button("🗑️", key=f"del_upload_{content['id']}", help="삭제"):
                    for idx, c in enumerate(st.session_state.daily_contents[content['date']]):
                        if c['id'] == content['id']:
                            st.session_state.daily_contents[content['date']].pop(idx)
                            if not st.session_state.daily_contents[content['date']]:
                                del st.session_state.daily_contents[content['date']]
                            if content['id'] in st.session_state.upload_status:
                                del st.session_state.upload_status[content['id']]
                            if content['id'] in st.session_state.content_props:
                                del st.session_state.content_props[content['id']]
                            break
                    auto_save()
                    st.rerun()
        
        # 통계
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("전체", f"{len(filtered_contents)}개")
        with col2:
            st.metric("촬영완료", f"{len([c for c in filtered_contents if st.session_state.upload_status.get(c['id'], '촬영전') == '촬영완료'])}개")
        with col3:
            st.metric("편집완료", f"{len([c for c in filtered_contents if st.session_state.upload_status.get(c['id'], '촬영전') == '편집완료'])}개")
        with col4:
            st.metric("업로드완료", f"{len([c for c in filtered_contents if st.session_state.upload_status.get(c['id'], '촬영전') == '업로드완료'])}개")
    else:
        st.info("아직 등록된 콘텐츠가 없습니다.")












