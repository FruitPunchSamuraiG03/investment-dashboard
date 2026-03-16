# =============================================================================
# INVESTMENT DASHBOARD — Bloomberg Terminal Aesthetic
# Author: Generated for personal use
# =============================================================================
# FUTURE ENHANCEMENTS (not yet built):
#   - Fear & Greed Gauge: Map India VIX to 0-100 sentiment gauge
#   - USD/INR Currency Tracker: Add USDINR=X to sidebar ticker
#   - Portfolio CSV Upload: Auto-filter news & technicals to holdings
#   - Alerts: Visual/audio alerts when RSI crosses 70/30 or price crosses 200 EMA
# =============================================================================

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

# ── Optional auto-refresh ──────────────────────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Investment Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# GLOBAL CSS — Dark Bloomberg-style theme
# =============================================================================
st.markdown("""
<style>
    /* ── Base ── */
    .stApp { background-color: #0a0a0f; color: #e0e0e0; }
    section[data-testid="stSidebar"] { background-color: #0d0d14; border-right: 1px solid #1e2030; }
    
    /* ── Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    body, .stApp { font-family: 'Inter', sans-serif; }
    .mono { font-family: 'JetBrains Mono', monospace !important; }

    /* ── Metric cards ── */
    [data-testid="metric-container"] {
        background: #0f0f1a;
        border: 1px solid #1e2030;
        border-radius: 6px;
        padding: 8px 12px;
    }
    [data-testid="stMetricLabel"] { font-size: 0.65rem !important; color: #8899aa !important; text-transform: uppercase; letter-spacing: 0.08em; }
    [data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; font-size: 1.1rem !important; color: #e8ecf0 !important; }
    [data-testid="stMetricDelta"] { font-family: 'JetBrains Mono', monospace !important; font-size: 0.75rem !important; }

    /* ── Section headers ── */
    .section-header {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6rem;
        letter-spacing: 0.15em;
        color: #4a5568;
        text-transform: uppercase;
        border-bottom: 1px solid #1a1f2e;
        padding-bottom: 4px;
        margin: 14px 0 8px 0;
    }
    
    /* ── Signal boxes ── */
    .signal-box {
        background: #0f0f1a;
        border-left: 3px solid #00b4d8;
        border-radius: 0 6px 6px 0;
        padding: 10px 14px;
        margin: 6px 0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        color: #c9d6e3;
    }
    .signal-bullish { border-left-color: #00c853; }
    .signal-bearish { border-left-color: #ff1744; }
    .signal-neutral { border-left-color: #ffd600; }
    
    /* ── News cards ── */
    .news-card {
        background: #0f0f1a;
        border: 1px solid #1e2030;
        border-radius: 6px;
        padding: 10px 14px;
        margin: 5px 0;
    }
    .news-headline { font-weight: 600; font-size: 0.88rem; color: #cbd5e0; }
    .news-meta { font-size: 0.72rem; color: #4a5568; margin-top: 3px; font-family: 'JetBrains Mono', monospace; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] { background: #0d0d14; gap: 4px; }
    .stTabs [data-baseweb="tab"] { background: #0f0f1a; border: 1px solid #1e2030; border-radius: 4px; color: #7a8a9a; font-size: 0.8rem; }
    .stTabs [aria-selected="true"] { background: #1a1f2e !important; color: #00b4d8 !important; border-color: #00b4d8 !important; }

    /* ── Buttons ── */
    .stButton button { background: #1a1f2e; border: 1px solid #2a3040; color: #8899aa; font-size: 0.78rem; border-radius: 4px; }
    .stButton button:hover { background: #1e2535; border-color: #00b4d8; color: #00b4d8; }

    /* ── Table ── */
    .stDataFrame { border: 1px solid #1e2030; border-radius: 6px; }

    /* ── Selectbox / Input ── */
    .stSelectbox > div, .stTextInput > div > div { background: #0f0f1a !important; border-color: #1e2030 !important; color: #e0e0e0 !important; font-family: 'JetBrains Mono', monospace; }

    /* ── Dashboard title ── */
    .dash-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.5rem;
        font-weight: 700;
        color: #00b4d8;
        letter-spacing: 0.1em;
    }
    .dash-subtitle {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        color: #4a5568;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    /* ── Gauge border ── */
    .gauge-container { border: 1px solid #1e2030; border-radius: 8px; background: #0f0f1a; padding: 4px; }
    
    div[data-testid="stHorizontalBlock"] { gap: 12px; }
    hr { border-color: #1e2030; }
</style>
""", unsafe_allow_html=True)

