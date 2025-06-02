# app.py

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ------------------------------
# Caching Decorators
# ------------------------------

@st.cache_data
def fetch_yfinance_data(symbol: str, period: str = "5y"):
    """
    Fetch historical price and fundamentals data from yfinance.
    """
    ticker = yf.Ticker(symbol)
    
    # Historical price data
    hist = ticker.history(period=period, actions=False).dropna()
    
    # Basic info
    info = ticker.info
    
    # Financial statements
    income_stmt = ticker.financials.T  # Transposed for easier access
    balance_sheet = ticker.balance_sheet.T
    cashflow = ticker.cashflow.T
    
    return {
        "info": info,
        "history": hist,
        "income": income_stmt,
        "balance": balance_sheet,
        "cashflow": cashflow,
    }

@st.cache_data
def fetch_tushare_data(symbol: str):
    """
    Placeholder for future A-share (Tushare) data fetching.
    """
    # TODO: Implement tushare data fetch
    return None

# ------------------------------
# Fundamental Analysis Functions
# ------------------------------

def piotroski_score(income: pd.DataFrame, balance: pd.DataFrame, cashflow: pd.DataFrame) -> (int, dict):
    """
    Calculate Piotroski F-score based on financial statements.
    Returns the score and a dictionary of individual criteria.
    """
    criteria = {}

    # Ensure at least two years of data
    if income.shape[0] < 2 or balance.shape[0] < 2 or cashflow.shape[0] < 2:
        return 0, criteria

    # Latest and prior year
    latest = income.index[0]
    prior = income.index[1]

    # 1. Net Income > 0
    ni = income.loc[latest, "Net Income"]
    criteria["NI_Positive"] = int(ni > 0)

    # 2. Operating Cash Flow > 0
    cfo = cashflow.loc[latest, "Total Cash From Operating Activities"]
    criteria["CFO_Positive"] = int(cfo > 0)

    # 3. ROA improvement: (NI / Total Assets) vs prior
    ta_latest = balance.loc[latest, "Total Assets"]
    ta_prior = balance.loc[prior, "Total Assets"]
    roa_latest = ni / ta_latest if ta_latest != 0 else 0
    roa_prior = income.loc[prior, "Net Income"] / ta_prior if ta_prior != 0 else 0
    criteria["ROA_Improved"] = int(roa_latest > roa_prior)

    # 4. CFO > NI
    criteria["CFO_gt_NI"] = int(cfo > ni)

    # 5. Long-term debt decreased: (LTD liabilities)
    ltd_latest = balance.loc[latest, "Long Term Debt"] if "Long Term Debt" in balance.columns else 0
    ltd_prior = balance.loc[prior, "Long Term Debt"] if "Long Term Debt" in balance.columns else 0
    criteria["Debt_Decreased"] = int(ltd_latest < ltd_prior)

    # 6. Current ratio improved: (Current Assets / Current Liabilities)
    ca_latest = balance.loc[latest, "Total Current Assets"]
    cl_latest = balance.loc[latest, "Total Current Liabilities"]
    ca_prior = balance.loc[prior, "Total Current Assets"]
    cl_prior = balance.loc[prior, "Total Current Liabilities"]
    cr_latest = ca_latest / cl_latest if cl_latest != 0 else 0
    cr_prior = ca_prior / cl_prior if cl_prior != 0 else 0
    criteria["Current_Ratio_Improved"] = int(cr_latest > cr_prior)

    # 7. Shares outstanding no new issuance: compare shares
    # yfinance does not provide shares outstanding history directly; assume constant for prototype
    criteria["No_New_Shares"] = 1

    # 8. Gross margin improvement: (Revenue - COGS) / Revenue
    rev_latest = income.loc[latest, "Total Revenue"]
    cogs_latest = income.loc[latest, "Cost Of Revenue"] if "Cost Of Revenue" in income.columns else 0
    gm_latest = (rev_latest - cogs_latest) / rev_latest if rev_latest != 0 else 0

    rev_prior = income.loc[prior, "Total Revenue"]
    cogs_prior = income.loc[prior, "Cost Of Revenue"] if "Cost Of Revenue" in income.columns else 0
    gm_prior = (rev_prior - cogs_prior) / rev_prior if rev_prior != 0 else 0

    criteria["Gross_Margin_Improved"] = int(gm_latest > gm_prior)

    # 9. Asset turnover improvement: Revenue / Total Assets
    at_latest = rev_latest / ta_latest if ta_latest != 0 else 0
    at_prior = rev_prior / ta_prior if ta_prior != 0 else 0
    criteria["Asset_Turnover_Improved"] = int(at_latest > at_prior)

    score = sum(criteria.values())
    return score, criteria

