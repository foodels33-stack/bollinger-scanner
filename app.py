import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
import plotly.graph_objects as go
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
DEFAULT_CHAT="6649894327"
BOT=st.sidebar.text_input("Bot Token", value=DEFAULT_BOT, type="password")
CHAT=st.sidebar.text_input("Chat ID", value=DEFAULT_CHAT)
if st.sidebar.button("TEST BOT"):
    try:
        r=requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id": CHAT, "text": "TEST PRO GRAPH - עובד"}, timeout=15)
        st.sidebar.write(f"Code: {r.status_code}")
        if r.status_code==200:
            st.sidebar.success("עובד!")
        else:
            st.sidebar.error(r.text)
    except Exception as e:
        st.sidebar.error(str(e))
INTERVAL=st.sidebar.selectbox("Interval", ["1d","1h","15m"], index=0)
RSI_L=st.sidebar.slider("RSI under", 10, 40, 25)
VOL_M=st.sidebar.slider("Vol X", 1.0, 3.0, 1.5)
NUM_SCAN=st.sidebar.slider("How many to scan", 10, 3500, 200, step=10)
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
def get_data(tkr):
    try:
        tkr=tkr.strip().upper()
        if tkr in ["BTC","ETH","SOL","DOGE","XRP","BNB","ADA"]:
            tkr=tkr+"-USD"
        per="2y" if INTERVAL=="1d" else "60d" if INTERVAL=="1h" else "20d"
        df=yf.download(tkr, period=per, interval=INTERVAL, progress=False, auto_adjust=True, threads=False)
        if df is None or len(df)<30:
            return None, None
        close=df["Close"]
        if isinstance(close, pd.DataFrame):
            close=close.iloc[:,0]
        df["BB_L"]=BollingerBands(close, 20, 2).bollinger_lband()
        df["BB_M"]=BollingerBands(close, 20, 2).bollinger_mavg()
        df["BB_H"]=BollingerBands(close, 20, 2).bollinger_hband()
        df["RSI"]=RSIIndicator(close, 14).rsi()
        return df.tail(150), tkr
    except:
        return None, None
def check(tkr):
    df, real_tkr=get_data(tkr)
    if df is None:
        return None
    try:
        h=float(df["High"].iloc[-1]); l=float(df["Low"].iloc[-1]); o=float(df["Open"].iloc[-1])
        c=float(df["Close"].iloc[-1]); ph=float(df["High"].iloc[-2]); pl=float(df["Low"].iloc[-2])
        bl=float(df["BB_L"].iloc[-1]); pbl=float(df["BB_L"].iloc[-2]); bm=float(df["BB_M"].iloc[-1])
        crsi=float(df["RSI"].iloc[-1])
        if pd.isna(bl) or pd.isna(pbl):
            return None
        full_break=(h<bl) and (l<bl) and (o<bl) and (c<bl)
        prev_inside=(ph>pbl) or (pl>pbl)
        vol_ok=True
        if "-USD" not in real_tkr:
            v=float(df["Volume"].iloc[-1]); av=float(df["Volume"].rolling(20).mean().iloc[-1])
            vol_ok=v>av*VOL_M
        pct=(bm-c)/c*100 if c!=0 else 0
        is_break=full_break and prev_inside and (crsi<RSI_L) and vol_ok
        return {"tkr": real_tkr, "price": round(c,2), "tp": round(bm,2), "pct": round(pct,2), "rsi": round(crsi,1), "interval": INTERVAL, "df": df, "is_break": is_break}
    except:
        return None
def plot_chart(df, tkr):
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name=tkr))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_H'], line=dict(color='rgba(255,0,0,0.3)'), name="BB Upper"))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_L'], line=dict(color='rgba(0,255,0,0.7)', width=2), name="BB Lower"))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_M'], line=dict(color='orange', dash='dash'), name="TP"))
    fig.update_layout(height=550, title=f"{tkr} - {INTERVAL}", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    fig2=go.Figure()
    fig2.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI"))
    fig2.add_hline(y=RSI_L, line_dash="dash", line_color="red")
    fig2.update_layout(height=200, title="RSI")
    st.plotly_chart(fig2, use_container_width=True)
st.title("FULL BREAK DOWN ONLY - PRO + GRAPH")
c1,c2=st.columns([3,1])
with c1:
    manual=st.text_input("הכנס טיקר לגרף", placeholder="TSLA / BTC")
with c2:
    st.write(""); st.write("")
    btn=st.button("בדוק + גרף", use_container_width=True, type="primary")
if btn and manual:
    r=check(manual)
    if r and r["df"] is not None:
        if r["is_break"]:
            key=f"{r['tkr']}_{r['interval']}_{r['price']}"
            if key not in st.session_state.found_db:
                st.session_state.found_db.add(key)
                st.session_state.history.append({k:v for k,v in r.items() if k!='df'})
            m=f"FULL BREAK {r['tkr']} ${r['price']} -> {r['tp']} (+{r['pct']}%) RSI {r['rsi']}"
            st.success(m)
            tg(m)
        else:
            st.info(f"{r['tkr']} אין פריצה מלאה - מחיר ${r['price']} RSI {r['rsi']} | מציג גרף לבדיקה")
        plot_chart(r["df"], r["tkr"])
    else:
        st.error("אין דאטה")
st.divider()
if st.button(f"סרוק {NUM_SCAN}", use_container_width=True):
    prog=st.progress(0); stat=st.empty(); new=0
    for i, tk in enumerate(ALL_TICKERS[:NUM_SCAN]):
        stat.text(f"{i+1}/{NUM_SCAN} {tk}")
        prog.progress((i+1)/NUM_SCAN)
        r=check(tk)
        if r and r["is_break"]:
            key=f"{r['tkr']}_{r['interval']}_{r['price']}"
            if key not in st.session_state.found_db:
                st.session_state.found_db.add(key)
                st.session_state.history.append({k:v for k,v in r.items() if k!='df'})
                new+=1
                m=f"FULL BREAK {r['tkr']} ${r['price']} -> {r['tp']} (+{r['pct']}%)"
                st.success(m)
                tg(m)
                with st.expander(f"גרף {r['tkr']}"):
                    plot_chart(r["df"], r["tkr"])
    prog.empty(); stat.empty()
    if new==0:
        st.warning("לא נמצאו פריצות חדשות")
if st.session_state.history:
    st.subheader(f"היסטוריה {len(st.session_state.history)}")
    dfh=pd.DataFrame(st.session_state.history[::-1])
    st.dataframe(dfh, use_container_width=True)
    sel=st.selectbox("בחר מההיסטוריה לגרף", dfh["tkr"].tolist())
    if st.button("הצג גרף מהיסטוריה"):
        d,_=get_data(sel)
        if d is not None:
            plot_chart(d, sel)
