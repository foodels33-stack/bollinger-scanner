import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
import plotly.graph_objects as go
import time
from datetime import datetime

st.set_page_config(page_title="FULL Down Only PRO AUTO", layout="wide")
if "ok" not in st.session_state:
    st.session_state.ok=False
    st.session_state.found_db=set()
    st.session_state.history=[]
    st.session_state.pending_breaks={}
    st.session_state.last_scan_time=None
    st.session_state.last_heartbeat=0
    st.session_state.auto_scan=False
    st.session_state.scan_count=0
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

st.sidebar.divider()
st.sidebar.subheader("אוטומציה")
st.session_state.auto_scan=st.sidebar.toggle("הפעל סריקה אוטומטית 24/7", value=st.session_state.auto_scan)
AUTO_SEC=st.sidebar.slider("כל כמה שניות", 60, 600, 300, step=30)
HEARTBEAT_MIN=st.sidebar.slider("Heartbeat כל כמה דקות", 15, 120, 60)

if st.sidebar.button("נקה היסטוריה"):
    st.session_state.found_db=set()
    st.session_state.history=[]
    st.session_state.pending_breaks={}
    st.sidebar.success("נוקה")

@st.cache_data(ttl=3600)
def get_tickers():
    tickers=[]
    urls=[
        "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all_tickers.txt",
        "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nasdaq/nasdaq_tickers.txt"
    ]
    for url in urls:
        try:
            df=pd.read_csv(url, header=None)
            lst=df.iloc[:,0].dropna().astype(str).str.strip().str.upper().tolist()
            tickers.extend(lst)
        except:
            pass
    tickers=list(dict.fromkeys(tickers))
    if len(tickers)<100:
        tickers=["AAPL","MSFT","NVDA","TSLA","SPY","QQQ","META","GOOGL","AMZN","BTC-USD","ETH-USD","SOL-USD","NFLX","AMD","INTC","BA","NIO","PLTR","SOFI","MARA","COIN","RIVN","LCID","F","T","PFE","MRNA","GME","AMC","DKNG","UBER","LYFT","SNAP","SHOP","SQ","PYPL","ROKU","ZM","DOCU","CRWD","DDOG","NET","SNOW","AI","UPST","AFRM","SMR","NU","GRAB","JOBY","OPEN","CLOV","WISH","BBBY","DWAC"]
    return tickers
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
        if tkr in ["BTC","ETH","SOL","DOGE","XRP","BNB","ADA","AVAX"]:
            tkr=tkr+"-USD"
        per="2y" if INTERVAL=="1d" else "60d" if INTERVAL=="1h" else "20d"
        df=None
        try:
            df=yf.Ticker(tkr).history(period=per, interval=INTERVAL, auto_adjust=True)
        except:
            df=None
        if df is None or len(df)<30:
            try:
                df=yf.download(tkr, period=per, interval=INTERVAL, progress=False, auto_adjust=True, threads=False)
            except:
                df=None
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
        c=float(df["Close"].iloc[-1]); ph=float(df["High"].iloc[-2]); pl=float(df["Low"].iloc[-2]); pc=float(df["Close"].iloc[-2])
        bl=float(df["BB_L"].iloc[-1]); pbl=float(df["BB_L"].iloc[-2]); bm=float(df["BB_M"].iloc[-1])
        crsi=float(df["RSI"].iloc[-1]); prsi=float(df["RSI"].iloc[-2])
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
        stopped_break=(c>pc) and (l>float(df["Low"].iloc[-2])) and (crsi>prsi)
        return {"tkr": real_tkr, "price": round(c,2), "low": round(l,4), "tp": round(bm,2), "pct": round(pct,2), "rsi": round(crsi,1), "interval": INTERVAL, "df": df, "is_break": is_break, "stopped": stopped_break, "close": c}
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

st.title("FULL BREAK DOWN ONLY - PRO AUTO + BUY SIGNAL")
st.caption(f"טיקרים זמינים: {len(ALL_TICKERS)} | סריקה אוטומטית: {'🟢 פעיל' if st.session_state.auto_scan else '🔴 כבוי'}")
if st.session_state.last_scan_time:
    st.info(f"⏱️ סריקה אחרונה: {st.session_state.last_scan_time} | סריקות שבוצעו: {st.session_state.scan_count} | ממתין לאישור נעצר: {len(st.session_state.pending_breaks)} | אונליין: ✅")

c1,c2=st.columns(2)
with c1:
    manual=st.text_input("הכנס טיקר לגרף", placeholder="TSLA / BTC")
with c2:
    st.write("")
    st.write("")
    btn=st.button("בדוק + גרף", use_container_width=True, type="primary")

if btn and manual:
    r=check(manual)
    if r and r["df"] is not None:
        if r["is_break"]:
            key=f"{r['tkr']}_{r['interval']}_{r['price']}"
            if key not in st.session_state.found_db:
                st.session_state.found_db.add(key)
                st.session_state.history.append({k:v for k,v in r.items() if k!='df'})
                st.session_state.pending_breaks[r['tkr']]={'low': r['low'], 'price': r['price'], 'time': str(datetime.now())}
            m=f"🔴 FULL BREAK {r['tkr']} ${r['price']} -> {r['tp']} (+{r['pct']}%) RSI {r['rsi']} | ממתין לנעצר"
            st.success(m)
            tg(m)
        else:
            st.info(f"{r['tkr']} אין פריצה מלאה - מחיר ${r['price']} RSI {r['rsi']} | מציג גרף לבדיקה")
        plot_chart(r["df"], r["tkr"])
    else:
        st.error("אין דאטה - נסה שוב או טיקר אחר, Yahoo חסם זמנית")

