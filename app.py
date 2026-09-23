import streamlit as st
import yfinance as yf
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
import requests

TELEGRAM_TOKEN = "YOUR_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
PERIOD = "6mo"
INTERVAL = "1d"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except:
        pass

def is_real_breakout(df):
    bb = BollingerBands(df["Close"], 20, 2.0)
    bb_l = bb.bollinger_lband()
    bb_m = bb.bollinger_mavg()
    rsi = RSIIndicator(df["Close"], 14).rsi()
    close = df["Close"].iloc[-1]
    high = df["High"].iloc[-1]
    prev_close = df["Close"].iloc[-2]
    curr_bb_l = bb_l.iloc[-1]
    prev_bb_l = bb_l.iloc[-2]
    curr_bb_m = bb_m.iloc[-1]
    curr_rsi = rsi.iloc[-1]
    vol = df["Volume"].iloc[-1]
    avg_vol = df["Volume"].rolling(20).mean().iloc[-1]
    cond = close < curr_bb_l and high < curr_bb_l and prev_close > prev_bb_l and curr_rsi < 25 and vol > avg_vol * 1.5
    return cond, curr_bb_m

st.title("Bollinger Real Breakout Scanner - 1D")

if st.button("Scan Full List"):
    tickers = ["AAPL","MSFT","NVDA","TSLA","AMD","META","GOOGL","SPY","QQQ"]
    for t in tickers:
        df = yf.download(t, period=PERIOD, interval=INTERVAL, progress=False)
        if len(df) < 30:
            continue
        cond, tp = is_real_breakout(df)
        if cond:
            close = float(df["Close"].iloc[-1])
            pct = ((tp - close) / close) * 100
            msg = f"{t} פריצה אמיתית ${close:.2f} -> TP {tp:.2f} (+{pct:.2f}%)"
            st.success(msg)
            send_telegram(msg)
