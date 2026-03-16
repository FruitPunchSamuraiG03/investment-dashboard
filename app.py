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
    /* Sticky tab bar: sits just below the ticker bar (top: 104px = 58px header + 46px ticker) */
    .stTabs [data-baseweb="tab-list"] {
        background: #ffffff;
        gap: 6px;
        border-radius: 0;
        padding: 6px 8px;
        position: sticky;
        top: 104px;
        z-index: 990;
        border-bottom: 2px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab"] { background: transparent; border: none; border-radius: 6px; color: #64748b; font-size: 0.82rem; font-family: 'Inter', sans-serif; padding: 6px 18px !important; }
    .stTabs [aria-selected="true"] { background: #f0f5ff !important; color: #0057b8 !important; font-weight: 600; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
    /* Extra top padding to prevent content hiding under sticky ticker + tabs */
    [data-testid="stAppViewContainer"] > .main > .block-container {
        padding-top: 90px !important;
    }

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
tab_tv, tab_technicals, tab_breadth, tab_news, tab_calendar, tab_twitter, tab_holdings, tab_research = st.tabs([
    "📈 Chart",
    "🔬 Technicals",
    "🌡️ Breadth",
    "📰 News",
    "📅 Calendar",
    "📬 Channels",
    "💼 Portfolio",
    "🔍 Research",
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
    st.markdown("#### 📅 Economic Calendar — 2026")

    # ── TradingEconomics link (they block iframes — direct link is the only option) ──
    st.markdown(
        '<a href="https://tradingeconomics.com/calendar" target="_blank" '
        'style="display:inline-flex;align-items:center;gap:8px;'
        'background:#0057b8;color:#fff;padding:9px 20px;border-radius:7px;'
        'font-size:.85rem;font-weight:600;text-decoration:none;'
        'font-family:Inter,sans-serif;margin-bottom:14px;display:inline-block;">'
        '📊 Open TradingEconomics Calendar ↗</a>',
        unsafe_allow_html=True
    )
    st.caption(
        "TradingEconomics cannot be embedded (they block iframes). "
        "Click above to open their full live calendar in a new tab. "
        "The table below has key India & global events for 2026 — "
        "**update it** by editing `events` under `# ── CALENDAR DATA ──` in `app.py`."
    )

    # ── CALENDAR DATA ── (Update this list manually when dates change)
    # Source: federalreserve.gov (FOMC), rbi.org.in (RBI MPC), ecb.europa.eu (ECB)
    # All times in IST. ✅ = already announced/passed. Upcoming = still relevant.
    events = [
        # ── Already occurred in 2026 ──────────────────────────────────────────
        {"Date": "28 Jan 2026", "Time": "00:30 IST", "Event": "US FOMC Rate Decision (held at 3.50–3.75%)", "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "✅ Done"},
        {"Date": "06 Feb 2026", "Time": "10:00 IST", "Event": "RBI MPC Decision (held at 5.25%)",           "Country": "🇮🇳 India", "Impact": "High",   "Status": "✅ Done"},
        {"Date": "12 Feb 2026", "Time": "19:00 IST", "Event": "US CPI Inflation (Jan 2026)",                "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "✅ Done"},
        {"Date": "06 Mar 2026", "Time": "18:30 IST", "Event": "US Non-Farm Payrolls (Feb 2026)",            "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "✅ Done"},
        {"Date": "12 Mar 2026", "Time": "19:00 IST", "Event": "US CPI Inflation (Feb 2026)",                "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "✅ Done"},
        # ── Upcoming ──────────────────────────────────────────────────────────
        {"Date": "19 Mar 2026", "Time": "00:30 IST", "Event": "US FOMC Rate Decision + SEP Projections",   "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "20 Mar 2026", "Time": "18:30 IST", "Event": "US PCE Price Index (Feb 2026)",              "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "27 Mar 2026", "Time": "18:30 IST", "Event": "US GDP Q4 2025 (Final)",                    "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "03 Apr 2026", "Time": "18:30 IST", "Event": "US Non-Farm Payrolls (Mar 2026)",            "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "08 Apr 2026", "Time": "10:00 IST", "Event": "RBI MPC Decision",                          "Country": "🇮🇳 India", "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "10 Apr 2026", "Time": "19:00 IST", "Event": "US CPI Inflation (Mar 2026)",                "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "17 Apr 2026", "Time": "19:15 IST", "Event": "ECB Rate Decision",                         "Country": "🇪🇺 EU",    "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "30 Apr 2026", "Time": "20:00 IST", "Event": "US GDP Q1 2026 (Advance Estimate)",         "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "07 May 2026", "Time": "00:30 IST", "Event": "US FOMC Rate Decision",                     "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "08 May 2026", "Time": "18:30 IST", "Event": "US Non-Farm Payrolls (Apr 2026)",            "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "13 May 2026", "Time": "19:00 IST", "Event": "US CPI Inflation (Apr 2026)",                "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "05 Jun 2026", "Time": "19:15 IST", "Event": "ECB Rate Decision",                         "Country": "🇪🇺 EU",    "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "Jun 2026",    "Time": "10:00 IST", "Event": "RBI MPC Decision (date TBC)",               "Country": "🇮🇳 India", "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "18 Jun 2026", "Time": "00:30 IST", "Event": "US FOMC Rate Decision + SEP Projections",   "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "30 Jul 2026", "Time": "00:30 IST", "Event": "US FOMC Rate Decision",                     "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "Aug 2026",    "Time": "10:00 IST", "Event": "RBI MPC Decision (date TBC)",               "Country": "🇮🇳 India", "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "17 Sep 2026", "Time": "00:30 IST", "Event": "US FOMC Rate Decision + SEP Projections",   "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "Oct 2026",    "Time": "10:00 IST", "Event": "RBI MPC Decision (date TBC)",               "Country": "🇮🇳 India", "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "29 Oct 2026", "Time": "00:30 IST", "Event": "US FOMC Rate Decision",                     "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "10 Dec 2026", "Time": "00:30 IST", "Event": "US FOMC Rate Decision + SEP Projections",   "Country": "🇺🇸 USA",   "Impact": "High",   "Status": "🔜 Upcoming"},
        {"Date": "Dec 2026",    "Time": "10:00 IST", "Event": "RBI MPC Decision (date TBC)",               "Country": "🇮🇳 India", "Impact": "High",   "Status": "🔜 Upcoming"},
    ]
    # ── END CALENDAR DATA ──

    cal_df = pd.DataFrame(events)

    def impact_color(val):
        if val == "High":   return "color: #dc2626; font-weight: 700"
        elif val == "Medium": return "color: #d97706; font-weight: 600"
        return "color: #16a34a"

    def status_color(val):
        if "Done" in str(val):     return "color: #94a3b8"
        if "Upcoming" in str(val): return "color: #0057b8; font-weight: 600"
        return ""

    cc1, cc2, cc3 = st.columns([1, 1, 2])
    with cc1:
        impact_filter = st.multiselect("Impact", ["High", "Medium", "Low"], default=["High", "Medium"])
    with cc2:
        status_filter = st.multiselect("Status", ["✅ Done", "🔜 Upcoming"], default=["🔜 Upcoming"])
    with cc3:
        country_filter = st.multiselect("Country", cal_df["Country"].unique().tolist(),
                                        default=cal_df["Country"].unique().tolist())

    filtered_cal = cal_df[
        cal_df["Impact"].isin(impact_filter) &
        cal_df["Status"].isin(status_filter) &
        cal_df["Country"].isin(country_filter)
    ]
    st.dataframe(
        filtered_cal.style
            .applymap(impact_color, subset=["Impact"])
            .applymap(status_color, subset=["Status"]),
        use_container_width=True, height=500, hide_index=True
    )

    st.markdown("---")
    st.markdown("##### 📺 Live Economic Calendar (TradingView)")
    tv_cal_html = """
    <iframe src="https://s.tradingview.com/embed-widget/events/?locale=en#%7B%22colorTheme%22%3A%22light%22%2C%22isTransparent%22%3Afalse%2C%22width%22%3A%22100%25%22%2C%22height%22%3A%22500%22%2C%22importanceFilter%22%3A%22-1%2C0%2C1%22%2C%22countryFilter%22%3A%22in%2Cus%2Ceu%2Cgb%2Cjp%22%7D"
        style="width:100%;height:500px;border:none;border-radius:8px;" allowtransparency="true">
    </iframe>"""
    st.components.v1.html(tv_cal_html, height=510)


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

            st.markdown("---")

            # ================================================================
            # RED FLAGS & BUY/HOLD/SELL SIGNALS
            # Technical: RSI, MACD, 200 EMA, 50 EMA, Bollinger, 52w position
            # Fundamental: P/E, P/B, Debt/Equity, ROE, profit margin,
            #              current ratio, EPS growth, revenue growth
            # ================================================================
            st.markdown("##### \U0001f6a8 Red Flags & Signals")
            st.caption("Technical + Fundamental screening for all holdings. Not financial advice.")

            @st.cache_data(ttl=3600)
            def get_fundamentals(sym):
                try:
                    t    = yf.Ticker(f"{sym}.NS")
                    info = t.info
                    eps_trail = info.get("trailingEps")
                    eps_fwd   = info.get("forwardEps")
                    eps_g = ((eps_fwd - eps_trail) / abs(eps_trail) * 100
                             if eps_trail and eps_fwd and eps_trail != 0 else None)
                    rev_g = None
                    try:
                        inc = t.income_stmt
                        if inc is not None and not inc.empty and "Total Revenue" in inc.index:
                            revs = inc.loc["Total Revenue"].dropna()
                            if len(revs) >= 2:
                                rev_g = (revs.iloc[0]-revs.iloc[1])/abs(revs.iloc[1])*100
                    except Exception:
                        pass
                    return {
                        "pe": info.get("trailingPE"), "pb": info.get("priceToBook"),
                        "de": info.get("debtToEquity"), "roe": info.get("returnOnEquity"),
                        "profit_mg": info.get("profitMargins"),
                        "current_r": info.get("currentRatio"),
                        "eps_growth": eps_g, "rev_growth": rev_g,
                        "beta": info.get("beta"),
                    }
                except Exception:
                    return {}

            @st.cache_data(ttl=300)
            def get_technicals(sym):
                try:
                    df_t = yf.download(f"{sym}.NS", period="1y", interval="1d",
                                       progress=False, auto_adjust=True)
                    if df_t.empty or len(df_t) < 30:
                        return None
                    close = df_t["Close"].squeeze()
                    high  = df_t["High"].squeeze()
                    low   = df_t["Low"].squeeze()
                    d = close.diff()
                    g = d.clip(lower=0).ewm(com=13, min_periods=14).mean()
                    l = (-d.clip(upper=0)).ewm(com=13, min_periods=14).mean()
                    rsi    = float((100 - 100/(1+g/l.replace(0,0.0001))).iloc[-1])
                    ema50  = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
                    ema200 = float(close.ewm(span=200,adjust=False).mean().iloc[-1])
                    ltp    = float(close.iloc[-1])
                    macd   = close.ewm(span=12,adjust=False).mean() - close.ewm(span=26,adjust=False).mean()
                    sig_ln = macd.ewm(span=9, adjust=False).mean()
                    sma20  = close.rolling(20).mean()
                    std20  = close.rolling(20).std()
                    bb_up  = float((sma20+2*std20).iloc[-1])
                    bb_lo  = float((sma20-2*std20).iloc[-1])
                    w52_h  = float(high.tail(252).max())
                    w52_l  = float(low.tail(252).min())
                    w52p   = (ltp-w52_l)/(w52_h-w52_l)*100 if w52_h != w52_l else 50
                    vol    = df_t["Volume"].squeeze()
                    return {
                        "rsi": round(rsi,1), "ltp": round(ltp,2),
                        "ema50": round(ema50,2), "ema200": round(ema200,2),
                        "above_50": ltp>ema50, "above_200": ltp>ema200,
                        "macd_val": float(macd.iloc[-1]),
                        "macd_bull": bool(macd.iloc[-1]>sig_ln.iloc[-1] and macd.iloc[-2]<=sig_ln.iloc[-2]),
                        "macd_bear": bool(macd.iloc[-1]<sig_ln.iloc[-1] and macd.iloc[-2]>=sig_ln.iloc[-2]),
                        "macd_pos":  bool(macd.iloc[-1]>0),
                        "bb_upper": round(bb_up,2), "bb_lower": round(bb_lo,2),
                        "above_bb": ltp>bb_up, "below_bb": ltp<bb_lo,
                        "w52_pos": round(w52p,1),
                        "vol_surge": bool(float(vol.tail(20).mean()) > float(vol.tail(50).mean())*1.5),
                    }
                except Exception:
                    return None

            def score_and_flags(tech, fund, ret_pct, pledge_pct):
                score = 0
                tf = []   # technical flags
                ff = []   # fundamental flags

                if tech:
                    if tech["above_200"]:
                        score += 2
                    else:
                        score -= 2; tf.append("\U0001f534 Below 200 EMA \u2014 long-term downtrend")
                    if tech["above_50"]:
                        score += 1
                    else:
                        score -= 1; tf.append("\U0001f7e1 Below 50 EMA \u2014 medium-term downtrend")
                    if tech["rsi"] < 35:
                        score += 2; tf.append(f"\U0001f7e2 RSI oversold ({tech['rsi']}) \u2014 potential bounce zone")
                    elif tech["rsi"] > 72:
                        score -= 2; tf.append(f"\U0001f534 RSI overbought ({tech['rsi']}) \u2014 caution on new longs")
                    if tech["macd_bull"]:
                        score += 2; tf.append("\U0001f7e2 MACD bullish crossover \u2014 momentum shifting up")
                    elif tech["macd_bear"]:
                        score -= 2; tf.append("\U0001f534 MACD bearish crossover \u2014 momentum shifting down")
                    elif tech["macd_pos"]:
                        score += 1
                    else:
                        score -= 1
                    if tech["above_bb"]:
                        score -= 1; tf.append("\U0001f7e1 Above upper Bollinger Band \u2014 overextended")
                    elif tech["below_bb"]:
                        score += 1; tf.append("\U0001f7e2 Below lower Bollinger Band \u2014 potential reversal zone")
                    if tech["w52_pos"] > 90:
                        tf.append(f"\U0001f7e1 Near 52w high ({tech['w52_pos']:.0f}% of range)")
                    elif tech["w52_pos"] < 15:
                        tf.append(f"\U0001f534 Near 52w low ({tech['w52_pos']:.0f}% of range)")
                    if tech["vol_surge"]:
                        tf.append("\U0001f7e2 Volume surge (20d avg > 1.5x 50d avg)")

                if fund:
                    pe = fund.get("pe"); pb = fund.get("pb"); de = fund.get("de")
                    roe = fund.get("roe"); pm = fund.get("profit_mg")
                    cr = fund.get("current_r"); eps_g = fund.get("eps_growth")
                    rev_g = fund.get("rev_growth"); beta = fund.get("beta")
                    if pe is not None:
                        if pe < 0:
                            score -= 2; ff.append(f"\U0001f534 Negative P/E ({pe:.1f}) \u2014 company in losses")
                        elif pe > 60:
                            score -= 1; ff.append(f"\U0001f7e1 High P/E ({pe:.1f}) \u2014 expensive valuation")
                        elif 0 < pe < 12:
                            score += 1; ff.append(f"\U0001f7e2 Low P/E ({pe:.1f}) \u2014 potentially undervalued")
                    if pb is not None and pb > 8:
                        score -= 1; ff.append(f"\U0001f7e1 High P/B ({pb:.1f}) \u2014 expensive vs book value")
                    if de is not None:
                        if de > 200:
                            score -= 2; ff.append(f"\U0001f534 High D/E ({de:.0f}%) \u2014 elevated debt burden")
                        elif de > 100:
                            score -= 1; ff.append(f"\U0001f7e1 Moderate D/E ({de:.0f}%)")
                        elif de < 20:
                            score += 1; ff.append(f"\U0001f7e2 Low D/E ({de:.0f}%) \u2014 strong balance sheet")
                    if roe is not None:
                        r = roe*100
                        if r > 20:   score += 1; ff.append(f"\U0001f7e2 Strong ROE ({r:.1f}%)")
                        elif r < 5:  score -= 1; ff.append(f"\U0001f534 Weak ROE ({r:.1f}%)")
                    if pm is not None:
                        p = pm*100
                        if p < 0:    score -= 2; ff.append(f"\U0001f534 Negative profit margin ({p:.1f}%)")
                        elif p < 3:  score -= 1; ff.append(f"\U0001f7e1 Very thin margin ({p:.1f}%)")
                    if cr is not None:
                        if cr < 1.0: score -= 2; ff.append(f"\U0001f534 Low current ratio ({cr:.2f}) \u2014 liquidity risk")
                        elif cr < 1.5: score -= 1; ff.append(f"\U0001f7e1 Tight current ratio ({cr:.2f})")
                    if eps_g is not None:
                        if eps_g > 15:  score += 2; ff.append(f"\U0001f7e2 Strong EPS growth ({eps_g:+.1f}%)")
                        elif eps_g < -15: score -= 2; ff.append(f"\U0001f534 EPS declining ({eps_g:+.1f}%)")
                    if rev_g is not None:
                        if rev_g < -10:  score -= 1; ff.append(f"\U0001f534 Revenue declining ({rev_g:+.1f}% YoY)")
                        elif rev_g > 20: score += 1; ff.append(f"\U0001f7e2 Strong revenue growth ({rev_g:+.1f}% YoY)")
                    if beta is not None and beta > 2.0:
                        ff.append(f"\U0001f7e1 High beta ({beta:.2f}) \u2014 highly volatile stock")

                if pledge_pct > 70:
                    score -= 2; ff.append(f"\U0001f534 Promoter pledge {pledge_pct:.0f}% \u2014 major red flag")
                elif pledge_pct > 30:
                    score -= 1; ff.append(f"\U0001f7e1 Promoter pledge {pledge_pct:.0f}%")
                if ret_pct < -25:
                    score -= 1; ff.append(f"\U0001f534 Portfolio loss {ret_pct:+.1f}%")
                elif ret_pct > 100:
                    ff.append(f"\U0001f7e2 Multi-bagger {ret_pct:+.0f}% \u2014 consider partial profit booking")

                label = "BUY" if score >= 5 else "SELL" if score <= -3 else "HOLD"
                return label, score, tf, ff

            rf_rows = []
            pledge_col_m = "Quantity Pledged (Margin)" if "Quantity Pledged (Margin)" in df_h.columns else None
            pledge_col_l = "Quantity Pledged (Loan)"   if "Quantity Pledged (Loan)"   in df_h.columns else None
            prog = st.progress(0, text="Running analysis\u2026")

            for i, row in df_h.iterrows():
                sym     = row["Symbol"]
                ret_pct = float(row.get("Return %", 0) or 0)
                qty     = float(row.get("Qty", 1) or 1)
                pm  = float(str(row.get(pledge_col_m, 0) or 0)) if pledge_col_m else 0
                pl  = float(str(row.get(pledge_col_l, 0) or 0)) if pledge_col_l else 0
                pledge_pct = (pm+pl)/qty*100

                tech = get_technicals(sym)
                fund = get_fundamentals(sym)
                label, score, t_flags, f_flags = score_and_flags(tech, fund, ret_pct, pledge_pct)

                rf_rows.append({
                    "Symbol":     sym,
                    "Sector":     row.get("Sector",""),
                    "Signal":     label,
                    "Score":      score,
                    "RSI":        tech["rsi"] if tech else "\u2014",
                    "vs 200EMA":  ("Above" if tech["above_200"] else "Below") if tech else "\u2014",
                    "P/E":        round(fund["pe"],1) if fund and fund.get("pe") else "\u2014",
                    "D/E %":      round(fund["de"],0) if fund and fund.get("de") else "\u2014",
                    "ROE %":      round(fund["roe"]*100,1) if fund and fund.get("roe") else "\u2014",
                    "EPS Gr.":    f"{fund['eps_growth']:+.1f}%" if fund and fund.get("eps_growth") else "\u2014",
                    "Pledged%":   f"{pledge_pct:.0f}%",
                    "Tech Flags": " | ".join(t_flags) if t_flags else "\u2705 Clean",
                    "Fund Flags": " | ".join(f_flags) if f_flags else "\u2705 Clean",
                })
                prog.progress((i+1)/len(df_h), text=f"Analysing {sym}\u2026")

            prog.empty()
            rf_df = pd.DataFrame(rf_rows).sort_values("Score", ascending=True)

            def _sc(val):
                if val == "BUY":  return "color:#16a34a;font-weight:700"
                if val == "SELL": return "color:#dc2626;font-weight:700"
                return "color:#d97706;font-weight:700"
            def _fc(val):
                s = str(val)
                if "\U0001f534" in s: return "color:#dc2626;font-size:.78rem"
                if "\U0001f7e1" in s: return "color:#d97706;font-size:.78rem"
                if "\U0001f7e2" in s or "\u2705" in s: return "color:#16a34a;font-size:.78rem"
                return "font-size:.78rem"

            st.dataframe(
                rf_df.style
                    .applymap(_sc, subset=["Signal"])
                    .applymap(_fc, subset=["Tech Flags","Fund Flags"]),
                use_container_width=True,
                height=min(60+len(rf_df)*36, 560),
                hide_index=True,
            )
            st.caption(
                "Technical: RSI \u00b7 MACD \u00b7 200 EMA \u00b7 50 EMA \u00b7 Bollinger \u00b7 52w position \u00b7 Volume  |  "
                "Fundamental: P/E \u00b7 P/B \u00b7 D/E \u00b7 ROE \u00b7 Margin \u00b7 Current ratio \u00b7 EPS/Rev growth  |  "
                "Score \u22655 = BUY \u00b7 \u2264\u22123 = SELL \u00b7 else HOLD \u2014 screening only, not financial advice."
            )

            st.markdown("---")

            # ================================================================
            # PORTFOLIO NEWS FEED — PER COMPANY SCROLLABLE PANELS
            # 2 companies per row, each panel has sticky header + scrollable body
            # Sources: Yahoo Finance, Mint, Business Standard, NSE Announcements
            # ================================================================
            st.markdown("##### \U0001f4f0 Portfolio News Feed")
            st.caption("Each panel shows all news for one company. Scroll within each panel. 2 columns, sorted by portfolio value.")

            @st.cache_data(ttl=300)
            def fetch_portfolio_news(symbols_tuple):
                all_items = []
                sym_set = set(s.upper() for s in symbols_tuple)

                for sym in symbols_tuple:
                    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={sym}.NS&region=IN&lang=en-IN"
                    for item in fetch_rss(url):
                        item["symbol"] = sym; item["source_type"] = "Yahoo Finance"
                        all_items.append(item)

                for url in ["https://www.livemint.com/rss/markets",
                            "https://www.livemint.com/rss/companies"]:
                    for item in fetch_rss(url):
                        m = next((s for s in sym_set if s in item["title"].upper()), None)
                        if m:
                            item["symbol"] = m; item["source_type"] = "Mint"
                            all_items.append(item)

                for url in ["https://www.business-standard.com/rss/markets-106.rss",
                            "https://www.business-standard.com/rss/companies-101.rss"]:
                    for item in fetch_rss(url):
                        m = next((s for s in sym_set if s in item["title"].upper()), None)
                        if m:
                            item["symbol"] = m; item["source_type"] = "Business Standard"
                            all_items.append(item)

                nse_hdrs = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Accept": "application/json, text/plain, */*",
                    "Referer": "https://www.nseindia.com/",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                try:
                    sess = requests.Session()
                    sess.get("https://www.nseindia.com", headers=nse_hdrs, timeout=6)
                    for sym in symbols_tuple:
                        try:
                            url  = f"https://www.nseindia.com/api/corp-info?symbol={sym}&corpType=announcements&FMTType=0"
                            resp = sess.get(url, headers=nse_hdrs, timeout=7)
                            anns = resp.json()
                            for ann in (anns.get("annDetails") or anns.get("data") or [])[:8]:
                                title = ann.get("subject") or ann.get("headline","")
                                link  = ann.get("attchmntFile","")
                                if link and not link.startswith("http"):
                                    link = f"https://www.nseindia.com{link}"
                                pub_str = ann.get("exchdisstime","") or ann.get("date","")
                                pub_dt  = None
                                try:
                                    from datetime import datetime as _dt2
                                    pub_dt  = _dt2.strptime(pub_str[:16], "%d-%b-%Y %H:%M")
                                    pub_str = pub_dt.strftime("%d %b %Y  %H:%M")
                                except Exception:
                                    pass
                                if title:
                                    all_items.append({
                                        "title": title,
                                        "link": link or f"https://www.nseindia.com/get-quotes/equity?symbol={sym}",
                                        "published": pub_str or "\u2014",
                                        "pub_dt": pub_dt,
                                        "source": "NSE", "source_type": "NSE", "symbol": sym,
                                    })
                        except Exception:
                            pass
                except Exception:
                    pass

                seen, unique = set(), []
                for item in all_items:
                    k = item["title"][:60].lower().strip()
                    if k not in seen:
                        seen.add(k); unique.append(item)
                unique.sort(key=lambda x: x.get("pub_dt") or datetime.min, reverse=True)
                return unique

            SOURCE_COLORS = {
                "Yahoo Finance": "#0057b8", "Mint": "#e11d48",
                "Business Standard": "#7c3aed", "NSE": "#059669",
            }

            with st.spinner("Fetching news for all holdings\u2026"):
                all_news = fetch_portfolio_news(tuple(df_h["Symbol"].tolist()))

            if not all_news:
                st.info("No news found. Feeds may be temporarily unavailable.")
            else:
                from collections import defaultdict
                news_by_sym = defaultdict(list)
                for item in all_news:
                    s = item.get("symbol","")
                    if s:
                        news_by_sym[s].append(item)

                # Only render panels for companies that have at least one article
                syms_with_news = [s for s in df_h["Symbol"].tolist() if news_by_sym.get(s)]
                syms_no_news   = [s for s in df_h["Symbol"].tolist() if not news_by_sym.get(s)]
                PANEL_H = 560

                total_items = sum(len(news_by_sym.get(s,[])) for s in syms_with_news)
                note_no_news = (f" · No news found for: {', '.join(syms_no_news)}" if syms_no_news else "")
                st.caption(f"{total_items} articles across {len(syms_with_news)} holdings · Latest first per company{note_no_news}")

                for row_i in range(0, len(syms_with_news), 2):
                    pair = syms_with_news[row_i:row_i+2]
                    cols = st.columns(len(pair))
                    if not isinstance(cols, list):
                        cols = [cols]

                    for col, sym in zip(cols, pair):
                        with col:
                            items  = news_by_sym.get(sym, [])
                            sector = ""
                            try:
                                sector = df_h.loc[df_h["Symbol"]==sym, "Sector"].iloc[0]
                            except Exception:
                                pass

                            cards = ""
                            for item in items:
                                src_type  = item.get("source_type","News")
                                badge_clr = SOURCE_COLORS.get(src_type, "#64748b")
                                cards += (
                                    f'<div style="background:#fff;border:1px solid #e2e8f0;'
                                    f'border-radius:7px;padding:9px 12px;margin-bottom:6px;'
                                    f'box-shadow:0 1px 2px rgba(0,0,0,.03);">'
                                    f'<div style="margin-bottom:3px;">'
                                    f'<span style="background:{badge_clr}20;color:{badge_clr};'
                                    f'font-size:.6rem;font-weight:700;padding:1px 5px;'
                                    f'border-radius:3px;font-family:JetBrains Mono,monospace;">'
                                    f'{src_type}</span></div>'
                                    f'<div style="font-size:.82rem;font-weight:600;'
                                    f'line-height:1.35;color:#1e293b;">'
                                    f'<a href="{item["link"]}" target="_blank" '
                                    f'style="color:#0057b8;text-decoration:none;">'
                                    f'{item["title"]}</a></div>'
                                    f'<div style="font-size:.65rem;color:#94a3b8;margin-top:3px;'
                                    f'font-family:JetBrains Mono,monospace;">'
                                    f'\U0001f550 {item["published"]}</div>'
                                    f'</div>'
                                )

                            panel_html = (
                                f'<!DOCTYPE html><html><head><meta charset="utf-8">'
                                f'<style>'
                                f'*{{box-sizing:border-box;margin:0;padding:0;}}'
                                f'html,body{{background:#f4f6f9;font-family:Inter,sans-serif;}}'
                                f'.hdr{{position:sticky;top:0;z-index:10;background:#ffffff;'
                                f'border-bottom:2px solid #e2e8f0;padding:8px 12px;}}'
                                f'.sym{{font-size:.9rem;font-weight:700;color:#1e293b;'
                                f'font-family:JetBrains Mono,monospace;}}'
                                f'.meta{{display:flex;justify-content:space-between;'
                                f'align-items:center;margin-top:2px;}}'
                                f'.sector{{font-size:.65rem;color:#64748b;}}'
                                f'.count{{font-size:.62rem;color:#94a3b8;'
                                f'font-family:JetBrains Mono,monospace;}}'
                                f'.body{{height:{PANEL_H-54}px;overflow-y:auto;padding:10px 12px;'
                                f'scrollbar-width:thin;scrollbar-color:#cbd5e0 transparent;}}'
                                f'.body::-webkit-scrollbar{{width:4px;}}'
                                f'.body::-webkit-scrollbar-thumb{{background:#cbd5e0;border-radius:3px;}}'
                                f'</style></head><body>'
                                f'<div class="hdr">'
                                f'<div class="sym">{sym}</div>'
                                f'<div class="meta">'
                                f'<span class="sector">{sector}</span>'
                                f'<span class="count">{len(items)} articles</span>'
                                f'</div></div>'
                                f'<div class="body">{cards}</div>'
                                f'</body></html>'
                            )
                            st.components.v1.html(panel_html, height=PANEL_H, scrolling=False)

    st.markdown("---")
    st.markdown(
        '<div style="font-size:.72rem;color:#94a3b8;font-family:JetBrains Mono,monospace;">'
        "\U0001f4bc Holdings XLSX from Zerodha Console \u2192 Portfolio \u2192 Holdings \u2192 Download \u00b7 "
        "Live LTP via yfinance \u00b7 News: Yahoo Finance, Mint, Business Standard, NSE \u00b7 "
        "Signals: technical + fundamental screening \u2014 not financial advice."
        '</div>',
        unsafe_allow_html=True
    )



# =============================================================================
# TAB 9 — Equity Research (AI-Powered Institutional Analysis)
# Uses Claude claude-sonnet-4-20250514 via the Anthropic API.
# The full 15-section institutional research prompt is sent with the company name.
# Output streams section by section. Multi-part reports use "Continue" button.
# =============================================================================
with tab_research:
    st.markdown("#### 🔍 Equity Research — AI Institutional Analysis")
    st.caption(
        "Enter any company name or ticker. The AI generates a full 15-section institutional "
        "equity research report: thesis, Porter's Five Forces, financial model, DCF, scenario analysis, "
        "risk framework, and more. Methodology: Goldman/JPMorgan calibre. Powered by Claude."
    )

    # ── Prompt constants ──────────────────────────────────────────────────────
    RESEARCH_SYSTEM_PROMPT = """You are a senior equity research analyst with 20+ years of institutional experience across bulge-bracket and elite boutique firms — equivalent in calibre to lead analysts at Goldman Sachs, JPMorgan, Morgan Stanley, UBS, Barclays, HSBC, Bank of America, Citi, and Jefferies. You have deep expertise across all sectors, market caps, and geographies, covering both listed equities and private companies.

Your output will be consumed exclusively by senior buy-side and sell-side professionals, portfolio managers, and capital allocators. Do not simplify, do not hedge unnecessarily, do not add disclaimers beyond those standard in institutional research. Use the full vocabulary of the profession: EV/EBITDA, FCF yield, ROIC, WACC, NTM multiples, comps, DCF, sum-of-the-parts, operating leverage, convexity, downside protection, and all other technical terminology as required. The reader is sophisticated. Speak to them accordingly.

REPORT STRUCTURE — MANDATORY SEQUENCE

BEFORE YOU WRITE A SINGLE WORD OF THE REPORT, output a REPORT ROADMAP first — a numbered list of all 15 sections with a one-line company-specific statement of what you will cover in each section.

DATA INTEGRITY RULES (non-negotiable):
- NEVER fabricate financial figures, metrics, dates, names, or transactions.
- NEVER extrapolate silently — state methodology and limitations.
- NEVER conflate actuals with estimates — label each clearly.
- Mark unavailable data as: [DATA UNAVAILABLE — external source required: suggest checking (source)]
- Flag stale data (>12 months for fast-moving companies): [DATA MAY BE STALE — verify against latest filings]

Produce the report in this mandatory sequence:
1. COVER PAGE DATA — ticker, exchange, sector, rating (BUY/HOLD/SELL), price target, current price, upside/downside, investment horizon (short/medium/long), key risks
2. EXECUTIVE SUMMARY (max 400 words) — thesis in 3-5 bullets, Howard Marks second-level thinking, Mauboussin expectations investing lens (reverse-engineer price-implied assumptions), cycle positioning, conviction level
3. COMPANY OVERVIEW — business model, revenue streams, geographic exposure, customer concentration, ownership structure
4. INDUSTRY & COMPETITIVE LANDSCAPE — full Porter's Five Forces, moat analysis, peer/comp set selection with rationale
5. MACRO & GEOPOLITICAL CONTEXT — rates, inflation, FX, commodities, geopolitical risk, sovereign risk
6. INDUSTRY TAILWINDS, HEADWINDS & POLICY — structural demand drivers, cyclical headwinds, government policy, regulatory risk, ESG capital flows
7. GOVERNMENT CONNECTIONS & POLITICAL ECONOMY — SOE dynamics, regulatory capture, subsidies, political affiliations of key principals, geopolitical exposure
8. MANAGEMENT QUALITY & CAPITAL ALLOCATION — track record, capital allocation scorecard, incentive alignment, earnings quality, Mauboussin ROIC/CAP framework
9. FINANCIAL ANALYSIS & MODEL — income statement, balance sheet, cash flow, returns summary across LTM/current/NTM/+2Y
10. VALUATION — Mauboussin expectations anchor (reverse DCF), DCF (base/bear/bull), trading comps (EV/EBITDA, P/E, P/FCF), precedent transactions, SOTP where applicable, football field summary
11. SCENARIO ANALYSIS — Bull/Base/Bear with probabilities summing to 100%, Marks asymmetry ratio (bull upside ÷ bear downside must be stated), probability-weighted PT
12. CATALYST TIMELINE — time-bound catalysts with magnitude, probability, and direction
13. KEY RISKS — ranked by severity × probability, with materiality, crystallisation probability, mitigants, and PT impact
14. SHORT THESIS / BEAR STEELMAN — strongest possible bear case as a short-seller would construct it
15. KNOWLEDGE GAPS & DATA LIMITATIONS — unavailable data, information asymmetry, model limitations, primary research required

ANALYTICAL STANDARDS:
→ Apply Howard Marks second-level thinking: what does consensus believe, what do you believe, why does the gap exist, why will it close?
→ Apply Mauboussin expectations investing: reverse-engineer price-implied growth, margin, and ROIC. State whether price-implied expectations are too optimistic, too pessimistic, or fair.
→ Apply Marks asymmetry framework: assess upside/downside ratio. BUY at high conviction requires ratio > 2.0x.
→ ROIC vs WACC analysis and competitive advantage period are mandatory.
→ Use base rates to pressure-test management guidance and consensus forecasts.
→ When you reach your output limit, stop at the end of the current section and output exactly:
  ── REPORT PAUSED ──
  Completed through: [Section number and title]
  Remaining sections: [list]
  To continue: reply with "Continue"
→ When the user sends "Continue", resume from the next section without re-introducing the company."""

    # ── Session state ─────────────────────────────────────────────────────────
    if "research_messages" not in st.session_state:
        st.session_state.research_messages = []   # list of {role, content}
    if "research_company" not in st.session_state:
        st.session_state.research_company  = ""
    if "research_running" not in st.session_state:
        st.session_state.research_running  = False

    # ── Input row ─────────────────────────────────────────────────────────────
    ri1, ri2, ri3 = st.columns([3, 1, 1])
    with ri1:
        company_input = st.text_input(
            "Company name or ticker",
            placeholder="e.g. HDFCBANK, Reliance Industries, JSW Steel, Adani Ports, AAPL",
            key="research_company_input",
            label_visibility="collapsed",
        )
    with ri2:
        run_btn = st.button("🔍 Generate Report", use_container_width=True, key="run_research")
    with ri3:
        clear_btn = st.button("🗑️ Clear", use_container_width=True, key="clear_research")

    if clear_btn:
        st.session_state.research_messages = []
        st.session_state.research_company  = ""
        st.rerun()

    # ── Trigger new report ────────────────────────────────────────────────────
    if run_btn and company_input.strip():
        company = company_input.strip()
        st.session_state.research_company  = company
        st.session_state.research_messages = [
            {"role": "user", "content": f"Analyse {company}"}
        ]
        st.rerun()

    # ── Continue button (shown when report is paused) ─────────────────────────
    last_content = ""
    if st.session_state.research_messages:
        last_msg = st.session_state.research_messages[-1]
        if last_msg["role"] == "assistant":
            last_content = last_msg["content"]

    is_paused = "REPORT PAUSED" in last_content

    if is_paused:
        if st.button("▶️ Continue Report", use_container_width=False, key="continue_research"):
            st.session_state.research_messages.append(
                {"role": "user", "content": "Continue"}
            )
            st.rerun()

    # ── Display existing conversation ─────────────────────────────────────────
    if st.session_state.research_messages:
        company_label = st.session_state.research_company
        if company_label:
            st.markdown(
                f'<div style="font-size:.78rem;font-weight:700;color:#0057b8;'
                f'font-family:JetBrains Mono,monospace;margin-bottom:8px;">'
                f'Research: {company_label}</div>',
                unsafe_allow_html=True
            )

        for msg in st.session_state.research_messages:
            if msg["role"] == "user" and msg["content"] not in ("Continue",):
                st.markdown(
                    f'<div style="background:#e0f2fe;border-radius:8px;padding:8px 14px;'
                    f'margin:6px 0;font-size:.82rem;color:#0057b8;font-family:Inter,sans-serif;">'
                    f'🔍 Analysing: <strong>{msg["content"].replace("Analyse ","")}</strong></div>',
                    unsafe_allow_html=True
                )
            elif msg["role"] == "assistant":
                # Render the report in a styled scrollable container
                import html as _html
                safe_content = msg["content"]

                # Style section headers (lines starting with digit+dot or === lines)
                import re as _re
                lines = safe_content.split('\n')
                styled_lines = []
                for line in lines:
                    # Section headers like "1. COVER PAGE" or "══════"
                    if _re.match(r'^─+$', line) or _re.match(r'^═+$', line):
                        styled_lines.append(f'<hr style="border:none;border-top:1px solid #e2e8f0;margin:12px 0;">')
                    elif _re.match(r'^\d+\.\s+[A-Z]', line):
                        styled_lines.append(
                            f'<div style="font-size:.95rem;font-weight:700;color:#0057b8;'
                            f'font-family:JetBrains Mono,monospace;margin:18px 0 6px 0;'
                            f'border-bottom:2px solid #e2e8f0;padding-bottom:4px;">{line}</div>'
                        )
                    elif line.startswith('──') or line.startswith('══'):
                        styled_lines.append(
                            f'<div style="font-size:.75rem;font-weight:700;color:#64748b;'
                            f'font-family:JetBrains Mono,monospace;margin:10px 0 4px 0;'
                            f'letter-spacing:.06em;">{line}</div>'
                        )
                    elif line.startswith('REPORT PAUSED') or '── REPORT PAUSED ──' in line:
                        styled_lines.append(
                            f'<div style="background:#fef3c7;border:1px solid #f59e0b;'
                            f'border-radius:6px;padding:10px 14px;margin:12px 0;'
                            f'font-size:.82rem;font-family:JetBrains Mono,monospace;color:#92400e;">'
                            f'⏸ {line}</div>'
                        )
                    elif line.startswith('- ') or line.startswith('→ '):
                        styled_lines.append(
                            f'<div style="padding:2px 0 2px 16px;font-size:.83rem;color:#334155;'
                            f'line-height:1.6;">{line}</div>'
                        )
                    elif line.strip() == '':
                        styled_lines.append('<br>')
                    else:
                        styled_lines.append(
                            f'<div style="font-size:.83rem;color:#1e293b;line-height:1.65;'
                            f'padding:1px 0;">{line}</div>'
                        )

                report_html = '\n'.join(styled_lines)

                st.components.v1.html(
                    f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  *{{box-sizing:border-box;margin:0;padding:0;}}
  html,body{{background:#ffffff;font-family:Inter,sans-serif;}}
  .report{{padding:20px 24px 24px 24px;}}
  a{{color:#0057b8;}}
</style></head><body>
<div class="report">{report_html}</div>
</body></html>''',
                    height=900,
                    scrolling=True,
                )

    # ── Run the API call (Google Gemini — free tier) ─────────────────────────
    # Get free API key at: https://aistudio.google.com
    # Add to Streamlit Cloud → Settings → Secrets:  GEMINI_API_KEY = "AIza..."
    msgs = st.session_state.research_messages
    if msgs and msgs[-1]["role"] == "user":
        with st.spinner("Generating institutional research report… this takes 30–60 seconds."):
            try:
                _gemini_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
                if not _gemini_key:
                    st.error(
                        "⚠️ **GEMINI_API_KEY not found in Streamlit Secrets.**\n\n"
                        "**Free setup (no credit card needed):**\n"
                        "1. Go to [aistudio.google.com](https://aistudio.google.com) → Sign in with Google\n"
                        "2. Click **Get API key** → **Create API key** → Copy it\n"
                        "3. Streamlit Cloud → your app → ⋮ → **Settings → Secrets** → add:\n"
                        "```toml\nGEMINI_API_KEY = \"AIza...\"\n```\n"
                        "4. Save → Reboot app"
                    )
                    st.stop()

                # Convert conversation history to Gemini format
                # Gemini uses "parts" instead of "content", and "model" instead of "assistant"
                gemini_contents = []
                for m in msgs:
                    role = "model" if m["role"] == "assistant" else "user"
                    gemini_contents.append({
                        "role":  role,
                        "parts": [{"text": m["content"]}]
                    })

                # Gemini 1.5 Pro — free tier: 15 RPM, 1M TPD
                _gemini_url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"gemini-2.0-flash:generateContent?key={_gemini_key}"
                )
                resp = requests.post(
                    _gemini_url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "system_instruction": {
                            "parts": [{"text": RESEARCH_SYSTEM_PROMPT}]
                        },
                        "contents":           gemini_contents,
                        "generationConfig": {
                            "maxOutputTokens": 8192,
                            "temperature":     0.3,
                        },
                    },
                    timeout=180,
                )
                data = resp.json()

                # Extract text from Gemini response structure
                if "candidates" in data and data["candidates"]:
                    text = (
                        data["candidates"][0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", "")
                    )
                    if text:
                        st.session_state.research_messages.append(
                            {"role": "assistant", "content": text}
                        )
                    else:
                        st.error("Empty response from Gemini. Try again.")
                elif "error" in data:
                    err = data["error"]
                    st.error(f"Gemini API error: {err.get('message', str(err))}")
                    if "API_KEY_INVALID" in str(err) or "401" in str(err.get("code","")):
                        st.caption("The GEMINI_API_KEY in Streamlit Secrets appears to be invalid. Regenerate it at aistudio.google.com.")
                else:
                    st.error(f"Unexpected Gemini response: {str(data)[:300]}")
                st.rerun()
            except Exception as e:
                st.error(f"Request failed: {e}")

    if not st.session_state.research_messages:
        st.markdown(
            '<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;'
            'padding:24px 28px;margin-top:12px;">'
            '<div style="font-size:.9rem;font-weight:700;color:#1e293b;margin-bottom:10px;">'
            '📋 What this generates</div>'
            '<div style="font-size:.82rem;color:#475569;line-height:1.7;">'
            '• <b>15-section institutional report</b> — Cover Page, Executive Summary, '
            'Company Overview, Porter\'s Five Forces, Macro Context, Industry Tailwinds/Headwinds, '
            'Government Connections, Management Quality, Financial Model, DCF Valuation, '
            'Scenario Analysis, Catalyst Timeline, Risk Framework, Bear Steelman, Knowledge Gaps<br>'
            '• <b>Howard Marks framework</b> — second-level thinking, asymmetry of outcomes, cycle positioning<br>'
            '• <b>Mauboussin framework</b> — reverse DCF, price-implied expectations, ROIC/CAP analysis<br>'
            '• <b>Multi-part reports</b> — click "Continue Report" when the report pauses at output limit<br>'
            '• Works for any listed or private company globally<br>'
            '</div>'
            '</div>',
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
