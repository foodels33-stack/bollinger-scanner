import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
import plotly.graph_objects as go
import time
from datetime import datetime
import pytz, random
import streamlit.components.v1 as components

JERUSALEM_TZ = pytz.timezone('Asia/Jerusalem')
def now_il(): return datetime.now(JERUSALEM_TZ)
def now_il_str(f="%H:%M:%S"): return now_il().strftime(f)

st.set_page_config(page_title="FULL INTELLIGENT AUTO 60s SECURE LITE", layout="wide")
components.html("<script>setInterval(()=>{fetch(window.location.href+'?ping=true',{mode:'no-cors'})},60000);</script>", height=0)
if "ping" in st.query_params:
    st.write("alive")
    st.stop()

MASTER_PASS = st.secrets.get("APP_PASSWORD", "1234")
if "ok" not in st.session_state:
    st.session_state.ok=False
    st.session_state.auth_fail=0
    st.session_state.found_db=set()
    st.session_state.history=[]
    st.session_state.pending_breaks={}
    st.session_state.last_scan_time=None
    st.session_state.last_heartbeat=0
    st.session_state.auto_scan=True
    st.session_state.scan_count=0
    st.session_state.last_random_batch=[]
    st.session_state.futures_found=set()
    st.session_state.futures_history=[]
    st.session_state.futures_last_scan=None
    st.session_state.futures_auto=True
    st.session_state.futures_scan_count=0
    st.session_state.futures_heartbeat=0
    st.session_state.intel_auto=True
    st.session_state.intel_history=[]
    st.session_state.intel_found=set()
    st.session_state.intel_last_scan=None
    st.session_state.intel_scan_count=0
    st.session_state.intel_heartbeat=0
    st.session_state.top_scores=[]
    st.session_state.last_seen_ticker={}
    st.session_state.runtime_pass=MASTER_PASS

if not st.session_state.ok:
    st.title("כניסה מאובטחת")
    p=st.text_input("Password", type="password")
    if st.button("Login"):
        if p==st.session_state.runtime_pass:
            st.session_state.ok=True
            st.session_state.auth_fail=0
            st.rerun()
        else:
            st.session_state.auth_fail+=1
            st.error(f"שגוי {st.session_state.auth_fail}/3")
            if st.session_state.auth_fail>=3:
                time.sleep(30)
    st.stop()

DEFAULT_BOT=st.secrets.get("BOT_TOKEN","8857531191:AAFFGNJjEbO-1HPofP_hozyqqp0ieCMa_FY")
DEFAULT_CHAT=st.secrets.get("CHAT_ID","6649894327,-1004229452727")
BOT=st.sidebar.text_input("Bot Token", value=DEFAULT_BOT, type="password")
CHAT=st.sidebar.text_input("Chat IDs comma separated", value=DEFAULT_CHAT)

def tg(m):
    if not BOT or not CHAT:
        return
    for cid in [c.strip() for c in CHAT.split(",") if c.strip()]:
        try:
            requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":cid,"text":m}, timeout=10)
        except:
            pass

if st.sidebar.button("TEST BOT"):
    for cid in [c.strip() for c in CHAT.split(",") if c.strip()]:
        try:
            r=requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":cid,"text":"TEST OK - SECURE LITE"}, timeout=15)
            st.sidebar.write(f"{cid} -> {r.status_code}")
        except Exception as e:
            st.sidebar.error(str(e))

st.sidebar.divider()
st.sidebar.subheader("אבטחה")
with st.sidebar.expander("ניהול גישה"):
    new_pass=st.text_input("סיסמה חדשה", type="password")
    if st.button("שנה סיסמה"):
        if len(new_pass)>=4:
            st.session_state.runtime_pass=new_pass
            st.success("שונתה! עדכן Secrets APP_PASSWORD")
        else:
            st.error("מינימום 4 תווים")
    if st.button("Logout"):
        st.session_state.ok=False
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("INTELLIGENT AUTO 60 SEC")
st.session_state.intel_auto=st.sidebar.toggle("AUTO INTELLIGENT 60s", value=st.session_state.intel_auto)
INTEL_MIN_SCORE=st.sidebar.selectbox("Send only SCORE above", [1,2,3,4,5,6,7,8,9,10], index=7)
INTEL_COOLDOWN=st.sidebar.selectbox("No repeat ticker minutes", [1,5,10,15,20,30], index=2)
INTEL_MODE=st.sidebar.selectbox("Scan type", ["BUY+SELL","BUY ONLY","SELL ONLY"], index=0)
SL_PCT=st.sidebar.selectbox("SL real %", [2,3,4,5,6,8,10], index=2)

