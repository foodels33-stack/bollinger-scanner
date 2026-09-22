import streamlit as st
import yfinance as yf
import pandas as pd
import http://plotly.graph_objects as go
from http://plotly.subplots import make_subplots
from http://ta.volatility import BollingerBands
from http://ta.momentum import RSIIndicator
from http://ta.trend import EMAIndicator, SMAIndicator
import requests
import time
from datetime import datetime

http://st.set_page_config(page_title="TradePulse PRO - BUY LOW FULL MONSTER", layout="wide", page_icon="🚀")

if 'scan_results' not in http://st.session_state:
    http://st.session_state.scan_results=[]

BOT_TOKEN = http://st.secrets.get("BOT_TOKEN", "8777322821:AAFzDGdAzFjz_7vJLEDsGxgxp5GkplGs9vg")
CHAT_ID = http://st.secrets.get("CHAT_ID", "6649894327")
BOT_USERNAME = "@omer_turbo72_bot"

def send_telegram(msg):
    try:
        token = http://st.secrets.get("BOT_TOKEN", BOT_TOKEN)
        chat_id = http://st.secrets.get("CHAT_ID", CHAT_ID)
        if not chat_id:
            try:
                r = http://requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10).json()
                if http://r.get("result"):
                    chat_id = str(r["result"][-1]["message"]["chat"]["id"])
            except:
                pass
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = http://requests.get(url, params={"chat_id": str(chat_id), "text": msg}, timeout=15)
        if http://resp.status_code == 200:
            return True
        else:
            http://st.error(f"Telegram API: {resp.text}")
            return False
    except Exception as e:
        http://st.error(f"Telegram error: {e}")
        return False

TURBO_LIST=["NVDA","AAPL","MSFT","TSLA","AMD","META","GOOGL","AMZN","SPY","QQQ","NFLX","PLTR","SOFI","MARA","RIOT","COIN","MSTR","SMCI","ARM","AVGO","MU","INTC","QCOM","BA","NIO","LCID","RIVN","UPST","AI","SOUN","BBAI","DKNG","ROKU","SHOP","SQ","PYPL","UBER","LYFT","SNAP","PINS","RDDT","ASTS","LUNR","RKLB","IONQ","JOBY","HOOD","AFRM","OPEN","GME","AMC","TLRY","CGC","SPCE","PLUG","FCEL","NCLH","CCL","AAL","UAL","DAL","MRO","OXY","XOM","CVX","JPM","BAC","WFC","C","GS","MS","BLK","ARKK","TQQQ","SQQQ","SPXL","SOXL","SOXS","LABU","LABD","BITO","BITX","ETHU","CONL","NVDL","TSLL","TSLS","MSTU","MSTZ"]

@st.cache_data(ttl=60, show_spinner=False)
def get_data(t,p,i):
    try:
        df=yf.download(t,period=p,interval=i,progress=False,auto_adjust=True)
        if http://df.empty: return df
        if isinstance(df.columns,pd.MultiIndex):
            http://df.columns=df.columns.get_level_values(0)
        return http://df.dropna()
    except:
        return http://pd.DataFrame()

def add_ind(df):
    if len(df)<20: return df
    bb=BollingerBands(close=df["Close"],window=20,window_dev=2.0)
    df["BB_H"]=bb.bollinger_hband()
    df["BB_L"]=bb.bollinger_lband()
    df["BB_M"]=bb.bollinger_mavg()
    df["BB_W"]=(df["BB_H"]-df["BB_L"])/df["BB_M"].replace(0,0.0001)_100
    df["BB_P"]=(df["Close"]-df["BB_L"])/(df["BB_H"]-df["BB_L"]).replace(0,0.0001)_100
    df["RSI"]=RSIIndicator(close=df["Close"],window=14).rsi()
    df["EMA20"]=EMAIndicator(close=df["Close"],window=20).ema_indicator()
    df["EMA50"]=EMAIndicator(close=df["Close"],window=50).ema_indicator()
    df["SMA200"]=SMAIndicator(close=df["Close"],window=200).sma_indicator()
    df["VOL_AVG"]=df["Volume"].rolling(20).mean().fillna(df["Volume"].mean())
    return df

