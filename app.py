import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
import requests
import pytz
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
IL_TZ = pytz.timezone("Asia/Jerusalem")
NY_TZ = pytz.timezone("America/New_York")
TELEGRAM_USER = "@Bollingeromer"
def is_market_open_il():
    now_il = datetime.now(IL_TZ)
    if now_il.weekday() >= 5:
        return False
    total_minutes = now_il.hour * 60 + now_il.minute
    open_min = 16*60 + 30
    close_min = 23*60
    return open_min <= total_minutes < close_min
def send_telegram(msg):
    if not is_market_open_il():
        return
    try:
        url = f"https://api.callmebot.com/text.php?user={TELEGRAM_USER}&text={msg}"
        requests.get(url, timeout=3)
    except:
        pass
st.set_page_config(layout="wide", page_title="טרמינל לייב חכם", page_icon="👹")
st.markdown("""
<style>
.stApp{background:#111315;color:#f5f5f5}
.block-container{max-width:98%!important; padding:1rem!important;}
.stButton>button{background:#1e2228!important; color:#fff!important; border:1px solid #00ff88!important; border-radius:12px!important; font-weight:bold!important; height:3em!important;}
.stButton>button:hover{background:#00ff88!important; color:#000!important;}
[data-testid="stDataFrame"]{background:#1a1d22!important;}
thead tr th{background:#22262d!important; color:#00ff88!important; font-size:1.05rem!important;}
tbody tr td{color:#e8e8e8!important; font-size:0.95rem!important;}
@media (max-width: 768px){
 .block-container{padding:0.5rem!important;}
    h1,h2,h3{font-size:1.2rem!important; color:#00ff88!important;}
    [data-testid="column"]{width:100%!important; flex: 1 1 100%!important;}
    [data-testid="stHorizontalBlock"]{flex-direction: column-reverse!important;}
}
</style>
""", unsafe_allow_html=True)
if 'focus' not in st.session_state:
    st.session_state.focus="NVDA"
if 'scan' not in st.session_state:
    st.session_state.scan=pd.DataFrame()
if 'is_scanning' not in st.session_state:
    st.session_state.is_scanning=False
tf = st.session_state.get('tf', 'יומי')
is_live = st.sidebar.checkbox("🔴 לייב פעיל", value=True)
enable_tg = st.sidebar.checkbox("📲 שלח לטלגרם Bollingeromer", value=True)
now_il_str = datetime.now(IL_TZ).strftime('%H:%M:%S %d/%m/%Y')
market_status = "🟢 שוק פתוח (שעון ישראל)" if is_market_open_il() else "🔴 שוק סגור (שעון ישראל)"
st.sidebar.info(f"{market_status}\n\nשעון ישראל: {now_il_str}")
if is_live and not st.session_state.is_scanning:
    sec = 10 if tf=="1דק לייב" else 15
    st_autorefresh(interval=sec*1000, key="smart_live")
def winrate(ticker):
    try:
        d=yf.download(ticker, period="2y", interval="1d", progress=False, auto_adjust=True)
        if d is None or len(d)<60:
            return 50
        if isinstance(d.columns, pd.MultiIndex):
            d.columns=d.columns.get_level_values(0)
        d['upper']=ta.volatility.bollinger_hband(d['Close'],20,2)
        wins=total=0
        for i in range(20, len(d)-5):
            if d['Close'].iloc[i] > d['upper'].iloc[i]:
                total+=1
                if d['Close'].iloc[i+5] > d['Close'].iloc[i]:
                    wins+=1
        return int(wins/total*100) if total>10 else 50
    except:
        return 50
