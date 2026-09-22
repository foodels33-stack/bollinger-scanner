import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, SMAIndicator
import requests
from datetime import datetime

st.set_page_config(page_title="TradePulse PRO - BUY LOW FULL MONSTER", layout="wide", page_icon="🚀")

ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "omer1234")
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'scan_results' not in st.session_state:
    st.session_state.scan_results=[]

BOT_TOKEN = st.secrets.get("BOT_TOKEN", "8777322821:AAFzDGdAzFjz_7vJLEDsGxgxp5GkplGs9vg")
CHAT_ID = st.secrets.get("CHAT_ID", "6649894327")
CHAT_IDS_RAW = st.secrets.get("CHAT_IDS", None)
BOT_USERNAME = "@omer_turbo72_bot"

def get_all_chat_ids():
    ids=[]
    if CHAT_IDS_RAW:
        if isinstance(CHAT_IDS_RAW, list):
            ids=[str(x).strip() for x in CHAT_IDS_RAW]
        else:
            ids=[str(CHAT_IDS_RAW).strip()]
    if CHAT_ID:
        ids.append(str(CHAT_ID).strip())
    seen=set(); out=[]
    for x in ids:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

def send_telegram(msg):
    try:
        token=str(st.secrets.get("BOT_TOKEN", BOT_TOKEN)).strip()
        ok=False
        for cid in get_all_chat_ids():
            url=f"https://api.telegram.org/bot{token}/sendMessage"
            r=requests.get(url, params={"chat_id":cid, "text":msg}, timeout=15)
            if r.status_code==200: ok=True
        return ok
    except Exception as e:
        st.error(f"Telegram error: {e}")
        return False

TURBO_LIST=["NVDA","AAPL","MSFT","TSLA","AMD","META","GOOGL","AMZN","SPY","QQQ","NFLX","PLTR","SOFI","MARA","RIOT","COIN","MSTR","SMCI","ARM","AVGO","MU","INTC","QCOM","BA","NIO","LCID","RIVN","UPST","AI","SOUN","BBAI","DKNG","ROKU","SHOP","SQ","PYPL","UBER","LYFT","SNAP","PINS","RDDT","ASTS","LUNR","RKLB","IONQ","JOBY","HOOD","AFRM","OPEN","GME","AMC","TLRY","CGC","SPCE","PLUG","FCEL","NCLH","CCL","AAL","UAL","DAL","MRO","OXY","XOM","CVX","JPM","BAC","WFC","C","GS","MS","BLK","ARKK","TQQQ","SQQQ","SPXL","SOXL","SOXS","LABU","LABD","BITO","BITX","ETHU","CONL","NVDL","TSLL","TSLS","MSTU","MSTZ"]

@st.cache_data(ttl=60, show_spinner=False)
def get_data(t,p,i):
    try:
        if i=="1d" and p in ["1d","5d"]: p="1mo"
        if p=="1d" and i=="1d": p="5d"
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
    df["EMA50"]=EMAIndicator(close=df["Close"],window=50).ema_indicator()
    df["SMA200"]=SMAIndicator(close=df["Close"],window=200).sma_indicator()
    df["VOL_AVG"]=df["Volume"].rolling(20).mean().fillna(df["Volume"].mean())
    return df

def analyze_long(df):
    if df.empty or len(df)<21: return {"sig":"NO DATA","score":0}
    l=df.iloc[-1]; p=df.iloc[-2]
    full_break=l["High"]<l["BB_L"] and l["Open"]<l["BB_L"] and l["Close"]<l["BB_L"]
    was_above=p["Close"]>p["BB_L"] or p["High"]>p["BB_L"]
    if full_break and was_above and l["RSI"]<35:
        return {"sig":"BUY DIP - Full Breakdown","score":100,"last":l}
    body_break=l["Open"]<l["BB_L"] and l["Close"]<l["BB_L"] and l["Low"]<l["BB_L"]
    if body_break and l["RSI"]<42:
        return {"sig":"BUY DIP - Near Breakdown","score":80,"last":l}
    return {"sig":"neutral","score":0,"last":l}

def run_scan_20():
    res=[]
    for t in TURBO_LIST:
        d=get_data(t,"5d","5m")
        if d.empty or len(d)<21: continue
        try:
            d=add_ind(d); l=d.iloc[-1]
            if len(d)<2: continue
            chg=(float(d.iloc[-2]["Close"])-float(l["Close"]))/float(d.iloc[-2]["Close"])*100
            if chg<=0.3: continue
            vr=l["Volume"]/l["VOL_AVG"] if l["VOL_AVG"]>0 else 0
            r=analyze_long(d)
            if r["score"]>=80:
                tp_mid=round(float(l["BB_M"]),2)
                profit=round((tp_mid-float(l["Close"]))/float(l["Close"])*100,2)
                res.append({"SYMBOL":t,"PRICE":round(float(l["Close"]),2),"ירידה %":round(float(chg),2),"VOLUME":f"{l['Volume']/1000000:.1f}M","VOL_X":f"{float(vr):.1f}x","BB_LOW":round(float(l["BB_L"]),2),"TP_BB_MID":tp_mid,"רווח צפוי %":profit,"SIGNAL":r["sig"],"RSI":round(float(l["RSI"]),1),"Score":r["score"]})
        except: continue
    return sorted(res, key=lambda x: x["Score"], reverse=True)[:20]

