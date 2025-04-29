import streamlit as st
from datetime import date
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time

# Konfigurasi halaman
st.set_page_config(page_title="TradeCast - Analyze Page", layout="wide")

# Judul Aplikasi
st.title("TradeCast")
st.markdown("## Hey there! Welcome to **TraderCast** 👋")
st.write("Ready to take your trading to the next level? Explore our smart features and make the most out of every market move!")
st.markdown("---")

# Konstanta
START = "2015-01-01"
TODAY = date.today().strftime("%Y-%m-%d")

# Deteksi apakah ini mata uang (forex)
def is_currency(ticker):
    return ticker.endswith("=X")

# Fungsi rekomendasi saham
def get_stock_suggestions():
    return [
        # Saham
        "AAPL", "TSLA", "GOOG", "BBCA.JK", "BBTN.JK", "BRIS.JK",
        "JPM", "BAC", "WFC", "HSBC", "RY.TO", "SAN", "TD", 
        "GOLD", "CL=F",
        # Forex / Currency
        "USDIDR=X", "EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X"
    ]


# Input pencarian saham
selected_stock = st.text_input("Enter stock symbol (eg: AAPL, TSLA, BBCA.JK, etc.):")

# Tampilkan rekomendasi berdasarkan input
if selected_stock:
    suggestions = [stock for stock in get_stock_suggestions() if selected_stock.upper() in stock]
    if suggestions:
        st.write("Maybe what you are looking for:", ", ".join(suggestions))

# Pilih Mode Analisis
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<h3 style="text-align:center;">Select Analysis Mode</h3>', unsafe_allow_html=True)
    mode = st.radio('', ["Investor Mode 💼", "Trader Mode 📉"], horizontal=True)

if "Trader" in mode:
    st.warning("⚡ You choose Trader Mode! Focus on daily trading opportunities.")
else:
    st.success("📈 You choose Investor Mode! Focus on long-term growth.")

    # Fungsi ambil data saham
@st.cache_data
def load_data(ticker):
    try:
        df = yf.download(ticker, START, TODAY).reset_index()
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        return df.dropna()
    except Exception as e:
        st.error(f"Failed to retrieve data {e}")
        return pd.DataFrame()


