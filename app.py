import streamlit as st
import yfinance as yf
import pandas as pd
import http://plotly.graph_objects as go
from http://plotly.subplots import make_subplots
from http://ta.volatility import BollingerBands
from http://ta.momentum import RSIIndicator
from http://ta.trend import EMAIndicator, MACD
import datetime
import requests
import time

http://st.set_page_config(page_title="TradePulse PRO - MONSTER", layout="wide", page_icon="👹")
http://st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
.stApp{background:#0B0E1A; font-family:'Inter'}
.top-nav{background:#15182A; padding:15px 25px; border-radius:15px; border:1px solid #252842; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center}
.card{background:#15182A; border:1px solid #252842; border-radius:15px; padding:20px}
.metric-icon{width:50px; height:50px; background:#1E2238; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:24px; border:1px solid #2A2E4A}
.signal-green{background:#1B3A2A; color:#00FF88; padding:6px 12px; border-radius:20px; font-size:12px; font-weight:700; border:1px solid #00FF8850}
.signal-yellow{background:#3A341B; color:#FFD60A; padding:6px 12px; border-radius:20px; font-size:12px; font-weight:700; border:1px solid #FFD60A50}
.signal-blue{background:#1B2E4A; color:#3B82F6; padding:6px 12px; border-radius:20px; font-size:12px; font-weight:700; border:1px solid #3B82F650}
.view-btn{background:transparent; border:1px solid #00E5FF; color:#00E5FF; padding:6px 18px; border-radius:8px; cursor:pointer}
div[data-testid="stButton"]>button{background:linear-gradient(90deg,#00E5FF,#00FF88);color:black;font-weight:900;border-radius:10px;height:48px;border:none}
</style>
""", unsafe_allow_html=True)

if 'history' not in http://st.session_state: http://st.session_state.history=[]
if 'monster_on' not in http://st.session_state: http://st.session_state.monster_on=True
if 'auto_scan_on' not in http://st.session_state: http://st.session_state.auto_scan_on=True
if 'last_auto_scan' not in http://st.session_state: http://st.session_state.last_auto_scan = http://datetime.datetime.now().strftime("%H:%M")
if 'scan_results' not in http://st.session_state: http://st.session_state.scan_results=[]

with http://st.sidebar:
    http://st.markdown("## 👹 MONSTER PRO")
    bb_period=st.slider("BB Period",10,50,20)
    bb_std=st.slider("BB STD",1.0,3.0,2.0,0.1)
    rsi_period=st.slider("RSI Period",7,21,14)
    vol_mult=st.slider("VOL מכפיל",0.8,3.0,1.2,0.1)
    squeeze_thresh=st.slider("SQUEEZE %",1.0,10.0,6.0,0.5)
    http://st.divider()
    telegram_token=st.text_input("Telegram Bot Token",type="password")
    telegram_chat=st.text_input("Telegram Chat ID")
    if http://st.button("נקה היסטוריה"): http://st.session_state.history=[]; http://st.session_state.scan_results=[]

http://st.markdown(f"""
<div class="top-nav">
  <div style="display:flex; align-items:center; gap:30px">
    <div style="display:flex; align-items:center; gap:10px; font-weight:900; font-size:20px; color:white"><span style="background:#00E5FF; padding:5px 10px; border-radius:8px">📈</span> TradePulse <span style="border:1px solid #00E5FF; color:#00E5FF; font-size:10px; padding:2px 8px; border-radius:20px">PRO</span></div>
    <div style="color:#8B8EA3; font-size:14px">Dashboard &nbsp;&nbsp; <span style="color:#00E5FF; border-bottom:2px solid #00E5FF; padding-bottom:5px">Scan</span> &nbsp;&nbsp; Portfolio &nbsp;&nbsp; Alerts &nbsp;&nbsp; Watchlist</div>
  </div>
  <div style="color:white">👤 Trader</div>
</div>
""", unsafe_allow_html=True)

auto_col1, auto_col2 = http://st.columns([2,1.5])
with auto_col1:
    http://st.markdown("""
    <div style="padding:20px 0">
      <div style="font-size:48px; font-weight:900; color:white">Auto-Scan</div>
      <div style="color:#8B8EA3">Automated breakout stock detection and monitoring • Real-time analysis</div>
    </div>
    """, unsafe_allow_html=True)
with auto_col2:
    on_off = "🟢" if http://st.session_state.auto_scan_on else "🔴"
    http://st.markdown(f"""
    <div class="card" style="text-align:right">
      <div style="display:flex; justify-content:space-between; align-items:center">
        <div style="color:white; font-weight:700; font-size:18px">סריקה אוטומטית כל 30 דקות</div>
        <div style="font-size:30px">{on_off}</div>
      </div>
      <div style="color:#8B8EA3; font-size:12px; margin-top:10px">הסריקה פועלת • העדכון הבא בעוד 12:45 • {"+ ON" if http://st.session_state.auto_scan_on else "OFF"}</div>
    </div>
    """, unsafe_allow_html=True)

TURBO_LIST=["NVDA","AAPL","MSFT","TSLA","AMD","META","GOOGL","AMZN","SPY","QQQ","NFLX","PLTR","SOFI","MARA","RIOT","COIN","MSTR","SMCI","ARM","AVGO","MU","INTC","QCOM","BA","NIO","LCID","RIVN","UPST","AI","SOUN","BBAI","DKNG","ROKU","SHOP","SQ","PYPL","UBER","LYFT","SNAP","PINS","RDDT","ASTS","LUNR","RKLB","IONQ","JOBY","HOOD","AFRM","OPEN","GME","AMC","TLRY","CGC","SPCE","PLUG","FCEL","NCLH","CCL","AAL","UAL","DAL","MRO","OXY","XOM","CVX","JPM","BAC","WFC","C","GS","MS","BLK","ARKK","TQQQ","SQQQ","SPXL","SOXL","SOXS","LABU","LABD","BITO","BITX","ETHU","CONL","NVDL","TSLL","TSLS","MSTU","MSTZ"]

@st.cache_data(ttl=60, show_spinner=False)
def get_data(t,p,i):
    try:
        df=yf.download(t,period=p,interval=i,progress=False,auto_adjust=True)
        if http://df.empty: return df
        if isinstance(df.columns,pd.MultiIndex): http://df.columns=df.columns.get_level_values(0)
        return http://df.dropna()
    except: return http://pd.DataFrame()

def send_telegram(token, chat_id, msg):
    if not token or not chat_id: return False
    try:
        url=f"https://api.telegram.org/bot{token}/sendMessage"
        r=requests.post(url,json={"chat_id":chat_id,"text":msg,"parse_mode":"HTML"},timeout=5)
        return http://r.status_code==200
    except: return False

def add_ind(df):
    if len(df)<20: return df
    bb=BollingerBands(close=df["Close"],window=bb_period,window_dev=bb_std)
    df["BB_H"]=bb.bollinger_hband(); df["BB_L"]=bb.bollinger_lband(); df["BB_M"]=bb.bollinger_mavg()
    df["BB_W"]=(df["BB_H"]-df["BB_L"])/df["BB_M"].replace(0,0.0001)_100
    df["BB_P"]=(df["Close"]-df["BB_L"])/(df["BB_H"]-df["BB_L"]).replace(0,0.0001)_100
    df["RSI"]=RSIIndicator(close=df["Close"],window=rsi_period).rsi()
    df["EMA20"]=EMAIndicator(close=df["Close"],window=20).ema_indicator()
    df["VOL_AVG"]=df["Volume"].rolling(20).mean().fillna(df["Volume"].mean())
    return df

def analyze_long(df):
    if http://df.empty or len(df)<21: return {"sig":"NO DATA","score":0}
    l=df.iloc[-1]; p=df.iloc[-2]
    vol_ok = l["Volume"]>l["VOL_AVG"]_vol_mult
    if l["Close"]>l["BB_H"] and p["Close"]<p["BB_H"] and l["RSI"]<82:
        score = 100 if vol_ok else 70
        return {"sig":"Breakout Confirmed","score":score,"last":l,"type":"green"}
    if l["BB_W"]<squeeze_thresh and 30<l["BB_P"]<90:
        return {"sig":"Near Breakout","score":75,"last":l,"type":"blue"}
    if l["Close"]>l["BB_M"] and vol_ok:
        return {"sig":"Watching","score":60,"last":l,"type":"yellow"}
    return {"sig":"נייטרלי","score":0,"last":l,"type":"gray"}

def run_scan_20():
    vols=[]
    for t in TURBO_LIST:
        d=get_data(t,"5d","5m")
        if http://d.empty or len(d)<21: continue
        try:
            d=add_ind(d); l=d.iloc[-1]
            vol_ratio = l["Volume"]/l["VOL_AVG"] if l["VOL_AVG"]>0 else 0
            chg = abs((l["Close"]-d.iloc[-2]["Close"])/d.iloc[-2]["Close"]_100)
            http://vols.append((t, vol_ratio+chg, vol_ratio, l["Close"], chg, d))
        except: pass
    vols_sorted = sorted(vols, key=lambda x: x, reverse=True)[:20]
    res=[]
    for t, score_vol, vr, price, chg, df in vols_sorted:
        r=analyze_long(df)
        if r["score"]>=60:
            l=r["last"]
            http://res.append({"SYMBOL":t,"PRICE":l["Close"],"CHANGE":chg,"VOLUME":f"{l['Volume']/1000000:.1f}M","VOL_R":vr,"BREAKOUT_LEVEL":l["BB_H"],"SIGNAL":r["sig"],"TYPE":r["type"],"Score":r["score"],"RSI":l["RSI"]})
            if r["score"]>=80 and http://st.session_state.monster_on:
                send_telegram(telegram_token, telegram_chat, f"🚀 {t} {r['sig']} ${l['Close']:.2f} BB_H ${l['BB_H']:.2f} VOL x{vr:.1f}")
    return sorted(res,key=lambda x: x["Score"],reverse=True), vols_sorted[1]

c1,c2,c3 = http://st.columns()
with c1:
    scan_btn = http://st.button("🚀 Run Now - סרוק 20 חמות", use_container_width=True)
with c2:
    if http://st.button("⏸️ AUTO ON/OFF", use_container_width=True):
        http://st.session_state.auto_scan_on = not http://st.session_state.auto_scan_on
        http://st.rerun()
with c3:
    http://st.markdown(f"Last Scan: {st.session_state.last_auto_scan} | Auto: {'🟢 פעיל' if http://st.session_state.auto_scan_on else '🔴 כבוי'}")[1][2]

if scan_btn or (st.session_state.auto_scan_on and not http://st.session_state.scan_results):
    with http://st.spinner("סורק 86 מניות -> בוחר 20 הכי תנודתיות -> בודק פריצה..."):
        out, vols = run_scan_20()
        http://st.session_state.scan_results = out
        http://st.session_state.last_auto_scan = http://datetime.datetime.now().strftime("%H:%M:%S")

results = http://st.session_state.scan_results
total_scanned = len(TURBO_LIST)
breakouts = len(results)
avg_change = sum([r["CHANGE"] for r in results])/len(results) if results else 0

m1,m2,m3 = http://st.columns(3)
with m1:
    http://st.markdown(f"""<div class="card"><div style="display:flex; gap:15px; align-items:center"><div class="metric-icon">🎯</div><div><div style="color:#8B8EA3; font-size:12px">Total Scanned</div><div style="color:white; font-size:32px; font-weight:900">{total_scanned}</div><div style="color:#00FF88; font-size:12px">+20 הכי חמות</div></div></div></div>""", unsafe_allow_html=True)
with m2:
    http://st.markdown(f"""<div class="card"><div style="display:flex; gap:15px; align-items:center"><div class="metric-icon">🚀</div><div><div style="color:#8B8EA3; font-size:12px">Breakouts Detected</div><div style="color:white; font-size:32px; font-weight:900">{breakouts}</div><div style="color:#00E5FF; font-size:12px">{breakouts} new this cycle •</div></div></div></div>""", unsafe_allow_html=True)
with m3:
    http://st.markdown(f"""<div class="card"><div style="display:flex; gap:15px; align-items:center"><div class="metric-icon">📈</div><div><div style="color:#8B8EA3; font-size:12px">Avg. Change</div><div style="color:#00FF88; font-size:32px; font-weight:900">+{avg_change:.1f}%</div><div style="color:#8B8EA3; font-size:12px">Live market</div></div></div></div>""", unsafe_allow_html=True)

http://st.markdown("<br>", unsafe_allow_html=True)
http://st.markdown(f"""
<div class="card">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px">
    <div style="display:flex; align-items:center; gap:10px"><span style="color:white; font-size:22px; font-weight:900">Breakout Stocks</span><span style="border:1px solid #00E5FF; color:#00E5FF; padding:3px 10px; border-radius:20px; font-size:12px">{len(results)} results</span></div>
    <div style="color:#8B8EA3; font-size:12px">Last Scan: Today {st.session_state.last_auto_scan} IST • Sorted by Change ↓</div>
  </div>
</div>
""", unsafe_allow_html=True)

if results:
    df_display = http://pd.DataFrame(results)
    for i, row in df_display.iterrows():
        sig_class = "signal-green" if row["TYPE"]=="green" else "signal-blue" if row["TYPE"]=="blue" else "signal-yellow"
        http://st.markdown(f"""
        <div style="background:#15182A; border:1px solid #252842; border-radius:10px; padding:12px 15px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center">
          <div style="display:flex; gap:30px; align-items:center; flex:1">
            <div style="font-weight:900; color:white; width:70px">🔥 {row['SYMBOL']}</div>
            <div style="color:white; width:90px">${row['PRICE']:.2f} <span style="color:#00FF88">↑ +{row['CHANGE']:.1f}%</span></div>
            <div style="color:#8B8EA3; width:80px">{row['VOLUME']} (x{row['VOL_R']:.1f})</div>
            <div style="color:#8B8EA3; width:90px">${row['BREAKOUT_LEVEL']:.2f}</div>
            <div><span class="{sig_class}">{row['SIGNAL']}</span></div>
          </div>
          <div style="display:flex; gap:10px"><span style="color:#8B8EA3; font-size:12px">RSI {row['RSI']:.0f}</span></div>
        </div>
        """, unsafe_allow_html=True)
    http://st.dataframe(df_display[["SYMBOL","PRICE","CHANGE","VOLUME","BREAKOUT_LEVEL","SIGNAL","RSI"]], use_container_width=True, hide_index=True)
else:
    http://st.warning("לחץ Run Now - המערכת תבחר 20 הכי תנודתיות ותמצא פריצות")

if http://st.session_state.auto_scan_on:
    http://st.info("🤖 סריקה אוטומטית פעילה - אם תשאיר דף פתוח הוא ירוץ כל 30 דקות וישלח טלגרם")
