"""
Investment Dashboard — Bloomberg-Style Real-Time Market Intelligence
====================================================================
A professional-grade, single-file Streamlit application for Indian & global
market tracking, technical analysis, market breadth, news aggregation, and
TradingView chart embedding.

Author : Auto-generated
Stack  : Python 3.10+ · Streamlit · yfinance · Plotly · feedparser
License: MIT

FUTURE ENHANCEMENTS (not built yet):
- Fear & Greed Gauge: Map India VIX to a 0–100 sentiment scale gauge.
- USD/INR Currency Tracker: Add USDINR=X to sidebar tickers.
- Portfolio CSV Upload: Auto-filter news & technicals to user holdings.
- Alerts: Visual/audio alerts on RSI 70/30 cross or 200 EMA cross.
"""

# ──────────────────────────────────────────────
# 0. Imports & Page Configuration
# ──────────────────────────────────────────────
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import feedparser
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Investment Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# 0a. Auto-Refresh Setup
# ──────────────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

# ──────────────────────────────────────────────
# 1. Custom CSS — Bloomberg Dark Theme
# ──────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Global dark overrides ── */
    .stApp {
        background-color: #0e1117;
        color: #c9d1d9;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #21262d;
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] {
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 0.78rem;
        color: #8b949e;
    }
    [data-testid="stMetricValue"] {
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 1.25rem;
        color: #e6edf3;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #21262d;
    }
    section[data-testid="stSidebar"] h3 {
        color: #58a6ff;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        border-bottom: 1px solid #21262d;
        padding-bottom: 4px;
        margin-top: 1.2rem;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #161b22;
        border-radius: 6px;
        padding: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #8b949e;
        border-radius: 4px;
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 0.8rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #21262d;
        color: #e6edf3;
    }

    /* Tables */
    .stDataFrame {
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 0.8rem;
    }

    /* Header */
    .dashboard-header {
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        color: #58a6ff;
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 0;
        padding-bottom: 0;
    }
    .dashboard-sub {
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        color: #484f58;
        font-size: 0.75rem;
        margin-top: 0;
    }

    /* News items */
    .news-item {
        border-bottom: 1px solid #21262d;
        padding: 8px 0;
    }
    .news-item a {
        color: #58a6ff;
        text-decoration: none;
        font-weight: 500;
    }
    .news-item a:hover {
        text-decoration: underline;
    }
    .news-meta {
        color: #484f58;
        font-size: 0.75rem;
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# 2. Helper Functions
# ──────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    font=dict(family="SF Mono, Fira Code, Consolas, monospace", size=11, color="#c9d1d9"),
    margin=dict(l=40, r=20, t=40, b=30),
    xaxis=dict(gridcolor="#21262d", gridwidth=0.5),
    yaxis=dict(gridcolor="#21262d", gridwidth=0.5),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
)


@st.cache_data(ttl=120, show_spinner=False)
def fetch_ticker_data(symbol: str, period: str = "5d") -> dict | None:
    """Fetch current price & daily change for a single ticker."""
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period=period)
        if hist.empty or len(hist) < 2:
            return None
        last_close = hist["Close"].iloc[-1]
        prev_close = hist["Close"].iloc[-2]
        pct_change = ((last_close - prev_close) / prev_close) * 100
        return {"price": last_close, "change": pct_change}
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def fetch_ohlcv(symbol: str, period: str = "1y") -> pd.DataFrame:
    """Fetch 1-year daily OHLCV data for technical analysis."""
    try:
        tk = yf.Ticker(symbol)
        df = tk.history(period=period)
        if df.empty:
            return pd.DataFrame()
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def fetch_breadth_data(tickers: list[str]) -> pd.DataFrame:
    """Download recent data for Nifty 50 constituents & compute 50-day SMA status."""
    records = []
    for sym in tickers:
        try:
            tk = yf.Ticker(sym)
            hist = tk.history(period="6mo")
            if hist.empty or len(hist) < 50:
                continue
            sma50 = hist["Close"].rolling(50).mean().iloc[-1]
            last = hist["Close"].iloc[-1]
            records.append(
                {
                    "Ticker": sym.replace(".NS", ""),
                    "Price": round(last, 2),
                    "50-SMA": round(sma50, 2),
                    "Above SMA": "✅ Yes" if last > sma50 else "❌ No",
                    "_above": last > sma50,
                }
            )
        except Exception:
            continue
    return pd.DataFrame(records)


