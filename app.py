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

# 技术分析库（如果没有安装，系统会自动使用备用方案）
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
    """获取股票数据（不缓存版本）"""
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
            return 0, ["❌ 财务数据不完整"]
        
        # 1. 盈利能力
        if len(financials.columns) >= 2 and 'Net Income' in financials.index:
            net_income = financials.loc['Net Income'].iloc[0]
            if net_income > 0:
                score += 1
                reasons.append("✅ 净利润为正")
            else:
                reasons.append("❌ 净利润为负")
        
        # 2. 经营现金流
        if len(cash_flow.columns) >= 1 and 'Operating Cash Flow' in cash_flow.index:
            ocf = cash_flow.loc['Operating Cash Flow'].iloc[0]
            if ocf > 0:
                score += 1
                reasons.append("✅ 经营现金流为正")
            else:
                reasons.append("❌ 经营现金流为负")
        
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
                reasons.append("✅ ROA同比增长")
            else:
                reasons.append("❌ ROA同比下降")
        
        # 4. 现金流质量
        if 'net_income' in locals() and 'ocf' in locals() and net_income != 0 and ocf > net_income:
            score += 1
            reasons.append("✅ 经营现金流大于净利润")
        else:
            reasons.append("❌ 经营现金流小于净利润")
        
        # 5-9. 其他财务指标（简化版本）
        score += 3
        reasons.append("📊 财务结构基础分: 3分")
        
    except Exception as e:
        st.warning(f"Piotroski Score计算部分指标失败: {str(e)}")
        return 0, ["❌ 计算过程出现错误"]
    
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
        'take_profit': (0, 0),
        'position_size': 0
    }
    
    buy_signals = 0
    sell_signals = 0
    
    # 检查买入条件
    if valuation_signals['undervalued'] or valuation_signals['pe_status'] == 'undervalued' or valuation_signals['pb_status'] == 'undervalued':
        buy_signals += 1
        recommendation['reasons'].append("估值处于低估区间")
    
    tech_buy_conditions = [
        (technical_signals['ma_golden_cross'], "10日均线上穿60日均线"),
        (technical_signals['macd_golden_cross'], "MACD金叉成立"),
        (technical_signals['rsi_oversold'], "RSI超卖且拐头向上"),
        (technical_signals['bb_breakout'], "突破布林带中轨且带宽扩张")
    ]
    
    tech_buy_count = sum([1 for condition, _ in tech_buy_conditions if condition])
    
    if tech_buy_count >= 2:
        buy_signals += 1
        recommendation['reasons'].extend([reason for condition, reason in tech_buy_conditions if condition])
    
    # 检查卖出条件
    if valuation_signals['overvalued'] or valuation_signals['pe_status'] == 'overvalued' or valuation_signals['pb_status'] == 'overvalued':
        sell_signals += 1
        recommendation['reasons'].append("估值处于高估区间")
    
    tech_sell_conditions = [
        (technical_signals['rsi_overbought'], "RSI超买"),
        (technical_signals['macd_death_cross'], "MACD死叉"),
        (technical_signals['volume_divergence'], "量价背离"),
        (technical_signals['ma_death_cross'], "均线死叉")
    ]
    
    tech_sell_count = sum([1 for condition, _ in tech_sell_conditions if condition])
    
    if tech_sell_count >= 2:
        sell_signals += 1
        recommendation['reasons'].extend([reason for condition, reason in tech_sell_conditions if condition])
    
    # 生成最终建议
    if buy_signals >= 2:
        recommendation['action'] = 'BUY'
        recommendation['confidence'] = min(buy_signals * 30 + tech_buy_count * 10, 90)
        recommendation['entry_range'] = (current_price * 0.98, current_price * 1.02)
        recommendation['stop_loss'] = current_price * 0.92
        
        if dcf_value and dcf_value > current_price:
            recommendation['take_profit'] = (dcf_value * 0.95, dcf_value * 1.05)
        else:
            recommendation['take_profit'] = (current_price * 1.15, current_price * 1.25)
        
        win_prob = 0.6 + (recommendation['confidence'] / 100) * 0.2
        recommendation['position_size'] = calculate_kelly_criterion(win_prob, 2.0) * 100
        
    elif sell_signals >= 2:
        recommendation['action'] = 'SELL'
        recommendation['confidence'] = min(sell_signals * 30 + tech_sell_count * 10, 90)
        recommendation['reasons'].insert(0, "建议减仓或清仓")
        recommendation['entry_range'] = (current_price * 0.98, current_price * 1.02)
        recommendation['stop_loss'] = current_price * 1.08
        recommendation['take_profit'] = (current_price * 0.90, current_price * 0.85)
        
    else:
        recommendation['action'] = 'HOLD'
        recommendation['confidence'] = 50
        recommendation['reasons'] = ["估值和技术信号不明确", "建议继续观察"]
        recommendation['entry_range'] = (current_price * 0.95, current_price * 0.98)
        recommendation['stop_loss'] = current_price * 0.92
        if dcf_value and dcf_value > current_price:
            recommendation['take_profit'] = (dcf_value * 0.90, dcf_value)
        else:
            recommendation['take_profit'] = (current_price * 1.10, current_price * 1.20)
        recommendation['position_size'] = 10.0
    
    return recommendation