st.sidebar.divider()
st.sidebar.subheader("BOLLINGER OMER")
INTERVAL=st.sidebar.selectbox("Interval", ["1d","1h","15m"], index=0)
RSI_L=st.sidebar.selectbox("RSI under", [10,15,20,25,30,35,40], index=3)
VOL_M=st.sidebar.selectbox("Vol X", [1.0,1.2,1.5,2.0,2.5,3.0], index=2)
NUM_SCAN=st.sidebar.selectbox("How many to scan", [200,500,590,1000,1500], index=2)
SCAN_2245=st.sidebar.checkbox("Scan yesterday 22:45")
st.session_state.auto_scan=st.sidebar.toggle("Auto OMER 24/7", value=st.session_state.auto_scan)
AUTO_SEC=st.sidebar.selectbox("OMER seconds", [60,120,180,300,600], index=3)
HEARTBEAT_MIN=st.sidebar.selectbox("Heartbeat OMER min", [15,30,60,90,120], index=2)

st.sidebar.divider()
st.sidebar.subheader("MATRIX FUTURES")
FUTURES_TICKERS=["ES=F","NQ=F","RTY=F"]
FUTURES_INTERVAL=st.sidebar.selectbox("Futures Interval", ["2m","5m","15m","1h","4h"], index=2)
FUTURES_VIX_LVL=st.sidebar.selectbox("VIX above", [10,15,20,22,24,26,30,35], index=4)
FUTURES_RSI_LONG=st.sidebar.selectbox("RSI long above", [50,55,60,65,70,75], index=2)
FUTURES_RSI_SHORT=st.sidebar.selectbox("RSI short below", [25,30,35,40,45,50], index=3)
st.session_state.futures_auto=st.sidebar.toggle("Auto MATRIX 24/7", value=st.session_state.futures_auto)
FUTURES_AUTO_SEC=st.sidebar.selectbox("MATRIX seconds", [60,120,180,300,600], index=2)
FUTURES_HB_MIN=st.sidebar.selectbox("Heartbeat MATRIX min", [15,30,60,90,120], index=2)

if st.sidebar.button("Clear INTEL"):
    st.session_state.intel_found=set()
    st.session_state.intel_history=[]
    st.session_state.top_scores=[]
    st.session_state.last_seen_ticker={}
if st.sidebar.button("Clear OMER"):
    st.session_state.found_db=set()
    st.session_state.history=[]
    st.session_state.pending_breaks={}
if st.sidebar.button("Clear MATRIX"):
    st.session_state.futures_found=set()
    st.session_state.futures_history=[]

@st.cache_data(ttl=3600)
def get_tickers():
    tickers=[]
    for url in ["https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all_tickers.txt","https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nasdaq/nasdaq_tickers.txt"]:
        try:
            df=pd.read_csv(url, header=None)
            tickers.extend(df.iloc[:,0].dropna().astype(str).str.strip().str.upper().tolist())
        except:
            pass
    tickers=list(dict.fromkeys(tickers))
    clean=[t for t in tickers if not (len(t)>=4 and t.endswith('W')) and not t.endswith(('WS','WT','WSW'))]
    return clean if len(clean)>100 else ["AAPL","MSFT","NVDA","TSLA","SPY","QQQ","META","GOOGL","AMZN","BTC-USD","ETH-USD"]

ALL_TICKERS=get_tickers()

