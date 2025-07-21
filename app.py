# LIVE SENTIMENT SCANNER APP (Streamlit)
# Uses Finnhub, FRED, Alpaca, yfinance, and cot_reports

import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from fredapi import Fred
from datetime import datetime, timedelta
import cot_reports as cot

# ========== API KEYS ==========
FINNHUB_API_KEY = "d1uv2rhr01qujmdeohv0d1uv2rhr01qujmdeohvg"
FRED_API_KEY = "550ba571cdf3a095e3523cfe947b41af"
ALPACA_KEY = "f9d8f27f3cd24ad1a1919722aee7afae"
ALPACA_SECRET = "pP8fBD7oiajpxwdUDUKV"

# ========== INIT ==========
st.set_page_config(page_title="Live Sentiment Scanner", layout="wide")
st.title("📈 Live Sentiment Scanner")

# ========== FRED SETUP ==========
fred = Fred(api_key=FRED_API_KEY)

def get_macro_data():
    cpi = fred.get_series("CPIAUCSL")
    pce = fred.get_series("PCEPI")
    gdp = fred.get_series("GDP")
    return {
        "CPI YoY": cpi.pct_change(12).dropna().iloc[-1],
        "PCE YoY": pce.pct_change(12).dropna().iloc[-1],
        "GDP Last": gdp.dropna().iloc[-1],
    }

# ========== FINNHUB NEWS & EARNINGS ==========
def get_news_sentiment(symbol):
    url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    news = response.json()
    score = sum(1 if symbol in article['headline'] and 'beat' in article['headline'].lower() else -1 for article in news)
    return "Positive" if score > 0 else "Negative" if score < 0 else "Neutral"

def get_earnings_sentiment(symbol):
    url = f"https://finnhub.io/api/v1/stock/earnings?symbol={symbol}&token={FINNHUB_API_KEY}"
    res = requests.get(url)
    data = res.json()
    if data and isinstance(data, list):
        latest = data[0]
        if latest['actual'] > latest['estimate']:
            return "Beat"
        elif latest['actual'] < latest['estimate']:
            return "Miss"
    return "Neutral"

# ========== COT DATA ==========
def get_cot_sentiment(market="S&P 500 Consolidated"):
    try:
        df = cot.cot_all(contract_market=market)
        df = df[df["As of Date in Form YYYY-MM-DD"] != '']
        latest = df.iloc[-1]
        commercials = int(latest["Commercials Long"] or 0) - int(latest["Commercials Short"] or 0)
        specs = int(latest["Noncommercials Long"] or 0) - int(latest["Noncommercials Short"] or 0)
        if specs > commercials:
            return "Bullish"
        elif specs < commercials:
            return "Bearish"
        else:
            return "Neutral"
    except:
        return "Neutral"

# ========== STOCK DATA ==========
def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "Symbol": symbol,
            "Price": info.get("currentPrice", 0),
            "Volume": info.get("volume", 0),
            "Float": info.get("floatShares", 0),
            "NewsSentiment": get_news_sentiment(symbol),
            "EarningsSentiment": get_earnings_sentiment(symbol)
        }
    except:
        return {
            "Symbol": symbol,
            "Price": 0,
            "Volume": 0,
            "Float": 0,
            "NewsSentiment": "Neutral",
            "EarningsSentiment": "Neutral"
        }

# ========== UI + EXECUTION ==========
st.sidebar.header("Scanner Settings")
stocks = st.sidebar.text_area("Enter Symbols (comma-separated)", "AAPL,MSFT,TSLA,NVDA,GOOG").split(',')
stocks = [s.strip().upper() for s in stocks if s.strip()]

macro = get_macro_data()
cot_sentiment = get_cot_sentiment("S&P 500 Consolidated")

st.subheader("📊 Macro Environment")
st.metric("🧾 CPI YoY", f"{macro['CPI YoY']*100:.2f}%")
st.metric("🏠 PCE YoY", f"{macro['PCE YoY']*100:.2f}%")
st.metric("📈 GDP Last", f"{macro['GDP Last'] / 1e3:.2f}B")
st.metric("🧠 COT Sentiment", cot_sentiment)

st.subheader("📈 Stock Sentiment Scanner")
df = pd.DataFrame([get_stock_data(sym) for sym in stocks])
st.dataframe(df, use_container_width=True)

# ========== END ==========
st.caption("Powered by yfinance, Finnhub, FRED, Alpaca, and CFTC COT")
