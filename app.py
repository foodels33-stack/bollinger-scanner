import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
import plotly.graph_objects as go
import time
from datetime import datetime
import pytz
import random
import streamlit.components.v1 as components

JERUSALEM_TZ = pytz.timezone('Asia/Jerusalem')
def now_il():
    return datetime.now(JERUSALEM_TZ)
def now_il_str(fmt="%H:%M:%S"):
    return now_il().strftime(fmt)

st.set_page_config(page_title="FULL INTELLIGENT AUTO 60s", layout="wide")
components.html("<script>setInterval(()=>{fetch(window.location.href,{mode:'no-cors'})},60000);</script>", height=0)

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
    st.session_state.futures_found=set()
    st.session_state.futures_history=[]
    st.session_state.futures_last_scan=None
    st.session_state.futures_auto=False
    st.session_state.futures_scan_count=0
    st.session_state.futures_heartbeat=0
    st.session_state.intel_auto=False
    st.session_state.intel_history=[]
    st.session_state.intel_found=set()
    st.session_state.intel_last_scan=None
    st.session_state.intel_scan_count=0
    st.session_state.intel_heartbeat=0
    st.session_state.top_scores=[]
    st.session_state.last_seen_ticker={}

if not st.session_state.ok:
    p=st.text_input("Password", type="password")
    if st.button("Login"):
        if p=="1234":
            st.session_state.ok=True
            st.rerun()
    st.stop()

DEFAULT_BOT = st.secrets.get("BOT_TOKEN", "8857531191:AAFFGNJjEbO-1HPofP_hozyqqp0ieCMa_FY")
DEFAULT_CHAT = st.secrets.get("CHAT_ID", "6649894327,-1004229452727")
BOT=st.sidebar.text_input("Bot Token", value=DEFAULT_BOT, type="password")
CHAT=st.sidebar.text_input("Chat IDs comma separated", value=DEFAULT_CHAT)

if st.sidebar.button("TEST BOT"):
    try:
        chat_list=[c.strip() for c in CHAT.split(",") if c.strip()]
        for cid in chat_list:
            r=requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id": cid, "text": "TEST OK - OMER+GROUP"}, timeout=15)
            st.sidebar.write(f"{cid} -> {r.status_code}")
        st.sidebar.success("Sent to all")
    except Exception as e:
        st.sidebar.error(str(e))

st.sidebar.divider()
st.sidebar.subheader("INTELLIGENT AUTO 60 SEC")
st.session_state.intel_auto=st.sidebar.toggle("AUTO INTELLIGENT 60s FIXED", value=st.session_state.intel_auto)
INTEL_MIN_SCORE=st.sidebar.slider("Send only SCORE above", 1, 10, 8)
INTEL_COOLDOWN=st.sidebar.slider("No repeat ticker minutes", 1, 30, 10)
INTEL_MODE=st.sidebar.selectbox("Scan type", ["BUY+SELL", "BUY ONLY", "SELL ONLY"], index=0)

if st.sidebar.button("Clear INTELLIGENT"):
    st.session_state.intel_found=set()
    st.session_state.intel_history=[]
    st.session_state.top_scores=[]
    st.session_state.last_seen_ticker={}
    st.sidebar.success("Cleared INTEL")

st.sidebar.divider()
st.sidebar.subheader("BOLLINGER OMER")
INTERVAL=st.sidebar.selectbox("Interval", ["1d","1h","15m"], index=0)
RSI_L=st.sidebar.slider("RSI under", 10, 40, 25)
VOL_M=st.sidebar.slider("Vol X", 1.0, 3.0, 1.5)
NUM_SCAN=st.sidebar.slider("How many to scan", 10, 3500, 200, step=10)
SCAN_2245=st.sidebar.checkbox("Scan yesterday 22:45")
st.session_state.auto_scan=st.sidebar.toggle("Auto OMER 24/7", value=st.session_state.auto_scan)
AUTO_SEC=st.sidebar.slider("OMER seconds", 60, 600, 300, step=30)
HEARTBEAT_MIN=st.sidebar.slider("Heartbeat OMER min", 15, 120, 60)