# ==================== 主程序 ====================
# 侧边栏输入
with st.sidebar:
    st.header("📊 分析参数设置")
    
    ticker = st.text_input("股票代码", "AAPL", help="输入股票代码，如：AAPL")
    market = st.selectbox("市场选择", ["美股", "A股（待开发）"])
    analyze_button = st.button("🔍 开始分析", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    with st.expander("📘 使用说明"):
        st.markdown("""
        ### 如何解读各项数值指标
        
        **1. 安全边际 (Margin of Safety)**
        - 正值：股价低于估值，存在低估
        - 负值：股价高于估值，存在高估
        - 建议：
          - > 50%：强买入
          - 20-50%：买入
          - 0-20%：观察
          - < 0%：避免
        
        **2. 信心度 (Confidence)**
        - > 70%：高信心度
        - 50-70%：中等信心
        - < 50%：低信心度
        
        **3. 技术信号**
        - 金叉：买入信号
        - 死叉：卖出信号
        - RSI > 70：超买
        - RSI < 30：超卖
        
        **4. Piotroski F-score**
        - 7-9分：优秀
        - 4-6分：中等
        - 0-3分：较差
        
        **5. Altman Z-score**
        - Z > 2.99：✅ 财务健康
        - 1.81-2.99：⚠️ 临界风险
        - Z < 1.81：🚨 高破产风险
        """)
    
    with st.expander("📊 投资决策参考表"):
        st.markdown("""
        | 安全边际 | 信心度 | 操作建议 |
        |---------|--------|----------|
        | >30%    | >70%   | ✅ 强买入 |
        | >0%     | >50%   | ⚠️ 观察  |
        | <0%     | ≈50%   | 🔍 观望  |
        | <0%     | <50%   | 🚫 回避  |
        """)
    
    st.markdown("---")
    st.markdown("### 说明")
    st.markdown("- 输入股票代码后点击分析")
    st.markdown("- 系统将自动获取数据并进行全面分析")
    st.markdown("- 分析包含基本面、技术面和估值模型")

# 主界面
if analyze_button and ticker:
    # 立即更新 session state
    st.session_state.current_ticker = ticker
    
    with st.spinner(f"正在获取 {ticker} 的数据..."):
        try:
            data = fetch_stock_data(ticker)
        except:
            data = fetch_stock_data_uncached(ticker)
    
    if data:
        # 立即更新当前价格到 session state
        current_price = data['info'].get('currentPrice', 0)
        st.session_state.current_price = current_price
        st.session_state.analysis_data = data
        col1, col2, col3 = st.columns([1, 2, 1.5])
        
        # 左栏：公司基本信息
        with col1:
            st.subheader("📌 公司基本信息")
            info = data['info']
            
            with st.container():
                st.metric("公司名称", info.get('longName', ticker))
                st.metric("当前股价", f"${info.get('currentPrice', 0):.2f}")
                st.metric("市值", f"${info.get('marketCap', 0)/1e9:.2f}B")
                st.metric("行业", info.get('industry', 'N/A'))
                st.metric("Beta", f"{info.get('beta', 0):.2f}")
                
                st.markdown("---")
                st.metric("52周最高", f"${info.get('fiftyTwoWeekHigh', 0):.2f}")
                st.metric("52周最低", f"${info.get('fiftyTwoWeekLow', 0):.2f}")
        
        # 中栏：分析结果
        with col2:
            st.subheader("📈 综合分析结果")
            
            # Piotroski F-Score
            with st.expander("🔍 Piotroski F-Score 分析", expanded=True):
                f_score, reasons = calculate_piotroski_score(data)
                
                score_color = "green" if f_score >= 7 else "orange" if f_score >= 4 else "red"
                st.markdown(f"### 得分: <span style='color:{score_color}; font-size:24px'>{f_score}/9</span>", unsafe_allow_html=True)
                
                for reason in reasons:
                    st.write(reason)
                
                if f_score >= 7:
                    st.success("💡 建议: 财务健康状况良好，基本面强劲")
                elif f_score >= 4:
                    st.warning("💡 建议: 财务状况一般，需要谨慎评估")
                else:
                    st.error("💡 建议: 财务状况较差，投资风险较高")
            
            # 杜邦分析
            with st.expander("📊 杜邦分析", expanded=True):
                dupont = calculate_dupont_analysis(data)
                if dupont:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("ROE", f"{dupont['roe']:.2f}%")
                        st.metric("利润率", f"{dupont['profit_margin']:.2f}%")
                    with col_b:
                        st.metric("资产周转率", f"{dupont['asset_turnover']:.2f}")
                        st.metric("权益乘数", f"{dupont['equity_multiplier']:.2f}")
                    
                    st.write("📝 ROE = 利润率 × 资产周转率 × 权益乘数")
            
            # Altman Z-Score
            with st.expander("💰 Altman Z-Score 财务健康度", expanded=True):
                z_score, status, color = calculate_altman_z_score(data)
                if z_score:
                    st.markdown(f"### Z-Score: <span style='color:{color}; font-size:24px'>{z_score:.2f}</span>", unsafe_allow_html=True)
                    st.markdown(f"**状态**: <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)
                    
                    if z_score > 2.99:
                        st.success("✅ 财务健康 - 企业财务状况良好，破产风险极低")
                    elif z_score >= 1.81:
                        st.warning("⚠️ 临界风险 - 企业处于灰色地带，需要密切关注")
                    else:
                        st.error("🚨 高破产风险 - 企业财务状况堪忧，投资需谨慎")
                    
                    st.write("📊 评分标准:")
                    st.write("- Z > 2.99: 安全区域")
                    st.write("- 1.8 < Z < 2.99: 灰色区域")
                    st.write("- Z < 1.8: 危险区域")
            
            # 估值分析
            with st.expander("💎 估值分析", expanded=True):
                dcf_value, dcf_params = calculate_dcf_valuation(data)
                current_price = info.get('currentPrice', 0)
                
                if dcf_value and current_price > 0:
                    st.write("**DCF估值**")
                    col_x, col_y = st.columns(2)
                    with col_x:
                        st.metric("合理价值", f"${dcf_value:.2f}")
                        st.metric("当前价格", f"${current_price:.2f}")
                    with col_y:
                        margin = ((dcf_value - current_price) / dcf_value * 100) if dcf_value > 0 else 0
                        st.metric("安全边际", f"{margin:.2f}%")
                    
                    if dcf_params:
                        st.write("**📊 DCF模型参数详情**")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.write(f"**永续增长率 g**: {dcf_params['terminal_growth']*100:.1f}%")
                            st.write(f"**预测期增长率**: {dcf_params['growth_rate']*100:.1f}%")
                        with col_b:
                            st.write(f"**折现率 WACC**: {dcf_params['discount_rate']*100:.1f}%")
                            st.write(f"**预测年限**: {dcf_params['forecast_years']}年")
                        with col_c:
                            st.write(f"**初始FCF**: ${dcf_params['initial_fcf']/1e6:.1f}M")
                            st.write(f"**企业价值**: ${dcf_params['enterprise_value']/1e9:.2f}B")
                        
                        st.write("**预测期现金流（百万美元）**")
                        fcf_df = pd.DataFrame(dcf_params['fcf_projections'])
                        fcf_df['fcf'] = fcf_df['fcf'] / 1e6
                        fcf_df['pv'] = fcf_df['pv'] / 1e6
                        fcf_df.columns = ['年份', '预测FCF', '现值']
                        st.dataframe(fcf_df.style.format({'预测FCF': '${:.1f}M', '现值': '${:.1f}M'}))
                        
                        st.write(f"**终值**: ${dcf_params['terminal_value']/1e9:.2f}B")
                        st.write(f"**终值现值**: ${dcf_params['terminal_pv']/1e9:.2f}B")
                else:
                    st.info("DCF估值数据不足")
                
                st.write("**相对估值**")
                rel_val = calculate_relative_valuation(data)
                if rel_val:
                    col_m, col_n = st.columns(2)
                    with col_m:
                        pe_display = f"{rel_val['pe_ratio']:.2f}" if rel_val['pe_ratio'] > 0 else "N/A"
                        pb_display = f"{rel_val['pb_ratio']:.2f}" if rel_val['pb_ratio'] > 0 else "N/A"
                        st.metric("PE", pe_display)
                        st.metric("PB", pb_display)
                    with col_n:
                        st.metric("行业PE", f"{rel_val['industry_pe']:.2f}")
                        st.metric("行业PB", f"{rel_val['industry_pb']:.2f}")
                    
                    if rel_val['pe_ratio'] > 0:
                        hist_val = calculate_historical_valuation_percentile(ticker, rel_val['pe_ratio'], rel_val['pb_ratio'])
                        if hist_val:
                            st.write("**历史估值分位**")
                            fig_hist = go.Figure()
                            
                            fig_hist.add_trace(go.Scatter(
                                x=hist_val['hist_prices'].index,
                                y=hist_val['hist_prices'].values,
                                mode='lines',
                                name='历史价格',
                                line=dict(color='blue', width=2)
                            ))
                            
                            fig_hist.add_hline(y=current_price, line_dash="dash", line_color="red", 
                                             annotation_text=f"当前价格: ${current_price:.2f}")
                            
                            fig_hist.update_layout(
                                title=f"5年价格走势及当前位置（分位数: {hist_val['pe_percentile']:.1f}%）",
                                xaxis_title="日期",
                                yaxis_title="价格 ($)",
                                height=300
                            )
                            st.plotly_chart(fig_hist, use_container_width=True)
            
            # 财务趋势分析
            with st.expander("📊 财务趋势分析", expanded=False):
                fin_trends = calculate_financial_trends(data)
                if fin_trends:
                    fig_trends = go.Figure()
                    
                    fig_trends.add_trace(go.Bar(
                        name='营业收入',
                        x=fin_trends['years'],
                        y=[x/1e9 for x in fin_trends['revenues']],
                        yaxis='y',
                        marker_color='lightblue'
                    ))
                    
                    fig_trends.add_trace(go.Bar(
                        name='净利润',
                        x=fin_trends['years'],
                        y=[x/1e9 for x in fin_trends['net_incomes']],
                        yaxis='y',
                        marker_color='lightgreen'
                    ))
                    
                    fig_trends.add_trace(go.Scatter(
                        name='每股收益(EPS)',
                        x=fin_trends['years'],
                        y=fin_trends['eps'],
                        yaxis='y2',
                        mode='lines+markers',
                        line=dict(color='red', width=3)
                    ))
                    
                    fig_trends.update_layout(
                        title='近3年财务趋势',
                        xaxis=dict(title='年份'),
                        yaxis=dict(title='金额（十亿美元）', side='left'),
                        yaxis2=dict(title='EPS ($)', overlaying='y', side='right'),
                        hovermode='x',
                        barmode='group',
                        height=400
                    )
                    
                    st.plotly_chart(fig_trends, use_container_width=True)
                else:
                    st.info("财务趋势数据不足")
        
        # 右栏：图表和建议
        with col3:
            st.subheader("📉 技术分析与建议")
            
            hist_data = data['hist_data'].copy()
            hist_data = calculate_technical_indicators(hist_data)
            
            # 价格走势图
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(hist_data.index[-180:], hist_data['Close'][-180:], label='Close', linewidth=2)
            ax.plot(hist_data.index[-180:], hist_data['MA20'][-180:], label='MA20', alpha=0.7)
            ax.plot(hist_data.index[-180:], hist_data['MA60'][-180:], label='MA60', alpha=0.7)
            ax.set_title(f'{ticker} Price Trend (Last 180 Days)')
            ax.set_xlabel('Date')
            ax.set_ylabel('Price ($)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            
            # MACD图
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            ax2.plot(hist_data.index[-90:], hist_data['MACD'][-90:], label='MACD', color='blue')
            ax2.plot(hist_data.index[-90:], hist_data['Signal'][-90:], label='Signal', color='red')
            ax2.bar(hist_data.index[-90:], hist_data['MACD_Histogram'][-90:], label='Histogram', alpha=0.3)
            ax2.set_title('MACD Indicator')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig2)
            
            # 模块B：技术分析结论展示
            st.markdown("---")
            st.subheader("📊 技术指标快速解读")
            
            # 计算技术信号
            valuation_signals = analyze_valuation_signals(data, dcf_value, current_price)
            technical_signals = analyze_technical_signals(hist_data)
            latest = hist_data.iloc[-1]
            
            # 技术指标状态卡片
            tech_col1, tech_col2 = st.columns(2)
            
            with tech_col1:
                # MACD 状态
                if technical_signals['macd_golden_cross']:
                    st.success("🔺 MACD：金叉（看涨信号）")
                elif technical_signals['macd_death_cross']:
                    st.error("🔻 MACD：死叉（看跌信号）")
                else:
                    macd_val = latest['MACD']
                    signal_val = latest['Signal']
                    if macd_val > signal_val:
                        st.info("📈 MACD：多头排列")
                    else:
                        st.warning("📉 MACD：空头排列")
                
                # 均线状态
                if technical_signals['ma_golden_cross']:
                    st.success("🔺 均线：金叉突破")
                elif technical_signals['ma_death_cross']:
                    st.error("🔻 均线：死叉下破")
                elif 'MA10' in hist_data.columns and 'MA60' in hist_data.columns:
                    if latest['MA10'] > latest['MA60']:
                        st.info("📈 均线：多头排列")
                    else:
                        st.warning("📉 均线：空头排列")
            
            with tech_col2:
                # RSI 状态
                if 'RSI' in hist_data.columns:
                    rsi_value = latest['RSI']
                    if rsi_value > 70:
                        st.error(f"⚠️ RSI：{rsi_value:.1f} → 超买状态")
                    elif rsi_value < 30:
                        st.success(f"💡 RSI：{rsi_value:.1f} → 超卖状态")
                    else:
                        st.info(f"📊 RSI：{rsi_value:.1f} → 正常区间")
                
                # 布林带状态
                if 'BB_Upper' in hist_data.columns and 'BB_Lower' in hist_data.columns:
                    close_price = latest['Close']
                    bb_upper = latest['BB_Upper']
                    bb_lower = latest['BB_Lower']
                    bb_middle = latest['BB_Middle']
                    
                    if close_price > bb_upper:
                        st.warning("🔺 布林带：突破上轨")
                    elif close_price < bb_lower:
                        st.success("🔻 布林带：跌破下轨")
                    elif close_price > bb_middle:
                        st.info("📈 布林带：上半区运行")
                    else:
                        st.info("📉 布林带：下半区运行")
            
            # 模块C：Altman Z-score 简洁展示
            st.markdown("---")
            z_score, status, color = calculate_altman_z_score(data)
            if z_score and z_score > 0:
                if color == "green":
                    st.success(f"📉 破产风险评分（Altman Z-score）：{z_score:.2f} ✅ {status}")
                elif color == "orange":
                    st.warning(f"📉 破产风险评分（Altman Z-score）：{z_score:.2f} ⚠️ {status}")
                else:
                    st.error(f"📉 破产风险评分（Altman Z-score）：{z_score:.2f} 🚨 {status}")
            else:
                st.info("📉 破产风险评分：数据不足，无法计算")
            
            # 智能买卖点建议
            st.markdown("---")
            st.subheader("💡 智能买卖点建议")
            
            dcf_value, _ = calculate_dcf_valuation(data)
            z_score, _, _ = calculate_altman_z_score(data)
            
            valuation_signals = analyze_valuation_signals(data, dcf_value, current_price)
            technical_signals = analyze_technical_signals(hist_data)
            
            recommendation = generate_trading_recommendation(
                valuation_signals, 
                technical_signals, 
                current_price,
                dcf_value
            )
            
            if recommendation['action'] == 'BUY':
                st.success(f"🟢 **强烈建议：{recommendation['action']}**")
                color_style = "background-color: #d4edda; padding: 15px; border-radius: 10px; border: 1px solid #c3e6cb;"
            elif recommendation['action'] == 'SELL':
                st.error(f"🔴 **强烈建议：{recommendation['action']}**")
                color_style = "background-color: #f8d7da; padding: 15px; border-radius: 10px; border: 1px solid #f5c6cb;"
            else:
                st.info(f"🔵 **建议：{recommendation['action']}**")
                color_style = "background-color: #d1ecf1; padding: 15px; border-radius: 10px; border: 1px solid #bee5eb;"
            
            with st.container():
                st.markdown(f'<div style="{color_style}">', unsafe_allow_html=True)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("当前价格", f"${current_price:.2f}")
                    if dcf_value:
                        st.metric("合理估值", f"${dcf_value:.2f}")
                with col_b:
                    st.metric("安全边际", f"{valuation_signals['margin']:.1f}%")
                    st.metric("信心度", f"{recommendation['confidence']}%")
                
                st.markdown("**📊 判断依据：**")
                for reason in recommendation['reasons']:
                    st.write(f"• {reason}")
                
                st.markdown("**📍 操作建议：**")
                
                if recommendation['action'] == 'BUY':
                    st.write(f"• 🎯 建仓区间：${recommendation['entry_range'][0]:.2f} - ${recommendation['entry_range'][1]:.2f}")
                    st.write(f"• 🛡️ 止损价位：${recommendation['stop_loss']:.2f} (下跌{((current_price - recommendation['stop_loss'])/current_price*100):.1f}%)")
                    st.write(f"• 💰 止盈目标：${recommendation['take_profit'][0]:.2f} - ${recommendation['take_profit'][1]:.2f} (上涨{((recommendation['take_profit'][0] - current_price)/current_price*100):.1f}%-{((recommendation['take_profit'][1] - current_price)/current_price*100):.1f}%)")
                    st.write(f"• 📊 推荐仓位：{recommendation['position_size']:.1f}%")
                elif recommendation['action'] == 'SELL':
                    st.write(f"• 🔴 建议清仓或减仓")
                    st.write(f"• 📉 当前处于高估区域")
                    st.write(f"• ⚠️ 建议等待回调后再考虑")
                else:
                    st.write(f"• 🔵 建议继续持有观望")
                    st.write(f"• 📊 等待更明确的信号")
                    if dcf_value and current_price < dcf_value * 0.85:
                        buy_zone = (dcf_value * 0.75, dcf_value * 0.85)
                        st.write(f"• 💡 参考买入区间：${buy_zone[0]:.2f} - ${buy_zone[1]:.2f}")
                    if current_price > 0:
                        st.write(f"• 🛡️ 参考止损：${current_price * 0.92:.2f}")
                
                st.markdown("**📈 技术指标状态：**")
                latest = hist_data.iloc[-1]
                
                col_x, col_y = st.columns(2)
                with col_x:
                    if 'RSI' in hist_data.columns:
                        rsi_value = latest['RSI']
                        rsi_status = "超卖" if rsi_value < 30 else "超买" if rsi_value > 70 else "中性"
                        st.write(f"• RSI: {rsi_value:.1f} ({rsi_status})")
                    
                    if 'MACD' in hist_data.columns:
                        macd_status = "金叉" if technical_signals['macd_golden_cross'] else "死叉" if technical_signals['macd_death_cross'] else "中性"
                        st.write(f"• MACD: {macd_status}")
                
                with col_y:
                    if 'MA10' in hist_data.columns and 'MA60' in hist_data.columns:
                        ma_status = "多头" if latest['MA10'] > latest['MA60'] else "空头"
                        st.write(f"• 均线: {ma_status}")
                    
                    trend_status = "上升" if technical_signals['trend'] == 'bullish' else "下降"
                    st.write(f"• 趋势: {trend_status}")
                
                st.markdown("---")
                st.caption(f"⏰ 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 综合评分
            comprehensive = calculate_comprehensive_score(
                f_score, 
                z_score if z_score else 0,
                valuation_signals['margin'],
                technical_signals
            )
            
            st.markdown("---")
            st.subheader("🎯 智能投资评分")
            
            col_score1, col_score2, col_score3 = st.columns(3)
            with col_score1:
                st.metric("价值得分", f"{comprehensive['value_score']}/50")
            with col_score2:
                st.metric("技术得分", f"{comprehensive['tech_score']}/50")
            with col_score3:
                st.metric("综合得分", f"{comprehensive['total_score']}/100")
            
            if comprehensive['recommendation'] == 'BUY':
                st.success(f"🟢 **最终建议：{comprehensive['recommendation']}**")
            elif comprehensive['recommendation'] == 'SELL':
                st.error(f"🔴 **最终建议：{comprehensive['recommendation']}**")
            else:
                st.info(f"🔵 **最终建议：{comprehensive['recommendation']}**")
            
            # 风险雷达图
            st.markdown("---")
            st.subheader("🎯 风险评估雷达图")
            
            risk_metrics = calculate_risk_metrics(data)
            if risk_metrics:
                categories = ['偿债能力', '波动性控制', '财务杠杆', '现金流增长', '盈利能力']
                values = [
                    risk_metrics['interest_coverage'],
                    risk_metrics['beta_score'],
                    risk_metrics['leverage_score'],
                    risk_metrics['fcf_growth_score'],
                    risk_metrics['profitability_score']
                ]
                
                fig_radar = go.Figure(data=go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name='风险评分'
                ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 10]
                        )
                    ),
                    showlegend=False,
                    title="风险指标评分（10分制）",
                    height=400
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)
                
                avg_risk_score = sum(values) / len(values)
                if avg_risk_score >= 7:
                    st.success("✅ 总体风险等级：低")
                elif avg_risk_score >= 5:
                    st.warning("⚠️ 总体风险等级：中")
                else:
                    st.error("🚨 总体风险等级：高")
            
            st.markdown("---")
            if info.get('beta', 1) > 1.5:
                risk_level = "高风险"
                risk_color = "red"
            elif info.get('beta', 1) > 1.0:
                risk_level = "中风险"
                risk_color = "orange"
            else:
                risk_level = "低风险"
                risk_color = "green"
            
            st.markdown(f"**风险等级**: <span style='color:{risk_color}'>{risk_level}</span>", unsafe_allow_html=True)
            st.caption(f"Beta: {info.get('beta', 'N/A')}")
            
            # 智能止盈止损模拟器
            st.markdown("---")
            st.subheader("💰 智能止盈止损模拟器")
            
            with st.container():
                st.info(f"📊 当前分析股票：{ticker} | 实时价格：${current_price:.2f}")
                
                # 输入参数
                col_input1, col_input2 = st.columns(2)
                with col_input1:
                    default_buy_price = current_price * 0.95  # 默认比当前价格低5%
                    buy_price = st.number_input(
                        "买入价格 ($)", 
                        min_value=0.01, 
                        value=default_buy_price, 
                        step=0.01, 
                        help=f"默认设置为 {ticker} 当前价格的95%",
                        key=f"main_buy_price_{ticker}"
                    )
                with col_input2:
                    position_size = st.number_input(
                        "持仓数量", 
                        min_value=1, 
                        value=100, 
                        step=1,
                        key=f"main_position_size_{ticker}"
                    )
                
                # 选择止盈止损策略
                st.markdown("#### 🎯 选择止盈止损策略")
                strategy_tab1, strategy_tab2, strategy_tab3, strategy_tab4 = st.tabs([
                    "📊 固定比例法", "📈 技术指标法", "📉 波动率法", "🎯 成本加码法"
                ])
                
                # 实时计算基础数据
                position_value = position_size * buy_price
                current_value = position_size * current_price
                pnl = current_value - position_value
                pnl_pct = (pnl / position_value) * 100 if position_value > 0 else 0
                
                # 策略1：固定比例法
                with strategy_tab1:
                    st.markdown("#### 🎯 固定比例止盈止损")
                    st.write("**适用场景**: 大多数波动性股票，适合稳健型投资者")
                    
                    col_fixed1, col_fixed2 = st.columns(2)
                    with col_fixed1:
                        take_profit_pct = st.slider(
                            "止盈比例 (%)", 
                            min_value=5, 
                            max_value=50, 
                            value=15, 
                            step=1,
                            key=f"fixed_tp_{ticker}"
                        )
                    with col_fixed2:
                        stop_loss_pct = st.slider(
                            "止损比例 (%)", 
                            min_value=3, 
                            max_value=20, 
                            value=10, 
                            step=1,
                            key=f"fixed_sl_{ticker}"
                        )
                    
                    # 计算固定比例止盈止损价位
                    fixed_stop_loss = buy_price * (1 - stop_loss_pct / 100)
                    fixed_take_profit = buy_price * (1 + take_profit_pct / 100)
                    
                    col_metric1, col_metric2, col_metric3 = st.columns(3)
                    with col_metric1:
                        st.metric(
                            "💰 当前盈亏", 
                            f"${pnl:.2f}",
                            f"{pnl_pct:+.2f}%"
                        )
                    with col_metric2:
                        st.metric(
                            "🛡️ 止损价位", 
                            f"${fixed_stop_loss:.2f}",
                            f"{((fixed_stop_loss - current_price)/current_price*100):+.1f}%"
                        )
                    with col_metric3:
                        st.metric(
                            "🎯 止盈价位", 
                            f"${fixed_take_profit:.2f}",
                            f"{((fixed_take_profit - current_price)/current_price*100):+.1f}%"
                        )
                    
                    # 固定比例法状态判断
                    if current_price <= fixed_stop_loss:
                        st.error("⚠️ **已触及止损线！建议立即止损出场**")
                    elif current_price >= fixed_take_profit:
                        st.success("🎯 **已达到止盈目标！建议考虑获利了结**")
                    else:
                        st.info("📊 **持仓正常** | 继续观察市场走势")
                    
                    # 风险收益分析
                    fixed_risk = position_size * (buy_price - fixed_stop_loss)
                    fixed_reward = position_size * (fixed_take_profit - buy_price)
                    fixed_rr = fixed_reward / fixed_risk if fixed_risk > 0 else 0
                    st.caption(f"💡 风险：${fixed_risk:.2f} | 收益：${fixed_reward:.2f} | 风险收益比：1:{fixed_rr:.2f}")
                
                # 策略2：技术指标法
                with strategy_tab2:
                    st.markdown("#### 📈 技术指标止盈止损")
                    st.write("**适用场景**: 基于支撑阻力位、布林带等技术分析")
                    
                    # 计算技术指标位置
                    latest = hist_data.iloc[-1]
                    
                    # 支撑位计算（20日最低价）
                    support_level = hist_data['Low'].rolling(window=20).min().iloc[-1]
                    
                    # 阻力位计算（20日最高价）
                    resistance_level = hist_data['High'].rolling(window=20).max().iloc[-1]
                    
                    # 布林带位置
                    if 'BB_Lower' in hist_data.columns and 'BB_Upper' in hist_data.columns:
                        bb_lower = latest['BB_Lower']
                        bb_upper = latest['BB_Upper']
                        bb_middle = latest['BB_Middle']
                    else:
                        bb_lower = current_price * 0.95
                        bb_upper = current_price * 1.05
                        bb_middle = current_price
                    
                    # 均线支撑
                    ma20_support = latest['MA20'] if 'MA20' in hist_data.columns else current_price * 0.98
                    
                    col_tech1, col_tech2 = st.columns(2)
                    with col_tech1:
                        tech_method = st.selectbox(
                            "选择技术指标方法",
                            ["布林带策略", "支撑阻力位", "均线支撑", "自定义组合"],
                            key=f"tech_method_{ticker}"
                        )
                    
                    with col_tech2:
                        safety_margin = st.slider(
                            "安全边际 (%)", 
                            min_value=1, 
                            max_value=5, 
                            value=2,
                            key=f"safety_margin_{ticker}"
                        )
                    
                    # 根据选择的方法计算止盈止损
                    if tech_method == "布林带策略":
                        tech_stop_loss = bb_lower * (1 - safety_margin / 100)
                        tech_take_profit = bb_upper * (1 + safety_margin / 100)
                        method_desc = "基于布林带上下轨"
                    elif tech_method == "支撑阻力位":
                        tech_stop_loss = support_level * (1 - safety_margin / 100)
                        tech_take_profit = resistance_level * (1 + safety_margin / 100)
                        method_desc = "基于20日支撑阻力位"
                    elif tech_method == "均线支撑":
                        tech_stop_loss = ma20_support * (1 - safety_margin / 100)
                        tech_take_profit = current_price * 1.15  # 15%固定止盈
                        method_desc = "基于20日均线支撑"
                    else:  # 自定义组合
                        tech_stop_loss = min(bb_lower, support_level, ma20_support) * (1 - safety_margin / 100)
                        tech_take_profit = max(bb_upper, resistance_level) * (1 + safety_margin / 100)
                        method_desc = "综合多个技术指标"
                    
                    st.info(f"📊 当前策略：{method_desc}")
                    
                    col_tech_metric1, col_tech_metric2, col_tech_metric3 = st.columns(3)
                    with col_tech_metric1:
                        st.metric(
                            "💰 当前盈亏", 
                            f"${pnl:.2f}",
                            f"{pnl_pct:+.2f}%"
                        )
                    with col_tech_metric2:
                        st.metric(
                            "🛡️ 技术止损", 
                            f"${tech_stop_loss:.2f}",
                            f"{((tech_stop_loss - current_price)/current_price*100):+.1f}%"
                        )
                    with col_tech_metric3:
                        st.metric(
                            "🎯 技术止盈", 
                            f"${tech_take_profit:.2f}",
                            f"{((tech_take_profit - current_price)/current_price*100):+.1f}%"
                        )
                    
                    # 显示关键技术位
                    st.markdown("**📊 关键技术位参考**")
                    tech_info_col1, tech_info_col2 = st.columns(2)
                    with tech_info_col1:
                        st.write(f"• 支撑位：${support_level:.2f}")
                        st.write(f"• 布林下轨：${bb_lower:.2f}")
                    with tech_info_col2:
                        st.write(f"• 阻力位：${resistance_level:.2f}")
                        st.write(f"• 布林上轨：${bb_upper:.2f}")
                
                # 策略3：波动率法
                with strategy_tab3:
                    st.markdown("#### 📉 波动率自适应止盈止损")
                    st.write("**适用场景**: 根据股票波动性调整止损幅度，高波动股票设置更大空间")
                    
                    # 计算ATR（Average True Range）
                    high_low = hist_data['High'] - hist_data['Low']
                    high_close = np.abs(hist_data['High'] - hist_data['Close'].shift())
                    low_close = np.abs(hist_data['Low'] - hist_data['Close'].shift())
                    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                    atr = tr.rolling(window=14).mean().iloc[-1]
                    
                    # 计算历史波动率
                    returns = hist_data['Close'].pct_change().dropna()
                    volatility = returns.std() * np.sqrt(252) * 100  # 年化波动率
                    
                    col_vol1, col_vol2 = st.columns(2)
                    with col_vol1:
                        atr_multiplier = st.slider(
                            "ATR倍数", 
                            min_value=1.0, 
                            max_value=4.0, 
                            value=2.0, 
                            step=0.1,
                            key=f"atr_mult_{ticker}"
                        )
                    with col_vol2:
                        vol_adjustment = st.selectbox(
                            "波动率调整",
                            ["低波动(保守)", "中波动(平衡)", "高波动(激进)"],
                            index=1,
                            key=f"vol_adj_{ticker}"
                        )
                    
                    # 根据波动率调整参数
                    if vol_adjustment == "低波动(保守)":
                        vol_multiplier = 0.8
                        base_tp_pct = 10
                    elif vol_adjustment == "中波动(平衡)":
                        vol_multiplier = 1.0
                        base_tp_pct = 15
                    else:  # 高波动
                        vol_multiplier = 1.2
                        base_tp_pct = 20
                    
                    # 计算波动率调整后的止盈止损
                    atr_stop_distance = atr * atr_multiplier * vol_multiplier
                    vol_stop_loss = max(buy_price - atr_stop_distance, buy_price * 0.90)  # 最大不超过10%
                    vol_take_profit = buy_price * (1 + base_tp_pct / 100)
                    
                    # 显示波动率信息
                    st.markdown("**📊 波动率分析**")
                    vol_info_col1, vol_info_col2, vol_info_col3 = st.columns(3)
                    with vol_info_col1:
                        st.metric("ATR", f"${atr:.2f}")
                    with vol_info_col2:
                        st.metric("年化波动率", f"{volatility:.1f}%")
                    with vol_info_col3:
                        vol_level = "高" if volatility > 30 else "中" if volatility > 20 else "低"
                        st.metric("波动等级", vol_level)
                    
                    col_vol_metric1, col_vol_metric2, col_vol_metric3 = st.columns(3)
                    with col_vol_metric1:
                        st.metric(
                            "💰 当前盈亏", 
                            f"${pnl:.2f}",
                            f"{pnl_pct:+.2f}%"
                        )
                    with col_vol_metric2:
                        st.metric(
                            "🛡️ ATR止损", 
                            f"${vol_stop_loss:.2f}",
                            f"{((vol_stop_loss - current_price)/current_price*100):+.1f}%"
                        )
                    with col_vol_metric3:
                        st.metric(
                            "🎯 波动率止盈", 
                            f"${vol_take_profit:.2f}",
                            f"{((vol_take_profit - current_price)/current_price*100):+.1f}%"
                        )
                    
                    st.info(f"💡 基于ATR的止损距离：${atr_stop_distance:.2f} ({((atr_stop_distance/current_price)*100):.1f}%)")
                
                # 策略4：成本加码法
                with strategy_tab4:
                    st.markdown("#### 🎯 成本加码动态止盈止损")
                    st.write("**适用场景**: 根据盈利情况动态调整止损位，保护利润并追求更大收益")
                    
                    col_cost1, col_cost2 = st.columns(2)
                    with col_cost1:
                        profit_threshold = st.slider(
                            "利润阈值 (%)", 
                            min_value=5, 
                            max_value=30, 
                            value=10,
                            help="超过此盈利后开始调整止损",
                            key=f"profit_threshold_{ticker}"
                        )
                    with col_cost2:
                        trailing_distance = st.slider(
                            "追踪距离 (%)", 
                            min_value=3, 
                            max_value=15, 
                            value=5,
                            help="止损跟随价格的距离",
                            key=f"trailing_distance_{ticker}"
                        )
                    
                    # 动态止损逻辑
                    profit_threshold_price = buy_price * (1 + profit_threshold / 100)
                    
                    if current_price >= profit_threshold_price:
                        # 已超过利润阈值，启用动态止损
                        # 止损位不低于成本价，并跟随最高价
                        highest_price = max(current_price, buy_price * 1.1)  # 模拟历史最高价
                        dynamic_stop_loss = max(
                            buy_price * 1.02,  # 成本价上2%
                            highest_price * (1 - trailing_distance / 100)
                        )
                        status_msg = f"🟢 **动态止损激活** (突破{profit_threshold}%利润阈值)"
                        dynamic_take_profit = buy_price * 1.25  # 25%止盈目标
                    else:
                        # 未达到利润阈值，使用普通止损
                        dynamic_stop_loss = buy_price * 0.92  # 8%固定止损
                        status_msg = f"🔵 **等待激活** (需突破{((profit_threshold_price - current_price)/current_price*100):+.1f}%)"
                        dynamic_take_profit = profit_threshold_price
                    
                    # 分阶段止盈设置
                    stage1_tp = buy_price * (1 + profit_threshold / 100)  # 第一阶段
                    stage2_tp = buy_price * 1.20  # 第二阶段 20%
                    stage3_tp = buy_price * 1.35  # 第三阶段 35%
                    
                    st.info(status_msg)
                    
                    col_cost_metric1, col_cost_metric2, col_cost_metric3 = st.columns(3)
                    with col_cost_metric1:
                        st.metric(
                            "💰 当前盈亏", 
                            f"${pnl:.2f}",
                            f"{pnl_pct:+.2f}%"
                        )
                    with col_cost_metric2:
                        st.metric(
                            "🛡️ 动态止损", 
                            f"${dynamic_stop_loss:.2f}",
                            f"{((dynamic_stop_loss - current_price)/current_price*100):+.1f}%"
                        )
                    with col_cost_metric3:
                        st.metric(
                            "🎯 当前目标", 
                            f"${dynamic_take_profit:.2f}",
                            f"{((dynamic_take_profit - current_price)/current_price*100):+.1f}%"
                        )
                    
                    # 分阶段止盈计划
                    st.markdown("**📊 分阶段止盈计划**")
                    stage_col1, stage_col2, stage_col3 = st.columns(3)
                    with stage_col1:
                        stage1_status = "✅" if current_price >= stage1_tp else "⏳"
                        st.write(f"{stage1_status} 阶段1: ${stage1_tp:.2f} ({profit_threshold}%)")
                    with stage_col2:
                        stage2_status = "✅" if current_price >= stage2_tp else "⏳"
                        st.write(f"{stage2_status} 阶段2: ${stage2_tp:.2f} (20%)")
                    with stage_col3:
                        stage3_status = "✅" if current_price >= stage3_tp else "⏳"
                        st.write(f"{stage3_status} 阶段3: ${stage3_tp:.2f} (35%)")
                    
                    # 操作建议
                    if current_price >= stage3_tp:
                        st.success("🎯 **第三阶段达成！建议分批止盈**")
                    elif current_price >= stage2_tp:
                        st.info("📈 **第二阶段达成！可考虑部分止盈**")
                    elif current_price >= stage1_tp:
                        st.info("💡 **第一阶段达成！动态止损已激活**")
                    else:
                        st.warning("⏳ **等待突破第一阶段**")
                
                # 策略对比总结
                st.markdown("---")
                st.markdown("#### 📊 四种策略对比总结")
                
                # 计算所有策略的止盈止损位
                strategies_summary = {
                    "策略": ["固定比例法", "技术指标法", "波动率法", "成本加码法"],
                    "止损位": [f"${fixed_stop_loss:.2f}", f"${tech_stop_loss:.2f}", f"${vol_stop_loss:.2f}", f"${dynamic_stop_loss:.2f}"],
                    "止盈位": [f"${fixed_take_profit:.2f}", f"${tech_take_profit:.2f}", f"${vol_take_profit:.2f}", f"${dynamic_take_profit:.2f}"],
                    "风险收益比": [
                        f"1:{fixed_rr:.2f}",
                        f"1:{((position_size * (tech_take_profit - buy_price)) / (position_size * (buy_price - tech_stop_loss))):.2f}",
                        f"1:{((position_size * (vol_take_profit - buy_price)) / (position_size * (buy_price - vol_stop_loss))):.2f}",
                        f"1:{((position_size * (dynamic_take_profit - buy_price)) / (position_size * (buy_price - dynamic_stop_loss))):.2f}"
                    ],
                    "适用场景": ["稳健投资", "技术分析", "高波动股", "趋势追踪"]
                }
                
                summary_df = pd.DataFrame(strategies_summary)
                st.dataframe(summary_df, hide_index=True, use_container_width=True)
                
                # 推荐策略
                st.markdown("#### 💡 智能策略推荐")
                if volatility > 30:
                    st.info("🔥 **推荐波动率法** - 当前股票波动性较高，适合使用ATR动态调整")
                elif technical_signals['trend'] == 'bullish' and pnl_pct > 5:
                    st.info("📈 **推荐成本加码法** - 当前处于上升趋势且有盈利，适合动态管理")
                elif current_price > bb_middle:
                    st.info("📊 **推荐技术指标法** - 技术形态明确，可根据支撑阻力位操作")
                else:
                    st.info("🎯 **推荐固定比例法** - 市场信号不明确时，固定比例最为稳健")
            
            # 增强版止盈止损分析（基于当前股票）
            if st.session_state.current_ticker == ticker:
                st.markdown("---")
                st.subheader("💰 智能止盈止损建议")
                
                with st.container():
                    # 基于技术分析和估值的止盈止损建议
                    dcf_value, _ = calculate_dcf_valuation(data)
                    
                    # 动态止损点计算
                    if 'MA20' in hist_data.columns:
                        ma20_support = hist_data['MA20'].iloc[-1]
                        dynamic_stop_loss = min(current_price * 0.92, ma20_support * 0.98)
                    else:
                        dynamic_stop_loss = current_price * 0.92
                    
                    # 动态止盈点计算
                    if dcf_value and dcf_value > current_price:
                        target_profit = dcf_value * 0.95
                    else:
                        target_profit = current_price * 1.15
                    
                    col_sl, col_tp = st.columns(2)
                    with col_sl:
                        st.metric(
                            "🛡️ 建议止损位", 
                            f"${dynamic_stop_loss:.2f}",
                            f"{((dynamic_stop_loss - current_price)/current_price*100):+.1f}%"
                        )
                    with col_tp:
                        st.metric(
                            "🎯 建议止盈位", 
                            f"${target_profit:.2f}",
                            f"{((target_profit - current_price)/current_price*100):+.1f}%"
                        )
                    
                    # 风险收益比
                    risk_amount = abs(current_price - dynamic_stop_loss)
                    reward_amount = abs(target_profit - current_price)
                    risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
                    
                    st.info(f"📊 风险收益比：1 : {risk_reward_ratio:.2f} {'(建议进场)' if risk_reward_ratio >= 2 else '(风险偏高)'}")
                    
                    # 基于技术指标的操作建议
                    if technical_signals['rsi_oversold'] and technical_signals['macd_golden_cross']:
                        st.success("💡 技术面显示超卖反弹机会，适合建仓")
                    elif technical_signals['rsi_overbought'] and technical_signals['macd_death_cross']:
                        st.warning("⚠️ 技术面显示超买风险，建议减仓")
                    else:
                        st.info("📊 技术面信号中性，建议观望或轻仓操作")

