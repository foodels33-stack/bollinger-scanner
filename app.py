import streamlit as st, yfinance as yf, pandas as pd, ta, plotly.graph_objects as go
from plotly.subplots import make_subplots
st.set_page_config(layout="wide", page_title="PRO TERMINAL")
st.markdown("<style>.stApp{background:#000}</style>", unsafe_allow_html=True)
if 'focus' not in st.session_state: st.session_state.focus="NVDA"
def make_chart(ticker):
    try:
        df=yf.download(ticker, period="3mo", interval="1d", progress=False, auto_adjust=True)
        if df is None or len(df)<20: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        df['upper']=ta.volatility.bollinger_hband(df['Close'],20,2)
        df['lower']=ta.volatility.bollinger_lband(df['Close'],20,2)
        df['rsi']=ta.momentum.rsi(df['Close'],14)
        df['vol_ma']=df['Volume'].rolling(20).mean()
        fig=make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75,0.25], vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['upper'], line=dict(color='#00bfff', dash='dash'), name="BB"), row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['lower'], line=dict(color='#00bfff', dash='dash'), fill='tonexty', fillcolor='rgba(0,191,255,0.05)'), row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], line=dict(color='orange'), name="RSI"), row=2,col=1)
        fig.update_layout(height=600, template="plotly_dark", paper_bgcolor="black", plot_bgcolor="black", xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=30,b=10), title=f"{ticker} ${float(df['Close'].iloc[-1]):.2f}")
        fig.update_xaxes(showgrid=False); fig.update_yaxes(showgrid=False)
        return fig
    except Exception as e:
        st.error(f"Error {ticker}: {e}")
        return None
c1,c2,c3,c4=st.columns(4)
for col,sym in zip([c1,c2,c3,c4], ["SPY","QQQ","NVDA","BTC-USD"]):
    try:
        d=yf.download(sym, period="2d", progress=False, auto_adjust=True)
        if d is not None and len(d)>=2:
            if isinstance(d.columns, pd.MultiIndex): d.columns=d.columns.get_level_values(0)
            p=float(d['Close'].iloc[-1]); ch=(p-float(d['Close'].iloc[-2]))/float(d['Close'].iloc[-2])*100
            col.metric(sym, f"{p:.2f}", f"{ch:.2f}%")
    except: pass
left,right=st.columns([4,1])
with right:
    q=st.text_input("🔎 חפש טיקר", value="NVDA")
    if st.button("פתח גרף", use_container_width=True):
        st.session_state.focus=q.upper().strip()
    st.divider()
    st.write("⭐ Watchlist")
    for w in ["NVDA","AAPL","TSLA","PLTR","AMD","META","MSFT","GOOGL"]:
        if st.button(w, use_container_width=True, key=f"w_{w}"):
            st.session_state.focus=w
    st.divider()
    if st.button("SCAN 50 - בדיקה", use_container_width=True, type="primary"):
        tickers=["NVDA","AAPL","TSLA","PLTR","AMD","META","MSFT","GOOGL","AMZN","NFLX","SPY","QQQ"]*4
        res=[]
        for sym in tickers[:50]:
            try:
                d=yf.download(sym, period="1mo", progress=False, auto_adjust=True)
                if d is None or len(d)<20: continue
                if isinstance(d.columns, pd.MultiIndex): d.columns=d.columns.get_level_values(0)
                p=float(d['Close'].iloc[-1]); u=float(ta.volatility.bollinger_hband(d['Close'],20,2).iloc[-1]); l=float(ta.volatility.bollinger_lband(d['Close'],20,2).iloc[-1])
                if p>u or p<l:
                    res.append([sym, p, "LONG" if p>u else "SHORT"])
            except: pass
        st.session_state.scan=pd.DataFrame(res, columns=["Ticker","Price","Signal"])
        st.dataframe(st.session_state.scan, use_container_width=True)
with left:
    st.subheader(f"גרף: {st.session_state.focus}")
    fig=make_chart(st.session_state.focus)
    if fig:
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom':True, 'displayModeBar':True, 'modeBarButtonsToAdd':['drawline','drawrect','eraseshape']})
    else:
        st.warning("טוען...")
