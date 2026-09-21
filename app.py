import streamlit as st
import ccxt
import pandas as pd
import ta

st.set_page_config(page_title="Bollinger Breakout", layout="wide")
st.title("🎯 סורק פריצות בולינג'ר - LIVE")

@st.cache_data(ttl=60)
def scan():
    ex = ccxt.binance()
    tickers = ex.fetch_tickers()
    top = sorted(tickers.items(), key=lambda x: x[1]['quoteVolume'] or 0, reverse=True)[:80]
    res=[]
    for sym, _ in top:
        if '/USDT' not in sym: continue
        try:
            ohlcv = ex.fetch_ohlcv(sym, '1h', limit=40)
            df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
            uh = ta.volatility.bollinger_hband(df['c'], 20, 2).iloc[-1]
            ul = ta.volatility.bollinger_lband(df['c'], 20, 2).iloc[-1]
            price = df['c'].iloc[-1]
            if price > uh: res.append([sym, price, "פריצה למעלה 🔥"])
            if price < ul: res.append([sym, price, "פריצה למטה 💧"])
        except: pass
    return pd.DataFrame(res, columns=["סימבול","מחיר","סוג"])

if st.button("🚀 סרוק עכשיו"):
    with st.spinner("סורק 80 מטבעות..."):
        d = scan()
        if d.empty: st.warning("אין פריצות כרגע")
        else:
            st.success(f"נמצאו {len(d)} פריצות")
            st.dataframe(d, use_container_width=True)
