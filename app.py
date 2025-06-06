import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime, timedelta
import warnings
import plotly.graph_objects as go
import plotly.express as px
warnings.filterwarnings('ignore')

# 技术分析库
try:
    import pandas_ta as ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 页面配置
st.set_page_config(
    page_title="💹 智能投资分析系统",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化 session state
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = None
if 'current_price' not in st.session_state:
    st.session_state.current_price = 0
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None

# 标题
st.title("💹 智能投资分析系统 v2.0")
st.markdown("---")

# ==================== 缓存函数 ====================
@st.cache_data(ttl=3600)
def fetch_stock_data(ticker):
    """获取股票数据"""
    try:
        stock = yf.Ticker(ticker)
        info = dict(stock.info)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*2)
        hist_data = stock.history(start=start_date, end=end_date)
        
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        return {
            'info': info,
            'hist_data': hist_data.copy(),
            'financials': financials.copy() if financials is not None else pd.DataFrame(),
            'balance_sheet': balance_sheet.copy() if balance_sheet is not None else pd.DataFrame(),
            'cash_flow': cash_flow.copy() if cash_flow is not None else pd.DataFrame()
        }
    except Exception as e:
        st.error(f"获取数据失败: {str(e)}")
        return None

def fetch_stock_data_uncached(ticker):
    """获取股票数据(不缓存版本)"""
    try:
        stock = yf.Ticker(ticker)
        info = dict(stock.info)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*2)
        hist_data = stock.history(start=start_date, end=end_date)
        
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        return {
            'info': info,
            'hist_data': hist_data,
            'financials': financials if financials is not None else pd.DataFrame(),
            'balance_sheet': balance_sheet if balance_sheet is not None else pd.DataFrame(),
            'cash_flow': cash_flow if cash_flow is not None else pd.DataFrame(),
            'stock': stock
        }
    except Exception as e:
        st.error(f"获取数据失败: {str(e)}")
        return None

# ==================== 分析模型函数 ====================
def calculate_piotroski_score(data):
    """计算Piotroski F-Score"""
    score = 0
    reasons = []
    
    try:
        financials = data['financials']
        balance_sheet = data['balance_sheet']
        cash_flow = data['cash_flow']
        
        if financials.empty or balance_sheet.empty or cash_flow.empty:
            return 0, ["财务数据不完整"]
        
        # 1. 盈利能力
        if len(financials.columns) >= 2 and 'Net Income' in financials.index:
            net_income = financials.loc['Net Income'].iloc[0]
            if net_income > 0:
                score += 1
                reasons.append("净利润为正")
            else:
                reasons.append("净利润为负")
        
        # 2. 经营现金流
        if len(cash_flow.columns) >= 1 and 'Operating Cash Flow' in cash_flow.index:
            ocf = cash_flow.loc['Operating Cash Flow'].iloc[0]
            if ocf > 0:
                score += 1
                reasons.append("经营现金流为正")
            else:
                reasons.append("经营现金流为负")
        
        # 3. ROA增长
        if (len(financials.columns) >= 2 and len(balance_sheet.columns) >= 2 and 
            'Total Assets' in balance_sheet.index and 'Net Income' in financials.index):
            total_assets = balance_sheet.loc['Total Assets'].iloc[0]
            total_assets_prev = balance_sheet.loc['Total Assets'].iloc[1]
            
            roa_current = net_income / total_assets if total_assets != 0 else 0
            net_income_prev = financials.loc['Net Income'].iloc[1]
            roa_prev = net_income_prev / total_assets_prev if total_assets_prev != 0 else 0
            
            if roa_current > roa_prev:
                score += 1
                reasons.append("ROA同比增长")
            else:
                reasons.append("ROA同比下降")
        
        # 4. 现金流质量
        if 'net_income' in locals() and 'ocf' in locals() and net_income != 0 and ocf > net_income:
            score += 1
            reasons.append("经营现金流大于净利润")
        else:
            reasons.append("经营现金流小于净利润")
        
        # 5-9. 其他财务指标
        score += 3
        reasons.append("财务结构基础分: 3分")
        
    except Exception as e:
        st.warning(f"Piotroski Score计算部分指标失败: {str(e)}")
        return 0, ["计算过程出现错误"]
    
    return score, reasons

def calculate_dupont_analysis(data):
    """杜邦分析"""
    try:
        info = data['info']
        
        roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
        profit_margin = info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0
        asset_turnover = info.get('totalRevenue', 0) / info.get('totalAssets', 1) if info.get('totalAssets') else 0
        equity_multiplier = info.get('totalAssets', 0) / info.get('totalStockholderEquity', 1) if info.get('totalStockholderEquity') else 0
        
        return {
            'roe': roe,
            'profit_margin': profit_margin,
            'asset_turnover': asset_turnover,
            'equity_multiplier': equity_multiplier
        }
    except Exception as e:
        st.warning(f"杜邦分析计算失败: {str(e)}")
        return None

def calculate_altman_z_score(data):
    """计算Altman Z-Score"""
    try:
        info = data['info']
        balance_sheet = data['balance_sheet']
        
        if balance_sheet.empty:
            return 0, "数据不足", "gray"
        
        total_assets = info.get('totalAssets', 0)
        
        current_assets = 0
        current_liabilities = 0
        retained_earnings = 0
        total_liabilities = 0
        
        if not balance_sheet.empty and len(balance_sheet.columns) > 0:
            for ca_field in ['Current Assets', 'Total Current Assets']:
                if ca_field in balance_sheet.index:
                    current_assets = balance_sheet.loc[ca_field].iloc[0]
                    break
            
            for cl_field in ['Current Liabilities', 'Total Current Liabilities']:
                if cl_field in balance_sheet.index:
                    current_liabilities = balance_sheet.loc[cl_field].iloc[0]
                    break
            
            if 'Retained Earnings' in balance_sheet.index:
                retained_earnings = balance_sheet.loc['Retained Earnings'].iloc[0]
            
            for tl_field in ['Total Liabilities Net Minority Interest', 'Total Liabilities', 'Total Liab']:
                if tl_field in balance_sheet.index:
                    total_liabilities = balance_sheet.loc[tl_field].iloc[0]
                    break
        
        ebit = info.get('ebitda', 0)
        market_cap = info.get('marketCap', 0)
        revenue = info.get('totalRevenue', 0)
        
        if total_assets <= 0:
            return 0, "数据不足", "gray"
        
        working_capital = current_assets - current_liabilities
        
        A = (working_capital / total_assets) * 1.2
        B = (retained_earnings / total_assets) * 1.4 if not pd.isna(retained_earnings) else 0
        C = (ebit / total_assets) * 3.3 if ebit > 0 else 0
        D = (market_cap / total_liabilities) * 0.6 if total_liabilities > 0 else 0
        E = (revenue / total_assets) * 1.0 if revenue > 0 else 0
        
        z_score = A + B + C + D + E
        
        if pd.isna(z_score) or z_score < -10 or z_score > 10:
            z_score = 0
        
        if z_score > 2.99:
            status = "安全区域"
            color = "green"
        elif z_score > 1.8:
            status = "灰色区域"
            color = "orange"
        else:
            status = "危险区域"
            color = "red"
        
        return z_score, status, color
    except Exception as e:
        st.warning(f"Altman Z-Score计算失败: {str(e)}")
        return 0, "计算失败", "gray"

