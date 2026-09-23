import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator

st.set_page_config(page_title="FULL Down Only PRO", layout="wide")

if "ok" not in st.session_state:
    st.session_state.ok=False
    st.session_state.found_db=set()
    st.session_state.history=[]

if not st.session_state.ok:
    p=st.text_input("Password", type="password")
    if st.button("Login"):
        if p=="1234":
            st.session_state.ok=True
            st.rerun()
    st.stop()

DEFAULT_BOT="8777322821:AAFi4SikdUit4WJ3vEAUbYhBU0dp1KrBsuw"
BOT=st.sidebar.text_input("Bot Token", value=DEFAULT_BOT, type="password")
CHAT=st.sidebar.text_input("Chat ID")

if st.sidebar.button("TEST BOT"):
    try:
        r=requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id": CHAT, "text": "PRO TEST - עובד ✅"}, timeout=15)
        if r.status_code==200:
            st.sidebar.success("עובד!")
        else:
            st.sidebar.error(r.text)
    except Exception as e:
        st.sidebar.error(str(e))

INTERVAL=st.sidebar.selectbox("Interval", ["1d","1h","15m"], index=0)
RSI_L=st.sidebar.slider("RSI under", 10, 40, 25)
VOL_M=st.sidebar.slider("Vol X", 1.0, 3.0, 1.5)
NUM_SCAN=st.sidebar.slider("כמה לסרוק", 10, 3500, 200, step=10)

if st.sidebar.button("נקה היסטוריה"):
    st.session_state.found_db=set()
    st.session_state.history=[]
    st.sidebar.success("נוקה")

@st.cache_data(ttl=3600)
def get_tickers():
    try:
        url="https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all_tickers.txt"
        df=pd.read_csv(url, header=None)
        return df.iloc[:,0].dropna().astype(str).tolist()
    except:
        return ["AAPL","MSFT","NVDA","TSLA","SPY","QQQ","META","GOOGL","AMZN","BTC-USD","ETH-USD","SOL-USD"]

ALL_TICKERS=get_tickers()

def tg(m):
    if not BOT or not CHAT:
        return
    try:
        requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id": CHAT, "text": m}, timeout=10)
    except:
        pass

def check(tkr):
    try:
        tkr=tkr.strip().upper()
        if tkr in ["BTC","ETH","SOL","DOGE","XRP","BNB","ADA","AVAX"]:
            tkr=tkr+"-USD"
        per="2y" if INTERVAL=="1d" else "60d" if INTERVAL=="1h" else "20d"
        df=yf.download(tkr, period=per, interval=INTERVAL, progress=False, auto_adjust=True, threads=False)
        if df is None or len(df)<30:
            return None
        close=df["Close"]
        if isinstance(close, pd.DataFrame):
            close=close.iloc[:,0]
        if close.isna().all():
            return None
        bb_l=BollingerBands(close, 20, 2).bollinger_lband()
        bb_m=BollingerBands(close, 20, 2).bollinger_mavg()
        rsi=RSIIndicator(close, 14).rsi()
        h=float(df["High"].iloc[-1])
        l=float(df["Low"].iloc[-1])
        o=float(df["Open"].iloc[-1])
        c=float(close.iloc[-1])
        ph=float(df["High"].iloc[-2])
        pl=float(df["Low"].iloc[-2])
        bl=float(bb_l.iloc[-1])
        pbl=float(bb_l.iloc[-2])
        bm=float(bb_m.iloc[-1])
        crsi=float(rsi.iloc[-1])
        if pd.isna(bl) or pd.isna(pbl) or pd.isna(bm):
            return None
        full_break=(h<bl) and (l<bl) and (o<bl) and (c<bl)
        prev_inside=(ph>pbl) or (pl>pbl)
        vol_ok=True
        if "-USD" not in tkr:
            v=float(df["Volume"].iloc[-1])
            av=float(df["Volume"].rolling(20).mean().iloc[-1])
            if pd.isna(v) or pd.isna(av):
                vol_ok=False
            else:
                vol_ok=v>av*VOL_M
        if full_break and prev_inside and (crsi<RSI_L) and vol_ok:
            pct=(bm-c)/c*100 if c!=0 else 0
            return {"tkr": tkr, "price": round(c,2), "tp": round(bm,2), "pct": round(pct,2), "rsi": round(crsi,1), "interval": INTERVAL}
    except:
        return None
    return None

st.title("FULL BREAK DOWN ONLY - PRO Stable")

col1,col2=st.columns([3,1])
with col1:
    manual=st.text_input("בדיקת טיקר ידני")
with col2:
    st.write("")
    st.write("")
    check_btn=st.button("בדוק טיקר", use_container_width=True)

if check_btn and manual:
    with st.spinner(f"בודק {manual}..."):
        r=check(manual)
        if r:
            key=f"{r['tkr']}_{r['interval']}_{r['price']}"
            if key not in st.session_state.found_db:
                st.session_state.found_db.add(key)
                st.session_state.history.append(r)
            m=f"FULL BREAK {r['tkr']} {r['interval']} ${r['price']} -> TP {r['tp']} (+{r['pct']}%) RSI {r['rsi']}"
            st.success(m)
            tg(m)
        else:
            st.info(f"אין פריצה מלאה ל {manual.upper()} - נר לא כולו מתחת לרצועה")

st.divider()

scan_btn=st.button(f"סרוק {NUM_SCAN} מניות", type="primary", use_container_width=True)

if scan_btn:
    prog=st.progress(0)
    stat=st.empty()
    new_found=0
    for i, tk in enumerate(ALL_TICKERS[:NUM_SCAN]):
        stat.text(f"{i+1}/{NUM_SCAN} - {tk}")
        prog.progress((i+1)/NUM_SCAN)
        r=check(tk)
        if r:
            key=f"{r['tkr']}_{r['interval']}_{r['price']}"
            if key not in st.session_state.found_db:
                st.session_state.found_db.add(key)
                st.session_state.history.append(r)
                new_found+=1
                m=f"FULL BREAK {r['tkr']} ${r['price']} -> {r['tp']} (+{r['pct']}%) RSI {r['rsi']}"
                st.success(m)
                tg(m)
    prog.empty()
    stat.empty()
    if new_found==0:
        st.warning("סריקה הסתיימה - לא נמצאו פריצות חדשות")
    else:
        tg(f"סריקה הסתיימה - {new_found} פריצות חדשות")

if st.session_state.history:
    st.subheader(f"היסטוריה ({len(st.session_state.history)})")
    st.dataframe(pd.DataFrame(st.session_state.history[::-1]), use_container_width=True)
