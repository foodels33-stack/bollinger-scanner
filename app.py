import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import http://plotly.graph_objects as go
from http://plotly.subplots import make_subplots
import requests
import pytz
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
IL_TZ = http://pytz.timezone("Asia/Jerusalem")
NY_TZ = http://pytz.timezone("America/New_York")
BOT_TOKEN = http://st.secrets.get("BOT_TOKEN", "8777322821:AAHOqH07iKcQONEfEH3Zg-fhivMl1ctdyJ4")
CHAT_ID = http://st.secrets.get("CHAT_ID", "6649894327")
NASDAQ_100 = ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","AVGO","COST","TSLA","NFLX","AMD","TMUS","PEP","LIN","ADBE","CSCO","QCOM","INTU","AMGN","TXN","ISRG","BKNG","HON","AMAT","GILD","VRTX","PANW","ADP","MDLZ","ADI","REGN","LRCX","MU","KLAC","SNPS","CDNS","MELI","MAR","CTAS","ORLY","CSX","PYPL","MNST","FTNT","ADSK","DASH","NXPI","ABNB","PCAR","ROST","WDAY","KDP","MRVL","IDXX","CTSH","ODFL","FAST","CEG","CRWD","DDOG","TEAM","ZS","EXC","XEL","EA","BKR","GEHC","ON","TTD","WBD","BIIB","CHTR","MRNA","ILMN","LCID","ZM","RIVN","ARM","SMCI"]
def is_market_open_il():
    now_il = http://datetime.now(IL_TZ)
    if now_il.weekday() >= 5:
        return False
    total = now_il.hour_60+now_il.minute
    return (16_60+30) <= total < (23_60)
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        http://requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except:
        pass
