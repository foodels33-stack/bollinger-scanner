import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
import plotly.graph_objects as go
import time
from datetime import datetime
import random
import streamlit.components.v1 as components

st.set_page_config(page_title="FULL Down Only PRO AUTO", layout="wide")

ANTI SLEEP - PING SELF EVERY 60 SEC TO KEEP STREAMLIT AWAKE
components.html("""
<script>
setInterval(() => {
  fetch(window.location.href, {mode:'no-cors'}).then(()=>console.log('keepalive ping'));
}, 60000);
setInterval(() => {
  window.parent.document.title = "LIVE SCANNER - " + new Date().toLocaleTimeString();
}, 1000);
</script>
""", height=0)

UptimeRobot keepalive endpoint
if "ping" in st.query_params:
    st.write("alive")
    st.stop()

if "ok" not in st.session_state:
    st.session_state.ok=False
    st.session_state.found_db=set()
    st.session_state.history=[]
    st.session_state.pending_breaks={}
    st.session_state.last_scan_time=None
    st.session_state.last_heartbeat=0
    st.session_state.auto_scan=False
    st.session_state.scan_count=0
    st.session_state.last_random_batch=[]
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
st.sidebar.subheader("תוספת חדשה - סריקת ערב לפני")
SCAN_2245=st.sidebar.checkbox("🔍 סריקת אתמול 22:45 (15 דק' לפני סגירה) - V = ערב לפני / בלי V = אונליין")

st.sidebar.divider()
st.sidebar.subheader("אוטומציה")
st.session_state.auto_scan=st.sidebar.toggle("הפעל סריקה אוטומטית 24/7", value=st.session_state.auto_scan)
AUTO_SEC=st.sidebar.slider("כל כמה שניות", 60, 600, 300, step=30)
HEARTBEAT_MIN=st.sidebar.slider("Heartbeat כל כמה דקות", 15, 120, 60)

if st.sidebar.button("נקה היסטוריה"):
    st.session_state.found_db=set()
    st.session_state.history=[]
    st.session_state.pending_breaks={}
    st.session_state.last_random_batch=[]
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

def get_random_batch():
    n=min(NUM_SCAN, len(ALL_TICKERS))
    batch=random.sample(ALL_TICKERS, n)
    st.session_state.last_random_batch=batch
    return batch

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
        if SCAN_2245:
            per="60d"
            df=None
            try:
                df=yf.Ticker(tkr).history(period=per, interval="15m", auto_adjust=True)
            except:
                df=None
            if df is None or len(df)<30:
                try:
                    df=yf.download(tkr, period=per, interval="15m", progress=False, auto_adjust=True, threads=False)
                except:
                    df=None
            if df is None or len(df)<30:
                return None, None
            try:
                if df.index.tz is None:
                    df.index=df.index.tz_localize('UTC').tz_convert('Asia/Jerusalem')
                else:
                    df.index=df.index.tz_convert('Asia/Jerusalem')
            except:
                pass
            try:
                today_il=pd.Timestamp.now(tz='Asia/Jerusalem').normalize()
                unique_days=pd.to_datetime(df.index.normalize().unique())
                past_days=[d for d in unique_days if d < today_il]
                if not past_days:
                    return None, None
                last_day=past_days[-1]
                df_up_to_day=df[df.index.normalize() == last_day]
                if df_up_to_day.empty:
                    return None, None
                df_2245=df_up_to_day.between_time('22:30','22:55')
                if not df_2245.empty:
                    target_idx=df_2245.index[-1]
                else:
                    target_idx=df_up_to_day.index[-1]
                df=df.loc[:target_idx]
            except Exception:
                df=df.iloc[:-1] if len(df)>1 else df
            close=df["Close"]
            if isinstance(close, pd.DataFrame):
                close=close.iloc[:,0]
            df["BB_L"]=BollingerBands(close, 20, 2).bollinger_lband()
            df["BB_M"]=BollingerBands(close, 20, 2).bollinger_mavg()
            df["BB_H"]=BollingerBands(close, 20, 2).bollinger_hband()
            df["RSI"]=RSIIndicator(close, 14).rsi()
            return df.tail(150), tkr
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
        return {"tkr": real_tkr, "price": round(c,2), "low": round(l,4), "tp": round(bm,2), "pct": round(pct,2), "rsi": round(crsi,1), "interval": "15m-22:45-אתמול" if SCAN_2245 else INTERVAL, "df": df, "is_break": is_break, "stopped": stopped_break, "close": c}
    except:
        return None