st.divider()

def run_one_scan():
    new_break=0
    new_buy=0
    for tk in ALL_TICKERS[:NUM_SCAN]:
        r=check(tk)
        if not r:
            continue
        if r["is_break"]:
            key=f"{r['tkr']}_{r['interval']}_{r['price']}"
            if key not in st.session_state.found_db:
                st.session_state.found_db.add(key)
                st.session_state.history.append({k:v for k,v in r.items() if k!='df'})
                st.session_state.pending_breaks[r['tkr']]={'low': r['low'], 'price': r['price'], 'time': str(datetime.now())}
                new_break+=1
                m=f"🔴 FULL BREAK {r['tkr']} ${r['price']} -> {r['tp']} (+{r['pct']}%) RSI {r['rsi']} [{INTERVAL}]"
                tg(m)
        if r['tkr'] in st.session_state.pending_breaks:
            prev=st.session_state.pending_breaks[r['tkr']]
            if r['stopped'] and r['low'] > prev['low']:
                new_buy+=1
                m=f"🟢 הפריצה נעצרה - איתות קנייה {r['tkr']}\nפריצה הייתה ב-${prev['low']} מחיר פריצה ${prev['price']}\nעכשיו ${r['price']} RSI {r['rsi']}\nזה האיתות שלך לקנות!"
                tg(m)
                del st.session_state.pending_breaks[r['tkr']]
    st.session_state.last_scan_time=datetime.now().strftime("%H:%M:%S %d/%m")
    st.session_state.scan_count+=1
    return new_break, new_buy

if st.button(f"סרוק {NUM_SCAN} עכשיו", use_container_width=True):
    prog=st.progress(0); stat=st.empty()
    new_b=0; new_buy=0
    for i, tk in enumerate(ALL_TICKERS[:NUM_SCAN]):
        stat.text(f"{i+1}/{NUM_SCAN} {tk}")
        prog.progress((i+1)/NUM_SCAN)
        r=check(tk)
        if r and r["is_break"]:
            key=f"{r['tkr']}_{r['interval']}_{r['price']}"
            if key not in st.session_state.found_db:
                st.session_state.found_db.add(key)
                st.session_state.history.append({k:v for k,v in r.items() if k!='df'})
                st.session_state.pending_breaks[r['tkr']]={'low': r['low'], 'price': r['price'], 'time': str(datetime.now())}
                new_b+=1
                m=f"🔴 FULL BREAK {r['tkr']} ${r['price']} -> {r['tp']} (+{r['pct']}%)"
                st.success(m)
                tg(m)
                with st.expander(f"גרף {r['tkr']}"):
                    plot_chart(r["df"], r["tkr"])
        if r and r['tkr'] in st.session_state.pending_breaks and r['stopped']:
            prev=st.session_state.pending_breaks[r['tkr']]
            if r['low'] > prev['low']:
                new_buy+=1
                m=f"🟢 הפריצה נעצרה - קנייה {r['tkr']} ${r['price']}"
                st.success(m)
                tg(f"🟢 הפריצה נעצרה - איתות קנייה {r['tkr']} עכשיו ${r['price']}")
                del st.session_state.pending_breaks[r['tkr']]
    prog.empty(); stat.empty()
    st.session_state.last_scan_time=datetime.now().strftime("%H:%M:%S")
    st.session_state.scan_count+=1
    if new_b==0 and new_buy==0:
        st.warning("לא נמצאו פריצות חדשות")

if st.session_state.auto_scan:
    st.warning(f"🤖 אוטומציה פעילה - סורק כל {AUTO_SEC} שניות - רענון אוטומטי")
    nb, nbuy = run_one_scan()
    st.write(f"נסרקו {NUM_SCAN} | פריצות חדשות: {nb} | איתותי קנייה: {nbuy}")
    now=time.time()
    if now - st.session_state.last_heartbeat > HEARTBEAT_MIN*60:
        tg(f"✅ סורק חי - {datetime.now().strftime('%H:%M')} - נסרקו {NUM_SCAN} מניות - ממתין לנעצר: {len(st.session_state.pending_breaks)} - סריקה #{st.session_state.scan_count}")
        st.session_state.last_heartbeat=now
    time.sleep(AUTO_SEC)
    st.rerun()

if st.session_state.history:
    st.subheader(f"היסטוריה {len(st.session_state.history)}")
    dfh=pd.DataFrame(st.session_state.history[::-1])
    st.dataframe(dfh.drop(columns=['df'], errors='ignore'), use_container_width=True)
    sel=st.selectbox("בחר מההיסטוריה לגרף", dfh["tkr"].tolist())
    if st.button("הצג גרף מהיסטוריה"):
        d,_=get_data(sel)
        if d is not None:
            plot_chart(d, sel)

st.sidebar.divider()
st.sidebar.caption(f"סטטוס: {st.session_state.last_scan_time or 'לא נסרק'} | אונליין: {'✅' if st.session_state.auto_scan else 'OFF'}")
