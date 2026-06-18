import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import email.utils
from datetime import datetime, timezone
import json
import os

# ==========================================
# 1. 터미널 UI 및 다크모드 세팅
# ==========================================
st.set_page_config(page_title="남현석의 월가 퀀트 터미널", layout="wide", initial_sidebar_state="collapsed")
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

st.title("🎯 남현석의 실전 퀀트 터미널 (WallStreet v9.5)")
st.markdown("거시경제 모니터링 및 주도주 스윙 승률 극대화 알고리즘 탑재")

# ==========================================
# 2. 직전 추천 종목(TOP 3) 수익률 검증 파일 시스템
# ==========================================
HISTORY_FILE = "quant_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_history(top3_data):
    save_data = []
    for item in top3_data:
        save_data.append({"티커": item['티커'], "추천가": item['원가'], "시간": datetime.now().strftime("%Y-%m-%d %H:%M")})
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=4)

# ==========================================
# 3. 시장 거시경제(매크로) 전광판
# ==========================================
@st.cache_data(ttl=300)
def get_macro_data():
    try:
        tickers = ['^IXIC', '^GSPC', '^VIX', 'TLT'] # 나스닥, S&P, 공포지수, 장기채(금리)
        data = yf.download(tickers, period="5d", progress=False)['Close']
        macro = {}
        for t in tickers:
            last = float(data[t].iloc[-1])
            prev = float(data[t].iloc[-2])
            pct = ((last - prev) / prev) * 100
            macro[t] = {"price": last, "pct": pct}
        return macro
    except:
        return None

