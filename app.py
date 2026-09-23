import streamlit as st
import yfinance as yf
import pandas as pd
import importlib
import requests
m1 = http://importlib.import_module("ta.volatility")
m2 = http://importlib.import_module("ta.momentum")
BollingerBands = http://m1.BollingerBands
RSIIndicator = http://m2.RSIIndicator
http://st.set_page_config(page_title="Bollinger FULL Down Only", layout="wide")
ADMIN_PASS = "1234"
if "admin" not in http://st.session_state:
    http://st.session_state.admin = False
if not http://st.session_state.admin:
    p = http://st.text_input("סיסמת מנהל", type="password")
    if http://st.button("כניסה"):
        if p == ADMIN_PASS:
            http://st.session_state.admin = True
            http://st.rerun()
        else:
            http://st.error("סיסמה שגויה")
    http://st.stop()
http://st.sidebar.title("הגדרות")
TELEGRAM_TOKEN = http://st.sidebar.text_input("Bot Token", type="password")
TELEGRAM_CHAT_ID = http://st.sidebar.text_input("Chat ID")
def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = "https://api.telegram.org/bot{}/sendMessage".format(TELEGRAM_TOKEN)
        r = http://requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
        return http://r.status_code == 200
    except:
        return False
INTERVAL = http://st.sidebar.selectbox("אינטרוול", ["1d","1h","15m"], index=0)
RSI_LIMIT = http://st.sidebar.slider("RSI חייב להיות מתחת ל", 10, 40, 25)
VOL_MULT = http://st.sidebar.slider("מכפיל ווליום", 1.0, 3.0, 1.5)
search = http://st.sidebar.text_input("בדוק טיקר ידני")
@st.cache_data
def get_tickers():
    try:
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all_tickers.txt"
        df = http://pd.read_csv(url, header=None)
        tickers = http://df.iloc[:,0].tolist()
        return tickers[:3500]
    except:
        return ["AAPL","MSFT","NVDA","TSLA","BTC-USD","ETH-USD","SOL-USD","SPY","QQQ"]
ALL = get_tickers()
def norm(t):
    t = http://t.upper().strip()
    if t in ["BTC","ETH","SOL","DOGE","XRP","AVAX","ADA","BNB"]:
        return t + "-USD"
    return t
def check_full_break(ticker, interval):
    try:
        ticker = norm(ticker)
        per = "2y" if interval == "1d" else "60d" if interval == "1h" else "10d"
        df = http://yf.download(ticker, period=per, interval=interval, progress=False, auto_adjust=True)
        if len(df) < 35:
            return None
        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        open_ = df["Open"]
        bb = BollingerBands(close, 20, 2.0)
        bb_l = http://bb.bollinger_lband()
        bb_m = http://bb.bollinger_mavg()
        rsi = RSIIndicator(close, 14).rsi()
        c = float(close.iloc[-1])
        o = float(open_.iloc[-1])
        h = float(high.iloc[-1])
        l = float(low.iloc[-1])
        pc = float(close.iloc[-2])
        po = float(open_.iloc[-2])
        ph = float(high.iloc[-2])
        pl = float(low.iloc[-2])
        c_bl = float(bb_l.iloc[-1])
        p_bl = float(bb_l.iloc[-2])
        c_bm = float(bb_m.iloc[-1])
        c_rsi = float(rsi.iloc[-1])
        is_crypto = "-USD" in ticker
        body_low_now = min(o, c)
        full_break_now = (h < c_bl) and (l < c_bl) and (o < c_bl) and (c < c_bl) and (body_low_now < c_bl)
        prev_inside = (ph > p_bl) or (pl > p_bl) or (po > p_bl) or (pc > p_bl)
        filter_rsi = c_rsi < RSI_LIMIT
        if not is_crypto:
            vol = float(df["Volume"].iloc[-1])
            avg_vol = float(df["Volume"].rolling(20).mean().iloc[-1])
            filter_vol = vol > (avg_vol _ VOL_MULT)
        else:
            filter_vol = True
        if full_break_now and prev_inside and filter_rsi and filter_vol:
            pct = ((c_bm - c) / c) _ 100
            return {"ticker": ticker, "price": c, "tp": c_bm, "pct": pct, "rsi": c_rsi}
    except:
        return None
    return None
http://st.title("FULL BREAK DOWN ONLY - כל הגוף + זנב")
if search:
    r = check_full_break(search, INTERVAL)
    if r:
        msg = "FULL BREAK {} ${:.2f} RSI:{:.1f} -> TP {:.2f} (+{:.1f}%)".format(r['ticker'], r['price'], r['rsi'], r['tp'], r['pct'])
        http://st.success(msg)
        send_telegram(msg)
    else:
        http://st.info("אין פריצה מלאה")
if http://st.button("סרוק {} מניות".format(len(ALL))):
    prog = http://st.progress(0)
    txt = http://st.empty()
    res_list = []
    for i, t in enumerate(ALL):
        http://txt.text("{}/{} {}".format(i+1, len(ALL), t))
        http://prog.progress((i+1)/len(ALL))
        r = check_full_break(t, INTERVAL)
        if r:
            res_list.append(r)
            msg = "FULL BREAK {} [{}] ${:.2f} -> TP {:.2f} (+{:.1f}%) RSI:{:.1f}".format(r['ticker'], INTERVAL, r['price'], r['tp'], r['pct'], r['rsi'])
            http://st.success(msg)
            send_telegram(msg)
    if res_list:
        http://st.dataframe(pd.DataFrame(res_list))
    else:
        http://st.warning("אין פריצות מלאות כרגע")