def make_chart(ticker, tf):
    try:
        p_map={"1דק לייב":("1d","1m"), "5דק לייב":("5d","5m"), "יומי":("3mo","1d")}
        per, inter = p_map[tf]
        df=yf.download(ticker, period=per, interval=inter, progress=False, auto_adjust=True)
        if df is None or len(df)<20:
            return None, 0, "", ""
        if isinstance(df.columns, pd.MultiIndex):
            df.columns=df.columns.get_level_values(0)
        df['upper']=ta.volatility.bollinger_hband(df['Close'],20,2)
        df['lower']=ta.volatility.bollinger_lband(df['Close'],20,2)
        df['rsi']=ta.momentum.rsi(df['Close'],14)
        p=float(df['Close'].iloc[-1])
        wr=winrate(ticker)
        try:
            if df.index.tz is None:
                idx_il = df.index.tz_localize(NY_TZ).tz_convert(IL_TZ)
            else:
                idx_il = df.index.tz_convert(IL_TZ)
            last_candle_str = idx_il[-1].strftime("%d/%m %H:%M")
        except:
            last_candle_str = df.index[-1].strftime("%d/%m %H:%M")
        now_il_display = datetime.now(IL_TZ).strftime("%H:%M:%S %d/%m/%Y")
        live_time = f"{now_il_display} | נר אחרון: {last_candle_str}"
        bt = last_candle_str
        fig=make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8,0.2], vertical_spacing=0.08)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#00ff88', decreasing_line_color='#ff3344', increasing_fillcolor='#00ff88', decreasing_fillcolor='#ff3344', name="נרות"), row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['upper'], line=dict(color='#00d4ff', width=2, dash='dash'), name='Upper BB'), row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['lower'], line=dict(color='#00d4ff', width=2, dash='dash'), fill='tonexty', fillcolor='rgba(255,221,0,0.12)', name='Lower BB'), row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], line=dict(color='#ff00ff', width=2), name='RSI'), row=2,col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)
        fig.update_layout(height=700, template="plotly_dark", paper_bgcolor="#111315", plot_bgcolor="#1a1d22", xaxis_rangeslider_visible=False, font=dict(color="#ffffff", size=13), title=dict(text=f"{ticker} ${p:.2f} | שעון ישראל {now_il_display} | נר אחרון {last_candle_str} | הצלחה {wr}% | {tf} | {market_status}", font=dict(size=14, color="#00ff88")), margin=dict(l=10,r=10,t=60,b=10))
        return fig, wr, bt, live_time
    except Exception as e:
        st.error(f"שגיאת גרף: {e}")
        return None, 0, "", ""
def run_scan(n, mode, tf):
    st.session_state.is_scanning=True
    per, inter = "2d", "1m"
    try:
        syms=pd.read_csv("https://raw.githubusercontent.com/datasets/nasdaq-listings/main/data/nasdaq-listed.csv")['Symbol'].dropna().tolist()
        syms=[x for x in syms if x.isalpha() and 1<len(x)<=4][:n]
    except:
        syms=["NVDA","TSLA","PLTR","SOFI","AMD","META","COIN","MARA","SMCI","MRVL","AAPL","MSFT","GOOGL","AMZN","NFLX"]*350
        syms=syms[:n]
    res=[]
    prog=st.progress(0)
    status_text=st.empty()
    for i,sym in enumerate(syms[:n]):
        status_text.text(f"סורק {i+1}/{n} : {sym} | שעון ישראל {datetime.now(IL_TZ).strftime('%H:%M:%S')} | אונליין 1דק")
        try:
            d=yf.download(sym, period=per, interval=inter, progress=False, auto_adjust=True)
            if d is None or len(d)<30:
                continue
            if isinstance(d.columns, pd.MultiIndex):
                d.columns=d.columns.get_level_values(0)
            d['upper']=ta.volatility.bollinger_hband(d['Close'],20,2)
            d['lower']=ta.volatility.bollinger_lband(d['Close'],20,2)
            d['rsi']=ta.momentum.rsi(d['Close'],14)
            d['vol_ma']=d['Volume'].rolling(20).mean()
            p=float(d['Close'].iloc[-1])
            u=float(d['upper'].iloc[-1])
            l=float(d['lower'].iloc[-1])
            r=float(d['rsi'].iloc[-1])
            v=float(d['Volume'].iloc[-1])
            vm=float(d['vol_ma'].iloc[-1]) if pd.notna(d['vol_ma'].iloc[-1]) else v
            change=(p-float(d['Close'].iloc[-2]))/float(d['Close'].iloc[-2])*100 if len(d)>=2 else 0
            try:
                if d.index.tz is None:
                    idx_il = d.index.tz_localize(NY_TZ).tz_convert(IL_TZ)
                else:
                    idx_il = d.index.tz_convert(IL_TZ)
                breakout_time = idx_il[-1].strftime("%d/%m %H:%M:%S")
                bt_found = False
                for j in range(len(d)-1, max(-1,len(d)-20), -1):
                    cp=float(d['Close'].iloc[j])
                    up=float(d['upper'].iloc[j])
                    lo=float(d['lower'].iloc[j])
                    if cp>up or cp<lo:
                        breakout_time = idx_il[j].strftime("%d/%m %H:%M:%S")
                        bt_found=True
                        break
            except:
                breakout_time = d.index[-1].strftime("%d/%m %H:%M:%S")
            is_break=p>u or p<l
            is_hot=change>=5 and v>vm*2.5
            is_extreme=is_break and v>vm*1.8 and ((p>u and r>68) or (p<l and r<32))
            if mode=="קיצוני 🚨" and not is_extreme:
                continue
            if mode=="רותחות 🔥" and not is_hot:
                continue
            if mode=="בולינגר" and not is_break:
                continue
            if not (is_break or is_hot):
                continue
            wr=winrate(sym)
            sig="קיצוני 🚨" if is_extreme else f"רותחת 🔥 {change:.1f}%" if is_hot else "LONG 🚀" if p>u else "SHORT 🔻"
            dec="✅ קנה" if wr>=65 and "SHORT" not in sig else "❌ אל תקנה" if "SHORT" in sig else "⚠️ זהירות"
            res.append([sym, p, breakout_time, sig, f"{wr}%", dec, round(p*1.08,2), round(p*0.95,2)])
            if is_extreme and enable_tg and is_market_open_il():
                send_telegram(f"🚨 {sig} {sym} ${p:.2f} | {change:.1f}% | RSI {r:.0f} | Vol {v/vm:.1f}x | {breakout_time} שעון ישראל")
        except:
            pass
        prog.progress((i+1)/len(syms))
    st.session_state.scan=pd.DataFrame(res, columns=["טיקר","מחיר לייב","זמן פריצה (IL)","סוג","אחוז הצלחה","החלטה","יעד","סטופ"])
    prog.empty()
    status_text.empty()
    st.session_state.is_scanning=False
    st.success(f"סריקה אונליין 1דק הושלמה! נמצאו {len(res)} מניות | שעון ישראל {datetime.now(IL_TZ).strftime('%H:%M:%S')}")