PLOTLY_TEMPLATE = "plotly_dark"
PLOTLY_PAPER_BG = "#0a0a0f"
PLOTLY_PLOT_BG = "#0f0f1a"
PLOTLY_GRID = "#1a1f2e"
GREEN = "#00c853"
RED = "#ff1744"
BLUE = "#00b4d8"
YELLOW = "#ffd600"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def fmt_price(val, decimals=2):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    return f"{val:,.{decimals}f}"

def fmt_pct(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    return f"{val:+.2f}%"

def color_delta(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    return "normal" if val >= 0 else "inverse"


@st.cache_data(ttl=60)
def fetch_ticker_snapshot(symbol):
    """Fetch current price and daily change for a single ticker."""
    try:
        t = yf.Ticker(symbol)
        info = t.fast_info
        price = getattr(info, 'last_price', None)
        prev_close = getattr(info, 'previous_close', None)
        if price and prev_close and prev_close != 0:
            chg_pct = (price - prev_close) / prev_close * 100
        else:
            chg_pct = None
        return price, chg_pct
    except Exception:
        return None, None


@st.cache_data(ttl=300)
def fetch_ohlcv(symbol, period="1y", interval="1d"):
    """Fetch OHLCV data for a given symbol."""
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty:
            return None
        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        return None


def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calc_bollinger(series, period=20, std_dev=2):
    sma = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    return upper, sma, lower


@st.cache_data(ttl=3600)
def fetch_nifty50_breadth():
    """Fetch all Nifty 50 tickers and compute % above 50-day SMA."""
    tickers = [
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
    results = []
    try:
        raw = yf.download(tickers, period="3mo", interval="1d", progress=False, auto_adjust=True)
        close = raw["Close"] if "Close" in raw.columns else raw.xs("Close", axis=1, level=0)
        for t in tickers:
            try:
                s = close[t].dropna()
                if len(s) < 50:
                    status = "Insufficient data"
                    above = None
                else:
                    sma50 = s.rolling(50).mean().iloc[-1]
                    last = s.iloc[-1]
                    above = last > sma50
                    status = "Above 50 SMA" if above else "Below 50 SMA"
                results.append({"Ticker": t.replace(".NS", ""), "Status": status, "Above50SMA": above})
            except Exception:
                results.append({"Ticker": t.replace(".NS", ""), "Status": "Error", "Above50SMA": None})
    except Exception:
        for t in tickers:
            results.append({"Ticker": t.replace(".NS", ""), "Status": "Error", "Above50SMA": None})
    df = pd.DataFrame(results)
    valid = df["Above50SMA"].notna()
    pct = df.loc[valid, "Above50SMA"].mean() * 100 if valid.any() else 0
    return df, pct


@st.cache_data(ttl=600)
def fetch_rss(url):
    """Fetch and parse an RSS feed, return list of dicts."""
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:15]:
            pub = entry.get("published", entry.get("updated", ""))
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(pub)
                pub_str = dt.strftime("%d %b %Y  %H:%M")
            except Exception:
                pub_str = pub[:20] if pub else "–"
            items.append({
                "title": entry.get("title", "No title"),
                "link": entry.get("link", "#"),
                "published": pub_str,
                "source": feed.feed.get("title", url),
            })
        return items
    except Exception:
        return []


def plotly_base_layout(height=400):
    return dict(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=PLOTLY_PAPER_BG,
        plot_bgcolor=PLOTLY_PLOT_BG,
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(family="JetBrains Mono, monospace", size=10, color="#8899aa"),
        xaxis=dict(gridcolor=PLOTLY_GRID, showgrid=True, zeroline=False),
        yaxis=dict(gridcolor=PLOTLY_GRID, showgrid=True, zeroline=False),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
        hovermode="x unified",
    )


# =============================================================================
# SIDEBAR — Market Ticker + Controls
# =============================================================================

with st.sidebar:
    st.markdown('<div class="dash-title">📊 MKTS</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-subtitle">Live Market Intelligence</div>', unsafe_allow_html=True)
    st.markdown("---")

    # ── Auto Refresh ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">⟳ Auto Refresh</div>', unsafe_allow_html=True)
    refresh_map = {"Off": 0, "1 min": 60_000, "5 min": 300_000, "15 min": 900_000}
    refresh_sel = st.selectbox("Interval", list(refresh_map.keys()), index=0, label_visibility="collapsed")
    
    if AUTOREFRESH_AVAILABLE and refresh_map[refresh_sel] > 0:
        st_autorefresh(interval=refresh_map[refresh_sel], key="autorefresh")
    elif not AUTOREFRESH_AVAILABLE and refresh_map[refresh_sel] > 0:
        st.caption("⚠️ Install `streamlit-autorefresh` for auto-refresh.")

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        manual_refresh = st.button("↺ Refresh", use_container_width=True)
    if manual_refresh:
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")

    # ── Indian Indices ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🇮🇳 Indian Indices</div>', unsafe_allow_html=True)
    indian_tickers = {
        "Nifty 50": "^NSEI",
        "Bank Nifty": "^NSEBANK",
        "GIFT Nifty": "GIFTTY=F",
        "India VIX": "^INDIAVIX",
    }
    for label, sym in indian_tickers.items():
        price, chg = fetch_ticker_snapshot(sym)
        st.metric(label=label, value=fmt_price(price), delta=fmt_pct(chg))

    # ── Commodities ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🪙 Commodities</div>', unsafe_allow_html=True)
    commodity_tickers = {
        "Gold ($/oz)": "GC=F",
        "Silver ($/oz)": "SI=F",
        "Brent Crude": "BZ=F",
    }
    for label, sym in commodity_tickers.items():
        price, chg = fetch_ticker_snapshot(sym)
        st.metric(label=label, value=fmt_price(price), delta=fmt_pct(chg))

    # ── US Indices ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🇺🇸 US Markets</div>', unsafe_allow_html=True)
    us_tickers = {
        "S&P 500": "^GSPC",
        "Nasdaq 100": "^IXIC",
    }
    for label, sym in us_tickers.items():
        price, chg = fetch_ticker_snapshot(sym)
        st.metric(label=label, value=fmt_price(price), delta=fmt_pct(chg))

    st.markdown("---")

    # ── Portfolio News RSS inputs ──────────────────────────────────────────────
    st.markdown('<div class="section-header">📰 My News Sources</div>', unsafe_allow_html=True)
    st.caption("Paste your personal RSS feed URLs below. (e.g., your Economist subscriber feed)")
    with st.expander("ℹ️ How to find RSS URLs"):
        st.caption(
            "Most publications hide RSS behind their settings. "
            "Search: **[Publication name] RSS feed URL**. "
            "For The Economist, log in → Account → RSS feeds. "
            "The URL must end in `.rss`, `.xml`, or similar."
        )
    user_rss_1 = st.text_input("Custom Feed #1 URL", value="", placeholder="https://...")
    user_rss_2 = st.text_input("Custom Feed #2 URL", value="", placeholder="https://...")
    user_rss_3 = st.text_input("Custom Feed #3 URL", value="", placeholder="https://...")

    st.markdown("---")
    st.markdown('<div class="section-header">🕐 Last Updated</div>', unsafe_allow_html=True)
    st.caption(datetime.now().strftime("%d %b %Y  %H:%M:%S"))


# =============================================================================
# MAIN CONTENT AREA
# =============================================================================

st.markdown('<div class="dash-title">INVESTMENT COMMAND CENTER</div>', unsafe_allow_html=True)
st.markdown('<div class="dash-subtitle">Bloomberg-style · Real-time · Professional Grade</div>', unsafe_allow_html=True)
st.markdown("---")

# =============================================================================
# SECTION TABS
# =============================================================================
tab_charts, tab_technicals, tab_breadth, tab_news, tab_calendar, tab_tv = st.tabs([
    "📈 Live Chart",
    "🔬 Technicals",
    "🌡️ Breadth",
    "📰 News",
    "📅 Calendar",
    "📺 TradingView",
])

# =============================================================================
# TAB 1 — TradingView Live Chart (moved here for primacy)
# =============================================================================
with tab_charts:
    st.markdown("#### TradingView Live Chart")
    tv_col1, tv_col2 = st.columns([2, 1])
    with tv_col1:
        tv_symbol = st.text_input(
            "Symbol (TradingView format)",
            value="NSE:NIFTY",
            help="Examples: NSE:NIFTY, NSE:RELIANCE, NASDAQ:AAPL, NYSE:TSLA",
            key="tv_sym"
        )
    with tv_col2:
        tv_interval = st.selectbox("Interval", ["D", "W", "60", "30", "15", "5", "1"], index=0, key="tv_int")

    tv_html = f"""
    <div class="tradingview-widget-container" style="height:600px;width:100%;">
      <div id="tradingview_chart" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
        new TradingView.widget({{
          "width": "100%",
          "height": 580,
          "symbol": "{tv_symbol}",
          "interval": "{tv_interval}",
          "timezone": "Asia/Kolkata",
          "theme": "dark",
          "style": "1",
          "locale": "en",
          "toolbar_bg": "#0d0d14",
          "enable_publishing": false,
          "allow_symbol_change": true,
          "hide_side_toolbar": false,
          "container_id": "tradingview_chart"
        }});
      </script>
    </div>
    """
    st.components.v1.html(tv_html, height=600)


# =============================================================================
# TAB 2 — Technical Intelligence Engine
# =============================================================================
with tab_technicals:
    st.markdown("#### Technical Intelligence Engine")
    st.caption("💡 Use `.NS` suffix for NSE stocks (e.g. `RELIANCE.NS`, `INFY.NS`). Global stocks: `AAPL`, `MSFT`.")

    tech_col1, tech_col2 = st.columns([3, 1])
    with tech_col1:
        tech_sym = st.text_input("Enter Ticker Symbol", value="^NSEI", key="tech_sym",
                                  placeholder="e.g. RELIANCE.NS, AAPL, ^NSEI")
    with tech_col2:
        tech_period = st.selectbox("History", ["6mo", "1y", "2y"], index=1, key="tech_period")

    if tech_sym:
        with st.spinner(f"Fetching data for {tech_sym.upper()}..."):
            df = fetch_ohlcv(tech_sym, period=tech_period)

        if df is None or df.empty:
            st.warning(f"⚠️ Could not fetch data for `{tech_sym}`. Check the symbol and try again.")
        else:
            close = df["Close"].squeeze()
            high = df["High"].squeeze()
            low = df["Low"].squeeze()
            open_ = df["Open"].squeeze()

            # Calculate indicators
            rsi = calc_rsi(close)
            macd_line, signal_line, histogram = calc_macd(close)
            ema200 = close.ewm(span=200, adjust=False).mean()
            bb_upper, bb_mid, bb_lower = calc_bollinger(close)

            # ── Chart ─────────────────────────────────────────────────────────
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                row_heights=[0.55, 0.25, 0.20],
                vertical_spacing=0.02,
                subplot_titles=(f"{tech_sym.upper()} · Price + Indicators", "MACD (12,26,9)", "RSI (14)"),
            )

            # Price candlesticks
            fig.add_trace(go.Candlestick(
                x=df.index, open=open_, high=high, low=low, close=close,
                name="Price",
                increasing_line_color=GREEN, decreasing_line_color=RED,
                increasing_fillcolor=GREEN, decreasing_fillcolor=RED,
                line_width=1, showlegend=False,
            ), row=1, col=1)

            # 200 EMA
            fig.add_trace(go.Scatter(
                x=df.index, y=ema200, name="200 EMA",
                line=dict(color="#ff9800", width=1.5, dash="solid"),
            ), row=1, col=1)

            # Bollinger Bands
            fig.add_trace(go.Scatter(
                x=df.index, y=bb_upper, name="BB Upper",
                line=dict(color="#7b61ff", width=1, dash="dot"),
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=df.index, y=bb_lower, name="BB Lower",
                line=dict(color="#7b61ff", width=1, dash="dot"),
                fill="tonexty", fillcolor="rgba(123,97,255,0.06)",
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=df.index, y=bb_mid, name="BB Mid",
                line=dict(color="#7b61ff", width=0.7, dash="dash"),
            ), row=1, col=1)

            # MACD
            colors_hist = [GREEN if v >= 0 else RED for v in histogram.fillna(0)]
            fig.add_trace(go.Bar(
                x=df.index, y=histogram, name="MACD Hist",
                marker_color=colors_hist, showlegend=False,
            ), row=2, col=1)
            fig.add_trace(go.Scatter(
                x=df.index, y=macd_line, name="MACD",
                line=dict(color=BLUE, width=1.5),
            ), row=2, col=1)
            fig.add_trace(go.Scatter(
                x=df.index, y=signal_line, name="Signal",
                line=dict(color=YELLOW, width=1.2),
            ), row=2, col=1)

            # RSI
            fig.add_trace(go.Scatter(
                x=df.index, y=rsi, name="RSI",
                line=dict(color="#00e5ff", width=1.5),
            ), row=3, col=1)
            fig.add_hline(y=70, line_color=RED, line_dash="dash", line_width=1, row=3, col=1)
            fig.add_hline(y=30, line_color=GREEN, line_dash="dash", line_width=1, row=3, col=1)
            fig.add_hrect(y0=70, y1=100, fillcolor=RED, opacity=0.04, row=3, col=1)
            fig.add_hrect(y0=0, y1=30, fillcolor=GREEN, opacity=0.04, row=3, col=1)

            layout = plotly_base_layout(height=620)
            layout.update(
                xaxis3=dict(gridcolor=PLOTLY_GRID, rangeslider_visible=False, showgrid=True),
                yaxis3=dict(gridcolor=PLOTLY_GRID, range=[0, 100], showgrid=True),
                xaxis_rangeslider_visible=False,
            )
            fig.update_layout(**layout)
            fig.update_xaxes(showgrid=True, gridcolor=PLOTLY_GRID)
            fig.update_yaxes(showgrid=True, gridcolor=PLOTLY_GRID)
            for annotation in fig.layout.annotations:
                annotation.font.size = 9
                annotation.font.color = "#4a5568"

            st.plotly_chart(fig, use_container_width=True)

            # ── Signal Summary ────────────────────────────────────────────────
            st.markdown("#### Signal Summary")
            last_rsi = rsi.iloc[-1] if not rsi.empty else None
            last_close = close.iloc[-1]
            last_ema200 = ema200.iloc[-1]
            last_macd = macd_line.iloc[-1]
            last_signal = signal_line.iloc[-1]
            prev_macd = macd_line.iloc[-2] if len(macd_line) > 1 else None
            prev_signal = signal_line.iloc[-2] if len(signal_line) > 1 else None
            last_bb_upper = bb_upper.iloc[-1]
            last_bb_lower = bb_lower.iloc[-1]

            signals = []

            # RSI signal
            if last_rsi is not None:
                if last_rsi > 70:
                    signals.append(("bearish", f"RSI is {last_rsi:.1f} → Overbought territory. Price may be stretched — consider caution on new longs."))
                elif last_rsi < 30:
                    signals.append(("bullish", f"RSI is {last_rsi:.1f} → Oversold territory. Potential bounce candidate — watch for reversal confirmation."))
                else:
                    signals.append(("neutral", f"RSI is {last_rsi:.1f} → Neutral zone (30–70). No extreme momentum signal at this time."))

            # 200 EMA signal
            if not np.isnan(last_ema200):
                if last_close > last_ema200:
                    signals.append(("bullish", f"Price ({last_close:,.2f}) is ABOVE 200 EMA ({last_ema200:,.2f}) → Long-term trend is bullish."))
                else:
                    signals.append(("bearish", f"Price ({last_close:,.2f}) is BELOW 200 EMA ({last_ema200:,.2f}) → Long-term trend is bearish."))

            # MACD crossover
            if prev_macd is not None and prev_signal is not None:
                if prev_macd <= prev_signal and last_macd > last_signal:
                    signals.append(("bullish", "MACD bullish crossover detected → MACD line crossed above signal line. Possible bullish momentum shift."))
                elif prev_macd >= prev_signal and last_macd < last_signal:
                    signals.append(("bearish", "MACD bearish crossover detected → MACD line crossed below signal line. Possible bearish momentum shift."))
                elif last_macd > 0:
                    signals.append(("bullish", f"MACD is positive ({last_macd:.3f}) → Bullish momentum continues. No crossover imminent."))
                else:
                    signals.append(("bearish", f"MACD is negative ({last_macd:.3f}) → Bearish momentum. Watch for crossover above zero."))

            # Bollinger Bands signal
            if not np.isnan(last_bb_upper) and not np.isnan(last_bb_lower):
                if last_close > last_bb_upper:
                    signals.append(("bearish", f"Price ({last_close:,.2f}) is ABOVE the upper Bollinger Band ({last_bb_upper:,.2f}) → Potential overextension / mean-reversion risk."))
                elif last_close < last_bb_lower:
                    signals.append(("bullish", f"Price ({last_close:,.2f}) is BELOW the lower Bollinger Band ({last_bb_lower:,.2f}) → Potential oversold / mean-reversion opportunity."))
                else:
                    signals.append(("neutral", f"Price is trading within Bollinger Bands — no breakout or breakdown signal."))

            # Render signals
            sig_cols = st.columns(2)
            for i, (stype, msg) in enumerate(signals):
                with sig_cols[i % 2]:
                    icon = "🟢" if stype == "bullish" else "🔴" if stype == "bearish" else "🟡"
                    st.markdown(
                        f'<div class="signal-box signal-{stype}">{icon} {msg}</div>',
                        unsafe_allow_html=True
                    )

            # ── Key stats row ─────────────────────────────────────────────────
            st.markdown("---")
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            sc1.metric("Last Close", fmt_price(last_close))
            sc2.metric("RSI (14)", f"{last_rsi:.1f}" if last_rsi else "N/A")
            sc3.metric("200 EMA", fmt_price(last_ema200))
            sc4.metric("BB Upper", fmt_price(last_bb_upper))
            sc5.metric("BB Lower", fmt_price(last_bb_lower))


# =============================================================================
# TAB 3 — Nifty 50 Market Breadth
# =============================================================================
with tab_breadth:
    st.markdown("#### Nifty 50 Market Breadth — % Above 50-Day SMA")
    st.caption("Data refreshes every hour. Fetching 50 tickers may take 15–30 seconds on first load.")

    with st.spinner("Calculating market breadth…"):
        breadth_df, pct_above = fetch_nifty50_breadth()

    # ── Gauge Chart ───────────────────────────────────────────────────────────
    gauge_color = GREEN if pct_above >= 60 else RED if pct_above <= 40 else YELLOW
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct_above,
        delta={"reference": 50, "valueformat": ".1f"},
        title={"text": "% Nifty 50 Stocks Above 50 SMA", "font": {"size": 13, "color": "#8899aa", "family": "JetBrains Mono"}},
        number={"suffix": "%", "font": {"size": 36, "color": gauge_color, "family": "JetBrains Mono"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#4a5568", "tickfont": {"size": 9}},
            "bar": {"color": gauge_color, "thickness": 0.25},
            "bgcolor": PLOTLY_PLOT_BG,
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": "rgba(255,23,68,0.12)"},
                {"range": [40, 60], "color": "rgba(255,214,0,0.08)"},
                {"range": [60, 100], "color": "rgba(0,200,83,0.12)"},
            ],
            "threshold": {"line": {"color": "#ffffff", "width": 2}, "thickness": 0.8, "value": pct_above},
        },
    ))
    fig_gauge.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=PLOTLY_PAPER_BG,
        plot_bgcolor=PLOTLY_PLOT_BG,
        height=260,
        margin=dict(l=20, r=20, t=40, b=10),
        font=dict(family="JetBrains Mono, monospace", color="#8899aa"),
    )

    gc1, gc2 = st.columns([1, 1])
    with gc1:
        st.plotly_chart(fig_gauge, use_container_width=True)
    with gc2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        above_n = (breadth_df["Above50SMA"] == True).sum()
        below_n = (breadth_df["Above50SMA"] == False).sum()
        err_n = breadth_df["Above50SMA"].isna().sum()
        st.metric("Stocks Above 50 SMA", f"{above_n} / {len(breadth_df)}")
        st.metric("Stocks Below 50 SMA", str(below_n))
        if err_n:
            st.caption(f"⚠️ {err_n} ticker(s) had data errors.")
        
        interp = ("🟢 Bullish breadth — majority of Nifty 50 stocks are in uptrend." if pct_above >= 60
                  else "🔴 Bearish breadth — majority of Nifty 50 stocks are in downtrend." if pct_above <= 40
                  else "🟡 Mixed breadth — market is at a crossroads (near 50% threshold).")
        st.markdown(f'<div class="signal-box">{interp}</div>', unsafe_allow_html=True)

    # ── Sortable Table ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### Individual Stock Status")

    filter_opt = st.radio("Filter", ["All", "Above 50 SMA", "Below 50 SMA"], horizontal=True)
    display_df = breadth_df.copy()
    if filter_opt == "Above 50 SMA":
        display_df = display_df[display_df["Above50SMA"] == True]
    elif filter_opt == "Below 50 SMA":
        display_df = display_df[display_df["Above50SMA"] == False]

    def color_status(val):
        if val == "Above 50 SMA":
            return "color: #00c853; font-weight: 600"
        elif val == "Below 50 SMA":
            return "color: #ff1744; font-weight: 600"
        return "color: #8899aa"

    styled = display_df[["Ticker", "Status"]].style.applymap(color_status, subset=["Status"])
    st.dataframe(styled, use_container_width=True, height=420, hide_index=True)


