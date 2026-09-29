import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
import plotly.graph_objects as go
import time, random, pytz
from datetime import datetime
import streamlit.components.v1 as components

JERUSALEM_TZ = pytz.timezone('Asia/Jerusalem')
def now_il(): return datetime.now(JERUSALEM_TZ)
def now_il_str(f="%H:%M:%S"): return now_il().strftime(f)

st.set_page_config(page_title="BOLLINGER WINNER V2 - FINAL FIX", layout="wide")
components.html("<script>setInterval(()=>{fetch(window.location.href+'?ping=true',{mode:'no-cors'})},60000);</script>", height=0)
if "ping" in st.query_params: st.write("alive"); st.stop()

MASTER_PASS = st.secrets.get("APP_PASSWORD", "1234")
if "ok" not in st.session_state: st.session_state.ok=False
if "found" not in st.session_state: st.session_state.found=set()
if "history" not in st.session_state: st.session_state.history=[]
if "top" not in st.session_state: st.session_state.top=[]
if "scan_count" not in st.session_state: st.session_state.scan_count=0
if "last_scan" not in st.session_state: st.session_state.last_scan=None
if "last_heartbeat" not in st.session_state: st.session_state.last_heartbeat=0
if "runtime_pass" not in st.session_state: st.session_state.runtime_pass=MASTER_PASS

if not st.session_state.ok:
    st.title("WINNER V2 - כניסה")
    p=st.text_input("Password", type="password")
    if st.button("Login"):
        if p==st.session_state.runtime_pass:
            st.session_state.ok=True; st.rerun()
        else: st.error("שגוי")
    st.stop()

DEFAULT_BOT=st.secrets.get("BOT_TOKEN","8857531191:AAFFGNJjEbO-1HPofP_hozyqqp0ieCMa_FY")
DEFAULT_CHAT=st.secrets.get("CHAT_ID","6649894327,-1004229452727")
BOT=st.sidebar.text_input("Bot Token", value=DEFAULT_BOT, type="password")
CHAT=st.sidebar.text_input("Chat IDs", value=DEFAULT_CHAT)

def tg(m):
    if not BOT or not CHAT: return
    for cid in [c.strip() for c in CHAT.split(",") if c.strip()]:
        try: requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":cid,"text":m}, timeout=10)
        except: pass

st.sidebar.divider()
st.sidebar.title("WINNER V2 - FINAL FIX")
MIN_SCORE=st.sidebar.selectbox("Min Score", [6,7,8,9], index=0)
VOL_X=st.sidebar.selectbox("Vol X", [0.5,0.7,1.0,1.2], index=0)
RSI_BUY=st.sidebar.selectbox("RSI Buy <", [30,35,40,45], index=2)
RSI_SELL=st.sidebar.selectbox("RSI Sell >", [60,65,70], index=1)
SL_PCT=st.sidebar.selectbox("SL %", [3,4,5], index=1)
VIX_MIN=st.sidebar.selectbox("VIX Min", [6,10,15,20,24], index=0)
NUM_SCAN=st.sidebar.selectbox("Num scan", [200,500,590,1000], index=0)
INTERVAL=st.sidebar.selectbox("Interval", ["1d","1h","15m"], index=0)
PROX=st.sidebar.selectbox("Proximity %", [1.0,1.5,2.5,4.0], index=2)
AUTO=st.sidebar.toggle("AUTO 60s", value=False)
HEARTBEAT_MIN=st.sidebar.selectbox("Heartbeat min", [15,30,60,90], index=1)
if st.sidebar.button("Clear"): st.session_state.found=set(); st.session_state.history=[]; st.session_state.top=[]
if st.sidebar.button("Logout"): st.session_state.ok=False; st.rerun()

@st.cache_data(ttl=3600)
def get_tickers():
    try:
        df=pd.read_csv("https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all_tickers.txt", header=None)
        t=[t.strip().upper() for t in df.iloc[:,0].tolist() if not str(t).endswith(('W','WS','WT'))]
        return t[:2000]
    except: return ["AAPL","MSFT","NVDA","TSLA","AMD","SPY","QQQ","ES=F","NQ=F","RTY=F","META","GOOGL","NFLX"]

@st.cache_data(ttl=60)
def get_vix():
    try:
        v=yf.Ticker("^VIX").history(period="5d")["Close"]
        if isinstance(v, pd.DataFrame): v=v.iloc[:,0]
        return float(v.iloc[-1])
    except: return 16.3