def get_batch(smart=False):
    n=min(NUM_SCAN, len(ALL_TICKERS))
    if not smart:
        b=random.sample(ALL_TICKERS, n)
        st.session_state.last_random_batch=b
        return b
    pool=random.sample(ALL_TICKERS, min(600,len(ALL_TICKERS)))
    vol=[]
    for t in pool:
        try:
            df=yf.Ticker(t).history(period="2d", interval="1d", auto_adjust=True)
            if not df.empty:
                vol.append((t,float(df["Volume"].iloc[-1])))
        except:
            pass
    vol.sort(key=lambda x:x[1], reverse=True)
    top=[x[0] for x in vol[:n]]
    st.session_state.last_random_batch=top
    return top

@st.cache_data(ttl=60)
def get_vix_price():
    try:
        df=yf.Ticker("^VIX").history(period="5d", interval="15m", auto_adjust=True)
        return float(df["Close"].iloc[-1]) if not df.empty else 20.0
    except:
        return 20.0

def get_data_unified(tkr, interval, period):
    try:
        tkr=tkr.strip().upper()
        if tkr in ["BTC","ETH","SOL","DOGE","XRP","BNB","ADA","AVAX"]:
            tkr+="-USD"
        df=None
        try:
            df=yf.Ticker(tkr).history(period=period, interval=interval, auto_adjust=True)
        except:
            pass
        if df is None or len(df)<30:
            try:
                df=yf.download(tkr, period=period, interval=interval, progress=False, auto_adjust=True, threads=False)
            except:
                return None,None
        if df is None or len(df)<30:
            return None,None
        if SCAN_2245 and interval=="15m":
            try:
                if df.index.tz is None:
                    df.index=df.index.tz_localize('UTC').tz_convert('Asia/Jerusalem')
                else:
                    df.index=df.index.tz_convert('Asia/Jerusalem')
                today=pd.Timestamp.now(tz='Asia/Jerusalem').normalize()
                days=pd.to_datetime(df.index.normalize().unique())
                past=[d for d in days if d<today]
                if past:
                    last_day_df=df[df.index.normalize()==past[-1]]
                    b=last_day_df.between_time('22:30','22:55')
                    df=df.loc[:b.index[-1] if not b.empty else last_day_df.index[-1]]
            except:
                pass
        c=df["Close"]
        c=c.iloc[:,0] if isinstance(c,pd.DataFrame) else c
        df["BB_L"]=BollingerBands(c,20,2).bollinger_lband()
        df["BB_M"]=BollingerBands(c,20,2).bollinger_mavg()
        df["BB_H"]=BollingerBands(c,20,2).bollinger_hband()
        df["RSI"]=RSIIndicator(c,14).rsi()
        return df.tail(200), tkr
    except:
        return None,None

def calc_score(rsi, vol_ratio, rr, vix, bb_pct, side):
    s=0
    expl=[]
    if side=="BUY":
        s+=2.5 if rsi<15 else 2.2 if rsi<20 else 1.8 if rsi<25 else 1.2 if rsi<30 else 0.5
        expl.append(f"RSI {rsi} BUY")
    else:
        s+=2.5 if rsi>85 else 2.2 if rsi>80 else 1.8 if rsi>75 else 1.2 if rsi>70 else 0.5
        expl.append(f"RSI {rsi} SELL")
    s+=2.0 if vol_ratio>=2.5 else 1.7 if vol_ratio>=2 else 1.3 if vol_ratio>=1.5 else 0.8 if vol_ratio>=1.2 else 0.3
    expl.append(f"VOL x{vol_ratio}")
    s+=2.5 if rr>=3 else 2.0 if rr>=2 else 1.4 if rr>=1.5 else 0.8 if rr>=1 else 0.3
    expl.append(f"RR {rr}")
    s+=1.5 if 20<=vix<=28 else 1.2 if 18<=vix<=32 else 0.8 if vix>32 else 0.6
    expl.append(f"VIX {vix}")
    expl.append(f"BB {bb_pct}%")
    return round(min(10,max(1,s)),1)," | ".join(expl)