def analyze_long(df):
    if http://df.empty or len(df)<21: return {"sig":"NO DATA","score":0}
    l=df.iloc[-1]; p=df.iloc[-2]
    full_break = l["High"] < l["BB_L"] and l["Open"] < l["BB_L"] and l["Close"] < l["BB_L"]
    was_above = p["Close"] > p["BB_L"] or p["High"] > p["BB_L"]
    if full_break and was_above and l["RSI"] < 35:
        return {"sig":"BUY DIP - Full Breakdown","score":100,"last":l}
    body_break = l["Open"] < l["BB_L"] and l["Close"] < l["BB_L"] and l["Low"] < l["BB_L"]
    if body_break and l["RSI"] < 42:
        return {"sig":"BUY DIP - Near Breakdown","score":80,"last":l}
    return {"sig":"neutral","score":0,"last":l}

def run_scan_20():
    res=[]
    for t in TURBO_LIST:
        d=get_data(t,"5d","5m")
        if http://d.empty or len(d)<21: continue
        try:
            d=add_ind(d); l=d.iloc[-1]
            chg = (d.iloc[-2]["Close"]-l["Close"])/d.iloc[-2]["Close"]_100
            if chg <= 0.3: continue
            vr=l["Volume"]/l["VOL_AVG"] if l["VOL_AVG"]>0 else 0
            r=analyze_long(d)
            if r["score"]>=80:
                tp_mid = round(float(l["BB_M"]),2)
                profit = round((tp_mid - float(l["Close"]))/float(l["Close"])_100,2)
                http://res.append({"SYMBOL":t,"PRICE":round(float(l["Close"]),2),"ירידה %":round(float(chg),2),"VOLUME":f"{l['Volume']/1000000:.1f}M","VOL_X":f"{vr:.1f}x","BB_LOW":round(float(l["BB_L"]),2),"TP_BB_MID":tp_mid,"רווח צפוי %":profit,"SIGNAL":r["sig"],"RSI":round(float(l["RSI"]),1),"Score":r["score"]})
        except:
            continue
    return sorted(res, key=lambda x: x["Score"], reverse=True)[:20]

http://st.markdown(f'<div style="background:#15182A; padding:12px; border-radius:12px; color:white; font-weight:700">TradePulse PRO - BUY LOW FULL MONSTER - פריצה למטה גוף+זנב + {BOT_USERNAME} - אוטומט + TP</div>', unsafe_allow_html=True)

c1,c2,c3,c4=st.columns()
with c1:
    ticker=st.text_input("Ticker",value="NVDA").upper().strip()
with c2:
    mode=st.selectbox("סוג מסחר",["מסחר יומי","סווינג","סקאלפ","השקעה"], index=0)
with c3:
    period=st.selectbox("תקופה",["1d","5d","1mo","3mo","6mo","1y"], index=1)
with c4:
    interval=st.selectbox("נרות",["1m","2m","5m","15m","30m","60m","1d"], index=2)[3][1]

c5,c6,c7,c8=st.columns()
with c5:
    show_bb=st.checkbox("Bollinger", value=True)
with c6:
    show_ema=st.checkbox("EMA/SMA", value=True)
with c7:
    auto_scan=st.toggle("🤖 אוטומט + טלגרם", value=False)
with c8:
    if http://st.button("📩 טסט טלגרם"):
        ok = send_telegram(f"✅ טסט BUY LOW {datetime.now().strftime('%d/%m %H:%M')} - הבוט {BOT_USERNAME} מחובר! מוכן לפריצות למטה")
        if ok: http://st.success("נשלח לטלגרם!")
        else: http://st.error("שגיאת טלגרם - בדוק Secrets")[1]

