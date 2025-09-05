# youtube_manager.py
import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import json
import requests
import re

# ------------------------- 페이지/스타일 -------------------------
st.set_page_config(page_title="유튜브 콘텐츠 매니저", page_icon="🎬", layout="wide")
st.markdown("""
<style>
@media (max-width: 768px) {
  .stTimeInput > div > div { width: 90px !important; }
  .row-widget.stButton { padding: 0.1rem !important; }
  .row-widget.stButton button { padding: 0.25rem 0.5rem !important; font-size: 0.9rem !important; }
  .streamlit-expanderHeader { padding: 0.5rem !important; }
}
div[data-testid="column"] > div { padding: 0 2px; }
[data-testid="stVerticalBlock"] > [style*="gap"] { gap: 0.5rem !important; }
.element-container { margin-bottom: 0.5rem !important; }
hr { margin: 0.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------- 공용 상수 -------------------------
# 소품 상태(배송중 제거)
PROP_STATUS_OPTIONS = ["예정", "주문완료", "수령완료"]
PROP_STATUS_EMOJI   = {"예정":"🔵", "주문완료":"🟡", "수령완료":"🟢"}
PROP_STATUS_LEGEND  = "🔵 파랑=예정 · 🟡 노랑=주문완료 · 🟢 초록=수령완료"

# 업로드 현황 상태
UPLOAD_STATUS_OPTIONS = ["촬영전", "촬영완료", "편집완료", "업로드완료"]
UPLOAD_STATUS_EMOJI   = {"촬영전":"🔵","촬영완료":"🟡","편집완료":"🟠","업로드완료":"🟢"}

# ------------------------- 유틸 함수 -------------------------
def get_youtube_id(url: str | None):
    """watch?v= / youtu.be / embed / shorts 모두 지원, 쿼리 제거"""
    if not url:
        return None
    m = re.search(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/))([A-Za-z0-9_\-]{6,})', url)
    return m.group(1).split('?')[0].split('&')[0] if m else None

def show_youtube_player(video_id):
    if video_id:
        st.markdown(
            f'<iframe width="100%" height="315" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>',
            unsafe_allow_html=True
        )

def nearest_content_date_from_today():
    """
    오늘 기준으로 가장 가까운 '미래(오늘 포함)' 날짜 중
    콘텐츠가 1개 이상 등록된 날짜를 반환.
    없다면 가장 최근 과거 날짜를 반환.
    그래도 없으면 오늘 날짜를 반환.
    """
    contents = st.session_state.get('daily_contents', {})
    dates = [datetime.strptime(k, '%Y-%m-%d').date()
             for k, v in contents.items() if v]
    if not dates:
        return datetime.now().date()
    dates = sorted(dates)
    today = datetime.now().date()
    for d in dates:
        if d >= today:
            return d
    return dates[-1]

def _to_time(s: str) -> time:
    return datetime.strptime(s, "%H:%M").time()

def _fmt_time(t: time) -> str:
    return t.strftime("%H:%M")

# ------------------------- Gist 저장/불러오기 -------------------------
try:
    GITHUB_TOKEN = st.secrets["github_token"]
    GIST_ID = st.secrets["gist_id"]
except Exception:
    GITHUB_TOKEN = "ghp_YOUR_GITHUB_TOKEN_HERE"
    GIST_ID = "YOUR_GIST_ID_HERE"

SESSION = requests.Session()
SESSION.headers.update({"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"})
DEFAULT_TIMEOUT = 10

def _gist_ready():
    return bool(GITHUB_TOKEN and "YOUR_GITHUB_TOKEN_HERE" not in GITHUB_TOKEN and GIST_ID and "YOUR_GIST_ID_HERE" not in GIST_ID)

def _req(method, url, **kwargs):
    for _ in range(3):  # 간단 재시도
        try:
            resp = SESSION.request(method, url, timeout=DEFAULT_TIMEOUT, **kwargs)
            if resp.status_code in (429, 500, 502, 503, 504):
                continue
            return resp
        except requests.RequestException:
            continue
    return None

def save_to_gist(data):
    if not _gist_ready():
        return False
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        payload = {"files": {"youtube_data.json": {"content": json.dumps(data, ensure_ascii=False, indent=2)}}}
        r = _req("PATCH", url, json=payload)
        return bool(r and r.status_code == 200)
    except Exception:
        return False

def load_from_gist():
    if not _gist_ready():
        return None
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        r = _req("GET", url)
        if not r or r.status_code != 200:
            return None
        files = r.json().get("files", {})
        f = files.get("youtube_data.json")
        if not f:
            return None
        if f.get("truncated") and f.get("raw_url"):
            raw = _req("GET", f["raw_url"])
            if not raw or raw.status_code != 200:
                return None
            return json.loads(raw.text)
        return json.loads(f.get("content", "{}") or "{}")
    except Exception:
        return None

# ------------------------- 비밀번호 체크 -------------------------
def check_password():
    try:
        PASSWORD = st.secrets["app_password"]
    except Exception:
        PASSWORD = "youtube1234"

    def password_entered():
        if st.session_state["password"] == PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 유튜브 콘텐츠 매니저")
        st.text_input("비밀번호를 입력하세요", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 유튜브 콘텐츠 매니저")
        st.text_input("비밀번호를 입력하세요", type="password", on_change=password_entered, key="password")
        st.error("비밀번호가 틀렸습니다")
        return False
    else:
        return True

if not check_password():
    st.stop()

# ------------------------- 세션 초기화/저장/새로고침 -------------------------
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

if not st.session_state.initialized:
    data = load_from_gist()
    if data:
        st.session_state.daily_contents = data.get('contents', {})
        st.session_state.content_props  = data.get('props', {})
        st.session_state.schedules      = data.get('schedules', {})
        st.session_state.upload_status  = data.get('upload_status', {})
        st.toast("☁️ 데이터를 불러왔습니다", icon='✅')
    else:
        st.session_state.daily_contents = {}
        st.session_state.content_props  = {}
        st.session_state.schedules      = {}
        st.session_state.upload_status  = {}
    st.session_state.initialized = True

def auto_save():
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
    data = load_from_gist()
    if data:
        st.session_state.daily_contents = data.get('contents', {})
        st.session_state.content_props  = data.get('props', {})
        st.session_state.schedules      = data.get('schedules', {})
        st.session_state.upload_status  = data.get('upload_status', {})
        st.toast("🔄 새로고침 완료", icon='✅')
        st.rerun()

# ------------------------- 상단 바 -------------------------
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

# ------------------------- 탭 -------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📝 콘텐츠 기획", "🛍️ 소품 구매", "⏰ 타임테이블", "📹 영상 업로드 현황"])

# ========================= 탭1: 콘텐츠 기획 =========================
with tab1:
    st.subheader("📝 콘텐츠 기획")

    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        selected_date = st.date_input("날짜 선택", nearest_content_date_from_today(), key="content_date")
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
                st.session_state.upload_status[content_id] = '촬영전'
            auto_save()
            st.rerun()

    st.divider()

    if date_key in st.session_state.daily_contents and st.session_state.daily_contents[date_key]:
        st.subheader(f"📋 {selected_date.strftime('%m월 %d일')} 콘텐츠")
        contents = st.session_state.daily_contents[date_key]

        for idx, content in enumerate(contents):
            expander_title = f"#{idx+1}. {content.get('title', '')}" if content.get('title') else f"#{idx+1}"
            with st.expander(expander_title, expanded=True):

                col_del, col_move, col_title = st.columns([1, 2, 3])
                with col_del:
                    if st.button("🗑️", key=f"del_{date_key}_{idx}"):
                        st.session_state.daily_contents[date_key].pop(idx)
                        auto_save()
                        st.rerun()

                with col_move:
                    move_date = st.date_input("이동", datetime.now(), key=f"move_date_{date_key}_{idx}", label_visibility="collapsed")
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
                    content['title'] = st.text_input("제목", value=content.get('title', ''), key=f"{date_key}_title_{idx}", placeholder="제목 입력", label_visibility="collapsed")

                performers = ["전부", "다혜", "수빈", "예람", "보조"]
                content['performers'] = st.multiselect("출연자", performers, default=content.get('performers', []), key=f"{date_key}_performers_{idx}")

                col_ref, col_watch = st.columns([4, 1])
                with col_ref:
                    content['reference'] = st.text_input("링크", value=content.get('reference', ''), key=f"{date_key}_ref_{idx}", placeholder="YouTube/Instagram 링크", label_visibility="collapsed")
                with col_watch:
                    if content.get('reference'):
                        if 'youtube' in content['reference'] or 'youtu.be' in content['reference']:
                            if st.button("▶️", key=f"watch_{date_key}_{idx}"):
                                st.session_state[f"show_video_{date_key}_{idx}"] = True
                        elif 'instagram.com' in content['reference']:
                            st.link_button("📷 Instagram", content['reference'], help="Instagram에서 보기")

                if st.session_state.get(f"show_video_{date_key}_{idx}"):
                    video_id = get_youtube_id(content['reference'])
                    if video_id:
                        col_video, col_close = st.columns([10, 1])
                        with col_video:
                            show_youtube_player(video_id)
                        with col_close:
                            if st.button("✕", key=f"close_{date_key}_{idx}"):
                                st.session_state[f"show_video_{date_key}_{idx}"] = False
                                st.rerun()

                col1a, col2a, col3a, col4a = st.columns(4)
                with col1a:
                    st.markdown("**초안**")
                    content['draft'] = st.text_area("초안", value=content.get('draft', ''), height=120, key=f"{date_key}_draft_{idx}", label_visibility="collapsed")
                with col2a:
                    st.markdown("**피드백**")
                    content['feedback'] = st.text_area("피드백", value=content.get('feedback', ''), height=120, key=f"{date_key}_feedback_{idx}", label_visibility="collapsed")
                with col3a:
                    st.markdown("**추가의견**")
                    content['revision'] = st.text_area("추가", value=content.get('revision', ''), height=120, key=f"{date_key}_revision_{idx}", label_visibility="collapsed")
                with col4a:
                    st.markdown("**최종**")
                    content['final'] = st.text_area("최종", value=content.get('final', ''), height=120, key=f"{date_key}_final_{idx}", label_visibility="collapsed")

                filled = sum(1 for f in ('draft','feedback','revision','final') if content.get(f))
                st.progress(min(1.0, max(0.0, filled * 0.25)))

# ========================= 탭2: 소품 구매 =========================
with tab2:
    st.subheader("🛍️ 소품 구매")

    prop_date = st.date_input("날짜", nearest_content_date_from_today(), key="prop_date")
    prop_date_key = prop_date.strftime('%Y-%m-%d')

    if prop_date_key in st.session_state.daily_contents and st.session_state.daily_contents[prop_date_key]:
        contents = st.session_state.daily_contents[prop_date_key]
        total_props = 0

        for idx, content in enumerate(contents):
            content_id = content.get('id', f"{prop_date_key}_{idx}")

            open_key = f"props_open_{content_id}"
            if open_key not in st.session_state:
                st.session_state[open_key] = False

            if content_id not in st.session_state.content_props:
                st.session_state.content_props[content_id] = []

            props = st.session_state.content_props[content_id]
            total_quantity = sum(p.get('quantity', 1) for p in props)
            total_props += total_quantity

            expander_title = f"#{idx+1}. {content.get('title')}" if content.get('title') else f"#{idx+1}"
            expander_title += f" ({len(props)}종 / 총 {total_quantity}개)"

            with st.expander(expander_title, expanded=st.session_state[open_key]):
                if content.get('reference'):
                    col_ref, col_btn = st.columns([5, 1])
                    with col_ref:
                        st.caption(f"📎 {content['reference'][:50]}...")
                    with col_btn:
                        if st.button("▶️", key=f"prop_watch_{content_id}"):
                            st.session_state[f"show_prop_video_{content_id}"] = True
                            st.session_state[open_key] = True
                            st.rerun()

                    if st.session_state.get(f"show_prop_video_{content_id}"):
                        video_id = get_youtube_id(content['reference'])
                        if video_id:
                            show_youtube_player(video_id)
                            if st.button("✕ 닫기", key=f"close_prop_{content_id}"):
                                st.session_state[f"show_prop_video_{content_id}"] = False
                                st.session_state[open_key] = True
                                st.rerun()

                st.markdown("**➕ 추가**")
                col1b, col2b, col3b, col4b, col5b = st.columns([2, 2, 2, 2, 1])

                with col1b:
                    new_name = st.text_input("소품", key=f"new_n_{content_id}")
                with col2b:
                    new_vendor = st.selectbox(
                        "구매처",
                        ["쿠팡", "다이소", "세계과자", "개인(다혜)", "개인(예람)", "개인(수빈)", "테무", "알리", "마트", "기타"],
                        key=f"new_v_{content_id}")
                with col3b:
                    new_quantity = st.number_input("개수", min_value=1, value=1, step=1, key=f"new_q_{content_id}")
                with col4b:
                    new_status = st.selectbox("상태", PROP_STATUS_OPTIONS, key=f"new_s_{content_id}")
                with col5b:
                    if st.button("추가", key=f"add_{content_id}", type="primary"):
                        if new_name:
                            props.append({
                                'name': new_name.strip(),
                                'vendor': new_vendor,
                                'quantity': int(new_quantity),
                                'status': new_status
                            })
                            auto_save()
                            st.session_state[open_key] = True
                            st.rerun()

                if props:
                    st.divider()
                    for p_idx, p in enumerate(props):
                        col1c, col2c, col3c, col4c, col5c = st.columns([2, 2, 2, 2, 1])

                        with col1c:
                            p['name'] = st.text_input("", value=p['name'], key=f"pn_{content_id}_{p_idx}", label_visibility="collapsed")
                        with col2c:
                            vendor_list = ["쿠팡", "다이소", "세계과자", "개인(다혜)", "개인(예람)", "개인(수빈)", "테무", "알리", "마트", "기타"]
                            cur_vendor = p.get('vendor', '기타')
                            if cur_vendor not in vendor_list:
                                cur_vendor = '기타'
                            p['vendor'] = st.selectbox("", vendor_list, index=vendor_list.index(cur_vendor), key=f"pv_{content_id}_{p_idx}", label_visibility="collapsed")
                        with col3c:
                            p['quantity'] = st.number_input("", value=int(p.get('quantity', 1)), min_value=1, step=1, key=f"pq_{content_id}_{p_idx}", label_visibility="collapsed")
                        with col4c:
                            if p.get('status') not in PROP_STATUS_OPTIONS:
                                p['status'] = "예정"
                            p['status'] = st.selectbox("", PROP_STATUS_OPTIONS, index=PROP_STATUS_OPTIONS.index(p['status']), key=f"ps_{content_id}_{p_idx}", label_visibility="collapsed")
                        with col5c:
                            if st.button("🗑️", key=f"d_{content_id}_{p_idx}"):
                                props.pop(p_idx)
                                auto_save()
                                st.session_state[open_key] = True
                                st.rerun()

                    if st.button("💾 저장", key=f"save_{content_id}"):
                        auto_save()
                        st.session_state[open_key] = True
                        st.success("저장됨")

        st.divider()
        st.subheader("📊 전체 소품 현황")
        st.caption(PROP_STATUS_LEGEND)

        summary_data, total_count = [], 0
        for idx, content in enumerate(contents):
            content_id = content.get('id', f"{prop_date_key}_{idx}")
            if content_id in st.session_state.content_props:
                props = st.session_state.content_props[content_id]
                if props:
                    items = []
                    for p in props:
                        emoji = PROP_STATUS_EMOJI.get(p.get('status'), '')
                        qty = int(p.get('quantity', 1))
                        total_count += qty
                        items.append(f"{p['name']}{emoji} ({qty}개)")
                    summary_data.append({
                        '콘텐츠': content.get('title', f'#{idx+1}'),
                        '소품': ', '.join(items),
                        '총개수': f"{sum(int(x.get('quantity', 1)) for x in props)}개"
                    })

        if summary_data:
            df = pd.DataFrame(summary_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.metric("전체 개수", f"{total_count}개")
    else:
        st.warning("이 날짜에 콘텐츠가 없습니다")

# ========================= 탭3: 타임테이블 =========================
with tab3:
    st.subheader("⏰ 타임테이블")

    schedule_date = st.date_input("날짜", datetime.now(), key="schedule_date")
    schedule_date_key = schedule_date.strftime('%Y-%m-%d')

    if schedule_date_key not in st.session_state.schedules:
        st.session_state.schedules[schedule_date_key] = []

    schedule = st.session_state.schedules[schedule_date_key]

    with st.expander("➕ 일정 추가", expanded=False):
        col1d, col2d, col3d, col4d, col5d = st.columns([1, 1, 1, 2, 1])
        with col1d:
            new_start = st.time_input("시작", time(12, 0), key="new_start")
        with col2d:
            new_end = st.time_input("종료", time(13, 0), key="new_end")
        with col3d:
            types = ["🎬촬영", "🍽️식사", "☕휴식", "📝회의", "🚗이동", "🎯기타"]
            new_type = st.selectbox("유형", types, key="new_type")
        with col4d:
            new_title = st.text_input("제목", key="new_title")
        with col5d:
            if st.button("추가", type="primary"):
                if new_title:
                    new_item = {
                        'start': _fmt_time(new_start),
                        'end': _fmt_time(new_end),
                        'type': new_type,
                        'title': new_title.strip(),
                        'content_id': None,
                        'details': ''
                    }
                    schedule.append(new_item)
                    st.session_state.schedules[schedule_date_key] = schedule
                    auto_save()
                    st.rerun()

    contents = st.session_state.daily_contents.get(schedule_date_key, [])
    if contents:
        with st.expander("📺 콘텐츠 일괄 추가"):
            col1e, col2e, col3e, col4e = st.columns([2, 2, 1, 1])
            with col1e:
                batch_start = st.time_input("시작", time(12, 40), key="batch_start")
            with col2e:
                batch_dur = st.selectbox("시간", ["50분", "1시간", "1시간 30분"], key="batch_dur")
            with col3e:
                rest_gap = st.selectbox("간격", ["0분", "5분", "10분"], index=2, key="batch_gap")
            with col4e:
                if st.button("일괄추가"):
                    dur_map = {"50분": 50, "1시간": 60, "1시간 30분": 90}
                    gap_map = {"0분": 0, "5분": 5, "10분": 10}
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
                            current = end + timedelta(minutes=gap_map[rest_gap])
                    st.session_state.schedules[schedule_date_key] = schedule
                    auto_save()
                    st.rerun()

    # ----------- 인라인 편집 가능한 일정 목록 -----------
    if schedule:
        st.markdown("### 📋 일정 목록")
        ccol1, ccol2 = st.columns([6, 1])
        with ccol1:
            st.caption("시작/종료/유형/제목을 직접 수정할 수 있어요. 변경 시 자동 저장됩니다.")
        with ccol2:
            if st.button("🕒 시간순 정렬"):
                schedule.sort(key=lambda x: x['start'])
                auto_save()
                st.rerun()

        types_all = ["🎬촬영", "🍽️식사", "☕휴식", "📝회의", "🚗이동", "🎯기타"]

        for idx, item in enumerate(schedule):
            with st.container():
                # ----- 상단 요약 라인 (인라인 편집) -----
                c1, c2, c3, c4, c5, c6 = st.columns([1.1, 1.1, 1.1, 2.8, 0.7, 0.7])

                start_val = _to_time(item["start"])
                end_val   = _to_time(item["end"])
                type_val  = item.get("type", types_all[0])
                title_val = item.get("title", "")

                with c1:
                    new_start = st.time_input("시작", start_val, key=f"s_start_{schedule_date_key}_{idx}", label_visibility="visible")
                with c2:
                    new_end = st.time_input("종료", end_val, key=f"s_end_{schedule_date_key}_{idx}", label_visibility="visible")
                with c3:
                    new_type = st.selectbox("유형", types_all,
                                            index=types_all.index(type_val) if type_val in types_all else 0,
                                            key=f"s_type_{schedule_date_key}_{idx}")
                with c4:
                    new_title = st.text_input("제목", value=title_val, key=f"s_title_{schedule_date_key}_{idx}")

                with c5:
                    if st.button("↑", key=f"up_{idx}", help="위로"):
                        if idx > 0:
                            schedule[idx], schedule[idx-1] = schedule[idx-1], schedule[idx]
                            auto_save(); st.rerun()
                with c6:
                    if st.button("↓", key=f"down_{idx}", help="아래"):
                        if idx < len(schedule) - 1:
                            schedule[idx], schedule[idx+1] = schedule[idx+1], schedule[idx]
                            auto_save(); st.rerun()

                # 값 변경 감지 → 즉시 반영/저장
                changed = False
                ns, ne = _fmt_time(new_start), _fmt_time(new_end)

                if ns != item["start"]:
                    item["start"] = ns; changed = True
                if ne != item["end"]:
                    item["end"] = ne; changed = True
                if new_type != item.get("type"):
                    item["type"] = new_type; changed = True
                if new_title != item.get("title"):
                    item["title"] = new_title; changed = True

                if changed:
                    st.session_state.schedules[schedule_date_key][idx] = item
                    auto_save()

                # ----- 상세 정보 (콘텐츠/소품/메모) -----
                with st.expander("상세보기"):
                    performers_info = ""
                    if item.get('content_id'):
                        for date_contents in st.session_state.daily_contents.values():
                            for c in date_contents:
                                if c.get('id') == item['content_id']:
                                    if c.get('performers'):
                                        performers_info = " (" + ", ".join(c['performers']) + ")"
                                    if c.get('reference'):
                                        r1, r2 = st.columns([5, 1])
                                        with r1: st.caption(f"📎{c['reference'][:50]}...")
                                        with r2:
                                            if st.button("▶️", key=f"tv_{idx}"):
                                                vid = get_youtube_id(c['reference'])
                                                if vid: show_youtube_player(vid)
                                    if c.get('final'):
                                        st.text_area("최종 픽스", c['final'], disabled=True, key=f"f_{idx}")
                                    break

                    if item.get('content_id') in st.session_state.content_props:
                        props = st.session_state.content_props[item['content_id']]
                        if props:
                            props_list = []
                            for p in props:
                                emoji = PROP_STATUS_EMOJI.get(p.get('status'))
                                props_list.append(f"{p['name']}{emoji}")
                            st.success("소품: " + ", ".join(props_list))

                    details_val = item.get('details', '')
                    new_details = st.text_area("메모", value=details_val, key=f"memo_{idx}")
                    if new_details != details_val:
                        item['details'] = new_details
                        st.session_state.schedules[schedule_date_key][idx] = item
                        auto_save()

                # 삭제 버튼은 상세 아래 또는 라인 끝으로 빼도 OK
                del_col = st.columns([0.9, 0.1])[1]
                with del_col:
                    if st.button("🗑️", key=f"del_{idx}", help="삭제"):
                        schedule.pop(idx)
                        auto_save(); st.rerun()

        st.divider()
        if schedule:
            st.info(f"📌 전체: {schedule[0]['start']} ~ {schedule[-1]['end']}")

# ========================= 탭4: 업로드 현황 =========================
with tab4:
    st.subheader("📹 영상 업로드 현황")

    all_contents = []
    for dkey, contents in st.session_state.daily_contents.items():
        for content in contents:
            cc = content.copy()
            cc['date'] = dkey
            all_contents.append(cc)

    all_contents.sort(key=lambda x: x['date'], reverse=True)

    if all_contents:
        col1g, col2g, col3g = st.columns(3)
        with col1g:
            filter_status = st.multiselect("상태 필터", UPLOAD_STATUS_OPTIONS, key="filter_upload_status")
        with col2g:
            filter_date_from = st.date_input("시작일", datetime.now() - timedelta(days=30), key="filter_from")
        with col3g:
            filter_date_to = st.date_input("종료일", datetime.now(), key="filter_to")

        filtered = all_contents
        if filter_status:
            filtered = [c for c in filtered if st.session_state.upload_status.get(c['id'], '촬영전') in filter_status]
        filtered = [c for c in filtered if filter_date_from.strftime('%Y-%m-%d') <= c['date'] <= filter_date_to.strftime('%Y-%m-%d')]

        if filtered:
            st.markdown("### 📊 전체 콘텐츠 현황")
            h1, h2, h3, h4, h5, h6 = st.columns([0.8, 2.5, 1.2, 1, 0.7, 0.3])
            with h1: st.caption("**날짜**")
            with h2: st.caption("**제목**")
            with h3: st.caption("**상태**")
            with h4: st.caption("**이동날짜선택**")
            with h5: st.caption("")
            with h6: st.caption("")
        else:
            st.info("필터 조건에 맞는 콘텐츠가 없습니다.")

        for content in filtered:
            k1, k2, k3, k4, k5, k6 = st.columns([0.8, 2.5, 1.2, 1, 0.7, 0.3])

            with k1: st.write(content['date'][5:])
            with k2:
                title = content.get('title', '제목 없음')
                if content.get('performers'):
                    title += f" ({', '.join(content['performers'])})"
                st.write(title)

            with k3:
                current = st.session_state.upload_status.get(content['id'], '촬영전')
                new = st.selectbox("", UPLOAD_STATUS_OPTIONS, index=UPLOAD_STATUS_OPTIONS.index(current),
                                   key=f"status_{content['id']}", label_visibility="collapsed",
                                   format_func=lambda x: f"{UPLOAD_STATUS_EMOJI.get(x,'')} {x}")
                if new != current:
                    st.session_state.upload_status[content['id']] = new
                    auto_save()

            with k4:
                new_date = st.date_input("", datetime.strptime(content['date'], '%Y-%m-%d'),
                                         key=f"move_upload_{content['id']}", label_visibility="collapsed")
            with k5:
                if st.button("이동", key=f"move_btn_{content['id']}"):
                    old = content['date']
                    new_key = new_date.strftime('%Y-%m-%d')
                    if old != new_key:
                        for idx, c in enumerate(st.session_state.daily_contents[old]):
                            if c['id'] == content['id']:
                                moved = st.session_state.daily_contents[old].pop(idx)
                                break
                        if new_key not in st.session_state.daily_contents:
                            st.session_state.daily_contents[new_key] = []
                        st.session_state.daily_contents[new_key].append(moved)
                        auto_save(); st.toast(f"✅ {new_key}로 이동", icon='✅'); st.rerun()

            with k6:
                if st.button("🗑️", key=f"del_upload_{content['id']}", help="삭제"):
                    for idx, c in enumerate(st.session_state.daily_contents[content['date']]):
                        if c['id'] == content['id']:
                            st.session_state.daily_contents[content['date']].pop(idx)
                            if not st.session_state.daily_contents[content['date']]:
                                del st.session_state.daily_contents[content['date']]
                            break
                    if content['id'] in st.session_state.upload_status:
                        del st.session_state.upload_status[content['id']]
                    if content['id'] in st.session_state.content_props:
                        del st.session_state.content_props[content['id']]
                    auto_save(); st.rerun()

        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("전체", f"{len(filtered)}개")
        with m2: st.metric("촬영완료", f"{len([c for c in filtered if st.session_state.upload_status.get(c['id'],'촬영전')=='촬영완료'])}개")
        with m3: st.metric("편집완료", f"{len([c for c in filtered if st.session_state.upload_status.get(c['id'],'촬영전')=='편집완료'])}개")
        with m4: st.metric("업로드완료", f"{len([c for c in filtered if st.session_state.upload_status.get(c['id'],'촬영전')=='업로드완료'])}개")
    else:
        st.info("아직 등록된 콘텐츠가 없습니다.")