def check_intel(tkr):
    per="2y" if INTERVAL=="1d" else "60d" if INTERVAL=="1h" else "20d"
    df,real=get_data_unified(tkr, INTERVAL, per)
    if df is None:
        return None
    try:
        h=float(df["High"].iloc[-1]); l=float(df["Low"].iloc[-1]); o=float(df["Open"].iloc[-1]); c=float(df["Close"].iloc[-1])
        ph=float(df["High"].iloc[-2]); pl=float(df["Low"].iloc[-2])
        bl=float(df["BB_L"].iloc[-1]); pbl=float(df["BB_L"].iloc[-2]); bh=float(df["BB_H"].iloc[-1]); pbh=float(df["BB_H"].iloc[-2])
        bm=float(df["BB_M"].iloc[-1]); crsi=float(df["RSI"].iloc[-1])
        if pd.isna(bl) or pd.isna(bh):
            return None
        v=float(df["Volume"].iloc[-1]); av=float(df["Volume"].rolling(20).mean().iloc[-1]); vr=round(v/av,2) if av>0 else 1.0
        vix=get_vix_price(); bb_b=round((c-bl)/bl*100,2); bb_s=round((c-bh)/bh*100,2); res=[]
        if (h<bl and l<bl and o<bl and c<bl) and (ph>pbl or pl>pbl) and crsi<RSI_L and v>av*VOL_M:
            sl=min(round(l*0.99,2), round(c*(1-SL_PCT/100),2))
            if c-sl<c*0.02:
                sl=round(c*0.96,2)
            rr=min(round((bm-c)/(c-sl),2) if c-sl>0 else 0,6.0)
            score,ex=calc_score(crsi,vr,rr,vix,bb_b,"BUY")
            res.append({"tkr":real,"side":"BUY","price":round(c,2),"low":round(l,4),"tp":round(bm,2),"sl":sl,"pct":round((bm-c)/c*100,2),"rsi":round(crsi,1),"vol":vr,"rr":rr,"vix":round(vix,2),"bb_pct":bb_b,"score":score,"explain":ex,"interval":INTERVAL,"df":df})
        if (h>bh and l>bh and o>bh and c>bh) and (ph<pbh or pl<pbh) and crsi>70 and v>av*VOL_M:
            sl=max(round(h*1.01,2), round(c*(1+SL_PCT/100),2))
            if sl-c<c*0.02:
                sl=round(c*1.04,2)
            rr=min(round((c-bm)/(sl-c),2) if sl-c>0 else 0,6.0)
            score,ex=calc_score(crsi,vr,rr,vix,bb_s,"SELL")
            res.append({"tkr":real,"side":"SELL","price":round(c,2),"high":round(h,4),"tp":round(bm,2),"sl":sl,"pct":round((c-bm)/c*100,2),"rsi":round(crsi,1),"vol":vr,"rr":rr,"vix":round(vix,2),"bb_pct":bb_s,"score":score,"explain":ex,"interval":INTERVAL,"df":df})
        return res
    except:
        return None

def check_omer(tkr):
    per="2y" if INTERVAL=="1d" else "60d" if INTERVAL=="1h" else "20d"
    df,real=get_data_unified(tkr, INTERVAL, per)
    if df is None:
        return None
    try:
        h=float(df["High"].iloc[-1]); l=float(df["Low"].iloc[-1]); o=float(df["Open"].iloc[-1]); c=float(df["Close"].iloc[-1])
        ph=float(df["High"].iloc[-2]); pl=float(df["Low"].iloc[-2]); pc=float(df["Close"].iloc[-2])
        bl=float(df["BB_L"].iloc[-1]); pbl=float(df["BB_L"].iloc[-2]); bm=float(df["BB_M"].iloc[-1])
        crsi=float(df["RSI"].iloc[-1]); prsi=float(df["RSI"].iloc[-2])
        if pd.isna(bl):
            return None
        vol_ok=True
        if "-USD" not in real:
            v=float(df["Volume"].iloc[-1]); av=float(df["Volume"].rolling(20).mean().iloc[-1]); vol_ok=v>av*VOL_M
        is_break=(h<bl and l<bl and o<bl and c<bl) and (ph>pbl or pl>pbl) and crsi<RSI_L and vol_ok
        stopped=(c>pc) and (l>float(df["Low"].iloc[-2])) and (crsi>prsi)
        return {"tkr":real,"price":round(c,2),"low":round(l,4),"tp":round(bm,2),"pct":round((bm-c)/c*100,2),"rsi":round(crsi,1),"interval":"15m-22:45" if SCAN_2245 else INTERVAL,"df":df,"is_break":is_break,"stopped":stopped,"close":c}
    except:
        return None

