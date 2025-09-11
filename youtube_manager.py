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
PROP_STATUS_OPTIONS = ["예정", "주문완료", "수령완료"]
PROP_STATUS_EMOJI    = {"예정":"🔴", "주문완료":"🟡", "수령완료":"🟢"}
PROP_STATUS_LEGEND   = "🔴 빨강=예정 · 🟡 노랑=주문완료 · 🟢 초록=수령완료"
UPLOAD_STATUS_OPTIONS = ["촬영전", "촬영완료", "편집완료", "업로드완료"]
UPLOAD_STATUS_EMOJI   = {"촬영전":"🔵","촬영완료":"🟡","편집완료":"🟠","업로드완료":"🟢"}

# ------------------------- 유틸 함수 -------------------------
def get_youtube_id(url: str | None):
    if not url: return None
    m = re.search(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/))([A-Za-z0-9_\-]{6,})', url)
    return m.group(1).split('?')[0].split('&')[0] if m else None

def show_youtube_player(video_id):
    if video_id:
        st.markdown(
            f'<iframe width="100%" height="315" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>',
            unsafe_allow_html=True
        )

def nearest_content_date_from_today():
    contents = st.session_state.get('daily_contents', {})
    dates = [datetime.strptime(k, '%Y-%m-%d').date() for k, v in contents.items() if v]
    if not dates: return datetime.now().date()
    dates = sorted(dates)
    today = datetime.now().date()
    future_dates = [d for d in dates if d >= today]
    return future_dates[0] if future_dates else dates[-1]

def _to_time(s: str) -> time: return datetime.strptime(s, "%H:%M").time()
def _fmt_time(t: time) -> str: return t.strftime("%H:%M")

# ------------------------- Gist 저장/불러오기 -------------------------
try:
    GIST_ID = st.secrets["gist_id"]
    GITHUB_TOKEN = st.secrets["github_token"]
except Exception:
    GIST_ID = "YOUR_GIST_ID_HERE"
    GITHUB_TOKEN = "ghp_YOUR_GITHUB_TOKEN_HERE"

SESSION = requests.Session()
SESSION.headers.update({"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"})

def _gist_ready():
    return bool(GIST_ID and "YOUR_GIST_ID_HERE" not in GIST_ID and GITHUB_TOKEN and "YOUR_GITHUB_TOKEN_HERE" not in GITHUB_TOKEN)