else:
    st.info("👈 请在左侧输入股票代码并点击分析按钮开始")
    
    with st.expander("📖 使用说明"):
        st.markdown("""
        ### 系统功能
        1. **自动数据获取**: 输入股票代码后，系统自动获取最新财务数据和历史价格
        2. **多维度分析**: 包含基本面、技术面、估值等多个维度的综合分析
        3. **智能建议**: 基于多个模型的评分，给出买入/卖出建议和仓位建议
        
        ### 分析模型说明
        - **Piotroski F-Score**: 评估公司财务健康状况（9分制）
        - **杜邦分析**: 分解ROE，了解盈利能力来源
        - **Altman Z-Score**: 预测企业破产风险
        - **DCF估值**: 基于现金流的内在价值评估
        - **相对估值**: PE、PB等指标与行业对比
        - **技术分析**: 均线、MACD等技术指标
        - **Kelly公式**: 科学计算最优投资仓位
        
        ### 新增功能 (v2.0)
        - **DCF参数详情**: 展示估值模型的详细参数
        - **历史估值分位**: 当前估值在历史中的位置
        - **财务趋势图**: 营收、利润、EPS趋势
        - **风险雷达图**: 多维度风险评估
        - **智能评分系统**: 价值面+技术面综合评分
        - **智能止盈止损模拟器**: 计算盈亏和关键价位
        
        ### 注意事项
        - 本系统仅供参考，不构成投资建议
        - 请结合其他信息进行综合判断
        - 投资有风险，入市需谨慎
        """)
    
    with st.expander("🆕 新功能展示"):
        st.markdown("### v2.0 新增功能预览")
        
        st.subheader("风险雷达图示例")
        categories = ['偿债能力', '波动性控制', '财务杠杆', '现金流增长', '盈利能力']
        values = [8, 7, 6, 5, 8]
        
        fig_demo = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='风险评分'
        ))
        
        fig_demo.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )
            ),
            showlegend=False,
            title="风险指标评分示例（10分制）",
            height=300
        )
        
        st.plotly_chart(fig_demo, use_container_width=True)
        
        st.subheader("智能评分示例")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("价值得分", "35/50")
        with col2:
            st.metric("技术得分", "40/50")
        with col3:
            st.metric("综合得分", "75/100")
        
        st.info("输入股票代码后即可查看完整分析结果")
    
    with st.expander("🚀 未来功能规划"):
        st.markdown("""
        - [ ] A股市场支持（集成tushare）
        - [ ] 一键导出PDF分析报告
        - [ ] 多股票对比分析
        - [ ] 自定义分析模型参数
        - [ ] 实时数据推送提醒
        - [ ] AI智能投资助手
        - [ ] 投资组合优化建议
        - [ ] 新闻情绪分析
        - [ ] 期权策略建议
        """)

# 页脚
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns([1, 2, 1])
with col_footer2:
    if st.button("🔙 返回首页 / 清除数据", type="secondary", use_container_width=True):
        st.rerun()

st.markdown("💹 智能投资分析系统 v2.0 | 仅供参考，投资需谨慎")