def check_futures(tkr):
    per="7d" if FUTURES_INTERVAL in ["2m","5m"] else "60d" if FUTURES_INTERVAL in ["15m","1h"] else "2y"
    df,_=get_data_unified(tkr, FUTURES_INTERVAL, per)
    if df is None:
        return None
    try:
        c=float(df["Close"].iloc[-1]); pc=float(df["Close"].iloc[-2]); bh=float(df["BB_H"].iloc[-1]); bl=float(df["BB_L"].iloc[-1])
        pbh=float(df["BB_H"].iloc[-2]); pbl=float(df["BB_L"].iloc[-2]); bm=float(df["BB_M"].iloc[-1]); crsi=float(df["RSI"].iloc[-1]); vix=get_vix_price()
        is_long=c>bh and pc<=pbh and crsi>FUTURES_RSI_LONG and vix>FUTURES_VIX_LVL
        is_short=c<bl and pc>=pbl and crsi<FUTURES_RSI_SHORT and vix>FUTURES_VIX_LVL
        sl=bm
        tp=c+(c-sl)*1.8 if is_long else c-(sl-c)*1.8 if is_short else bm
        side="LONG" if is_long else "SHORT" if is_short else "NONE"
        return {"tkr":tkr,"price":round(c,2),"side":side,"entry":round(c,2),"sl":round(sl,2),"tp":round(tp,2),"rsi":round(crsi,1),"vix":round(vix,2),"bh":round(bh,2),"bl":round(bl,2),"bm":round(bm,2),"interval":FUTURES_INTERVAL,"df":df,"is_long":is_long,"is_short":is_short}
    except:
        return None

