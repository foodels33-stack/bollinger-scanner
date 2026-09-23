import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
st.set_page_config(page_title="FULL Down Only", layout="wide")
if "ok" not in st.session_state:
    st.session_state.ok=False
if not st.session_state.ok:
    p=st.text_input("Password", type="password")
    if st.button("Login"):
        if p=="1234":
            st.session_state.ok=True
            st.rerun()
    st.stop()
BOT=st.sidebar.text_input("Bot Token", type="password")
CHAT=st.sidebar.text_input("Chat ID")
INTERVAL=st.sidebar.selectbox("Interval", ["1d","1h","15m"])
RSI_L=st.sidebar.slider("RSI under", 10, 40, 25)
VOL_M=st.sidebar.slider("Vol X", 1.0, 3.0, 1.5)
def tg(m):
    if not BOT or not CHAT:
        return
    try:
        requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id": CHAT, "text": m}, timeout=10)
    except:
        pass
def check(tkr):
    try:
        df=yf.download(tkr, period="2y" if INTERVAL=="1d" else "60d", interval=INTERVAL, progress=False, auto_adjust=True)
        if len(df)<30:
            return None
        bb_l=BollingerBands(df["Close"], 20, 2).bollinger_lband()
        bb_m=BollingerBands(df["Close"], 20, 2).bollinger_mavg()
        rsi=RSIIndicator(df["Close"], 14).rsi()
        h=float(df["High"].iloc[-1])
        l=float(df["Low"].iloc[-1])
        o=float(df["Open"].iloc[-1])
        c=float(df["Close"].iloc[-1])
        ph=float(df["High"].iloc[-2])
        pl=float(df["Low"].iloc[-2])
        bl=float(bb_l.iloc[-1])
        pbl=float(bb_l.iloc[-2])
        bm=float(bb_m.iloc[-1])
        crsi=float(rsi.iloc[-1])
        full_break=(h<bl) and (l<bl) and (o<bl) and (c<bl)
        prev_inside=(ph>pbl) or (pl>pbl)
        vol_ok=True
        if "-USD" not in tkr:
            v=float(df["Volume"].iloc[-1])
            av=float(df["Volume"].rolling(20).mean().iloc[-1])
            vol_ok=v>av*VOL_M
        if full_break and prev_inside and (crsi<RSI_L) and vol_ok:
            pct=(bm-c)/c*100
            return {"tkr": tkr, "c": c, "tp": bm, "pct": pct, "rsi": crsi}
    except:
        return None
    return None
t=st.sidebar.text_input("Manual ticker")
if t:
    r=check(t.upper())
    if r:
        m=f"FULL BREAK {r['tkr']} {INTERVAL} ${r['c']:.2f} -> TP {r['tp']:.2f} (+{r['pct']:.1f}%) RSI {r['rsi']:.1f}"
        st.success(m)
        tg(m)
    else:
        st.info("No full break")
if st.button("Scan"):
    tickers=["AAPL","MSFT","NVDA","TSLA","BTC-USD","ETH-USD","SOL-USD","SPY","QQQ","META","GOOGL","AMZN"]
    for tk in tickers:
        r=check(tk)
        if r:
            m=f"FULL BREAK {r['tkr']} ${r['c']:.2f} -> {r['tp']:.2f} (+{r['pct']:.1f}%)"
            st.write(m)
            tg(m)
