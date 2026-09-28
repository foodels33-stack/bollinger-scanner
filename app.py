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

st.set_page_config(page_title="BOLLINGER WINNER V2 - 1 SCANNER", layout="wide")
components.html("<script>setInterval(()=>{fetch(window.location.href+'?ping=true',{mode:'no-cors'})},60000);</script>", height=0)
if "ping" in st.query_params: st.write("alive"); st.stop()

MASTER_PASS = st.secrets.get("APP_PASSWORD", "1234")
if "ok" not in st.session_state:
    st.session_state.ok=False
    st.session_state.found=set()
    st.session_state.history=[]
    st.session_state.top=[]
    st.session_state.cooldown={}
    st.session_state.scan_count=0
    st.session_state.last_scan=None

if not st.session_state.ok:
    st.title("WINNER V2 - כניסה")
    p=st.text_input("Password", type="password")
    if st.button("Login"):
        if p==MASTER_PASS: st.session_state.ok=True; st.rerun()
        else: st.error("שגוי")
    st.stop()

BOT=st.secrets.get("BOT_TOKEN","8857531191:AAFFGNJjEbO-1HPofP_hozyqqp0ieCMa_FY")
CHAT=st.secrets.get("CHAT_ID","6649894327,-1004229452727")

def tg(m):
    for cid in [c.strip() for c in CHAT.split(",") if c.strip()]:
        try: requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":cid,"text":m}, timeout=10)
        except: pass

st.sidebar.title("WINNER V2 - 1 SCANNER")
MIN_SCORE=st.sidebar.selectbox("Min Score", [6,7,8,9], index=2)
VOL_X=st.sidebar.selectbox("Vol X", [1.0,1.2,1.5], index=1)
RSI_BUY=st.sidebar.selectbox("RSI Buy <", [25,30,35], index=1)
SL_PCT=st.sidebar.selectbox("SL %", [3,4,5], index=1)
VIX_MIN=st.sidebar.selectbox("VIX Min", [15,20,24], index=1)
NUM_SCAN=st.sidebar.selectbox("Num scan", [200,500,590,1000], index=2)
INTERVAL=st.sidebar.selectbox("Interval", ["1d","1h","15m"], index=0)
AUTO=st.sidebar.toggle("AUTO 60s", value=True)
if st.sidebar.button("Clear"): st.session_state.found=set(); st.session_state.history=[]; st.session_state.top=[]

@st.cache_data(ttl=3600)
def get_tickers():
    try:
        df=pd.read_csv("https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all_tickers.txt", header=None)
        t=[t.strip().upper() for t in df.iloc[:,0].tolist() if not str(t).endswith(('W','WS','WT'))]
        return t[:2000]
    except: return ["AAPL","MSFT","NVDA","TSLA","SPY","QQQ","ES=F","NQ=F","RTY=F"]

@st.cache_data(ttl=60)
def get_vix():
    try: return float(yf.Ticker("^VIX").history(period="5d", interval="15m")["Close"].iloc[-1])
    except: return 20.0

def get_data(tkr):
    try:
        per="2y" if INTERVAL=="1d" else "60d"
        df=yf.Ticker(tkr).history(period=per, interval=INTERVAL, auto_adjust=True)
        if len(df)<30: return None
        c=df["Close"]
        c=c.iloc[:,0] if isinstance(c, pd.DataFrame) else c
        df["BB_L"]=BollingerBands(c,20,2).bollinger_lband()
        df["BB_M"]=BollingerBands(c,20,2).bollinger_mavg()
        df["BB_H"]=BollingerBands(c,20,2).bollinger_hband()
        df["RSI"]=RSIIndicator(c,14).rsi()
        return df.tail(200)
    except: return None

def calc_score(rsi, vr, rr, vix, side):
    s=0
    s+=2.5 if (side=="BUY" and rsi<15) or (side=="SELL" and rsi>85) else 2.0 if rsi<20 or rsi>80 else 1.5 if rsi<30 or rsi>70 else 0.6
    s+=2.0 if vr>=2.5 else 1.5 if vr>=1.5 else 1.0 if vr>=1.2 else 0.3
    s+=2.5 if rr>=3 else 2.0 if rr>=2 else 1.4 if rr>=1.5 else 0.8
    s+=1.5 if 20<=vix<=28 else 1.0 if 18<=vix<=32 else 0.6
    return round(min(10,s),1)

