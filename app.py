import yfinance as yf
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator

TELEGRAM_TOKEN = "AAFi4Sik...הטוקן החדש שלך"
PERIOD = "6mo"
INTERVAL = "1d"

def is_real_breakout(df):
    bb = BollingerBands(df["Close"], 20, 2.0)
    bb_l = bb.bollinger_lband()
    bb_m = bb.bollinger_mavg()
    rsi = RSIIndicator(df["Close"], 14).rsi()
    
    close = df["Close"].iloc[-1]
    high = df["High"].iloc[-1]
    prev_close = df["Close"].iloc[-2]
    prev_bb_l = bb_l.iloc[-2]
    curr_bb_l = bb_l.iloc[-1]
    curr_bb_m = bb_m.iloc[-1]
    curr_rsi = rsi.iloc[-1]
    vol = df["Volume"].iloc[-1]
    avg_vol = df["Volume"].rolling(20).mean().iloc[-1]
    
    cond = (
        close < curr_bb_l and
        high < curr_bb_l and
        prev_close > prev_bb_l and
        curr_rsi < 25 and
        vol > avg_vol * 1.5
    )
    return cond, curr_bb_m

def run_full_scan(tickers):
    alerts = []
    for t in tickers:
        try:
            df = yf.download(t, period=PERIOD, interval=INTERVAL, progress=False)
            if len(df) < 30: continue
            cond, tp = is_real_breakout(df)
            if cond:
                close = df["Close"].iloc[-1]
                pct = ((tp - close) / close) * 100
                alerts.append(f"{t} ${close:.2f} TP {tp:.2f} (+{pct:.2f}%)")
        except: continue
    return alerts