def plot_chart(df, tkr):
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name=tkr))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_H'], line=dict(color='rgba(255,0,0,0.3)'), name="BB Upper"))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_L'], line=dict(color='rgba(0,255,0,0.7)', width=2), name="BB Lower"))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_M'], line=dict(color='orange', dash='dash'), name="TP"))
    fig.update_layout(height=550, title=f"{tkr} - {'אתמול 22:45' if SCAN_2245 else INTERVAL}", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    fig2=go.Figure()
    fig2.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI"))
    fig2.add_hline(y=RSI_L, line_dash="dash", line_color="red")
    fig2.update_layout(height=200, title="RSI")
    st.plotly_chart(fig2, use_container_width=True)

c_logo1, c_logo2, c_logo3 = st.columns([1,2,1])
with c_logo2:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.markdown("<h2 style='text-align:center;color:gold;'>FULL BREAK TRADING SYSTEM<br><span style='font-size:14px;letter-spacing:8px;'>omer revah</span></h2>", unsafe_allow_html=True)

with st.expander("📖 מדריך מקצועי - איך המערכת עובדת (לחץ לפתיחה)"):
    st.markdown("### FULL BREAK TRADING SYSTEM - By omer revah")
    st.markdown("**הקונספט:** פריצה מלאה מתחת לרצועת בולינגר התחתונה = מומנטום מכירה קיצוני -> הזדמנות קנייה בהיפוך")
    try:
        st.image("bollinger_diagram.png", caption="BOLLINGER BANDS - FULL BREAK CONCEPT", use_container_width=True)
    except:
        pass
    st.markdown("""
**1. get_tickers()** - מוריד 3500 טיקרים מ-GitHub. סורק את כל השוק. Cache שעה.

**2. tg(message)** - שולח התראות ל-Bot API.

**3. get_data(ticker)** - מושך 2 שנים (1D) / 60 יום (1H). מחשב Bollinger Bands (20,2) ו-RSI (14).

**4. check(ticker)** - המוח:
- full_break = H<BB_L and L<BB_L and O<BB_L and C<BB_L
- prev_inside = פריצה חדשה
- vol_ok = ווליום > ממוצע
- is_break = כל התנאים + RSI < 25 = התראת FULL BREAK
- stopped_break = נר ירוק + Low עולה + RSI עולה = איתות קנייה

**5. plot_chart()** - גרף נרות + BB Lower ירוק + TP כתום + RSI.

**6. run_one_scan()** - סורק 200 רנדומלי מתוך 3500. פריצה -> pending_breaks + אדום. עצירה + pending -> ירוק.

**7. SESSION STATE** - found_db, history, pending_breaks, auto_scan.

**8. SECURITY:** סיסמת Admin 1234 היא רק ל-UI.
    """)

st.title("FULL BREAK DOWN ONLY - PRO AUTO + BUY SIGNAL")
mode_text="🔍 סריקת אתמול 22:45 (15 דק' לפני סגירה)" if SCAN_2245 else "⚡ סריקת אונליין LIVE"
st.caption(f"טיקרים זמינים: {len(ALL_TICKERS)} | מצב: {mode_text} | סריקה: רנדומלית חכמה מכל השוק | אוטומציה: {'🟢 פעיל' if st.session_state.auto_scan else '🔴 כבוי'}")

STATUS BAR WITH REAL TIME
if st.session_state.last_scan_time:
    now_ts=time.time()
    hb_diff=int(now_ts - st.session_state.last_heartbeat) if st.session_state.last_heartbeat else 0
    is_alive=hb_diff < (HEARTBEAT_MIN*60*2.5)
    alive_icon="🟢 חי" if is_alive else "🔴 נרדם!"
    st.info(f"⏱️ סריקה אחרונה: {st.session_state.last_scan_time} | סריקות: {st.session_state.scan_count} | ממתין לירוק: {len(st.session_state.pending_breaks)} | סטטוס: {alive_icon} ({hb_diff//60} דק' מאז heartbeat) | שעון: {datetime.now().strftime('%H:%M:%S')}")
    if not is_alive and st.session_state.auto_scan:
        st.error("⚠️ הסורק נרדם! Streamlit כיבה אותו. תרענן את הדף!")
        tg(f"🚨 הסורק נרדם! לא סרק {hb_diff//60} דקות - תרענן את Streamlit")
else:
    st.info(f"שעון חי: {datetime.now().strftime('%H:%M:%S %d/%m')} | ממתין לסריקה ראשונה")

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
            m=f"🔴 FULL BREAK {r['tkr']} ${r['price']} -> {r['tp']} (+{r['pct']}%) RSI {r['rsi']} | {r['interval']} | ממתין לנעצר"
            st.success(m)
            tg(m)
        else:
            st.info(f"{r['tkr']} אין פריצה מלאה - מחיר ${r['price']} RSI {r['rsi']} | {r['interval']} | מציג גרף לבדיקה")
        plot_chart(r["df"], r["tkr"])
    else:
        st.error("אין דאטה - נסה שוב או טיקר אחר, Yahoo חסם זמנית")

st.divider()

def run_one_scan():
    new_break=0
    new_buy=0
    batch=get_random_batch()
    for tk in batch:
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
                m=f"🔴 FULL BREAK {r['tkr']} ${r['price']} -> {r['tp']} (+{r['pct']}%) RSI {r['rsi']} [{r['interval']}]"
                tg(m)
    for pend_tkr in list(st.session_state.pending_breaks.keys()):
        r=check(pend_tkr)
        if not r:
            continue
        prev=st.session_state.pending_breaks[pend_tkr]
        if r['stopped'] and r['low'] > prev['low']:
            new_buy+=1
            m=f"🟢 הפריצה נעצרה - איתות קנייה {r['tkr']}\nפריצה הייתה ב-${prev['low']} מחיר פריצה ${prev['price']}\nעכשיו ${r['price']} RSI {r['rsi']}\nזה האיתות שלך לקנות!"
            tg(m)
            del st.session_state.pending_breaks[pend_tkr]
    st.session_state.last_scan_time=datetime.now().strftime("%H:%M:%S %d/%m")
    st.session_state.scan_count+=1
    return new_break, new_buy

if st.button(f"סרוק {NUM_SCAN} רנדומלי עכשיו - {mode_text}", use_container_width=True):
    prog=st.progress(0); stat=st.empty()
    new_b=0; new_buy=0
    batch=get_random_batch()
    for i, tk in enumerate(batch):
        stat.text(f"{i+1}/{NUM_SCAN} {tk} [{mode_text}] RANDOM")
        prog.progress((i+1)/NUM_SCAN)
        r=check(tk)
        if r and r["is_break"]:
            key=f"{r['tkr']}_{r['interval']}_{r['price']}"
            if key not in st.session_state.found_db:
                st.session_state.found_db.add(key)
                st.session_state.history.append({k:v for k,v in r.items() if k!='df'})
                st.session_state.pending_breaks[r['tkr']]={'low': r['low'], 'price': r['price'], 'time': str(datetime.now())}
                new_b+=1
                m=f"🔴 FULL BREAK {r['tkr']} ${r['price']} -> {r['tp']} (+{r['pct']}%) [{r['interval']}]"
                st.success(m)
                tg(m)
                with st.expander(f"גרף {r['tkr']}"):
                    plot_chart(r["df"], r["tkr"])
    for pend_tkr in list(st.session_state.pending_breaks.keys()):
        r=check(pend_tkr)
        if r and r['stopped']:
            prev=st.session_state.pending_breaks[pend_tkr]
            if r['low'] > prev['low']:
                new_buy+=1
                m=f"🟢 הפריצה נעצרה - קנייה {r['tkr']} ${r['price']}"
                st.success(m)
                tg(f"🟢 הפריצה נעצרה - איתות קנייה {r['tkr']} עכשיו ${r['price']}")
                del st.session_state.pending_breaks[pend_tkr]
    prog.empty(); stat.empty()
    st.session_state.last_scan_time=datetime.now().strftime("%H:%M:%S")
    st.session_state.scan_count+=1
    if new_b==0 and new_buy==0:
        st.warning("לא נמצאו פריצות חדשות")

if st.session_state.auto_scan:
    st.warning(f"🤖 אוטומציה פעילה - סורק {NUM_SCAN} רנדומלי כל {AUTO_SEC} שניות - {mode_text} - Anti-Sleep פעיל")
    nb, nbuy = run_one_scan()
    st.write(f"נסרקו {NUM_SCAN} רנדומלי | מצב: {mode_text} | פריצות חדשות: {nb} | איתותי קנייה: {nbuy}")
    now=time.time()
    if now - st.session_state.last_heartbeat > HEARTBEAT_MIN*60:
        tg(f"✅ סורק חי - {datetime.now().strftime('%H:%M:%S')} - {mode_text} - נסרקו {NUM_SCAN} רנדומלי - ממתין לנעצר: {len(st.session_state.pending_breaks)} - סריקה #{st.session_state.scan_count} - AntiSleep ON")
        st.session_state.last_heartbeat=now
    # COUNTDOWN INSTEAD OF FREEZE
    countdown_placeholder=st.empty()
    for sec in range(AUTO_SEC, 0, -1):
        countdown_placeholder.caption(f"⏳ סריקה הבאה בעוד {sec} שניות... | שעון חי {datetime.now().strftime('%H:%M:%S')} | אל תסגור את הטאב!")
        time.sleep(1)
    countdown_placeholder.empty()
    st.rerun()

if st.session_state.pending_breaks:
    st.subheader(f"⏳ ממתין לירוק - {len(st.session_state.pending_breaks)} מניות")
    df_p=pd.DataFrame.from_dict(st.session_state.pending_breaks, orient='index')
    st.dataframe(df_p, use_container_width=True)

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
st.sidebar.caption(f"סטטוס: {st.session_state.last_scan_time or 'לא נסרק'} | {mode_text} | RANDOM: ✅ | אונליין: {'✅' if st.session_state.auto_scan else 'OFF'} | Anti-Sleep: ✅")