def plot_chart(df,tkr):
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name=tkr))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_H'], line=dict(color='rgba(255,0,0,0.3)'), name="BB Upper"))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_L'], line=dict(color='rgba(0,255,0,0.7)', width=2), name="BB Lower"))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_M'], line=dict(color='orange', dash='dash'), name="TP"))
    fig.update_layout(height=550, title=f"{tkr}", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    fig2=go.Figure()
    fig2.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI"))
    fig2.update_layout(height=200, title="RSI")
    st.plotly_chart(fig2, use_container_width=True)

def run_intel_scan():
    batch=get_batch(smart=True); new=0; now=time.time()
    for tk in batch:
        if tk in st.session_state.last_seen_ticker and now-st.session_state.last_seen_ticker[tk] < INTEL_COOLDOWN*60:
            continue
        rl=check_intel(tk)
        if not rl:
            continue
        for r in rl:
            if INTEL_MODE=="BUY ONLY" and r["side"]!="BUY":
                continue
            if INTEL_MODE=="SELL ONLY" and r["side"]!="SELL":
                continue
            if r["score"]<INTEL_MIN_SCORE:
                continue
            key=f"{r['tkr']}_{r['side']}_{r['price']}_{now_il_str('%Y%m%d%H')}"
            if key in st.session_state.intel_found:
                continue
            st.session_state.intel_found.add(key)
            rec={"time":now_il_str("%H:%M:%S %d/%m"),"tkr":r["tkr"],"side":r["side"],"score":r["score"],"entry":r["price"],"tp":r["tp"],"sl":r["sl"],"pct":r["pct"],"rsi":r["rsi"],"vol":r["vol"],"rr":r["rr"],"vix":r["vix"],"bb_pct":r["bb_pct"],"explain":r["explain"],"interval":r["interval"]}
            st.session_state.intel_history.append(rec)
            st.session_state.top_scores.append(rec)
            st.session_state.last_seen_ticker[tk]=now
            new+=1
            tg(f"{r['side']} INTEL {r['tkr']} SCORE {r['score']}/10 Entry {r['price']} TP {r['tp']} SL {r['sl']} | RSI {r['rsi']} VOL x{r['vol']} RR {r['rr']} VIX {r['vix']}")
    if st.session_state.top_scores:
        df=pd.DataFrame(st.session_state.top_scores).sort_values(by="score", ascending=False).drop_duplicates(subset=["tkr","side"], keep="first").head(20)
        st.session_state.top_scores=df.to_dict("records")
    st.session_state.intel_last_scan=now_il_str("%H:%M:%S %d/%m")
    st.session_state.intel_scan_count+=1
    return new,batch

def run_one_scan():
    nb=0; nbuy=0; batch=get_batch(smart=False)
    for tk in batch:
        r=check_omer(tk)
        if not r:
            continue
        if r["is_break"]:
            k=f"{r['tkr']}_{r['interval']}_{r['price']}"
            if k not in st.session_state.found_db:
                st.session_state.found_db.add(k)
                st.session_state.history.append({kk:vv for kk,vv in r.items() if kk!='df'})
                st.session_state.pending_breaks[r['tkr']]={'low':r['low'],'price':r['price'],'time':str(now_il())}
                nb+=1
                tg(f"FULL BREAK {r['tkr']} ${r['price']} -> {r['tp']} (+{r['pct']}%) RSI {r['rsi']} [{r['interval']}]")
    for tkr in list(st.session_state.pending_breaks.keys()):
        r=check_omer(tkr)
        if not r:
            continue
        if r['stopped'] and r['low']>st.session_state.pending_breaks[tkr]['low']:
            nbuy+=1
            tg(f"Buy signal {r['tkr']} ${r['price']}")
            del st.session_state.pending_breaks[tkr]
    st.session_state.last_scan_time=now_il_str("%H:%M:%S %d/%m")
    st.session_state.scan_count+=1
    return nb,nbuy

def run_futures_scan():
    nl=0; ns=0; vix=get_vix_price()
    for tk in FUTURES_TICKERS:
        rf=check_futures(tk)
        if not rf:
            continue
        key=f"{rf['tkr']}_{rf['interval']}_{rf['side']}_{rf['price']}_{now_il_str('%Y%m%d%H')}"
        if (rf["is_long"] or rf["is_short"]) and key not in st.session_state.futures_found:
            st.session_state.futures_found.add(key)
            st.session_state.futures_history.append(rf)
            if rf["is_long"]:
                nl+=1
                tg(f"MATRIX LONG {rf['tkr']} Entry {rf['entry']} SL {rf['sl']} TP {rf['tp']} RSI {rf['rsi']} VIX {rf['vix']}")
            else:
                ns+=1
                tg(f"MATRIX SHORT {rf['tkr']} Entry {rf['entry']} SL {rf['sl']} TP {rf['tp']} RSI {rf['rsi']} VIX {rf['vix']}")
    st.session_state.futures_last_scan=now_il_str("%H:%M:%S %d/%m")
    st.session_state.futures_scan_count+=1
    return nl,ns,vix

st.title("INTELLIGENT SECURE LITE 60s + OMER + MATRIX")
st.caption(f"Tickers: {len(ALL_TICKERS)} | VIX: {get_vix_price():.2f} | Time IL: {now_il_str('%H:%M:%S')} | Lines 320")

st.header("INTELLIGENT SCAN - Every 60 sec hottest volume - REAL SL")
if st.session_state.intel_last_scan:
    st.info(f"INTEL Last: {st.session_state.intel_last_scan} | Scans: {st.session_state.intel_scan_count} | TOP: {len(st.session_state.top_scores)}")
c1,c2=st.columns(2)
with c1:
    if st.button("Scan smart now 200 hottest", use_container_width=True, type="primary"):
        with st.spinner("Scanning..."):
            nc,batch=run_intel_scan()
            st.success(f"Scanned {len(batch)} | New {nc} SCORE {INTEL_MIN_SCORE}+")
with c2:
    manual=st.text_input("Manual INTEL check", placeholder="TSLA / NVDA")
    if st.button("Check INTEL manual", use_container_width=True):
        rl=check_intel(manual) if manual else None
        if rl:
            for r in rl:
                st.write(f"{r['side']} {r['tkr']} SCORE {r['score']} Entry {r['price']} TP {r['tp']} SL {r['sl']} RR {r['rr']}")
                plot_chart(r["df"], r["tkr"])
        else:
            st.error("No signal")

if st.session_state.top_scores:
    st.subheader("TOP SCORES - REAL SL FIXED")
    df_top=pd.DataFrame(st.session_state.top_scores)
    st.dataframe(df_top[["score","tkr","side","entry","tp","sl","pct","rsi","vol","rr","vix","bb_pct","explain","time"]].sort_values(by="score", ascending=False), use_container_width=True, height=400)
if st.session_state.intel_history:
    st.subheader(f"History INTELLIGENT - {len(st.session_state.intel_history)}")
    st.dataframe(pd.DataFrame(st.session_state.intel_history[::-1]), use_container_width=True)

st.divider()
st.header("OMER - ORIGINAL")
if st.session_state.last_scan_time:
    st.info(f"OMER Last: {st.session_state.last_scan_time} | Scans: {st.session_state.scan_count} | Pending: {len(st.session_state.pending_breaks)}")
if st.session_state.pending_breaks:
    st.dataframe(pd.DataFrame.from_dict(st.session_state.pending_breaks, orient='index'), use_container_width=True)
if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history[::-1]).drop(columns=['df'], errors='ignore'), use_container_width=True)

