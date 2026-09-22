import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import datetime
import requests

st.set_page_config(page_title="MONSTER FULL DASHBOARD", layout="wide")

if 'monster_on' not in st.session_state:
    st.session_state.monster_on=True
if 'scan_results' not in st.session_state:
    st.session_state.scan_results=[]
if 'last_scan' not in st.session_state:
    st.session_state.last_scan="--:--"

TURBO_LIST=["NVDA","AAPL","MSFT","TSLA","AMD","META","GOOGL","AMZN","SPY","QQQ","NFLX","PLTR","SOFI","MARA","RIOT","COIN","MSTR","SMCI","ARM","AVGO","MU","INTC","QCOM","BA","NIO","LCID","RIVN","UPST","AI","SOUN","BBAI","DKNG","ROKU","SHOP","SQ","PYPL","UBER","LYFT","SNAP","PINS","RDDT","ASTS","LUNR","RKLB","IONQ","JOBY","HOOD","AFRM","OPEN","GME","AMC","TLRY","CGC","SPCE","PLUG","FCEL","NCLH","CCL","AAL","UAL","DAL","MRO","OXY","XOM","CVX","JPM","BAC","WFC","C","GS","MS","BLK","ARKK","TQQQ","SQQQ","SPXL","SOXL","SOXS","LABU","LABD","BITO","BITX","ETHU","CONL","NVDL","TSLL","TSLS","MSTU","MSTZ"]

@st.cache_data(ttl=60, show_spinner=False)
def get_data(t,p,i):
    try:
        df=yf.download(t,period=p,interval=i,progress=False,auto_adjust=True)
        if df.empty: return df
        if isinstance(df.columns,pd.MultiIndex):
            df.columns=df.columns.get_level_values(0)
        return df.dropna()
    except:
        return pd.DataFrame()

def add_ind(df):
    if len(df)<20: return df
    bb=BollingerBands(close=df["Close"],window=20,window_dev=2.0)
    df["BB_H"]=bb.bollinger_hband()
    df["BB_L"]=bb.bollinger_lband()
    df["BB_M"]=bb.bollinger_mavg()
    df["BB_W"]=(df["BB_H"]-df["BB_L"])/df["BB_M"].replace(0,0.0001)*100
    df["BB_P"]=(df["Close"]-df["BB_L"])/(df["BB_H"]-df["BB_L"]).replace(0,0.0001)*100
    df["RSI"]=RSIIndicator(close=df["Close"],window=14).rsi()
    df["EMA20"]=EMAIndicator(close=df["Close"],window=20).ema_indicator()
    df["VOL_AVG"]=df["Volume"].rolling(20).mean().fillna(df["Volume"].mean())
    return df

def analyze_long(df):
    if df.empty or len(df)<21:
        return {"sig":"NO DATA","score":0}
    l=df.iloc[-1]
    p=df.iloc[-2]
    vol_ok=l["Volume"]>l["VOL_AVG"]*1.2
    if l["Close"]>l["BB_H"] and p["Close"]<p["BB_H"] and l["RSI"]<82:
        return {"sig":"Breakout Confirmed","score":100,"last":l}
    if l["BB_W"]<6.0 and 30<l["BB_P"]<90:
        return {"sig":"Near Breakout","score":75,"last":l}
    if l["Close"]>l["BB_M"] and vol_ok:
        return {"sig":"Watching","score":60,"last":l}
    return {"sig":"neutral","score":0,"last":l}

def run_scan_20():
    vols=[]
    for t in TURBO_LIST:
        d=get_data(t,"5d","5m")
        if d.empty or len(d)<21: continue
        try:
            d=add_ind(d)
            l=d.iloc[-1]
            vr=l["Volume"]/l["VOL_AVG"] if l["VOL_AVG"]>0 else 0
            chg=abs((l["Close"]-d.iloc[-2]["Close"])/d.iloc[-2]["Close"]*100)
            vols.append((t, vr+chg, vr, chg, d))
        except:
            pass
    vols_sorted=sorted(vols, key=lambda x: x[1], reverse=True)[:20]
    res=[]
    for t, sv, vr, chg, df in vols_sorted:
        r=analyze_long(df)
        if r["score"]>=60:
            l=r["last"]
            res.append({"SYMBOL":t,"PRICE":float(l["Close"]),"CHANGE":float(chg),"VOLUME":f"{l['Volume']/1000000:.1f}M","VOL_X":f"{vr:.1f}x","BREAKOUT_LEVEL":float(l["BB_H"]),"SIGNAL":r["sig"],"RSI":float(l["RSI"]),"Score":r["score"]})
    return sorted(res, key=lambda x: x["Score"], reverse=True)

st.markdown('<div style="background:#15182A; padding:15px; border-radius:15px; color:white">TradePulse PRO - FULL + DASHBOARD</div>', unsafe_allow_html=True)

c1,c2=st.columns([2,1])
with c1:
    ticker=st.text_input("ticker",value="NVDA").upper().strip()
with c2:
    if st.button("ON" if st.session_state.monster_on else "OFF",use_container_width=True):
        st.session_state.monster_on=not st.session_state.monster_on

if ticker:
    df=get_data(ticker,"5d","5m")
    if not df.empty:
        df=add_ind(df)
        r=analyze_long(df)
        last=r.get("last")
        if last is not None:
            st.metric("price",f"${last['Close']:.2f}")
            fig=make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[0.8,0.2])
            fig.add_trace(go.Candlestick(x=df.index,open=df["Open"],high=df["High"],low=df["Low"],close=df["Close"]),row=1,col=1)
            fig.add_trace(go.Scatter(x=df.index,y=df["BB_H"]),row=1,col=1)
            fig.add_trace(go.Scatter(x=df.index,y=df["BB_L"]),row=1,col=1)
            fig.add_trace(go.Bar(x=df.index,y=df["Volume"]),row=2,col=1)
            fig.update_layout(template="plotly_dark",height=500,xaxis_rangeslider_visible=False)
            st.plotly_chart(fig,use_container_width=True)

if st.button("Run Now - 20 hot"):
    out=run_scan_20()
    st.session_state.scan_results=out
    st.session_state.last_scan=datetime.datetime.now().strftime("%H:%M:%S")

results=st.session_state.scan_results
m1,m2,m3=st.columns(3)
with m1: st.metric("Total Scanned", len(TURBO_LIST))
with m2: st.metric("Breakouts", len(results))
with m3:
    avg=sum([r["CHANGE"] for r in results])/len(results) if results else 0
    st.metric("Avg Change", f"{avg:.1f}%")

if results:
    st.dataframe(pd.DataFrame(results), use_container_width=True)
else:
    st.info("press Run Now")
