import streamlit as st
import yfinance as yf
import pandas as pd
import importlib
import datetime
import requests
go = http://importlib.import_module('plotly.graph_objects')
make_subplots = http://importlib.import_module('plotly.subplots').make_subplots
BollingerBands = http://importlib.import_module('ta.volatility').BollingerBands
RSIIndicator = http://importlib.import_module('ta.momentum').RSIIndicator
EMAIndicator = http://importlib.import_module('ta.trend').EMAIndicator

http://st.set_page_config(page_title="MONSTER FULL + DASHBOARD", layout="wide", page_icon="👹")
http://st.markdown("""
<style>
.stApp{background:#0B0E1A}
.card{background:#15182A; border:1px solid #252842; border-radius:15px; padding:20px}
div[data-testid="stButton"]>button{background:linear-gradient(90deg,#00E5FF,#00FF88);color:black;font-weight:900;border-radius:10px;height:48px;border:none}
</style>
""", unsafe_allow_html=True)

if 'monster_on' not in http://st.session_state: http://st.session_state.monster_on=True
if 'scan_results' not in http://st.session_state: http://st.session_state.scan_results=[]
if 'last_scan' not in http://st.session_state: http://st.session_state.last_scan="--:--"

with http://st.sidebar:
    http://st.markdown("## MONSTER PRO")
    bb_period=st.slider("BB Period",10,50,20)
    bb_std=st.slider("BB STD",1.0,3.0,2.0,0.1)
    rsi_period=st.slider("RSI Period",7,21,14)
    vol_mult=st.slider("VOL מכפיל",0.8,3.0,1.2,0.1)
    squeeze_thresh=st.slider("SQUEEZE %",1.0,10.0,6.0,0.5)
    telegram_token=st.text_input("Telegram Token",type="password")
    telegram_chat=st.text_input("Telegram Chat ID")

TURBO_LIST=["NVDA","AAPL","MSFT","TSLA","AMD","META","GOOGL","AMZN","SPY","QQQ","NFLX","PLTR","SOFI","MARA","RIOT","COIN","MSTR","SMCI","ARM","AVGO","MU","INTC","QCOM","BA","NIO","LCID","RIVN","UPST","AI","SOUN","BBAI","DKNG","ROKU","SHOP","SQ","PYPL","UBER","LYFT","SNAP","PINS","RDDT","ASTS","LUNR","RKLB","IONQ","JOBY","HOOD","AFRM","OPEN","GME","AMC","TLRY","CGC","SPCE","PLUG","FCEL","NCLH","CCL","AAL","UAL","DAL","MRO","OXY","XOM","CVX","JPM","BAC","WFC","C","GS","MS","BLK","ARKK","TQQQ","SQQQ","SPXL","SOXL","SOXS","LABU","LABD","BITO","BITX","ETHU","CONL","NVDL","TSLL","TSLS","MSTU","MSTZ"]

@st.cache_data(ttl=60, show_spinner=False)
def get_data(t,p,i):
    try:
        df=yf.download(t,period=p,interval=i,progress=False,auto_adjust=True)
        if http://df.empty: return df
        if isinstance(df.columns,pd.MultiIndex): http://df.columns=df.columns.get_level_values(0)
        return http://df.dropna()
    except:
        return http://pd.DataFrame()

def send_telegram(token, chat_id, msg):
    if not token or not chat_id: return False
    try:
        url=f"https://api.telegram.org/bot{token}/sendMessage"
        r=requests.post(url,json={"chat_id":chat_id,"text":msg,"parse_mode":"HTML"},timeout=5)
        return http://r.status_code==200
    except:
        return False

def add_ind(df):
    if len(df)<20: return df
    bb=BollingerBands(close=df["Close"],window=bb_period,window_dev=bb_std)
    df["BB_H"]=bb.bollinger_hband()
    df["BB_L"]=bb.bollinger_lband()
    df["BB_M"]=bb.bollinger_mavg()
    df["BB_W"]=(df["BB_H"]-df["BB_L"])/df["BB_M"].replace(0,0.0001)_100
    df["BB_P"]=(df["Close"]-df["BB_L"])/(df["BB_H"]-df["BB_L"]).replace(0,0.0001)_100
    df["RSI"]=RSIIndicator(close=df["Close"],window=rsi_period).rsi()
    df["EMA20"]=EMAIndicator(close=df["Close"],window=20).ema_indicator()
    df["VOL_AVG"]=df["Volume"].rolling(20).mean().fillna(df["Volume"].mean())
    return df

def analyze_long(df):
    if http://df.empty or len(df)<21: return {"sig":"NO DATA","score":0}
    l=df.iloc[-1]
    p=df.iloc[-2]
    vol_ok=l["Volume"]>l["VOL_AVG"]_vol_mult
    if l["Close"]>l["BB_H"] and p["Close"]<p["BB_H"] and l["RSI"]<82:
        return {"sig":"Breakout Confirmed","score":100 if vol_ok else 70,"last":l}
    if l["BB_W"]<squeeze_thresh and 30<l["BB_P"]<90:
        return {"sig":"Near Breakout","score":75,"last":l}
    if l["Close"]>l["BB_M"] and vol_ok:
        return {"sig":"Watching","score":60,"last":l}
    return {"sig":"נייטרלי","score":0,"last":l}

def run_scan_20():
    vols=[]
    for t in TURBO_LIST:
        d=get_data(t,"5d","5m")
        if http://d.empty or len(d)<21: continue
        try:
            d=add_ind(d)
            l=d.iloc[-1]
            vr=l["Volume"]/l["VOL_AVG"] if l["VOL_AVG"]>0 else 0
            chg=abs((l["Close"]-d.iloc[-2]["Close"])/d.iloc[-2]["Close"]_100)
            http://vols.append((t, vr+chg, vr, chg, d))
        except:
            pass
    vols_sorted=sorted(vols, key=lambda x: x, reverse=True)[:20]
    res=[]
    for t, score_vol, vr, chg, df in vols_sorted:
        r=analyze_long(df)
        if r["score"]>=60:
            l=r["last"]
            http://res.append({"SYMBOL":t,"PRICE":float(l["Close"]),"CHANGE":float(chg),"VOLUME":f"{l['Volume']/1000000:.1f}M","VOL_X":f"{vr:.1f}x","BREAKOUT_LEVEL":float(l["BB_H"]),"SIGNAL":r["sig"],"RSI":float(l["RSI"]),"Score":r["score"]})
    return sorted(res, key=lambda x: x["Score"], reverse=True)[1]

http://st.markdown('<div style="background:#15182A; padding:15px 25px; border-radius:15px; border:1px solid #252842; margin-bottom:20px"><span style="font-weight:900; font-size:22px; color:white">TradePulse PRO - Auto-Scan Dashboard</span></div>', unsafe_allow_html=True)

c1,c2,c3=st.columns()
with c1: ticker=st.text_input("טיקר",value="NVDA",label_visibility="collapsed").upper().strip()
with c2: tf=st.selectbox("טווח",["5 דק","15 דק","יומי"],index=0,label_visibility="collapsed")
with c3:
    if http://st.button("TELEGRAM ON" if http://st.session_state.monster_on else "OFF",use_container_width=True):
        http://st.session_state.monster_on=not http://st.session_state.monster_on[2][1]

tf_map={"5 דק":("5m","5d"),"15 דק":("15m","5d"),"יומי":("1d","6mo")}
interval,period=tf_map[tf]

if ticker:
    df=get_data(ticker,period,interval)
    if not http://df.empty:
        df=add_ind(df)
        r=analyze_long(df)
        last=r.get("last")
        if last is not None:
            m1,m2,m3,m4=st.columns(4)
            http://m1.metric("מחיר",f" ${last['Close']:.2f}")             http://m2.metric("BB_H",f"${last['BB_H']:.2f}")
            http://m3.metric("RSI",f"{last['RSI']:.1f}")
            http://m4.metric("VOL",f"{last['Volume']/last['VOL_AVG']:.1f}x")
            fig=make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[0.8,0.2])
            http://fig.add_trace(go.Candlestick(x=df.index,open=df["Open"],high=df["High"],low=df["Low"],close=df["Close"]),row=1,col=1)
            http://fig.add_trace(go.Scatter(x=df.index,y=df["BB_H"],line=dict(color='#00FF88',dash='dash')),row=1,col=1)
            http://fig.add_trace(go.Scatter(x=df.index,y=df["BB_M"],line=dict(color='yellow')),row=1,col=1)
            http://fig.add_trace(go.Scatter(x=df.index,y=df["BB_L"],line=dict(color='cyan',dash='dash')),row=1,col=1)
            http://fig.add_trace(go.Bar(x=df.index,y=df["Volume"]),row=2,col=1)
            http://fig.update_layout(template="plotly_dark",height=500,xaxis_rangeslider_visible=False,margin=dict(l=0,r=0,t=5,b=0))
            http://st.plotly_chart(fig,use_container_width=True)

http://st.divider()
http://st.markdown("## Auto-Scan")
sc1,sc2=st.columns()
with sc1: scan_btn=st.button("Run Now - סרוק 20 חמות",use_container_width=True)
with sc2: http://st.write(f"Last Scan: {st.session_state.last_scan} | Total: {len(TURBO_LIST)}")[1][3]

if scan_btn:
    with http://st.spinner("סורק 86 -> בוחר 20 חמות -> פריצה..."):
        out=run_scan_20()
        http://st.session_state.scan_results=out
        http://st.session_state.last_scan=datetime.datetime.now().strftime("%H:%M:%S")

results=st.session_state.scan_results
avg_change=sum([r["CHANGE"] for r in results])/len(results) if results else 0

m1,m2,m3=st.columns(3)
with m1: http://st.markdown(f'<div class="card"><div style="color:#8B8EA3">Total Scanned</div><div style="color:white; font-size:36px; font-weight:900">{len(TURBO_LIST)}</div><div style="color:#00FF88">-> 20 הכי חמות</div></div>', unsafe_allow_html=True)
with m2: http://st.markdown(f'<div class="card"><div style="color:#8B8EA3">Breakouts Detected</div><div style="color:white; font-size:36px; font-weight:900">{len(results)}</div></div>', unsafe_allow_html=True)
with m3: http://st.markdown(f'<div class="card"><div style="color:#8B8EA3">Avg. Change</div><div style="color:#00FF88; font-size:36px; font-weight:900">+{avg_change:.1f}%</div></div>', unsafe_allow_html=True)

http://st.markdown(f'<div class="card" style="margin-top:20px"><span style="color:white; font-size:20px; font-weight:900">Breakout Stocks - {len(results)} results</span><span style="color:#8B8EA3; float:right">Last: {st.session_state.last_scan}</span></div>', unsafe_allow_html=True)

if results:
    http://st.dataframe(pd.DataFrame(results)[["SYMBOL","PRICE","CHANGE","VOLUME","VOL_X","BREAKOUT_LEVEL","SIGNAL","RSI","Score"]], use_container_width=True, hide_index=True)
else:
    http://st.info("לחץ Run Now")