def dupont_analysis(income: pd.DataFrame, balance: pd.DataFrame) -> dict:
    """
    Perform DuPont analysis: ROE = (Net Income / Revenue) * (Revenue / Assets) * (Assets / Equity)
    """
    result = {}
    if income.shape[0] < 1 or balance.shape[0] < 1:
        return result

    latest = income.index[0]
    # Net Income Margin
    net_income = income.loc[latest, "Net Income"]
    revenue = income.loc[latest, "Total Revenue"]
    margin = net_income / revenue if revenue != 0 else np.nan
    result["Profit_Margin"] = margin

    # Asset Turnover
    ta = balance.loc[latest, "Total Assets"]
    at = revenue / ta if ta != 0 else np.nan
    result["Asset_Turnover"] = at

    # Equity Multiplier
    te = balance.loc[latest, "Total Stockholder Equity"]
    em = ta / te if te != 0 else np.nan
    result["Equity_Multiplier"] = em

    # ROE
    result["ROE"] = margin * at * em if not any(np.isnan([margin, at, em])) else np.nan

    return result

def altman_zscore(balance: pd.DataFrame, income: pd.DataFrame, info: dict) -> float:
    """
    Calculate Altman Z-score for public manufacturing companies (original formula).
    Z = 1.2*(WC/TA) + 1.4*(RE/TA) + 3.3*(EBIT/TA) + 0.6*(MVE/TL) + (Sales/TA)
    """
    if balance.shape[0] < 1 or income.shape[0] < 1:
        return np.nan

    latest = balance.index[0]
    # Working Capital = Current Assets - Current Liabilities
    ca = balance.loc[latest, "Total Current Assets"]
    cl = balance.loc[latest, "Total Current Liabilities"]
    wc = ca - cl

    ta = balance.loc[latest, "Total Assets"]
    re = balance.loc[latest, "Retained Earnings"]

    # EBIT
    ebit = income.loc[latest, "Ebit"] if "Ebit" in income.columns else income.loc[latest, "Operating Income"] if "Operating Income" in income.columns else np.nan

    # Market Value of Equity
    mve = info.get("marketCap", np.nan)

    # Total Liabilities
    tl = balance.loc[latest, "Total Liab"] if "Total Liab" in balance.columns else balance.loc[latest, "Total Liabilities"] if "Total Liabilities" in balance.columns else np.nan

    # Sales
    sales = income.loc[latest, "Total Revenue"]

    z = (
        1.2 * (wc / ta if ta != 0 else 0)
        + 1.4 * (re / ta if ta != 0 else 0)
        + 3.3 * (ebit / ta if ta != 0 else 0)
        + 0.6 * (mve / tl if tl != 0 else 0)
        + (sales / ta if ta != 0 else 0)
    )
    return round(z, 2)