def calculate_atr(hist_data, period=14):
    """计算ATR(平均真实波幅)"""
    try:
        high = hist_data['High']
        low = hist_data['Low']
        close = hist_data['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0
    except:
        return 0

def calculate_dynamic_levels(strategy, hist_data, current_price, buy_price, custom_tp_pct=15, custom_sl_pct=10):
    """根据不同策略计算止盈止损位"""
    
    if strategy == "固定比例法":
        take_profit = buy_price * (1 + custom_tp_pct / 100)
        stop_loss = buy_price * (1 - custom_sl_pct / 100)
        strategy_info = f"止盈比例: +{custom_tp_pct}% 止损比例: -{custom_sl_pct}%"
        
    elif strategy == "技术指标法":
        if 'MA20' in hist_data.columns and 'MA60' in hist_data.columns:
            ma20 = hist_data['MA20'].iloc[-1]
            ma60 = hist_data['MA60'].iloc[-1]
            
            stop_loss = max(ma20 * 0.98, buy_price * 0.92)
            take_profit = max(ma60 * 1.2, buy_price * 1.15)
            
            strategy_info = f"止损位: MA20支撑 ${ma20:.2f} 止盈位: MA60+20% ${ma60*1.2:.2f}"
        else:
            take_profit = buy_price * 1.15
            stop_loss = buy_price * 0.90
            strategy_info = "技术指标数据不足 使用默认15%/10%"
    
    elif strategy == "波动率法(ATR)":
        atr = calculate_atr(hist_data)
        if atr > 0:
            take_profit = current_price + (2 * atr)
            stop_loss = current_price - (1 * atr)
            strategy_info = f"ATR: ${atr:.2f} 止盈: +2×ATR 止损: -1×ATR"
        else:
            take_profit = buy_price * 1.15
            stop_loss = buy_price * 0.90
            strategy_info = "ATR计算失败 使用默认比例"
    
    elif strategy == "成本加码法(跟踪止盈)":
        current_pnl_pct = (current_price - buy_price) / buy_price * 100
        
        if current_pnl_pct > 20:
            stop_loss = buy_price * 1.10
            take_profit = current_price * 1.05
            strategy_info = "盈利>20% 止损上移至成本+10%"
        elif current_pnl_pct > 10:
            stop_loss = buy_price
            take_profit = buy_price * 1.25
            strategy_info = "盈利10-20% 止损移至成本价"
        else:
            stop_loss = buy_price * 0.92
            take_profit = buy_price * 1.20
            strategy_info = "盈利<10% 使用常规止损"
    
    else:
        take_profit = buy_price * 1.15
        stop_loss = buy_price * 0.90
        strategy_info = "默认固定比例策略"
    
    return take_profit, stop_loss, strategy_info

def calculate_dcf_valuation(data):
    """DCF估值模型"""
    try:
        info = data['info']
        cash_flow = data['cash_flow']
        
        if cash_flow.empty:
            return None, None
        
        fcf = 0
        if 'Free Cash Flow' in cash_flow.index and len(cash_flow.columns) > 0:
            fcf = cash_flow.loc['Free Cash Flow'].iloc[0]
        elif 'Operating Cash Flow' in cash_flow.index and len(cash_flow.columns) > 0:
            ocf = cash_flow.loc['Operating Cash Flow'].iloc[0]
            capex = cash_flow.loc['Capital Expenditure'].iloc[0] if 'Capital Expenditure' in cash_flow.index else 0
            fcf = ocf + capex
        
        if fcf <= 0:
            return None, None
        
        growth_rate = 0.05
        discount_rate = 0.10
        terminal_growth = 0.02
        forecast_years = 5
        
        fcf_projections = []
        dcf_value = 0
        
        for i in range(1, forecast_years + 1):
            future_fcf = fcf * (1 + growth_rate) ** i
            pv = future_fcf / (1 + discount_rate) ** i
            fcf_projections.append({
                'year': i,
                'fcf': future_fcf,
                'pv': pv
            })
            dcf_value += pv
        
        terminal_fcf = fcf * (1 + growth_rate) ** forecast_years * (1 + terminal_growth)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth)
        terminal_pv = terminal_value / (1 + discount_rate) ** forecast_years
        
        enterprise_value = dcf_value + terminal_pv
        
        shares = info.get('sharesOutstanding', 0)
        if shares <= 0:
            return None, None
            
        fair_value_per_share = enterprise_value / shares
        
        if fair_value_per_share < 0 or fair_value_per_share > 10000:
            return None, None
        
        dcf_params = {
            'growth_rate': growth_rate,
            'discount_rate': discount_rate,
            'terminal_growth': terminal_growth,
            'forecast_years': forecast_years,
            'initial_fcf': fcf,
            'fcf_projections': fcf_projections,
            'terminal_value': terminal_value,
            'terminal_pv': terminal_pv,
            'enterprise_value': enterprise_value,
            'shares': shares
        }
            
        return fair_value_per_share, dcf_params
    except Exception as e:
        st.warning(f"DCF估值计算失败: {str(e)}")
        return None, None

def calculate_relative_valuation(data):
    """相对估值分析"""
    try:
        info = data['info']
        
        pe_ratio = info.get('trailingPE', 0)
        pb_ratio = info.get('priceToBook', 0)
        ev_ebitda = info.get('enterpriseToEbitda', 0)
        
        industry_pe = 20
        industry_pb = 3
        industry_ev_ebitda = 12
        
        return {
            'pe_ratio': pe_ratio,
            'pb_ratio': pb_ratio,
            'ev_ebitda': ev_ebitda,
            'industry_pe': industry_pe,
            'industry_pb': industry_pb,
            'industry_ev_ebitda': industry_ev_ebitda
        }
    except Exception as e:
        st.warning(f"相对估值计算失败: {str(e)}")
        return None

def calculate_technical_indicators(hist_data):
    """计算技术指标"""
    try:
        hist_data['MA10'] = hist_data['Close'].rolling(window=10).mean()
        hist_data['MA20'] = hist_data['Close'].rolling(window=20).mean()
        hist_data['MA60'] = hist_data['Close'].rolling(window=60).mean()
        
        exp1 = hist_data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist_data['Close'].ewm(span=26, adjust=False).mean()
        hist_data['MACD'] = exp1 - exp2
        hist_data['Signal'] = hist_data['MACD'].ewm(span=9, adjust=False).mean()
        hist_data['MACD_Histogram'] = hist_data['MACD'] - hist_data['Signal']
        
        delta = hist_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist_data['RSI'] = 100 - (100 / (1 + rs))
        
        hist_data['BB_Middle'] = hist_data['Close'].rolling(window=20).mean()
        bb_std = hist_data['Close'].rolling(window=20).std()
        hist_data['BB_Upper'] = hist_data['BB_Middle'] + (bb_std * 2)
        hist_data['BB_Lower'] = hist_data['BB_Middle'] - (bb_std * 2)
        hist_data['BB_Width'] = hist_data['BB_Upper'] - hist_data['BB_Lower']
        
        hist_data['Volume_MA'] = hist_data['Volume'].rolling(window=20).mean()
        
        return hist_data
    except Exception as e:
        st.warning(f"技术指标计算失败: {str(e)}")
        return hist_data

def calculate_kelly_criterion(win_prob, win_loss_ratio):
    """Kelly公式计算推荐仓位"""
    f = (win_prob * win_loss_ratio - (1 - win_prob)) / win_loss_ratio
    return max(0, min(f, 0.25))