macro_data = get_macro_data()
if macro_data:
    st.markdown(f"""
    <div class='macro-container'>
        <div class='macro-box' style='border-top-color: #3B82F6;'>
            <div class='macro-title'>📈 나스닥 종합</div>
            <div class='macro-value'>{macro_data['^IXIC']['price']:,.2f} <span style='font-size:14px; color:{"#EF4444" if macro_data['^IXIC']['pct']<0 else "#10B981"};'>({macro_data['^IXIC']['pct']:+.2f}%)</span></div>
        </div>
        <div class='macro-box' style='border-top-color: #F59E0B;'>
            <div class='macro-title'>🚨 VIX 공포지수</div>
            <div class='macro-value'>{macro_data['^VIX']['price']:.2f} <span style='font-size:14px; color:{"#10B981" if macro_data['^VIX']['pct']<0 else "#EF4444"};'>({macro_data['^VIX']['pct']:+.2f}%)</span></div>
        </div>
        <div class='macro-box' style='border-top-color: #8B5CF6;'>
            <div class='macro-title'>🏦 TLT (거시 금리 방어막)</div>
            <div class='macro-value'>${macro_data['TLT']['price']:.2f} <span style='font-size:14px; color:{"#EF4444" if macro_data['TLT']['pct']<0 else "#10B981"};'>({macro_data['TLT']['pct']:+.2f}%)</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. 실시간 뉴스 엔진
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
            if " - " in title:
                title, source = title.rsplit(" - ", 1)
                
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
# 5. 글로벌 핵심 주도주 100선 + 승률 최적화 타점 엔진
# ==========================================
TARGET_STOCKS = [
    # 레버리지 및 시장 지수 ETF
    "SPY", "QQQ", "DIA", "IWM", "SOXX", "TQQQ", "SOXL", "NVDL", "TECL", "FNGU", "BULZ",
    # M7 및 빅테크
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
    # 인공지능 & 반도체 핵심
    "AVGO", "TSM", "AMD", "QCOM", "ASML", "AMAT", "MU", "LRCX", "INTC", "ARM", "SMCI", "SIMO", "WDC", "TXN", "NXPI",
    # 거대 소프트웨어 & 클라우드
    "CRM", "ADBE", "NFLX", "CSCO", "ORCL", "NOW", "INTU", "UBER", "SNOW", "PLTR", "CRWD", "PANW", "FTNT", "DDOG", "NET", "MDB", "TEAM", "WDAY",
    # 금융 & 핀테크 & 코인
    "V", "MA", "JPM", "BAC", "WFC", "GS", "MS", "AXP", "PYPL", "SQ", "COIN", "MARA", "RIOT", "MSTR", "HOOD", "SOFI", "AFRM", "UPST",
    # 바이오 & 헬스케어
    "LLY", "NVO", "UNH", "JNJ", "ABBV", "MRK", "TMO", "DHR", "PFE", "VRTX", "REGN", "MRNA", "ISRG", "SYK",
    # 전통 우량주 & 에너지 & 로보틱스
    "WMT", "COST", "PG", "KO", "PEP", "MCD", "NKE", "SBUX", "XOM", "CVX", "GE", "CAT", "BA", "DE",
    "RIVN", "LCID", "NIO", "XPEV", "LI", "JOBY", "ACHR", "IONQ", "RGTI", "RBLX", "U", "DKNG", "CVNA"
]

def analyze_practical_signals():
    data = yf.download(TARGET_STOCKS, period="6mo", group_by='ticker', progress=False)
    swing, momentum, accum, reversal = [], [], [], []
    
    for ticker in TARGET_STOCKS:
        try:
            df = data[ticker].dropna()
            if len(df) < 60: continue
            
            # --- 1. 기본 이동평균선 ---
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA50'] = df['Close'].rolling(window=50).mean()
            df['MA120'] = df['Close'].rolling(window=120).mean()
            df['Vol_20MA'] = df['Volume'].rolling(window=20).mean()
            
            # --- 2. RSI 및 StochRSI (윗꼬리 함정 회피용) ---
            delta = df['Close'].diff()
            ema_up = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
            ema_down = (-1 * delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
            df['RSI'] = 100 - (100 / (1 + (ema_up / ema_down)))
            
            min_rsi = df['RSI'].rolling(window=14).min()
            max_rsi = df['RSI'].rolling(window=14).max()
            df['StochRSI'] = (df['RSI'] - min_rsi) / (max_rsi - min_rsi)
            df['K'] = df['StochRSI'].rolling(window=3).mean() * 100
            df['D'] = df['K'].rolling(window=3).mean()
            
            # --- 3. MFI (자금 유출입 확인 - 가짜 상승 필터링) ---
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
            
            # 기계적 손절선 설정 (-7% 기준)
            stop_loss = float(last['Close'] * 0.93)
            
            base_info = {
                "티커": ticker, 
                "현재가": f"${float(last['Close']):.2f}", 
                "손절선(-7%)": f"${stop_loss:.2f}",
                "당일 등락률": change_str, 
                "변동%": change_pct,
                "원가": float(last['Close'])
            }
            
            # [전략 1] 100억 참모 '20일선 콘크리트 눌림목' 스윙
            is_near_ma20 = (last['MA20'] * 0.98 <= last['Close'] <= last['MA20'] * 1.03)
            if is_near_ma20 and (change_pct > 0) and (last['K'] < 40) and (last['K'] > prev['K']) and (last['MFI'] < 50):
                swing.append({**base_info, "타점": "20일선 완벽 눌림목", "승률기대": "⭐️⭐️⭐️⭐️⭐️"})
                
            # [전략 2] 종가 MOC 돌파
            if (last['Close'] > df['High'].rolling(20).max().iloc[-2]) and (vol_ratio >= 1.5) and (change_pct >= 3.0) and (last['K'] < 80):
                momentum.append({**base_info, "타점": "종가 대량거래 돌파", "승률기대": "⭐️⭐️⭐️⭐️"})
                
            # [전략 3] 거대 세력 딥(Deep) 매집
            if (last['Close'] < last['MA120']) and (last['MFI'] <= 25) and (last['K'] > last['D']):
                accum.append({**base_info, "타점": "패닉셀 후 V자 매집", "승률기대": "⭐️⭐️⭐️"})
                
        except Exception as e: 
            continue
            
    return swing, momentum, accum, reversal

# ==========================================
# 6. 메인 렌더링 파트
# ==========================================
col_main, col_side = st.columns([7, 3])

if 'scanned' not in st.session_state:
    st.session_state.scanned = False
    st.session_state.swing = []

with col_main:
    if st.button("🚀 월가 주도주 100선 + 레버리지 정밀 스캔", use_container_width=True):
        with st.spinner("주도주 데이터 다운로드 및 퀀트 지표 교차 검증 중... (약 10~15초 소요)"):
            swing, momentum, accum, reversal = analyze_practical_signals()
            st.session_state.swing = swing
            st.session_state.scanned = True
            
            if swing:
                top3_to_save = pd.DataFrame(swing).sort_values("변동%", ascending=False).head(3).to_dict('records')
                save_history(top3_to_save)

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"<div class='metric-box'><div class='metric-title'>📈 20일선 스윙</div><div class='metric-value text-blue'>{len(swing)}건</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='metric-box'><div class='metric-title'>🚀 모멘텀 돌파</div><div class='metric-value text-red'>{len(momentum)}건</div></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='metric-box'><div class='metric-title'>🐳 세력 딥 매집</div><div class='metric-value text-yellow'>{len(accum)}건</div></div>", unsafe_allow_html=True)
            c4.markdown(f"<div class='metric-box'><div class='metric-title'>🔄 추세 전환</div><div class='metric-value text-green'>{len(reversal)}건</div></div>", unsafe_allow_html=True)
            
            st.write("")
            tab1, tab2, tab3, tab4 = st.tabs(["📈 안전 스윙 (추천)", "🚀 급등주 돌파", "🐳 스마트머니 매집", "🔄 추세전환 시그널"])
            
            def display_data(data, msg):
                if data:
                    df = pd.DataFrame(data).sort_values("변동%", ascending=False).drop(columns=['변동%', '원가']).reset_index(drop=True)
                    st.dataframe(df, use_container_width=True)
                else: st.info(msg)

            with tab1: display_data(swing, "스윙 타점이 없습니다.")
            with tab2: display_data(momentum, "신고가 돌파 종목이 없습니다.")
            with tab3: display_data(accum, "매집 종목이 없습니다.")
            with tab4: display_data(reversal, "생명선을 돌파한 종목이 없습니다.")

# ==========================================
# 7. 우측 사이드바 (과거 수익률 검증 & 뉴스)
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
            except:
                st.write(f"{ticker}: 실시간 데이터를 불러올 수 없습니다.")
    else:
        st.info("아직 저장된 과거 추천 기록이 없습니다. 스캔을 돌려주세요.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### 🏆 신규 스윙 원픽 TOP 3")
    if st.session_state.scanned and st.session_state.swing:
        df_top = pd.DataFrame(st.session_state.swing).sort_values("변동%", ascending=False).head(3)
        for idx, row in df_top.iterrows():
            st.markdown(f"""
            <div class='top-pick-card'>
                <div class='top-pick-ticker'>🎯 {row['티커']}</div>
                <div class='top-pick-price'>{row['현재가']} <span style='font-size:13px; color:#A1A1AA;'>({row['당일 등락률']})</span></div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:#64748B; font-size:14px; margin-bottom:20px;'>스캔을 완료하면 오늘의 추천 종목이 뜹니다.</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    news_tab1, news_tab2, news_tab3 = st.tabs(["🌐 전체 시장 뉴스", "🚨 특징주 속보", "📊 시황 분석"])
    
    def render_clickable_news(keyword):
        news_list = get_live_clickable_news(keyword)
        if news_list:
            for n in news_list:
                st.markdown(f"""
                <a href="{n['link']}" target="_blank">
                    <div class='news-box'>
                        <div class='news-title'>⚡ {n['title']}</div>
                        <div class='news-meta'>
                            <span>{n['source']}</span>
                            <span style="color:#F59E0B;">{n['time']}</span>
                        </div>
                    </div>
                </a>
                """, unsafe_allow_html=True)
        else:
            st.write("새로운 뉴스를 수집 중입니다.")

    with news_tab1: render_clickable_news("미국증시 OR 뉴욕증시 OR 연준")
    with news_tab2: render_clickable_news("나스닥 속보 OR 테슬라 OR 반도체")
    with news_tab3: render_clickable_news("월가 전망 OR 특징주 분석")