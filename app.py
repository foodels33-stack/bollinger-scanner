import streamlit as st
import ccxt
import pandas as pd
import ta

st.set_page_config(page_title="Bollinger Breakout", layout="wide")
st.title("🎯 סורק פריצות בולינג'ר - LIVE")

def scan():
    ex = ccxt.okx()
    res = []
    symbols = ['BTC/USDT','ETH/USDT','SOL/USDT','BNB/USDT','XRP/USDT','DOGE/USDT','ADA/USDT','AVAX/USDT','SHIB/USDT','DOT/USDT','LINK/USDT','LTC/USDT','TRX/USDT','MATIC/USDT','UNI/USDT','PEPE/USDT','ETC/USDT','FIL/USDT','NEAR/USDT','APT/USDT']
    for sym in symbols:
        try:
            ohlcv = ex.fetch_ohlcv(sym, '1h', limit=40)
            df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
            upper = ta.volatility.bollinger_hband(df['c'], 20, 2).iloc[-1]
            lower = ta.volatility.bollinger_lband(df['c'], 20, 2).iloc[-1]
            price = df['c'].iloc[-1]
            if price > upper:
                res.append([sym, round(price,4), "פריצה למעלה 🔥"])
            if price < lower:
                res.append([sym, round(price,4), "פריצה למטה 💧"])
        except:
            pass
    return pd.DataFrame(res, columns=["סימבול","מחיר","סוג"])

if st.button("🚀 סרוק עכשיו"):
    with st.spinner("סורק..."):
        d = scan()
        if d.empty:
            st.warning("אין פריצות כרגע, הכל בתוך הרצועות")
        else:
            st.success(f"נמצאו {len(d)} פריצות!")
            st.dataframe(d, use_container_width=True)
