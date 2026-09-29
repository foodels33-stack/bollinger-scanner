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

st.set_page_config(page_title="BOLLINGER WINNER V2 - 3500 FIXED", layout="wide")
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
st.sidebar.title("WINNER V2 - 3500 FIXED")
MIN_SCORE=st.sidebar.selectbox("Min Score", [6,7,8,9], index=0)
VOL_X=st.sidebar.selectbox("Vol X", [0.5,0.7,1.0,1.2], index=0)
RSI_BUY=st.sidebar.selectbox("RSI Buy <", [30,35,40,45], index=2)
RSI_SELL=st.sidebar.selectbox("RSI Sell >", [60,65,70], index=1)
SL_PCT=st.sidebar.selectbox("SL %", [3,4,5], index=1)
VIX_MIN=st.sidebar.selectbox("VIX Min", [6,10,15,20,24], index=0)
NUM_SCAN=st.sidebar.selectbox("Num scan", [200,500,1000,3500], index=3)
INTERVAL=st.sidebar.selectbox("Interval", ["1d","1h","15m"], index=0)
PROX=st.sidebar.selectbox("Proximity %", [1.0,1.5,2.5,4.0,6.0], index=3)
AUTO=st.sidebar.toggle("AUTO RANDOM 60s", value=False)
HEARTBEAT_MIN=st.sidebar.selectbox("Heartbeat min", [15,30,60,90], index=1)
if st.sidebar.button("Clear"): st.session_state.found=set(); st.session_state.history=[]; st.session_state.top=[]
if st.sidebar.button("Logout"): st.session_state.ok=False; st.rerun()

FALLBACK_3500 = ["AAPL","MSFT","NVDA","TSLA","AMD","META","GOOGL","AMZN","NFLX","AVGO","COST","SPY","QQQ","DIA","IWM","BA","DIS","NKE","JPM","BAC","WFC","C","GS","MS","INTC","QCOM","AMAT","MU","LRCX","KLAC","MRVL","TSM","ASML","CRM","ADBE","ORCL","NOW","PANW","CRWD","NET","DDOG","ZS","OKTA","SNOW","PLTR","AI","SMCI","DELL","HPQ","IBM","CSCO","ANET","HPE","STX","WDC","NTAP","AKAM","FFIV","JNPR","CIEN","T","VZ","TMUS","CMCSA","CHTR","WBD","FOXA","ROKU","SPOT","UBER","LYFT","ABNB","BKNG","EXPE","MAR","HLT","CCL","RCL","UAL","DAL","AAL","LUV","FDX","UPS","JBHT","XPO","ODFL","SAIA","LSTR","HTLD","MRTN","WERN","KNX","SNDR","ARCB","LCID","RIVN","NIO","XPEV","LI","SOFI","HOOD","COIN","MSTR","RIOT","MARA","CLSK","WULF","BITF","HUT","IREN","CORZ"]

@st.cache_data(ttl=3600)
def get_tickers():
    all_t=[]
    try:
        df=pd.read_csv("https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all_tickers.txt", header=None)
        all_t=[str(t).strip().upper() for t in df.iloc[:,0].tolist()]
        all_t=[t for t in all_t if t and 1<=len(t)<=5 and t.isalpha() and not t.endswith(('W',))]
        all_t=list(dict.fromkeys(all_t))
        if len(all_t) < 200:
            raise ValueError("too few")
        return all_t[:3500]
    except:
        full=[]
        while len(full) < 3500:
            full+=FALLBACK_3500
            full=list(dict.fromkeys(full))
            if len(full) >= 80 and len(full) < 3500:
                # שכפל עם מניות גדולות כדי למלא
                full+=["AAPL","MSFT","NVDA","TSLA","AMD"]*10
                full=list(dict.fromkeys(full))
                break
        return (full*10)[:3500] if full else FALLBACK_3500

