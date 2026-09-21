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
BOT_TOKEN = http://st.secrets.get("BOT_TOKEN", "8777322821:AAHOqH07iKcQONEfEH3Zg-fhivMl1ctdyJ4")
CHAT_ID = http://st.secrets.get("CHAT_ID", "6649894327")
NASDAQ_100 = ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","AVGO","COST","TSLA","NFLX","AMD","TMUS","PEP","LIN","ADBE","CSCO","QCOM","INTU","AMGN","TXN","ISRG","BKNG","HON","AMAT","GILD","VRTX","PANW","ADP","MDLZ","ADI","REGN","LRCX","MU","KLAC","SNPS","CDNS","MELI","MAR","CTAS","ORLY","CSX","PYPL","MNST","FTNT","ADSK","DASH","NXPI","ABNB","PCAR","ROST","WDAY","KDP","MRVL","IDXX","CTSH","ODFL","FAST","CEG","CRWD","DDOG","TEAM","ZS","EXC","XEL","EA","BKR","GEHC","ON","TTD","WBD","BIIB","CHTR","MRNA","ILMN","LCID","ZM","RIVN","ARM","SMCI"]
def is_market_open_il():
    now_il = http://datetime.now(IL_TZ)
    if now_il.weekday() >= 5: return False
    return (16_60+30) <= now_il.hour_60+now_il.minute < (23_60)
def send_telegram(msg):
    try: http://requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHAT_ID,"text":msg,"parse_mode":"Markdown"}, timeout=5)
    except: pass
http://st.set_page_config(layout="wide", page_title="MONSTER FULL", page_icon="🚀")
if 'focus' not in http://st.session_state: http://st.session_state.focus="NVDA"
if 'scan' not in http://st.session_state: http://st.session_state.scan=pd.DataFrame()
if 'is_scanning' not in http://st.session_state: http://st.session_state.is_scanning=False
if 'tf' not in http://st.session_state: http://st.session_state.tf="5דק לייב"
if 'auto_monster' not in http://st.session_state: http://st.session_state.auto_monster=False
if http://st.session_state.auto_monster: st_autorefresh(interval=30_1000, key="monster_auto")
is_live = http://st.sidebar.checkbox("🔴 לייב פעיל", value=True)
enable_tg = http://st.sidebar.checkbox("📲 שלח לטלגרם", value=True)
http://st.sidebar.write("🟢 שוק פתוח" if is_market_open_il() else "🔴 שוק סגור")
if is_live and not http://st.session_state.is_scanning and not http://st.session_state.auto_monster:
    sec = 10 if http://st.session_state.tf=="1דק לייב" else 15 if http://st.session_state.tf=="5דק לייב" else 60
    st_autorefresh(interval=sec_1000, key="smart_live")
def winrate(ticker):
    try:
        d=yf.download(ticker, period="2y", interval="1d", progress=False, auto_adjust=True)
        if d is None or len(d)<60: return 50
        if isinstance(d.columns, http://pd.MultiIndex): http://d.columns=d.columns.get_level_values(0)
        d['upper']=ta.volatility.bollinger_hband(d['Close'],20,2)
        wins=total=0
        low_v = d['Low'].values
        up_v = d['upper'].values
        close_v = d['Close'].values
        for idx in range(20, len(d)-5):
            if low_v > up_v:
                total+=1
                if close_v[idx+5] > close_v: wins+=1
        return int(wins/total_100) if total>10 else 50
    except: return 50
def make_chart(ticker, tf):
    pmap={"1דק לייב":("1d","1m"), "5דק לייב":("5d","5m"), "יומי":("3mo","1d")}
    per, inter = http://pmap.get(tf, ("5d","5m"))
    df=yf.download(ticker, period=per, interval=inter, progress=False, auto_adjust=True)
    if df is None or len(df)<20: return None,0,0,0,0,""
    if isinstance(df.columns, http://pd.MultiIndex): http://df.columns=df.columns.get_level_values(0)
    df['upper']=ta.volatility.bollinger_hband(df['Close'],20,2)
    df['lower']=ta.volatility.bollinger_lband(df['Close'],20,2)
    df['rsi']=ta.momentum.rsi(df['Close'],14)
    price=float(df['Close'].iloc[-1])
    upper=float(df['upper'].iloc[-1])
    wr=winrate(ticker)
    entry=upper; stop=price_0.97; target=price_1.05
    bt_txt = f"WR {wr}% | כניסה {entry:.2f} | סטופ {stop:.2f} | יעד {target:.2f}"
    fig=make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8,0.2], vertical_spacing=0.08)
    http://fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#00ff88', decreasing_line_color='#ff3344'), row=1,col=1)
    http://fig.add_trace(go.Scatter(x=df.index, y=df['upper'], line=dict(color='#00d4ff', width=2, dash='dash')), row=1,col=1)
    http://fig.add_trace(go.Scatter(x=df.index, y=df['lower'], line=dict(color='#00d4ff', width=2, dash='dash'), fill='tonexty', fillcolor='rgba(255,221,0,0.12)'), row=1,col=1)
    http://fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], line=dict(color='#ff00ff', width=2)), row=2,col=1)
    http://fig.update_layout(height=750, template="plotly_dark", xaxis_rangeslider_visible=False, title=f"{ticker} ${price:.2f} | {wr}%")
    return fig, wr, entry, stop, target, bt_txt