st.sidebar.divider()
st.sidebar.subheader("MATRIX FUTURES")
FUTURES_TICKERS=["ES=F","NQ=F","RTY=F"]
FUTURES_INTERVAL=st.sidebar.selectbox("Futures Interval", ["2m","5m","15m","1h","4h"], index=2)
FUTURES_VIX_LVL=st.sidebar.slider("VIX above", 10, 35, 24)
FUTURES_RSI_LONG=st.sidebar.slider("RSI long above", 50, 75, 60)
FUTURES_RSI_SHORT=st.sidebar.slider("RSI short below", 25, 50, 40)
st.session_state.futures_auto=st.sidebar.toggle("Auto MATRIX 24/7", value=st.session_state.futures_auto)
FUTURES_AUTO_SEC=st.sidebar.slider("MATRIX seconds", 60, 600, 180, step=30)
FUTURES_HB_MIN=st.sidebar.slider("Heartbeat MATRIX min", 15, 120, 60)

if st.sidebar.button("Clear OMER"):
    st.session_state.found_db=set()
    st.session_state.history=[]
    st.session_state.pending_breaks={}
    st.session_state.last_random_batch=[]
    st.sidebar.success("Cleared")
if st.sidebar.button("Clear MATRIX"):
    st.session_state.futures_found=set()
    st.session_state.futures_history=[]
    st.sidebar.success("Cleared")

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

def get_smart_volume_batch():
    try:
        pool_size=min(600, len(ALL_TICKERS))
        pool=random.sample(ALL_TICKERS, pool_size)
        vol_list=[]
        for t in pool:
            try:
                df=yf.Ticker(t).history(period="2d", interval="1d", auto_adjust=True)
                if df.empty: continue
                v=float(df["Volume"].iloc[-1])
                if v>0:
                    vol_list.append((t, v))
            except:
                continue
        vol_list.sort(key=lambda x: x[1], reverse=True)
        top=[x[0] for x in vol_list[:NUM_SCAN]]
        if len(top)<NUM_SCAN:
            extra=random.sample(ALL_TICKERS, NUM_SCAN-len(top))
            top.extend(extra)
        st.session_state.last_random_batch=top
        return top
    except:
        return get_random_batch()

def tg(m):
    if not BOT or not CHAT:
        return
    chat_list=[c.strip() for c in CHAT.split(",") if c.strip()]
    for cid in chat_list:
        try:
            requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id": cid, "text": m}, timeout=10)
        except:
            pass

@st.cache_data(ttl=60)
def get_vix_price():
    try:
        df=yf.Ticker("^VIX").history(period="5d", interval="15m", auto_adjust=True)
        if df is None or df.empty:
            return 20.0
        return float(df["Close"].iloc[-1])
    except:
        return 20.0

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
            except:
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

def calc_intel_score(rsi, vol_ratio, rr, vix, bb_pct, side):
    score=0
    explain=[]
    if side=="BUY":
        if rsi<15: s=2.5
        elif rsi<20: s=2.2
        elif rsi<25: s=1.8
        elif rsi<30: s=1.2
        else: s=0.5
        explain.append(f"RSI {rsi} BUY")
    else:
        if rsi>85: s=2.5
        elif rsi>80: s=2.2
        elif rsi>75: s=1.8
        elif rsi>70: s=1.2
        else: s=0.5
        explain.append(f"RSI {rsi} SELL")
    score+=s
    if vol_ratio>=2.5: s=2.0
    elif vol_ratio>=2.0: s=1.7
    elif vol_ratio>=1.5: s=1.3
    elif vol_ratio>=1.2: s=0.8
    else: s=0.3
    score+=s
    explain.append(f"VOL x{vol_ratio}")
    if rr>=3: s=2.5
    elif rr>=2: s=2.0
    elif rr>=1.5: s=1.4
    elif rr>=1: s=0.8
    else: s=0.3
    score+=s
    explain.append(f"RR {rr}")
    if 20<=vix<=28: s=1.5
    elif 18<=vix<=32: s=1.2
    elif vix>32: s=0.8
    else: s=0.6
    score+=s
    explain.append(f"VIX {vix}")
    if side=="BUY":
        if bb_pct<-5: s=1.5
        elif bb_pct<-2: s=1.2
        elif bb_pct<0: s=0.9
        else: s=0.4
    else:
        if bb_pct>5: s=1.5
        elif bb_pct>2: s=1.2
        elif bb_pct>0: s=0.9
        else: s=0.4
    score+=s
    explain.append(f"BB {bb_pct}%")
    return round(min(10, max(1, score)),1), " | ".join(explain)