c1, c2, c3 = st.columns([2,1,1])
with c1:
    q=st.text_input("🔎 חיפוש טיקר", value=st.session_state.focus, label_visibility="collapsed", placeholder="NVDA, TSLA...")
with c2:
    if st.button("פתח גרף", use_container_width=True, type="primary"):
        st.session_state.focus=q.upper().strip()
        st.rerun()
with c3:
    tf_select=st.radio("טווח גרף", ["1דק לייב","5דק לייב","יומי"], index=2, horizontal=True, label_visibility="collapsed")
    st.session_state.tf=tf_select
st.divider()
left,right=st.columns([3,1])
with right:
    st.markdown("### ⚙️ סריקה אונליין 1דק")
    st.caption(f"שעון ישראל: {datetime.now(IL_TZ).strftime('%H:%M:%S')} | {market_status}")
    st.caption("הסריקה תמיד 1 דק' לייב - איתות פריצה אונליין אמיתי | NY->IL תיקון")
    mode=st.selectbox("סוג סינון", ["הכל","קיצוני 🚨","רותחות 🔥","בולינגר"])
    colA, colB = st.columns(2)
    with colA:
        if st.button("SCAN 100", use_container_width=True):
            run_scan(100, mode, st.session_state.get('tf','יומי'))
        if st.button("SCAN 500", use_container_width=True):
            run_scan(500, mode, st.session_state.get('tf','יומי'))
    with colB:
        if st.button("SCAN 1000", use_container_width=True):
            run_scan(1000, mode, st.session_state.get('tf','יומי'))
        if st.button("SCAN 3500 🚀", use_container_width=True, type="primary"):
            run_scan(3500, mode, st.session_state.get('tf','יומי'))
    if not st.session_state.scan.empty:
        st.dataframe(st.session_state.scan.sort_values("אחוז הצלחה", ascending=False), use_container_width=True, height=450)
        sel=st.selectbox("פתח מהטבלה", st.session_state.scan["טיקר"].tolist())
        if st.button("הצג מטבלה", use_container_width=True):
            st.session_state.focus=sel
            st.rerun()
with left:
    fig, wr, bt, live_time = make_chart(st.session_state.focus, st.session_state.get('tf','יומי'))
    if fig:
        if wr>=65:
            st.success(f"🔴 לייב: {st.session_state.focus} | {live_time} | הצלחה {wr}% | ✅ קנה | {market_status}")
        else:
            st.warning(f"🔴 לייב: {st.session_state.focus} | {live_time} | הצלחה {wr}% | {market_status}")
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom':True, 'displayModeBar':True, 'modeBarButtonsToAdd':['drawline','drawrect','eraseshape']})
    else:
        st.error("לא נמצא גרף - בדוק טיקר")
