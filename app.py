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
    
    .ticker-wrap { width: 100%; overflow: hidden; background-color: #151A23; border-bottom: 2px solid #252B3B; padding: 10px 0; margin-bottom: 20px; display: flex; }
    .ticker-move { display: flex; white-space: nowrap; animation: ticker 35s linear infinite; }
    .ticker-move:hover { animation-play-state: paused; }
    @keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
    .ticker-item { padding: 0 40px; font-size: 15px; font-weight: 700; color: #FFFFFF; flex-shrink: 0; }
    .ticker-up { color: #EF4444; } .ticker-down { color: #3B82F6; } .ticker-name { color: #94A3B8; font-size: 13px; margin-right: 8px; }
    
    .dashboard-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
    .dash-card { background: linear-gradient(145deg, #1A1F2B 0%, #11151D 100%); padding: 20px; border-radius: 12px; border: 1px solid #2D3748; box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-align: center; }
    .dash-title { color: #94A3B8; font-size: 13px; font-weight: bold; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
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
        'VIX 공포지수': '^VIX', '달러 환율': 'KRW=X', '코스피': '^KS11', '비트코인': 'BTC-USD'
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
st.markdown("<p style='text-align: center; color: #94A3B8; margin-bottom: 30px;'>WallStreet v11.1 | 지수 ETF 전면 숙청 및 탐욕/공포 지수 실시간 연동</p>", unsafe_allow_html=True)

# ==========================================
# 5. 실시간 공포/탐욕 지수 계산 (Fear & Greed)
# ==========================================
@st.cache_data(ttl=60)
def get_fear_greed_index():
    try:
        spy = yf.download('^GSPC', period='6mo', progress=False)['Close']
        vix = yf.download('^VIX', period='5d', progress=False)['Close'].iloc[-1]
        
        # SPY RSI 계산
        delta = spy.diff()
        up = delta.clip(lower=0).ewm(com=13).mean().iloc[-1]
        down = -1 * delta.clip(upper=0).ewm(com=13).mean().iloc[-1]
        rsi = 100 - (100 / (1 + up / down))
        
        # VIX 점수화 (10=탐욕 100점, 30=공포 0점)
        vix_score = max(0, min(100, 100 - (vix - 10) * 5))
        fgi = int((rsi + vix_score) / 2)
        
        if fgi >= 75: return fgi, "🟢 극단적 탐욕 (과열)", "#10B981"
        elif fgi >= 55: return fgi, "🟢 탐욕 (매수 우위)", "#34D399"
        elif fgi >= 45: return fgi, "⚪ 중립 (관망)", "#94A3B8"
        elif fgi >= 25: return fgi, "🔴 공포 (저점 매수 기회)", "#F87171"
        else: return fgi, "🔴 극단적 공포 (패닉셀)", "#EF4444"
    except: return 50, "⚪ 중립", "#94A3B8"

fgi_score, fgi_text, fgi_color = get_fear_greed_index()

# ==========================================
# 6. 헤지펀드 AI 퀀트 엔진 (순수 개별주만 포착)
# ==========================================
# 🔥 SSO, QLD, USD 등 모든 지수 추종 2배 레버리지 삭제 (오직 개별주 대장만)
BULL_STOCKS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
    "AVGO", "TSM", "AMD", "QCOM", "ASML", "AMAT", "MU", "LRCX", "INTC", "ARM", "SMCI", "SIMO", "WDC", "TXN", "NXPI",
    "CRM", "ADBE", "NFLX", "CSCO", "ORCL", "NOW", "INTU", "UBER", "SNOW", "PLTR", "CRWD", "PANW", "FTNT", "DDOG", "NET", "MDB", "TEAM", "WDAY",
    "V", "MA", "JPM", "BAC", "WFC", "GS", "MS", "AXP", "PYPL", "SQ", "COIN", "MARA", "RIOT", "MSTR", "HOOD", "SOFI", "AFRM"
]
BEAR_ETFS = ["SH", "PSQ", "QID"]

def analyze_hedgefund_signals():
    data = yf.download(BULL_STOCKS + BEAR_ETFS + ['^GSPC', '^VIX', 'TLT'], period="2y", group_by='ticker', progress=False)
    vcp_swing, bear_defense, momentum = [], [], []
    
    try:
        vix_df, tlt_df = data['^VIX'].dropna(), data['TLT'].dropna()
        current_vix = vix_df['Close'].iloc[-1]
        tlt_trend = tlt_df['Close'].iloc[-1] < tlt_df['Close'].iloc[-20]
        vix_limit = 20.0 if tlt_trend else 25.0 
        spy_df = data['^GSPC'].dropna()
        spy_return_6m = (spy_df['Close'].iloc[-1] - spy_df['Close'].iloc[-120]) / spy_df['Close'].iloc[-120]
    except: current_vix, vix_limit, spy_return_6m = 20.0, 25.0, 0.05

    for ticker in BULL_STOCKS + BEAR_ETFS:
        try:
            df = data[ticker].dropna()
            if len(df) < 255: continue
            
            df['MA20'], df['MA50'] = df['Close'].rolling(window=20).mean(), df['Close'].rolling(window=50).mean()
            df['MA150'], df['MA200'] = df['Close'].rolling(window=150).mean(), df['Close'].rolling(window=200).mean()
            df['High52'], df['Low52'] = df['High'].rolling(window=250).max(), df['Low'].rolling(window=250).min()
            
            # ATR (스마트 손절)
            tr1 = df['High'] - df['Low']
            tr2 = np.abs(df['High'] - df['Close'].shift())
            tr3 = np.abs(df['Low'] - df['Close'].shift())
            df['ATR'] = np.max(pd.concat([tr1, tr2, tr3], axis=1), axis=1).rolling(14).mean()
            
            # 👑 매수 폭발 점수 (구 '압축률')
            df['BB_std'] = df['Close'].rolling(window=20).std()
            df['BB_Width'] = (df['BB_std'] * 4) / df['MA20']
            bb_min_120, bb_max_120 = df['BB_Width'].rolling(120).min(), df['BB_Width'].rolling(120).max()
            df['BB_Percentile'] = (df['BB_Width'] - bb_min_120) / (bb_max_120 - bb_min_120) 
            
            df['Vol_50MA'] = df['Volume'].rolling(window=50).mean()
            
            last, prev = df.iloc[-1], df.iloc[-2]
            change_pct = ((last['Close'] - prev['Close']) / prev['Close']) * 100
            change_str = f"🔥 +{change_pct:.2f}%" if change_pct > 0 else f"❄️ {change_pct:.2f}%"
            atr_stop_loss = last['Close'] - (last['ATR'] * 2)
            
            # RS 주도력 및 매수 점수 계산
            stock_return_6m = (last['Close'] - df['Close'].iloc[-120]) / df['Close'].iloc[-120]
            rs_score = (stock_return_6m / spy_return_6m) * 100 if spy_return_6m > 0 else 100
            rs_rating = "👑 S급 대장주" if rs_score > 200 else "A급 주도주" if rs_score > 100 else "B급"
            
            # 🔥 직관적인 '매수 폭발 점수' (1~100점)
            buy_score = int(max(0, min(100, (1 - last['BB_Percentile']) * 100)))
            
            base_info = {
                "티커": ticker, 
                "현재가": float(last['Close']), 
                "손절가(ATR)": float(atr_stop_loss),
                "당일등락": change_str, 
                "시장 주도력": rs_rating,
                "💥 매수 폭발 점수": f"{buy_score}점", # 🔥 점수 표기로 변경
                "원가": float(last['Close'])
            }
            
            if ticker in BULL_STOCKS:
                is_uptrend = (last['Close'] > last['MA150'] and last['MA150'] > last['MA200'] and 
                              last['MA200'] > df['MA200'].iloc[-20] and last['Close'] > last['MA50'] and
                              last['Close'] >= last['Low52'] * 1.30 and last['Close'] >= last['High52'] * 0.75)
                
                is_vcp_extreme = buy_score >= 75 # 점수가 75점 이상(하위 25% 압축)일 때만
                is_vol_dry = df['Volume'].iloc[-3:].mean() < (last['Vol_50MA'] * 0.8)
                is_near_ma20 = (last['MA20'] * 0.98 <= last['Close'] <= last['MA20'] * 1.05)
                
                if (current_vix < vix_limit) and is_uptrend and is_near_ma20 and is_vcp_extreme and is_vol_dry and (change_pct > 0):
                    vcp_swing.append({**base_info, "타점": "👑 극압축 VCP 눌림목"})
                    
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
    if st.button("🚀 100억 엔진 가동 (순수 개별주 A+급만 포착)", use_container_width=True):
        with st.spinner("지수 ETF 숙청 및 매수 폭발 점수 계산 중... (약 20초 소요)"):
            vcp_swing, bear_defense, momentum, current_vix, vix_limit = analyze_hedgefund_signals()
            st.session_state.vcp_swing = vcp_swing
            st.session_state.scanned = True
            
            safe_status = "🟢 공격 베팅 (안전)" if current_vix < vix_limit else "🔴 현금 관망 (위험)"
            
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
                    <div class='dash-title'>🧭 탐욕/공포 지수</div>
                    <div class='dash-value' style='color:{fgi_color};'>{fgi_score}점</div>
                    <div class='dash-sub'>{fgi_text}</div>
                </div>
                <div class='dash-card'>
                    <div class='dash-title'>🛡️ PCE 매크로 방어벽</div>
                    <div class='dash-value' style='color:#3B82F6;'>{safe_status}</div>
                    <div class='dash-sub'>현재 VIX: {current_vix:.2f} / 기준: {vix_limit}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            tab1, tab2, tab3 = st.tabs(["👑 1순위: 극압축 VCP (100억 타점)", "🚀 2순위: 포켓 피봇 돌파", "🚨 3순위: 인버스 방어"])
            
            def display_premium_data(data, msg):
                if data:
                    df = pd.DataFrame(data).drop(columns=['원가']).sort_values("💥 매수 폭발 점수", ascending=False)
                    df['현재가'] = df['현재가'].apply(lambda x: f"${x:,.2f}")
                    df['손절가(ATR)'] = df['손절가(ATR)'].apply(lambda x: f"${x:,.2f}")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else: st.info(msg)

            with tab1: display_premium_data(vcp_swing, "현재 VCP 압축(매수 폭발 점수 75점 이상)을 통과한 개별 주도주가 없습니다.")
            with tab2: display_premium_data(momentum, "포켓 피봇(대량 거래 돌파) 개별 종목이 없습니다.")
            with tab3: display_premium_data(bear_defense, "현재 인버스 돌파 타점이 없습니다.")

# ==========================================
# 8. 우측 사이드바 (내 계좌 트래커 & 속보)
# ==========================================
with col_side:
    st.markdown("### 💼 나의 실시간 수익률 트래커")
    st.markdown("<p style='font-size:12px; color:#8A94A6;'>진입하신 종목(티커)과 단가를 입력하시면 실시간 수익률이 계산됩니다.</p>", unsafe_allow_html=True)
    
    if 'my_portfolio' not in st.session_state:
        st.session_state.my_portfolio = pd.DataFrame([{"티커": "NXPI", "진입단가": 310.00}], columns=["티커", "진입단가"])
    
    edited_df = st.data_editor(st.session_state.my_portfolio, num_rows="dynamic", use_container_width=True)
    st.session_state.my_portfolio = edited_df
    
    if st.button("🔄 실시간 수익률 확인", use_container_width=True):
        for index, row in edited_df.iterrows():
            ticker = str(row['티커']).upper().strip()
            try:
                entry_price = float(row['진입단가'])
                curr_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
                profit_pct = ((curr_price - entry_price) / entry_price) * 100
                color, arrow = ("#EF4444", "🔥") if profit_pct > 0 else ("#3B82F6", "❄️")
                
                st.markdown(f"""
                <div class='news-box' style='border-left: 4px solid {color};'>
                    <div style='display:flex; justify-content:space-between;'>
                        <span style='font-weight:bold; font-size:16px;'>{ticker}</span>
                        <span style='font-size:18px; font-weight:bold; color:{color};'>{arrow} {profit_pct:+.2f}%</span>
                    </div>
                    <div style='font-size:12px; color:#94A3B8; margin-top:4px;'>
                        매수단가 ${entry_price:,.2f} ➔ 현재가 ${curr_price:,.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except:
                if ticker: st.error(f"{ticker}: 데이터를 불러올 수 없습니다.")

    st.markdown("<br>", unsafe_allow_html=True)
    news_tab1, news_tab2 = st.tabs(["🌐 100억 거시경제", "🚨 주도주 속보"])
    def render_news(keyword):
        for n in get_live_clickable_news(keyword):
            st.markdown(f"<a href='{n['link']}' target='_blank'><div class='news-box'><div class='news-title'>⚡ {n['title']}</div><div class='news-meta'><span>{n['source']}</span><span style='color:#F59E0B;'>{n['time']}</span></div></div></a>", unsafe_allow_html=True)

    with news_tab1: render_news("미국 PCE OR 금리인하 OR 연준")
    with news_tab2: render_news("엔비디아 OR 나스닥 특징주")
