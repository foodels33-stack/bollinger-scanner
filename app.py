import streamlit as st
import yfinance as yf
import pandas as pd
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
import requests

TELEGRAM_TOKEN = "YOUR_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"
PERIOD = "6mo"
INTERVAL = "1d"
BB_PERIOD = 20
BB_STD = 2.0
RSI_LIMIT = 25
VOL_MULT = 1.5

ALL_TICKERS = [
"AAPL","MSFT","NVDA","TSLA","AMD","META","GOOGL","AMZN","SPY","QQQ",
"PLTR","NIO","SOFI","MARA","COIN","MRVL","AVGO","NFLX","BA","DIS",
"INTC","PYPL","UBER","BABA","NKE","XOM","JPM","BAC","WMT","COST"
]

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
    except:
        pass

def check_real_breakout(ticker):
    try:
        df = yf.download(ticker, period=PERIOD, interval=INTERVAL, progress=False, auto_adjust=True)
        if len(df) < 35:
            return None
        close = df["Close"]
        high = df["High"]
        bb = BollingerBands(close, BB_PERIOD, BB_STD)
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
        is_break = c < c_bb_l and h < c_bb_l and pc > p_bb_l and c_rsi < RSI_LIMIT and vol > avg_vol * VOL_MULT
        if is_break:
            pct = ((c_bb_m - c) / c) * 100
            return {"ticker": ticker, "price": c, "tp": c_bb_m, "pct": pct, "rsi": c_rsi}
    except:
        return None
    return None

st.set_page_config(page_title="Bollinger Real Scanner", layout="wide")
st.title("Bollinger Scanner - פריצות אמיתיות בלבד [1D]")

if st.button("הרץ סריקה מלאה"):
    progress = st.progress(0)
    results = []
    for i, t in enumerate(ALL_TICKERS):
        progress.progress((i+1)/len(ALL_TICKERS))
        res = check_real_breakout(t)
        if res:
            results.append(res)
            msg = f"🚨 {res['ticker']} פריצה אמיתית ${res['price']:.2f} RSI:{res['rsi']:.1f} TP:{res['tp']:.2f} (+{res['pct']:.2f}%)"
            st.success(msg)
            send_telegram(msg)
    if not results:
        st.info("אין פריצות אמיתיות כרגע")
    else:
        df = pd.DataFrame(results)
        st.dataframe(df)