def check_intel(tkr):
    df, real_tkr=get_data(tkr)
    if df is None: return None
    try:
        h=float(df["High"].iloc[-1]); l=float(df["Low"].iloc[-1]); o=float(df["Open"].iloc[-1]); c=float(df["Close"].iloc[-1])
        ph=float(df["High"].iloc[-2]); pl=float(df["Low"].iloc[-2])
        bl=float(df["BB_L"].iloc[-1]); pbl=float(df["BB_L"].iloc[-2]); bh=float(df["BB_H"].iloc[-1]); pbh=float(df["BB_H"].iloc[-2]); bm=float(df["BB_M"].iloc[-1])
        crsi=float(df["RSI"].iloc[-1])
        if pd.isna(bl) or pd.isna(bh): return None
        v=float(df["Volume"].iloc[-1]); av=float(df["Volume"].rolling(20).mean().iloc[-1]); vol_ratio=round(v/av,2) if av>0 else 1.0
        vix=get_vix_price()
        bb_pct_buy=round((c-bl)/bl*100,2); bb_pct_sell=round((c-bh)/bh*100,2)
        results=[]
        full_break_down=(h<bl) and (l<bl) and (o<bl) and (c<bl)
        prev_inside_down=(ph>pbl) or (pl>pbl)
        vol_ok=v>av*VOL_M
        pct_buy=(bm-c)/c*100 if c!=0 else 0
        risk_buy=c-l
        reward_buy=bm-c
        rr_buy=round(reward_buy/risk_buy,2) if risk_buy>0 else 0.5
        is_buy=full_break_down and prev_inside_down and (crsi<RSI_L) and vol_ok
        if is_buy:
            score, expl=calc_intel_score(crsi, vol_ratio, rr_buy, vix, bb_pct_buy, "BUY")
            results.append({"tkr":real_tkr,"side":"BUY","price":round(c,2),"low":round(l,4),"tp":round(bm,2),"sl":round(l,2),"pct":round(pct_buy,2),"rsi":round(crsi,1),"vol":vol_ratio,"rr":rr_buy,"vix":round(vix,2),"bb_pct":bb_pct_buy,"score":score,"explain":expl,"interval":INTERVAL,"df":df})
        full_break_up=(h>bh) and (l>bh) and (o>bh) and (c>bh)
        prev_inside_up=(ph<pbh) or (pl<pbh)
        pct_sell=(c-bm)/c*100 if c!=0 else 0
        risk_sell=h-c
        reward_sell=c-bm
        rr_sell=round(reward_sell/risk_sell,2) if risk_sell>0 else 0.5
        is_sell=full_break_up and prev_inside_up and (crsi>70) and vol_ok
        if is_sell:
            score, expl=calc_intel_score(crsi, vol_ratio, rr_sell, vix, bb_pct_sell, "SELL")
            results.append({"tkr":real_tkr,"side":"SELL","price":round(c,2),"high":round(h,4),"tp":round(bm,2),"sl":round(h,2),"pct":round(pct_sell,2),"rsi":round(crsi,1),"vol":vol_ratio,"rr":rr_sell,"vix":round(vix,2),"bb_pct":bb_pct_sell,"score":score,"explain":expl,"interval":INTERVAL,"df":df})
        return results
    except:
        return None

def check(tkr):
    df, real_tkr=get_data(tkr)
    if df is None:
        return None
    try:
        h=float(df["High"].iloc[-1]); l=float(df["Low"].iloc[-1]); o=float(df["Open"].iloc[-1]); c=float(df["Close"].iloc[-1])
        ph=float(df["High"].iloc[-2]); pl=float(df["Low"].iloc[-2]); pc=float(df["Close"].iloc[-2])
        bl=float(df["BB_L"].iloc[-1]); pbl=float(df["BB_L"].iloc[-2]); bm=float(df["BB_M"].iloc[-1])
        crsi=float(df["RSI"].iloc[-1]); prsi=float(df["RSI"].iloc[-2])
        if pd.isna(bl) or pd.isna(pbl): return None
        full_break=(h<bl) and (l<bl) and (o<bl) and (c<bl)
        prev_inside=(ph>pbl) or (pl>pbl)
        vol_ok=True
        if "-USD" not in real_tkr:
            v=float(df["Volume"].iloc[-1]); av=float(df["Volume"].rolling(20).mean().iloc[-1]); vol_ok=v>av*VOL_M
        pct=(bm-c)/c*100 if c!=0 else 0
        is_break=full_break and prev_inside and (crsi<RSI_L) and vol_ok
        stopped_break=(c>pc) and (l>float(df["Low"].iloc[-2])) and (crsi>prsi)
        interval_name="15m-22:45" if SCAN_2245 else INTERVAL
        return {"tkr": real_tkr, "price": round(c,2), "low": round(l,4), "tp": round(bm,2), "pct": round(pct,2), "rsi": round(crsi,1), "interval": interval_name, "df": df, "is_break": is_break, "stopped": stopped_break, "close": c}
    except:
        return None

