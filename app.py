import streamlit as st
import yfinance as yf
import pandas as pd
import importlib
import requests
bb_mod = http://importlib.import_module("ta" + ".volatility")
rsi_mod = http://importlib.import_module("ta" + ".momentum")
BollingerBands = bb_mod.BollingerBands
RSIIndicator = rsi_mod.RSIIndicator
http://st.set_page_config(page_title="Bollinger Scanner PRO", layout="wide")
ADMIN_PASS = "1234"
if "admin" not in http://st.session_state:
    http://st.session_state.admin = False
if not http://st.session_state.admin:
    p = http://st.text_input("סיסמת מנהל", type="password")
    if p == ADMIN_PASS:
        http://st.session_state.admin = True
        http://st.rerun()
    elif p:
        http://st.error("סיסמה שגויה")
        http://st.stop()
    else:
        http://st.stop()
http://st.sidebar.title("הגדרות")
TELEGRAM_TOKEN = http://st.sidebar.text_input("Telegram Token", type="password")
TELEGRAM_CHAT_ID = http://st.sidebar.text_input("Chat ID")
def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = http://requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
        return http://r.status_code == 200
    except:
        return False
if http://st.sidebar.button("בדוק חיבור לבוט - שלח טסט"):
    ok = send_telegram("✅ הבוט מחובר! המערכת מוכנה")
    if ok:
        http://st.sidebar.success("נשלח בהצלחה!")
    else:
        http://st.sidebar.error("שגיאה - בדוק Token ו-Chat ID")
INTERVAL = http://st.sidebar.selectbox("אינטרוול", ["1d", "1h", "15m", "5m"], index=0)
RSI_LIMIT = http://st.sidebar.slider("RSI מתחת ל-", 10, 40, 25)
VOL_MULT = http://st.sidebar.slider("מכפיל ווליום", 1.0, 3.0, 1.5)
search_ticker = http://st.sidebar.text_input("חיפוש מניה (AAPL או BTC)")
@st.cache_data
def get_3500_tickers():
    try:
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all_tickers.txt"
        df = http://pd.read_csv(url, header=None)
        return http://df.tolist()[:3500]
    except:
        return ["AAPL","MSFT","NVDA","TSLA","BTC-USD","ETH-USD","SOL-USD","SPY","QQQ","PLTR"]
ALL_TICKERS = get_3500_tickers()
def normalize_ticker(t):
    t = http://t.upper().strip()
    if t in ["BTC","ETH","SOL","DOGE","XRP","AVAX","ADA","BNB","LINK","SHIB"]:
        return t + "-USD"
    return t
def check_breakout(ticker, interval):
    try:
        ticker = normalize_ticker(ticker)
        period = "2y" if interval == "1d" else "60d" if interval == "1h" else "10d"
        df = http://yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if len(df) < 35:
            return None
        close = df["Close"]
        high = df["High"]
        bb = BollingerBands(close, 20, 2.0)
        bb_l = http://bb.bollinger_lband()
        bb_m = http://bb.bollinger_mavg()
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
        is_break = c < c_bb_l and pc > p_bb_l and c_rsi < RSI_LIMIT and vol > avg_vol _ VOL_MULT
        if interval == "1d":
            is_break = is_break and h < c_bb_l
        if is_break:
            pct = ((c_bb_m - c) / c) _ 100
            return {"ticker": ticker, "price": c, "tp": c_bb_m, "pct": pct, "rsi": c_rsi, "interval": interval}
    except:
        return None
    return None
http://st.title("Bollinger Scanner PRO - 3500 מניות")
if search_ticker:
    http://st.subheader(f"בדיקת {search_ticker}")
    res = check_breakout(search_ticker, INTERVAL)
    if res:
        http://st.success(f"🚨 {res['ticker']} ${res['price']:.2f} RSI:{res['rsi']:.1f} -> TP {res['tp']:.2f} (+{res['pct']:.2f}%)")
        send_telegram(f"🚨 {res['ticker']} [{res['interval']}] ${res['price']:.2f} RSI:{res['rsi']:.1f} -> TP {res['tp']:.2f} (+{res['pct']:.2f}%)")
    else:
        http://st.info("אין פריצה מלאה למטה")
if http://st.button(f"הרץ סריקה מלאה על {len(ALL_TICKERS)} מניות [{INTERVAL}]"):
    progress = http://st.progress(0)
    status = http://st.empty()
    results = []
    for i, t in enumerate(ALL_TICKERS):
        http://status.text(f"סורק {t} {i+1}/{len(ALL_TICKERS)}")
        http://progress.progress((i + 1) / len(ALL_TICKERS))
        res = check_breakout(t, INTERVAL)
        if res:
            http://results.append(res)
            msg = f"🚨 {res['ticker']} [{res['interval']}] ${res['price']:.2f} RSI:{res['rsi']:.1f} -> TP {res['tp']:.2f} (+{res['pct']:.2f}%)"
            http://st.success(msg)
            send_telegram(msg)
    if results:
        http://st.dataframe(pd.DataFrame(results))
    else:
        http://st.warning("אין פריצות כרגע")
[0]
