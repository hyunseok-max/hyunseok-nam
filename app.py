import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import email.utils
from datetime import datetime, timezone
import json
import os
import numpy as np

# ==========================================
# 1. 100억 전황판 VIP UI 세팅
# ==========================================
st.set_page_config(page_title="남현석과 함께 100억 만들기", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 🔒 2. 통제실 보안 구역
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color: #F59E0B;'>🔒 100억 작전 통제실</h2>", unsafe_allow_html=True)
        pwd = st.text_input("마스터 암호 입력", type="password")
        if st.button("진입 (ENTER)", use_container_width=True):
            if pwd == "100억":  
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("🚨 암호가 일치하지 않습니다. 접근을 차단합니다.")
    st.stop() 

# ==========================================
# 3. 프리미엄 CSS (무한 전광판 & 대시보드)
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0B0E14; color: #E2E8F0; font-family: 'Pretendard', sans-serif; }
    
    /* 완벽 이음새 무한 전광판 */
    .ticker-wrap { width: 100%; overflow: hidden; background-color: #151A23; border-bottom: 2px solid #252B3B; padding: 10px 0; margin-bottom: 20px; display: flex; }
    .ticker-move { display: flex; white-space: nowrap; animation: ticker 35s linear infinite; }
    .ticker-move:hover { animation-play-state: paused; }
    @keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
    .ticker-item { padding: 0 40px; font-size: 15px; font-weight: 700; color: #FFFFFF; flex-shrink: 0; }
    .ticker-up { color: #F87171; } .ticker-down { color: #60A5FA; } .ticker-name { color: #94A3B8; font-size: 13px; margin-right: 8px; }
    
    /* 100억 대시보드 카드 */
    .dashboard-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
    .dash-card { background: linear-gradient(145deg, #1A1F2B 0%, #11151D 100%); padding: 20px; border-radius: 12px; border: 1px solid #2D3748; box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-align: center; }
    .dash-title { color: #94A3B8; font-size: 14px; font-weight: bold; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
    .dash-value { font-size: 28px; font-weight: 900; color: #FFFFFF; }
    .dash-sub { font-size: 12px; color: #64748B; margin-top: 5px; }
    
    .news-box { background-color: #1A1F2B; padding: 15px; margin-bottom: 12px; border-radius: 8px; border-left: 4px solid #F59E0B; transition: 0.2s; }
    .news-box:hover { background-color: #252B3B; transform: translateX(5px); }
    .news-title { font-size: 14px; font-weight: bold; color: #F1F5F9; line-height: 1.4; margin-bottom: 8px; }
    .news-meta { font-size: 11px; color: #94A3B8; display: flex; justify-content: space-between; }
    a { text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. 실시간 무빙 티커 (1분 초정밀)
# ==========================================
@st.cache_data(ttl=60)
def get_ticker_data():
    ticker_symbols = {
        '나스닥': '^IXIC', 'S&P 500': '^GSPC', '필라델피아 반도체': '^SOX', 
        'VIX 공포지수': '^VIX', '달러 환율': 'KRW=X', '코스피': '^KS11', '비트코인': 'BTC-USD', '미 10년물 국채': '^TNX'
    }
    try:
        data = yf.download(list(ticker_symbols.values()), period="5d", progress=False)['Close'].ffill().dropna()
        items_html = ""
        for name, symbol in ticker_symbols.items():
            last, prev = float(data[symbol].iloc[-1]), float(data[symbol].iloc[-2])
            diff, pct = last - prev, ((last - prev) / prev) * 100
            color, sign = ("ticker-up", "+") if diff > 0 else ("ticker-down", "")
            
            if name in ['달러 환율', '코스피', 'S&P 500', '나스닥']: val_str = f"{last:,.2f}"
            elif name == '비트코인': val_str = f"${last:,.0f}"
            else: val_str = f"{last:,.2f}"
            items_html += f"<div class='ticker-item'><span class='ticker-name'>{name}</span> {val_str} <span class='{color}'>({sign}{pct:.2f}%)</span></div>"
        
        return f"<div class='ticker-wrap'><div class='ticker-move'>{items_html}{items_html}</div></div>"
    except: return "<div class='ticker-wrap'><div class='ticker-move'>실시간 지수 연결 중...</div></div>"

st.markdown(get_ticker_data(), unsafe_allow_html=True)

# 메인 타이틀
st.markdown("<h1 style='text-align: center; color: #F59E0B; font-weight: 900; margin-bottom: 0;'>👑 남현석과 함께 100억 만들기</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94A3B8; margin-bottom: 30px;'>WallStreet v11.0 Ultimate | 헤지펀드 VCP 극압축 필터 & PCE 매크로 방어벽 가동 중</p>", unsafe_allow_html=True)

# ==========================================
# 5. 데이터 저장소 및 뉴스 엔진
# ==========================================
HISTORY_FILE = "quant_history.json"
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return None
def save_history(top3_data):
    save_data = [{"티커": item['티커'], "추천가": item['현재가'], "시간": datetime.now().strftime("%Y-%m-%d %H:%M")} for item in top3_data]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump(save_data, f, ensure_ascii=False, indent=4)

@st.cache_data(ttl=60)
def get_live_clickable_news(keyword):
    try:
        url = f"https://news.google.com/rss/search?q={keyword}+when:1d&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        root = ET.fromstring(res.content)
        news_list = []
        now = datetime.now(timezone.utc)
        for item in root.findall('.//item')[:8]:
            title, link, pubDate_str = item.find('title').text, item.find('link').text, item.find('pubDate').text
            source = "글로벌 매체"
            if " - " in title: title, source = title.rsplit(" - ", 1)
            try:
                pub_tuple = email.utils.parsedate_tz(pubDate_str)
                pub_time = datetime.fromtimestamp(email.utils.mktime_tz(pub_tuple), timezone.utc)
                diff_sec = (now - pub_time).total_seconds()
                time_str = f"{int(diff_sec//60)}분 전" if diff_sec < 3600 else f"{int(diff_sec//3600)}시간 전"
            except: time_str = "방금 전"
            news_list.append({"title": title, "link": link, "source": source, "time": time_str})
        return news_list
    except: return []

# ==========================================
# 6. 헤지펀드 AI 퀀트 엔진 (PCE 방어 & 극압축 VCP)
# ==========================================
BULL_STOCKS = [
    "QLD", "SSO", "USD", "NVDL",
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
    "AVGO", "TSM", "AMD", "QCOM", "ASML", "AMAT", "MU", "LRCX", "INTC", "ARM", "SMCI", "SIMO", "WDC", "TXN", "NXPI",
    "CRM", "ADBE", "NFLX", "CSCO", "ORCL", "NOW", "INTU", "UBER", "SNOW", "PLTR", "CRWD", "PANW", "FTNT", "DDOG", "NET", "MDB", "TEAM", "WDAY",
    "V", "MA", "JPM", "BAC", "WFC", "GS", "MS", "AXP", "PYPL", "SQ", "COIN", "MARA", "RIOT", "MSTR", "HOOD", "SOFI", "AFRM", "UPST"
]
BEAR_ETFS = ["SH", "PSQ", "QID"]

def analyze_hedgefund_signals():
    data = yf.download(BULL_STOCKS + BEAR_ETFS + ['^GSPC', '^VIX', 'TLT'], period="2y", group_by='ticker', progress=False)
    vcp_swing, bear_defense, momentum = [], [], []
    
    # 🛡️ PCE 매크로 동적 방어벽 계산
    try:
        vix_df, tlt_df = data['^VIX'].dropna(), data['TLT'].dropna()
        current_vix = vix_df['Close'].iloc[-1]
        tlt_trend = tlt_df['Close'].iloc[-1] < tlt_df['Close'].iloc[-20] # 한달 전보다 장기채 하락(금리상승/인플레 우려)
        # 매크로가 불안하면 VIX 허용치를 25에서 20으로 확 낮춰서 극도로 보수적 스탠스 취함
        vix_limit = 20.0 if tlt_trend else 25.0 
        spy_df = data['^GSPC'].dropna()
        spy_return_6m = (spy_df['Close'].iloc[-1] - spy_df['Close'].iloc[-120]) / spy_df['Close'].iloc[-120]
    except:
        current_vix, vix_limit, spy_return_6m = 20.0, 25.0, 0.05

    for ticker in BULL_STOCKS + BEAR_ETFS:
        try:
            df = data[ticker].dropna()
            if len(df) < 255: continue
            
            # 이평선 및 기본 지표
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA50'] = df['Close'].rolling(window=50).mean()
            df['MA150'] = df['Close'].rolling(window=150).mean()
            df['MA200'] = df['Close'].rolling(window=200).mean()
            df['High52'] = df['High'].rolling(window=250).max()
            df['Low52'] = df['Low'].rolling(window=250).min()
            
            # ATR (스마트 손절)
            tr1 = df['High'] - df['Low']
            tr2 = np.abs(df['High'] - df['Close'].shift())
            tr3 = np.abs(df['Low'] - df['Close'].shift())
            df['ATR'] = np.max(pd.concat([tr1, tr2, tr3], axis=1), axis=1).rolling(14).mean()
            
            # 👑 헤지펀드 극압축 VCP 지표 (BB Percentile)
            df['BB_std'] = df['Close'].rolling(window=20).std()
            df['BB_Width'] = (df['BB_std'] * 4) / df['MA20']
            bb_min_120 = df['BB_Width'].rolling(120).min()
            bb_max_120 = df['BB_Width'].rolling(120).max()
            df['BB_Percentile'] = (df['BB_Width'] - bb_min_120) / (bb_max_120 - bb_min_120) # 0에 가까울수록 과거 6개월 내 가장 압축됨
            
            df['Vol_50MA'] = df['Volume'].rolling(window=50).mean()
            
            last, prev = df.iloc[-1], df.iloc[-2]
            change_pct = ((last['Close'] - prev['Close']) / prev['Close']) * 100
            change_str = f"🔥 +{change_pct:.2f}%" if change_pct > 0 else f"❄️ {change_pct:.2f}%"
            atr_stop_loss = last['Close'] - (last['ATR'] * 2)
            
            # RS 주도력 평가
            stock_return_6m = (last['Close'] - df['Close'].iloc[-120]) / df['Close'].iloc[-120]
            rs_score = (stock_return_6m / spy_return_6m) * 100 if spy_return_6m > 0 else 100
            rs_rating = "👑 S급 대장주" if rs_score > 200 else "A급 주도주" if rs_score > 100 else "B급"
            
            base_info = {
                "티커": ticker, 
                "현재가": float(last['Close']), 
                "손절가(ATR)": float(atr_stop_loss),
                "당일등락": change_str, 
                "시장 주도력": rs_rating,
                "압축률": f"상위 {int((1 - last['BB_Percentile'])*100)}%", # 100%에 가까울수록 좋음
                "원가": float(last['Close'])
            }
            
            if ticker in BULL_STOCKS:
                # 1. 미너비니 완벽 우상향 템플릿 (UPST 등 완벽 차단)
                is_uptrend = (last['Close'] > last['MA150'] and last['MA150'] > last['MA200'] and 
                              last['MA200'] > df['MA200'].iloc[-20] and last['Close'] > last['MA50'] and
                              last['Close'] >= last['Low52'] * 1.30 and last['Close'] >= last['High52'] * 0.75)
                
                # 2. 헤지펀드 변형 VCP (극압축 + 거래량 마름)
                is_vcp_extreme = last['BB_Percentile'] < 0.25 # 최근 6개월 내 밴드폭 하위 25% 이내로 질식 상태
                is_vol_dry = df['Volume'].iloc[-3:].mean() < (last['Vol_50MA'] * 0.8) # 3일 평균 거래량이 50일 평균의 80% 미만
                is_near_ma20 = (last['MA20'] * 0.98 <= last['Close'] <= last['MA20'] * 1.05)
                
                # 매크로 방어벽(vix_limit) 작동 하에서만 진입
                if (current_vix < vix_limit) and is_uptrend and is_near_ma20 and is_vcp_extreme and is_vol_dry and (change_pct > 0):
                    vcp_swing.append({**base_info, "타점": "👑 극압축 VCP 눌림목"})
                    
                # 포켓 피봇 (Pocket Pivot) 돌파 매매
                is_pocket_pivot = (last['Volume'] > df['Volume'].rolling(10).max().iloc[-2]) and (change_pct >= 2.0)
                if is_uptrend and is_pocket_pivot and (last['Close'] > df['High'].rolling(20).max().iloc[-2]):
                    momentum.append({**base_info, "타점": "🚀 포켓피봇 대량 돌파"})

            if ticker in BEAR_ETFS:
                if (last['Close'] > last['MA20']) and (last['MA20'] > prev['MA20']) and (change_pct > 1.0):
                    bear_defense.append({**base_info, "타점": "🚨 하락장 방어 돌파"})
                
        except Exception as e: continue
            
    return vcp_swing, bear_defense, momentum, current_vix, vix_limit

# ==========================================
# 7. 메인 렌더링 및 프리미엄 UI
# ==========================================
col_main, col_side = st.columns([7, 3])

if 'scanned' not in st.session_state:
    st.session_state.scanned = False
    st.session_state.vcp_swing = []

with col_main:
    if st.button("🚀 100억 엔진 가동 (헤지펀드 알고리즘 & PCE 매크로 스캔)", use_container_width=True):
        with st.spinner("월가 스마트머니 자금 추적 및 극압축 VCP 맵핑 중... (약 20초 소요)"):
            vcp_swing, bear_defense, momentum, current_vix, vix_limit = analyze_hedgefund_signals()
            st.session_state.vcp_swing = vcp_swing
            st.session_state.scanned = True
            
            if vcp_swing: save_history(pd.DataFrame(vcp_swing).sort_values("원가", ascending=False).head(3).to_dict('records'))

            # 100억 대시보드 렌더링
            safe_status = "🟢 안전 (공격 베팅)" if current_vix < vix_limit else "🔴 위험 (현금 관망)"
            st.markdown(f"""
            <div class='dashboard-grid'>
                <div class='dash-card'>
                    <div class='dash-title'>👑 극압축 VCP 스윙</div>
                    <div class='dash-value' style='color:#F59E0B;'>{len(vcp_swing)}건</div>
                    <div class='dash-sub'>세력 멱살잡이 타점</div>
                </div>
                <div class='dash-card'>
                    <div class='dash-title'>🚀 포켓피봇 돌파</div>
                    <div class='dash-value' style='color:#10B981;'>{len(momentum)}건</div>
                    <div class='dash-sub'>기관 대량 매수 포착</div>
                </div>
                <div class='dash-card'>
                    <div class='dash-title'>🚨 인버스 (하락 방어)</div>
                    <div class='dash-value' style='color:#EF4444;'>{len(bear_defense)}건</div>
                    <div class='dash-sub'>시장 붕괴 헷징 타점</div>
                </div>
                <div class='dash-card'>
                    <div class='dash-title'>🛡️ PCE 매크로 통제실</div>
                    <div class='dash-value' style='color:#3B82F6;'>{safe_status}</div>
                    <div class='dash-sub'>현재 VIX: {current_vix:.2f} / 허용치: {vix_limit}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            tab1, tab2, tab3 = st.tabs(["👑 1순위: 극압축 VCP (100억 타점)", "🚀 2순위: 포켓 피봇 돌파", "🚨 3순위: 인버스 방어"])
            
            def display_premium_data(data, msg):
                if data:
                    df = pd.DataFrame(data).drop(columns=['원가'])
                    # 달러 표시 포맷팅
                    df['현재가'] = df['현재가'].apply(lambda x: f"${x:,.2f}")
                    df['손절가(ATR)'] = df['손절가(ATR)'].apply(lambda x: f"${x:,.2f}")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else: st.info(msg)

            with tab1: display_premium_data(vcp_swing, "현재 헤지펀드 필터(VCP 압축+거래량 마름)를 완벽히 통과한 주도주가 없습니다. (100억 군자금 보존 요망)")
            with tab2: display_premium_data(momentum, "포켓 피봇(대량 거래 돌파) 종목이 없습니다.")
            with tab3: display_premium_data(bear_defense, "현재 인버스 돌파 타점이 없습니다.")

# ==========================================
# 8. 우측 사이드바 (과거 수익률 검증 & 뉴스)
# ==========================================
with col_side:
    st.markdown("### 🕵️‍♂️ 직전 100억 타점 검증")
    past_history = load_history()
    
    if past_history:
        st.caption(f"기록 시간: {past_history[0]['시간']}")
        for item in past_history:
            ticker, old_price = item['티커'], item['추천가']
            try:
                curr_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
                profit_pct = ((curr_price - old_price) / old_price) * 100
                color, arrow = ("#EF4444", "🔥") if profit_pct > 0 else ("#3B82F6", "❄️")
                bg_class = "history-card-up" if profit_pct > 0 else "history-card-down"
                
                st.markdown(f"""
                <div class='{bg_class}'>
                    <div><div style='font-weight:bold; font-size:16px;'>{ticker}</div>
                    <div style='font-size:11px; color:#94A3B8;'>${old_price:,.2f} ➔ ${curr_price:,.2f}</div></div>
                    <div style='font-size:18px; font-weight:bold; color:{color};'>{arrow} {profit_pct:+.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
            except: pass
    else: st.info("과거 추천 기록이 없습니다.")

    st.markdown("<br>", unsafe_allow_html=True)
    news_tab1, news_tab2 = st.tabs(["🌐 100억 거시경제", "🚨 주도주 속보"])
    def render_news(keyword):
        for n in get_live_clickable_news(keyword):
            st.markdown(f"<a href='{n['link']}' target='_blank'><div class='news-box'><div class='news-title'>⚡ {n['title']}</div><div class='news-meta'><span>{n['source']}</span><span style='color:#F59E0B;'>{n['time']}</span></div></div></a>", unsafe_allow_html=True)

    with news_tab1: render_news("미국 PCE OR 금리인하 OR 연준")
    with news_tab2: render_news("엔비디아 OR 나스닥 특징주")
