# =============================================================================
# TERMINAL — Quant Screener (Full Institutional Engine)
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import os
import json
from io import StringIO, BytesIO
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule

# =============================================================================
# PAGE CONFIG & CSS
# =============================================================================
st.set_page_config(page_title="Quant Screener | TERMINAL", page_icon="⬛", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    .stApp { background-color: #f4f6f9; color: #1a202c; font-family: 'Inter', sans-serif; }
    .dash-title { font-family: 'JetBrains Mono', monospace; font-size: 1.4rem; font-weight: 700; color: #0057b8; letter-spacing: 0.08em; }
    .dash-subtitle { font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; color: #94a3b8; letter-spacing: 0.12em; text-transform: uppercase; }
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
# CACHE & UNIVERSE LOGIC
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

# =============================================================================
# PIOTROSKI F-SCORE
# =============================================================================
def compute_piotroski(inc, bs, cf):
    score = 0; details = []
    try:
        def gi(stmt, keys, yr=0):
            if stmt is None: return np.nan
            for k in keys:
                if k in stmt.index:
                    v = stmt.loc[k].dropna().sort_index(ascending=False)
                    return safe_float(v.iloc[yr]) if len(v) > yr else np.nan
            return np.nan
        ni_0 = gi(inc, ["Net Income"]); ni_1 = gi(inc, ["Net Income"], yr=1)
        ocf_0 = gi(cf, ["Operating Cash Flow","Total Cash From Operating Activities"])
        ta_0 = gi(bs, ["Total Assets"]); ta_1 = gi(bs, ["Total Assets"], yr=1)
        ltd_0 = gi(bs, ["Long Term Debt","Total Debt"]); ltd_1 = gi(bs, ["Long Term Debt","Total Debt"], yr=1)
        ca_0 = gi(bs, ["Current Assets","Total Current Assets"]); ca_1 = gi(bs, ["Current Assets","Total Current Assets"], yr=1)
        cl_0 = gi(bs, ["Current Liabilities","Total Current Liabilities"]); cl_1 = gi(bs, ["Current Liabilities","Total Current Liabilities"], yr=1)
        rev_0 = gi(inc, ["Total Revenue"]); rev_1 = gi(inc, ["Total Revenue"], yr=1)
        cg_0 = gi(inc, ["Cost Of Revenue","Cost of Goods Sold"]); cg_1 = gi(inc, ["Cost Of Revenue","Cost of Goods Sold"], yr=1)
        sh_0 = gi(bs, ["Ordinary Shares Number","Share Issued","Common Stock"]); sh_1 = gi(bs, ["Ordinary Shares Number","Share Issued","Common Stock"], yr=1)
        roa_0 = ni_0/ta_0 if not np.isnan(ni_0) and not np.isnan(ta_0) and ta_0>0 else np.nan
        roa_1 = ni_1/ta_1 if not np.isnan(ni_1) and not np.isnan(ta_1) and ta_1>0 else np.nan
        def f(cond, label):
            nonlocal score; v = 1 if cond else 0; score += v; details.append(f"{label}={v}")
        if not np.isnan(roa_0): f(roa_0>0, "F1_ROA+")
        if not np.isnan(ocf_0): f(ocf_0>0, "F2_OCF+")
        if not np.isnan(roa_0) and not np.isnan(roa_1): f(roa_0>roa_1, "F3_ROAimprv")
        if not np.isnan(ocf_0) and not np.isnan(ni_0): f(ocf_0>ni_0, "F4_CFqual")
        if not np.isnan(ltd_0) and not np.isnan(ltd_1) and ta_0>0 and ta_1>0: f(ltd_0/ta_0 < ltd_1/ta_1, "F5_Lev-")
        if not np.isnan(ca_0) and not np.isnan(cl_0) and cl_0>0 and cl_1>0: f(ca_0/cl_0 > ca_1/cl_1, "F6_CRimprv")
        if not np.isnan(sh_0) and not np.isnan(sh_1): f(sh_0 <= sh_1*1.02, "F7_NoDilut")
        if not np.isnan(rev_0) and rev_0>0 and not np.isnan(rev_1) and rev_1>0 and not np.isnan(cg_0) and not np.isnan(cg_1):
            f((rev_0-cg_0)/rev_0 > (rev_1-cg_1)/rev_1, "F8_GMimprv")
        if not np.isnan(rev_0) and ta_0>0 and not np.isnan(rev_1) and ta_1>0: f(rev_0/ta_0 > rev_1/ta_1, "F9_ATimprv")
    except Exception: pass
    return score, " | ".join(details)

# =============================================================================
# DATA FETCHING (Full Fundamentals)
# =============================================================================
def _get_item(stmt, keys, yr=0):
    if stmt is None: return np.nan
    for k in keys:
        if k in stmt.index:
            vals = stmt.loc[k].dropna().sort_index(ascending=False)
            return safe_float(vals.iloc[yr]) if len(vals) > yr else np.nan
    return np.nan

def fetch_stock_data(symbol, nse_sector="Unknown"):
    cached = load_cache(symbol)
    if cached: return cached
    result = {"symbol": symbol, "sector": nse_sector, "fetch_status": "ok", "error_msg": ""}
    ticker_obj = None
    for suffix in [".NS", ".BO"]:
        try:
            t = yf.Ticker(symbol + suffix)
            price = safe_float(t.info.get("regularMarketPrice") or t.info.get("currentPrice"))
            if not np.isnan(price) and price > 0:
                ticker_obj = t; result["yf_symbol"] = symbol + suffix; break
        except: continue
    if ticker_obj is None:
        result["fetch_status"] = "failed"; result["error_msg"] = "No valid price"
        return result
    try:
        info = ticker_obj.info
        pct = lambda k: safe_float(info.get(k)) * 100 if not np.isnan(safe_float(info.get(k))) else np.nan
        mktcap = safe_float(info.get("marketCap"))
        result.update({
            "company_name": info.get("longName", symbol), "yf_sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"), "market_cap_cr": mktcap / 1e7 if not np.isnan(mktcap) else np.nan,
            "current_price": safe_float(info.get("regularMarketPrice") or info.get("currentPrice")),
            "beta": safe_float(info.get("beta")), "pe_ttm": safe_float(info.get("trailingPE")),
            "pb": safe_float(info.get("priceToBook")), "ps": safe_float(info.get("priceToSalesTrailing12Months")),
            "ev_ebitda": safe_float(info.get("enterpriseToEbitda")), "forward_pe": safe_float(info.get("forwardPE")),
            "roe": pct("returnOnEquity"), "roa": pct("returnOnAssets"), "gross_margin": pct("grossMargins"),
            "operating_margin": pct("operatingMargins"), "net_margin": pct("profitMargins"),
            "revenue_growth_yoy": pct("revenueGrowth"), "earnings_growth_yoy": pct("earningsGrowth"),
            "debt_to_equity": safe_float(info.get("debtToEquity")) / 100 if not np.isnan(safe_float(info.get("debtToEquity"))) else np.nan,
            "current_ratio": safe_float(info.get("currentRatio")), "momentum_12m": pct("52WeekChange"),
        })
        try:
            inc = ticker_obj.financials; bs = ticker_obj.balance_sheet; cf = ticker_obj.cashflow
            if inc is not None and "Total Revenue" in inc.index:
                rev = inc.loc["Total Revenue"].dropna().sort_index(ascending=False)
                if len(rev) >= 4:
                    r0 = safe_float(rev.iloc[0]); r3 = safe_float(rev.iloc[3])
                    if not np.isnan(r0) and not np.isnan(r3) and r3 > 0: result["revenue_cagr_3yr"] = ((r0/r3)**(1/3)-1)*100
                elif len(rev) >= 2:
                    r0 = safe_float(rev.iloc[0]); rn = safe_float(rev.iloc[-1]); n = len(rev)-1
                    if not np.isnan(r0) and not np.isnan(rn) and rn > 0: result["revenue_cagr_3yr"] = ((r0/rn)**(1/n)-1)*100
            for ek in ["Operating Income","EBIT"]:
                if inc is not None and ek in inc.index:
                    op = inc.loc[ek].dropna().sort_index(ascending=False)
                    if len(op) >= 4:
                        o0 = safe_float(op.iloc[0]); o3 = safe_float(op.iloc[3])
                        if not np.isnan(o0) and not np.isnan(o3) and o3 > 0 and o0 > 0: result["op_income_cagr_3yr"] = ((o0/o3)**(1/3)-1)*100
                    break
            ebit = _get_item(inc, ["Operating Income","EBIT"])
            if bs is not None:
                equity = _get_item(bs, ["Stockholders Equity","Total Stockholder Equity","Common Stock Equity"])
                debt = _get_item(bs, ["Long Term Debt","Total Debt","Long-Term Debt"])
                cash = _get_item(bs, ["Cash And Cash Equivalents","Cash","Cash And Short Term Investments"])
                assets = _get_item(bs, ["Total Assets"])
                if not np.isnan(ebit) and not np.isnan(equity):
                    ic = equity + (debt if not np.isnan(debt) else 0) - (cash if not np.isnan(cash) else 0)
                    if ic > 0: result["roic"] = (ebit * 0.75) / ic * 100
                if not np.isnan(assets) and assets > 0:
                    rev_l = _get_item(inc, ["Total Revenue"])
                    if not np.isnan(rev_l): result["asset_turnover"] = rev_l / assets
                    if not np.isnan(equity) and equity > 0: result["equity_multiplier"] = assets / equity
                int_exp = _get_item(inc, ["Interest Expense","Interest And Debt Expense"])
                if not np.isnan(int_exp) and abs(int_exp) > 0 and not np.isnan(ebit): result["interest_coverage"] = ebit / abs(int_exp)
            if cf is not None:
                ocf = _get_item(cf, ["Operating Cash Flow","Total Cash From Operating Activities"])
                capex = _get_item(cf, ["Capital Expenditure","Capital Expenditures"])
                ni = _get_item(inc, ["Net Income"])
                if not np.isnan(ocf):
                    result["operating_cf_cr"] = ocf / 1e7
                    if not np.isnan(ni) and ni > 0: result["cf_quality"] = ocf / ni
                    if not np.isnan(capex):
                        fcf = ocf + capex
                        if not np.isnan(mktcap) and mktcap > 0: result["fcf_yield"] = fcf / mktcap * 100
                        if not np.isnan(ni) and ni > 0: result["fcf_conversion"] = fcf / ni * 100
                        if not np.isnan(ni) and not np.isnan(assets) and assets > 0: result["accruals_ratio"] = (ni - fcf) / assets * 100
                for ok in ["Operating Cash Flow","Total Cash From Operating Activities"]:
                    if ok in cf.index:
                        ocf_vals = cf.loc[ok].dropna().sort_index(ascending=False)
                        result["neg_ocf_count_3yr"] = int((ocf_vals[:3] < 0).sum())
                        break
            pe = result.get("pe_ttm", np.nan); eg = result.get("earnings_growth_yoy", np.nan)
            if not np.isnan(pe) and not np.isnan(eg) and eg > 0: result["peg"] = pe / eg
            p_score, p_detail = compute_piotroski(inc, bs, cf)
            result["piotroski_score"] = p_score; result["piotroski_detail"] = p_detail
        except Exception as e: result["stmt_error"] = str(e)[:150]
    except Exception as e: result["fetch_status"] = "partial"; result["error_msg"] = str(e)[:150]
    save_cache(symbol, result)
    return result

# =============================================================================
# SCORING & GATES
# =============================================================================
def apply_hard_gates(row):
    reasons = []
    de = safe_float(row.get("debt_to_equity"))
    ic = safe_float(row.get("interest_coverage"))
    neg = row.get("neg_ocf_count_3yr", 0) or 0
    opm = safe_float(row.get("operating_margin"))
    is_fin = "financial" in str(row.get("sector", "")).lower() or "bank" in str(row.get("sector", "")).lower()
    
    if np.isnan(de) and not is_fin: reasons.append("Missing D/E")
    elif not np.isnan(de) and de > CONFIG["max_debt_to_equity"]: reasons.append(f"D/E={de:.1f}x>3")
    
    if np.isnan(ic) and not is_fin: reasons.append("Missing IntCov")
    elif not np.isnan(ic) and ic < CONFIG["min_interest_coverage"]: reasons.append(f"IntCov={ic:.1f}x<1.5")
    
    if neg >= CONFIG["max_neg_ocf_years"]: reasons.append(f"NegOCF {int(neg)}/3yrs")
    
    if np.isnan(opm): reasons.append("Missing OPM")
    elif opm < 0: reasons.append(f"NegOPM={opm:.1f}%")
        
    return (False, "; ".join(reasons)) if reasons else (True, "")

VALUATION_BANDS = {
    "pe_ttm": [(10,10),(15,8),(20,6),(25,4),(30,2),(1e9,0)],
    "pb": [(1,10),(2,8),(3,6),(4,4),(5,2),(1e9,0)],
    "ps": [(0.5,10),(1,8),(2,6),(3,4),(5,2),(1e9,0)],
    "ev_ebitda": [(6,10),(9,8),(12,6),(15,4),(20,2),(1e9,0)],
    "peg": [(0.5,10),(1,8),(1.5,6),(2,4),(3,2),(1e9,0)],
}

def score_tiered(v, bands):
    v = safe_float(v)
    if np.isnan(v): return np.nan
    for upper, sc in bands:
        if v <= upper: return sc
    return 0

def score_hi(v, lo, mid, hi):
    v = safe_float(v)
    if np.isnan(v): return np.nan
    if v >= hi: return 10
    if v >= mid: return 7
    if v >= lo: return 4
    return 1

def score_lo(v, good, mid, bad):
    v = safe_float(v)
    if np.isnan(v): return np.nan
    if v <= good: return 10
    if v <= mid: return 6
    if v <= bad: return 3
    return 0

def _blend(a, r):
    a = safe_float(a); r = safe_float(r)
    if np.isnan(a) and np.isnan(r): return np.nan
    if np.isnan(r): return a
    if np.isnan(a): return r
    return a * CONFIG["abs_weight"] + r * CONFIG["rel_weight"]

def _nm(lst):
    v = [safe_float(x) for x in lst if not np.isnan(safe_float(x))]
    return float(np.mean(v)) if v else np.nan

def rel_score(sv, mv, direction="lower_better"):
    sv = safe_float(sv); mv = safe_float(mv)
    if np.isnan(sv) or np.isnan(mv) or mv == 0: return np.nan
    ratio = sv / mv
    if direction == "lower_better":
        for t, sc in [(0.50,10),(0.70,8),(0.90,6),(1.10,4),(1.30,2)]: 
            if ratio <= t: return sc
        return 0
    else:
        for t, sc in [(2.00,10),(1.50,8),(1.20,6),(1.00,4),(0.80,2)]:
            if ratio >= t: return sc
        return 0

def momentum_multiplier(pct_12m):
    pct_12m = safe_float(pct_12m)
    if np.isnan(pct_12m): return 1.0
    if pct_12m >= 30: return 1.10
    if pct_12m >= 10: return 1.05
    if pct_12m >= 0: return 1.00
    if pct_12m >= -10: return 0.95
    return 0.85

def compute_sector_medians(df):
    metrics = ["pe_ttm","pb","ps","ev_ebitda","roe","roic","roa","fcf_yield"]
    result = {}
    for sector, grp in df.groupby("sector"):
        result[sector] = {}
        for m in metrics:
            if m in grp.columns:
                s = pd.to_numeric(grp[m], errors="coerce")
                result[sector][m] = safe_float(s.median(skipna=True))
    return result

def compute_scores(row, sm_dict):
    s = {}
    sm = sm_dict.get(row.get("sector","Unknown"), {})
    ra = lambda m: safe_float(row.get(m)); rm = lambda m: safe_float(sm.get(m))
    s["capital_efficiency"] = _nm([
        _blend(score_hi(ra("roe"), 12,18,25), rel_score(ra("roe"), rm("roe"), "higher_better")),
        _blend(score_hi(ra("roic"), 12,18,25), rel_score(ra("roic"), rm("roic"), "higher_better")),
        score_hi(ra("roa"), 5,10,15),
    ])
    s["valuation"] = _nm([
        _blend(score_tiered(ra("pe_ttm"), VALUATION_BANDS["pe_ttm"]), rel_score(ra("pe_ttm"), rm("pe_ttm"))),
        _blend(score_tiered(ra("pb"), VALUATION_BANDS["pb"]), rel_score(ra("pb"), rm("pb"))),
        _blend(score_tiered(ra("ps"), VALUATION_BANDS["ps"]), rel_score(ra("ps"), rm("ps"))),
        score_tiered(ra("ev_ebitda"), VALUATION_BANDS["ev_ebitda"]),
        score_tiered(ra("peg"), VALUATION_BANDS["peg"]),
        score_hi(ra("fcf_yield"), 2, 5, 8),
    ])
    s["growth_quality"] = _nm([
        score_hi(ra("revenue_cagr_3yr"), 8, 15, 25), score_hi(ra("op_income_cagr_3yr"), 10, 18, 30),
        score_hi(ra("operating_margin"), 8, 15, 25), score_hi(ra("revenue_growth_yoy"), 5, 12, 20),
    ])
    s["cashflow_quality"] = _nm([
        score_hi(ra("cf_quality"), 0.8, 1.0, 1.2), score_lo(ra("accruals_ratio"), -5, 0, 7),
        score_hi(ra("fcf_conversion"), 50, 70, 90),
    ])
    s["dupont_health"] = _nm([
        score_hi(ra("net_margin"), 5, 10, 20), score_hi(ra("asset_turnover"), 0.5, 0.8, 1.2),
        score_lo(ra("equity_multiplier"), 1.5, 2.5, 4.0),
    ])
    s["balance_sheet"] = _nm([
        score_hi(ra("current_ratio"), 1.2, 1.8, 2.5), score_hi(ra("interest_coverage"), 3, 6, 10),
        score_lo(ra("debt_to_equity"), 0.3, 0.7, 1.5),
    ])
    tw = ws = 0
    for cluster, w in CONFIG["cluster_weights"].items():
        v = s.get(cluster, np.nan)
        if not np.isnan(safe_float(v)): ws += v*w; tw += w
    base = (ws/tw)*10 if tw > 0 else np.nan
    mult = momentum_multiplier(ra("momentum_12m"))
    s["momentum_multiplier"] = mult
    s["composite_score"] = round(min(100, base * mult), 2) if not np.isnan(safe_float(base)) else np.nan
    return s

# =============================================================================
# PORTFOLIO CONSTRUCTION
# =============================================================================
def build_portfolio(df_scored, n, method, pval):
    if "yf_symbol" not in df_scored.columns: return None, None
    top_n = df_scored.dropna(subset=["yf_symbol"]).head(n).copy().reset_index(drop=True)
    yf_symbols = top_n["yf_symbol"].tolist()
    
    try:
        raw = yf.download(yf_symbols, period=CONFIG["price_history"], progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            prices = raw.xs('Close', level=0, axis=1) if 'Close' in raw.columns.levels[0] else raw
        else:
            prices = raw[['Close']] if 'Close' in raw.columns else raw
        if isinstance(prices, pd.Series): prices = prices.to_frame(yf_symbols[0])
        prices = prices.dropna(axis=1, how="all")
        returns = prices.pct_change().dropna()
    except Exception as e:
        st.error(f"Price Download Error: {e}")
        return None, None
        
    top_n_avail = top_n[top_n["yf_symbol"].isin(prices.columns)].copy()
    if len(top_n_avail) < 5: return None, None
    
    sym_list = top_n_avail["yf_symbol"].tolist()
    vol = returns[sym_list].std() * np.sqrt(252)
    
    if method == 1:
        sc = top_n_avail.set_index("yf_symbol")["composite_score"].apply(safe_float).fillna(0)
        raw_w = sc / sc.sum()
    elif method == 2:
        iv = 1.0 / vol.replace(0, np.nan).dropna()
        raw_w = iv / iv.sum()
    elif method == 3:
        sc = top_n_avail.set_index("yf_symbol")["composite_score"].apply(safe_float).fillna(0)
        sv = sc / (vol * 100 + 1e-9)
        raw_w = sv / sv.sum()
    elif method == 4:
        try:
            from pypfopt import EfficientFrontier, risk_models, expected_returns
            mu = expected_returns.mean_historical_return(prices[sym_list])
            S = risk_models.sample_cov(prices[sym_list])
            ef = EfficientFrontier(mu, S, weight_bounds=(CONFIG["min_position"], CONFIG["max_position"]))
            ef.max_sharpe(risk_free_rate=CONFIG["risk_free_rate"])
            raw_w = pd.Series(ef.clean_weights())
        except Exception as e:
            st.warning(f"Max Sharpe failed ({e}). Falling back to Score/Volatility.")
            sc = top_n_avail.set_index("yf_symbol")["composite_score"].apply(safe_float).fillna(0)
            sv = sc / (vol * 100 + 1e-9)
            raw_w = sv / sv.sum()
    elif method == 5:
        try:
            from pypfopt.hierarchical_portfolio import HRPOpt
            hrp = HRPOpt(returns[sym_list])
            hrp.optimize()
            raw_w = pd.Series(hrp.clean_weights())
        except Exception as e:
            st.warning(f"HRP failed ({e}). Falling back to Inverse Volatility.")
            iv = 1.0 / vol.replace(0, np.nan).dropna()
            raw_w = iv / iv.sum()

    raw_w = raw_w.clip(lower=CONFIG["min_position"], upper=CONFIG["max_position"])
    weights = raw_w / raw_w.sum()
    sym_to_sector = dict(zip(top_n_avail["yf_symbol"], top_n_avail["sector"]))
    sec_wts = {}
    for sym, w in weights.items():
        sec = sym_to_sector.get(sym, "Unknown")
        sec_wts[sec] = sec_wts.get(sec, 0) + w
    for sec, sw in list(sec_wts.items()):
        if sw > CONFIG["max_sector_wt"]:
            scale = CONFIG["max_sector_wt"] / sw
            for sym in list(weights.index):
                if sym_to_sector.get(sym) == sec: weights[sym] *= scale
    weights = weights / weights.sum()

    def w_avg(col):
        if col not in top_n_avail.columns: return np.nan
        vals = pd.to_numeric(top_n_avail.set_index("yf_symbol")[col], errors="coerce").reindex(weights.index)
        mask = vals.notna()
        if mask.sum() == 0: return np.nan
        w = weights[mask] / weights[mask].sum()
        return round(float((vals[mask] * w).sum()), 2)

    port_ret = (returns[list(weights.index)] * weights).sum(axis=1)
    ann_ret = float((1 + port_ret).prod() ** (252/len(port_ret)) - 1)
    ann_vol = float(port_ret.std() * np.sqrt(252))
    
    analytics = {
        "Annualised Return": f"{ann_ret*100:.2f}%", 
        "Annualised Volatility": f"{ann_vol*100:.2f}%",
        "Sharpe Ratio": f"{(ann_ret - CONFIG['risk_free_rate']) / ann_vol:.2f}" if ann_vol > 0 else "N/A",
        "Weighted P/E": w_avg("pe_ttm"),
        "Weighted ROIC (%)": w_avg("roic"),
        "Avg Piotroski F-Score": w_avg("piotroski_score")
    }

    port_cols = ["symbol","company_name","sector","composite_score","momentum_12m","piotroski_score","pe_ttm","roe","roic","fcf_yield","yf_symbol", "current_price"]
    avail_cols = [c for c in port_cols if c in top_n_avail.columns]
    port_df = top_n_avail[avail_cols].copy()
    port_df["weight_pct"] = port_df["yf_symbol"].map(weights) * 100
    port_df = port_df.sort_values("weight_pct", ascending=False).reset_index(drop=True)
    port_df["rank"] = port_df.index + 1
    
    if pval:
        port_df["alloc_inr"] = port_df["weight_pct"] / 100 * pval
        def calc_shares(r):
            cp = safe_float(r.get("current_price"))
            ai = safe_float(r.get("alloc_inr"))
            if np.isnan(cp) or cp <= 0 or np.isnan(ai): return np.nan
            return max(1, int(ai / cp))
        port_df["shares_to_buy"] = port_df.apply(calc_shares, axis=1)
        
    return port_df, analytics

# =============================================================================
# EXCEL EXPORT (Memory Buffer)
# =============================================================================
def create_excel_buffer(df_scored, df_gated, failed_list, port_df, analytics):
    wb = Workbook()
    navy = PatternFill("solid", fgColor="1F3864"); red = PatternFill("solid", fgColor="7B2C2C"); grn = PatternFill("solid", fgColor="1A5C38")
    wh = Font(color="FFFFFF", bold=True, size=10); ctr = Alignment(horizontal="center")
    
    def write_df(ws, df, cols, fill):
        avail = [c for c in cols if c in df.columns]
        for ci, col in enumerate(avail, 1):
            cell = ws.cell(row=1, column=ci, value=col.replace("_"," ").title())
            cell.fill = fill; cell.font = wh; cell.alignment = ctr
        for ri, (_, row) in enumerate(df[avail].iterrows(), 2):
            for ci, val in enumerate(row, 1):
                if isinstance(val, (float, np.floating)): v = "" if (pd.isna(val) or np.isinf(val)) else round(float(val), 2)
                elif pd.isna(val): v = ""
                else: v = val
                ws.cell(row=ri, column=ci, value=v).alignment = ctr
        for ci in range(1, len(avail)+1): ws.column_dimensions[get_column_letter(ci)].width = 16
        return avail

    ws1 = wb.active; ws1.title = "Screener Results"
    C1 = ["rank","symbol","company_name","sector","composite_score","momentum_multiplier","capital_efficiency","valuation","growth_quality","cashflow_quality","dupont_health","balance_sheet","piotroski_score","pe_ttm","roe","roic","fcf_yield","debt_to_equity"]
    write_df(ws1, df_scored, C1, navy)
    ws1.freeze_panes = "E2"

    if port_df is not None:
        ws2 = wb.create_sheet("Portfolio")
        C2 = ["rank","symbol","company_name","sector","weight_pct","composite_score","momentum_12m","piotroski_score","pe_ttm","roe","roic","fcf_yield","current_price"]
        if "alloc_inr" in port_df.columns: C2 += ["alloc_inr","shares_to_buy"]
        write_df(ws2, port_df, C2, grn)
        if analytics:
            sr = len(port_df) + 4
            ws2.cell(row=sr, column=1, value="PORTFOLIO ANALYTICS").font = Font(bold=True, size=12)
            for i, (k, v) in enumerate(analytics.items(), 1):
                ws2.cell(row=sr+i, column=1, value=k).font = Font(bold=True)
                ws2.cell(row=sr+i, column=2, value=str(v))
            ws2.column_dimensions["A"].width = 30
            
    ws3 = wb.create_sheet("Eliminated")
    write_df(ws3, df_gated, ["symbol","company_name","sector","gate_reason","debt_to_equity","interest_coverage","neg_ocf_count_3yr","operating_margin"], red)
    
    ws4 = wb.create_sheet("Failed")
    ws4.cell(row=1,column=1,value="Symbol").font = Font(bold=True); ws4.cell(row=1,column=2,value="Reason").font = Font(bold=True)
    for i, sym in enumerate(failed_list, 2):
        ws4.cell(row=i,column=1,value=sym["symbol"]); ws4.cell(row=i,column=2,value=sym["reason"])
    ws4.column_dimensions["B"].width = 50

    output = BytesIO()
    wb.save(output)
    return output.getvalue()

# =============================================================================
# UI LAYOUT
# =============================================================================
st.markdown('<div class="dash-title">⬛ QUANT SCREENER</div>', unsafe_allow_html=True)
st.markdown('<div class="dash-subtitle">Automated Multi-Factor Institutional Equity Screening</div>', unsafe_allow_html=True)
st.markdown("---")

with st.sidebar:
    st.markdown('<div class="section-header">⚙️ Screener Engine</div>', unsafe_allow_html=True)
    universe = st.selectbox("Universe", ["Nifty 500", "Nifty 750 (500 + Microcap)", "Quick Test (Top 30)"])
    st.markdown('<div class="section-header">💼 Portfolio Optimizer</div>', unsafe_allow_html=True)
    n_stocks = st.slider("Number of Stocks", 10, 40, 25)
    wt_method = st.selectbox("Weighting Method", ["Score / Volatility", "Score-Weighted", "Inverse Volatility", "Maximum Sharpe Ratio", "Hierarchical Risk Parity"])
    pval = st.number_input("Portfolio Value (₹)", min_value=10000, value=100000, step=10000)
    
    run_btn = st.button("🚀 Run Full Screener", use_container_width=True, type="primary")
    
    if st.button("🗑️ Clear Cache", use_container_width=True):
        count = sum([1 for f in os.listdir(CONFIG["cache_dir"]) if f.endswith(".json")] if os.path.exists(CONFIG["cache_dir"]) else [])
        for f in os.listdir(CONFIG["cache_dir"]): os.remove(os.path.join(CONFIG["cache_dir"], f))
        st.toast(f"Cleared {count} cached files.")

if run_btn:
    st.session_state["screener_run"] = True

if st.session_state.get("screener_run"):
    status_box = st.empty()
    progress_bar = st.progress(0)
    
    status_box.info("📥 Fetching index constituents...")
    df_uni = fetch_index_universe("nifty500")
    if universe == "Nifty 750 (500 + Microcap)":
        df_micro = fetch_index_universe("microcap250")
        df_uni = pd.concat([df_uni, df_micro]).drop_duplicates(subset=["Symbol"])
    
    symbols = df_uni["Symbol"].str.strip().tolist()
    sector_map = dict(zip(df_uni["Symbol"].str.strip(), df_uni[df_uni.columns[1]].str.strip()))
    if universe == "Quick Test (Top 30)": symbols = symbols[:30]
    
    records, failed = [], []
    for i, sym in enumerate(symbols):
        status_box.info(f"🔍 Deep Fundamental Analysis: {sym} ({i+1}/{len(symbols)})...")
        data = fetch_stock_data(sym, sector_map.get(sym, "Unknown"))
        if data["fetch_status"] != "failed": records.append(data)
        else: failed.append({"symbol": sym, "reason": data["error_msg"]})
        progress_bar.progress((i + 1) / len(symbols))
        
    progress_bar.empty()
    status_box.success(f"✅ Data fetched for {len(records)} stocks. Applying Quant Math...")
    
    df_all = pd.DataFrame(records)
    numeric_cols = ["pe_ttm","pb","ps","ev_ebitda","roe","roa","roic","fcf_yield","debt_to_equity","interest_coverage","operating_margin","current_ratio","beta","momentum_12m","revenue_cagr_3yr","op_income_cagr_3yr"]
    for col in numeric_cols: 
        if col in df_all.columns: df_all[col] = pd.to_numeric(df_all[col], errors="coerce")
    
    df_all["sector"] = df_all.apply(lambda r: r["sector"] if r["sector"] not in ["Unknown",""] else r.get("yf_sector","Unknown"), axis=1)
    
    gate_res = df_all.apply(apply_hard_gates, axis=1)
    df_all["passes_gate"] = gate_res.apply(lambda x: x[0])
    df_all["gate_reason"] = gate_res.apply(lambda x: x[1])

    df_passed = df_all[df_all["passes_gate"]].copy().reset_index(drop=True)
    df_gated  = df_all[~df_all["passes_gate"]].copy().reset_index(drop=True)
    
    status_box.info(f"🛡️ Passed Gates: {len(df_passed)} | Eliminated: {len(df_gated)}. Computing Sector Medians...")
    
    # --- ADD THIS NEW SAFETY CHECK HERE ---
    if df_passed.empty:
        status_box.empty()
        st.error("⚠️ Zero stocks passed the Hard Gates! Try increasing your universe or checking Yahoo Finance data.")
        st.stop()
    # --------------------------------------
    
    sector_medians = compute_sector_medians(df_passed)
    
    sector_medians = compute_sector_medians(df_passed)
    score_rows = df_passed.apply(lambda row: compute_scores(row.to_dict(), sector_medians), axis=1)
    df_scored  = pd.concat([df_passed, pd.DataFrame(score_rows.tolist())], axis=1)
    df_scored  = df_scored.sort_values("composite_score", ascending=False).reset_index(drop=True)
    df_scored["rank"] = df_scored.index + 1
    
    status_box.info("⚖️ Optimizing Portfolio Weights (Matrix Math)...")
    method_map = {"Score-Weighted": 1, "Inverse Volatility": 2, "Score / Volatility": 3, "Maximum Sharpe Ratio": 4, "Hierarchical Risk Parity": 5}
    port_df, analytics = build_portfolio(df_scored, n_stocks, method_map[wt_method], pval)
    
    status_box.empty()
    
    # Render Output
    tab_port, tab_screen, tab_elim, tab_failed = st.tabs(["📊 Optimized Portfolio", "🏆 Full Screener Results", "🚫 Eliminated", "⚠️ Fetch Failed"])
    
    with tab_port:
        if port_df is not None:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Expected Annual Return", analytics["Annualised Return"])
            c2.metric("Portfolio Volatility", analytics["Annualised Volatility"])
            c3.metric("Est. Sharpe Ratio", analytics["Sharpe Ratio"])
            c4.metric("Avg Piotroski F-Score", analytics.get("Avg Piotroski F-Score", "N/A"))
            
            st.markdown("<br>", unsafe_allow_html=True)
            show_cols = ["rank", "symbol", "sector", "weight_pct"]
            if "shares_to_buy" in port_df.columns: show_cols += ["alloc_inr", "shares_to_buy"]
            show_cols += ["composite_score", "piotroski_score", "pe_ttm", "roic"]
            
            st.dataframe(
                port_df[show_cols].style
                .format({"weight_pct": "{:.2f}%", "alloc_inr": "₹{:,.0f}", "composite_score": "{:.1f}", "pe_ttm": "{:.1f}", "roic": "{:.1f}%"})
                .background_gradient(subset=["weight_pct"], cmap="Blues"),
                use_container_width=True, hide_index=True
            )
            
            # Generate Excel Button
            excel_data = create_excel_buffer(df_scored, df_gated, failed, port_df, analytics)
            st.download_button(
                label="📥 Download Full Excel Report",
                data=excel_data,
                file_name=f"Quant_Screener_Results_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        else:
            st.error("Not enough data to build portfolio. Try increasing the universe size.")
            
    with tab_screen:
        show_screen = ["rank", "symbol", "company_name", "sector", "composite_score", "piotroski_score", "capital_efficiency", "valuation", "growth_quality", "cashflow_quality", "pe_ttm", "roe", "roic"]
        st.dataframe(
            df_scored[[c for c in show_screen if c in df_scored.columns]].style
            .format({"composite_score": "{:.1f}", "capital_efficiency": "{:.1f}", "valuation": "{:.1f}", "growth_quality": "{:.1f}", "cashflow_quality": "{:.1f}", "pe_ttm": "{:.1f}", "roe": "{:.1f}%", "roic": "{:.1f}%"})
            .background_gradient(subset=["composite_score"], cmap="RdYlGn"),
            use_container_width=True, hide_index=True
        )

    with tab_elim:
        st.dataframe(df_gated[["symbol", "company_name", "sector", "gate_reason", "debt_to_equity", "interest_coverage", "operating_margin"]], use_container_width=True, hide_index=True)
        
    with tab_failed:
        st.dataframe(pd.DataFrame(failed), use_container_width=True, hide_index=True)
