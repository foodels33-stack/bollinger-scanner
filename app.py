import streamlit as st, yfinance as yf, pandas as pd, requests, plotly.graph_objects as go
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
from datetime import datetime
import pytz
st.set_page_config(page_title="BUY LOW 3500 - Full Body Break", layout="wide", page_icon="📉")
ISRAEL_TZ = pytz.timezone('Asia/Jerusalem')
ADMIN_PASS = st.secrets.get("ADMIN_PASSWORD", "omer1234")
BOT_TOKEN = st.secrets.get("BOT_TOKEN", "8777322821:AAFi4SikdUit4WJ3vEAUbYhBU0dp1KrBsuw")
CHAT_IDS = st.secrets.get("CHAT_IDS", ["6649894327"])
if 'is_admin' not in st.session_state: st.session_state.is_admin=False
if 'scan_res' not in st.session_state: st.session_state.scan_res=[]
if 'nasdaq_list' not in st.session_state: st.session_state.nasdaq_list=[]
def get_all_chat_ids():
    if isinstance(CHAT_IDS, list): return [str(x) for x in CHAT_IDS]
    return [str(CHAT_IDS)]
def send_tg(msg):
    try:
        token=str(BOT_TOKEN).strip()
        for cid in get_all_chat_ids():
            requests.get(f"https://api.telegram.org/bot{token}/sendMessage", params={"chat_id":cid,"text":msg}, timeout=10)
        return True
    except: return False
@st.cache_data(ttl=86400)
def load_nasdaq_3500():
    urls = ["https://raw.githubusercontent.com/datasets/nasdaq-listings/master/data/nasdaq-listed.csv","https://datahub.io/core/nasdaq-listings/r/nasdaq-listed_csv.csv"]
    for url in urls:
        try:
            df = pd.read_csv(url)
            col = None
            for c in ["Symbol","symbol","Ticker","ticker","ACT Symbol"]:
                if c in df.columns: col=c; break
            if col:
                lst = df[col].dropna().astype(str).str.strip().str.upper().tolist()
                lst = [x for x in lst if x.isalpha() and len(x)<=5]
                if len(lst) > 500: return lst[:3500]
        except: continue
    return ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","AVGO","COST","AMD","NFLX","PEP","ADBE","CSCO","QCOM","TMUS","INTC","INTU","AMAT","ISRG","BKNG","HON","VRTX","AMGN","REGN","ADI","LRCX","GILD","PANW","MDLZ","KLAC","SNPS","CDNS","CRWD","MELI","CSX","MAR","ORLY","CTAS","PYPL","ROP","ADSK","NXPI","ABNB","CPRT","ADP","MNST","FTNT","DASH","ROST","PCAR","PAYX","ODFL","CHTR","FAST","KDP","KHC","CTSH","EA","EXC","VRSK","GEHC","BKR","LULU","XEL","IDXX","WBD","TEAM","CSGP","TTWO","ANSS","BIIB","ILMN","ALGN","MRVL","ZS","DDOG","MDB","WDAY","OKTA","SPLK","NET","SNOW","PLTR","SOFI","HOOD","COIN","MARA","RIOT","MSTR","ARM","SMCI","MU","BA","NIO","LCID","RIVN","UPST","AI","SOUN","BBAI","DKNG","ROKU","SHOP","SQ","UBER","SNAP","PINS","RDDT","ASTS","LUNR","RKLB","IONQ","AFRM","OPEN","GME","AMC","SPCE","PLUG","CCL","AAL","JPM","BAC","WFC","C","GS","MS","TQQQ","SQQQ","SOXL","SOXS","SPY","QQQ","DIA","IWM","ARKK","VOO","VTI"]*20
def get_data(ticker, period="5d", interval="5m"):
    try:
        df=yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        return df.dropna()
    except: return pd.DataFrame()
def is_full_body_break(df):
    if len(df)<21: return False, None
    bb=BollingerBands(df["Close"],20,2.0)
    df["BB_L"]=bb.bollinger_lband(); df["BB_M"]=bb.bollinger_mavg(); df["BB_H"]=bb.bollinger_hband()
    df["RSI"]=RSIIndicator(df["Close"],14).rsi()
    last=df.iloc[-1]; prev=df.iloc[-2]
    close_break = last["Close"] < last["BB_L"]
    prev_above = prev["Close"] > prev["BB_L"]
    rsi_low = last["RSI"] < 35
    if close_break and prev_above and rsi_low:
        return True, last
    return False, last
if not st.session_state.nasdaq_list:
    with st.spinner("טוען 3500 מניות NASDAQ..."):
        st.session_state.nasdaq_list = load_nasdaq_3500()
ticker_list = st.session_state.nasdaq_list
now_il = datetime.now(ISRAEL_TZ).strftime("%d/%m/%Y %H:%M:%S")
st.markdown(f"<div style='background:#0e1117;padding:12px;border-radius:10px;color:white'>🕒 שעון ישראל: {now_il} | סורק {len(ticker_list)} מניות | Close < BB_L + RSI</div>", unsafe_allow_html=True)
with st.sidebar:
    st.header("🔐 מנהל")
    if not st.session_state.is_admin:
        pwd=st.text_input("סיסמה", type="password")
        if st.button("התחבר"):
            if pwd==ADMIN_PASS: st.session_state.is_admin=True; st.rerun()
            else: st.error("שגויה")
    else:
        st.success(f"מחובר - {len(ticker_list)} טיקרים")
        if st.button("התנתק"): st.session_state.is_admin=False; st.rerun()
    st.divider()
    auto=st.toggle("🤖 אוטומט כל 2 דק'", value=False, disabled=not st.session_state.is_admin)
    scan_limit=st.slider("כמה לסרוק", 50, 500, 250, step=50, disabled=not st.session_state.is_admin)