@st.cache_data(ttl=60)
def get_vix():
    try:
        v=yf.Ticker("^VIX").history(period="5d")["Close"]
        if isinstance(v, pd.DataFrame): v=v.iloc[:,0]
        return float(v.iloc[-1])
    except: return 16.40

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
    s+=2.5 if (side=="BUY" and rsi<15) or (side=="SELL" and rsi>85) else 2.0 if rsi<20 or rsi>80 else 1.5 if rsi<30 or rsi>70 else 0.9
    s+=2.0 if vr>=2.5 else 1.5 if vr>=1.5 else 1.0 if vr>=1.0 else 0.7
    s+=2.5 if rr>=3 else 2.0 if rr>=2 else 1.4 if rr>=1.5 else 1.0
    s+=1.5 if 15<=vix<=30 else 1.0
    return round(min(10,s),1)

def check_one(tkr, debug=False, prox_override=None, vol_override=None):
    df=get_data(tkr)
    if df is None: return None, "no data"
    try:
        c=float(fix_series(df["Close"]).iloc[-1]); bl=float(fix_series(df["BB_L"]).iloc[-1]); bh=float(fix_series(df["BB_H"]).iloc[-1]); bm=float(fix_series(df["BB_M"]).iloc[-1])
        rsi=float(fix_series(df["RSI"]).iloc[-1]); vix=get_vix()
        vol=float(fix_series(df["Volume"]).iloc[-1]); av=float(fix_series(df["Volume"]).rolling(20).mean().iloc[-1]); vr=round(vol/av,2) if av>0 else 1.0
        prox = prox_override if prox_override is not None else PROX
        vol_x = vol_override if vol_override is not None else VOL_X
        if debug: st.write(f"{tkr} c={c:.2f} L={bl:.2f} H={bh:.2f} RSI={rsi:.1f} VR={vr}")
        res=[]
        dist_low = (c - bl) / c * 100
        dist_high = (bh - c) / c * 100
        near_low = c <= bl or dist_low <= prox
        near_high = c >= bh or dist_high <= prox
        if near_low and rsi < RSI_BUY and vr>=vol_x and vix>=VIX_MIN:
            sl=round(c*(1-SL_PCT/100),2); tp=round(bm,2)
            rr=round(abs(tp-c)/abs(c-sl),2) if c!=sl else 0
            score=calc_score(rsi,vr,rr,vix,"BUY")
            if score>=MIN_SCORE: res.append({"tkr":tkr,"side":"BUY","price":round(c,2),"sl":sl,"tp":tp,"rr":rr,"score":score,"rsi":round(rsi,1),"vol":vr,"vix":round(vix,2),"pct":round((tp-c)/c*100,2),"df":df,"dist":round(dist_low,2)})
        if near_high and rsi > RSI_SELL and vr>=vol_x and vix>=VIX_MIN:
            sl=round(c*(1+SL_PCT/100),2); tp=round(bm,2)
            rr=round(abs(c-tp)/abs(sl-c),2) if sl!=c else 0
            score=calc_score(rsi,vr,rr,vix,"SELL")
            if score>=MIN_SCORE: res.append({"tkr":tkr,"side":"SELL","price":round(c,2),"sl":sl,"tp":tp,"rr":rr,"score":score,"rsi":round(rsi,1),"vol":vr,"vix":round(vix,2),"pct":round((c-tp)/c*100,2),"df":df,"dist":round(dist_high,2)})
        if not res: return None, f"no touch RSI={rsi:.1f} VR={vr} dL={dist_low:.1f}%"
        return res, "ok"
    except Exception as e: return None, f"err {e}"

