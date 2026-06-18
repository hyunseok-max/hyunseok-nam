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
# 1. 터미널 UI 세팅
# ==========================================
st.set_page_config(page_title="남현석의 월가 퀀트 터미널", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🔒 2. 통제실 보안 구역
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
# 3. CSS 스타일링 (전광판 애니메이션 최적화)
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0F111A; color: #FFFFFF; font-family: 'Pretendard', sans-serif; }
    
    .ticker-wrap { width: 100%; overflow: hidden; background-color: #1A1D27; border-bottom: 2px solid #2D3243; padding: 12px 0; margin-bottom: 20px; display: flex; box-sizing: border-box; }
    .ticker-move { display: flex; white-space: nowrap; animation: ticker 40s linear infinite; }
    .ticker-move:hover { animation-play-state: paused; }
    @keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
    .ticker-item { padding: 0 40px; font-size: 15px; font-weight: 600; color: #FFFFFF; flex-shrink: 0; }
    
    .ticker-up { color: #EF4444; }
    .ticker-down { color: #3B82F6; }
    .ticker-name { color: #8A94A6; font-size: 13px; margin-right: 8px; }
    
    .metric-box { background-color: #1A1D27; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #2D3243; }
    .metric-title { color: #8A94A6; font-size: 13px; margin-bottom: 5px; font-weight: bold; }
    .metric-value { font-size: 24px; font-weight: bold; color: #FFFFFF; }
    .history-card-up { background-color: rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
    .history-card-down { background-color: rgba(59, 130, 246, 0.1); border: 1px solid #3B82F6; padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
    .news-box { background-color: #1A1D27; padding: 12px 15px; margin-bottom: 10px; border-radius: 8px; border-left: 4px solid #3B82F6; transition: 0.2s; }
    .news-box:hover { background-color: #24283B; transform: translateX(3px); }
    .news-title { font-size: 14px; font-weight: bold; color: #F8FAFC; line-height: 1.4; margin-bottom: 6px; }
    .news-meta { font-size: 11px; color: #8A94A6; display: flex; justify-content: space-between; }
    a { text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. 실시간 무빙 티커 (1분 단위 초정밀 캐싱으로 오차 최소화)
# ==========================================
@st.cache_data(ttl=60) # 🔥 5분에서 1분으로 단축 (실시간 성 강화)
def get_ticker_data():
    ticker_symbols = {
        '나스닥': '^IXIC', 'S&P 500': '^GSPC', '다우존스': '^DJI', '필라델피아 반도체': '^SOX', 
        'VIX 공포지수': '^VIX', '달러 환율': 'KRW=X', '코스피': '^KS11', '비트코인': 'BTC-USD', '금': 'GC=F'
    }
    try:
        # 최근 5일치 데이터를 가져오되, 마지막 줄이 가장 실시간에 가까움
        data = yf.download(list(ticker_symbols.values()), period="5d", progress=False)['Close'].ffill().dropna()
        items_html = ""
        for name, symbol in ticker_symbols.items():
            last = float(data[symbol].iloc[-1])
            prev = float(data[symbol].iloc[-2])
            diff = last - prev
            pct = (diff / prev) * 100
            color_class = "ticker-up" if diff > 0 else "ticker-down"
            sign = "+" if diff > 0 else ""
            
            if name in ['달러 환율', '코스피', 'S&P 500']: val_str = f"{last:,.2f}"
            elif name == '비트코인': val_str = f"${last:,.0f}"
            else: val_str = f"{last:,.2f}"
            
            items_html += f"<div class='ticker-item'><span class='ticker-name'>{name}</span> {val_str} <span class='{color_class}'>({sign}{pct:.2f}%)</span></div>"
        
        html_str = f"<div class='ticker-wrap'><div class='ticker-move'>{items_html}{items_html}</div></div>"
        return html_str
    except: return "<div class='ticker-wrap'><div class='ticker-move'>실시간 지수 데이터를 불러오는 중입니다...</div></div>"

st.markdown(get_ticker_data(), unsafe_allow_html=True)

st.title("🎯 남현석의 실전 퀀트 터미널 (WallStreet v10.5)")
st.markdown("🏆 미너비니 트렌드 템플릿 + 시장 주도력(RS) 절대강자 정밀 포착 엔진")

# ==========================================
# 5. 직전 추천 종목 수익률 검증 
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
# 7. 궁극의 퀀트 엔진: 미너비니 템플릿 + 상대강도(RS) 점수
# ==========================================
BULL_STOCKS = [
    "QLD", "SSO", "USD", "NVDL",
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
    "AVGO", "TSM", "AMD", "QCOM", "ASML", "AMAT", "MU", "LRCX", "INTC", "ARM", "SMCI", "SIMO", "WDC", "TXN", "NXPI",
    "CRM", "ADBE", "NFLX", "CSCO", "ORCL", "NOW", "INTU", "UBER", "SNOW", "PLTR", "CRWD", "PANW", "FTNT", "DDOG", "NET", "MDB", "TEAM", "WDAY",
    "V", "MA", "JPM", "BAC", "WFC", "GS", "MS", "AXP", "PYPL", "SQ", "COIN", "MARA", "RIOT", "MSTR", "HOOD", "SOFI", "AFRM", "UPST"
]
BEAR_ETFS = ["SH", "PSQ", "QID", "DXD"]

def analyze_practical_signals():
    # RS(상대강도) 비교를 위해 S&P 500(^GSPC) 데이터 필수 수집
    data = yf.download(BULL_STOCKS + BEAR_ETFS + ['^GSPC'], period="2y", group_by='ticker', progress=False)
    signature_swing, bear_defense, momentum = [], [], []
    
    # S&P 500의 최근 6개월(120일) 수익률 계산 (RS 점수 기준점)
    try:
        spy_df = data['^GSPC'].dropna()
        spy_return_6m = (spy_df['Close'].iloc[-1] - spy_df['Close'].iloc[-120]) / spy_df['Close'].iloc[-120]
    except:
        spy_return_6m = 0.05

    for ticker in BULL_STOCKS + BEAR_ETFS:
        try:
            df = data[ticker].dropna()
            if len(df) < 255: continue
            
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA50'] = df['Close'].rolling(window=50).mean()
            df['MA150'] = df['Close'].rolling(window=150).mean()
            df['MA200'] = df['Close'].rolling(window=200).mean()
            
            df['High52'] = df['High'].rolling(window=250).max()
            df['Low52'] = df['Low'].rolling(window=250).min()
            
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            true_range = np.max(pd.concat([high_low, high_close, low_close], axis=1), axis=1)
            df['ATR'] = true_range.rolling(14).mean()
            
            delta = df['Close'].diff()
            ema_up = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
            ema_down = (-1 * delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
            df['RSI'] = 100 - (100 / (1 + (ema_up / ema_down)))
            min_rsi = df['RSI'].rolling(window=14).min()
            max_rsi = df['RSI'].rolling(window=14).max()
            df['StochRSI'] = (df['RSI'] - min_rsi) / (max_rsi - min_rsi)
            df['K'] = df['StochRSI'].rolling(window=3).mean() * 100
            
            df['Vol_20MA'] = df['Volume'].rolling(window=20).mean()
            
            last = df.iloc[-1]
            prev = df.iloc[-2]
            change_pct = float(((last['Close'] - prev['Close']) / prev['Close']) * 100)
            change_str = f"🔥 +{change_pct:.2f}%" if change_pct > 0 else f"❄️ {change_pct:.2f}%"
            vol_ratio = float(last['Volume'] / last['Vol_20MA'])
            atr_stop_loss = float(last['Close'] - (last['ATR'] * 2))
            
            # 🔥 상대강도 (RS) 점수 계산: 종목의 6개월 수익률 vs S&P500 6개월 수익률
            stock_return_6m = (last['Close'] - df['Close'].iloc[-120]) / df['Close'].iloc[-120]
            rs_rating = "압도적 대장주" if stock_return_6m > (spy_return_6m * 2) else "시장 상회" if stock_return_6m > spy_return_6m else "시장 하회"
            
            base_info = {
                "티커": ticker, 
                "현재가": f"${float(last['Close']):.2f}", 
                "ATR 스마트손절": f"${atr_stop_loss:.2f}",
                "당일 등락률": change_str, 
                "시장 주도력(RS)": rs_rating, # 🔥 신규 무기 장착
                "변동%": change_pct,
                "원가": float(last['Close'])
            }
            
            if ticker in BULL_STOCKS:
                # 미너비니 템플릿 필터
                cond1 = last['Close'] > last['MA150'] and last['Close'] > last['MA200']
                cond2 = last['MA150'] > last['MA200']
                cond3 = last['MA200'] > df['MA200'].iloc[-20] 
                cond4 = last['MA50'] > last['MA150'] and last['MA50'] > last['MA200']
                cond5 = last['Close'] > last['MA50']
                cond6 = last['Close'] >= last['Low52'] * 1.30 
                cond7 = last['Close'] >= last['High52'] * 0.75 
                
                is_ultimate_uptrend = cond1 and cond2 and cond3 and cond4 and cond5 and cond6 and cond7
                
                # 타점 조건
                is_near_ma20 = (last['MA20'] * 0.98 <= last['Close'] <= last['MA20'] * 1.05)
                is_stoch_cool = last['K'] < 40
                is_vol_low = vol_ratio < 1.0 
                
                if is_ultimate_uptrend and is_near_ma20 and is_stoch_cool and is_vol_low and (change_pct > 0):
                    signature_swing.append({**base_info, "타점": "👑 미너비니 20일선 눌림", "승률기대": "S++ 급"})
                    
                if is_ultimate_uptrend and (last['Close'] > df['High'].rolling(20).max().iloc[-2]) and (vol_ratio >= 1.5) and (change_pct >= 2.0):
                    momentum.append({**base_info, "타점": "주도주 거래량 폭발 돌파", "승률기대": "⭐️⭐️⭐️⭐️"})

            if ticker in BEAR_ETFS:
                if (last['Close'] > last['MA20']) and (last['MA20'] > prev['MA20']) and (change_pct > 1.0):
                    bear_defense.append({**base_info, "타점": "🚨 하락장 진입: 인버스 돌파", "승률기대": "방어용"})
                
        except Exception as e: continue
            
    return signature_swing, bear_defense, momentum

# ==========================================
# 8. 메인 렌더링 파트
# ==========================================
col_main, col_side = st.columns([7, 3])

if 'scanned' not in st.session_state:
    st.session_state.scanned = False
    st.session_state.signature_swing = []

with col_main:
    st.markdown("### ⚡ All-Weather: 궁극의 주도주 스윙 및 하락장 방어 스캔")
    if st.button("🚀 월가 0.01% 궁극의 정밀 스캔 가동", use_container_width=True):
        with st.spinner("상대강도(RS) 점수 계산 및 미너비니 템플릿 가동 중... (약 20초 소요)"):
            signature_swing, bear_defense, momentum = analyze_practical_signals()
            st.session_state.signature_swing = signature_swing
            st.session_state.scanned = True
            
            if signature_swing:
                top3_to_save = pd.DataFrame(signature_swing).sort_values("변동%", ascending=False).head(3).to_dict('records')
                save_history(top3_to_save)

            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='metric-box'><div class='metric-title'>👑 미너비니 20일선 스윙</div><div class='metric-value text-blue'>{len(signature_swing)}건</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='metric-box'><div class='metric-title'>🚨 하락장 방어 (인버스)</div><div class='metric-value text-red'>{len(bear_defense)}건</div></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='metric-box'><div class='metric-title'>🚀 찐주도주 돌파</div><div class='metric-value text-green'>{len(momentum)}건</div></div>", unsafe_allow_html=True)
            
            st.write("")
            tab1, tab2, tab3 = st.tabs(["👑 미너비니 시그니처 (S++급)", "🚨 하락장 인버스 방어", "🚀 주도주 신고가 돌파"])
            
            def display_data(data, msg):
                if data:
                    df = pd.DataFrame(data).sort_values("변동%", ascending=False).drop(columns=['변동%', '원가']).reset_index(drop=True)
                    st.dataframe(df, use_container_width=True)
                else: st.info(msg)

            with tab1: display_data(signature_swing, "현재 미너비니 템플릿을 통과한 종목 중 20일선 눌림목 자리가 없습니다. (현금 관망)")
            with tab2: display_data(bear_defense, "현재 시장은 상승장이며, 뚜렷한 하락(인버스) 타점이 없습니다.")
            with tab3: display_data(momentum, "신고가 돌파 종목이 없습니다.")

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
    news_tab1, news_tab2 = st.tabs(["🌐 전체 시장 뉴스", "🚨 특징주 속보"])
    def render_clickable_news(keyword):
        news_list = get_live_clickable_news(keyword)
        if news_list:
            for n in news_list:
                st.markdown(f"""<a href="{n['link']}" target="_blank"><div class='news-box'><div class='news-title'>⚡ {n['title']}</div><div class='news-meta'><span>{n['source']}</span><span style="color:#F59E0B;">{n['time']}</span></div></div></a>""", unsafe_allow_html=True)
        else: st.write("새로운 뉴스를 수집 중입니다.")

    with news_tab1: render_clickable_news("미국증시 OR 뉴욕증시 OR 연준")
    with news_tab2: render_clickable_news("나스닥 속보 OR 테슬라 OR 반도체")