def calculate_historical_valuation_percentile(ticker, current_pe, current_pb):
    """计算历史估值分位"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*5)
        
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date, interval="1mo")
        
        price_percentile = (hist['Close'] < hist['Close'].iloc[-1]).sum() / len(hist) * 100
        
        return {
            'pe_percentile': price_percentile,
            'pb_percentile': price_percentile * 0.9,
            'hist_prices': hist['Close']
        }
    except:
        return None

def calculate_financial_trends(data):
    """计算财务趋势"""
    try:
        financials = data['financials']
        info = data['info']
        
        if financials.empty or len(financials.columns) < 3:
            return None
        
        years = []
        revenues = []
        net_incomes = []
        eps_values = []
        
        for i in range(min(3, len(financials.columns))):
            year = datetime.now().year - i
            years.append(str(year))
            
            revenue = financials.loc['Total Revenue'].iloc[i] if 'Total Revenue' in financials.index else 0
            net_income = financials.loc['Net Income'].iloc[i] if 'Net Income' in financials.index else 0
            
            revenues.append(revenue)
            net_incomes.append(net_income)
            
            shares = info.get('sharesOutstanding', 1)
            eps = net_income / shares if shares > 0 else 0
            eps_values.append(eps)
        
        return {
            'years': years[::-1],
            'revenues': revenues[::-1],
            'net_incomes': net_incomes[::-1],
            'eps': eps_values[::-1]
        }
    except:
        return None

def calculate_risk_metrics(data):
    """计算风险指标"""
    try:
        info = data['info']
        financials = data['financials']
        balance_sheet = data['balance_sheet']
        
        ebit = info.get('ebitda', 0)
        interest_expense = financials.loc['Interest Expense'].iloc[0] if 'Interest Expense' in financials.index and not financials.empty else 1
        interest_coverage = abs(ebit / interest_expense) if interest_expense != 0 else 10
        interest_coverage = min(interest_coverage, 10)
        
        beta = info.get('beta', 1)
        beta_score = max(0, 10 - beta * 5)
        
        total_assets = info.get('totalAssets', 1)
        total_debt = info.get('totalDebt', 0)
        debt_ratio = total_debt / total_assets if total_assets > 0 else 0
        leverage_score = max(0, 10 - debt_ratio * 10)
        
        fcf_growth_score = 5
        
        profit_margin = info.get('profitMargins', 0) * 100
        profitability_score = min(profit_margin, 10)
        
        return {
            'interest_coverage': interest_coverage,
            'beta_score': beta_score,
            'leverage_score': leverage_score,
            'fcf_growth_score': fcf_growth_score,
            'profitability_score': profitability_score
        }
    except:
        return None

def calculate_comprehensive_score(f_score, z_score, valuation_margin, technical_signals):
    """计算综合评分"""
    value_score = 0
    if f_score >= 7:
        value_score += 20
    elif f_score >= 4:
        value_score += 10
    
    if z_score and z_score > 2.99:
        value_score += 15
    elif z_score and z_score > 1.8:
        value_score += 5
    
    if valuation_margin > 20:
        value_score += 15
    elif valuation_margin > 0:
        value_score += 7
    
    tech_score = 0
    if technical_signals['ma_golden_cross']:
        tech_score += 15
    if technical_signals['macd_golden_cross']:
        tech_score += 15
    if technical_signals['rsi_oversold']:
        tech_score += 10
    if technical_signals['bb_breakout']:
        tech_score += 10
    
    total_score = value_score + tech_score
    
    if total_score >= 70:
        recommendation = "BUY"
    elif total_score >= 40:
        recommendation = "HOLD"
    else:
        recommendation = "SELL"
    
    return {
        'value_score': value_score,
        'tech_score': tech_score,
        'total_score': total_score,
        'recommendation': recommendation
    }

def analyze_valuation_signals(data, dcf_value, current_price):
    """分析估值信号"""
    valuation_signals = {
        'undervalued': False,
        'overvalued': False,
        'margin': 0,
        'pe_status': 'neutral',
        'pb_status': 'neutral'
    }
    
    try:
        info = data['info']
        
        if dcf_value and current_price > 0:
            margin = ((dcf_value - current_price) / dcf_value * 100)
            valuation_signals['margin'] = margin
            
            if margin > 20:
                valuation_signals['undervalued'] = True
            elif margin < -20:
                valuation_signals['overvalued'] = True
        
        pe_ratio = info.get('trailingPE', 0)
        pb_ratio = info.get('priceToBook', 0)
        
        if pe_ratio > 0 and pe_ratio < 15:
            valuation_signals['pe_status'] = 'undervalued'
        elif pe_ratio > 30:
            valuation_signals['pe_status'] = 'overvalued'
            
        if pb_ratio > 0 and pb_ratio < 1.5:
            valuation_signals['pb_status'] = 'undervalued'
        elif pb_ratio > 5:
            valuation_signals['pb_status'] = 'overvalued'
    
    except Exception as e:
        st.warning(f"估值信号分析失败: {str(e)}")
    
    return valuation_signals

def analyze_technical_signals(hist_data):
    """分析技术信号"""
    signals = {
        'ma_golden_cross': False,
        'ma_death_cross': False,
        'macd_golden_cross': False,
        'macd_death_cross': False,
        'rsi_oversold': False,
        'rsi_overbought': False,
        'bb_breakout': False,
        'volume_divergence': False,
        'trend': 'neutral'
    }
    
    try:
        if len(hist_data) < 60:
            return signals
        
        latest = hist_data.iloc[-1]
        prev = hist_data.iloc[-2]
        
        if 'MA10' in hist_data.columns and 'MA60' in hist_data.columns:
            if latest['MA10'] > latest['MA60'] and prev['MA10'] <= prev['MA60']:
                signals['ma_golden_cross'] = True
            elif latest['MA10'] < latest['MA60'] and prev['MA10'] >= prev['MA60']:
                signals['ma_death_cross'] = True
        
        if 'MACD' in hist_data.columns and 'Signal' in hist_data.columns:
            if latest['MACD'] > latest['Signal'] and prev['MACD'] <= prev['Signal']:
                signals['macd_golden_cross'] = True
            elif latest['MACD'] < latest['Signal'] and prev['MACD'] >= prev['Signal']:
                signals['macd_death_cross'] = True
        
        if 'RSI' in hist_data.columns:
            rsi_recent = hist_data['RSI'].iloc[-5:]
            if latest['RSI'] < 30:
                signals['rsi_oversold'] = True
            elif latest['RSI'] > 70:
                signals['rsi_overbought'] = True
            
            if len(rsi_recent) >= 3 and rsi_recent.iloc[-1] > rsi_recent.iloc[-2] < rsi_recent.iloc[-3]:
                if latest['RSI'] < 40:
                    signals['rsi_oversold'] = True
        
        if 'BB_Middle' in hist_data.columns:
            if latest['Close'] > latest['BB_Middle'] and prev['Close'] <= prev['BB_Middle']:
                bb_width_change = (latest['BB_Width'] - hist_data['BB_Width'].iloc[-5]) / hist_data['BB_Width'].iloc[-5]
                if bb_width_change > 0.1:
                    signals['bb_breakout'] = True
        
        if 'Volume_MA' in hist_data.columns:
            recent_prices = hist_data['Close'].iloc[-5:]
            recent_volumes = hist_data['Volume'].iloc[-5:]
            
            if recent_prices.iloc[-1] > recent_prices.iloc[0] and recent_volumes.iloc[-1] < recent_volumes.iloc[0]:
                signals['volume_divergence'] = True
        
        if latest['Close'] > latest['MA60']:
            signals['trend'] = 'bullish'
        else:
            signals['trend'] = 'bearish'
            
    except Exception as e:
        st.warning(f"技术信号分析失败: {str(e)}")
    
    return signals

def generate_trading_recommendation(valuation_signals, technical_signals, current_price, dcf_value):
    """生成交易建议"""
    recommendation = {
        'action': 'HOLD',
        'confidence': 0,
        'reasons': [],
        'entry_range': (0, 0),
        'stop_loss': 0,
        'take_profit': 0,
        'position_size': 0
    }
    
    try:
        # 基于估值和技术信号生成建议
        bullish_signals = 0
        bearish_signals = 0
        
        # 估值信号
        if valuation_signals['undervalued']:
            bullish_signals += 2
            recommendation['reasons'].append("估值被低估")
        elif valuation_signals['overvalued']:
            bearish_signals += 2
            recommendation['reasons'].append("估值过高")
        
        # 技术信号
        if technical_signals['ma_golden_cross']:
            bullish_signals += 1
            recommendation['reasons'].append("均线金叉")
        if technical_signals['macd_golden_cross']:
            bullish_signals += 1
            recommendation['reasons'].append("MACD金叉")
        if technical_signals['rsi_oversold']:
            bullish_signals += 1
            recommendation['reasons'].append("RSI超卖")
        if technical_signals['bb_breakout']:
            bullish_signals += 1
            recommendation['reasons'].append("布林带突破")
        
        if technical_signals['ma_death_cross']:
            bearish_signals += 1
            recommendation['reasons'].append("均线死叉")
        if technical_signals['macd_death_cross']:
            bearish_signals += 1
            recommendation['reasons'].append("MACD死叉")
        if technical_signals['rsi_overbought']:
            bearish_signals += 1
            recommendation['reasons'].append("RSI超买")
        
        # 生成最终建议
        net_signals = bullish_signals - bearish_signals
        
        if net_signals >= 2:
            recommendation['action'] = 'BUY'
            recommendation['confidence'] = min(90, 50 + net_signals * 10)
            recommendation['entry_range'] = (current_price * 0.98, current_price * 1.02)
            recommendation['stop_loss'] = current_price * 0.92
            recommendation['take_profit'] = current_price * 1.15
            
            # Kelly公式计算仓位
            win_prob = 0.6 + (net_signals * 0.05)
            win_loss_ratio = 1.5
            kelly_position = calculate_kelly_criterion(win_prob, win_loss_ratio)
            recommendation['position_size'] = kelly_position
            
        elif net_signals <= -2:
            recommendation['action'] = 'SELL'
            recommendation['confidence'] = min(90, 50 + abs(net_signals) * 10)
            recommendation['reasons'].append("多个负面信号")
            
        else:
            recommendation['action'] = 'HOLD'
            recommendation['confidence'] = 30
            recommendation['reasons'].append("信号不明确，建议观望")
    
    except Exception as e:
        st.warning(f"交易建议生成失败: {str(e)}")
    
    return recommendation

# ==================== UI界面 ====================

# 侧边栏
st.sidebar.header("🔍 股票查询")
ticker = st.sidebar.text_input("输入股票代码 (如: AAPL, TSLA, MSFT):", value="AAPL")

# 分析选项
st.sidebar.header("📊 分析选项")
analysis_options = st.sidebar.multiselect(
    "选择分析模块:",
    ["基本信息", "技术分析", "财务分析", "估值分析", "风险分析", "交易建议"],
    default=["基本信息", "技术分析", "财务分析"]
)

# 更新按钮
if st.sidebar.button("🔄 获取最新数据", type="primary"):
    st.session_state.current_ticker = ticker
    with st.spinner("正在获取数据..."):
        data = fetch_stock_data_uncached(ticker)
        if data:
            st.session_state.analysis_data = data
            st.session_state.current_price = data['hist_data']['Close'].iloc[-1] if not data['hist_data'].empty else 0
            st.success("数据更新成功!")
        else:
            st.error("数据获取失败，请检查股票代码!")

# 主界面
if ticker and (st.session_state.current_ticker != ticker or st.session_state.analysis_data is None):
    st.session_state.current_ticker = ticker
    with st.spinner("正在加载数据..."):
        data = fetch_stock_data(ticker)
        if data:
            st.session_state.analysis_data = data
            st.session_state.current_price = data['hist_data']['Close'].iloc[-1] if not data['hist_data'].empty else 0

if st.session_state.analysis_data:
    data = st.session_state.analysis_data
    
    # Initialize recommendation variable for use across sections
    recommendation = {
        'action': 'HOLD',
        'confidence': 0,
        'reasons': [],
        'entry_range': (0, 0),
        'stop_loss': 0,
        'take_profit': 0,
        'position_size': 0
    }
    
    # ==================== 基本信息 ====================
    if "基本信息" in analysis_options:
        st.header("📈 基本信息")
        info = data['info']
        hist_data = data['hist_data']
        
        if not hist_data.empty:
            current_price = hist_data['Close'].iloc[-1]
            prev_close = hist_data['Close'].iloc[-2]
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("当前价格", f"${current_price:.2f}", f"{change:+.2f} ({change_pct:+.2f}%)")
            
            with col2:
                market_cap = info.get('marketCap', 0)
                if market_cap > 1e9:
                    market_cap_str = f"${market_cap/1e9:.1f}B"
                else:
                    market_cap_str = f"${market_cap/1e6:.1f}M"
                st.metric("市值", market_cap_str)
            
            with col3:
                pe_ratio = info.get('trailingPE', 0)
                st.metric("P/E比率", f"{pe_ratio:.2f}" if pe_ratio else "N/A")
            
            with col4:
                volume = hist_data['Volume'].iloc[-1]
                volume_str = f"{volume/1e6:.1f}M" if volume > 1e6 else f"{volume/1e3:.1f}K"
                st.metric("成交量", volume_str)
            
            with col5:
                year_high = hist_data['High'].max()
                year_low = hist_data['Low'].min()
                st.metric("52周区间", f"${year_low:.2f} - ${year_high:.2f}")
        
        # 公司信息
        if info:
            st.subheader("📋 公司信息")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**公司名称:** {info.get('longName', 'N/A')}")
                st.write(f"**行业:** {info.get('industry', 'N/A')}")
                st.write(f"**板块:** {info.get('sector', 'N/A')}")
                st.write(f"**员工数:** {info.get('fullTimeEmployees', 'N/A'):,}" if info.get('fullTimeEmployees') else "**员工数:** N/A")
            
            with col2:
                st.write(f"**总部:** {info.get('city', '')}, {info.get('country', '')}")
                st.write(f"**网站:** {info.get('website', 'N/A')}")
                st.write(f"**Beta系数:** {info.get('beta', 'N/A')}")
                dividend_yield = info.get('dividendYield', 0)
                st.write(f"**股息率:** {dividend_yield*100:.2f}%" if dividend_yield else "**股息率:** N/A")
        
        st.markdown("---")
    
    # ==================== 技术分析 ====================
    if "技术分析" in analysis_options:
        st.header("📊 技术分析")
        
        hist_data = data['hist_data'].copy()
        if not hist_data.empty:
            # 计算技术指标
            hist_data = calculate_technical_indicators(hist_data)
            
            # 价格图表
            fig = go.Figure()
            
            # K线图
            fig.add_trace(go.Candlestick(
                x=hist_data.index,
                open=hist_data['Open'],
                high=hist_data['High'],
                low=hist_data['Low'],
                close=hist_data['Close'],
                name="价格"
            ))
            
            # 移动平均线
            if 'MA10' in hist_data.columns:
                fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['MA10'], 
                                       name="MA10", line=dict(color='orange', width=1)))
            if 'MA20' in hist_data.columns:
                fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['MA20'], 
                                       name="MA20", line=dict(color='blue', width=1)))
            if 'MA60' in hist_data.columns:
                fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['MA60'], 
                                       name="MA60", line=dict(color='red', width=1)))
            
            # 布林带
            if 'BB_Upper' in hist_data.columns:
                fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['BB_Upper'], 
                                       name="BB上轨", line=dict(color='gray', width=1, dash='dot')))
                fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['BB_Lower'], 
                                       name="BB下轨", line=dict(color='gray', width=1, dash='dot'),
                                       fill='tonexty', fillcolor='rgba(128,128,128,0.1)'))
            
            fig.update_layout(
                title=f"{ticker} 价格走势图",
                xaxis_title="日期",
                yaxis_title="价格 ($)",
                height=500,
                xaxis_rangeslider_visible=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 技术指标面板
            col1, col2 = st.columns(2)
            
            with col1:
                # MACD图
                if 'MACD' in hist_data.columns:
                    fig_macd = go.Figure()
                    fig_macd.add_trace(go.Scatter(x=hist_data.index, y=hist_data['MACD'], 
                                                name="MACD", line=dict(color='blue')))
                    fig_macd.add_trace(go.Scatter(x=hist_data.index, y=hist_data['Signal'], 
                                                name="Signal", line=dict(color='red')))
                    fig_macd.add_trace(go.Bar(x=hist_data.index, y=hist_data['MACD_Histogram'], 
                                            name="Histogram"))
                    
                    fig_macd.update_layout(title="MACD指标", height=300)
                    st.plotly_chart(fig_macd, use_container_width=True)
            
            with col2:
                # RSI图
                if 'RSI' in hist_data.columns:
                    fig_rsi = go.Figure()
                    fig_rsi.add_trace(go.Scatter(x=hist_data.index, y=hist_data['RSI'], 
                                               name="RSI", line=dict(color='purple')))
                    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超买线")
                    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超卖线")
                    
                    fig_rsi.update_layout(title="RSI指标", height=300, yaxis=dict(range=[0, 100]))
                    st.plotly_chart(fig_rsi, use_container_width=True)
            
            # 技术信号分析
            technical_signals = analyze_technical_signals(hist_data)
            
            st.subheader("🎯 技术信号")
            signal_cols = st.columns(4)
            
            signals_info = [
                ("均线金叉", technical_signals['ma_golden_cross'], "🟢"),
                ("MACD金叉", technical_signals['macd_golden_cross'], "🟢"),
                ("RSI超卖", technical_signals['rsi_oversold'], "🟡"),
                ("布林带突破", technical_signals['bb_breakout'], "🔵")
            ]
            
            for i, (signal_name, signal_value, emoji) in enumerate(signals_info):
                with signal_cols[i]:
                    if signal_value:
                        st.success(f"{emoji} {signal_name}")
                    else:
                        st.info(f"⚪ {signal_name}")
        
        st.markdown("---")
    
    # ==================== 财务分析 ====================
    if "财务分析" in analysis_options:
        st.header("💰 财务分析")
        
        # Piotroski F-Score
        f_score, f_reasons = calculate_piotroski_score(data)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📊 Piotroski F-Score")
            score_color = "green" if f_score >= 7 else "orange" if f_score >= 4 else "red"
            st.markdown(f"<h2 style='color: {score_color}'>{f_score}/9</h2>", unsafe_allow_html=True)
            
            if f_score >= 7:
                st.success("优秀财务质量")
            elif f_score >= 4:
                st.warning("中等财务质量")
            else:
                st.error("较差财务质量")
        
        with col2:
            st.subheader("📋 评分详情")
            for reason in f_reasons:
                if "为正" in reason or "增长" in reason or "大于" in reason:
                    st.success(f"✅ {reason}")
                elif "基础分" in reason:
                    st.info(f"ℹ️ {reason}")
                else:
                    st.error(f"❌ {reason}")
        
        # 杜邦分析
        dupont = calculate_dupont_analysis(data)
        if dupont:
            st.subheader("🔍 杜邦分析")
            dup_col1, dup_col2, dup_col3, dup_col4 = st.columns(4)
            
            with dup_col1:
                st.metric("ROE", f"{dupont['roe']:.2f}%")
            with dup_col2:
                st.metric("净利润率", f"{dupont['profit_margin']:.2f}%")
            with dup_col3:
                st.metric("资产周转率", f"{dupont['asset_turnover']:.2f}")
            with dup_col4:
                st.metric("权益乘数", f"{dupont['equity_multiplier']:.2f}")
        
        # Altman Z-Score
        z_score, z_status, z_color = calculate_altman_z_score(data)
        
        st.subheader("⚖️ Altman Z-Score (破产风险)")
        z_col1, z_col2 = st.columns(2)
        
        with z_col1:
            st.markdown(f"<h3 style='color: {z_color}'>{z_score:.2f}</h3>", unsafe_allow_html=True)
        
        with z_col2:
            if z_color == "green":
                st.success(f"🟢 {z_status}")
            elif z_color == "orange":
                st.warning(f"🟡 {z_status}")
            else:
                st.error(f"🔴 {z_status}")
        
        # 财务趋势
        trends = calculate_financial_trends(data)
        if trends:
            st.subheader("📈 财务趋势 (近3年)")
            
            fig_trends = go.Figure()
            
            # 营收趋势
            fig_trends.add_trace(go.Scatter(
                x=trends['years'], 
                y=[r/1e9 for r in trends['revenues']], 
                name="营收 (十亿)", 
                line=dict(color='blue'),
                yaxis='y1'
            ))
            
            # 净利润趋势
            fig_trends.add_trace(go.Scatter(
                x=trends['years'], 
                y=[ni/1e9 for ni in trends['net_incomes']], 
                name="净利润 (十亿)", 
                line=dict(color='green'),
                yaxis='y1'
            ))
            
            fig_trends.update_layout(
                title="财务趋势",
                xaxis_title="年份",
                yaxis_title="金额 (十亿美元)",
                height=400
            )
            
            st.plotly_chart(fig_trends, use_container_width=True)
        
        st.markdown("---")
    
    # ==================== 估值分析 ====================
    if "估值分析" in analysis_options:
        st.header("💎 估值分析")
        
        # DCF估值
        dcf_value, dcf_params = calculate_dcf_valuation(data)
        current_price = st.session_state.current_price
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 DCF估值模型")
            if dcf_value:
                valuation_margin = ((dcf_value - current_price) / dcf_value * 100) if dcf_value > 0 else 0
                
                st.metric("DCF公允价值", f"${dcf_value:.2f}")
                st.metric("当前价格", f"${current_price:.2f}")
                
                if valuation_margin > 20:
                    st.success(f"🟢 被低估 {valuation_margin:.1f}%")
                elif valuation_margin > 0:
                    st.warning(f"🟡 略被低估 {valuation_margin:.1f}%")
                elif valuation_margin > -20:
                    st.warning(f"🟡 略被高估 {abs(valuation_margin):.1f}%")
                else:
                    st.error(f"🔴 被高估 {abs(valuation_margin):.1f}%")
                
                # DCF参数
                if dcf_params:
                    with st.expander("📊 DCF模型参数"):
                        st.write(f"**初始自由现金流:** ${dcf_params['initial_fcf']/1e6:.1f}M")
                        st.write(f"**增长率:** {dcf_params['growth_rate']*100:.1f}%")
                        st.write(f"**折现率:** {dcf_params['discount_rate']*100:.1f}%")
                        st.write(f"**终值增长率:** {dcf_params['terminal_growth']*100:.1f}%")
                        st.write(f"**企业价值:** ${dcf_params['enterprise_value']/1e9:.2f}B")
            else:
                st.warning("DCF估值数据不足")
        
        with col2:
            # 相对估值
            relative_val = calculate_relative_valuation(data)
            if relative_val:
                st.subheader("📏 相对估值")
                
                val_metrics = [
                    ("P/E比率", relative_val['pe_ratio'], relative_val['industry_pe']),
                    ("P/B比率", relative_val['pb_ratio'], relative_val['industry_pb']),
                    ("EV/EBITDA", relative_val['ev_ebitda'], relative_val['industry_ev_ebitda'])
                ]
                
                for metric_name, current_val, industry_avg in val_metrics:
                    if current_val and current_val > 0:
                        premium = ((current_val - industry_avg) / industry_avg * 100)
                        
                        if premium > 20:
                            status = f"🔴 溢价 {premium:.1f}%"
                        elif premium > 0:
                            status = f"🟡 溢价 {premium:.1f}%"
                        elif premium > -20:
                            status = f"🟡 折价 {abs(premium):.1f}%"
                        else:
                            status = f"🟢 折价 {abs(premium):.1f}%"
                        
                        st.metric(
                            metric_name,
                            f"{current_val:.2f}",
                            f"行业均值: {industry_avg:.2f}"
                        )
                        st.write(status)
                    else:
                        st.metric(metric_name, "N/A")
        
        # 历史估值分位
        hist_valuation = calculate_historical_valuation_percentile(
            ticker, 
            data['info'].get('trailingPE', 0), 
            data['info'].get('priceToBook', 0)
        )
        
        if hist_valuation:
            st.subheader("📊 历史估值分位")
            
            hist_col1, hist_col2 = st.columns(2)
            
            with hist_col1:
                pe_percentile = hist_valuation['pe_percentile']
                st.metric("价格历史分位", f"{pe_percentile:.1f}%")
                
                if pe_percentile < 20:
                    st.success("🟢 处于历史低位")
                elif pe_percentile < 40:
                    st.info("🔵 处于相对低位")
                elif pe_percentile < 60:
                    st.warning("🟡 处于中等位置")
                elif pe_percentile < 80:
                    st.warning("🟠 处于相对高位")
                else:
                    st.error("🔴 处于历史高位")
            
            with hist_col2:
                # 历史价格分布图
                if 'hist_prices' in hist_valuation:
                    fig_hist = go.Figure()
                    fig_hist.add_trace(go.Histogram(
                        x=hist_valuation['hist_prices'],
                        nbinsx=20,
                        name="价格分布"
                    ))
                    fig_hist.add_vline(
                        x=current_price,
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"当前价格: ${current_price:.2f}"
                    )
                    
                    fig_hist.update_layout(
                        title="5年价格分布",
                        xaxis_title="价格 ($)",
                        yaxis_title="频次",
                        height=300
                    )
                    
                    st.plotly_chart(fig_hist, use_container_width=True)
        
        st.markdown("---")
    
    # ==================== 风险分析 ====================
    if "风险分析" in analysis_options:
        st.header("⚠️ 风险分析")
        
        risk_metrics = calculate_risk_metrics(data)
        
        if risk_metrics:
            st.subheader("🎯 风险评分 (10分制)")
            
            risk_cols = st.columns(5)
            
            risk_items = [
                ("利息覆盖", risk_metrics['interest_coverage'], "偿债能力"),
                ("Beta风险", risk_metrics['beta_score'], "系统性风险"),
                ("杠杆风险", risk_metrics['leverage_score'], "财务杠杆"),
                ("现金流", risk_metrics['fcf_growth_score'], "现金流稳定性"),
                ("盈利能力", risk_metrics['profitability_score'], "盈利稳定性")
            ]
            
            total_risk_score = 0
            
            for i, (risk_name, score, description) in enumerate(risk_items):
                with risk_cols[i]:
                    if score >= 7:
                        st.success(f"🟢 {risk_name}\n{score:.1f}/10")
                    elif score >= 4:
                        st.warning(f"🟡 {risk_name}\n{score:.1f}/10")
                    else:
                        st.error(f"🔴 {risk_name}\n{score:.1f}/10")
                    
                    st.caption(description)
                
                total_risk_score += score
            
            # 总体风险评级
            avg_risk_score = total_risk_score / len(risk_items)
            
            st.subheader("📊 综合风险评级")
            
            if avg_risk_score >= 7:
                st.success(f"🟢 低风险 ({avg_risk_score:.1f}/10)")
                risk_description = "该股票整体风险较低，财务状况稳健"
            elif avg_risk_score >= 5:
                st.warning(f"🟡 中等风险 ({avg_risk_score:.1f}/10)")
                risk_description = "该股票存在一定风险，需要密切关注"
            else:
                st.error(f"🔴 高风险 ({avg_risk_score:.1f}/10)")
                risk_description = "该股票风险较高，投资需谨慎"
            
            st.write(risk_description)
        
        # 波动率分析
        if not data['hist_data'].empty:
            st.subheader("📈 波动率分析")
            
            returns = data['hist_data']['Close'].pct_change().dropna()
            
            vol_col1, vol_col2, vol_col3 = st.columns(3)
            
            with vol_col1:
                daily_vol = returns.std() * 100
                st.metric("日波动率", f"{daily_vol:.2f}%")
            
            with vol_col2:
                annual_vol = daily_vol * np.sqrt(252)
                st.metric("年化波动率", f"{annual_vol:.2f}%")
            
            with vol_col3:
                max_drawdown = ((data['hist_data']['Close'].cummax() - data['hist_data']['Close']) / data['hist_data']['Close'].cummax()).max() * 100
                st.metric("最大回撤", f"{max_drawdown:.2f}%")
            
            # 波动率图表
            rolling_vol = returns.rolling(window=30).std() * np.sqrt(252) * 100
            
            fig_vol = go.Figure()
            fig_vol.add_trace(go.Scatter(
                x=rolling_vol.index,
                y=rolling_vol,
                name="30日滚动年化波动率",
                line=dict(color='red')
            ))
            
            fig_vol.update_layout(
                title="波动率走势",
                xaxis_title="日期",
                yaxis_title="年化波动率 (%)",
                height=300
            )
            
            st.plotly_chart(fig_vol, use_container_width=True)
        
        st.markdown("---")
    
    # ==================== 交易建议 ====================
    if "交易建议" in analysis_options:
        st.header("🎯 交易建议")
        
        # 获取估值和技术信号
        dcf_value, _ = calculate_dcf_valuation(data)
        current_price = st.session_state.current_price
        
        hist_data = data['hist_data'].copy()
        hist_data = calculate_technical_indicators(hist_data)
        
        valuation_signals = analyze_valuation_signals(data, dcf_value, current_price)
        technical_signals = analyze_technical_signals(hist_data)
        
        # 生成交易建议 - Update the global recommendation variable
        recommendation = generate_trading_recommendation(
            valuation_signals, technical_signals, current_price, dcf_value
        )
        
        # 显示建议
        rec_col1, rec_col2 = st.columns([1, 2])
        
        with rec_col1:
            action = recommendation['action']
            confidence = recommendation['confidence']
            
            if action == "BUY":
                st.success(f"🟢 {action}")
                action_color = "green"
            elif action == "SELL":
                st.error(f"🔴 {action}")
                action_color = "red"
            else:
                st.warning(f"🟡 {action}")
                action_color = "orange"
            
            st.metric("置信度", f"{confidence}%")
            
            # 推荐仓位
            if recommendation['position_size'] > 0:
                st.metric("建议仓位", f"{recommendation['position_size']*100:.1f}%")
        
        with rec_col2:
            st.subheader("📋 建议理由")
            for reason in recommendation['reasons']:
                st.write(f"• {reason}")
            
            if action == "BUY" and recommendation['entry_range'][0] > 0:
                st.subheader("💰 交易参数")
                st.write(f"**建议买入区间:** ${recommendation['entry_range'][0]:.2f} - ${recommendation['entry_range'][1]:.2f}")
                st.write(f"**止损位:** ${recommendation['stop_loss']:.2f}")
                st.write(f"**止盈位:** ${recommendation['take_profit']:.2f}")
        
        # 计算综合评分
        f_score, _ = calculate_piotroski_score(data)
        z_score, _, _ = calculate_altman_z_score(data)
        
        valuation_margin = valuation_signals.get('margin', 0)
        
        comprehensive_score = calculate_comprehensive_score(
            f_score, z_score, valuation_margin, technical_signals
        )
        
        st.subheader("🏆 综合评分")
        
        score_col1, score_col2, score_col3, score_col4 = st.columns(4)
        
        with score_col1:
            st.metric("价值评分", f"{comprehensive_score['value_score']}/50")
        
        with score_col2:
            st.metric("技术评分", f"{comprehensive_score['tech_score']}/50")
        
        with score_col3:
            st.metric("总评分", f"{comprehensive_score['total_score']}/100")
        
        with score_col4:
            final_rec = comprehensive_score['recommendation']
            if final_rec == "BUY":
                st.success(f"🟢 {final_rec}")
            elif final_rec == "SELL":
                st.error(f"🔴 {final_rec}")
            else:
                st.warning(f"🟡 {final_rec}")
        
        # 动态止盈止损策略
        st.subheader("⚙️ 止盈止损策略")
        
        strategy_options = [
            "固定比例法",
            "技术指标法", 
            "波动率法(ATR)",
            "成本加码法(跟踪止盈)"
        ]
        
        strategy_col1, strategy_col2 = st.columns(2)
        
        with strategy_col1:
            selected_strategy = st.selectbox("选择策略:", strategy_options)
            buy_price = st.number_input("买入成本价:", value=current_price, step=0.01)
        
        with strategy_col2:
            if selected_strategy == "固定比例法":
                custom_tp = st.slider("止盈比例 (%)", 5, 50, 15)
                custom_sl = st.slider("止损比例 (%)", 5, 30, 10)
            else:
                custom_tp = 15
                custom_sl = 10
        
        # 计算动态止盈止损
        take_profit, stop_loss, strategy_info = calculate_dynamic_levels(
            selected_strategy, hist_data, current_price, buy_price, custom_tp, custom_sl
        )
        
        st.info(f"📊 {strategy_info}")
        
        level_col1, level_col2, level_col3 = st.columns(3)
        
        with level_col1:
            current_pnl = ((current_price - buy_price) / buy_price * 100) if buy_price > 0 else 0
            pnl_color = "green" if current_pnl > 0 else "red"
            st.markdown(f"**当前盈亏:** <span style='color: {pnl_color}'>{current_pnl:+.2f}%</span>", unsafe_allow_html=True)
        
        with level_col2:
            tp_pct = ((take_profit - buy_price) / buy_price * 100) if buy_price > 0 else 0
            st.success(f"🎯 止盈位: ${take_profit:.2f} (+{tp_pct:.1f}%)")
        
        with level_col3:
            sl_pct = ((stop_loss - buy_price) / buy_price * 100) if buy_price > 0 else 0
            st.error(f"🛑 止损位: ${stop_loss:.2f} ({sl_pct:.1f}%)")
        
        # 风险回报比
        if take_profit > current_price and current_price > stop_loss:
            potential_gain = take_profit - current_price
            potential_loss = current_price - stop_loss
            risk_reward_ratio = potential_gain / potential_loss if potential_loss > 0 else 0
            
            st.subheader("⚖️ 风险回报分析")
            rr_col1, rr_col2, rr_col3 = st.columns(3)
            
            with rr_col1:
                st.metric("潜在收益", f"${potential_gain:.2f}")
            
            with rr_col2:
                st.metric("潜在损失", f"${potential_loss:.2f}")
            
            with rr_col3:
                if risk_reward_ratio >= 2:
                    st.success(f"🟢 风险回报比: {risk_reward_ratio:.2f}")
                elif risk_reward_ratio >= 1:
                    st.warning(f"🟡 风险回报比: {risk_reward_ratio:.2f}")
                else:
                    st.error(f"🔴 风险回报比: {risk_reward_ratio:.2f}")
        
        st.markdown("---")
    
    # ==================== 投资组合建议 ====================
    st.header("📁 投资组合建议")
    
    # Generate recommendation if not already done (when trading recommendation module is not selected)
    if "交易建议" not in analysis_options:
        # 获取估值和技术信号
        dcf_value, _ = calculate_dcf_valuation(data)
        current_price = st.session_state.current_price
        
        hist_data = data['hist_data'].copy()
        hist_data = calculate_technical_indicators(hist_data)
        
        valuation_signals = analyze_valuation_signals(data, dcf_value, current_price)
        technical_signals = analyze_technical_signals(hist_data)
        
        # 生成交易建议
        recommendation = generate_trading_recommendation(
            valuation_signals, technical_signals, current_price, dcf_value
        )
    
    # 基于Kelly公式的仓位建议
    if recommendation.get('position_size', 0) > 0:
        kelly_position = recommendation['position_size']
        
        port_col1, port_col2 = st.columns(2)
        
        with port_col1:
            st.subheader("📊 Kelly公式仓位建议")
            st.metric("理论最优仓位", f"{kelly_position*100:.1f}%")
            
            # 保守仓位建议
            conservative_position = kelly_position * 0.5  # Kelly的一半
            moderate_position = kelly_position * 0.75     # Kelly的75%
            
            st.write("**风险调整建议:**")
            st.write(f"• 保守型: {conservative_position*100:.1f}%")
            st.write(f"• 平衡型: {moderate_position*100:.1f}%")
            st.write(f"• 激进型: {kelly_position*100:.1f}%")
        
        with port_col2:
            st.subheader("🎯 分批建仓策略")
            
            total_investment = st.number_input("总投资金额 ($):", value=10000, step=100)
            
            if total_investment > 0:
                batch_1 = total_investment * 0.4
                batch_2 = total_investment * 0.35
                batch_3 = total_investment * 0.25
                
                entry_1 = current_price
                entry_2 = current_price * 0.95  # 下跌5%时加仓
                entry_3 = current_price * 0.90  # 下跌10%时加仓
                
                st.write("**建议分批方案:**")
                st.write(f"• 第一批: ${batch_1:.0f} @ ${entry_1:.2f}")
                st.write(f"• 第二批: ${batch_2:.0f} @ ${entry_2:.2f}")
                st.write(f"• 第三批: ${batch_3:.0f} @ ${entry_3:.2f}")
                
                avg_cost = (batch_1*entry_1 + batch_2*entry_2 + batch_3*entry_3) / total_investment
                st.info(f"平均成本: ${avg_cost:.2f}")
    
    # 相关性分析（如果有多只股票）
    st.subheader("🔗 相关性分析")
    
    correlation_tickers = st.text_input(
        "输入其他股票代码进行相关性分析 (用逗号分隔):",
        placeholder="MSFT,GOOGL,AMZN"
    )
    
    if correlation_tickers:
        tickers_list = [ticker.strip().upper() for ticker in correlation_tickers.split(',')]
        tickers_list.append(ticker.upper())
        
        if st.button("🔍 分析相关性"):
            with st.spinner("正在计算相关性..."):
                correlation_data = {}
                
                for t in tickers_list:
                    try:
                        stock = yf.Ticker(t)
                        hist = stock.history(period="1y")
                        if not hist.empty:
                            correlation_data[t] = hist['Close'].pct_change().dropna()
                    except:
                        continue
                
                if len(correlation_data) > 1:
                    corr_df = pd.DataFrame(correlation_data)
                    correlation_matrix = corr_df.corr()
                    
                    # 热力图
                    fig_corr = px.imshow(
                        correlation_matrix,
                        text_auto=True,
                        aspect="auto",
                        color_continuous_scale="RdBu_r",
                        title="股票相关性矩阵"
                    )
                    
                    fig_corr.update_layout(height=500)
                    st.plotly_chart(fig_corr, use_container_width=True)
                    
                    # 相关性解读
                    main_ticker = ticker.upper()
                    if main_ticker in correlation_matrix.columns:
                        correlations = correlation_matrix[main_ticker].drop(main_ticker)
                        
                        st.subheader(f"📊 {main_ticker} 相关性分析")
                        
                        for other_ticker, corr_value in correlations.items():
                            if abs(corr_value) > 0.7:
                                corr_level = "高度相关"
                                corr_color = "red"
                            elif abs(corr_value) > 0.3:
                                corr_level = "中等相关"
                                corr_color = "orange"
                            else:
                                corr_level = "低相关"
                                corr_color = "green"
                            
                            st.write(f"• **{other_ticker}**: {corr_value:.3f} ({corr_level})")
                        
                        st.info("💡 提示: 相关性过高的股票不适合同时持有，会增加投资组合风险")

else:
    st.info("👆 请在左侧输入股票代码开始分析")

# ==================== 页脚信息 ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>💹 智能投资分析系统 v2.0 | 
    数据来源: Yahoo Finance | 
    ⚠️ 投资有风险，入市需谨慎</p>
    <p>本系统仅供参考，不构成投资建议。请结合个人情况和专业意见做出投资决策。</p>
</div>
""", unsafe_allow_html=True)