http://st.set_page_config(layout="wide", page_title="NASDAQ 100 TURBO LONG FULL", page_icon="🚀")
http://st.markdown("""
<style>
.stApp{background:#111315;color:#f5f5f5}
.block-container{max-width:98%!important;padding:1rem!important}
.stButton>button{background:#1e2228!important;color:#fff!important;border:1px solid #00ff88!important;border-radius:12px!important;font-weight:bold!important;height:3em!important}
.stButton>button:hover{background:#00ff88!important;color:#000!important}
.monster-on{background:#00ff88!important;color:#000!important;animation: pulse 1.5s infinite;}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(0,255,136,0.7)}70%{box-shadow:0 0 0 10px rgba(0,255,136,0)}100%{box-shadow:0 0 0 0 rgba(0,255,136,0)}}
</style>
""", unsafe_allow_html=True)
if 'focus' not in http://st.session_state:
    http://st.session_state.focus="NVDA"
if 'scan' not in http://st.session_state:
    http://st.session_state.scan=pd.DataFrame()
if 'is_scanning' not in http://st.session_state:
    http://st.session_state.is_scanning=False
if 'tf' not in http://st.session_state:
    http://st.session_state.tf="5דק לייב"
if 'auto_monster' not in http://st.session_state:
    http://st.session_state.auto_monster=False
if http://st.session_state.auto_monster:
    st_autorefresh(interval=30_1000, key="monster_auto")
is_live = http://st.sidebar.checkbox("🔴 לייב פעיל", value=True)
enable_tg = http://st.sidebar.checkbox("📲 שלח לטלגרם", value=True)
now_il_str = http://datetime.now(IL_TZ).strftime('%H:%M:%S %d/%m/%Y')
market_status = "🟢 שוק פתוח" if is_market_open_il() else "🔴 שוק סגור"
http://st.sidebar.info(f"{market_status}\nשעון: {now_il_str}\nBOT: @omer_turbo72_bot")
if is_live and not http://st.session_state.is_scanning and not http://st.session_state.auto_monster:
    sec = 10 if http://st.session_state.tf=="1דק לייב" else 15 if http://st.session_state.tf=="5דק לייב" else 60
    st_autorefresh(interval=sec_1000, key="smart_live")
def winrate(ticker):
    try:
        d=yf.download(ticker, period="2y", interval="1d", progress=False, auto_adjust=True)
        if d is None or len(d)<60:
            return 50
        if isinstance(d.columns, http://pd.MultiIndex):
            http://d.columns=d.columns.get_level_values(0)
        d['upper']=ta.volatility.bollinger_hband(d['Close'],20,2)
        wins=total=0
        for i in range(20, len(d)-5):
            if d['Low'].iloc > d['upper'].iloc:
                total+=1
                if d['Close'].iloc[i+5] > d['Close'].iloc:
                    wins+=1
        return int(wins/total_100) if total>10 else 50
    except:
        return 50
def make_chart(ticker, tf):
    try:
        pmap={"1דק לייב":("1d","1m"), "5דק לייב":("5d","5m"), "יומי":("3mo","1d")}
        per, inter = http://pmap.get(tf, ("5d","5m"))
        df=yf.download(ticker, period=per, interval=inter, progress=False, auto_adjust=True)
        if df is None or len(df)<20:
            return None, 0, "", ""
        if isinstance(df.columns, http://pd.MultiIndex):
            http://df.columns=df.columns.get_level_values(0)
        df['upper']=ta.volatility.bollinger_hband(df['Close'],20,2)
        df['lower']=ta.volatility.bollinger_lband(df['Close'],20,2)
        df['rsi']=ta.momentum.rsi(df['Close'],14)
        p=float(df['Close'].iloc[-1])
        wr=winrate(ticker)
        try:
            if http://df.index.tz is None:
                idx_il = http://df.index.tz_localize(NY_TZ).tz_convert(IL_TZ)
            else:
                idx_il = http://df.index.tz_convert(IL_TZ)
            last_str = idx_il[-1].strftime("%d/%m %H:%M")
        except:
            last_str = http://df.index[-1].strftime("%d/%m %H:%M")
        now_disp = http://datetime.now(IL_TZ).strftime("%H:%M:%S %d/%m/%Y")
        live_time = f"{now_disp} | נר אחרון: {last_str}"
        fig=make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8,0.2], vertical_spacing=0.08)
        http://fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#00ff88', decreasing_line_color='#ff3344', name="נרות"), row=1,col=1)
        http://fig.add_trace(go.Scatter(x=df.index, y=df['upper'], line=dict(color='#00d4ff', width=2, dash='dash'), name='Upper'), row=1,col=1)
        http://fig.add_trace(go.Scatter(x=df.index, y=df['lower'], line=dict(color='#00d4ff', width=2, dash='dash'), fill='tonexty', fillcolor='rgba(255,221,0,0.12)', name='Lower'), row=1,col=1)
        http://fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], line=dict(color='#ff00ff', width=2), name='RSI'), row=2,col=1)
        http://fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
        http://fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)
        http://fig.update_layout(height=700, template="plotly_dark", paper_bgcolor="#111315", plot_bgcolor="#1a1d22", xaxis_rangeslider_visible=False, font=dict(color="#ffffff", size=13), title=dict(text=f"{ticker} ${p:.2f} | {now_disp} | {tf} | {wr}% | LONG FULL BREAKOUT 5m | {market_status}", font=dict(size=14, color="#00ff88")), margin=dict(l=10,r=10,t=60,b=10))
        return fig, wr, last_str, live_time
    except Exception as e:
        http://st.error(f"שגיאת גרף: {e}")
        return None, 0, "", ""
def run_scan(n, mode, tf):
    http://st.session_state.is_scanning=True
    if mode == "NASDAQ 100 TURBO 🚀":
        syms = NASDAQ_100
    else:
        try:
            syms=pd.read_csv("https://raw.githubusercontent.com/datasets/nasdaq-listings/main/data/nasdaq-listed.csv")['Symbol'].dropna().tolist()
            syms=[x for x in syms if http://x.isalpha() and 1<len(x)<=5][:n]
        except:
            syms=NASDAQ_100_20
            syms=syms[:n]
    res=[]
    prog=st.progress(0)
    status=st.empty()
    for i,sym in enumerate(syms[:n]):
        http://status.text(f"סורק LONG FULL {i+1}/{len(syms[:n])} : {sym} | {datetime.now(IL_TZ).strftime('%H:%M:%S')} | {mode}")
        try:
            d=yf.download(sym, period="2d", interval="5m", progress=False, auto_adjust=True)
            if d is None or len(d)<30:
                continue
            if isinstance(d.columns, http://pd.MultiIndex):
                http://d.columns=d.columns.get_level_values(0)
            d['upper']=ta.volatility.bollinger_hband(d['Close'],20,2)
            d['lower']=ta.volatility.bollinger_lband(d['Close'],20,2)
            d['rsi']=ta.momentum.rsi(d['Close'],14)
            d['vol_ma']=d['Volume'].rolling(20).mean()
            p=float(d['Close'].iloc[-1])
            o=float(d['Open'].iloc[-1])
            l=float(d['Low'].iloc[-1])
            u=float(d['upper'].iloc[-1])
            r=float(d['rsi'].iloc[-1])
            v=float(d['Volume'].iloc[-1])
            vm=float(d['vol_ma'].iloc[-1]) if http://pd.notna(d['vol_ma'].iloc[-1]) else v
            change=(p-float(d['Close'].iloc[-2]))/float(d['Close'].iloc[-2])_100 if len(d)>=2 else 0
            try:
                if http://d.index.tz is None:
                    idx_il = http://d.index.tz_localize(NY_TZ).tz_convert(IL_TZ)
                else:
                    idx_il = http://d.index.tz_convert(IL_TZ)
                btime = idx_il[-1].strftime("%d/%m %H:%M:%S")
            except:
                btime = http://d.index[-1].strftime("%d/%m %H:%M:%S")
            is_full_break = l > u
            is_body_break = min(o,p) > u
            is_break = is_full_break and is_body_break
            is_hot=change>=5 and v>vm_2.5 and p>u
            is_extreme=is_break and v>vm_1.8 and r>68
            if mode=="NASDAQ 100 TURBO 🚀":
                if not is_break:
                    continue
            else:
                if mode=="קיצוני 🚨" and not is_extreme:
                    continue
                if mode=="רותחות 🔥" and not is_hot:
                    continue
                if mode=="בולינגר" and not is_break:
                    continue
                if not (is_break or is_hot):
                    continue
            wr=winrate(sym)
            sig="TURBO LONG 🚀 פריצה מלאה גוף+זנב מעל" if is_full_break else f"LONG רותחת 🔥 {change:.1f}%"
            dec="✅ קנה" if wr>=65 else "⚠️ זהירות"
            http://res.append([sym, p, btime, sig, f"{wr}%", dec, round(p_1.08,2), round(p_0.95,2)])
            if enable_tg and (is_extreme or is_break or is_hot):
                send_telegram(f"🚀 LONG ONLY FULL BREAKOUT {sym} {sig} ${p:.2f} | LOW {l:.2f} > Upper {u:.2f} | גוף+זנב בחוץ | RSI {r:.0f} | Vol x{v/vm:.1f} | {btime}")
        except:
            pass
        http://prog.progress((i+1)/len(syms[:n]))
    http://st.session_state.scan=pd.DataFrame(res, columns=["טיקר","מחיר לייב","זמן פריצה (IL)","סוג","אחוז הצלחה","החלטה","יעד","סטופ"])
    http://prog.empty()
    http://status.empty()
    http://st.session_state.is_scanning=False
    http://st.success(f"סריקה LONG FULL BREAKOUT {mode} הושלמה! נמצאו {len(res)} | {datetime.now(IL_TZ).strftime('%H:%M:%S')}")
if http://st.session_state.auto_monster:
    if is_market_open_il():
        http://st.toast(f"מפלצת סורקת אוטומטית... {datetime.now(IL_TZ).strftime('%H:%M:%S')}")
        run_scan(100, "NASDAQ 100 TURBO 🚀", http://st.session_state.tf)
    else:
        http://st.warning(f"מפלצת דולקת אבל שוק סגור - ממתין לפתיחה... {datetime.now(IL_TZ).strftime('%H:%M:%S')}")
c1,c2,c3=st.columns(3)
with c1:
    q=st.text_input("🔎 חיפוש טיקר", value=st.session_state.focus, label_visibility="collapsed", placeholder="NVDA, TSLA...")
with c2:
    if http://st.button("פתח גרף", use_container_width=True, type="primary"):
        http://st.session_state.focus=q.upper().strip()
        http://st.rerun()
with c3:
    tf_sel=st.radio("טווח", ["1דק לייב","5דק לייב","יומי"], index=1, horizontal=True, label_visibility="collapsed")
    http://st.session_state.tf=tf_sel
http://st.divider()
left,right=st.columns()
with right:
    http://st.markdown("### ⚙️ סריקה LONG פריצה מלאה 5דק")
    http://st.caption(f"{market_status} | {datetime.now(IL_TZ).strftime('%H:%M:%S')} | BOT: @omer_turbo72_bot FULL BODY")
    if not http://st.session_state.auto_monster:
        if http://st.button("🔴 מפלצת כבויה - לחץ להפעלה כל 30 שניות", use_container_width=True, type="primary"):
            http://st.session_state.auto_monster = True
            http://st.rerun()
    else:
        if http://st.button("🟢 מפלצת פועלת - סורקת כל 30 שניות (לחץ לכיבוי)", use_container_width=True):
            http://st.session_state.auto_monster = False
            http://st.rerun()
        http://st.success("מפלצת רצה ברקע - אל תסגור את החלון הזה")
    http://st.divider()
    mode=st.selectbox("סוג סינון", ["NASDAQ 100 TURBO 🚀","הכל","קיצוני 🚨","רותחות 🔥","בולינגר"])
    colA,colB=st.columns(2)
    with colA:
        if http://st.button("SCAN 100 TURBO LONG", use_container_width=True, type="primary"):
            run_scan(100, mode, http://st.session_state.tf)
        if http://st.button("SCAN 100", use_container_width=True):
            run_scan(100, mode, http://st.session_state.tf)
    with colB:
        if http://st.button("SCAN 500", use_container_width=True):
            run_scan(500, mode, http://st.session_state.tf)
        if http://st.button("SCAN 3500 🚀", use_container_width=True):
            run_scan(3500, mode, http://st.session_state.tf)
    if not http://st.session_state.scan.empty:
        http://st.dataframe(st.session_state.scan.sort_values("אחוז הצלחה", ascending=False), use_container_width=True, height=450)
        sel=st.selectbox("פתח מהטבלה", http://st.session_state.scan["טיקר"].tolist())
        if http://st.button("הצג מטבלה", use_container_width=True):
            http://st.session_state.focus=sel
            http://st.rerun()
with left:
    fig, wr, bt, live_time = make_chart(st.session_state.focus, http://st.session_state.tf)
    if fig:
        if wr>=65:
            http://st.success(f"🔴 לייב LONG FULL: {st.session_state.focus} | {live_time} | הצלחה {wr}% | ✅ פריצה מלאה גוף+זנב מעל | 5דק")
        else:
            http://st.warning(f"🔴 לייב: {st.session_state.focus} | {live_time} | הצלחה {wr}% | {market_status} LONG ONLY FULL")
        http://st.plotly_chart(fig, use_container_width=True, config={'scrollZoom':True, 'displayModeBar':True, 'modeBarButtonsToAdd':['drawline','drawrect','eraseshape']})
    else:
        http://st.error("לא נמצא גרף - בדוק טיקר")[i][2][1]