def get_futures_data(tkr):
    try:
        if FUTURES_INTERVAL in ["2m","5m"]: per="7d"
        elif FUTURES_INTERVAL in ["15m","1h"]: per="60d"
        else: per="2y"
        df=None
        try: df=yf.Ticker(tkr).history(period=per, interval=FUTURES_INTERVAL, auto_adjust=True)
        except: df=None
        if df is None or len(df)<30:
            try: df=yf.download(tkr, period=per, interval=FUTURES_INTERVAL, progress=False, auto_adjust=True, threads=False)
            except: df=None
        if df is None or len(df)<30: return None
        close=df["Close"]
        if isinstance(close, pd.DataFrame): close=close.iloc[:,0]
        df["BB_L"]=BollingerBands(close, 20, 2).bollinger_lband()
        df["BB_M"]=BollingerBands(close, 20, 2).bollinger_mavg()
        df["BB_H"]=BollingerBands(close, 20, 2).bollinger_hband()
        df["RSI"]=RSIIndicator(close, 14).rsi()
        return df.tail(200)
    except:
        return None

def check_futures(tkr):
    df=get_futures_data(tkr)
    if df is None: return None
    try:
        c=float(df["Close"].iloc[-1]); pc=float(df["Close"].iloc[-2]); bh=float(df["BB_H"].iloc[-1]); bl=float(df["BB_L"].iloc[-1]); pbh=float(df["BB_H"].iloc[-2]); pbl=float(df["BB_L"].iloc[-2]); bm=float(df["BB_M"].iloc[-1]); crsi=float(df["RSI"].iloc[-1]); vix=get_vix_price()
        if pd.isna(bh) or pd.isna(bl): return None
        long_prev_inside=pc <= pbh; long_break=c > bh; long_rsi=crsi > FUTURES_RSI_LONG; long_vix=vix > FUTURES_VIX_LVL
        is_long=long_break and long_prev_inside and long_rsi and long_vix
        short_prev_inside=pc >= pbl; short_break=c < bl; short_rsi=crsi < FUTURES_RSI_SHORT; short_vix=vix > FUTURES_VIX_LVL
        is_short=short_break and short_prev_inside and short_rsi and short_vix
        entry=c
        if is_long:
            sl=bm; risk=entry-sl; tp=entry + risk*1.8 if risk>0 else entry*1.01; side="LONG"
        elif is_short:
            sl=bm; risk=sl-entry; tp=entry - risk*1.8 if risk>0 else entry*0.99; side="SHORT"
        else:
            sl=bm; tp=bm; side="NONE"
        return {"tkr": tkr, "price": round(c,2), "side": side, "entry": round(entry,2), "sl": round(sl,2), "tp": round(tp,2), "rsi": round(crsi,1), "vix": round(vix,2), "bh": round(bh,2), "bl": round(bl,2), "bm": round(bm,2), "interval": FUTURES_INTERVAL, "df": df, "is_long": is_long, "is_short": is_short}
    except:
        return None