@st.cache_data(ttl=900, show_spinner=False)
def fetch_rss(url: str) -> list[dict]:
    """Parse an RSS feed and return a list of article dicts."""
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:20]:
            published = ""
            if hasattr(entry, "published"):
                published = entry.published
            elif hasattr(entry, "updated"):
                published = entry.updated
            items.append(
                {
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", "#"),
                    "published": published,
                    "source": feed.feed.get("title", "Unknown"),
                }
            )
        return items
    except Exception:
        return []


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_macd(
    series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def compute_bollinger(
    series: pd.Series, period: int = 20, std_dev: int = 2
) -> tuple[pd.Series, pd.Series, pd.Series]:
    sma = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    return sma, upper, lower


def format_price(val: float, decimals: int = 2) -> str:
    if abs(val) >= 1_000:
        return f"{val:,.{decimals}f}"
    return f"{val:.{decimals}f}"


# ──────────────────────────────────────────────
# 3. Sidebar — Live Market Ticker & Controls
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 Market Dashboard")

    # Refresh controls
    refresh_options = {"Off": 0, "1 min": 60_000, "5 min": 300_000, "15 min": 900_000}
    refresh_choice = st.selectbox("Auto-Refresh Interval", list(refresh_options.keys()), index=0)
    if HAS_AUTOREFRESH and refresh_options[refresh_choice] > 0:
        st_autorefresh(interval=refresh_options[refresh_choice], key="data_refresh")

    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()

    # ── Indian Indices ──
    st.markdown("### 🇮🇳 Indian Indices")
    indian_tickers = {
        "NIFTY 50": "^NSEI",
        "BANK NIFTY": "^NSEBANK",
        "GIFT NIFTY": "GIFTTY=F",
        "INDIA VIX": "^INDIAVIX",
    }
    for label, sym in indian_tickers.items():
        data = fetch_ticker_data(sym)
        if data:
            st.metric(label, format_price(data["price"]), f"{data['change']:+.2f}%")
        else:
            st.metric(label, "N/A", "—")

    # ── Commodities ──
    st.markdown("### 🪙 Commodities")
    commodity_tickers = {
        "GOLD": "GC=F",
        "SILVER": "SI=F",
        "BRENT CRUDE": "BZ=F",
    }
    for label, sym in commodity_tickers.items():
        data = fetch_ticker_data(sym)
        if data:
            st.metric(label, format_price(data["price"]), f"{data['change']:+.2f}%")
        else:
            st.metric(label, "N/A", "—")

    # ── US Indices ──
    st.markdown("### 🇺🇸 US Indices")
    us_tickers = {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
    }
    for label, sym in us_tickers.items():
        data = fetch_ticker_data(sym)
        if data:
            st.metric(label, format_price(data["price"]), f"{data['change']:+.2f}%")
        else:
            st.metric(label, "N/A", "—")

    st.divider()

    # ── Custom RSS Inputs ──
    st.markdown("### 📡 Custom RSS Feeds")
    st.caption(
        "Paste RSS URLs from your subscriptions (e.g., The Economist, The Ken). "
        "Find these in your account settings under 'RSS' or 'Feeds'. "
        "Paywalled content requires your personal feed URL."
    )
    custom_rss_1 = st.text_input("Custom Feed 1", placeholder="https://example.com/rss", key="rss1")
    custom_rss_2 = st.text_input("Custom Feed 2", placeholder="https://example.com/rss", key="rss2")
    custom_rss_3 = st.text_input("Custom Feed 3", placeholder="https://example.com/rss", key="rss3")


# ──────────────────────────────────────────────
# 4. Main Content — Header
# ──────────────────────────────────────────────
st.markdown('<p class="dashboard-header">INVESTMENT DASHBOARD</p>', unsafe_allow_html=True)
st.markdown(
    f'<p class="dashboard-sub">Last refreshed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  •  '
    f"Data via Yahoo Finance  •  Not financial advice</p>",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# 5. TradingView Chart Embed
# ──────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 Live Chart — TradingView")
tv_symbol = st.text_input(
    "TradingView Symbol",
    value="NSE:NIFTY",
    help="Enter any TradingView symbol, e.g., NSE:RELIANCE, NASDAQ:AAPL, BSE:SENSEX",
)
tradingview_html = f"""
<div class="tradingview-widget-container" style="height:520px;width:100%;">
  <div id="tradingview_chart" style="height:100%;width:100%;"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "autosize": true,
    "symbol": "{tv_symbol}",
    "interval": "D",
    "timezone": "Asia/Kolkata",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#0e1117",
    "enable_publishing": false,
    "allow_symbol_change": true,
    "container_id": "tradingview_chart",
    "hide_side_toolbar": false,
    "studies": ["MAExp@tv-basicstudies"],
    "backgroundColor": "#0e1117",
    "gridColor": "#21262d"
  }});
  </script>
</div>
"""
st.components.v1.html(tradingview_html, height=540)

# ──────────────────────────────────────────────
# 6. Technical Intelligence Engine
# ──────────────────────────────────────────────
st.markdown("---")
st.subheader("🔬 Technical Intelligence Engine")
st.caption(
    "Enter any ticker symbol. For NSE-listed Indian stocks, add the `.NS` suffix "
    "(e.g., `RELIANCE.NS`, `TCS.NS`). US stocks use plain symbols (e.g., `AAPL`, `MSFT`)."
)

tech_ticker = st.text_input(
    "Analyse Ticker",
    value="RELIANCE.NS",
    key="tech_ticker_input",
    placeholder="e.g., RELIANCE.NS, AAPL, TCS.NS",
)

if tech_ticker:
    with st.spinner(f"Fetching data for {tech_ticker}…"):
        ohlcv = fetch_ohlcv(tech_ticker)

    if ohlcv.empty:
        st.warning(f"⚠️ Could not fetch data for **{tech_ticker}**. Check the symbol and try again.")
    else:
        close = ohlcv["Close"]

        # Indicators
        rsi = compute_rsi(close)
        macd_line, signal_line, macd_hist = compute_macd(close)
        ema200 = close.ewm(span=200, adjust=False).mean()
        bb_mid, bb_upper, bb_lower = compute_bollinger(close)

        # ── Tabbed Chart ──
        tab_price, tab_rsi, tab_macd = st.tabs(["Price + Overlays", "RSI", "MACD"])

        with tab_price:
            fig = go.Figure()
            fig.add_trace(
                go.Candlestick(
                    x=ohlcv.index,
                    open=ohlcv["Open"],
                    high=ohlcv["High"],
                    low=ohlcv["Low"],
                    close=ohlcv["Close"],
                    name="OHLC",
                    increasing_line_color="#3fb950",
                    decreasing_line_color="#f85149",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ohlcv.index, y=ema200, mode="lines",
                    name="200 EMA", line=dict(color="#f0883e", width=1.5),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ohlcv.index, y=bb_upper, mode="lines",
                    name="BB Upper", line=dict(color="#8b949e", width=1, dash="dot"),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ohlcv.index, y=bb_lower, mode="lines",
                    name="BB Lower", line=dict(color="#8b949e", width=1, dash="dot"),
                    fill="tonexty", fillcolor="rgba(139,148,158,0.06)",
                )
            )
            fig.update_layout(
                **PLOTLY_LAYOUT,
                title=f"{tech_ticker} — Price, 200 EMA & Bollinger Bands",
                xaxis_rangeslider_visible=False,
                height=480,
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab_rsi:
            fig_rsi = go.Figure()
            fig_rsi.add_trace(
                go.Scatter(
                    x=ohlcv.index, y=rsi, mode="lines",
                    name="RSI (14)", line=dict(color="#58a6ff", width=1.5),
                )
            )
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="#f85149", annotation_text="Overbought (70)")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="#3fb950", annotation_text="Oversold (30)")
            fig_rsi.add_hline(y=50, line_dash="dot", line_color="#484f58")
            fig_rsi.update_layout(
                **PLOTLY_LAYOUT,
                title=f"{tech_ticker} — RSI (14)",
                yaxis=dict(range=[0, 100], gridcolor="#21262d"),
                height=350,
            )
            st.plotly_chart(fig_rsi, use_container_width=True)

        with tab_macd:
            fig_macd = make_subplots(rows=1, cols=1)
            colors = ["#3fb950" if v >= 0 else "#f85149" for v in macd_hist]
            fig_macd.add_trace(
                go.Bar(x=ohlcv.index, y=macd_hist, name="Histogram", marker_color=colors)
            )
            fig_macd.add_trace(
                go.Scatter(
                    x=ohlcv.index, y=macd_line, mode="lines",
                    name="MACD", line=dict(color="#58a6ff", width=1.5),
                )
            )
            fig_macd.add_trace(
                go.Scatter(
                    x=ohlcv.index, y=signal_line, mode="lines",
                    name="Signal", line=dict(color="#f0883e", width=1.5),
                )
            )
            fig_macd.update_layout(
                **PLOTLY_LAYOUT,
                title=f"{tech_ticker} — MACD (12, 26, 9)",
                height=350,
                barmode="overlay",
            )
            st.plotly_chart(fig_macd, use_container_width=True)

        # ── Signal Summary ──
        st.markdown("#### Signal Summary")
        latest_rsi = rsi.iloc[-1]
        latest_price = close.iloc[-1]
        latest_ema200 = ema200.iloc[-1]
        latest_macd = macd_line.iloc[-1]
        latest_signal = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        prev_signal = signal_line.iloc[-2]
        latest_bb_upper = bb_upper.iloc[-1]
        latest_bb_lower = bb_lower.iloc[-1]

        col_s1, col_s2 = st.columns(2)

        with col_s1:
            # RSI Signal
            if latest_rsi >= 70:
                st.warning(f"⚠️ **RSI is {latest_rsi:.1f}** → Overbought territory. Consider caution.")
            elif latest_rsi <= 30:
                st.success(f"🟢 **RSI is {latest_rsi:.1f}** → Oversold territory. Potential buying opportunity.")
            else:
                st.info(f"ℹ️ **RSI is {latest_rsi:.1f}** → Neutral zone.")

            # Bollinger Band Signal
            if latest_price >= latest_bb_upper:
                st.warning("⚠️ **Price at upper Bollinger Band** → Potentially overextended.")
            elif latest_price <= latest_bb_lower:
                st.success("🟢 **Price at lower Bollinger Band** → Potentially oversold.")
            else:
                st.info("ℹ️ **Price within Bollinger Bands** → Normal volatility range.")

        with col_s2:
            # EMA Signal
            if latest_price > latest_ema200:
                st.success(
                    f"🟢 **Price ({format_price(latest_price)}) is above 200 EMA "
                    f"({format_price(latest_ema200)})** → Long-term trend is bullish."
                )
            else:
                st.warning(
                    f"⚠️ **Price ({format_price(latest_price)}) is below 200 EMA "
                    f"({format_price(latest_ema200)})** → Long-term trend is bearish."
                )

            # MACD Signal
            if prev_macd <= prev_signal and latest_macd > latest_signal:
                st.success("🟢 **MACD bullish crossover detected** → Possible upward momentum shift.")
            elif prev_macd >= prev_signal and latest_macd < latest_signal:
                st.warning("⚠️ **MACD bearish crossover detected** → Possible downward momentum shift.")
            else:
                if latest_macd > latest_signal:
                    st.info("ℹ️ **MACD above signal line** → Bullish momentum continues.")
                else:
                    st.info("ℹ️ **MACD below signal line** → Bearish momentum continues.")


# ──────────────────────────────────────────────
# 7. Nifty 50 Market Breadth Tracker
# ──────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 Nifty 50 Market Breadth")

NIFTY50_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "HCLTECH.NS", "SUNPHARMA.NS", "TITAN.NS", "WIPRO.NS", "ULTRACEMCO.NS",
    "NESTLEIND.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "POWERGRID.NS", "NTPC.NS",
    "M&M.NS", "TECHM.NS", "INDUSINDBK.NS", "ADANIENT.NS", "JSWSTEEL.NS",
    "BAJAJFINSV.NS", "ONGC.NS", "COALINDIA.NS", "GRASIM.NS", "HINDALCO.NS",
    "CIPLA.NS", "DRREDDY.NS", "BPCL.NS", "EICHERMOT.NS", "DIVISLAB.NS",
    "APOLLOHOSP.NS", "TATACONSUM.NS", "HEROMOTOCO.NS", "SBILIFE.NS", "BRITANNIA.NS",
    "LTIM.NS", "BAJAJ-AUTO.NS", "HDFCLIFE.NS", "SHRIRAMFIN.NS", "ADANIPORTS.NS",
]

