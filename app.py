import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import http://plotly.graph_objects as go
import requests
import pytz
from http://plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
IL_TZ = http://pytz.timezone("Asia/Jerusalem")
NY_TZ = http://pytz.timezone("America/New_York")
BOT_TOKEN = "8777322821:AAFzDGdAzFjz_7vJLEDsGxgxp5GkplGs9vg"
CHAT_ID = "6649894327"
NASDAQ_100 = ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","AVGO","COST","TSLA","NFLX","AMD","TMUS","PEP","LIN","ADBE","CSCO","QCOM","INTU","AMGN","TXN","ISRG","BKNG","HON","AMAT","GILD","VRTX","PANW","ADP","MDLZ","ADI","REGN","LRCX","MU","KLAC","SNPS","CDNS","MELI","MAR","CTAS","ORLY","CSX","PYPL","MNST","FTNT","ADSK","DASH","NXPI","ABNB","PCAR","ROST","WDAY","KDP","MRVL","IDXX","CTSH","ODFL","FAST","CEG","CRWD","DDOG","TEAM","ZS","EXC","XEL","EA","BKR","GEHC","ON","TTD","WBD","BIIB","CHTR","MRNA","ILMN","LCID","ZM","RIVN","ARM","SMCI"]
def is_market_open_il():
    now_il = http://datetime.now(IL_TZ)
    if now_il.weekday() >= 5:
        return False
    total_minutes = now_il.hour _ 60 + now_il.minute
    open_min = 16_60 + 30
    close_min = 23_60
    return open_min <= total_minutes < close_min
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        http://requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except:
        pass