# Tombol SEARCH
if st.button("SEARCH"):
    if not selected_stock:
        st.warning("Please enter the stock symbol first.")
    else:
        if selected_stock.upper() == "GOLD":
            st.markdown("[Lihat harga emas di Yahoo Finance](https://finance.yahoo.com/quote/GOLD)")
        else:
            @st.cache_data
            def load_data(ticker):
                try:
                    data = yf.download(ticker, START, TODAY).reset_index()
                    data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
                    return data.dropna()
                except Exception as e:
                    st.error(f"Gagal mengambil data: {e}")
                    return pd.DataFrame()

            with st.spinner("Retrieving stock data..."):
                time.sleep(2)
                data = load_data(selected_stock)

            if data.empty:
                st.error("Data is not available for this stock. Try searching for another stock..")
            else:
                stock_info = yf.Ticker(selected_stock).info

                if mode == "Investor Mode 💼":
                    st.subheader("📊 Fundamental Stock Information")
                    st.write(f"**Market Cap:** ${stock_info.get('marketCap', 'N/A')}")
                    st.write(f"**P/E Ratio:** {stock_info.get('trailingPE', 'N/A')}")
                    st.write(f"**EPS:** {stock_info.get('trailingEps', 'N/A')}")
                    st.write(f"**Dividend Yield:** {stock_info.get('dividendYield', 'N/A')}")

                elif mode == "Trader Mode 📉":
                    st.subheader("📈 Technical Analysis")

                    # Moving Averages
                    data["MA50"] = data["Close"].rolling(window=50).mean()
                    data["MA200"] = data["Close"].rolling(window=200).mean()

                    # MACD
                    short_ema = data["Close"].ewm(span=12, adjust=False).mean()
                    long_ema = data["Close"].ewm(span=26, adjust=False).mean()
                    data["MACD"] = short_ema - long_ema
                    data["Signal Line"] = data["MACD"].ewm(span=9, adjust=False).mean()

                    # Bollinger Bands
                    data["20MA"] = data["Close"].rolling(window=20).mean()
                    data["stddev"] = data["Close"].rolling(window=20).std()
                    data["Upper Band"] = data["20MA"] + (data["stddev"] * 2)
                    data["Lower Band"] = data["20MA"] - (data["stddev"] * 2)

                    # Grafik-grafik
                    fig_vol = go.Figure()
                    fig_vol.add_trace(go.Bar(x=data["Date"], y=data["Volume"], name="Volume"))
                    fig_vol.update_layout(title="Volume Saham", template="plotly_dark")

                    fig_macd = go.Figure()
                    fig_macd.add_trace(go.Scatter(x=data["Date"], y=data["MACD"], name="MACD", line=dict(color="blue")))
                    fig_macd.add_trace(go.Scatter(x=data["Date"], y=data["Signal Line"], name="Signal Line", line=dict(color="red")))
                    fig_macd.update_layout(title="MACD & Signal Line", template="plotly_dark")

                    fig_bollinger = go.Figure()
                    fig_bollinger.add_trace(go.Scatter(x=data["Date"], y=data["Upper Band"], name="Upper Band", line=dict(color="green")))
                    fig_bollinger.add_trace(go.Scatter(x=data["Date"], y=data["Lower Band"], name="Lower Band", line=dict(color="red")))
                    fig_bollinger.add_trace(go.Scatter(x=data["Date"], y=data["Close"], name="Closing Price", line=dict(color="white")))
                    fig_bollinger.update_layout(title="Bollinger Bands", template="plotly_dark")

                    st.plotly_chart(fig_vol, use_container_width=True)
                    st.plotly_chart(fig_macd, use_container_width=True)
                    st.plotly_chart(fig_bollinger, use_container_width=True)

                    # Tampilan Data Saham Terbaru
                st.subheader("Stock Data View")
                data["Change"] = data["Close"].diff()
                st.dataframe(data.tail().style.applymap(lambda x: 'background-color: green' if x >= 0 else 'background-color: red', subset=["Change"]))

                # Candlestick
                st.subheader("Stock Price Chart")
                fig = go.Figure(data=[go.Candlestick(
                    x=data["Date"],
                    open=data["Open"],
                    high=data["High"],
                    low=data["Low"],
                    close=data["Close"]
                )])
                fig.update_layout(
                    title=f"Stock Price {selected_stock.upper()} From {START} to {TODAY}",
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)

                # ===== Keputusan Investasi =====
                st.subheader("🛒 Investment Decisions")

                # RSI
                delta = data["Close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data["RSI"] = 100 - (100 / (1 + rs))

                # MACD & MA
                short_ema = data['Close'].ewm(span=12, adjust=False).mean()
                long_ema = data['Close'].ewm(span=26, adjust=False).mean()
                data["MACD"] = short_ema - long_ema
                data["Signal Line"] = data["MACD"].ewm(span=9, adjust=False).mean()
                data["MA50"] = data["Close"].rolling(window=50).mean()
                data["MA200"] = data["Close"].rolling(window=200).mean()

                # Indikator
                last_rsi = data["RSI"].iloc[-1]
                last_macd = data["MACD"].iloc[-1]
                last_signal = data["Signal Line"].iloc[-1]
                last_ma50 = data["MA50"].iloc[-1]
                last_ma200 = data["MA200"].iloc[-1]
                last_price_raw = data["Close"].iloc[-1]
                last_price = float(last_price_raw) if not pd.isna(last_price_raw) else 0.0

                open_price = data["Open"].iloc[-1]
                today_change = last_price - open_price
                percent_change = (today_change / open_price) * 100 if open_price != 0 else 0

                # Sinyal
                rsi_oversold = last_rsi < 30
                rsi_overbought = last_rsi > 70
                macd_bullish = last_macd > last_signal and last_macd < 0
                macd_bearish = last_macd < last_signal and last_macd > 0
                golden_cross = last_ma50 > last_ma200
                death_cross = last_ma50 < last_ma200
                price_above_ma50 = last_price > last_ma50
                price_below_ma50 = last_price < last_ma50

                buy_signal = (rsi_oversold or golden_cross or macd_bullish) and price_above_ma50
                sell_signal = (rsi_overbought or death_cross or macd_bearish) and price_below_ma50
                if percent_change < -2:
                    sell_signal = True

                currency_mode = is_currency(selected_stock.upper())
                symbol_display = "USD" if currency_mode else "$"
                label_display = "Current Price" if currency_mode else "Current Stock Price"

                # Tampilkan harga terakhir
                st.markdown(f"<div style='font-size:18px;'>💵 <strong>{label_display}:</strong> {symbol_display} {last_price:,.2f}</div>", unsafe_allow_html=True)

                # Tampilkan sinyal
                if buy_signal and not sell_signal:
                    st.markdown('<div class="rekomendasi-beli">✅ <strong>BUY</strong></div>', unsafe_allow_html=True)
                elif sell_signal and not buy_signal:
                    st.markdown('<div class="rekomendasi-jual">📉 <strong>SELL</strong></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="rekomendasi-tahan">⚖️ <strong>STAND</strong></div>', unsafe_allow_html=True)

# Footer
st.markdown("[Data source: Yahoo Finance](https://finance.yahoo.com/)")

# CSS eksternal
def load_css():
    try:
        with open("styles.css", "r") as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("File CSS tidak ditemukan.")

load_css()