def dcf_valuation(cashflow: pd.DataFrame, info: dict) -> dict:
    """
    Perform a simplified 5-year DCF valuation.
    Assumptions:
    - Use last year's Free Cash Flow (FCF) = CFO - CapEx
    - Assume a constant growth rate equal to (FCF_Latest / FCF_Prior) - 1
    - Discount rate = WACC approximated by CAPM: rf + beta*(rm - rf)
    """
    result = {}
    if cashflow.shape[0] < 2:
        return result

    # Latest and prior year
    latest = cashflow.index[0]
    prior = cashflow.index[1]

    # Calculate FCF
    cfo_latest = cashflow.loc[latest, "Total Cash From Operating Activities"]
    capex_latest = cashflow.loc[latest, "Capital Expenditures"] if "Capital Expenditures" in cashflow.columns else 0
    fcf_latest = cfo_latest + capex_latest  # capex is negative in yfinance

    cfo_prior = cashflow.loc[prior, "Total Cash From Operating Activities"]
    capex_prior = cashflow.loc[prior, "Capital Expenditures"] if "Capital Expenditures" in cashflow.columns else 0
    fcf_prior = cfo_prior + capex_prior

    # Estimate growth rate
    growth_rate = (fcf_latest / fcf_prior - 1) if fcf_prior != 0 else 0.0
    growth_rate = max(min(growth_rate, 0.20), 0.0)  # Cap growth at 20%

    # Estimate discount rate via CAPM
    beta = info.get("beta", 1.0)
    rf = 0.02  # risk-free rate 2%
    rm = 0.07  # market return 7%
    wacc = rf + beta * (rm - rf)

    # Project FCF for next 5 years
    fcf_projections = [(fcf_latest * ((1 + growth_rate) ** i)) for i in range(1, 6)]

    # Discount projected FCFs
    discounted_fcf = [
        fcf_projections[i] / ((1 + wacc) ** (i + 1)) for i in range(5)
    ]
    pv_fcf = sum(discounted_fcf)

    # Terminal value using Gordon Growth (assume perpetual growth = 2%)
    perp_growth = 0.02
    terminal_value = fcf_projections[-1] * (1 + perp_growth) / (wacc - perp_growth)
    pv_terminal = terminal_value / ((1 + wacc) ** 5)

    # Enterprise Value
    ev = pv_fcf + pv_terminal

    # Equity Value = EV - debt + cash
    debt = info.get("totalDebt", 0)
    cash = info.get("totalCash", 0)
    equity_value = ev - debt + cash

    # Shares outstanding
    shares = info.get("sharesOutstanding", np.nan)
    intrinsic_price = equity_value / shares if shares else np.nan

    result["Intrinsic_Value"] = round(intrinsic_price, 2)
    result["WACC"] = round(wacc, 4)
    result["Growth_Rate"] = round(growth_rate, 4)
    return result

def relative_valuation(info: dict) -> dict:
    """
    Calculate PE, PB, EV/EBITDA.
    """
    result = {}
    price = info.get("currentPrice", np.nan)
    eps = info.get("trailingEps", np.nan)
    bv = info.get("bookValue", np.nan)
    ebidta = info.get("ebitda", np.nan)

    # PE
    result["PE"] = round(price / eps, 2) if eps else np.nan

    # PB
    result["PB"] = round(price / bv, 2) if bv else np.nan

    # EV/EBITDA
    mcap = info.get("marketCap", np.nan)
    debt = info.get("totalDebt", 0)
    cash = info.get("totalCash", 0)
    ev = mcap + debt - cash
    result["EV_EBITDA"] = round(ev / ebidta, 2) if ebidta else np.nan

    return result

def safety_margin(intrinsic: float, current: float) -> float:
    """
    Calculate safety margin: (Intrinsic - Market Price) / Intrinsic
    """
    if intrinsic and current:
        return round((intrinsic - current) / intrinsic * 100, 2)
    return np.nan

# ------------------------------
# Technical Analysis Functions
# ------------------------------

@st.cache_data
def compute_technical_indicators(history: pd.DataFrame) -> pd.DataFrame:
    """
    Compute 60-day SMA, 12-26-9 MACD, and volume average.
    """
    df = history.copy()
    df["SMA_60"] = df["Close"].rolling(window=60).mean()

    # MACD
    exp1 = df["Close"].ewm(span=12, adjust=False).mean()
    exp2 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = exp1 - exp2
    df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # Volume average
    df["Vol_Avg_30"] = df["Volume"].rolling(window=30).mean()

    return df

def generate_technical_plots(df: pd.DataFrame):
    """
    Generate line charts for SMA and MACD, and highlight golden cross.
    """
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df.index, df["Close"], label="Close", linewidth=1)
    ax.plot(df.index, df["SMA_60"], label="SMA 60-day", linewidth=1)
    ax.set_title("Price & 60-Day SMA")
    ax.legend()
    st.pyplot(fig)

    fig2, ax2 = plt.subplots(figsize=(8, 3))
    ax2.plot(df.index, df["MACD"], label="MACD", linewidth=1)
    ax2.plot(df.index, df["Signal_Line"], label="Signal Line", linewidth=1)
    ax2.set_title("MACD & Signal Line")
    ax2.legend()
    st.pyplot(fig2)

    # Volume bar chart with average
    fig3, ax3 = plt.subplots(figsize=(8, 2))
    ax3.bar(df.index, df["Volume"], alpha=0.5, label="Volume")
    ax3.plot(df.index, df["Vol_Avg_30"], color="orange", label="30-Day Vol Avg", linewidth=1)
    ax3.set_title("Volume & 30-Day Average")
    ax3.legend()
    st.pyplot(fig3)