def fix_series(s):
    if isinstance(s, pd.DataFrame): return s.iloc[:,0]
    return s

def get_data(tkr):
    try:
        per="2y" if INTERVAL=="1d" else "60d"
        df=yf.Ticker(tkr).history(period=per, interval=INTERVAL, auto_adjust=True)
        if len(df)<30: return None
        close = fix_series(df["Close"])
        df["BB_L"]=BollingerBands(close,20,2).bollinger_lband()
        df["BB_M"]=BollingerBands(close,20,2).bollinger_mavg()
        df["BB_H"]=BollingerBands(close,20,2).bollinger_hband()
        df["RSI"]=RSIIndicator(close,14).rsi()
        return df.tail(200)
    except: return None

def calc_score(rsi, vr, rr, vix, side):
    s=0
    s+=2.5 if (side=="BUY" and rsi<15) or (side=="SELL" and rsi>85) else 2.0 if rsi<20 or rsi>80 else 1.5 if rsi<30 or rsi>70 else 0.8
    s+=2.0 if vr>=2.5 else 1.5 if vr>=1.5 else 1.0 if vr>=1.0 else 0.6
    s+=2.5 if rr>=3 else 2.0 if rr>=2 else 1.4 if rr>=1.5 else 1.0
    s+=1.5 if 15<=vix<=30 else 1.0
    return round(min(10,s),1)

def check_one(tkr, debug=False):
    df=get_data(tkr)
    if df is None: return None, "no data"
    try:
        c=float(fix_series(df["Close"]).iloc[-1]); bl=float(fix_series(df["BB_L"]).iloc[-1]); bh=float(fix_series(df["BB_H"]).iloc[-1]); bm=float(fix_series(df["BB_M"]).iloc[-1])
        rsi=float(fix_series(df["RSI"]).iloc[-1]); vix=get_vix()
        vol=float(fix_series(df["Volume"]).iloc[-1]); av=float(fix_series(df["Volume"]).rolling(20).mean().iloc[-1]); vr=round(vol/av,2) if av>0 else 1.0
        if debug: st.write(f"{tkr} c={c:.2f} L={bl:.2f} H={bh:.2f} RSI={rsi:.1f} VR={vr} VIX={vix:.2f} distL={((c-bl)/c*100):.2f}% distH={((bh-c)/c*100):.2f}%")
        res=[]
        dist_low = (c - bl) / c * 100
        dist_high = (bh - c) / c * 100
        near_low = c <= bl or dist_low <= PROX
        near_high = c >= bh or dist_high <= PROX
        if near_low and rsi < RSI_BUY and vr>=VOL_X and vix>=VIX_MIN:
            sl=round(c*(1-SL_PCT/100),2); tp=round(bm,2)
            rr=round(abs(tp-c)/abs(c-sl),2) if c!=sl else 0
            score=calc_score(rsi,vr,rr,vix,"BUY")
            if score>=MIN_SCORE: res.append({"tkr":tkr,"side":"BUY","price":round(c,2),"sl":sl,"tp":tp,"rr":rr,"score":score,"rsi":round(rsi,1),"vol":vr,"vix":round(vix,2),"pct":round((tp-c)/c*100,2),"df":df,"dist":round(dist_low,2)})
        if near_high and rsi > RSI_SELL and vr>=VOL_X and vix>=VIX_MIN:
            sl=round(c*(1+SL_PCT/100),2); tp=round(bm,2)
            rr=round(abs(c-tp)/abs(sl-c),2) if sl!=c else 0
            score=calc_score(rsi,vr,rr,vix,"SELL")
            if score>=MIN_SCORE: res.append({"tkr":tkr,"side":"SELL","price":round(c,2),"sl":sl,"tp":tp,"rr":rr,"score":score,"rsi":round(rsi,1),"vol":vr,"vix":round(vix,2),"pct":round((c-tp)/c*100,2),"df":df,"dist":round(dist_high,2)})
        if not res: return None, f"no touch RSI={rsi:.1f} VR={vr} distL={dist_low:.1f}% distH={dist_high:.1f}%"
        return res, "ok"
    except Exception as e: return None, f"err {e}"