st.divider()
st.header("MATRIX BREAKER FUTURES")
if st.session_state.futures_last_scan:
    st.info(f"MATRIX Last: {st.session_state.futures_last_scan} | Scans: {st.session_state.futures_scan_count} | VIX: {get_vix_price():.2f}")
if st.session_state.futures_history:
    st.dataframe(pd.DataFrame([{k:v for k,v in x.items() if k!='df'} for x in st.session_state.futures_history[::-1]]), use_container_width=True)

auto_any=st.session_state.intel_auto or st.session_state.auto_scan or st.session_state.futures_auto
if auto_any:
    st.divider()
    st.warning(f"AUTO 24/7 ACTIVE - INTEL:{st.session_state.intel_auto} OMER:{st.session_state.auto_scan} MATRIX:{st.session_state.futures_auto} - {now_il_str('%H:%M:%S')} IL")
    if st.session_state.intel_auto:
        nc,_=run_intel_scan()
        st.write(f"INTEL #{st.session_state.intel_scan_count} New {nc}")
        if time.time()-st.session_state.intel_heartbeat>3600:
            tg(f"INTEL alive {now_il_str('%H:%M:%S')} TOP {len(st.session_state.top_scores)} VIX {get_vix_price():.2f}")
            st.session_state.intel_heartbeat=time.time()
    if st.session_state.auto_scan:
        nb,nbuy=run_one_scan()
        st.write(f"OMER #{st.session_state.scan_count} Breaks {nb} Buys {nbuy}")
        if time.time()-st.session_state.last_heartbeat>HEARTBEAT_MIN*60:
            tg(f"OMER alive {now_il_str('%H:%M:%S')} pending {len(st.session_state.pending_breaks)}")
            st.session_state.last_heartbeat=time.time()
    if st.session_state.futures_auto:
        nl,ns,vix_now=run_futures_scan()
        st.write(f"MATRIX #{st.session_state.futures_scan_count} L:{nl} S:{ns} VIX:{vix_now:.2f}")
        if time.time()-st.session_state.futures_heartbeat>FUTURES_HB_MIN*60:
            tg(f"MATRIX alive {now_il_str('%H:%M:%S')} VIX {vix_now:.2f}")
            st.session_state.futures_heartbeat=time.time()
    sleep_sec=min([s for s in [60, AUTO_SEC if st.session_state.auto_scan else 9999, FUTURES_AUTO_SEC if st.session_state.futures_auto else 9999]])
    ph=st.empty()
    for sec in range(sleep_sec,0,-1):
        ph.caption(f"Next scan in {sec} sec - {now_il_str('%H:%M:%S')} IL")
        time.sleep(1)
    ph.empty()
    st.rerun()