# ==================== 快捷操作 ====================
st.sidebar.markdown("---")
st.sidebar.header("🚀 快捷操作")

# 热门股票快速选择
popular_stocks = {
    "🍎 苹果": "AAPL",
    "🚗 特斯拉": "TSLA", 
    "💻 微软": "MSFT",
    "🔍 谷歌": "GOOGL",
    "📦 亚马逊": "AMZN",
    "🎬 奈飞": "NFLX",
    "💳 Visa": "V",
    "🏦 摩根大通": "JPM",
    "🥤 可口可乐": "KO",
    "💊 强生": "JNJ"
}

selected_stock = st.sidebar.selectbox("选择热门股票:", list(popular_stocks.keys()))

if st.sidebar.button("📈 快速分析"):
    selected_ticker = popular_stocks[selected_stock]
    st.session_state.current_ticker = selected_ticker
    
    with st.spinner(f"正在分析 {selected_stock}..."):
        data = fetch_stock_data_uncached(selected_ticker)
        if data:
            st.session_state.analysis_data = data
            st.session_state.current_price = data['hist_data']['Close'].iloc[-1] if not data['hist_data'].empty else 0
            st.experimental_rerun()

# 市场概览
st.sidebar.header("📊 市场概览")

try:
    # 获取主要指数
    indices = {
        "S&P 500": "^GSPC",
        "纳斯达克": "^IXIC", 
        "道琼斯": "^DJI"
    }
    
    for index_name, index_symbol in indices.items():
        try:
            index_data = yf.Ticker(index_symbol).history(period="2d")
            if not index_data.empty and len(index_data) >= 2:
                current = index_data['Close'].iloc[-1]
                previous = index_data['Close'].iloc[-2]
                change = current - previous
                change_pct = (change / previous) * 100
                
                st.sidebar.metric(
                    index_name,
                    f"{current:.0f}",
                    f"{change:+.0f} ({change_pct:+.2f}%)"
                )
        except:
            st.sidebar.metric(index_name, "数据获取失败")
            