def run_scan():
    tickers=get_tickers()
    pool=random.sample(tickers, min(500,len(tickers)))
    vols=[]
    prog=st.progress(0, text="בודק VOL...")
    for i, t in enumerate(pool[:200]):
        try:
            df=yf.Ticker(t).history(period="2d", interval="1d", auto_adjust=True)
            if not df.empty: vols.append((t,float(fix_series(df["Volume"]).iloc[-1])))
        except: pass
        if i%20==0: prog.progress(i/200)
    prog.empty()
    vols.sort(key=lambda x:x[1], reverse=True)
    batch=[x[0] for x in vols[:NUM_SCAN]] if vols else random.sample(tickers, NUM_SCAN)
    batch+=["AMD","NVDA","AAPL","TSLA","MSFT","META","GOOGL","ES=F","NQ=F","RTY=F"]; batch=list(dict.fromkeys(batch))
    new=0; fails=[]
    prog2=st.progress(0, text=f"סורק {len(batch)}...")
    for idx, tk in enumerate(batch):
        lst, reason = check_one(tk)
        if not lst: fails.append(f"{tk}:{reason}")
        else:
            for r in lst:
                key=f"{r['tkr']}_{r['side']}_{r['price']}_{now_il_str('%Y%m%d%H')}"
                if key in st.session_state.found: continue
                st.session_state.found.add(key); st.session_state.history.append({k:v for k,v in r.items() if k!='df'}); st.session_state.top.append(r)
                new+=1; tg(f"🏆 {r['side']} {r['tkr']} SCORE {r['score']}/10 RR {r['rr']} ${r['price']} TP {r['tp']} SL {r['sl']} RSI {r['rsi']} VOL x{r['vol']} VIX {r['vix']}")
        prog2.progress((idx+1)/len(batch))
    prog2.empty()
    if st.session_state.top:
        df=pd.DataFrame([{k:v for k,v in x.items() if k!='df'} for x in st.session_state.top]).sort_values(by="score", ascending=False).drop_duplicates(subset=["tkr","side"], keep="first").head(30)
        st.session_state.top=df.to_dict("records")
    st.session_state.last_scan=now_il_str("%H:%M:%S %d/%m"); st.session_state.scan_count+=1
    return new, batch, fails[:10]

st.title("🏆 BOLLINGER WINNER V2 - FINAL FIX")
st.caption(f"VIX: {get_vix():.2f} | Time: {now_il_str('%H:%M:%S')} | Proximity {PROX}% | VOL {VOL_X}x | VIX {VIX_MIN}")
if st.session_state.last_scan: st.info(f"Last: {st.session_state.last_scan} | Scans: {st.session_state.scan_count} | Top: {len(st.session_state.top)} | History: {len(st.session_state.history)}")

c1,c2=st.columns(2)
with c1:
    if st.button("🔥 SCAN WINNER NOW", use_container_width=True, type="primary"):
        with st.spinner("Scanning..."): n,b,fails=run_scan(); st.success(f"Scanned {len(b)} | New {n}"); st.write("Fails sample:", fails)
with c2:
    man=st.text_input("Manual", placeholder="AMD", value="AMD")
    if st.button("Check Manual"):
        lst, reason = check_one(man, debug=True)
        if lst:
            for r in lst:
                st.write(f"{r['side']} {r['tkr']} SCORE {r['score']} RR {r['rr']} dist {r['dist']}%")
                fig=go.Figure(); df=r["df"]
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=fix_series(df['Close'])))
                fig.add_trace(go.Scatter(x=df.index, y=fix_series(df['BB_L']), line=dict(color='green'), name='L')); fig.add_trace(go.Scatter(x=df.index, y=fix_series(df['BB_H']), line=dict(color='red'), name='H')); fig.add_trace(go.Scatter(x=df.index, y=fix_series(df['BB_M']), line=dict(color='blue'), name='M'))
                fig.update_layout(height=500, xaxis_rangeslider_visible=False); st.plotly_chart(fig, use_container_width=True)
        else: st.error(f"No signal - {reason}")

st.divider()
st.subheader("TOP WINNERS - RR SCORE TABLE")
if st.session_state.top:
    top_df=pd.DataFrame(st.session_state.top)[["score","rr","tkr","side","price","tp","sl","pct","rsi","vol","vix","dist"]].sort_values(by="score", ascending=False)
    st.dataframe(top_df, use_container_width=True, height=450)
else:
    st.warning("אין TOP חדש - מציג היסטוריה")
    if st.session_state.history:
        hist_df=pd.DataFrame(st.session_state.history).tail(100)[["score","rr","tkr","side","price","tp","sl","pct","rsi","vol","vix"]].sort_values(by="score", ascending=False)
        st.dataframe(hist_df, use_container_width=True, height=450)
    else:
        st.info("טבלה ריקה כי אין איתותים - שנה Proximity ל-4.0% ותריץ שוב")