def save_to_gist(data):
    if not _gist_ready(): return False
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        payload = {"files": {"youtube_data.json": {"content": json.dumps(data, ensure_ascii=False, indent=2)}}}
        r = SESSION.patch(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception:
        return False

def load_from_gist():
    if not _gist_ready(): return None
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        r = SESSION.get(url, timeout=10)
        if r.status_code == 200:
            files = r.json().get("files", {})
            content = files.get("youtube_data.json", {}).get("content")
            if content:
                return json.loads(content)
    except Exception:
        return None
    return None

# ------------------------- 비밀번호 체크 -------------------------
def check_password():
    try: PASSWORD = st.secrets["app_password"]
    except: PASSWORD = "youtube1234"

    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    def password_entered():
        if st.session_state["password"] == PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if not st.session_state.password_correct:
        st.title("🔐 유튜브 콘텐츠 매니저")
        st.text_input("비밀번호를 입력하세요", type="password", on_change=password_entered, key="password")
        if "password" in st.session_state and not st.session_state.password_correct:
            st.error("비밀번호가 틀렸습니다")
        return False
    return True

if not check_password():
    st.stop()

# ------------------------- 세션 초기화/저장/새로고침 -------------------------
def auto_save():
    data = {
        'contents': st.session_state.daily_contents,
        'props': st.session_state.content_props,
        'schedules': st.session_state.schedules,
        'upload_status': st.session_state.upload_status,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    if save_to_gist(data):
        st.session_state.last_save_time = datetime.now().strftime('%H:%M:%S')

if 'initialized' not in st.session_state:
    data = load_from_gist()
    st.session_state.daily_contents = data.get('contents', {}) if data else {}
    st.session_state.content_props  = data.get('props', {}) if data else {}
    st.session_state.schedules      = data.get('schedules', {}) if data else {}
    st.session_state.upload_status  = data.get('upload_status', {}) if data else {}
    st.session_state.initialized = True
    st.toast("☁️ 데이터를 불러왔습니다", icon='✅')

def refresh_data():
    st.session_state.initialized = False
    st.rerun()

# ------------------------- 상단 바 -------------------------
col1, col2, col3, col4 = st.columns([5, 1, 1, 1.5])
with col1: st.title("🎬 유튜브 콘텐츠 매니저")
with col2:
    if st.button("🔄", help="데이터 새로고침"): refresh_data()
with col3:
    if st.button("💾", help="수동 저장"):
        auto_save()
        st.toast(f"✅ 수동 저장 완료! ({st.session_state.get('last_save_time', 'N/A')})")
with col4:
    st.caption(f"Last auto-save: {st.session_state.get('last_save_time', 'N/A')}")

# ------------------------- 탭 -------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📝 콘텐츠 기획", "🛍️ 소품 구매", "⏰ 타임테이블", "📹 영상 업로드 현황"])

# ========================= 탭1: 콘텐츠 기획 =========================
with tab1:
    st.subheader("📝 콘텐츠 기획")

    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        if 'selected_date' not in st.session_state:
            st.session_state.selected_date = nearest_content_date_from_today()

        def update_selected_date():
            st.session_state.selected_date = st.session_state.content_date_widget

        selected_date = st.date_input("날짜 선택", value=st.session_state.selected_date, key="content_date_widget", on_change=update_selected_date)
        date_key = selected_date.strftime('%Y-%m-%d')
    with col2:
        num_contents = st.number_input("개수", min_value=1, max_value=10, value=3)
    with col3:
        if st.button("✨ 양식 생성", type="primary"):
            if date_key not in st.session_state.daily_contents: st.session_state.daily_contents[date_key] = []
            current_count = len(st.session_state.daily_contents[date_key])
            for i in range(num_contents):
                content_id = f"{date_key}_{current_count + i}"
                st.session_state.daily_contents[date_key].append({'id': content_id, 'title': '', 'draft': '', 'feedback': '', 'revision': '', 'final': '', 'reference': '', 'performers': []})
                st.session_state.upload_status[content_id] = '촬영전'
            auto_save()
            st.rerun()

    st.divider()

    if date_key in st.session_state.daily_contents and st.session_state.daily_contents[date_key]:
        st.subheader(f"📋 {selected_date.strftime('%m월 %d일')} 콘텐츠")
        contents = st.session_state.daily_contents[date_key]
        for idx, content in enumerate(contents):
            content_id = content.get('id', f"{date_key}_{idx}")
            upload_status = st.session_state.upload_status.get(content_id, "촬영전")
            status_emoji = UPLOAD_STATUS_EMOJI.get(upload_status, "❓")
            expander_title = f"{status_emoji} #{idx+1}. {content.get('title', '제목 없음')}"
            
            with st.expander(expander_title, expanded=False):
                content['title'] = st.text_input("제목", value=content.get('title', ''), key=f"title_{content_id}", on_change=auto_save)
                performers = ["전부", "다혜", "수빈", "예람", "보조"]
                content['performers'] = st.multiselect("출연자", performers, default=content.get('performers', []), key=f"performers_{content_id}", on_change=auto_save)
                content['reference'] = st.text_input("참고 링크", value=content.get('reference', ''), key=f"ref_{content_id}", on_change=auto_save)
                if 'youtube' in content.get('reference', ''): show_youtube_player(get_youtube_id(content['reference']))

                plan_tabs = st.tabs(["📝 초안", "🗣️ 피드백", "🤔 추가의견", "✅ 최종"])
                with plan_tabs[0]: content['draft'] = st.text_area("초안", value=content.get('draft', ''), height=150, key=f"draft_{content_id}", on_change=auto_save)
                with plan_tabs[1]: content['feedback'] = st.text_area("피드백", value=content.get('feedback', ''), height=150, key=f"feedback_{content_id}", on_change=auto_save)
                with plan_tabs[2]: content['revision'] = st.text_area("추가의견", value=content.get('revision', ''), height=150, key=f"revision_{content_id}", on_change=auto_save)
                with plan_tabs[3]: content['final'] = st.text_area("최종", value=content.get('final', ''), height=150, key=f"final_{content_id}", on_change=auto_save)

                filled = sum(1 for f in ('draft','feedback','revision','final') if content.get(f))
                st.progress(min(1.0, max(0.0, filled * 0.25)))

# ========================= 탭2: 소품 구매 =========================
with tab2:
    st.subheader("🛍️ 소품 구매")
    st.caption(PROP_STATUS_LEGEND)
    prop_date = st.date_input("날짜", nearest_content_date_from_today(), key="prop_date")
    prop_date_key = prop_date.strftime('%Y-%m-%d')

    if prop_date_key in st.session_state.daily_contents and st.session_state.daily_contents[prop_date_key]:
        for idx, content in enumerate(st.session_state.daily_contents[prop_date_key]):
            content_id = content.get('id', f"{prop_date_key}_{idx}")
            if content_id not in st.session_state.content_props: st.session_state.content_props[content_id] = []
            
            props = st.session_state.content_props[content_id]
            expander_title = f"#{idx+1}. {content.get('title', '제목 없음')} (소품 {len(props)}개)"
            
            with st.expander(expander_title):
                st.markdown("**➕ 소품 추가**")
                c1,c2,c3,c4,c5 = st.columns([3,2,1,2,1])
                with c1: new_name = st.text_input("소품명", key=f"new_n_{content_id}")
                with c2: new_vendor = st.text_input("구매처", key=f"new_v_{content_id}")
                with c3: new_quantity = st.number_input("개수", 1, key=f"new_q_{content_id}")
                with c4: new_status = st.selectbox("상태", PROP_STATUS_OPTIONS, key=f"new_s_{content_id}")
                with c5:
                    st.write("")
                    if st.button("추가", key=f"add_{content_id}"):
                        if new_name:
                            props.append({'name': new_name, 'vendor': new_vendor, 'quantity': new_quantity, 'status': new_status})
                            auto_save()
                            st.rerun()

                if props:
                    st.divider()
                    for p_idx, p in enumerate(props):
                        c1,c2,c3,c4,c5 = st.columns([3,2,1,2,1])
                        with c1: p['name'] = st.text_input("소품명", p['name'], key=f"pn_{content_id}_{p_idx}", label_visibility="collapsed", on_change=auto_save)
                        with c2: p['vendor'] = st.text_input("구매처", p.get('vendor', ''), key=f"pv_{content_id}_{p_idx}", label_visibility="collapsed", on_change=auto_save)
                        with c3: 
                            # 안전한 정수 변환
                            safe_qty = 1
                            try:
                                safe_qty = int(p.get('quantity', 1))
                            except (ValueError, TypeError):
                                safe_qty = 1
                            p['quantity'] = st.number_input("개수", value=safe_qty, min_value=1, step=1, key=f"pq_{content_id}_{p_idx}", label_visibility="collapsed", on_change=auto_save)
                        with c4:
                            current_status = p.get('status', PROP_STATUS_OPTIONS[0])
                            if current_status not in PROP_STATUS_OPTIONS: current_status = PROP_STATUS_OPTIONS[0]
                            p['status'] = st.selectbox("상태", PROP_STATUS_OPTIONS, index=PROP_STATUS_OPTIONS.index(current_status), key=f"ps_{content_id}_{p_idx}", label_visibility="collapsed", on_change=auto_save)
                        with c5:
                            if st.button("🗑️", key=f"del_p_{content_id}_{p_idx}"):
                                props.pop(p_idx)
                                auto_save()
                                st.rerun()

# ========================= 탭3: 타임테이블 =========================
with tab3:
    st.subheader("⏰ 타임테이블")
    schedule_date = st.date_input("날짜", datetime.now().date(), key="schedule_date")
    schedule_date_key = schedule_date.strftime('%Y-%m-%d')

    if schedule_date_key not in st.session_state.schedules: st.session_state.schedules[schedule_date_key] = []
    schedule = st.session_state.schedules[schedule_date_key]

    with st.expander("➕ 일정 추가"):
        c1,c2,c3,c4,c5 = st.columns([1,1,1.5,3,1])
        with c1: new_start = st.time_input("시작", time(12,0), key=f"new_s_{schedule_date_key}")
        with c2: new_end = st.time_input("종료", time(13,0), key=f"new_e_{schedule_date_key}")
        with c3: new_type = st.selectbox("유형", ["🎬촬영", "🍽️식사", "☕휴식", "📝회의", "🚗이동", "🎯기타"], key=f"new_t_{schedule_date_key}")
        with c4: new_title = st.text_input("제목", key=f"new_title_{schedule_date_key}")
        with c5:
            st.write("")
            if st.button("추가", key=f"add_sched_{schedule_date_key}"):
                if new_title:
                    schedule.append({'start': _fmt_time(new_start), 'end': _fmt_time(new_end), 'type': new_type, 'title': new_title, 'details': ''})
                    schedule.sort(key=lambda x: x['start'])
                    auto_save()
                    st.rerun()
    st.divider()

    if schedule:
        for idx, item in enumerate(schedule):
            st.markdown("---")
            c1,c2,c3,c4,c5 = st.columns([1,1,1.5,3,1])
            key_suffix = f"_{idx}_{schedule_date_key}"
            with c1: item['start'] = _fmt_time(st.time_input("시작", _to_time(item['start']), key=f"s_start{key_suffix}", label_visibility="collapsed", on_change=auto_save))
            with c2: item['end'] = _fmt_time(st.time_input("종료", _to_time(item['end']), key=f"s_end{key_suffix}", label_visibility="collapsed", on_change=auto_save))
            with c3:
                types_list = ["🎬촬영", "🍽️식사", "☕휴식", "📝회의", "🚗이동", "🎯기타"]
                current_type = item.get('type', types_list[0])
                if current_type not in types_list: current_type = types_list[0]
                item['type'] = st.selectbox("유형", types_list, index=types_list.index(current_type), key=f"s_type{key_suffix}", label_visibility="collapsed", on_change=auto_save)
            with c4: item['title'] = st.text_input("제목", item['title'], key=f"s_title{key_suffix}", label_visibility="collapsed", on_change=auto_save)
            with c5:
                st.write("")
                if st.button("🗑️", key=f"del_sched{key_suffix}"):
                    schedule.pop(idx)
                    auto_save()
                    st.rerun()
            item['details'] = st.text_area("세부사항", item.get('details', ''), key=f"s_details{key_suffix}", label_visibility="collapsed", on_change=auto_save)

# ========================= 탭4: 업로드 현황 =========================
with tab4:
    st.subheader("📹 영상 업로드 현황")

    all_contents = []
    for dkey, contents in st.session_state.daily_contents.items():
        for content in contents:
            if content:
                c = content.copy()
                c['date'] = dkey
                all_contents.append(c)
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
        filtered = [c for c in filtered if filter_date_from <= datetime.strptime(c['date'], '%Y-%m-%d').date() <= filter_date_to]

        if not filtered:
            st.info("필터 조건에 맞는 콘텐츠가 없습니다.")
        
        for content in filtered:
            content_id = content['id']
            st.markdown("---")
            k1, k2, k3, k4, k5, k6 = st.columns([0.8, 2.5, 1.2, 1, 0.7, 0.3])

            with k1: st.write(content['date'][5:])
            with k2:
                title = f"{content.get('title', '제목 없음')} ({', '.join(content.get('performers',[]))})"
                st.write(title)
            with k3:
                current = st.session_state.upload_status.get(content_id, '촬영전')
                def on_status_change():
                    st.session_state.upload_status[content_id] = st.session_state[f"status_{content_id}"]
                    auto_save()
                st.selectbox("상태", UPLOAD_STATUS_OPTIONS, index=UPLOAD_STATUS_OPTIONS.index(current), key=f"status_{content_id}", label_visibility="collapsed", on_change=on_status_change)
            with k4:
                st.date_input("이동 날짜", datetime.strptime(content['date'], '%Y-%m-%d'), key=f"move_date_{content_id}", label_visibility="collapsed")
            with k5:
                if st.button("이동", key=f"move_btn_{content_id}"):
                    old_key = content['date']
                    new_date = st.session_state[f"move_date_{content_id}"]
                    new_key = new_date.strftime('%Y-%m-%d')
                    if old_key != new_key:
                        moved_content = next((c for c in st.session_state.daily_contents[old_key] if c['id'] == content_id), None)
                        if moved_content:
                            st.session_state.daily_contents[old_key].remove(moved_content)
                            if not st.session_state.daily_contents[old_key]: del st.session_state.daily_contents[old_key]
                            if new_key not in st.session_state.daily_contents: st.session_state.daily_contents[new_key] = []
                            st.session_state.daily_contents[new_key].append(moved_content)
                            auto_save()
                            st.toast(f"✅ {new_key}로 이동", icon='✅'); st.rerun()
            with k6:
                if st.button("🗑️", key=f"del_upload_{content_id}", help="삭제"):
                    st.session_state.daily_contents[content['date']] = [c for c in st.session_state.daily_contents[content['date']] if c['id'] != content_id]
                    if not st.session_state.daily_contents[content['date']]: del st.session_state.daily_contents[content['date']]
                    if content_id in st.session_state.upload_status: del st.session_state.upload_status[content_id]
                    if content_id in st.session_state.content_props: del st.session_state.content_props[content_id]
                    auto_save(); st.rerun()

        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        statuses = [st.session_state.upload_status.get(c['id'],'촬영전') for c in filtered]
        with m1: st.metric("필터된 콘텐츠", f"{len(filtered)}개")
        with m2: st.metric("촬영완료", f"{statuses.count('촬영완료')}개")
        with m3: st.metric("편집완료", f"{statuses.count('편집완료')}개")
        with m4: st.metric("업로드완료", f"{statuses.count('업로드완료')}개")
    else:
        st.info("아직 등록된 콘텐츠가 없습니다.")
