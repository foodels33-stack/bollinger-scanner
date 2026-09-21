import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import hmac, hashlib, base64, hashlib as hl
from urllib.parse import urlencode
import requests
from datetime import datetime

st.set_page_config(page_title="NASDAQ Zadarma", layout="wide")
st.title("👹 מפלצת נאסדק + Zadarma SMS")

ZADARMA_KEY = "092cdfccc45ef0db0479"
ZADARMA_SECRET = "5a414893704349011794"
ZADARMA_FROM = "972559662037"
ZADARMA_TO = st.sidebar.text_input("המספר שלך", value="9725")

def zadarma_send_sms(to_number, message):
    method = "/v1/sms/send/"
    params = {
        "number": to_number.replace("+","").replace(" ",""),
        "message": message,
        "caller_id": ZADARMA_FROM
    }
    sorted_params = sorted(params.items())
    query_string = urlencode(sorted_params)
    md5_qs = hl.md5(query_string.encode()).hexdigest()
    sign_string = method + query_string + md5_qs
    signature = base64.b64encode(
        hmac.new(ZADARMA_SECRET.encode(), sign_string.encode(), hashlib.sha1).digest()
    ).decode()
    headers = {"Authorization": f"{ZADARMA_KEY}:{signature}"}
    r = requests.post(f"https://api.zadarma.com{method}", data=params, headers=headers, timeout=10)
    return r.json()

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

if st.sidebar.button("שלח SMS בדיקה"):
    res = zadarma_send_sms(ZADARMA_TO, "מפלצת נאסדק מחוברת!")
    st.sidebar.json(res)

if st.button("סרוק 3500 מניות + שלח SMS"):
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
                    direction="UP" if price>upper else "DOWN"
                    results.append([sym,price,direction,f"{pct:.2f}%",f"{win_rate}%",f"{avg_prof}%"])
        except: pass
        prog.progress((i+1)/len(tickers))
    if results:
        df=pd.DataFrame(results, columns=["Ticker","Price","Dir","Break%","Win%","Profit%"])
        st.dataframe(df.sort_values("Break%", ascending=False), use_container_width=True)
        top3 = ", ".join(df['Ticker'].head(3).tolist())
        msg = f"{len(df)} breakouts! TOP: {top3} {datetime.now().strftime('%H:%M')}"
        sms_res = zadarma_send_sms(ZADARMA_TO, msg)
        st.success(f"SMS sent from {ZADARMA_FROM}")
        st.json(sms_res)
    else:
        st.warning("No breakouts")
