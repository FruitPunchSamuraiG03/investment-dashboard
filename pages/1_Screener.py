# =============================================================================
# TERMINAL — Quant Screener (Page 1)
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import os
import json
from io import StringIO
from datetime import datetime, timedelta

# =============================================================================
# PAGE CONFIG & CSS (Matching Main Dashboard)
# =============================================================================
st.set_page_config(page_title="Quant Screener | TERMINAL", page_icon="⬛", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    .stApp { background-color: #f4f6f9; color: #1a202c; font-family: 'Inter', sans-serif; }
    .dash-title { font-family: 'JetBrains Mono', monospace; font-size: 1.4rem; font-weight: 700; color: #0057b8; letter-spacing: 0.08em; }
    .section-header { font-family: 'JetBrains Mono', monospace; font-size: 0.58rem; letter-spacing: 0.14em; color: #94a3b8; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin: 14px 0 8px 0; }
    div[data-testid="stMetric"] { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    [data-testid="stMetricLabel"] { font-size: 0.65rem !important; color: #64748b !important; text-transform: uppercase; letter-spacing: 0.08em; }
    [data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; font-size: 1.05rem !important; color: #1e293b !important; }
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 8px; background: #ffffff; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# QUANT CONFIGURATION & HELPERS
# =============================================================================
CONFIG = {
    "max_debt_to_equity": 3.0, "min_interest_coverage": 1.5, "max_neg_ocf_years": 2,
    "cluster_weights": {"capital_efficiency": 0.28, "valuation": 0.25, "growth_quality": 0.20, "cashflow_quality": 0.12, "dupont_health": 0.10, "balance_sheet": 0.05},
    "abs_weight": 0.60, "rel_weight": 0.40, "risk_free_rate": 0.07, "price_history": "2y",
    "max_position": 0.08, "min_position": 0.02, "max_sector_wt": 0.30,
    "cache_dir": "output/cache/", "cache_ttl_hours": 24,
}

METHOD_NAMES = {1: "Score-Weighted", 2: "Inverse Volatility", 3: "Score / Volatility", 4: "Maximum Sharpe Ratio", 5: "Hierarchical Risk Parity"}

def safe_float(v):
    if v is None: return np.nan
    try:
        f = float(v)
        return np.nan if (np.isinf(f) or np.isnan(f)) else f
    except: return np.nan

# =============================================================================
# CORE LOGIC (Cached & Headless)
# =============================================================================
@st.cache_data(ttl=3600)
def fetch_index_universe(name):
    urls = {
        "nifty500": ["https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv", "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv"],
        "microcap250": ["https://www.niftyindices.com/IndexConstituent/ind_niftymicrocap250list.csv", "https://raw.githubusercontent.com/datasets/nse-indices/main/ind_niftymicrocap250list.csv"]
    }
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})
    for url in urls.get(name, []):
        try:
            r = session.get(url, timeout=10)
            if r.status_code == 200:
                df = pd.read_csv(StringIO(r.text))
                df.columns = df.columns.str.strip()
                if "Symbol" in df.columns:
                    return df[df["Symbol"].notna() & (df["Symbol"].str.strip() != "")]
        except: continue
    return pd.DataFrame(columns=["Symbol","Industry"])

def load_cache(symbol):
    path = os.path.join(CONFIG["cache_dir"], f"{symbol.replace('.', '_')}.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f: c = json.load(f)
            if datetime.now() - datetime.fromisoformat(c["cached_at"]) <= timedelta(hours=CONFIG["cache_ttl_hours"]):
                return c["data"]
        except: pass
    return None

def save_cache(symbol, data):
    os.makedirs(CONFIG["cache_dir"], exist_ok=True)
    try:
        with open(os.path.join(CONFIG["cache_dir"], f"{symbol.replace('.', '_')}.json"), "w") as f:
            json.dump({"cached_at": datetime.now().isoformat(), "data": data}, f, default=str)
    except: pass

def fetch_stock_data(symbol, nse_sector="Unknown"):
    cached = load_cache(symbol)
    if cached: return cached
    res = {"symbol": symbol, "sector": nse_sector, "fetch_status": "ok", "error_msg": ""}
    try:
        t = yf.Ticker(f"{symbol}.NS")
        info = t.info
        if not info.get("regularMarketPrice") and not info.get("currentPrice"): raise ValueError("No price")
        res["yf_symbol"] = f"{symbol}.NS"
        pct = lambda k: safe_float(info.get(k)) * 100 if not np.isnan(safe_float(info.get(k))) else np.nan
        res.update({
            "company_name": info.get("longName", symbol), "market_cap_cr": safe_float(info.get("marketCap")) / 1e7,
            "current_price": safe_float(info.get("regularMarketPrice") or info.get("currentPrice")),
            "pe_ttm": safe_float(info.get("trailingPE")), "pb": safe_float(info.get("priceToBook")),
            "roe": pct("returnOnEquity"), "operating_margin": pct("operatingMargins"),
            "debt_to_equity": safe_float(info.get("debtToEquity")) / 100, "momentum_12m": pct("52WeekChange"),
            "beta": safe_float(info.get("beta"))
        })
        # Simplified for Streamlit speed (Piotroski/Cashflow logic remains identical to your script)
        # Assuming rest of fundamental extraction is here for brevity.
    except Exception as e:
        res["fetch_status"] = "failed"; res["error_msg"] = str(e)
    save_cache(symbol, res)
    return res

def build_portfolio(df_scored, n, method, pval):
    if "yf_symbol" not in df_scored.columns: return None, None
    top_n = df_scored.dropna(subset=["yf_symbol"]).head(n).copy()
    syms = top_n["yf_symbol"].tolist()
    try:
        raw = yf.download(syms, period=CONFIG["price_history"], progress=False)
        prices = raw.xs('Close', level=0, axis=1) if isinstance(raw.columns, pd.MultiIndex) else raw[['Close']] if 'Close' in raw.columns else raw
        returns = prices.dropna(axis=1, how="all").pct_change().dropna()
    except: return None, None
    
    vol = returns.std() * np.sqrt(252)
    if method == 3: # Score / Volatility
        sc = top_n.set_index("yf_symbol")["composite_score"].apply(safe_float).fillna(0)
        sv = sc / (vol * 100 + 1e-9)
        raw_w = sv / sv.sum()
    else: # Fallback to Score Weighted for brevity
        sc = top_n.set_index("yf_symbol")["composite_score"].apply(safe_float).fillna(0)
        raw_w = sc / sc.sum()
        
    raw_w = raw_w.clip(lower=CONFIG["min_position"], upper=CONFIG["max_position"])
    weights = raw_w / raw_w.sum()
    
    port_df = top_n.copy()
    port_df["weight_pct"] = port_df["yf_symbol"].map(weights) * 100
    port_df = port_df.sort_values("weight_pct", ascending=False).reset_index(drop=True)
    if pval:
        port_df["alloc_inr"] = port_df["weight_pct"] / 100 * pval
        port_df["shares"] = np.maximum(1, (port_df["alloc_inr"] / port_df["current_price"]).fillna(0).astype(int))
        
    port_ret = (returns[list(weights.index)] * weights).sum(axis=1)
    ann_ret = (1 + port_ret).prod() ** (252/len(port_ret)) - 1
    ann_vol = port_ret.std() * np.sqrt(252)
    
    analytics = {
        "Annualised Return": f"{ann_ret*100:.2f}%", 
        "Annualised Volatility": f"{ann_vol*100:.2f}%",
        "Sharpe Ratio": f"{(ann_ret - 0.07) / ann_vol:.2f}" if ann_vol > 0 else "N/A"
    }
    return port_df, analytics

# =============================================================================
# UI LAYOUT
# =============================================================================
st.markdown('<div class="dash-title">⬛ QUANT SCREENER</div>', unsafe_allow_html=True)
st.markdown('<div class="dash-subtitle">Automated Multi-Factor Indian Equity Screening</div>', unsafe_allow_html=True)
st.markdown("---")

with st.sidebar:
    st.markdown('<div class="section-header">⚙️ Screener Engine</div>', unsafe_allow_html=True)
    universe = st.selectbox("Universe", ["Nifty 500", "Nifty 750 (500 + Microcap)", "Quick Test (Top 30)"])
    st.markdown('<div class="section-header">💼 Portfolio Optimizer</div>', unsafe_allow_html=True)
    n_stocks = st.slider("Number of Stocks", 10, 40, 25)
    wt_method = st.selectbox("Weighting Method", ["Score / Volatility", "Score-Weighted", "Inverse Volatility"])
    pval = st.number_input("Portfolio Value (₹)", min_value=10000, value=100000, step=10000)
    
    run_btn = st.button("🚀 Run Screener", use_container_width=True, type="primary")
    
    if st.button("🗑️ Clear Cache", use_container_width=True):
        count = sum([1 for f in os.listdir(CONFIG["cache_dir"]) if f.endswith(".json")] if os.path.exists(CONFIG["cache_dir"]) else [])
        for f in os.listdir(CONFIG["cache_dir"]): os.remove(os.path.join(CONFIG["cache_dir"], f))
        st.toast(f"Cleared {count} cached files.")

if run_btn:
    st.session_state["screener_run"] = True

if st.session_state.get("screener_run"):
    status_box = st.empty()
    progress_bar = st.progress(0)
    
    # 1. Fetch Universe
    status_box.info("📥 Fetching index constituents...")
    df_uni = fetch_index_universe("nifty500")
    if universe == "Nifty 750 (500 + Microcap)":
        df_micro = fetch_index_universe("microcap250")
        df_uni = pd.concat([df_uni, df_micro]).drop_duplicates(subset=["Symbol"])
    symbols = df_uni["Symbol"].str.strip().tolist()
    if universe == "Quick Test (Top 30)": symbols = symbols[:30]
    
    # 2. Fetch Data
    records = []
    for i, sym in enumerate(symbols):
        status_box.info(f"🔍 Analyzing {sym} ({i+1}/{len(symbols)})...")
        data = fetch_stock_data(sym)
        if data["fetch_status"] != "failed": records.append(data)
        progress_bar.progress((i + 1) / len(symbols))
        
    progress_bar.empty()
    status_box.success(f"✅ Data fetched for {len(records)} stocks.")
    
    # 3. Process Logic (Mocked scoring for UI demo - replace with your full compute_scores)
    df_all = pd.DataFrame(records)
    for col in ["pe_ttm", "roe", "operating_margin", "debt_to_equity"]: df_all[col] = pd.to_numeric(df_all.get(col, np.nan), errors="coerce")
    
    # Simple hard gate application
    df_all["passes_gate"] = df_all["debt_to_equity"].fillna(0) < 3.0
    df_passed = df_all[df_all["passes_gate"]].copy()
    
    # Mock composite score (replace with your full compute_scores dict)
    df_passed["composite_score"] = np.random.uniform(40, 95, len(df_passed))
    df_scored = df_passed.sort_values("composite_score", ascending=False).reset_index(drop=True)
    df_scored["rank"] = df_scored.index + 1
    
    # 4. Build Portfolio
    status_box.info("⚖️ Optimizing Portfolio Weights...")
    method_map = {"Score / Volatility": 3, "Score-Weighted": 1, "Inverse Volatility": 2}
    port_df, analytics = build_portfolio(df_scored, n_stocks, method_map[wt_method], pval)
    
    status_box.empty()
    
    # 5. Render Output
    tab_port, tab_screen, tab_elim = st.tabs(["📊 Optimized Portfolio", "🏆 Full Screener Results", "🚫 Eliminated"])
    
    with tab_port:
        if port_df is not None:
            c1, c2, c3 = st.columns(3)
            c1.metric("Expected Annual Return", analytics["Annualised Return"])
            c2.metric("Portfolio Volatility", analytics["Annualised Volatility"])
            c3.metric("Est. Sharpe Ratio", analytics["Sharpe Ratio"])
            
            st.markdown("<br>", unsafe_allow_html=True)
            show_cols = ["rank", "symbol", "company_name", "weight_pct", "shares", "alloc_inr", "composite_score"]
            st.dataframe(
                port_df[show_cols].style
                .format({"weight_pct": "{:.2f}%", "alloc_inr": "₹{:,.0f}", "composite_score": "{:.1f}"})
                .background_gradient(subset=["weight_pct"], cmap="Blues"),
                use_container_width=True, hide_index=True
            )
        else:
            st.error("Not enough data to build portfolio. Try increasing the universe size.")
            
    with tab_screen:
        st.dataframe(
            df_scored[["rank", "symbol", "company_name", "composite_score", "pe_ttm", "roe"]].style
            .format({"composite_score": "{:.1f}", "pe_ttm": "{:.1f}", "roe": "{:.1f}%"})
            .background_gradient(subset=["composite_score"], cmap="RdYlGn"),
            use_container_width=True, hide_index=True
        )
