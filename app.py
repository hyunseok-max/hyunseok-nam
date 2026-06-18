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
# 1. 터미널 UI 및 다크모드 세팅
# ==========================================
st.set_page_config(page_title="남현석의 월가 퀀트 터미널", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🔒 2. 통제실 보안 암호 시스템
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color: #F59E0B;'>🔒 통제실 보안 구역</h2>", unsafe_allow_html=True)
        pwd = st.text_input("암호 입력", type="password")
        if st.button("진입 (ENTER)", use_container_width=True):
            if pwd == "100억":  
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("🚨 암호가 일치하지 않습니다. 접근을 차단합니다.")
    st.stop() 

# ==========================================
# 3. CSS 스타일링
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0F111A; color: #FFFFFF; font-family: 'Pretendard', sans-serif; }
    .macro-container { display: flex; gap: 15px; margin-bottom: 20px; }
    .macro-box { background-color: #1A1D27; padding: 15px; border-radius: 10px; flex: 1; border-top: 3px solid #3B82F6; }
    .macro-title { font-size: 13px; color: #8A94A6; font-weight: bold; margin-bottom: 5px; }
    .macro-value { font-size: 20px; font-weight: bold; color: #FFFFFF; }
    .metric-box { background-color: #1A1D27; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #2D3243; }
    .metric-title { color: #8A94A6; font-size: 13px; margin-bottom: 5px; font-weight: bold; }
    .metric-value { font-size: 24px; font-weight: bold; color: #FFFFFF; }
    .history-card-up { background-color: rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
    .history-card-down { background-color: rgba(59, 130, 246, 0.1); border: 1px solid #3B82F6; padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
    .top-pick-card { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #F59E0B; padding: 15px; border-radius: 10px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
    .top-pick-ticker { font-size: 18px; font-weight: bold; color: #F59E0B; }
    .top-pick-price { font-size: 15px; color: #FFFFFF; }
    .news-box { background-color: #1A1D27; padding: 12px 15px; margin-bottom: 10px; border-radius: 8px; border-left: 4px solid #3B82F6; transition: 0.2s; }
    .news-box:hover { background-color: #24283B; transform: translateX(3px); }
    .news-title { font-size: 14px; font-weight: bold; color: #F8FAFC; line-height: 1.4; margin-bottom: 6px; }
    .news-meta { font-size: 11px; color: #8A94A6; display: flex; justify-content: space-between; }
    a { text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

st.title("🎯 남현석의 실전 퀀트 터미널 (WallStreet v10.1)")
st.markdown("단기 스윙(3~7일) 최적화: 완벽한 정배열(우상향) VCP 압축 타점만 포착")

# ==========================================
# 4. 직전 추천 종목 수익률 검증 파일 시스템
# ==========================================
HISTORY_FILE = "quant_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return None

def save_history(top3_data):
    save_data = [{"티커": item['티커'], "추천가": item['원가'], "시간": datetime.now().strftime("%Y-%m-%d %H:%M")} for item in top3_data]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump(save_data, f, ensure_ascii=False, indent=4)

# ==========================================
# 5. 시장 거시경제(매크로) 전광판
# ==========================================
@st.cache_data(ttl=300)
def get_macro_data():
    try:
        tickers = ['^IXIC', '^GSPC', '^VIX', 'TLT']
        data = yf.download(tickers, period="5d", progress=False)['Close'].ffill().dropna()
        macro = {}
        for t in tickers:
            last = float(data[t].iloc[-1])
            prev = float(data[t].iloc[-2])
            pct = ((last - prev) / prev) * 100
            macro[t] = {"price": last, "pct": pct}
        return macro
    except: return None

macro_data = get_macro_data()
if macro_data:
    st.markdown(f"""
    <div class='macro-container'>
        <div class='macro-box' style='border-top-color: #3B82F6;'>
            <div class='macro-title'>📈 나스닥 종합</div>
            <div class='macro-value'>{macro_data['^IXIC']['price']:,.2f} <span style='font-size:14px; color:{"#EF4444" if macro_data['^IXIC']['pct']<0 else "#10B981"};'>({macro_data['^IXIC']['pct']:+.2f}%)</span></div>
        </div>
        <div class='macro-box' style='border-top-color: #F59E0B;'>
            <div class='macro-title'>🚨 VIX 공포지수 (매크로 방어막)</div>
            <div class='macro-value'>{macro_data['^VIX']['price']:.2f} <span style='font-size:14px; color:{"#10B981" if macro_data['^VIX']['pct']<0 else "#EF4444"};'>({macro_data['^VIX']['pct']:+.2f}%)</span></div>
        </div>
        <div class='macro-box' style='border-top-color: #8B5CF6;'>
            <div class='macro-title'>🏦 TLT (거시 금리 방어막)</div>
            <div class='macro-value'>${macro_data['TLT']['price']:.2f} <span style='font-size:14px; color:{"#EF4444" if macro_data['TLT']['pct']<0 else "#10B981"};'>({macro_data['TLT']['pct']:+.2f}%)</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 6. 실시간 뉴스 엔진
# ==========================================
@st.cache_data(ttl=60)
def get_live_clickable_news(keyword):
    try:
        url = f"https://news.google.com/rss/search?q={keyword}+when:1d&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        root = ET.fromstring(res.content)
        news_list = []
        now = datetime.now(timezone.utc)
        for item in root.findall('.//item')[:8]:
            title = item.find('title').text
            link = item.find('link').text
            pubDate_str = item.find('pubDate').text
            source = "글로벌 매체"
            if " - " in title: title, source = title.rsplit(" - ", 1)
            try:
                pub_tuple = email.utils.parsedate_tz(pubDate_str)
                pub_time = datetime.fromtimestamp(email.utils.mktime_tz(pub_tuple), timezone.utc)
                diff_sec = (now - pub_time).total_seconds()
                if diff_sec < 3600: time_str = f"{int(diff_sec//60)}분 전"
                elif diff_sec < 86400: time_str = f"{int(diff_sec//3600)}시간 전"
                else: time_str = "오늘"
            except: time_str = "방금 전"
            news_list.append({"title": title, "link": link, "source": source, "time": time_str})
        return news_list
    except: return []

# ==========================================
# 7. 최상위 퀀트 엔진: 완벽한 정배열 + VCP 필터 + ATR 손절
# ==========================================
TARGET_STOCKS = [
    "SPY", "QQQ", "DIA", "IWM", "SOXX", "TQQQ", "SOXL", "NVDL", "TECL", "FNGU", "BULZ",
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
    "AVGO", "TSM", "AMD", "QCOM", "ASML", "AMAT", "MU", "LRCX", "INTC", "ARM", "SMCI", "SIMO", "WDC", "TXN", "NXPI",
    "CRM", "ADBE", "NFLX", "CSCO", "ORCL", "NOW", "INTU", "UBER", "SNOW", "PLTR", "CRWD", "PANW", "FTNT", "DDOG", "NET", "MDB", "TEAM", "WDAY",
    "V", "MA", "JPM", "BAC", "WFC", "GS", "MS", "AXP", "PYPL", "SQ", "COIN", "MARA", "RIOT", "MSTR", "HOOD", "SOFI", "AFRM", "UPST",
    "LLY", "NVO", "UNH", "JNJ", "ABBV", "MRK", "TMO", "DHR", "PFE", "VRTX", "REGN", "MRNA", "ISRG", "SYK",
    "WMT", "COST", "PG", "KO", "PEP", "MCD", "NKE", "SBUX", "XOM", "CVX", "GE", "CAT", "BA", "DE",
    "RIVN", "LCID", "NIO", "XPEV", "LI", "JOBY", "ACHR", "IONQ", "RGTI", "RBLX", "U", "DKNG", "CVNA"
]

def analyze_practical_signals(vix_level):
    # MA120을 정확히 구하기 위해 데이터 수집 기간을 1y(1년)으로 확장
    data = yf.download(TARGET_STOCKS, period="1y", group_by='ticker', progress=False)
    vcp_swing, momentum, accum, reversal = [], [], [], []
    
    for ticker in TARGET_STOCKS:
        try:
            df = data[ticker].dropna()
            # 120일 이평선을 계산해야 하므로 최소 130일치 데이터가 없는 신규 상장주는 과감히 제외
            if len(df) < 130: continue
            
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA50'] = df['Close'].rolling(window=50).mean()
            df['MA120'] = df['Close'].rolling(window=120).mean()
            df['BB_std'] = df['Close'].rolling(window=20).std()
            df['BB_Width'] = (df['BB_std'] * 4) / df['MA20']
            
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['ATR'] = true_range.rolling(14).mean()
            
            df['Vol_20MA'] = df['Volume'].rolling(window=20).mean()
            typical_price = (df['High'] + df['Low'] + df['Close']) / 3
            raw_money_flow = typical_price * df['Volume']
            money_flow_pos = raw_money_flow.where(df['Close'] > df['Close'].shift(1), 0)
            money_flow_neg = raw_money_flow.where(df['Close'] < df['Close'].shift(1), 0)
            mf_pos_sum = money_flow_pos.rolling(window=14).sum()
            mf_neg_sum = money_flow_neg.rolling(window=14).sum()
            df['MFI'] = 100 - (100 / (1 + (mf_pos_sum / mf_neg_sum)))
            
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            change_pct = float(((last['Close'] - prev['Close']) / prev['Close']) * 100)
            change_str = f"🔥 +{change_pct:.2f}%" if change_pct > 0 else f"❄️ {change_pct:.2f}%"
            vol_ratio = float(last['Volume'] / last['Vol_20MA'])
            
            atr_stop_loss = float(last['Close'] - (last['ATR'] * 2))
            
            base_info = {
                "티커": ticker, 
                "현재가": f"${float(last['Close']):.2f}", 
                "ATR 스마트손절": f"${atr_stop_loss:.2f}",
                "당일 등락률": change_str, 
                "변동%": change_pct,
                "원가": float(last['Close'])
            }
            
            # 🔥 핵심 패치: 완벽한 정배열(우상향) 상태인 주도주만 걸러내는 'Stage 2' 필터
            # 20일선 > 50일선 > 120일선 위에 주가가 위치해야 함. (어도비, 나이키 같은 하락 차트 원천 차단)
            is_uptrend = (last['Close'] > last['MA20']) and (last['MA20'] > last['MA50']) and (last['MA50'] > last['MA120'])
            
            # [전략 1] 우상향 주도주 + VCP(변동성 축소) + 20일선 지지
            is_vcp_tight = last['BB_Width'] < df['BB_Width'].rolling(20).mean().iloc[-1]
            is_near_ma20 = (last['MA20'] * 0.99 <= last['Close'] <= last['MA20'] * 1.05)
            
            # 하락장이 아닌 완벽한 우상향 종목에서만 VCP 스윙 타점을 잡음
            if (vix_level < 25.0) and is_uptrend and is_near_ma20 and is_vcp_tight and (last['MFI'] > prev['MFI']):
                vcp_swing.append({**base_info, "타점": "주도주 VCP 완벽 눌림목", "승률기대": "👑 S+ 급"})
                
            # [전략 2] 기관 대량 수급 돌파 (역시 정배열 주도주에서만)
            if is_uptrend and (last['Close'] > df['High'].rolling(20).max().iloc[-2]) and (vol_ratio >= 2.0) and (change_pct >= 3.0):
                momentum.append({**base_info, "타점": "주도주 기관 대량 돌파", "승률기대": "⭐️⭐️⭐️⭐️"})
                
            # [전략 3] 거대 세력 딥(Deep) 매집 (이것만 낙폭과대 역발상 매매)
            if (last['Close'] < last['MA120']) and (last['MFI'] <= 25) and (change_pct > 0):
                accum.append({**base_info, "타점": "패닉셀 후 V자 매집", "승률기대": "⭐️⭐️⭐️"})
                
        except Exception as e: continue
            
    return vcp_swing, momentum, accum, reversal

# ==========================================
# 8. 메인 렌더링 파트
# ==========================================
col_main, col_side = st.columns([7, 3])

if 'scanned' not in st.session_state:
    st.session_state.scanned = False
    st.session_state.vcp_swing = []

with col_main:
    st.markdown("### ⚡ 월가 기관급 VCP(변동성 축소) + 주도주 정배열 정밀 스캔")
    if st.button("🚀 매크로 방어막 가동 및 전 종목 정밀 스캔", use_container_width=True):
        with st.spinner("과거 1년치 데이터 다운로드 및 우상향(Stage 2) 필터링 중... (약 15~20초 소요)"):
            current_vix = macro_data['^VIX']['price'] if macro_data else 20.0
            vcp_swing, momentum, accum, reversal = analyze_practical_signals(current_vix)
            st.session_state.vcp_swing = vcp_swing
            st.session_state.scanned = True
            
            if vcp_swing:
                top3_to_save = pd.DataFrame(vcp_swing).sort_values("변동%", ascending=False).head(3).to_dict('records')
                save_history(top3_to_save)

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"<div class='metric-box'><div class='metric-title'>👑 주도주 압축 스윙</div><div class='metric-value text-blue'>{len(vcp_swing)}건</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='metric-box'><div class='metric-title'>🚀 우상향 돌파</div><div class='metric-value text-red'>{len(momentum)}건</div></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='metric-box'><div class='metric-title'>🐳 세력 딥 매집</div><div class='metric-value text-yellow'>{len(accum)}건</div></div>", unsafe_allow_html=True)
            c4.markdown(f"<div class='metric-box'><div class='metric-title'>🛡️ VIX 지수 (방어막)</div><div class='metric-value text-green'>{current_vix:.2f}</div></div>", unsafe_allow_html=True)
            
            st.write("")
            tab1, tab2, tab3 = st.tabs(["👑 주도주 VCP 스윙 (최우선 타점)", "🚀 우상향 돌파", "🐳 스마트머니 매집"])
            
            def display_data(data, msg):
                if data:
                    df = pd.DataFrame(data).sort_values("변동%", ascending=False).drop(columns=['변동%', '원가']).reset_index(drop=True)
                    st.dataframe(df, use_container_width=True)
                else: st.info(msg)

            with tab1: display_data(vcp_swing, "현재 완벽한 우상향 상태에서 VCP로 압축된 주도주가 없습니다. (현금 관망 권장)")
            with tab2: display_data(momentum, "우상향 돌파 종목이 없습니다.")
            with tab3: display_data(accum, "매집 종목이 없습니다.")

# ==========================================
# 9. 우측 사이드바 (과거 수익률 검증 & 뉴스)
# ==========================================
with col_side:
    st.markdown("### 🕵️‍♂️ 직전 추천종목 자동 검증")
    past_history = load_history()
    
    if past_history:
        st.caption(f"기록된 시간: {past_history[0]['시간']}")
        for item in past_history:
            ticker = item['티커']
            old_price = item['추천가']
            try:
                curr_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
                profit_pct = ((curr_price - old_price) / old_price) * 100
                card_class = "history-card-up" if profit_pct > 0 else "history-card-down"
                arrow = "🔥" if profit_pct > 0 else "❄️"
                color = "#EF4444" if profit_pct > 0 else "#3B82F6"
                
                st.markdown(f"""
                <div class='{card_class}'>
                    <div>
                        <div style='font-weight:bold; font-size:16px; color:#FFFFFF;'>{ticker}</div>
                        <div style='font-size:11px; color:#8A94A6;'>추천가 ${old_price:.2f} ➔ 현재가 ${curr_price:.2f}</div>
                    </div>
                    <div style='font-size:18px; font-weight:bold; color:{color};'>
                        {arrow} {profit_pct:+.2f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except: st.write(f"{ticker}: 실시간 데이터 로딩 불가")
    else: st.info("과거 추천 기록이 없습니다. 스캔을 돌려주세요.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🏆 주도주 스윙 원픽 TOP 3")
    if st.session_state.scanned and st.session_state.vcp_swing:
        df_top = pd.DataFrame(st.session_state.vcp_swing).sort_values("변동%", ascending=False).head(3)
        for idx, row in df_top.iterrows():
            st.markdown(f"""
            <div class='top-pick-card'>
                <div class='top-pick-ticker'>👑 {row['티커']}</div>
                <div class='top-pick-price'>{row['현재가']} <span style='font-size:13px; color:#A1A1AA;'>({row['당일 등락률']})</span></div>
            </div>
            """, unsafe_allow_html=True)
    else: st.markdown("<div style='color:#64748B; font-size:14px; margin-bottom:20px;'>스캔을 완료하면 오늘의 추천 종목이 뜹니다.</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    news_tab1, news_tab2, news_tab3 = st.tabs(["🌐 전체 시장 뉴스", "🚨 특징주 속보", "📊 매크로/PCE 지표 분석"])
    def render_clickable_news(keyword):
        news_list = get_live_clickable_news(keyword)
        if news_list:
            for n in news_list:
                st.markdown(f"""<a href="{n['link']}" target="_blank"><div class='news-box'><div class='news-title'>⚡ {n['title']}</div><div class='news-meta'><span>{n['source']}</span><span style="color:#F59E0B;">{n['time']}</span></div></div></a>""", unsafe_allow_html=True)
        else: st.write("새로운 뉴스를 수집 중입니다.")

    with news_tab1: render_clickable_news("미국증시 OR 뉴욕증시 OR 연준")
    with news_tab2: render_clickable_news("나스닥 속보 OR 테슬라 OR 반도체")
    with news_tab3: render_clickable_news("미국 PCE 물가지수 OR 금리 인하 전망")
