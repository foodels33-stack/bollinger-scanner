import streamlit as st, yfinance as yf, pandas as pd, ta, plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
st.set_page_config(layout="wide", page_title="PRO TERMINAL")
st.markdown("<style>.stApp{background-color:#000} [data-testid='stSidebar']{background-color:#0a0a0a}</style>", unsafe_allow_html=True)
if 'focus' not in st.session_state: st.session_state.focus="NVDA"
if 'last_refresh' not in st.session_state: st.session_state.last_refresh=time.time()
if time.time()-st.session_state.last_refresh>60:
    st.session_state.last_refresh=time.time(); st.rerun()
def make_chart(ticker, period="3mo"):
    df=yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
    if len(df)<20: return None
    df['upper']=ta.volatility.bollinger_hband(df['Close'],20,2)
    df['lower']=ta.volatility.bollinger_lband(df['Close'],20,2)
    df['middle']=ta.volatility.bollinger_mavg(df['Close'],20)
    df['rsi']=ta.momentum.rsi(df['Close'],14)
    df['vol_ma']=df['Volume'].rolling(20).mean()
    fig=make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6,0.2,0.2], vertical_spacing=0.02)
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['upper'], line=dict(color='#00bfff', width=1, dash='dash'), name="BB Up"), row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['lower'], line=dict(color='#00bfff', width=1, dash='dash'), name="BB Low", fill='tonexty', fillcolor='rgba(0,191,255,0.05)'), row=1,col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='gray', name="Vol"), row=2,col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['vol_ma'], line=dict(color='orange', width=1), name="Vol MA"), row=2,col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], line=dict(color='#ffaa00'), name="RSI"), row=3,col=1)
    fig.add_hline(y=70, line_color="red", line_dash="dash", row=3,col=1)
    fig.add_hline(y=30, line_color="green", line_dash="dash", row=3,col=1)
    fig.update_layout(height=700, template="plotly_dark", paper_bgcolor="black", plot_bgcolor="black", xaxis_rangeslider_visible=False, dragmode="pan", margin=dict(l=10,r=10,t=30,b=10), title=f"{ticker} - ${float(df['Close'].iloc[-1]):.2f}")
    fig.update_xaxes(showgrid=False); fig.update_yaxes(showgrid=False)
    return fig
cols=st.columns(8)
for i,sym in enumerate(["SPY","QQQ","NVDA","AAPL","TSLA","MSFT","META","BTC-USD"]):
    try:
        d=yf.download(sym, period="2d", progress=False, auto_adjust=True)['Close']
        p=float(d.iloc[-1]); ch=(p-float(d.iloc[-2]))/float(d.iloc[-2])*100
        cols[i].metric(sym, f"{p:.2f}", f"{ch:.2f}%")
    except: pass
left,right=st.columns([4,1])
with right:
    st.text_input("🔎 חפש (tesla / AAPL)", key="search")
    if st.session_state.search:
        try:
            s=yf.Search(st.session_state.search, max_results=1)
            sym=s.quotes[0]['symbol'] if s.quotes else st.session_state.search.upper()
            st.session_state.focus=sym
        except: st.session_state.focus=st.session_state.search.upper()
    st.divider()
    st.subheader("⭐ Watchlist")
    watch=["NVDA","AAPL","TSLA","PLTR","AMD","META","MSFT","GOOGL"]
    for w in watch:
        if st.button(w, use_container_width=True): st.session_state.focus=w
    st.divider()
    st.subheader("👹 Bollinger Scanner")
    size=st.select_slider("Size", [50,500,1000,3500], value=500)
    if st.button(f"SCAN {size}", type="primary", use_container_width=True):
        lst=[x for x in pd.read_csv("https://raw.githubusercontent.com/datasets/nasdaq-listings/main/data/nasdaq-listed.csv")['Symbol'].dropna().tolist() if x.isalpha() and len(x)<=4][:size]
        res=[]; prog=st.progress(0)
        for idx,sym in enumerate(lst):
            try:
                d=yf.download(sym, period="1mo", interval="1d", progress=False, auto_adjust=True)
                if len(d)<20: continue
                p=float(d['Close'].iloc[-1]); u=float(ta.volatility.bollinger_hband(d['Close'],20,2).iloc[-1]); l=float(ta.volatility.bollinger_lband(d['Close'],20,2).iloc[-1])
                dist=min(abs(p-u)/u, abs(p-l)/l)*100
                if p>u or p<l or dist<1.0:
                    sig="LONG 🚀" if p>u else "SHORT 🔻" if p<l else "CLOSE"
                    res.append([sym, round(p,2), sig, round(dist,2)])
            except: pass
            prog.progress((idx+1)/len(lst))
        st.session_state.scan=pd.DataFrame(res, columns=["Ticker","Price","Signal","Dist"])
        prog.empty()
    if 'scan' in st.session_state and not st.session_state.scan.empty:
        st.dataframe(st.session_state.scan.sort_values("Dist"), use_container_width=True)
        sel=st.selectbox("Open chart", st.session_state.scan['Ticker'].tolist())
        if sel: st.session_state.focus=sel
with left:
    fig=make_chart(st.session_state.focus, "3mo")
    if fig:
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True, 'modeBarButtonsToAdd': ['drawline','drawrect','eraseshape']})
    if 'scan' in st.session_state and not st.session_state.scan.empty:
        c1,c2=st.columns(2)
        for i,t in enumerate(st.session_state.scan.head(4)['Ticker']):
            with (c1 if i%2==0 else c2):
                f=make_chart(t, "3mo")
                if f: st.plotly_chart(f, use_container_width=True)