with st.spinner("Scanning Nifty 50 constituents…"):
    breadth_df = fetch_breadth_data(NIFTY50_TICKERS)

if breadth_df.empty:
    st.warning("⚠️ Could not fetch breadth data. Try refreshing.")
else:
    above_count = breadth_df["_above"].sum()
    total_count = len(breadth_df)
    pct_above = (above_count / total_count) * 100 if total_count > 0 else 0

    col_g, col_t = st.columns([1, 2])

    with col_g:
        fig_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=pct_above,
                number=dict(suffix="%", font=dict(size=36, color="#e6edf3")),
                title=dict(text="Stocks Above 50-SMA", font=dict(size=14, color="#8b949e")),
                delta=dict(reference=50, suffix="%"),
                gauge=dict(
                    axis=dict(range=[0, 100], tickcolor="#484f58"),
                    bar=dict(color="#58a6ff"),
                    bgcolor="#161b22",
                    bordercolor="#21262d",
                    steps=[
                        dict(range=[0, 30], color="#3d1f1f"),
                        dict(range=[30, 70], color="#1f2d1f"),
                        dict(range=[70, 100], color="#1a3a1a"),
                    ],
                    threshold=dict(line=dict(color="#f0883e", width=3), value=pct_above),
                ),
            )
        )
        fig_gauge.update_layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font=dict(family="SF Mono, Fira Code, Consolas, monospace", color="#c9d1d9"),
            height=300,
            margin=dict(l=30, r=30, t=60, b=20),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.caption(f"**{int(above_count)}/{total_count}** constituents above their 50-day SMA")

    with col_t:
        display_df = breadth_df[["Ticker", "Price", "50-SMA", "Above SMA"]].copy()
        st.dataframe(
            display_df,
            use_container_width=True,
            height=340,
            hide_index=True,
        )