# =============================================================================
# TAB 4 — News Command Center
# =============================================================================
with tab_news:
    st.markdown("#### Geopolitical & Market News Command Center")

    GLOBAL_FEEDS = {
        "Reuters World News": "https://feeds.reuters.com/Reuters/worldNews",
        "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
        "Reuters Markets": "https://feeds.reuters.com/reuters/financialsNews",
        "Moneycontrol Markets": "https://www.moneycontrol.com/rss/marketreports.xml",
        "Economic Times Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    }

    news_tab1, news_tab2 = st.tabs(["🌐 Global Macro", "💼 My Portfolio News"])

    def render_news_items(items, source_override=None):
        if not items:
            st.warning("No items fetched. The feed may be unavailable or rate-limited.")
            return
        for item in items:
            src = source_override or item["source"]
            st.markdown(
                f"""<div class="news-card">
                    <div class="news-headline"><a href="{item['link']}" target="_blank" style="color:#00b4d8;text-decoration:none;">{item['title']}</a></div>
                    <div class="news-meta">📡 {src} &nbsp;·&nbsp; 🕐 {item['published']}</div>
                </div>""",
                unsafe_allow_html=True
            )

    with news_tab1:
        st.caption("Aggregating from Reuters, Moneycontrol, Economic Times, and more.")
        all_global = []
        with st.spinner("Fetching global news feeds…"):
            for src_name, url in GLOBAL_FEEDS.items():
                items = fetch_rss(url)
                for item in items:
                    item["source"] = src_name
                    all_global.append(item)
        # Sort by published string (best-effort)
        all_global.sort(key=lambda x: x.get("published", ""), reverse=True)
        for item in all_global[:40]:
            render_news_items([item])

    with news_tab2:
        user_feeds = {k: v for k, v in {
            "Custom Feed #1": user_rss_1,
            "Custom Feed #2": user_rss_2,
            "Custom Feed #3": user_rss_3,
        }.items() if v.strip()}

        if not user_feeds:
            st.info("📌 Enter your personal RSS feed URLs in the **sidebar** to see your curated news here.")
        else:
            all_user = []
            with st.spinner("Fetching your custom feeds…"):
                for label, url in user_feeds.items():
                    items = fetch_rss(url)
                    for item in items:
                        item["source"] = label
                        all_user.append(item)
            all_user.sort(key=lambda x: x.get("published", ""), reverse=True)
            if all_user:
                for item in all_user[:30]:
                    render_news_items([item])
            else:
                st.warning("⚠️ No items fetched from your custom feeds. Verify the URLs are valid RSS feeds.")


# =============================================================================
# TAB 5 — Economic Calendar
# =============================================================================
with tab_calendar:
    st.markdown("#### Economic Calendar — Major Events")
    st.caption(
        "📝 **How to update:** Edit the `events` list in `app.py` under `# ── CALENDAR DATA ──`. "
        "Add rows as `{'Date': 'DD Mon YYYY', 'Time': 'HH:MM IST', 'Event': '...', 'Country': '...', 'Impact': 'High/Medium/Low'}`."
    )

    # ── CALENDAR DATA ── (Update this list manually)
    events = [
        {"Date": "20 Mar 2025", "Time": "10:00 IST", "Event": "RBI Monetary Policy Decision", "Country": "🇮🇳 India", "Impact": "High"},
        {"Date": "19 Mar 2025", "Time": "23:30 IST", "Event": "US FOMC Rate Decision", "Country": "🇺🇸 USA", "Impact": "High"},
        {"Date": "20 Mar 2025", "Time": "18:30 IST", "Event": "US CPI Inflation (Feb)", "Country": "🇺🇸 USA", "Impact": "High"},
        {"Date": "28 Mar 2025", "Time": "18:30 IST", "Event": "US PCE Price Index (Feb)", "Country": "🇺🇸 USA", "Impact": "High"},
        {"Date": "31 Mar 2025", "Time": "17:30 IST", "Event": "India GDP Growth (Q3 FY25)", "Country": "🇮🇳 India", "Impact": "High"},
        {"Date": "04 Apr 2025", "Time": "18:30 IST", "Event": "US Non-Farm Payrolls (Mar)", "Country": "🇺🇸 USA", "Impact": "High"},
        {"Date": "07 Apr 2025", "Time": "18:30 IST", "Event": "US CPI Inflation (Mar)", "Country": "🇺🇸 USA", "Impact": "High"},
        {"Date": "09 Apr 2025", "Time": "18:30 IST", "Event": "US PPI (Mar)", "Country": "🇺🇸 USA", "Impact": "Medium"},
        {"Date": "09 Apr 2025", "Time": "18:00 IST", "Event": "ECB Rate Decision", "Country": "🇪🇺 EU", "Impact": "High"},
        {"Date": "30 Apr 2025", "Time": "20:30 IST", "Event": "US GDP Growth (Q1 2025 Advance)", "Country": "🇺🇸 USA", "Impact": "High"},
        {"Date": "07 May 2025", "Time": "10:00 IST", "Event": "RBI Monetary Policy Decision", "Country": "🇮🇳 India", "Impact": "High"},
        {"Date": "07 May 2025", "Time": "23:30 IST", "Event": "US FOMC Rate Decision", "Country": "🇺🇸 USA", "Impact": "High"},
        {"Date": "02 May 2025", "Time": "18:30 IST", "Event": "US Non-Farm Payrolls (Apr)", "Country": "🇺🇸 USA", "Impact": "High"},
        {"Date": "15 May 2025", "Time": "18:30 IST", "Event": "US CPI Inflation (Apr)", "Country": "🇺🇸 USA", "Impact": "High"},
        {"Date": "18 Jun 2025", "Time": "23:30 IST", "Event": "US FOMC Rate Decision", "Country": "🇺🇸 USA", "Impact": "High"},
        {"Date": "06 Aug 2025", "Time": "23:30 IST", "Event": "US FOMC Rate Decision", "Country": "🇺🇸 USA", "Impact": "High"},
        {"Date": "17 Sep 2025", "Time": "23:30 IST", "Event": "US FOMC Rate Decision", "Country": "🇺🇸 USA", "Impact": "High"},
        {"Date": "05 Nov 2025", "Time": "23:30 IST", "Event": "US FOMC Rate Decision", "Country": "🇺🇸 USA", "Impact": "High"},
        {"Date": "17 Dec 2025", "Time": "23:30 IST", "Event": "US FOMC Rate Decision", "Country": "🇺🇸 USA", "Impact": "High"},
    ]
    # ── END CALENDAR DATA ──

    cal_df = pd.DataFrame(events)

    def impact_color(val):
        if val == "High":
            return "color: #ff1744; font-weight: 700"
        elif val == "Medium":
            return "color: #ffd600; font-weight: 600"
        return "color: #00c853"

    # Filter controls
    cc1, cc2 = st.columns([1, 2])
    with cc1:
        impact_filter = st.multiselect("Impact Filter", ["High", "Medium", "Low"], default=["High", "Medium"])
    with cc2:
        country_filter = st.multiselect(
            "Country Filter",
            cal_df["Country"].unique().tolist(),
            default=cal_df["Country"].unique().tolist(),
        )

    filtered_cal = cal_df[
        cal_df["Impact"].isin(impact_filter) &
        cal_df["Country"].isin(country_filter)
    ]

    styled_cal = filtered_cal.style.applymap(impact_color, subset=["Impact"])
    st.dataframe(styled_cal, use_container_width=True, height=480, hide_index=True)

    # TradingView Economic Calendar embed as bonus
    st.markdown("---")
    with st.expander("📅 TradingView Economic Calendar (Live)"):
        tv_cal_html = """
        <div class="tradingview-widget-container">
          <iframe src="https://s.tradingview.com/embed-widget/events/?locale=en#%7B%22colorTheme%22%3A%22dark%22%2C%22isTransparent%22%3Atrue%2C%22width%22%3A%22100%25%22%2C%22height%22%3A%22450%22%2C%22importanceFilter%22%3A%22-1%2C0%2C1%22%2C%22countryFilter%22%3A%22in%2Cus%2Ceu%22%7D"
            style="width:100%;height:450px;border:none;"
            allowtransparency="true">
          </iframe>
        </div>
        """
        st.components.v1.html(tv_cal_html, height=460)


# =============================================================================
# TAB 6 — TradingView (duplicate placed here for navigation convenience)
# =============================================================================
with tab_tv:
    st.markdown("#### Advanced TradingView Widget")
    st.caption("Full-featured TradingView chart with drawing tools, indicators, and real-time data.")

    tv2_sym = st.text_input(
        "Symbol", value="NSE:NIFTY", key="tv2_sym",
        help="Examples: NSE:NIFTY, BSE:SENSEX, NASDAQ:AAPL, COMEX:GC1!, NYMEX:CL1!"
    )
    tv2_html = f"""
    <div class="tradingview-widget-container" style="height:700px;width:100%;">
      <div id="tradingview_adv" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
        new TradingView.widget({{
          "width": "100%",
          "height": 680,
          "symbol": "{tv2_sym}",
          "interval": "D",
          "timezone": "Asia/Kolkata",
          "theme": "dark",
          "style": "1",
          "locale": "en",
          "toolbar_bg": "#0d0d14",
          "enable_publishing": false,
          "withdateranges": true,
          "hide_side_toolbar": false,
          "allow_symbol_change": true,
          "studies": ["RSI@tv-basicstudies", "MACD@tv-basicstudies", "BB@tv-basicstudies"],
          "container_id": "tradingview_adv",
          "show_popup_button": true,
          "popup_width": "1000",
          "popup_height": "650"
        }});
      </script>
    </div>
    """
    st.components.v1.html(tv2_html, height=700)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown(
    '<div style="text-align:center; font-family:\'JetBrains Mono\',monospace; font-size:0.62rem; color:#2a3040;">'
    "📊 INVESTMENT DASHBOARD · For personal research only. Not financial advice. "
    "Data via yfinance / TradingView / RSS. Prices may be delayed 15–20 min."
    "</div>",
    unsafe_allow_html=True
)