def check_macd_signal(df: pd.DataFrame) -> str:
    """
    Check for MACD golden cross in last 2 days.
    """
    if df.shape[0] < 2:
        return "Neutral"
    prev_macd = df["MACD"].iloc[-2]
    prev_signal = df["Signal_Line"].iloc[-2]
    curr_macd = df["MACD"].iloc[-1]
    curr_signal = df["Signal_Line"].iloc[-1]
    if prev_macd < prev_signal and curr_macd > curr_signal:
        return "Bullish"
    elif prev_macd > prev_signal and curr_macd < curr_signal:
        return "Bearish"
    return "Neutral"

# ------------------------------
# Risk & Position Sizing Function
# ------------------------------

@st.cache_data
def kelly_criterion(history: pd.DataFrame) -> float:
    """
    Simplified Kelly formula: f* = mu / sigma^2
    where mu and sigma are average and standard deviation of daily returns.
    """
    returns = history["Close"].pct_change().dropna()
    mu = returns.mean()
    sigma2 = returns.var()
    if sigma2 == 0:
        return 0.0
    f = mu / sigma2
    return round(max(min(f, 1), 0), 4)  # constrain between 0 and 1

# ------------------------------
# Streamlit App
# ------------------------------

st.set_page_config(
    page_title="💹 我的智能投资分析系统",
    layout="wide"
)

st.title("💹 我的智能投资分析系统")

# Sidebar: User Inputs
st.sidebar.header("🔧 输入设置")
symbol = st.sidebar.text_input("请输入股票代码（如 AAPL）").upper().strip()
market = st.sidebar.selectbox("市场选择", ["US（默认）", "CN（A股-预留）"])
st.sidebar.markdown("---")