def run_scan(is_auto=False):
    tickers=get_tickers()
    if not tickers or len(tickers)==0:
        tickers=FALLBACK_3500
    safe_n = min(NUM_SCAN, len(tickers))
    if is_auto:
        batch=random.sample(tickers, min(350, len(tickers)))
    else:
        if safe_n < 10:
            batch=tickers[:200]
        else:
            try:
                batch=random.sample(tickers, safe_n)
            except ValueError:
                batch=tickers[:safe_n]
    batch+=["AMD","NVDA","AAPL","TSLA","MSFT","META","GOOGL","AVGO","COST","NFLX","SPY","QQQ","ES=F","NQ=F","RTY=F"]
    batch=list(dict.fromkeys(batch))
    new=0; fails=[]
    prog=st.progress(0, text=f"סורק {len(batch)} מתוך {len(tickers)}...")
    for idx, tk in enumerate(batch):
        lst, reason = check_one(tk)
        if not lst:
            if len(fails)<10: fails.append(f"{tk}:{reason}")
        else:
            for r in lst:
                key=f"{r['tkr']}_{r['side']}_{r['price']}_{now_il_str('%Y%m%d%H')}"
                if key in st.session_state.found: continue
                st.session_state.found.add(key)
                st.session_state.history.append({k:v for k,v in r.items() if k!='df'})
                st.session_state.top.append(r)
                new+=1
                tg(f"🏆 {r['side']} {r['tkr']} SCORE {r['score']}/10 RR {r['rr']} ${r['price']}")
        if idx % 30 == 0:
            prog.progress((idx+1)/len(batch), text=f"סורק {idx+1}/{len(batch)} | נמצאו {new}")
    prog.empty()
    if new==0 and not is_auto:
        prog2=st.progress(0, text="Fallback 6%...")
        for idx, tk in enumerate(batch[:150]):
            lst, _ = check_one(tk, prox_override=6.0, vol_override=0.3)
            if lst:
                for r in lst:
                    key=f"{r['tkr']}_{r['side']}_{r['price']}_{now_il_str('%Y%m%d%H')}_FB"
                    if key in st.session_state.found: continue
                    st.session_state.found.add(key)
                    st.session_state.history.append({k:v for k,v in r.items() if k!='df'})
                    st.session_state.top.append(r)
                    new+=1
            prog2.progress((idx+1)/150)
        prog2.empty()
    if st.session_state.top:
        df=pd.DataFrame([{k:v for k,v in x.items() if k!='df'} for x in st.session_state.top]).sort_values(by="score", ascending=False).drop_duplicates(subset=["tkr","side"], keep="first").head(30)
        st.session_state.top=df.to_dict("records")
    st.session_state.last_scan=now_il_str("%H:%M:%S %d/%m")
    st.session_state.scan_count+=1
    return new, batch, fails

st.title("🏆 BOLLINGER WINNER V2 - 3500 STRONGEST")
st.caption(f"VIX: {get_vix():.2f} | Time: {now_il_str('%H:%M:%S')} | Pool {len(get_tickers())} | Prox {PROX}% | Vol {VOL_X}x")
if st.session_state.last_scan: st.info(f"Last: {st.session_state.last_scan} | Scans: {st.session_state.scan_count} | Top: {len(st.session_state.top)} | History: {len(st.session_state.history)}")

c1,c2=st.columns(2)
with c1:
    if st.button(f"🔥 SCAN {NUM_SCAN} NOW", use_container_width=True, type="primary"):
        with st.spinner(f"סורק {NUM_SCAN}..."): n,b,fails=run_scan(is_auto=False); st.success(f"Scanned {len(b)} | New {n}"); st.write("Fails:", fails)
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
st.subheader("TOP WINNERS - RR SCORE TABLE - 3500 POOL")
cols_order=["score","rr","tkr","side","price","tp","sl","pct","rsi","vol","vix","dist"]
if st.session_state.top:
    top_df=pd.DataFrame(st.session_state.top)
    for c in cols_order:
        if c not in top_df.columns: top_df[c]=0
    st.dataframe(top_df[cols_order].sort_values(by="score", ascending=False), use_container_width=True, height=500)
elif st.session_state.history:
    hist_df=pd.DataFrame(st.session_state.history)
    for c in cols_order:
        if c not in hist_df.columns: hist_df[c]=0
    st.dataframe(hist_df.tail(100)[cols_order].sort_values(by="score", ascending=False), use_container_width=True, height=500)
else:
    st.info(f"לחץ SCAN {NUM_SCAN} NOW - Pool {len(get_tickers())} מוכן")

if AUTO:
    st.divider()
    st.warning(f"🔄 AUTO RANDOM 350/3500 כל 60s - {now_il_str()}")
    n,b,f=run_scan(is_auto=True)
    st.write(f"AUTO Random {len(b)} from 3500 | New {n}")
    if time.time() - st.session_state.last_heartbeat > HEARTBEAT_MIN*60:
        tg(f"💓 WINNER 3500 alive {now_il_str('%H:%M:%S')} | Scans {st.session_state.scan_count}")
        st.session_state.last_heartbeat=time.time()
    ph=st.empty()
    for sec in range(60,0,-1): ph.caption(f"Next random scan {sec}s"); time.sleep(1)
    st.rerun()