http://st.set_page_config(layout="wide", page_title="טרמינל NASDAQ 100 TURBO", page_icon="🚀")
http://st.markdown("""
<style>
.stApp{background:#111315;color:#f5f5f5}
.block-container{max-width:98%!important; padding:1rem!important;}
.stButton>button{background:#1e2228!important; color:#fff!important; border:1px solid #00ff88!important; border-radius:12px!important; font-weight:bold!important; height:3em!important;}
.stButton>button:hover{background:#00ff88!important; color:#000!important;}
</style>
""", unsafe_allow_html=True)
if 'focus' not in http://st.session_state:
    http://st.session_state.focus="NVDA"
if 'scan' not in http://st.session_state:
    http://st.session_state.scan=pd.DataFrame()
if 'is_scanning' not in http://st.session_state:
    http://st.session_state.is_scanning=False
tf = http://st.session_state.get('tf', 'יומי')
is_live = http://st.sidebar.checkbox("🔴 לייב פעיל", value=True)
enable_tg = http://st.sidebar.checkbox("📲 שלח לטלגרם @omer_turbo72_bot", value=True)
now_il_str = http://datetime.now(IL_TZ).strftime('%H:%M:%S %d/%m/%Y')
market_status = "🟢 שוק פתוח" if is_market_open_il() else "🔴 שוק סגור"
http://st.sidebar.info(f"{market_status}\n\nשעון ישראל: {now_il_str}\n\nBOT: @omer_turbo72_bot\nCHAT ID: {CHAT_ID}")
if is_live and not http://st.session_state.is_scanning:
    sec = 10 if tf=="1דק לייב" else 15 if tf=="5דק לייב" else 60
    st_autorefresh(interval=sec_1000, key="smart_live")
def winrate(ticker):
    try:
        d=yf.download(ticker, period="2y", interval="1d", progress=False, auto_adjust=True)
        if d is None or len(d)<60: return 50
        if isinstance(d.columns, http://pd.MultiIndex): http://d.columns=d.columns.get_level_values(0)
        d['upper']=ta.volatility.bollinger_hband(d['Close'],20,2)
        wins=total=0
        for i in range(20, len(d)-5):
            if d['Close'].iloc > d['upper'].iloc:
                total+=1
                if d['Close'].iloc[i+5] > d['Close'].iloc: wins+=1
        return int(wins/total_100) if total>10 else 50
    except: return 50
def make_chart(ticker, tf):
    try:
        p_map={"1דק לייב":("1d","1m"), "5דק לייב":("5d","5m"), "יומי":("3mo","1d")}
        per, inter = p_map
        df=yf.download(ticker, period=per, interval=inter, progress=False, auto_adjust=True)
        if df is None or len(df)<20: return None, 0, "", ""
        if isinstance(df.columns, http://pd.MultiIndex): http://df.columns=df.columns.get_level_values(0)
        df['upper']=ta.volatility.bollinger_hband(df['Close'],20,2)
        df['lower']=ta.volatility.bollinger_lband(df['Close'],20,2)
        df['rsi']=ta.momentum.rsi(df['Close'],14)
        p=float(df['Close'].iloc[-1])
        wr=winrate(ticker)
        try:
            if http://df.index.tz is None: idx_il = http://df.index.tz_localize(NY_TZ).tz_convert(IL_TZ)
            else: idx_il = http://df.index.tz_convert(IL_TZ)
            last_candle_str = idx_il[-1].strftime("%d/%m %H:%M")
        except: last_candle_str = http://df.index[-1].strftime("%d/%m %H:%M")
        now_il_display = http://datetime.now(IL_TZ).strftime("%H:%M:%S %d/%m/%Y")
        live_time = f"{now_il_display} | נר אחרון: {last_candle_str}"
        fig=make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8,0.2], vertical_spacing=0.08)
        http://fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#00ff88', decreasing_line_color='#ff3344', name="נרות"), row=1,col=1)
        http://fig.add_trace(go.Scatter(x=df.index, y=df['upper'], line=dict(color='#00d4ff', width=2, dash='dash'), name='Upper BB'), row=1,col=1)
        http://fig.add_trace(go.Scatter(x=df.index, y=df['lower'], line=dict(color='#00d4ff', width=2, dash='dash'), fill='tonexty', fillcolor='rgba(255,221,0,0.12)', name='Lower BB'), row=1,col=1)
        http://fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], line=dict(color='#ff00ff', width=2), name='RSI'), row=2,col=1)
        http://fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
        http://fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)
        http://fig.update_layout(height=700, template="plotly_dark", paper_bgcolor="#111315", plot_bgcolor="#1a1d22", xaxis_rangeslider_visible=False, font=dict(color="#ffffff", size=13), title=dict(text=f"{ticker} ${p:.2f} | {now_il_display} | {tf} | הצלחה {wr}% | {market_status} | TURBO BOT", font=dict(size=14, color="#00ff88")), margin=dict(l=10,r=10,t=60,b=10))
        return fig, wr, last_candle_str, live_time
    except Exception as e:
        http://st.error(f"שגיאת גרף: {e}")
        return None, 0, "", ""
def run_scan(n, mode, tf):
    http://st.session_state.is_scanning=True
    if mode == "NASDAQ 100 TURBO 🚀":
        syms = NASDAQ_100
        per, inter = "2d", "5m"
    else:
        per, inter = "2d", "1m"
        try:
            syms=pd.read_csv("https://raw.githubusercontent.com/datasets/nasdaq-listings/main/data/nasdaq-listed.csv")['Symbol'].dropna().tolist()
            syms=[x for x in syms if http://x.isalpha() and 1<len(x)<=4][:n]
        except:
            syms=["NVDA","TSLA","PLTR","SOFI","AMD","META","COIN","MARA","SMCI","MRVL","AAPL","MSFT","GOOGL","AMZN","NFLX"]_350
            syms=syms[:n]
    res=[]
    prog=st.progress(0)
    status_text=st.empty()
    for i,sym in enumerate(syms[:n]):
        status_text.text(f"סורק {i+1}/{len(syms[:n])} : {sym} | {datetime.now(IL_TZ).strftime('%H:%M:%S')} | {mode}")
        try:
            d=yf.download(sym, period=per, interval=inter, progress=False, auto_adjust=True)
            if d is None or len(d)<30: continue
            if isinstance(d.columns, http://pd.MultiIndex): http://d.columns=d.columns.get_level_values(0)
            d['upper']=ta.volatility.bollinger_hband(d['Close'],20,2)
            d['lower']=ta.volatility.bollinger_lband(d['Close'],20,2)
            d['rsi']=ta.momentum.rsi(d['Close'],14)
            d['vol_ma']=d['Volume'].rolling(20).mean()
            p=float(d['Close'].iloc[-1])
            u=float(d['upper'].iloc[-1])
            l=float(d['lower'].iloc[-1])
            r=float(d['rsi'].iloc[-1])
            v=float(d['Volume'].iloc[-1])
            vm=float(d['vol_ma'].iloc[-1]) if http://pd.notna(d['vol_ma'].iloc[-1]) else v
            change=(p-float(d['Close'].iloc[-2]))/float(d['Close'].iloc[-2])_100 if len(d)>=2 else 0
            try:
                if http://d.index.tz is None: idx_il = http://d.index.tz_localize(NY_TZ).tz_convert(IL_TZ)
                else: idx_il = http://d.index.tz_convert(IL_TZ)
                breakout_time = idx_il[-1].strftime("%d/%m %H:%M:%S")
            except: breakout_time = http://d.index[-1].strftime("%d/%m %H:%M:%S")
            is_break=p>u or p<l
            is_hot=change>=5 and v>vm_2.5
            is_extreme=is_break and v>vm_1.8 and ((p>u and r>68) or (p<l and r<32))
            if mode=="NASDAQ 100 TURBO 🚀":
                if not (p>l and float(d['Close'].iloc[-2]) < float(d['lower'].iloc[-2]) and v>vm_1.3):
                    if not (p>u or p<l): continue
            else:
                if mode=="קיצוני 🚨" and not is_extreme: continue
                if mode=="רותחות 🔥" and not is_hot: continue
                if mode=="בולינגר" and not is_break: continue
                if not (is_break or is_hot): continue
            wr=winrate(sym)
            sig="TURBO 🚀" if mode=="NASDAQ 100 TURBO 🚀" else "קיצוני 🚨" if is_extreme else f"רותחת 🔥 {change:.1f}%" if is_hot else "LONG 🚀" if p>u else "SHORT 🔻"
            dec="✅ קנה" if wr>=65 and "SHORT" not in sig else "❌ אל תקנה" if "SHORT" in sig else "⚠️ זהירות"
            http://res.append([sym, p, breakout_time, sig, f"{wr}%", dec, round(p_1.08,2), round(p_0.95,2)])
            if enable_tg and (is_extreme or mode=="NASDAQ 100 TURBO 🚀" and is_break):
                send_telegram(f"🚀 {sym} {sig} ${p:.2f} | RSI {r:.0f} | Vol x{v/vm:.1f} | {breakout_time} | {mode}")
        except: pass
        http://prog.progress((i+1)/len(syms[:n]))
    http://st.session_state.scan=pd.DataFrame(res, columns=["טיקר","מחיר לייב","זמן פריצה (IL)","סוג","אחוז הצלחה","החלטה","יעד","סטופ"])
    http://prog.empty()
    status_text.empty()
    http://st.session_state.is_scanning=False
    http://st.success(f"סריקה {mode} הושלמה! נמצאו {len(res)} | {datetime.now(IL_TZ).strftime('%H:%M:%S')}")
c1, c2, c3 = http://st.columns()
with c1:
    q=st.text_input("🔎 חיפוש טיקר", value=st.session_state.focus, label_visibility="collapsed", placeholder="NVDA, TSLA...")
with c2:
    if http://st.button("פתח גרף", use_container_width=True, type="primary"):
        http://st.session_state.focus=q.upper().strip()
        http://st.rerun()
with c3:
    tf_select=st.radio("טווח גרף", ["1דק לייב","5דק לייב","יומי"], index=1, horizontal=True, label_visibility="collapsed")
    http://st.session_state.tf=tf_select
http://st.divider()
left,right=st.columns()
with right:
    http://st.markdown("### ⚙️ סריקה")
    http://st.caption(f"שעון ישראל: {datetime.now(IL_TZ).strftime('%H:%M:%S')} | {market_status}")
    http://st.caption(f"BOT: @omer_turbo72_bot")
    mode=st.selectbox("סוג סינון", ["NASDAQ 100 TURBO 🚀","הכל","קיצוני 🚨","רותחות 🔥","בולינגר"])
    colA, colB = http://st.columns(2)
    with colA:
        if http://st.button("SCAN 100 TURBO", use_container_width=True, type="primary"):
            run_scan(100, mode, http://st.session_state.get('tf','יומי'))
        if http://st.button("SCAN 100", use_container_width=True):
            run_scan(100, mode, http://st.session_state.get('tf','יומי'))
    with colB:
        if http://st.button("SCAN 500", use_container_width=True):
            run_scan(500, mode, http://st.session_state.get('tf','יומי'))
        if http://st.button("SCAN 3500 🚀", use_container_width=True):
            run_scan(3500, mode, http://st.session_state.get('tf','יומי'))
    if not http://st.session_state.scan.empty:
        http://st.dataframe(st.session_state.scan.sort_values("אחוז הצלחה", ascending=False), use_container_width=True, height=450)
        sel=st.selectbox("פתח מהטבלה", http://st.session_state.scan["טיקר"].tolist())
        if http://st.button("הצג מטבלה", use_container_width=True):
            http://st.session_state.focus=sel
            http://st.rerun()
with left:
    fig, wr, bt, live_time = make_chart(st.session_state.focus, http://st.session_state.get('tf','יומי'))
    if fig:
        if wr>=65: http://st.success(f"🔴 לייב: {st.session_state.focus} | {live_time} | הצלחה {wr}% | ✅ קנה | TURBO")
        else: http://st.warning(f"🔴 לייב: {st.session_state.focus} | {live_time} | הצלחה {wr}% | {market_status}")
        http://st.plotly_chart(fig, use_container_width=True, config={'scrollZoom':True, 'displayModeBar':True, 'modeBarButtonsToAdd':['drawline','drawrect','eraseshape']})
    else:
        http://st.error("לא נמצא גרף - בדוק טיקר")[i][tf][2][1][3]