c1,c2 = st.columns([1,2])
with c1:
    st.subheader(f"🔍 חיפוש מתוך {len(ticker_list)}")
    search=st.selectbox("בחר טיקר", ticker_list, index=0)
    period=st.selectbox("תקופה", ["5d","1mo","3mo"], index=1)
    interval=st.selectbox("נרות", ["1m","5m","15m","30m","60m","1d"], index=1)
with c2:
    if search:
        df=get_data(search, period, interval)
        if not df.empty and len(df)>20:
            bb=BollingerBands(df["Close"],20,2.0)
            df["BB_L"]=bb.bollinger_lband(); df["BB_M"]=bb.bollinger_mavg(); df["BB_H"]=bb.bollinger_hband()
            df["RSI"]=RSIIndicator(df["Close"],14).rsi()
            fig=go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name=search))
            fig.add_trace(go.Scatter(x=df.index, y=df["BB_H"], line=dict(color="red",width=1), name="BB Upper"))
            fig.add_trace(go.Scatter(x=df.index, y=df["BB_M"], line=dict(color="yellow",width=1,dash="dash"), name="BB Mid TP"))
            fig.add_trace(go.Scatter(x=df.index, y=df["BB_L"], line=dict(color="#00FF00",width=2), name="BB Lower BREAK"))
            fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, title=f"{search} - שעון ישראל {now_il} - {interval}")
            st.plotly_chart(fig, use_container_width=True)
            broke,last=is_full_body_break(df)
            if broke: st.error(f"🚨 פריצה! {search} Close ${float(last['Close']):.2f} < BB_L ${float(last['BB_L']):.2f} -> TP ${float(last['BB_M']):.2f} RSI {float(last['RSI']):.1f}")
            else: st.info(f"אין פריצה | Close ${float(last['Close']):.2f} | BB_L ${float(last['BB_L']):.2f} | RSI {float(last['RSI']):.1f}")
st.divider()
st.subheader("📡 סורק פריצות אמיתיות")
def run_full_scan(limit=250):
    res=[]
    for t in ticker_list[:limit]:
        try:
            df=get_data(t,"5d","5m")
            broke,last=is_full_body_break(df)
            if broke:
                price=float(last["Close"]); tp=float(last["BB_M"])
                res.append({"SYMBOL":t,"PRICE":round(price,2),"BB_LOW":round(float(last["BB_L"]),2),"TP_MID":round(tp,2),"PROFIT%":round((tp-price)/price*100,2),"RSI":round(float(last["RSI"]),1),"TIME_IL":datetime.now(ISRAEL_TZ).strftime("%H:%M:%S")})
        except: continue
    return res
col_a,col_b = st.columns(2)
with col_a:
    if st.session_state.is_admin:
        if st.button("▶️ סרוק עכשיו 3500 - פריצות אמיתיות", use_container_width=True):
            with st.spinner(f"סורק {scan_limit} מניות..."):
                res=run_full_scan(scan_limit)
                st.session_state.scan_res=res
                if res:
                    msg=f"🔻 FULL BREAK {datetime.now(ISRAEL_TZ).strftime('%d/%m %H:%M')} IL - {len(res)} פריצות (Close < BB_L)\n"
                    for r in res[:10]: msg+=f"{r['SYMBOL']} ${r['PRICE']} -> TP ${r['TP_MID']} (+{r['PROFIT%']}%) RSI {r['RSI']}\n"
                    send_tg(msg); st.success(f"נמצאו {len(res)} ונשלחו לטלגרם")
                else: st.info("לא נמצאו פריצות אמיתיות")
    else:
        st.button("▶️ סרוק עכשיו", disabled=True, use_container_width=True)
with col_b:
    if st.session_state.is_admin:
        if st.button("📩 טסט בוט - שלח הודעת בדיקה", use_container_width=True):
            ok=send_tg(f"✅ טסט 3500 - שעון ישראל {now_il} - הבוט מחובר! Close < BB_L עובד!")
            if ok: st.success("נשלח לטלגרם! בדוק את הבוט")
            else: st.error("שגיאת טלגרם - בדוק Secrets")
    else:
        st.button("📩 טסט בוט", disabled=True, use_container_width=True)
if auto and st.session_state.is_admin:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2*60*1000, key="auto_3500")
    res=run_full_scan(scan_limit)
    if res:
        st.session_state.scan_res=res
        msg=f"AUTO BREAK {datetime.now(ISRAEL_TZ).strftime('%H:%M')} IL\n"
        for r in res[:5]: msg+=f"{r['SYMBOL']} ${r['PRICE']} TP {r['TP_MID']} (+{r['PROFIT%']}%)\n"
        send_tg(msg)
if st.session_state.scan_res:
    st.dataframe(pd.DataFrame(st.session_state.scan_res), use_container_width=True)
