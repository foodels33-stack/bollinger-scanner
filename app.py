import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
import datetime
import requests

st.set_page_config(page_title="MONSTER LONG TELEGRAM", layout="wide", page_icon="👹")
st.markdown("""
<style>
.stApp{background:#0E1117}
div[data-testid="stButton"]>button{background:linear-gradient(90deg,#00FF88,#00CC66);color:black;font-weight:900;border-radius:10px;height:48px;border:none}
div[data-testid="stMetric"]{background:#1A1D27;padding:10px;border-radius:10px;border:1px solid #2A2D3A}
</style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state: st.session_state.history=[]
if 'monster_on' not in st.session_state: st.session_state.monster_on=True

with st.sidebar:
    st.markdown("## 👹 MONSTER LONG + TELEGRAM")
    bb_period=st.slider("BB Period",10,50,20)
    bb_std=st.slider("BB STD",1.0,3.0,2.0,0.1)
    rsi_period=st.slider("RSI Period",7,21,14)
    vol_mult=st.slider("VOL מכפיל",1.0,3.0,1.5,0.1)
    squeeze_thresh=st.slider("SQUEEZE %",1.0,10.0,5.0,0.5)
    st.divider()
    telegram_token=st.text_input("Telegram Bot Token",type="password",placeholder="123456:ABC...")
    telegram_chat=st.text_input("Telegram Chat ID",placeholder="123456789")
    auto_refresh=st.checkbox("רענון 30 שניות",False)
    if st.button("נקה היסטוריה"): st.session_state.history=[]

c1,c2,c3=st.columns([2,1,2])
with c1: ticker=st.text_input("טיקר",value="NVDA",label_visibility="collapsed").upper().strip()
with c2: tf=st.selectbox("טווח",["1 דק","5 דק","15 דק","יומי","שבועי"],index=1,label_visibility="collapsed")
with c3:
    lbl="🔴 OFF" if not st.session_state.monster_on else "🟢 ON - LONG + TELEGRAM"
    if st.button(lbl,use_container_width=True): st.session_state.monster_on=not st.session_state.monster_on

col1,col2=st.columns(2)
with col1: scan_btn=st.button("🚀 SCAN 100 LONG פריצה מלאה",use_container_width=True)
with col2: top5_btn=st.button("👑 TOP 5 SQUEEZE LONG",use_container_width=True)

tf_map={"1 דק":("1m","1d"),"5 דק":("5m","5d"),"15 דק":("15m","5d"),"יומי":("1d","6mo"),"שבועי":("1wk","2y")}
interval,period=tf_map[tf]

TURBO_LIST=["NVDA","AAPL","MSFT","TSLA","AMD","META","GOOGL","AMZN","SPY","QQQ","NFLX","PLTR","SOFI","MARA","RIOT","COIN","MSTR","SMCI","ARM","AVGO","MU","INTC","QCOM","BA","NIO","LCID","RIVN","UPST","AI","SOUN","BBAI","DKNG","ROKU","SHOP","SQ","PYPL","UBER","LYFT","SNAP","PINS","RDDT","ASTS","LUNR","RKLB","IONQ","JOBY","HOOD","AFRM","OPEN","GME","AMC","TLRY","CGC","SPCE","PLUG","FCEL","NCLH","CCL","AAL","UAL","DAL","MRO","OXY","XOM","CVX","JPM","BAC","WFC","C","GS","MS","BLK","ARKK","TQQQ","SQQQ","SPXL","SOXL","SOXS","LABU","LABD","BITO","BITX","ETHU","CONL","NVDL","TSLL","TSLS","MSTU","MSTZ"]

@st.cache_data(ttl=30, show_spinner=False)
def get_data(t,p,i):
    try:
        df=yf.download(t,period=p,interval=i,progress=False,auto_adjust=True)
        if df.empty: return df
        if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        return df.dropna()
    except: return pd.DataFrame()

def send_telegram(token, chat_id, msg):
    if not token or not chat_id: return False
    try:
        url=f"https://api.telegram.org/bot{token}/sendMessage"
        r=requests.post(url,json={"chat_id":chat_id,"text":msg,"parse_mode":"HTML"},timeout=5)
        return r.status_code==200
    except: return False

def add_ind(df):
    if len(df)<bb_period: return df
    bb=BollingerBands(close=df["Close"],window=bb_period,window_dev=bb_std)
    df["BB_H"]=bb.bollinger_hband(); df["BB_L"]=bb.bollinger_lband(); df["BB_M"]=bb.bollinger_mavg()
    df["BB_W"]=(df["BB_H"]-df["BB_L"])/df["BB_M"].replace(0,0.0001)*100
    df["BB_P"]=(df["Close"]-df["BB_L"])/(df["BB_H"]-df["BB_L"]).replace(0,0.0001)*100
    df["RSI"]=RSIIndicator(close=df["Close"],window=rsi_period).rsi()
    df["EMA20"]=EMAIndicator(close=df["Close"],window=20).ema_indicator()
    df["EMA50"]=EMAIndicator(close=df["Close"],window=50).ema_indicator()
    df["VOL_AVG"]=df["Volume"].rolling(20).mean().fillna(df["Volume"].mean())
    macd=MACD(close=df["Close"]); df["MACD"]=macd.macd(); df["MACD_SIG"]=macd.macd_signal()
    return df

def analyze_long(df):
    if df.empty or len(df)<21: return {"sig":"NO DATA","score":0,"color":"gray"}
    l=df.iloc[-1]; p=df.iloc[-2]
    body_full = l["Close"]>l["BB_H"] and l["Open"]>l["BB_H"]
    wick = l["High"]>l["BB_H"]
    body_cross = l["Close"]>l["BB_H"] and l["Open"]<=l["BB_H"]
    prev_inside = p["Close"]<p["BB_H"]
    vol_ok = l["Volume"]>l["VOL_AVG"]*vol_mult
    if body_full and wick and prev_inside and vol_ok and l["RSI"]<78:
        return {"sig":f"🚀 פריצה מלאה LONG - גוף {l['Open']:.2f}->{l['Close']:.2f} + זנב {l['High']:.2f} מעל BB {l['BB_H']:.2f}","score":100,"color":"#00FF88","last":l}
    if body_cross and wick and prev_inside and vol_ok and l["RSI"]<75:
        return {"sig":f"🟢 פריצת גוף LONG - סגירה {l['Close']:.2f} מעל {l['BB_H']:.2f}","score":85,"color":"#00FF88","last":l}
    if l["BB_W"]<squeeze_thresh and 45<l["BB_P"]<85 and vol_ok:
        return {"sig":f"💥 SQUEEZE לפני LONG - רוחב {l['BB_W']:.2f}%","score":80,"color":"gold","last":l}
    return {"sig":"נייטרלי LONG","score":0,"color":"#262730","last":l}

if ticker:
    df=get_data(ticker,period,interval)
    if not df.empty:
        df=add_ind(df)
        r=analyze_long(df); last=r["last"]
        if r["score"]>=80 and st.session_state.monster_on:
            st.toast(f"{ticker}: {r['sig']}",icon="🚀")
            tg_msg=f"🚀 <b>{ticker} LONG BREAKOUT</b>\n{ r['sig'] }\nמחיר: ${last['Close']:.2f}\nBB_H: ${last['BB_H']:.2f}\nגוף: {last['Open']:.2f}→{last['Close']:.2f}\nHigh זנב: {last['High']:.2f}\nRSI: {last['RSI']:.1f} VOL x{last['Volume']/last['VOL_AVG']:.2f}"
            sent=send_telegram(telegram_token, telegram_chat, tg_msg)
            if sent: st.success("נשלח לטלגרם ✅")
            st.session_state.history.insert(0,{"זמן":datetime.datetime.now().strftime("%H:%M:%S"),"טיקר":ticker,"סיגנל":r["sig"],"מחיר":f"${last['Close']:.2f}","BB_H":f"${last['BB_H']:.2f}"})
        m1,m2,m3,m4,m5=st.columns(5)
        m1.metric("מחיר",f"${last['Close']:.2f}"); m2.metric("BB עליון",f"${last['BB_H']:.2f}"); m3.metric("BB רוחב",f"{last['BB_W']:.2f}%"); m4.metric("RSI",f"{last['RSI']:.1f}"); m5.metric("VOL x",f"{last['Volume']/last['VOL_AVG']:.2f}x")
        st.markdown(f"<div style='background:{r['color']};padding:14px;border-radius:10px;text-align:center;font-weight:900;font-size:18px;color:black'>{ticker} | {r['sig']} | Score {r['score']}</div>",unsafe_allow_html=True)
        fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=0.02,row_heights=[0.75,0.25])
        fig.add_trace(go.Candlestick(x=df.index,open=df["Open"],high=df["High"],low=df["Low"],close=df["Close"],name="נרות"),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["BB_H"],line=dict(color='#00FF88',width=2,dash='dash'),name="BB_H פריצה"),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["BB_M"],line=dict(color='yellow'),name="BB_M"),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["BB_L"],line=dict(color='cyan',dash='dash'),name="BB_L"),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["EMA20"],line=dict(color='orange'),name="EMA20"),row=1,col=1)
        fig.add_trace(go.Bar(x=df.index,y=df["Volume"],name="VOL",marker_color='rgba(0,255,136,0.3)'),row=2,col=1)
        fig.update_layout(template="plotly_dark",height=700,xaxis_rangeslider_visible=False,margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig,use_container_width=True)
        if st.session_state.history:
            st.dataframe(pd.DataFrame(st.session_state.history),use_container_width=True,hide_index=True)
    else: st.error("אין נתונים")

def run_scan():
    res=[]; prog=st.progress(0); stat=st.empty()
    for i,t in enumerate(TURBO_LIST):
        stat.text(f"סורק {t} {i+1}/{len(TURBO_LIST)}"); prog.progress((i+1)/len(TURBO_LIST))
        d=get_data(t,"5d","5m")
        if d.empty or len(d)<21: continue
        d=add_ind(d); r=analyze_long(d)
        if r["score"]>=70:
            l=r["last"]
            res.append({"טיקר":t,"מחיר":f"${l['Close']:.2f}","BB_H":f"${l['BB_H']:.2f}","גוף":f"{l['Open']:.2f}->{l['Close']:.2f}","זנב":f"{l['High']:.2f}","סיגנל":r["sig"],"Score":r["score"],"VOL x":f"{l['Volume']/l['VOL_AVG']:.2f}x"})
            if r["score"]>=90:
                send_telegram(telegram_token, telegram_chat, f"🚀 SCAN LONG {t}: {r['sig']} מחיר ${l['Close']:.2f}")
    prog.empty(); stat.empty()
    return sorted(res,key=lambda x: x["Score"],reverse=True)

if scan_btn:
    st.markdown("### 🔥 SCAN 100 LONG")
    out=run_scan()
    if out: st.dataframe(pd.DataFrame(out),use_container_width=True,hide_index=True)
    else: st.warning("אין פריצה LONG כרגע")

if top5_btn:
    st.markdown("### 👑 TOP 5 SQUEEZE LONG")
    out=run_scan()
    if out:
        st.dataframe(pd.DataFrame(out[:5]),use_container_width=True,hide_index=True)

if auto_refresh:
    import time; time.sleep(30); st.rerun()