if ticker:
    df=get_data(ticker,period,interval)
    if not http://df.empty:
        df=add_ind(df)
        last=df.iloc[-1]
        prev=df.iloc[-2]
        http://st.metric(f"{ticker} - {mode}", f"${last['Close']:.2f}", f"{last['Close']-prev['Close']:.2f} ({(last['Close']-prev['Close'])/prev['Close']_100:.2f}%)")
        fig=make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6,0.2,0.2], vertical_spacing=0.03)
        http://fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="נרות"), row=1, col=1)
        if show_bb:
            http://fig.add_trace(go.Scatter(x=df.index, y=df["BB_H"], name="BB Upper", line=dict(color='rgba(255,100,100,0.8)')), row=1, col=1)
            http://fig.add_trace(go.Scatter(x=df.index, y=df["BB_M"], name="BB Middle - TP", line=dict(color='rgba(255,255,100,0.8)')), row=1, col=1)
            http://fig.add_trace(go.Scatter(x=df.index, y=df["BB_L"], name="BB Lower - קנייה", line=dict(color='rgba(100,255,100,0.8)')), row=1, col=1)
        if show_ema:
            http://fig.add_trace(go.Scatter(x=df.index, y=df["EMA20"], name="EMA20"), row=1, col=1)
            http://fig.add_trace(go.Scatter(x=df.index, y=df["EMA50"], name="EMA50"), row=1, col=1)
            http://fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"], name="SMA200"), row=1, col=1)
        http://fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume"), row=2, col=1)
        http://fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI 14"), row=3, col=1)
        http://fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        http://fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        http://fig.update_layout(template="plotly_dark", height=750, xaxis_rangeslider_visible=False, showlegend=True)
        http://st.plotly_chart(fig, use_container_width=True)
        http://st.write(f"RSI: {last['RSI']:.1f} | BB Width: {last['BB_W']:.2f}% | BB %P: {last['BB_P']:.1f}% | Vol x: {last['Volume']/last['VOL_AVG']:.1f}x | BB Low: {last['BB_L']:.2f} | Close: {last['Close']:.2f}")
        sig = analyze_long(df)
        if sig["score"]>=80:
            http://st.success(f"🔥 {sig['sig']} - {ticker} - כל הגוף והזנב מתחת ל-BB_L!")
            if http://st.button("שלח איתות זה לטלגרם"):
                send_telegram(f"🟢 {sig['sig']} {ticker} ${float(last['Close']):.2f} RSI {float(last['RSI']):.1f} TP {float(last['BB_M']):.2f}")

http://st.divider()
http://st.subheader("סורק MONSTER - BUY LOW - 20 הכי נפלו לקנייה בזול")

col_a, col_b = http://st.columns()
with col_a:
    if http://st.button("Run Now - מצא נפילות לקנייה", use_container_width=True):
        with http://st.spinner("סורק 80 טיקרים לנפילות..."):
            results=run_scan_20()
            http://st.session_state.scan_results=results
            if results:
                msg = f"🚨 BUY LOW ALERT - {len(results)} נפילות\n\n"
                for r in results[:7]:
                    msg += f"{r['SYMBOL']} ${r['PRICE']} | ירידה {r['ירידה %']}% | RSI {r['RSI']} | TP {r['TP_BB_MID']} (+{r['רווח צפוי %']}%)\n"
                send_telegram(msg)
                http://st.success(f"נמצאו {len(results)} - נשלח לטלגרם!")
with col_b:
    http://st.caption(f"אוטומט סורק כל 2 דקות ושולח ל-{BOT_USERNAME} גם כשאתה לא מול המחשב. צריך להשאיר טאב פתוח ב-Streamlit Cloud")[1][2]

if auto_scan:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=2_60*1000, key="auto_buy_low")
        with http://st.spinner("סריקה אוטומטית רצה..."):
            results=run_scan_20()
            if results:
                if not http://st.session_state.scan_results or (len(st.session_state.scan_results)>0 and results[0]["SYMBOL"]!= http://st.session_state.scan_results[0]["SYMBOL"]):
                    http://st.session_state.scan_results=results
                    msg = f"🤖 AUTO BUY LOW {datetime.now().strftime('%H:%M')}\n\n"
                    for r in results[:5]:
                        msg += f"{r['SYMBOL']} ${r['PRICE']} | ירידה {r['ירידה %']}% | RSI {r['RSI']} | TP {r['TP_BB_MID']} (+{r['רווח צפוי %']}%)\n"
                    send_telegram(msg)
    except Exception as e:
        http://st.warning(f"הוסף ל-requirements.txt: streamlit-autorefresh - שגיאה: {e}")

results=st.session_state.scan_results
if results:
    m1,m2,m3=st.columns(3)
    with m1: http://st.metric("Total Scanned", len(TURBO_LIST))
    with m2: http://st.metric("BUY DIP Found", len(results))
    with m3:
        avg=sum([r["ירידה %"] for r in results])/len(results) if results else 0
        http://st.metric("Avg Drop", f"{avg:.1f}%")
    http://st.dataframe(pd.DataFrame(results), use_container_width=True)
else:
    http://st.info("לחץ Run Now או הפעל אוטומט - ימצא רק מניות ששברו למטה עם כל הגוף והזנב - לקנייה בזול")