if symbol:
    # Fetch data based on market
    if market == "US（默认）":
        data = fetch_yfinance_data(symbol)
    else:
        data = fetch_tushare_data(symbol)  # placeholder

    if data:
        info = data["info"]
        history = data["history"]
        income = data["income"]
        balance = data["balance"]
        cashflow = data["cashflow"]

        # ------------------------------
        # Run analysis models
        # ------------------------------
        # Fundamental Models
        f_score, f_details = piotroski_score(income, balance, cashflow)
        dupont = dupont_analysis(income, balance)
        z_score = altman_zscore(balance, income, info)
        dcf = dcf_valuation(cashflow, info)
        rel_val = relative_valuation(info)
        current_price = info.get("currentPrice", np.nan)
        intrinsic = dcf.get("Intrinsic_Value", np.nan)
        margin = safety_margin(intrinsic, current_price)

        # Technical Models
        tech_df = compute_technical_indicators(history)
        macd_signal = check_macd_signal(tech_df)
        kelly = kelly_criterion(history)

        # ------------------------------
        # Layout: Columns
        # ------------------------------
        col1, col2, col3 = st.columns([1, 2, 1])

        # ------------------------------
        # Left Column: Company Basic Info
        # ------------------------------
        with col1:
            st.subheader("🏢 公司基本信息")
            logo_url = info.get("logo_url", None)
            if logo_url:
                st.image(logo_url, width=120)
            st.markdown(f"**名称**: {info.get('longName', 'N/A')}")
            st.markdown(f"**代码**: {symbol}")
            st.markdown(f"**市值**: {info.get('marketCap', 'N/A')}")
            st.markdown(f"**行业**: {info.get('industry', 'N/A')}")
            st.markdown(f"**Beta**: {info.get('beta', 'N/A')}")
            st.markdown(f"**当前价**: {current_price}")
            st.markdown("---")

        # ------------------------------
        # Middle Column: Valuation Models
        # ------------------------------
        with col2:
            st.subheader("🔍 估值模型与结果")

            # Piotroski F-score
            st.markdown(f"**Piotroski F-score**: {f_score} / 9")
            st.markdown("详细项：")
            for k, v in f_details.items():
                st.markdown(f"- {k.replace('_', ' ')}: {'通过' if v else '未通过'}")
            st.markdown("---")

            # DuPont Analysis
            st.markdown("**DuPont 分析**")
            if dupont:
                st.markdown(f"- 利润率 (Net Profit Margin): {dupont.get('Profit_Margin', 'N/A'):.2%}")
                st.markdown(f"- 资产周转率 (Asset Turnover): {dupont.get('Asset_Turnover', 'N/A'):.2f}")
                st.markdown(f"- 权益乘数 (Equity Multiplier): {dupont.get('Equity_Multiplier', 'N/A'):.2f}")
                st.markdown(f"- ROE: {dupont.get('ROE', np.nan):.2%}")
            else:
                st.markdown("数据不足，无法计算。")
            st.markdown("---")

            # Altman Z-score
            st.markdown(f"**Altman Z-score**: {z_score}")
            if z_score:
                if z_score > 2.99:
                    st.markdown("财务健康状况：安全区")
                elif z_score > 1.81:
                    st.markdown("财务健康状况：灰色区")
                else:
                    st.markdown("财务健康状况：困境区")
            st.markdown("---")

            # DCF Valuation
            st.markdown("**DCF 估值**")
            if dcf:
                st.markdown(f"- 内在价值 (每股): ${dcf.get('Intrinsic_Value', 'N/A')}")
                st.markdown(f"- WACC: {dcf.get('WACC', 'N/A'):.2%}")
                st.markdown(f"- 假设现金流增长率: {dcf.get('Growth_Rate', 'N/A'):.2%}")
            else:
                st.markdown("数据不足，无法计算。")
            st.markdown("---")

            # Relative Valuation
            st.markdown("**相对估值指标**")
            st.markdown(f"- PE: {rel_val.get('PE', 'N/A')}")
            st.markdown(f"- PB: {rel_val.get('PB', 'N/A')}")
            st.markdown(f"- EV/EBITDA: {rel_val.get('EV_EBITDA', 'N/A')}")
            st.markdown("---")

            # Safety Margin
            st.markdown("**安全边际评估**")
            if not np.isnan(margin):
                st.markdown(f"- 安全边际: {margin:.2f}%")
            else:
                st.markdown("- 数据不足，无法计算安全边际。")
            st.markdown("---")

            # Kelly Criterion
            st.markdown("**Kelly 公式推荐仓位**")
            st.markdown(f"- 建议仓位比: {kelly:.2%}")
            st.markdown("---")

        # ------------------------------
        # Right Column: Charts & Recommendation
        # ------------------------------
        with col3:
            st.subheader("📊 可视化 & 建议")

            # Safety Margin Bar Chart
            if not np.isnan(margin):
                fig_sm, ax_sm = plt.subplots(figsize=(4, 1.5))
                ax_sm.bar(["安全边际"], [margin], color=["#2E86C1"])
                ax_sm.set_ylim([-100, 100])
                ax_sm.set_ylabel("%")
                ax_sm.set_title("安全边际")
                st.pyplot(fig_sm)
            else:
                st.markdown("无安全边际可视化数据。")

            st.markdown("---")

            # Technical Charts
            st.markdown("**技术面信号**")
            generate_technical_plots(tech_df)
            st.markdown(f"MACD 信号: **{macd_signal}**")
            st.markdown("---")

            # Recommendation Logic
            def recommend_action(margin: float, macd_signal: str) -> (str, str, str):
                """
                Recommend BUY / WAIT / SELL based on safety margin and technical signal.
                """
                if np.isnan(margin):
                    return "WAIT", "数据不足，无法提供建议。", "中"
                # Example thresholds
                if margin > 20 and macd_signal == "Bullish":
                    return "BUY", "内在价值显著高于市价，技术面强势。", "低"
                elif margin < -10 and macd_signal == "Bearish":
                    return "SELL", "股价高于合理估值，技术面转弱。", "高"
                else:
                    return "WAIT", "综合指标不明确，建议观望。", "中"

            action, reason, risk = recommend_action(margin, macd_signal)
            st.markdown("**投资建议**")
            st.markdown(f"- 行动: **{action}**")
            st.markdown(f"- 原因: {reason}")
            st.markdown(f"- 风险等级: {risk}")

            # Placeholder: One-click Export Report
            st.markdown("---")
            st.button("导出完整分析报告（预留）")

    else:
        st.error("无法获取数据，请检查股票代码或网络连接。")
else:
    st.info("请输入有效股票代码以开始分析。")