st.markdown(f'<div style="background:#15182A; padding:12px; border-radius:12px; color:white; font-weight:700">TradePulse PRO - BUY LOW FULL MONSTER - {BOT_USERNAME} - אוטומט + TP</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🔐 כניסת מנהל")
    if not st.session_state.is_admin:
        pwd=st.text_input("סיסמת מנהל", type="password")
        if st.button("התחבר"):
            if pwd==ADMIN_PASSWORD:
                st.session_state.is_admin=True; st.rerun()
            else: st.error("סיסמה שגויה")
        st.info("צפייה פתוחה לכולם. ניהול רק עם סיסמה.")
    else:
        st.success("מחובר כמנהל")
        if st.button("התנתק"):
            st.session_state.is_admin=False; st.rerun()

c1,c2,c3,c4=st.columns(4)
with c1: ticker=st.text_input("Ticker",value="NVDA").upper().strip()
with c2: mode=st.selectbox("סוג מסחר",["מסחר יומי","סווינג","סקאלפ","השקעה"], index=0)
with c3: period=st.selectbox("תקופה",["1mo","3mo","6mo","1y","5d"], index=0)
with c4: interval=st.selectbox("נרות",["1m","2m","5m","15m","30m","60m","1d"], index=2)

c5,c6,c7,c8=st.columns(4)
with c5: show_bb=st.checkbox("Bollinger", value=True)
with c6: show_ema=st.checkbox("EMA/SMA", value=True)
with c7: auto_scan=st.toggle("🤖 אוטומט + טלגרם", value=False, disabled=not st.session_state.is_admin)
with c8:
    if st.session_state.is_admin:
        if st.button("📩 טסט טלגרם"):
            ok=send_telegram(f"טסט BUY LOW {datetime.now().strftime('%d/%m %H:%M')} - הבוט {BOT_USERNAME} מחובר!")
            st.success("נשלח!") if ok else st.error("שגיאת טלגרם")
    else: st.button("📩 טסט טלגרם", disabled=True)

if ticker:
    df=get_data(ticker,period,interval)
    if df.empty: st.warning(f"אין נתונים ל-{ticker}")
    elif len(df)<20: st.warning(f"יש רק {len(df)} נרות - צריך לפחות 20. בחר 1mo.")
    else:
        df=add_ind(df); last=df.iloc[-1]; prev=df.iloc[-2]
        st.metric(f"{ticker} - {mode}", f"${float(last['Close']):.2f}", f"{float(last['Close'])-float(prev['Close']):.2f} ({(float(last['Close'])-float(prev['Close']))/float(prev['Close'])*100:.2f}%)")
        fig=make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6,0.2,0.2], vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="נרות"), row=1, col=1)
        if show_bb:
            fig.add_trace(go.Scatter(x=df.index, y=df["BB_H"], name="BB Upper"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df["BB_M"], name="BB Middle - TP"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df["BB_L"], name="BB Lower"), row=1, col=1)
        if show_ema:
            fig.add_trace(go.Scatter(x=df.index, y=df["EMA20"], name="EMA20"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df["EMA50"], name="EMA50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"], name="SMA200"), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume"), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI 14"), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        fig.update_layout(template="plotly_dark", height=750, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        sig=analyze_long(df)
        if sig["score"]>=80:
            st.success(f"{sig['sig']} - {ticker}")
            if st.session_state.is_admin and st.button("שלח איתות זה לטלגרם"):
                send_telegram(f"{sig['sig']} {ticker} ${float(last['Close']):.2f} RSI {float(last['RSI']):.1f} TP {float(last['BB_M']):.2f}")

st.divider()
st.subheader("סורק MONSTER - BUY LOW")
col_a, col_b = st.columns(2)
with col_a:
    if st.session_state.is_admin:
        if st.button("Run Now - מצא נפילות לקנייה", use_container_width=True):
            with st.spinner("סורק..."):
                results=run_scan_20()
                st.session_state.scan_results=results
                if results:
                    msg=f"BUY LOW ALERT - {len(results)} נפילות\n\n"
                    for r in results[:7]: msg+=f"{r['SYMBOL']} ${r['PRICE']} | ירידה {r['ירידה %']}% | RSI {r['RSI']} | TP {r['TP_BB_MID']} (+{r['רווח צפוי %']}%)\n"
                    send_telegram(msg); st.success(f"נמצאו {len(results)}")
                else: st.info("לא נמצאו")
    else:
        st.button("Run Now", use_container_width=True, disabled=True)
with col_b: st.caption(f"אוטומט כל 2 דקות ל-{BOT_USERNAME}")

if auto_scan and st.session_state.is_admin:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=2*60*1000, key="auto_buy_low")
        results=run_scan_20()
        if results:
            prev=st.session_state.scan_results
            if not prev or results[0]["SYMBOL"]!=prev[0]["SYMBOL"]:
                st.session_state.scan_results=results
                msg=f"AUTO BUY LOW {datetime.now().strftime('%H:%M')}\n\n"
                for r in results[:5]: msg+=f"{r['SYMBOL']} ${r['PRICE']} | ירידה {r['ירידה %']}% | RSI {r['RSI']} | TP {r['TP_BB_MID']} (+{r['רווח צפוי %']}%)\n"
                send_telegram(msg)
    except Exception as e: st.warning(f"הוסף ל-requirements: streamlit-autorefresh - {e}")

if st.session_state.scan_results:
    st.dataframe(pd.DataFrame(st.session_state.scan_results), use_container_width=True)
else: st.info("לחץ Run Now (מנהל בלבד)")