except Exception as e:
    st.sidebar.warning("市场数据获取失败")

# 使用说明
with st.sidebar.expander("📖 使用说明"):
    st.write("""
    **功能模块:**
    • 基本信息: 股价、市值、财务概况
    • 技术分析: K线图、技术指标、信号
    • 财务分析: F-Score、杜邦分析、Z-Score
    • 估值分析: DCF模型、相对估值
    • 风险分析: 风险评分、波动率
    • 交易建议: 买卖信号、止盈止损
    
    **操作提示:**
    1. 输入股票代码(如AAPL)
    2. 选择分析模块
    3. 点击"获取最新数据"更新
    4. 查看分析结果和建议
    
    **注意事项:**
    • 数据有延迟，仅供参考
    • 投资决策需结合多方面因素
    • 建议咨询专业投资顾问
    """)

# 导出功能
st.sidebar.header("💾 数据导出")

if st.session_state.analysis_data and st.sidebar.button("📊 导出分析报告"):
    try:
        # 创建分析报告
        report_data = {
            "股票代码": ticker,
            "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "当前价格": st.session_state.current_price,
            "Piotroski F-Score": calculate_piotroski_score(st.session_state.analysis_data)[0],
            "Altman Z-Score": calculate_altman_z_score(st.session_state.analysis_data)[0]
        }
        
        # DCF估值
        dcf_value, _ = calculate_dcf_valuation(st.session_state.analysis_data)
        if dcf_value:
            report_data["DCF公允价值"] = dcf_value
            report_data["估值偏差"] = ((dcf_value - st.session_state.current_price) / dcf_value * 100)
        
        # 转换为DataFrame并提供下载
        report_df = pd.DataFrame([report_data])
        csv = report_df.to_csv(index=False, encoding='utf-8-sig')
        
        st.sidebar.download_button(
            label="📥 下载CSV报告",
            data=csv,
            file_name=f"{ticker}_analysis_report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        st.sidebar.success("报告准备完成!")
        
    except Exception as e:
        st.sidebar.error(f"报告生成失败: {str(e)}")

# 版本信息
st.sidebar.markdown("---")
st.sidebar.caption("🔄 最后更新: 2024年6月")
st.sidebar.caption("📧 问题反馈: support@example.com")
