# =============================================================================
# TERMINAL — Investment Dashboard
# Author: Generated for personal use
# =============================================================================
# FUTURE ENHANCEMENTS (not yet built):
#   - Fear & Greed Gauge: Map India VIX to 0-100 sentiment gauge
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
from datetime import datetime
import warnings
import requests
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
    page_title="TERMINAL",
    page_icon="⬛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# PLOTLY THEME — Light
# =============================================================================
PLOTLY_TEMPLATE  = "plotly_white"
PLOTLY_PAPER_BG  = "#f8f9fb"
PLOTLY_PLOT_BG   = "#ffffff"
PLOTLY_GRID      = "#e8ecf0"
GREEN            = "#16a34a"
RED              = "#dc2626"
BLUE             = "#0057b8"
YELLOW           = "#d97706"

# =============================================================================
# GLOBAL CSS — Professional Light Theme
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

    /* ── Base ── */
    .stApp { background-color: #f4f6f9; color: #1a202c; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    [data-testid="stHeader"] { background-color: #ffffff; border-bottom: 1px solid #e2e8f0; }

    /* ── Push main content below the sticky ticker bar ── */
    [data-testid="stAppViewContainer"] > .main > .block-container {
        padding-top: 70px !important;
    }

    /* ── Sticky ticker bar ── */
    #ticker-bar-wrapper {
        position: fixed;
        top: 58px;
        left: 0;
        right: 0;
        z-index: 998;
        background: #ffffff;
        border-bottom: 2px solid #e2e8f0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        padding: 0 16px;
        height: 46px;
        display: flex;
        align-items: center;
        gap: 0;
        overflow-x: auto;
        scrollbar-width: none;
    }
    #ticker-bar-wrapper::-webkit-scrollbar { display: none; }

    .ticker-live-dot {
        width: 7px; height: 7px; border-radius: 50%; background: #16a34a;
        animation: pulse 1.6s infinite;
        flex-shrink: 0;
        margin-right: 10px;
    }
    @keyframes pulse {
        0%,100% { opacity: 1; transform: scale(1); }
        50%      { opacity: 0.4; transform: scale(0.85); }
    }

    .ticker-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 0 18px;
        border-right: 1px solid #e8ecf0;
        line-height: 1.2;
        flex-shrink: 0;
        cursor: default;
    }
    .ticker-item:last-child { border-right: none; }
    .ticker-name {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.58rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .ticker-price {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        font-weight: 700;
        color: #1e293b;
    }
    .ticker-chg {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        font-weight: 600;
    }
    .ticker-chg.up   { color: #16a34a; }
    .ticker-chg.down { color: #dc2626; }
    .ticker-chg.flat { color: #64748b; }

    /* ── Metric cards ── */
    [data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    [data-testid="stMetricLabel"] { font-size: 0.65rem !important; color: #64748b !important; text-transform: uppercase; letter-spacing: 0.08em; }
    [data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; font-size: 1.05rem !important; color: #1e293b !important; }
    [data-testid="stMetricDelta"] { font-family: 'JetBrains Mono', monospace !important; font-size: 0.72rem !important; }

    /* ── Section headers ── */
    .section-header {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.58rem;
        letter-spacing: 0.14em;
        color: #94a3b8;
        text-transform: uppercase;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 4px;
        margin: 14px 0 8px 0;
    }

    /* ── Signal boxes ── */
    .signal-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 3px solid #0057b8;
        border-radius: 0 8px 8px 0;
        padding: 10px 14px;
        margin: 6px 0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #334155;
    }
    .signal-bullish { border-left-color: #16a34a; background: #f0fdf4; }
    .signal-bearish { border-left-color: #dc2626; background: #fff5f5; }
    .signal-neutral { border-left-color: #d97706; background: #fffbeb; }

    /* ── News cards ── */
    .news-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px 14px;
        margin: 5px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .news-headline { font-weight: 600; font-size: 0.87rem; color: #1e293b; }
    .news-meta { font-size: 0.7rem; color: #94a3b8; margin-top: 3px; font-family: 'JetBrains Mono', monospace; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] { background: #f4f6f9; gap: 6px; border-radius: 8px; padding: 5px 6px; }
    .stTabs [data-baseweb="tab"] { background: transparent; border: none; border-radius: 6px; color: #64748b; font-size: 0.82rem; font-family: 'Inter', sans-serif; padding: 6px 18px !important; }
    .stTabs [aria-selected="true"] { background: #ffffff !important; color: #0057b8 !important; font-weight: 600; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }

    /* ── Buttons ── */
    .stButton button { background: #ffffff; border: 1px solid #e2e8f0; color: #475569; font-size: 0.78rem; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
    .stButton button:hover { background: #f1f5f9; border-color: #0057b8; color: #0057b8; }

    /* ── Table ── */
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 8px; background: #ffffff; }

    /* ── Inputs / Selectbox ── */
    .stSelectbox > div > div, .stTextInput > div > div { background: #ffffff !important; border-color: #e2e8f0 !important; color: #1e293b !important; }

    /* ── Dashboard title ── */
    .dash-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.4rem;
        font-weight: 700;
        color: #0057b8;
        letter-spacing: 0.08em;
    }
    .dash-subtitle {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem;
        color: #94a3b8;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    /* ── Misc ── */
    div[data-testid="stHorizontalBlock"] { gap: 12px; }
    hr { border-color: #e2e8f0; }
    .stMarkdown p { color: #334155; }
    .stCaption { color: #94a3b8 !important; }

    /* ── Expander ── */
    [data-testid="stExpander"] { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; }

    /* ── Info/Warning/Success boxes ── */
    [data-testid="stAlert"] { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

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


@st.cache_data(ttl=60)
def fetch_ticker_snapshot(symbol):
    """Fetch current price and daily % change for a single ticker."""
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


@st.cache_data(ttl=60)
def fetch_ticker_bar_batch():
    """
    Batch-fetch all 10 ticker-bar symbols in one call for efficiency.
    MCX Gold/Silver/Copper: yfinance does not support MCX exchange directly.
    GC=F (COMEX Gold), SI=F (Silver), HG=F (Copper) are the closest
    international proxies and track MCX prices very closely.
    """
    TICKER_BAR_SYMBOLS = {
        "NIFTY 50":   "^NSEI",
        "BANK NIFTY": "^NSEBANK",
        "SENSEX":     "^BSESN",
        "SPX":        "^GSPC",
        "BTC":        "BTC-USD",
        "GOLD":       "GC=F",       # COMEX proxy — tracks MCX gold closely
        "SILVER":     "SI=F",       # COMEX proxy
        "COPPER":     "HG=F",       # COMEX proxy
        "USD/INR":    "USDINR=X",
        "EUR/USD":    "EURUSD=X",
    }
    results = {}
    for label, sym in TICKER_BAR_SYMBOLS.items():
        price, chg = fetch_ticker_snapshot(sym)
        results[label] = {"price": price, "chg": chg, "sym": sym}
    return results


@st.cache_data(ttl=300)
def fetch_ohlcv(symbol, period="1y", interval="1d"):
    """Fetch OHLCV data for a given symbol."""
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
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
    return sma + std_dev * std, sma, sma - std_dev * std


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
                    status, above = "Insufficient data", None
                else:
                    sma50 = s.rolling(50).mean().iloc[-1]
                    above = bool(s.iloc[-1] > sma50)
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
    """Fetch and parse an RSS feed. Returns items sorted newest-first."""
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:25]:
            pub = entry.get("published", entry.get("updated", ""))
            pub_dt = None
            try:
                from email.utils import parsedate_to_datetime
                pub_dt = parsedate_to_datetime(pub)
                pub_str = pub_dt.strftime("%d %b %Y  %H:%M")
            except Exception:
                pub_str = pub[:20] if pub else "–"
            items.append({
                "title":    entry.get("title", "No title"),
                "link":     entry.get("link", "#"),
                "published": pub_str,
                "pub_dt":   pub_dt,          # sortable datetime object
                "source":   feed.feed.get("title", url),
            })
        # Sort newest-first within each feed
        items.sort(key=lambda x: x["pub_dt"] or datetime.min, reverse=True)
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
        font=dict(family="JetBrains Mono, monospace", size=10, color="#475569"),
        xaxis=dict(gridcolor=PLOTLY_GRID, showgrid=True, zeroline=False),
        yaxis=dict(gridcolor=PLOTLY_GRID, showgrid=True, zeroline=False),
        legend=dict(bgcolor="rgba(255,255,255,0.8)", font=dict(size=9), bordercolor="#e2e8f0", borderwidth=1),
        hovermode="x unified",
    )


# =============================================================================
# STICKY TICKER BAR
# =============================================================================
ticker_data = fetch_ticker_bar_batch()

ticker_items_html = '<div class="ticker-live-dot"></div>'
for label, data in ticker_data.items():
    price  = data["price"]
    chg    = data["chg"]

    # Format price — use more decimals for FX pairs
    if price is None or (isinstance(price, float) and np.isnan(price)):
        price_str = "—"
    elif label in ("EUR/USD",):
        price_str = f"{price:,.4f}"
    elif label in ("USD/INR",):
        price_str = f"{price:,.2f}"
    elif label in ("BTC",):
        price_str = f"{price:,.0f}"
    else:
        price_str = f"{price:,.2f}"

    # Format change
    if chg is None or (isinstance(chg, float) and np.isnan(chg)):
        chg_str, chg_cls = "—", "flat"
    elif chg > 0:
        chg_str, chg_cls = f"+{chg:.2f}%", "up"
    elif chg < 0:
        chg_str, chg_cls = f"{chg:.2f}%", "down"
    else:
        chg_str, chg_cls = "0.00%", "flat"

    ticker_items_html += f"""
    <div class="ticker-item">
        <span class="ticker-name">{label}</span>
        <span class="ticker-price">{price_str}</span>
        <span class="ticker-chg {chg_cls}">{chg_str}</span>
    </div>"""

st.markdown(
    f'<div id="ticker-bar-wrapper">{ticker_items_html}</div>',
    unsafe_allow_html=True,
)

# ── Sidebar-aware sticky bar: shift left margin dynamically ──────────────────
st.components.v1.html("""
<script>
(function() {
  // Streamlit renders inside an iframe; we need to reach the parent document
  var doc = window.parent.document;

  function getSidebarWidth() {
    var sb = doc.querySelector('[data-testid="stSidebar"]');
    if (!sb) return 0;
    var style = window.parent.getComputedStyle(sb);
    // If sidebar is collapsed its width collapses to ~0 or it gets aria-expanded=false
    var expanded = sb.getAttribute('aria-expanded');
    if (expanded === 'false') return 0;
    // measure actual rendered width
    return sb.getBoundingClientRect().width || 0;
  }

  function updateTickerBar() {
    var bar = doc.getElementById('ticker-bar-wrapper');
    if (!bar) return;
    var w = getSidebarWidth();
    bar.style.left = w + 'px';
    bar.style.transition = 'left 0.3s ease';
  }

  // Run immediately
  updateTickerBar();

  // Watch for sidebar expand/collapse via MutationObserver
  var sidebar = doc.querySelector('[data-testid="stSidebar"]');
  if (sidebar) {
    var mo = new MutationObserver(updateTickerBar);
    mo.observe(sidebar, { attributes: true, attributeFilter: ['aria-expanded', 'style', 'class'] });
  }

  // Also watch for any DOM resize (window resize covers mobile rotations)
  window.parent.addEventListener('resize', updateTickerBar);

  // Poll every 300ms for the first 5 seconds to catch late renders
  var count = 0;
  var poll = setInterval(function() {
    updateTickerBar();
    if (++count > 16) clearInterval(poll);
  }, 300);
})();
</script>
""", height=0)

# =============================================================================
# SIDEBAR — Controls + Mini Market Ticker
# =============================================================================
with st.sidebar:
    st.markdown('<div class="dash-title">⬛ TERMINAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-subtitle">Markets · Data · Intelligence</div>', unsafe_allow_html=True)
    st.markdown("---")

    # ── Auto Refresh ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">⟳ Auto Refresh</div>', unsafe_allow_html=True)
    refresh_map = {"Off": 0, "1 min": 60_000, "5 min": 300_000, "15 min": 900_000}
    refresh_sel = st.selectbox("Interval", list(refresh_map.keys()), index=1, label_visibility="collapsed")

    if AUTOREFRESH_AVAILABLE and refresh_map[refresh_sel] > 0:
        st_autorefresh(interval=refresh_map[refresh_sel], key="autorefresh")
    elif not AUTOREFRESH_AVAILABLE and refresh_map[refresh_sel] > 0:
        st.caption("⚠️ Install `streamlit-autorefresh` for auto-refresh.")

    col_r1, _ = st.columns(2)
    with col_r1:
        if st.button("↺ Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")

    # ── Indian Indices ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🇮🇳 Indian Indices</div>', unsafe_allow_html=True)
    for label, sym in {"Nifty 50": "^NSEI", "Sensex": "^BSESN", "Bank Nifty": "^NSEBANK", "India VIX": "^INDIAVIX"}.items():
        price, chg = fetch_ticker_snapshot(sym)
        st.metric(label=label, value=fmt_price(price), delta=fmt_pct(chg))

    # ── Commodities ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🪙 Commodities</div>', unsafe_allow_html=True)
    for label, sym in {"Gold ($/oz)": "GC=F", "Silver ($/oz)": "SI=F", "Brent Crude": "BZ=F"}.items():
        price, chg = fetch_ticker_snapshot(sym)
        st.metric(label=label, value=fmt_price(price), delta=fmt_pct(chg))

    # ── US Markets ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🇺🇸 US Markets</div>', unsafe_allow_html=True)
    for label, sym in {"S&P 500": "^GSPC", "Nasdaq 100": "^IXIC", "Dow Jones": "^DJI", "Russell 2000": "^RUT"}.items():
        price, chg = fetch_ticker_snapshot(sym)
        st.metric(label=label, value=fmt_price(price), delta=fmt_pct(chg))

    # ── European Indices ───────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🇪🇺 Europe</div>', unsafe_allow_html=True)
    for label, sym in {"DAX (Germany)": "^GDAXI", "FTSE 100 (UK)": "^FTSE", "CAC 40 (France)": "^FCHI"}.items():
        price, chg = fetch_ticker_snapshot(sym)
        st.metric(label=label, value=fmt_price(price), delta=fmt_pct(chg))

    # ── Asian Indices ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🌏 Asia</div>', unsafe_allow_html=True)
    for label, sym in {"Nikkei 225 (JP)": "^N225", "Hang Seng (HK)": "^HSI", "Kospi (Korea)": "^KS11"}.items():
        price, chg = fetch_ticker_snapshot(sym)
        st.metric(label=label, value=fmt_price(price), delta=fmt_pct(chg))

    st.markdown("---")

    # ── Portfolio News RSS inputs ──────────────────────────────────────────────
    st.markdown('<div class="section-header">📰 My News Sources</div>', unsafe_allow_html=True)
    st.caption("Paste your personal RSS feed URLs below.")
    with st.expander("ℹ️ How to find RSS URLs"):
        st.caption(
            "Search **[Publication name] RSS feed URL**. "
            "For The Economist, log in → Account → RSS feeds. "
            "URL must end in `.rss` or `.xml`."
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
st.markdown('<div class="dash-title">TERMINAL</div>', unsafe_allow_html=True)
st.markdown('<div class="dash-subtitle">Markets. Data. Edge.</div>', unsafe_allow_html=True)
st.markdown("---")

# =============================================================================
# SECTION TABS
# =============================================================================
tab_tv, tab_technicals, tab_breadth, tab_news, tab_calendar, tab_twitter, tab_holdings = st.tabs([
    "📈 Chart",
    "🔬 Technicals",
    "🌡️ Breadth",
    "📰 News",
    "📅 Calendar",
    "📬 Channels",
    "💼 Portfolio",
])

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
            high  = df["High"].squeeze()
            low   = df["Low"].squeeze()
            open_ = df["Open"].squeeze()

            rsi                         = calc_rsi(close)
            macd_line, signal_line, histogram = calc_macd(close)
            ema200                      = close.ewm(span=200, adjust=False).mean()
            bb_upper, bb_mid, bb_lower  = calc_bollinger(close)

            # ── Chart ─────────────────────────────────────────────────────────
            fig = make_subplots(
                rows=3, cols=1, shared_xaxes=True,
                row_heights=[0.55, 0.25, 0.20], vertical_spacing=0.02,
                subplot_titles=(f"{tech_sym.upper()} · Price + Indicators", "MACD (12,26,9)", "RSI (14)"),
            )

            fig.add_trace(go.Candlestick(
                x=df.index, open=open_, high=high, low=low, close=close,
                name="Price",
                increasing_line_color=GREEN, decreasing_line_color=RED,
                increasing_fillcolor=GREEN, decreasing_fillcolor=RED,
                line_width=1, showlegend=False,
            ), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=ema200, name="200 EMA",
                line=dict(color="#d97706", width=1.5)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=bb_upper, name="BB Upper",
                line=dict(color="#7c3aed", width=1, dash="dot")), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=bb_lower, name="BB Lower",
                line=dict(color="#7c3aed", width=1, dash="dot"),
                fill="tonexty", fillcolor="rgba(124,58,237,0.05)"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=bb_mid, name="BB Mid",
                line=dict(color="#7c3aed", width=0.7, dash="dash")), row=1, col=1)

            colors_hist = [GREEN if v >= 0 else RED for v in histogram.fillna(0)]
            fig.add_trace(go.Bar(x=df.index, y=histogram, name="MACD Hist",
                marker_color=colors_hist, showlegend=False), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=macd_line, name="MACD",
                line=dict(color=BLUE, width=1.5)), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=signal_line, name="Signal",
                line=dict(color=YELLOW, width=1.2)), row=2, col=1)

            fig.add_trace(go.Scatter(x=df.index, y=rsi, name="RSI",
                line=dict(color="#0891b2", width=1.5)), row=3, col=1)
            fig.add_hline(y=70, line_color=RED,   line_dash="dash", line_width=1, row=3, col=1)
            fig.add_hline(y=30, line_color=GREEN, line_dash="dash", line_width=1, row=3, col=1)
            fig.add_hrect(y0=70, y1=100, fillcolor=RED,   opacity=0.03, row=3, col=1)
            fig.add_hrect(y0=0,  y1=30,  fillcolor=GREEN, opacity=0.03, row=3, col=1)

            layout = plotly_base_layout(height=620)
            layout.update(
                xaxis3=dict(gridcolor=PLOTLY_GRID, rangeslider_visible=False),
                yaxis3=dict(gridcolor=PLOTLY_GRID, range=[0, 100]),
                xaxis_rangeslider_visible=False,
            )
            fig.update_layout(**layout)
            fig.update_xaxes(showgrid=True, gridcolor=PLOTLY_GRID)
            fig.update_yaxes(showgrid=True, gridcolor=PLOTLY_GRID)
            for ann in fig.layout.annotations:
                ann.font.size = 9
                ann.font.color = "#64748b"

            st.plotly_chart(fig, use_container_width=True)

            # ── Signal Summary ────────────────────────────────────────────────
            st.markdown("#### Signal Summary")
            last_rsi    = rsi.iloc[-1] if not rsi.empty else None
            last_close  = close.iloc[-1]
            last_ema200 = ema200.iloc[-1]
            last_macd   = macd_line.iloc[-1]
            last_signal = signal_line.iloc[-1]
            prev_macd   = macd_line.iloc[-2] if len(macd_line) > 1 else None
            prev_signal = signal_line.iloc[-2] if len(signal_line) > 1 else None
            last_bb_upper = bb_upper.iloc[-1]
            last_bb_lower = bb_lower.iloc[-1]

            signals = []
            if last_rsi is not None:
                if last_rsi > 70:
                    signals.append(("bearish", f"RSI is {last_rsi:.1f} → Overbought. Consider caution on new longs."))
                elif last_rsi < 30:
                    signals.append(("bullish", f"RSI is {last_rsi:.1f} → Oversold. Watch for reversal confirmation."))
                else:
                    signals.append(("neutral", f"RSI is {last_rsi:.1f} → Neutral zone (30–70)."))

            if not np.isnan(last_ema200):
                if last_close > last_ema200:
                    signals.append(("bullish", f"Price ({last_close:,.2f}) ABOVE 200 EMA ({last_ema200:,.2f}) → Long-term uptrend."))
                else:
                    signals.append(("bearish", f"Price ({last_close:,.2f}) BELOW 200 EMA ({last_ema200:,.2f}) → Long-term downtrend."))

            if prev_macd is not None and prev_signal is not None:
                if prev_macd <= prev_signal and last_macd > last_signal:
                    signals.append(("bullish", "MACD bullish crossover → Crossed above signal line. Possible momentum shift up."))
                elif prev_macd >= prev_signal and last_macd < last_signal:
                    signals.append(("bearish", "MACD bearish crossover → Crossed below signal line. Possible momentum shift down."))
                elif last_macd > 0:
                    signals.append(("bullish", f"MACD positive ({last_macd:.3f}) → Bullish momentum continues."))
                else:
                    signals.append(("bearish", f"MACD negative ({last_macd:.3f}) → Bearish momentum."))

            if not np.isnan(last_bb_upper) and not np.isnan(last_bb_lower):
                if last_close > last_bb_upper:
                    signals.append(("bearish", f"Price ({last_close:,.2f}) ABOVE upper Bollinger Band → Overextension risk."))
                elif last_close < last_bb_lower:
                    signals.append(("bullish", f"Price ({last_close:,.2f}) BELOW lower Bollinger Band → Oversold / mean-reversion opportunity."))
                else:
                    signals.append(("neutral", "Price within Bollinger Bands — no breakout/breakdown signal."))

            sig_cols = st.columns(2)
            for i, (stype, msg) in enumerate(signals):
                with sig_cols[i % 2]:
                    icon = "🟢" if stype == "bullish" else "🔴" if stype == "bearish" else "🟡"
                    st.markdown(f'<div class="signal-box signal-{stype}">{icon} {msg}</div>', unsafe_allow_html=True)

            st.markdown("---")
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            sc1.metric("Last Close",  fmt_price(last_close))
            sc2.metric("RSI (14)",    f"{last_rsi:.1f}" if last_rsi else "N/A")
            sc3.metric("200 EMA",     fmt_price(last_ema200))
            sc4.metric("BB Upper",    fmt_price(last_bb_upper))
            sc5.metric("BB Lower",    fmt_price(last_bb_lower))


# =============================================================================
# TAB 3 — Nifty 50 Market Breadth
# =============================================================================
with tab_breadth:
    st.markdown("#### Nifty 50 Market Breadth — % Above 50-Day SMA")
    st.caption("Data refreshes every hour. First load may take 15–30 seconds.")

    with st.spinner("Calculating market breadth…"):
        breadth_df, pct_above = fetch_nifty50_breadth()

    gauge_color = GREEN if pct_above >= 60 else RED if pct_above <= 40 else YELLOW
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct_above,
        delta={"reference": 50, "valueformat": ".1f"},
        title={"text": "% Nifty 50 Stocks Above 50 SMA", "font": {"size": 13, "color": "#64748b", "family": "JetBrains Mono"}},
        number={"suffix": "%", "font": {"size": 36, "color": gauge_color, "family": "JetBrains Mono"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94a3b8", "tickfont": {"size": 9}},
            "bar": {"color": gauge_color, "thickness": 0.25},
            "bgcolor": PLOTLY_PLOT_BG,
            "borderwidth": 1, "bordercolor": "#e2e8f0",
            "steps": [
                {"range": [0,  40],  "color": "rgba(220,38,38,0.08)"},
                {"range": [40, 60],  "color": "rgba(217,119,6,0.06)"},
                {"range": [60, 100], "color": "rgba(22,163,74,0.08)"},
            ],
            "threshold": {"line": {"color": "#1e293b", "width": 2}, "thickness": 0.8, "value": pct_above},
        },
    ))
    fig_gauge.update_layout(
        template=PLOTLY_TEMPLATE, paper_bgcolor=PLOTLY_PAPER_BG, plot_bgcolor=PLOTLY_PLOT_BG,
        height=260, margin=dict(l=20, r=20, t=40, b=10),
        font=dict(family="JetBrains Mono, monospace", color="#475569"),
    )

    gc1, gc2 = st.columns([1, 1])
    with gc1:
        st.plotly_chart(fig_gauge, use_container_width=True)
    with gc2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        above_n = (breadth_df["Above50SMA"] == True).sum()
        below_n = (breadth_df["Above50SMA"] == False).sum()
        err_n   = breadth_df["Above50SMA"].isna().sum()
        st.metric("Stocks Above 50 SMA", f"{above_n} / {len(breadth_df)}")
        st.metric("Stocks Below 50 SMA", str(below_n))
        if err_n:
            st.caption(f"⚠️ {err_n} ticker(s) had data errors.")
        interp = ("🟢 Bullish breadth — majority in uptrend." if pct_above >= 60
                  else "🔴 Bearish breadth — majority in downtrend." if pct_above <= 40
                  else "🟡 Mixed breadth — market at crossroads.")
        st.markdown(f'<div class="signal-box">{interp}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("##### Individual Stock Status")
    filter_opt = st.radio("Filter", ["All", "Above 50 SMA", "Below 50 SMA"], horizontal=True)
    display_df = breadth_df.copy()
    if filter_opt == "Above 50 SMA":
        display_df = display_df[display_df["Above50SMA"] == True]
    elif filter_opt == "Below 50 SMA":
        display_df = display_df[display_df["Above50SMA"] == False]

    def color_status(val):
        if val == "Above 50 SMA":  return "color: #16a34a; font-weight: 600"
        elif val == "Below 50 SMA": return "color: #dc2626; font-weight: 600"
        return "color: #94a3b8"

    st.dataframe(
        display_df[["Ticker", "Status"]].style.applymap(color_status, subset=["Status"]),
        use_container_width=True, height=420, hide_index=True
    )


# =============================================================================
# TAB 4 — News Command Center
# =============================================================================
with tab_news:
    st.markdown("#### 📡 Market Pulse — Latest News")

    GLOBAL_FEEDS = {
        "Reuters World News":   "https://feeds.reuters.com/Reuters/worldNews",
        "Reuters Business":     "https://feeds.reuters.com/reuters/businessNews",
        "Reuters Markets":      "https://feeds.reuters.com/reuters/financialsNews",
        "Moneycontrol Markets": "https://www.moneycontrol.com/rss/marketreports.xml",
        "Economic Times Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    }

    news_tab1, news_tab2 = st.tabs(["🌐 Global Macro", "💼 My Portfolio News"])

    def render_news_items(items):
        if not items:
            st.warning("No items fetched. Feed may be unavailable.")
            return
        for item in items:
            st.markdown(
                f"""<div class="news-card">
                    <div class="news-headline"><a href="{item['link']}" target="_blank"
                        style="color:#0057b8;text-decoration:none;">{item['title']}</a></div>
                    <div class="news-meta">📡 {item['source']} &nbsp;·&nbsp; 🕐 {item['published']}</div>
                </div>""",
                unsafe_allow_html=True
            )

    with news_tab1:
        st.caption("Aggregating from Reuters, Moneycontrol, Economic Times.")
        all_global = []
        with st.spinner("Fetching global news feeds…"):
            for src_name, url in GLOBAL_FEEDS.items():
                for item in fetch_rss(url):
                    item["source"] = src_name
                    all_global.append(item)
        all_global.sort(key=lambda x: x.get("pub_dt") or datetime.min, reverse=True)
        render_news_items(all_global[:40])

    with news_tab2:
        user_feeds = {k: v for k, v in {
            "Custom Feed #1": user_rss_1,
            "Custom Feed #2": user_rss_2,
            "Custom Feed #3": user_rss_3,
        }.items() if v.strip()}

        if not user_feeds:
            st.info("📌 Enter your personal RSS feed URLs in the **sidebar** to see curated news here.")
        else:
            all_user = []
            with st.spinner("Fetching your custom feeds…"):
                for label, url in user_feeds.items():
                    for item in fetch_rss(url):
                        item["source"] = label
                        all_user.append(item)
            all_user.sort(key=lambda x: x.get("pub_dt") or datetime.min, reverse=True)
            if all_user:
                render_news_items(all_user[:30])
            else:
                st.warning("⚠️ No items fetched. Verify the URLs are valid RSS feeds.")


# =============================================================================
# TAB 5 — Economic Calendar
# =============================================================================
with tab_calendar:
    st.markdown("#### Economic Calendar — Major Events")
    st.caption(
        "📝 **How to update:** Edit the `events` list in `app.py` under `# ── CALENDAR DATA ──`. "
        "Add rows as `{'Date': 'DD Mon YYYY', 'Time': 'HH:MM IST', 'Event': '...', 'Country': '...', 'Impact': 'High/Medium/Low'}`."
    )

    # ── CALENDAR DATA ── (Update this list manually when dates change)
    events = [
        {"Date": "20 Mar 2025", "Time": "10:00 IST", "Event": "RBI Monetary Policy Decision",       "Country": "🇮🇳 India", "Impact": "High"},
        {"Date": "19 Mar 2025", "Time": "23:30 IST", "Event": "US FOMC Rate Decision",              "Country": "🇺🇸 USA",   "Impact": "High"},
        {"Date": "20 Mar 2025", "Time": "18:30 IST", "Event": "US CPI Inflation (Feb)",             "Country": "🇺🇸 USA",   "Impact": "High"},
        {"Date": "28 Mar 2025", "Time": "18:30 IST", "Event": "US PCE Price Index (Feb)",           "Country": "🇺🇸 USA",   "Impact": "High"},
        {"Date": "31 Mar 2025", "Time": "17:30 IST", "Event": "India GDP Growth (Q3 FY25)",         "Country": "🇮🇳 India", "Impact": "High"},
        {"Date": "04 Apr 2025", "Time": "18:30 IST", "Event": "US Non-Farm Payrolls (Mar)",         "Country": "🇺🇸 USA",   "Impact": "High"},
        {"Date": "07 Apr 2025", "Time": "18:30 IST", "Event": "US CPI Inflation (Mar)",             "Country": "🇺🇸 USA",   "Impact": "High"},
        {"Date": "09 Apr 2025", "Time": "18:30 IST", "Event": "US PPI (Mar)",                       "Country": "🇺🇸 USA",   "Impact": "Medium"},
        {"Date": "09 Apr 2025", "Time": "18:00 IST", "Event": "ECB Rate Decision",                  "Country": "🇪🇺 EU",    "Impact": "High"},
        {"Date": "30 Apr 2025", "Time": "20:30 IST", "Event": "US GDP Growth (Q1 2025 Advance)",    "Country": "🇺🇸 USA",   "Impact": "High"},
        {"Date": "07 May 2025", "Time": "10:00 IST", "Event": "RBI Monetary Policy Decision",       "Country": "🇮🇳 India", "Impact": "High"},
        {"Date": "07 May 2025", "Time": "23:30 IST", "Event": "US FOMC Rate Decision",              "Country": "🇺🇸 USA",   "Impact": "High"},
        {"Date": "02 May 2025", "Time": "18:30 IST", "Event": "US Non-Farm Payrolls (Apr)",         "Country": "🇺🇸 USA",   "Impact": "High"},
        {"Date": "15 May 2025", "Time": "18:30 IST", "Event": "US CPI Inflation (Apr)",             "Country": "🇺🇸 USA",   "Impact": "High"},
        {"Date": "18 Jun 2025", "Time": "23:30 IST", "Event": "US FOMC Rate Decision",              "Country": "🇺🇸 USA",   "Impact": "High"},
        {"Date": "06 Aug 2025", "Time": "23:30 IST", "Event": "US FOMC Rate Decision",              "Country": "🇺🇸 USA",   "Impact": "High"},
        {"Date": "17 Sep 2025", "Time": "23:30 IST", "Event": "US FOMC Rate Decision",              "Country": "🇺🇸 USA",   "Impact": "High"},
        {"Date": "05 Nov 2025", "Time": "23:30 IST", "Event": "US FOMC Rate Decision",              "Country": "🇺🇸 USA",   "Impact": "High"},
        {"Date": "17 Dec 2025", "Time": "23:30 IST", "Event": "US FOMC Rate Decision",              "Country": "🇺🇸 USA",   "Impact": "High"},
    ]
    # ── END CALENDAR DATA ──

    cal_df = pd.DataFrame(events)

    def impact_color(val):
        if val == "High":   return "color: #dc2626; font-weight: 700"
        elif val == "Medium": return "color: #d97706; font-weight: 600"
        return "color: #16a34a"

    cc1, cc2 = st.columns([1, 2])
    with cc1:
        impact_filter = st.multiselect("Impact Filter", ["High", "Medium", "Low"], default=["High", "Medium"])
    with cc2:
        country_filter = st.multiselect("Country Filter", cal_df["Country"].unique().tolist(),
                                        default=cal_df["Country"].unique().tolist())

    filtered_cal = cal_df[cal_df["Impact"].isin(impact_filter) & cal_df["Country"].isin(country_filter)]
    st.dataframe(
        filtered_cal.style.applymap(impact_color, subset=["Impact"]),
        use_container_width=True, height=480, hide_index=True
    )

    st.markdown("---")
    with st.expander("📅 TradingView Economic Calendar (Live)"):
        tv_cal_html = """
        <iframe src="https://s.tradingview.com/embed-widget/events/?locale=en#%7B%22colorTheme%22%3A%22light%22%2C%22isTransparent%22%3Atrue%2C%22width%22%3A%22100%25%22%2C%22height%22%3A%22450%22%2C%22importanceFilter%22%3A%22-1%2C0%2C1%22%2C%22countryFilter%22%3A%22in%2Cus%2Ceu%22%7D"
            style="width:100%;height:450px;border:none;" allowtransparency="true">
        </iframe>"""
        st.components.v1.html(tv_cal_html, height=460)


# =============================================================================
# TAB 1 (was 6) — Chart
# =============================================================================
with tab_tv:
    st.markdown("#### 📈 Chart")
    st.caption("Full-featured TradingView chart. Enter any ticker — NSE stocks: HDFCBANK, RELIANCE. Global: AAPL, MSFT.")

    tv2_sym = st.text_input(
        "Symbol", value="HDFCBANK", key="tv2_sym",
        help="For NSE stocks use just the ticker e.g. HDFCBANK, RELIANCE. Global: AAPL, MSFT."
    )
    import urllib.parse as _ul
    tv2_params = _ul.urlencode({
        "symbol": tv2_sym,
        "interval": "D",
        "timezone": "Asia/Kolkata",
        "theme": "light",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f8f9fb",
        "enable_publishing": "false",
        "withdateranges": "true",
        "hide_side_toolbar": "false",
        "allow_symbol_change": "true",
        "studies": "RSI@tv-basicstudies,MACD@tv-basicstudies,BB@tv-basicstudies",
        "show_popup_button": "true",
        "save_image": "false",
    })
    tv2_iframe_url = f"https://s.tradingview.com/widgetembed/?{tv2_params}"
    tv2_html = f'''
    <iframe
      src="{tv2_iframe_url}"
      style="width:100%;height:690px;border:none;display:block;border-radius:8px;"
      allowtransparency="true"
      scrolling="no"
      frameborder="0">
    </iframe>'''
    st.components.v1.html(tv2_html, height=700)


# =============================================================================
# TAB 7 — Telegram Channels (via RSSHub mirror fallback chain)
# Tries 6 public RSSHub mirrors in order. Stops at first one that responds.
# No setup, no token, no admin access required.
#
# ┌─────────────────────────────────────────────────────────────────┐
# │  TO ADD A NEW TELEGRAM CHANNEL:                                 │
# │  1. Find the channel's username (the part after t.me/)          │
# │  2. Add a new tuple to TELEGRAM_CHANNELS in this format:        │
# │       ("Display Name", "username", "description")               │
# │  3. Save and push to GitHub — done. No other changes needed.    │
# └─────────────────────────────────────────────────────────────────┘
# =============================================================================
with tab_twitter:
    st.markdown("#### 📬 Channels — Telegram Market Feeds")
    st.caption("Posts fetched from public Telegram channels. Refreshes every 60 sec.")

    # ══════════════════════════════════════════════════════════════
    # ADD / REMOVE TELEGRAM CHANNELS HERE
    # Format: ("Display Name", "telegram_username", "description")
    TELEGRAM_CHANNELS = [
        ("Beat The Street News",             "Beatthestreetnews", "Latest share market news"),
        ("Beat The Street Equity Research",  "btsreports",        "Research reports & books"),
        # ── Add more channels below this line ─────────────────────
        # ("Zerodha Varsity",   "zerodhaonline",  "Market education & insights"),
        # ("Moneycontrol News", "moneycontrol",   "Business & markets coverage"),
        # ("NSE India",         "NSEIndia",       "Official NSE announcements"),
    ]
    # ══════════════════════════════════════════════════════════════

    # ── Public RSSHub mirror list (tried in order, stops at first success) ────
    # If all fail, the app shows a clean error with direct Telegram links.
    # Update this list if mirrors go offline: https://docs.rsshub.app/instances
    RSSHUB_MIRRORS = [
        "https://rsshub.rssforever.com",
        "https://rss.fatpandadev.com",
        "https://hub.slar.in",
        "https://rsshub.app",
        "https://rsshub.woodland.cafe",
        "https://rsshub.renovamen.ink",
    ]

    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=60_000, key="telegram_refresh")

    @st.cache_data(ttl=60)
    def fetch_telegram_channel(channel_username):
        """
        Try each RSSHub mirror in order. Return (posts, mirror_used, error).
        Posts are returned on first mirror that gives a non-empty feed.
        """
        import re as _re
        last_error = "All mirrors failed or returned empty feeds."

        for mirror in RSSHUB_MIRRORS:
            url = f"{mirror}/telegram/channel/{channel_username}"
            try:
                feed = feedparser.parse(url)
                if not feed.entries:
                    last_error = f"{mirror} returned 0 entries."
                    continue

                posts = []
                for entry in feed.entries[:25]:
                    pub = entry.get("published", entry.get("updated", ""))
                    try:
                        from email.utils import parsedate_to_datetime
                        pub_str = parsedate_to_datetime(pub).strftime("%d %b %Y  %H:%M")
                    except Exception:
                        pub_str = pub[:16] if pub else "—"

                    raw = entry.get("summary", entry.get("description", ""))
                    clean = _re.sub(r"<[^>]+>", " ", raw).strip()
                    clean = _re.sub(r"\s+", " ", clean)[:300]

                    title = entry.get("title", "")
                    if not title or title == clean[:len(title)]:
                        title = clean[:80] or "—"

                    posts.append({
                        "title":     title,
                        "body":      clean if clean != title else "",
                        "link":      entry.get("link", f"https://t.me/{channel_username}"),
                        "published": pub_str,
                    })

                return posts, mirror, None   # success

            except Exception as e:
                last_error = f"{mirror}: {e}"
                continue

        return [], None, last_error   # all mirrors failed

    def build_channel_html(posts, err, handle, display_name, desc, mirror_used):
        """Build a self-contained scrollable HTML block for one Telegram channel."""
        if err:
            body = f"""
            <div style="padding:20px 16px;background:#fffbeb;border:1px solid #fde68a;
                        border-radius:8px;font-family:Inter,sans-serif;font-size:.82rem;color:#92400e;">
              ⚠️ Mirrors temporarily unavailable. Retrying every 60 sec.
            </div>
            <div style="margin-top:12px;">
              <a href="https://t.me/{handle}" target="_blank"
                 style="display:inline-block;background:#f1f5f9;color:#0057b8;
                        border:1px solid #e2e8f0;padding:7px 16px;border-radius:6px;
                        font-size:.78rem;font-weight:600;text-decoration:none;
                        font-family:Inter,sans-serif;">
                📬 Open @{handle} on Telegram ↗
              </a>
            </div>"""
        elif not posts:
            body = f"""
            <div style="padding:20px 16px;background:#f0f9ff;border:1px solid #bae6fd;
                        border-radius:8px;font-family:Inter,sans-serif;font-size:.82rem;color:#0c4a6e;">
              No posts found. Channel may be private or mirrors haven't indexed it yet.
            </div>"""
        else:
            mirror_short = mirror_used.replace("https://", "").split("/")[0]
            cards = ""
            for post in posts:
                body_part = (
                    f'<div style="font-size:.78rem;color:#475569;margin-top:5px;'
                    f'line-height:1.55;word-break:break-word;">{post["body"]}</div>'
                ) if post["body"] else ""
                cards += f"""
                <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;
                            padding:11px 14px;margin-bottom:8px;
                            box-shadow:0 1px 3px rgba(0,0,0,.04);">
                  <div style="font-size:.84rem;font-weight:600;line-height:1.4;">
                    <a href="{post['link']}" target="_blank"
                       style="color:#0057b8;text-decoration:none;">{post['title']}</a>
                  </div>
                  {body_part}
                  <div style="font-size:.68rem;color:#94a3b8;margin-top:6px;
                              font-family:'JetBrains Mono',monospace;">
                    🕐 {post['published']}
                  </div>
                </div>"""
            body = f'''
            <div style="font-size:.68rem;color:#94a3b8;font-family:'JetBrains Mono',monospace;
                        margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #e8ecf0;">
              {len(posts)} posts · {mirror_short} · latest first
            </div>
            {cards}'''

        return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  html, body {{
    background: #f4f6f9;
    font-family: Inter, sans-serif;
    height: 100%;
  }}
  .channel-wrap {{
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #f4f6f9;
  }}
  .channel-header {{
    position: sticky;
    top: 0;
    z-index: 10;
    background: #ffffff;
    border-bottom: 2px solid #e2e8f0;
    padding: 10px 14px 8px 14px;
    flex-shrink: 0;
  }}
  .ch-title {{
    font-size: .9rem;
    font-weight: 700;
    color: #1e293b;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }}
  .ch-handle {{
    font-weight: 400;
    color: #94a3b8;
    font-size: .75rem;
    font-family: 'JetBrains Mono', monospace;
  }}
  .ch-open {{
    display: inline-block;
    background: #0057b8;
    color: #fff !important;
    padding: 3px 11px;
    border-radius: 5px;
    font-size: .72rem;
    font-weight: 600;
    text-decoration: none;
    white-space: nowrap;
    flex-shrink: 0;
  }}
  .ch-desc {{
    font-size: .7rem;
    color: #64748b;
    margin-top: 2px;
  }}
  .channel-body {{
    flex: 1;
    overflow-y: auto;
    padding: 10px 12px 16px 12px;
    scrollbar-width: thin;
    scrollbar-color: #cbd5e0 transparent;
  }}
  .channel-body::-webkit-scrollbar {{ width: 5px; }}
  .channel-body::-webkit-scrollbar-thumb {{
    background: #cbd5e0;
    border-radius: 4px;
  }}
</style>
</head><body>
<div class="channel-wrap">
  <div class="channel-header">
    <div class="ch-title">
      <span>{display_name} <span class="ch-handle">@{handle}</span></span>
      <a href="https://t.me/{handle}" target="_blank" class="ch-open">Open ↗</a>
    </div>
    <div class="ch-desc">{desc}</div>
  </div>
  <div class="channel-body">
    {body}
  </div>
</div>
</body></html>"""

    if not TELEGRAM_CHANNELS:
        st.info("No channels configured. Add entries to `TELEGRAM_CHANNELS` in `app.py`.")
    else:
        # Fetch all channels first (parallel-ish — each call is cached)
        channel_data = []
        for (display_name, handle, desc) in TELEGRAM_CHANNELS:
            with st.spinner(f"Fetching @{handle}…"):
                posts, mirror_used, err = fetch_telegram_channel(handle)
            channel_data.append((display_name, handle, desc, posts, err, mirror_used))

        # Render as equal-width columns, each independently scrollable
        cols = st.columns(len(channel_data))
        if not isinstance(cols, list):
            cols = [cols]

        SCROLL_HEIGHT = 820  # px — tall enough to show ~8 posts, scrollable beyond

        for col, (display_name, handle, desc, posts, err, mirror_used) in zip(cols, channel_data):
            with col:
                html_block = build_channel_html(
                    posts, err, handle, display_name, desc, mirror_used
                )
                st.components.v1.html(html_block, height=SCROLL_HEIGHT, scrolling=False)

    st.markdown("---")
    st.markdown(
        '<div style="font-size:.72rem;color:#94a3b8;font-family:JetBrains Mono,monospace;">'
        "📬 Posts via public RSSHub mirrors · Auto-retries on failure · "
        "Refreshes every 60 sec · Only works for public Telegram channels."
        "</div>",
        unsafe_allow_html=True
    )


# =============================================================================
# TAB 8 — Portfolio (Zerodha Holdings Upload)
# Upload the holdings XLSX/CSV from Zerodha Console → Reports → Holdings.
# The file is parsed automatically — no API key, no login needed.
#
# ZERODHA FILE FORMAT (auto-detected):
#   Row 22 = headers: Symbol, ISIN, Sector, Quantity Available, ...
#   Row 23+ = holdings data
#   Rows 14-17 = summary: Invested Value, Present Value, Unrealized P&L
# =============================================================================
with tab_holdings:
    st.markdown("#### 💼 Portfolio — Holdings")

    # ── How to download the file ───────────────────────────────────────────────
    with st.expander("ℹ️ How to get your holdings file from Zerodha"):
        st.caption(
            "1. Open **[console.zerodha.com](https://console.zerodha.com)** → log in\n"
            "2. Go to **Portfolio → Holdings**\n"
            "3. Click **Download** (top-right) → choose **XLSX** or **CSV**\n"
            "4. Upload that file here — takes 2 seconds\n\n"
            "**Tip:** Do this once a day after market close for accurate P&L."
        )

    # ── File uploader ─────────────────────────────────────────────────────────
    uploaded_file = st.file_uploader(
        "Upload your Zerodha holdings file",
        type=["xlsx", "csv"],
        key="holdings_upload",
        label_visibility="collapsed",
        help="Download from Zerodha Console → Portfolio → Holdings → Download"
    )

    # ── Parser ────────────────────────────────────────────────────────────────
    def parse_zerodha_holdings(file_obj, filename):
        """
        Parse Zerodha holdings XLSX or CSV export.
        Returns (df_holdings, summary_dict, error_str).
        Summary keys: invested, present, pnl, pnl_pct
        """
        import re as _re
        try:
            if filename.endswith('.csv'):
                raw = pd.read_csv(file_obj, header=None)
            else:
                raw = pd.read_excel(file_obj, header=None)

            # ── Find summary values ────────────────────────────────────────────
            summary = {"invested": 0, "present": 0, "pnl": 0, "pnl_pct": 0}
            summary_map = {
                "Invested Value":      "invested",
                "Present Value":       "present",
                "Unrealized P&L":      "pnl",
                "Unrealized P&L Pct.": "pnl_pct",
            }
            for _, row in raw.iterrows():
                for col in row:
                    if str(col).strip() in summary_map:
                        key = summary_map[str(col).strip()]
                        # value is in the next non-null cell
                        vals = [v for v in row if str(v) not in ("nan","None","")]
                        if len(vals) >= 2:
                            try:
                                summary[key] = float(str(vals[1]).replace(",",""))
                            except Exception:
                                pass

            # ── Find header row (contains "Symbol" and "Sector") ───────────────
            header_row = None
            for i, row in raw.iterrows():
                row_vals = [str(v).strip() for v in row]
                if "Symbol" in row_vals and "Sector" in row_vals:
                    header_row = i
                    break

            if header_row is None:
                return None, summary, "Could not find header row with 'Symbol' and 'Sector'."

            # ── Extract holdings data ──────────────────────────────────────────
            df = pd.read_excel(file_obj, header=header_row) if filename.endswith('.xlsx')                  else pd.read_csv(file_obj, header=header_row)

            # Keep only rows that have a Symbol value (non-null, non-header)
            df = df[df["Symbol"].notna()].copy()
            df = df[df["Symbol"].astype(str).str.strip() != ""]
            df = df[~df["Symbol"].astype(str).str.lower().isin(["symbol","nan"])]
            df = df.reset_index(drop=True)

            # ── Rename columns to standard names ──────────────────────────────
            col_map = {
                "Symbol":                    "Symbol",
                "ISIN":                      "ISIN",
                "Sector":                    "Sector",
                "Quantity Available":        "Qty",
                "Average Price":             "Avg Price",
                "Previous Closing Price":    "Prev Close",
                "Unrealized P&L":            "Total P&L",
                "Unrealized P&L Pct.":       "Return %",
            }
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

            # ── Coerce numeric columns ─────────────────────────────────────────
            for col in ["Qty", "Avg Price", "Prev Close", "Total P&L", "Return %"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(
                        df[col].astype(str).str.replace(",",""), errors="coerce"
                    )

            # ── Derive computed columns ────────────────────────────────────────
            df["Invested"]  = (df["Avg Price"] * df["Qty"]).round(2)
            df["Cur Value"] = (df["Prev Close"] * df["Qty"]).round(2)
            df["Day P&L"]   = 0.0   # not available in static export

            # ── Filter zero-qty rows ───────────────────────────────────────────
            df = df[df["Qty"] > 0].copy()

            return df, summary, None

        except Exception as e:
            return None, {}, str(e)

    # ── Fetch live LTP for a batch of symbols ─────────────────────────────────
    @st.cache_data(ttl=60)
    def fetch_live_ltp(symbols_tuple):
        """Fetch live LTP for a tuple of NSE symbols via yfinance."""
        tickers = [f"{s}.NS" for s in symbols_tuple]
        live = {}
        try:
            data = yf.download(
                tickers, period="2d", interval="1d",
                progress=False, auto_adjust=True
            )
            close = data["Close"] if "Close" in data.columns else data.xs("Close", axis=1, level=0)
            for s in symbols_tuple:
                try:
                    col = f"{s}.NS"
                    series = close[col].dropna()
                    if len(series) >= 2:
                        live[s] = {
                            "ltp":   round(float(series.iloc[-1]), 2),
                            "prev":  round(float(series.iloc[-2]), 2),
                        }
                    elif len(series) == 1:
                        live[s] = {"ltp": round(float(series.iloc[-1]), 2), "prev": None}
                except Exception:
                    pass
        except Exception:
            pass
        return live

    @st.cache_data(ttl=300)
    def fetch_stock_news(symbol):
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}.NS&region=IN&lang=en-IN"
        return fetch_rss(url)

    # ── Main rendering ────────────────────────────────────────────────────────
    if uploaded_file is None:
        st.info(
            "📂 **Upload your Zerodha holdings file above** to see your portfolio.\n\n"
            "Download it from: **Zerodha Console → Portfolio → Holdings → Download (XLSX)**"
        )
        # Show sample of what the dashboard looks like
        st.markdown("---")
        st.markdown("**Once uploaded, you'll see:**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Invested",      "₹2,84,203")
        c2.metric("Current Value", "₹2,94,937", delta="+₹10,734 (+3.78%)")
        c3.metric("Holdings",      "31 stocks")
    else:
        with st.spinner("Parsing holdings file…"):
            df_h, summary, parse_err = parse_zerodha_holdings(
                uploaded_file, uploaded_file.name
            )

        if parse_err or df_h is None:
            st.error(f"❌ Could not parse file: {parse_err}")
            st.caption("Make sure you're uploading the Zerodha Holdings XLSX/CSV file.")
        else:
            # ── Fetch live prices ──────────────────────────────────────────────
            all_symbols = tuple(df_h["Symbol"].tolist())
            with st.spinner("Fetching live prices…"):
                live_prices = fetch_live_ltp(all_symbols)

            # Update LTP and Day P&L where live data is available
            def get_ltp(sym):
                return live_prices.get(sym, {}).get("ltp", df_h.loc[df_h["Symbol"]==sym, "Prev Close"].iloc[0])

            df_h["LTP"] = df_h["Symbol"].apply(get_ltp)
            df_h["LTP"] = pd.to_numeric(df_h["LTP"], errors="coerce")

            # Recalculate with live LTP
            df_h["Cur Value"]  = (df_h["LTP"] * df_h["Qty"]).round(2)
            df_h["Total P&L"]  = (df_h["Cur Value"] - df_h["Invested"]).round(2)
            df_h["Return %"]   = ((df_h["Total P&L"] / df_h["Invested"]) * 100).round(2)
            df_h["Day P&L"]    = df_h.apply(
                lambda r: round((r["LTP"] - live_prices.get(r["Symbol"], {}).get("prev", r["LTP"])) * r["Qty"], 2)
                if live_prices.get(r["Symbol"], {}).get("prev") else 0.0, axis=1
            )

            df_h = df_h.sort_values("Cur Value", ascending=False).reset_index(drop=True)

            # ── Summary Metrics ────────────────────────────────────────────────
            total_invested = df_h["Invested"].sum()
            total_cur      = df_h["Cur Value"].sum()
            total_pnl      = df_h["Total P&L"].sum()
            total_day      = df_h["Day P&L"].sum()
            total_ret_pct  = (total_pnl / total_invested * 100) if total_invested else 0

            st.caption(f"📅 File: `{uploaded_file.name}` · {len(df_h)} holdings · Prices via yfinance (live)")

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Invested",       f"₹{total_invested:,.0f}")
            m2.metric("Current Value",  f"₹{total_cur:,.0f}",
                      delta=f"₹{total_pnl:+,.0f}")
            m3.metric("Total P&L",      f"₹{total_pnl:+,.0f}",
                      delta=f"{total_ret_pct:+.2f}%")
            m4.metric("Day P&L",        f"₹{total_day:+,.0f}")
            m5.metric("Holdings",       str(len(df_h)))

            st.markdown("---")

            # ── Holdings Table ─────────────────────────────────────────────────
            st.markdown("##### Holdings")

            def _col_color(val):
                if isinstance(val, (int, float)):
                    if val > 0: return "color:#16a34a;font-weight:600"
                    if val < 0: return "color:#dc2626;font-weight:600"
                return ""

            display_cols = ["Symbol","Sector","Qty","Avg Price","LTP",
                            "Invested","Cur Value","Day P&L","Total P&L","Return %"]
            styled = (
                df_h[display_cols].style
                .applymap(_col_color, subset=["Day P&L","Total P&L","Return %"])
                .format({
                    "Avg Price":  "₹{:,.2f}",
                    "LTP":        "₹{:,.2f}",
                    "Invested":   "₹{:,.0f}",
                    "Cur Value":  "₹{:,.0f}",
                    "Day P&L":    "₹{:+,.2f}",
                    "Total P&L":  "₹{:+,.2f}",
                    "Return %":   "{:+.2f}%",
                })
            )
            st.dataframe(styled, use_container_width=True,
                         height=min(60 + len(df_h)*36, 560), hide_index=True)

            st.markdown("---")

            # ── Sector Allocation ──────────────────────────────────────────────
            st.markdown("##### Sector Allocation")

            sector_df = (
                df_h.groupby("Sector", as_index=False)["Cur Value"]
                .sum()
                .sort_values("Cur Value", ascending=False)
            )
            sector_df["% of Portfolio"] = (sector_df["Cur Value"] / total_cur * 100).round(1)

            pie_colors = [
                "#0057b8","#16a34a","#dc2626","#d97706","#7c3aed",
                "#0891b2","#db2777","#65a30d","#ea580c","#6366f1",
                "#0284c7","#059669","#9333ea","#b45309","#e11d48",
                "#0f766e","#a16207","#7e22ce",
            ]

            fig_pie = go.Figure(go.Pie(
                labels=sector_df["Sector"],
                values=sector_df["Cur Value"],
                hole=0.44,
                marker=dict(
                    colors=pie_colors[:len(sector_df)],
                    line=dict(color="#ffffff", width=2)
                ),
                textinfo="label+percent",
                textfont=dict(size=11, family="Inter, sans-serif"),
                hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
                sort=True,
            ))
            fig_pie.add_annotation(
                text=f"<b>₹{total_cur/1e5:.1f}L</b><br><span style=\'font-size:9px;color:#64748b\'>Portfolio</span>",
                x=0.5, y=0.5, showarrow=False, align="center",
                font=dict(size=12, family="JetBrains Mono, monospace", color="#1e293b"),
            )
            fig_pie.update_layout(
                template=PLOTLY_TEMPLATE,
                paper_bgcolor=PLOTLY_PAPER_BG,
                plot_bgcolor=PLOTLY_PLOT_BG,
                height=400,
                margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(
                    font=dict(size=10, family="Inter, sans-serif"),
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="#e2e8f0", borderwidth=1,
                    orientation="v",
                ),
                showlegend=True,
            )

            pc1, pc2 = st.columns([3, 2])
            with pc1:
                st.plotly_chart(fig_pie, use_container_width=True)
            with pc2:
                st.markdown("<br>", unsafe_allow_html=True)
                sector_display = sector_df.copy()
                sector_display["Cur Value"] = sector_display["Cur Value"].apply(lambda x: f"₹{x:,.0f}")
                sector_display["% of Portfolio"] = sector_display["% of Portfolio"].apply(lambda x: f"{x:.1f}%")
                st.dataframe(sector_display[["Sector","Cur Value","% of Portfolio"]],
                             use_container_width=True, height=380, hide_index=True)

            st.markdown("---")

            # ── Top Gainers & Losers ───────────────────────────────────────────
            st.markdown("##### Top Gainers & Losers")
            gl1, gl2 = st.columns(2)
            top_gain = df_h.nlargest(5, "Return %")[["Symbol","Sector","Return %","Total P&L"]]
            top_loss = df_h.nsmallest(5, "Return %")[["Symbol","Sector","Return %","Total P&L"]]

            with gl1:
                st.markdown("🟢 **Top Gainers**")
                st.dataframe(
                    top_gain.style
                    .applymap(_col_color, subset=["Return %","Total P&L"])
                    .format({"Return %": "{:+.2f}%", "Total P&L": "₹{:+,.0f}"}),
                    use_container_width=True, hide_index=True, height=220
                )
            with gl2:
                st.markdown("🔴 **Top Losers**")
                st.dataframe(
                    top_loss.style
                    .applymap(_col_color, subset=["Return %","Total P&L"])
                    .format({"Return %": "{:+.2f}%", "Total P&L": "₹{:+,.0f}"}),
                    use_container_width=True, hide_index=True, height=220
                )

            st.markdown("---")

            # ── Company News ───────────────────────────────────────────────────
            st.markdown("##### Company News")
            st.caption("Latest news for your top 8 holdings by value.")

            top8 = df_h.head(8)["Symbol"].tolist()
            news_cols = st.columns(2)
            for i, sym in enumerate(top8):
                with news_cols[i % 2]:
                    st.markdown(
                        f'<div style="font-size:.82rem;font-weight:700;color:#1e293b;'
                        f'font-family:Inter,sans-serif;margin:10px 0 4px 0;">'
                        f'📰 {sym}</div>',
                        unsafe_allow_html=True
                    )
                    items = fetch_stock_news(sym)
                    if not items:
                        st.caption("No news found.")
                    else:
                        for item in items[:3]:
                            st.markdown(
                                f'<div class="news-card" style="margin-bottom:6px;">'
                                f'<div class="news-headline">'
                                f'<a href="{item["link"]}" target="_blank" '
                                f'style="color:#0057b8;text-decoration:none;font-size:.82rem;">'
                                f'{item["title"]}</a></div>'
                                f'<div class="news-meta">🕐 {item["published"]}</div>'
                                f'</div>',
                                unsafe_allow_html=True
                            )

    st.markdown("---")
    st.markdown(
        '<div style="font-size:.72rem;color:#94a3b8;font-family:JetBrains Mono,monospace;">'
        "💼 Upload Zerodha Holdings XLSX from Console → Portfolio → Holdings → Download · "
        "Live LTP via yfinance · Sectors from Zerodha file · Refreshes on re-upload."
        "</div>",
        unsafe_allow_html=True
    )


# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown(
    '<div style="text-align:center;font-family:\'JetBrains Mono\',monospace;font-size:0.62rem;color:#94a3b8;">'
    "⬛ TERMINAL · For personal research only. Not financial advice. "
    "Data via yfinance / TradingView / RSS. Prices may be delayed 15–20 min. "
    "MCX commodity prices are COMEX proxies (GC=F, SI=F, HG=F)."
    "</div>",
    unsafe_allow_html=True
)
