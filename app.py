import streamlit as st
import yfinance as yf
import pandas as pd
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
import requests

st.set_page_config(page_title="Bollinger Scanner PRO", layout="wide")
st.sidebar.title("הגדרות")
TELEGRAM_TOKEN = st.sidebar.text_input("Telegram Token", type="password")
TELEGRAM_CHAT_ID = st.sidebar.text_input("Chat ID")
INTERVAL = st.sidebar.selectbox("אינטרוול", ["1d","1h","15m","5m"], index=0)
RSI_LIMIT = st.sidebar.slider("RSI מתחת ל-", 10, 40, 25)
VOL_MULT = st.sidebar.slider("מכפיל ווליום", 1.0, 3.0, 1.5)
search_ticker = st.sidebar.text_input("חיפוש מניה בודדת (למשל AAPL)")

@st.cache_data
def get_3500_tickers():
    try:
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all_tickers.txt"
        df = pd.read_csv(url, header=None)
        return df[0].tolist()[:3500]
    except:
        return ["AAPL","MSFT","NVDA","TSLA","AMD","META","GOOGL","AMZN","SPY","QQQ","PLTR","NIO","SOFI","MARA","COIN","MRVL","AVGO","NFLX","BA","DIS","INTC","PYPL","UBER","BABA","NKE","XOM","JPM","BAC","WMT","COST"]

ALL_TICKERS = get_3500_tickers()

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode":"Markdown"}, timeout=10)
    except:
        pass

def check_breakout(ticker, interval):
    try:
        period = "2y" if interval=="1d" else "60d" if interval=="1h" else "10d"
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if len(df) < 35:
            return None
        close = df["Close"]
        high = df["High"]
        bb = BollingerBands(close, 20, 2.0)
        bb_l = bb.bollinger_lband()
        bb_m = bb.bollinger_mavg()
        rsi = RSIIndicator(close, 14).rsi()
        c = float(close.iloc[-1])
        h = float(high.iloc[-1])
        pc = float(close.iloc[-2])
        c_bb_l = float(bb_l.iloc[-1])
        p_bb_l = float(bb_l.iloc[-2])
        c_bb_m = float(bb_m.iloc[-1])
        c_rsi = float(rsi.iloc[-1])
        vol = float(df["Volume"].iloc[-1])
        avg_vol = float(df["Volume"].rolling(20).mean().iloc[-1])
        is_break = c < c_bb_l and pc > p_bb_l and c_rsi < RSI_LIMIT and vol > avg_vol * VOL_MULT
        if interval == "1d":
            is_break = is_break and h < c_bb_l
        if is_break:
            pct = ((c_bb_m - c) / c) * 100
            return {"ticker": ticker, "price": c, "tp": c_bb_m, "pct": pct, "rsi": c_rsi, "interval": interval}
    except:
        return None
    return None

st.title("Bollinger Scanner PRO - 3500 מניות")
if search_ticker:
    st.subheader(f"בדיקת {search_ticker}")
    res = check_breakout(search_ticker.upper(), INTERVAL)
    if res:
        st.success(res)
        send_telegram(f"🚨 {res['ticker']} [{res['interval']}] ${res['price']:.2f} RSI:{res['rsi']:.1f} -> TP {res['tp']:.2f} (+{res['pct']:.2f}%)")
    else:
        st.info("אין פריצה")

if st.button(f"הרץ סריקה מלאה על {len(ALL_TICKERS)} מניות [{INTERVAL}]"):
    progress = st.progress(0)
    status = st.empty()
    results = []
    for i, t in enumerate(ALL_TICKERS):
        status.text(f"סורק {t} {i+1}/{len(ALL_TICKERS)}")
        progress.progress((i+1)/len(ALL_TICKERS))
        res = check_breakout(t, INTERVAL)
        if res:
            results.append(res)
            msg = f"🚨 {res['ticker']} [{res['interval']}] ${res['price']:.2f} RSI:{res['rsi']:.1f} -> TP {res['tp']:.2f} (+{res['pct']:.2f}%)"
            st.success(msg)
            send_telegram(msg)
    if results:
        st.dataframe(pd.DataFrame(results))
    else:
        st.warning("אין פריצות כרגע")