def check_one(tkr):
    df=get_data(tkr)
    if df is None: return None
    try:
        c=float(df["Close"].iloc[-1]); bl=float(df["BB_L"].iloc[-1]); bh=float(df["BB_H"].iloc[-1]); bm=float(df["BB_M"].iloc[-1])
        rsi=float(df["RSI"].iloc[-1]); vix=get_vix()
        vol=float(df["Volume"].iloc[-1]); av=float(df["Volume"].rolling(20).mean().iloc[-1]); vr=round(vol/av,2) if av>0 else 1.0
        res=[]
        if c < bl and rsi < RSI_BUY and vr>=VOL_X and vix>=VIX_MIN:
            sl=round(c*(1-SL_PCT/100),2); tp=round(bm,2)
            rr=round(abs(tp-c)/abs(c-sl),2) if c!=sl else 0
            score=calc_score(rsi,vr,rr,vix,"BUY")
            if score>=MIN_SCORE: res.append({"tkr":tkr,"side":"BUY","price":round(c,2),"sl":sl,"tp":tp,"rr":rr,"score":score,"rsi":round(rsi,1),"vol":vr,"vix":round(vix,1),"pct":round((tp-c)/c*100,2),"df":df})
        if c > bh and rsi > 70 and vr>=VOL_X and vix>=VIX_MIN:
            sl=round(c*(1+SL_PCT/100),2); tp=round(bm,2)
            rr=round(abs(c-tp)/abs(sl-c),2) if sl!=c else 0
            score=calc_score(rsi,vr,rr,vix,"SELL")
            if score>=MIN_SCORE: res.append({"tkr":tkr,"side":"SELL","price":round(c,2),"sl":sl,"tp":tp,"rr":rr,"score":score,"rsi":round(rsi,1),"vol":vr,"vix":round(vix,1),"pct":round((c-tp)/c*100,2),"df":df})
        return res if res else None
    except: return None

def run_scan():
    tickers=get_tickers()
    pool=random.sample(tickers, min(600,len(tickers)))
    vols=[]
    for t in pool[:250]:
        try:
            df=yf.Ticker(t).history(period="2d", interval="1d", auto_adjust=True)
            if not df.empty: vols.append((t,float(df["Volume"].iloc[-1])))
        except: pass
    vols.sort(key=lambda x:x[1], reverse=True)
    batch=[x[0] for x in vols[:NUM_SCAN]] if vols else random.sample(tickers, NUM_SCAN)
    batch+=["ES=F","NQ=F","RTY=F"]; batch=list(dict.fromkeys(batch))
    new=0
    for tk in batch:
        lst=check_one(tk)
        if not lst: continue
        for r in lst:
            key=f"{r['tkr']}_{r['side']}_{r['price']}_{now_il_str('%Y%m%d%H')}"
            if key in st.session_state.found: continue
            st.session_state.found.add(key); st.session_state.history.append({k:v for k,v in r.items() if k!='df'}); st.session_state.top.append(r)
            new+=1; tg(f"🏆 {r['side']} WINNER {r['tkr']} SCORE {r['score']}/10 RR {r['rr']} ${r['price']} TP {r['tp']} SL {r['sl']} RSI {r['rsi']} VOL x{r['vol']} VIX {r['vix']}")
    if st.session_state.top:
        df=pd.DataFrame([{k:v for k,v in x.items() if k!='df'} for x in st.session_state.top]).sort_values(by="score", ascending=False).drop_duplicates(subset=["tkr","side"], keep="first").head(30)
        st.session_state.top=df.to_dict("records")
    st.session_state.last_scan=now_il_str("%H:%M:%S %d/%m"); st.session_state.scan_count+=1
    return new, batch

st.title("🏆 BOLLINGER WINNER V2 - 1 SCANNER = 3")
st.caption(f"VIX: {get_vix():.2f} | Time: {now_il_str('%H:%M:%S')} | Unified")
if st.session_state.last_scan: st.info(f"Last: {st.session_state.last_scan} | Scans: {st.session_state.scan_count} | Top: {len(st.session_state.top)}")

c1,c2=st.columns(2)
with c1:
    if st.button("🔥 SCAN WINNER NOW", use_container_width=True, type="primary"):
        with st.spinner("Scanning hottest..."): n,b=run_scan(); st.success(f"Scanned {len(b)} | New {n} SCORE {MIN_SCORE}+")
with c2:
    man=st.text_input("Manual", placeholder="NVDA")
    if st.button("Check Manual"):
        lst=check_one(man) if man else None
        if lst:
            for r in lst:
                st.write(f"{r['side']} {r['tkr']} SCORE {r['score']} RR {r['rr']}")
                fig=go.Figure(); df=r["df"]
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']))
                fig.add_trace(go.Scatter(x=df.index, y=df['BB_L'], line=dict(color='green'))); fig.add_trace(go.Scatter(x=df.index, y=df['BB_H'], line=dict(color='red')))
                fig.update_layout(height=500, xaxis_rangeslider_visible=False); st.plotly_chart(fig, use_container_width=True)
        else: st.error("No signal")

if st.session_state.top:
    st.subheader("TOP WINNERS")
    st.dataframe(pd.DataFrame(st.session_state.top)[["score","rr","tkr","side","price","tp","sl","pct","rsi","vol","vix"]].sort_values(by="score", ascending=False), use_container_width=True, height=400)

if AUTO:
    st.divider(); st.warning(f"AUTO 60s - {now_il_str()}"); n,b=run_scan(); st.write(f"New {n}")
    ph=st.empty()
    for sec in range(60,0,-1): ph.caption(f"Next {sec}s"); time.sleep(1)
    st.rerun()