# ──────────────────────────────────────────────
# 8. Geopolitical & News Command Center
# ──────────────────────────────────────────────
st.markdown("---")
st.subheader("📰 News Command Center")

GLOBAL_FEEDS = {
    "Reuters World": "https://feeds.reuters.com/Reuters/worldNews",
    "CNBC Top News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "Moneycontrol Markets": "https://www.moneycontrol.com/rss/marketreports.xml",
    "Economic Times Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "MarketWatch Top Stories": "https://feeds.marketwatch.com/marketwatch/topstories/",
}


def render_news_items(items: list[dict]):
    """Render a list of news items as styled HTML."""
    if not items:
        st.caption("No items found. Feed may be temporarily unavailable.")
        return
    for item in items:
        st.markdown(
            f'<div class="news-item">'
            f'<a href="{item["link"]}" target="_blank">{item["title"]}</a><br>'
            f'<span class="news-meta">{item["source"]}  •  {item["published"]}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )


news_tab1, news_tab2 = st.tabs(["🌍 Global Macro", "📌 My Portfolio News"])

with news_tab1:
    all_global_items = []
    for name, url in GLOBAL_FEEDS.items():
        all_global_items.extend(fetch_rss(url))
    # Sort by published (best effort — RSS dates vary)
    all_global_items.sort(key=lambda x: x.get("published", ""), reverse=True)
    render_news_items(all_global_items[:40])

with news_tab2:
    custom_urls = [u for u in [custom_rss_1, custom_rss_2, custom_rss_3] if u.strip()]
    if not custom_urls:
        st.info(
            "📡 No custom feeds added yet. Paste your personal RSS URLs in the sidebar "
            "to see filtered portfolio news here."
        )
    else:
        custom_items = []
        for url in custom_urls:
            custom_items.extend(fetch_rss(url.strip()))
        custom_items.sort(key=lambda x: x.get("published", ""), reverse=True)
        render_news_items(custom_items[:30])


# ──────────────────────────────────────────────
# 9. Economic Calendar (Option B — TradingView Widget Embed)
# ──────────────────────────────────────────────
st.markdown("---")
st.subheader("📅 Economic Calendar")
st.caption("Powered by TradingView. Shows upcoming global economic events, filterable by country and importance.")

econ_cal_html = """
<div class="tradingview-widget-container" style="width:100%;height:500px;">
  <iframe
    scrolling="no"
    allowtransparency="true"
    frameborder="0"
    src="https://s.tradingview.com/embed-widget/events/?locale=en#%7B%22colorTheme%22%3A%22dark%22%2C%22isTransparent%22%3Atrue%2C%22width%22%3A%22100%25%22%2C%22height%22%3A%22500%22%2C%22importanceFilter%22%3A%22-1%2C0%2C1%22%2C%22countryFilter%22%3A%22in%2Cus%2Ceu%2Cgb%2Ccn%2Cjp%22%7D"
    style="width:100%;height:100%;border:none;">
  </iframe>
</div>
"""
st.components.v1.html(econ_cal_html, height=520)


# ──────────────────────────────────────────────
# 10. Footer
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="text-align:center;color:#484f58;font-size:0.72rem;font-family:monospace;">'
    "Investment Dashboard v1.0 • Data: Yahoo Finance, TradingView, RSS • "
    "This is not financial advice. Always do your own research."
    "</p>",
    unsafe_allow_html=True,
)