def plot_chart(df, tkr):
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name=tkr))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_H'], line=dict(color='rgba(255,0,0,0.3)'), name="BB Upper"))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_L'], line=dict(color='rgba(0,255,0,0.7)', width=2), name="BB Lower"))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_M'], line=dict(color='orange', dash='dash'), name="TP"))
    fig.update_layout(height=550, title=f"{tkr}", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    fig2=go.Figure()
    fig2.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI"))
    if tkr in FUTURES_TICKERS:
        fig2.add_hline(y=FUTURES_RSI_LONG, line_dash="dash", line_color="green")
        fig2.add_hline(y=FUTURES_RSI_SHORT, line_dash="dash", line_color="red")
    else:
        fig2.add_hline(y=RSI_L, line_dash="dash", line_color="red")
    fig2.update_layout(height=200, title="RSI")
    st.plotly_chart(fig2, use_container_width=True)

def run_intel_scan():
    batch=get_smart_volume_batch()
    new_count=0
    now_ts=time.time()
    for tk in batch:
        if tk in st.session_state.last_seen_ticker:
            if now_ts - st.session_state.last_seen_ticker[tk] < INTEL_COOLDOWN*60:
                continue
        res_list=check_intel(tk)
        if not res_list: continue
        for r in res_list:
            if INTEL_MODE=="BUY ONLY" and r["side"]!="BUY": continue
            if INTEL_MODE=="SELL ONLY" and r["side"]!="SELL": continue
            if r["score"] < INTEL_MIN_SCORE: continue
            key=f"{r['tkr']}_{r['side']}_{r['price']}_{now_il_str('%Y%m%d%H')}"
            if key in st.session_state.intel_found: continue
            st.session_state.intel_found.add(key)
            full_record={
                "time": now_il_str("%H:%M:%S %d/%m"),
                "tkr": r["tkr"],
                "side": r["side"],
                "score": r["score"],
                "entry": r["price"],
                "tp": r["tp"],
                "sl": r["sl"],
                "pct": r["pct"],
                "rsi": r["rsi"],
                "vol": r["vol"],
                "rr": r["rr"],
                "vix": r["vix"],
                "bb_pct": r["bb_pct"],
                "explain": r["explain"],
                "interval": r["interval"]
            }
            st.session_state.intel_history.append(full_record)
            st.session_state.top_scores.append(full_record)
            st.session_state.last_seen_ticker[tk]=now_ts
            new_count+=1
            emoji="BUY" if r["side"]=="BUY" else "SELL"
            msg=f"{emoji} INTEL {r['side']} {r['tkr']} SCORE {r['score']}/10 Entry {r['price']} -> TP {r['tp']} ({r['pct']}%) SL {r['sl']} | RSI {r['rsi']} VOL x{r['vol']} RR {r['rr']} VIX {r['vix']} BB {r['bb_pct']}% | {r['explain']} [{r['interval']}]"
            tg(msg)
    if st.session_state.top_scores:
        df_top=pd.DataFrame(st.session_state.top_scores)
        df_top=df_top.sort_values(by="score", ascending=False).drop_duplicates(subset=["tkr","side"], keep="first").head(20)
        st.session_state.top_scores=df_top.to_dict("records")
    st.session_state.intel_last_scan=now_il_str("%H:%M:%S %d/%m")
    st.session_state.intel_scan_count+=1
    return new_count, batch

st.title("INTELLIGENT AUTO 60s + OMER + MATRIX")
st.caption(f"Tickers: {len(ALL_TICKERS)} | VIX: {get_vix_price():.2f} | Time IL: {now_il_str('%H:%M:%S')} | AUTO 60s FIXED")

st.header("INTELLIGENT SCAN - Every 60 sec different 200 hottest volume")
if st.session_state.intel_last_scan:
    st.info(f"INTEL Last: {st.session_state.intel_last_scan} | Scans: {st.session_state.intel_scan_count} | TOP: {len(st.session_state.top_scores)} | History: {len(st.session_state.intel_history)}")
else:
    st.info("INTEL Ready - Turn AUTO ON at top. Every 60 sec scans 200 hottest volume now")

c_int1,c_int2=st.columns(2)
with c_int1:
    if st.button("Scan smart now 200 hottest", use_container_width=True, type="primary"):
        with st.spinner("Scanning 200 hottest volume now..."):
            nc, batch = run_intel_scan()
            st.success(f"Scanned {len(batch)} | New {nc} with SCORE {INTEL_MIN_SCORE}+")
            if nc==0:
                st.warning("No new above threshold - try lower SCORE to 7")
with c_int2:
    manual_intel=st.text_input("Manual INTEL check", placeholder="TSLA / NVDA", key="manual_intel_input")
    if st.button("Check INTEL manual", use_container_width=True):
        rl=check_intel(manual_intel) if manual_intel else None
        if rl:
            for r in rl:
                st.write(f"{r['side']} {r['tkr']} SCORE {r['score']} Entry {r['price']} TP {r['tp']} SL {r['sl']} {r['explain']}")
                plot_chart(r["df"], r["tkr"])
        else:
            st.error("No signal")

if st.session_state.top_scores:
    st.subheader("TOP SCORES - Sorted by score - Live updating every 60 sec")
    df_top=pd.DataFrame(st.session_state.top_scores)
    st.dataframe(df_top[["score","tkr","side","entry","tp","sl","pct","rsi","vol","rr","vix","bb_pct","explain","time"]].sort_values(by="score", ascending=False), use_container_width=True, height=400)

if st.session_state.intel_history:
    st.subheader(f"History INTELLIGENT full explain - {len(st.session_state.intel_history)}")
    dfh=pd.DataFrame(st.session_state.intel_history[::-1])
    st.dataframe(dfh, use_container_width=True)

if st.session_state.intel_auto:
    st.warning(f"AUTO INTELLIGENT running - scanning 200 different every 60 sec FIXED - {now_il_str('%H:%M:%S')} IL")
    nc, batch = run_intel_scan()
    st.write(f"Scan #{st.session_state.intel_scan_count} | Checked {len(batch)} hottest | New {nc} | TOP {len(st.session_state.top_scores)}")
    now=time.time()
    if now - st.session_state.intel_heartbeat > 3600:
        tg(f"INTEL alive {now_il_str('%H:%M:%S')} TOP {len(st.session_state.top_scores)} history {len(st.session_state.intel_history)} VIX {get_vix_price():.2f}")
        st.session_state.intel_heartbeat=now
    ph=st.empty()
    for sec in range(60, 0, -1):
        ph.caption(f"Next INTEL smart scan in {sec} sec - 200 different hottest - {now_il_str('%H:%M:%S')} IL")
        time.sleep(1)
    ph.empty()
    st.rerun()

st.divider()
st.header("OMER - ORIGINAL")
mode_text="yesterday 22:45" if SCAN_2245 else "LIVE"
if st.session_state.last_scan_time:
    now_ts=time.time()
    hb_diff=int(now_ts - st.session_state.last_heartbeat) if st.session_state.last_heartbeat else 0
    is_alive=hb_diff < (HEARTBEAT_MIN*60*2.5)
    alive_icon="LIVE" if is_alive else "SLEEP"
    st.info(f"OMER - Last: {st.session_state.last_scan_time} | Scans: {st.session_state.scan_count} | Pending: {len(st.session_state.pending_breaks)} | Status: {alive_icon}")
c1,c2=st.columns(2)
with c1:
    manual=st.text_input("Ticker OMER", placeholder="TSLA / BTC")
with c2:
    st.write("")
    btn=st.button("Check + Chart OMER", use_container_width=True, type="primary")
if btn and manual:
    r=check(manual)
    if r and r["df"] is not None:
        st.write(f"{r['tkr']} ${r['price']} RSI {r['rsi']}")
        plot_chart(r["df"], r["tkr"])
    else:
        st.error("No data")

def run_one_scan():
    new_break=0; new_buy=0
    batch=get_random_batch()
    for tk in batch:
        r=check(tk)
        if not r: continue
        if r["is_break"]:
            key=f"{r['tkr']}_{r['interval']}_{r['price']}"
            if key not in st.session_state.found_db:
                st.session_state.found_db.add(key)
                st.session_state.history.append({k:v for k,v in r.items() if k!='df'})
                st.session_state.pending_breaks[r['tkr']]={'low': r['low'], 'price': r['price'], 'time': str(now_il())}
                new_break+=1
                tg(f"FULL BREAK {r['tkr']} ${r['price']} -> {r['tp']} (+{r['pct']}%) RSI {r['rsi']} [{r['interval']}] RANDOM")
    for pend_tkr in list(st.session_state.pending_breaks.keys()):
        r=check(pend_tkr)
        if not r: continue
        prev=st.session_state.pending_breaks[pend_tkr]
        if r['stopped'] and r['low'] > prev['low']:
            new_buy+=1
            tg(f"Buy signal {r['tkr']} ${r['price']} RANDOM")
            del st.session_state.pending_breaks[pend_tkr]
    st.session_state.last_scan_time=now_il_str("%H:%M:%S %d/%m")
    st.session_state.scan_count+=1
    return new_break, new_buy

if st.button(f"Scan {NUM_SCAN} random OMER - {mode_text}", use_container_width=True):
    prog=st.progress(0); stat=st.empty()
    batch=get_random_batch(); new_b=0
    for i, tk in enumerate(batch):
        stat.text(f"{i+1}/{NUM_SCAN} {tk} [{mode_text}] RANDOM"); prog.progress((i+1)/NUM_SCAN)
        r=check(tk)
        if r and r["is_break"]:
            key=f"{r['tkr']}_{r['interval']}_{r['price']}"
            if key not in st.session_state.found_db:
                st.session_state.found_db.add(key)
                st.session_state.history.append({k:v for k,v in r.items() if k!='df'})
                st.session_state.pending_breaks[r['tkr']]={'low': r['low'], 'price': r['price'], 'time': str(now_il())}
                new_b+=1
                m=f"FULL BREAK {r['tkr']} ${r['price']} -> {r['tp']} (+{r['pct']}%) RSI {r['rsi']} RANDOM"
                st.success(m); tg(m)
                with st.expander(f"Chart {r['tkr']} RANDOM"): plot_chart(r["df"], r["tkr"])
    prog.empty(); stat.empty()
    st.session_state.last_scan_time=now_il_str("%H:%M:%S")
    st.session_state.scan_count+=1
    if new_b==0: st.warning("No new breaks")

if st.session_state.auto_scan:
    st.warning(f"AUTO OMER active - scanning {NUM_SCAN} every {AUTO_SEC} sec - Time IL {now_il_str('%H:%M:%S')}")
    nb, nbuy = run_one_scan()
    st.write(f"OMER scanned {NUM_SCAN} | breaks: {nb} | buys: {nbuy}")
    now=time.time()
    if now - st.session_state.last_heartbeat > HEARTBEAT_MIN*60:
        tg(f"OMER alive {now_il_str('%H:%M:%S')} pending {len(st.session_state.pending_breaks)}")
        st.session_state.last_heartbeat=now
    ph=st.empty()
    for sec in range(AUTO_SEC, 0, -1):
        ph.caption(f"Next OMER scan in {sec} sec - {now_il_str('%H:%M:%S')} IL"); time.sleep(1)
    ph.empty(); st.rerun()

if st.session_state.pending_breaks:
    st.subheader(f"OMER pending green - {len(st.session_state.pending_breaks)}")
    df_p=pd.DataFrame.from_dict(st.session_state.pending_breaks, orient='index')
    st.dataframe(df_p, use_container_width=True)
if st.session_state.history:
    st.subheader(f"History OMER {len(st.session_state.history)}")
    dfh=pd.DataFrame(st.session_state.history[::-1])
    st.dataframe(dfh.drop(columns=['df'], errors='ignore'), use_container_width=True)

st.divider()
st.header("MATRIX BREAKER FUTURES")
if st.session_state.futures_last_scan:
    hb_diff_f=int(time.time() - st.session_state.futures_heartbeat) if st.session_state.futures_heartbeat else 9999
    alive_f="LIVE" if hb_diff_f < (FUTURES_HB_MIN*60*2.5) else "SLEEP"
    st.info(f"MATRIX - Last: {st.session_state.futures_last_scan} | Scans: {st.session_state.futures_scan_count} | Status: {alive_f} | VIX: {get_vix_price():.2f}")

c3,c4=st.columns(2)
with c3: manual_f=st.text_input("Ticker MATRIX", placeholder="ES=F / NQ=F / RTY=F", key="manual_f")
with c4:
    st.write("")
    btn_f=st.button("Check + Chart MATRIX", use_container_width=True, type="secondary")
if btn_f and manual_f:
    rf=check_futures(manual_f.upper())
    if rf and rf["df"] is not None:
        st.write(f"{rf['tkr']} ${rf['price']} {rf['side']} RSI {rf['rsi']} VIX {rf['vix']} SL {rf['sl']} TP {rf['tp']}")
        plot_chart(rf["df"], rf["tkr"])
    else: st.error("No data futures")

def run_futures_scan():
    new_l=0; new_s=0; vix_now=get_vix_price()
    for tk in FUTURES_TICKERS:
        rf=check_futures(tk)
        if not rf: continue
        key_base=f"{rf['tkr']}_{rf['interval']}_{rf['side']}_{rf['price']}_{now_il_str('%Y%m%d%H')}"
        if rf["is_long"]:
            if key_base not in st.session_state.futures_found:
                st.session_state.futures_found.add(key_base); st.session_state.futures_history.append(rf); new_l+=1
                msg=f"MATRIX LONG {rf['tkr']} Entry {rf['entry']} SL {rf['sl']} TP {rf['tp']} RSI {rf['rsi']} VIX {rf['vix']}"
                tg(msg)
        if rf["is_short"]:
            if key_base not in st.session_state.futures_found:
                st.session_state.futures_found.add(key_base); st.session_state.futures_history.append(rf); new_s+=1
                msg=f"MATRIX SHORT {rf['tkr']} Entry {rf['entry']} SL {rf['sl']} TP {rf['tp']} RSI {rf['rsi']} VIX {rf['vix']}"
                tg(msg)
    st.session_state.futures_last_scan=now_il_str("%H:%M:%S %d/%m")
    st.session_state.futures_scan_count+=1
    return new_l, new_s, vix_now

if st.button(f"Scan now MATRIX - {', '.join(FUTURES_TICKERS)}", use_container_width=True):
    prog_f=st.progress(0); stat_f=st.empty(); new_l_tot=0; new_s_tot=0
    for i, tk in enumerate(FUTURES_TICKERS):
        stat_f.text(f"{i+1}/{len(FUTURES_TICKERS)} {tk} MATRIX {FUTURES_INTERVAL}"); prog_f.progress((i+1)/len(FUTURES_TICKERS))
        rf=check_futures(tk)
        if rf:
            with st.expander(f"{rf['tkr']} ${rf['price']} {rf['side']} RSI {rf['rsi']} VIX {rf['vix']} - chart"): plot_chart(rf["df"], rf["tkr"])
            if rf["is_long"]:
                key_base=f"{rf['tkr']}_{rf['interval']}_{rf['side']}_{rf['price']}_{now_il_str('%Y%m%d%H')}"
                if key_base not in st.session_state.futures_found:
                    st.session_state.futures_found.add(key_base); st.session_state.futures_history.append(rf); new_l_tot+=1
                    m=f"MATRIX LONG {rf['tkr']} ${rf['price']} SL {rf['sl']} TP {rf['tp']} RSI {rf['rsi']} VIX {rf['vix']}"
                    st.success(m); tg(m)
            if rf["is_short"]:
                key_base=f"{rf['tkr']}_{rf['interval']}_{rf['side']}_{rf['price']}_{now_il_str('%Y%m%d%H')}"
                if key_base not in st.session_state.futures_found:
                    st.session_state.futures_found.add(key_base); st.session_state.futures_history.append(rf); new_s_tot+=1
                    m=f"MATRIX SHORT {rf['tkr']} ${rf['price']} SL {rf['sl']} TP {rf['tp']} RSI {rf['rsi']} VIX {rf['vix']}"
                    st.error(m); tg(m)
    prog_f.empty(); stat_f.empty()
    st.session_state.futures_last_scan=now_il_str("%H:%M:%S")
    st.session_state.futures_scan_count+=1
    if new_l_tot==0 and new_s_tot==0: st.warning(f"No MATRIX breaks VIX {get_vix_price():.2f}")

if st.session_state.futures_auto:
    st.warning(f"AUTO MATRIX active - scanning {', '.join(FUTURES_TICKERS)} every {FUTURES_AUTO_SEC} sec - IL {now_il_str('%H:%M:%S')}")
    nl, ns, vix_now = run_futures_scan()
    st.write(f"MATRIX VIX: {vix_now:.2f} long new: {nl} short new: {ns} history: {len(st.session_state.futures_history)}")
    now_f=time.time()
    if now_f - st.session_state.futures_heartbeat > FUTURES_HB_MIN*60:
        tg(f"MATRIX alive {now_il_str('%H:%M:%S')} VIX {vix_now:.2f} history {len(st.session_state.futures_history)}")
        st.session_state.futures_heartbeat=now_f
    ph_f=st.empty()
    for sec in range(FUTURES_AUTO_SEC, 0, -1):
        ph_f.caption(f"Next MATRIX scan in {sec} sec - {now_il_str('%H:%M:%S')} IL VIX {get_vix_price():.2f}"); time.sleep(1)
    ph_f.empty(); st.rerun()

if st.session_state.futures_history:
    st.subheader(f"History MATRIX {len(st.session_state.futures_history)}")
    dfh_f=pd.DataFrame([{k:v for k,v in x.items() if k!='df'} for x in st.session_state.futures_history[::-1]])
    st.dataframe(dfh_f, use_container_width=True)