def run_scan(n, mode, tf):
    http://st.session_state.is_scanning=True
    res=[]; prog=st.progress(0)
    for k,sym in enumerate(NASDAQ_100[:n]):
        try:
            d=yf.download(sym, period="2d", interval="5m", progress=False, auto_adjust=True)
            if d is None or len(d)<30: continue
            if isinstance(d.columns, http://pd.MultiIndex): http://d.columns=d.columns.get_level_values(0)
            d['upper']=ta.volatility.bollinger_hband(d['Close'],20,2)
            p=float(d['Close'].iloc[-1]); o=float(d['Open'].iloc[-1]); l=float(d['Low'].iloc[-1]); u=float(d['upper'].iloc[-1])
            if l > u and min(o,p) > u:
                wr=winrate(sym)
                entry=u; stop=p_0.97; tgt=p_1.05
                dec="✅ קנה" if wr>=65 else "⚠️"
                http://res.append([sym, f"${p:.2f}", f"{wr}%", f" ${entry:.2f}", f"${stop:.2f}", f"${tgt:.2f}", dec])
                if enable_tg and wr>=65: send_telegram(f"🚀 MONSTER {sym} ${p:.2f} WR {wr}%")
        except: pass
        http://prog.progress((k+1)/n)
    http://st.session_state.scan=pd.DataFrame(res, columns=["טיקר","מחיר","הצלחה","כניסה","סטופ","יעד","החלטה"])
    http://prog.empty(); http://st.session_state.is_scanning=False
if http://st.session_state.auto_monster and is_market_open_il(): run_scan(100, "TURBO", http://st.session_state.tf)
c1,c2,c3=st.columns(3)
with c1: q=st.text_input("טיקר", value=st.session_state.focus, label_visibility="collapsed")
with c2:
    if http://st.button("פתח גרף", use_container_width=True, type="primary"):
        http://st.session_state.focus=q.upper().strip(); http://st.rerun()
with c3: http://st.session_state.tf=st.radio("טווח", ["1דק לייב","5דק לייב","יומי"], index=1, horizontal=True, label_visibility="collapsed")
left,right=st.columns(2)
with right:
    if not http://st.session_state.auto_monster:
        if http://st.button("🔴 מפלצת כבויה - הפעל ON", use_container_width=True, type="primary"):
            http://st.session_state.auto_monster=True; http://st.rerun()
    else:
        if http://st.button("🟢 מפלצת פועלת - כבה OFF", use_container_width=True):
            http://st.session_state.auto_monster=False; http://st.rerun()
    if http://st.button("SCAN 100 TURBO עכשיו", use_container_width=True): run_scan(100, "TURBO", http://st.session_state.tf)
    if not http://st.session_state.scan.empty: http://st.dataframe(st.session_state.scan, use_container_width=True, height=600)
with left:
    fig, wr, entry, stop, target, bt_txt = make_chart(st.session_state.focus, http://st.session_state.tf)
    if fig:
        http://st.plotly_chart(fig, use_container_width=True)
        http://st.code(bt_txt)
    else:
        http://st.error("לא נמצא גרף - בדוק טיקר")
