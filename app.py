import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
st.set_page_config(page_title="NASDAQ Monster", layout="wide")
st.title("👹 מפלצת נאסדק - פריצות בולינג'ר עם גרף")
@st.cache_data(ttl=86400)
def get_nasdaq():
    url = "https://raw.githubusercontent.com/datasets/nasdaq-listings/main/data/nasdaq-listed.csv"
    df = pd.read_csv(url)
    t = df['Symbol'].dropna().tolist()
    return [x for x in t if x.isalpha() and len(x) <= 5][:3500]
def analyze_success(ticker):
    try:
        data = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        if len(data) < 60: return 0,0,0
        close = data['Close']
        upper = ta.volatility.bollinger_hband(close, 20, 2)
        lower = ta.volatility.bollinger_lband(close, 20, 2)
        wins=total=profit=0
        for i in range(25, len(data)-5):
            p=float(close.iloc[i]); u=float(upper.iloc[i]); l=float(lower.iloc[i])
            if p>u or p<l:
                total+=1
                future=float(close.iloc[i+5])
                if (p>u and future>p) or (p<l and future<p):
                    wins+=1
                    profit+=abs(future-p)/p*100
        return round(wins/total*100,1) if total else 0, round(profit/total,2) if total else 0, total
    except: return 0,0,0
def plot_bollinger(ticker):
    data = yf.download(ticker, period="3mo", interval="1d", progress=False, auto_adjust=True)
    data['upper'] = ta.volatility.bollinger_hband(data['Close'], 20, 2)
    data['lower'] = ta.volatility.bollinger_lband(data['Close'], 20, 2)
    data['middle'] = ta.volatility.bollinger_mavg(data['Close'], 20)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Price"))
    fig.add_trace(go.Scatter(x=data.index, y=data['upper'], name="Upper", line=dict(dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=data['lower'], name="Lower", line=dict(dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=data['middle'], name="Middle"))
    fig.update_layout(height=350, margin=dict(l=0,r=0,t=30,b=0), title=f"{ticker} - Bollinger 20,2")
    st.plotly_chart(fig, use_container_width=True)
if st.button("👹 סרוק 3500 מניות"):
    tickers = get_nasdaq()
    results=[]; prog=st.progress(0)
    for i,sym in enumerate(tickers):
        try:
            data=yf.download(sym, period="2mo", interval="1d", progress=False, auto_adjust=True)
            if len(data)<22: continue
            price=float(data['Close'].iloc[-1])
            upper=float(ta.volatility.bollinger_hband(data['Close'],20,2).iloc[-1])
            lower=float(ta.volatility.bollinger_lband(data['Close'],20,2).iloc[-1])
            if price>upper or price<lower:
                win_rate,avg_prof,total_b = analyze_success(sym)
                if win_rate>=55:
                    pct=abs(price-upper)/upper*100 if price>upper else abs(lower-price)/lower*100
                    direction="UP 🔥" if price>upper else "DOWN 💧"
                    results.append([sym,price,direction,f"{pct:.2f}%",f"{win_rate}%",f"{avg_prof}%",total_b])
        except: pass
        prog.progress((i+1)/len(tickers))
    if results:
        df=pd.DataFrame(results, columns=["Ticker","Price","Dir","Break%","Win%","Profit%","Count"])
        df_sorted = df.sort_values("Break%", ascending=False)
        st.dataframe(df_sorted, use_container_width=True)
        st.divider()
        st.subheader("📈 גרפים לפריצות החזקות")
        for ticker in df_sorted.head(10)["Ticker"]:
            plot_bollinger(ticker)
    else:
        st.warning("No breakouts")
