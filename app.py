import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
import plotly.graph_objects as go
warnings.filterwarnings('ignore')

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
if 'show_analysis' not in st.session_state:
    st.session_state.show_analysis = False

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

# ==================== 分析函数 ====================
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
            if latest['RSI'] < 30:
                signals['rsi_oversold'] = True
            elif latest['RSI'] > 70:
                signals['rsi_overbought'] = True
        
        if latest['Close'] > latest['MA60']:
            signals['trend'] = 'bullish'
        else:
            signals['trend'] = 'bearish'
            
    except Exception as e:
        st.warning(f"技术信号分析失败: {str(e)}")
    
    return signals

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
          - >50%：强买入
          - 20-50%：买入
          - 0-20%：观察
          - <0%：避免
        
        **2. 信心度 (Confidence)**
        - >70%：高信心度
        - 50-70%：中等信心
        - <50%：低信心度
        
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
        ### 综合评分决策表
        | 安全边际 | 信心度 | 操作建议 |
        |---------|--------|----------|
        | >30%    | >70%   | ✅ 强买入 |
        | >0%     | >50%   | ⚠️ 观察  |
        | <0%     | ≈50%   | 🔍 观望  |
        | <0%     | <50%   | 🚫 回避  |
        
        ### Piotroski F-Score解读
        | 得分 | 评级 | 建议 |
        |------|------|------|
        | 8-9分 | 🟢 优秀 | 强烈买入 |
        | 6-7分 | 🟡 良好 | 可以买入 |
        | 4-5分 | 🟠 一般 | 谨慎观察 |
        | 0-3分 | 🔴 较差 | 避免投资 |
        
        ### Altman Z-Score风险等级
        | Z-Score | 风险等级 | 说明 |
        |---------|----------|------|
        | >2.99 | 🟢 安全 | 破产风险极低 |
        | 1.81-2.99 | 🟡 灰色 | 需要关注 |
        | <1.81 | 🔴 危险 | 破产风险高 |
        
        ### DCF估值参考
        - **安全边际 > 20%**: 明显低估，考虑买入
        - **安全边际 0-20%**: 合理估值区间
        - **安全边际 < 0%**: 高估，谨慎投资
        """)
    
    with st.expander("📈 技术分析指标说明"):
        st.markdown("""
        ### 均线系统
        - **MA10 > MA20 > MA60**: 🟢 多头排列，趋势向上
        - **MA10 < MA20 < MA60**: 🔴 空头排列，趋势向下
        - **金叉**: 短期均线上穿长期均线，买入信号
        - **死叉**: 短期均线下穿长期均线，卖出信号
        
        ### MACD指标
        - **MACD > Signal**: 🟢 多头市场
        - **MACD < Signal**: 🔴 空头市场
        - **MACD金叉**: DIF上穿DEA，买入信号
        - **MACD死叉**: DIF下穿DEA，卖出信号
        - **柱状图**: 反映趋势强度变化
        
        ### RSI相对强弱指标
        - **RSI > 70**: ⚠️ 超买，可能回调
        - **RSI < 30**: 💡 超卖，可能反弹
        - **30-70区间**: 📊 正常波动区间
        - **50附近**: 多空平衡点
        
        ### 布林带指标
        - **价格突破上轨**: 🔺 强势突破或超买
        - **价格跌破下轨**: 🔻 超卖或弱势
        - **价格在中轨上方**: 📈 多头趋势
        - **价格在中轨下方**: 📉 空头趋势
        - **带宽收窄**: 变盘在即
        - **带宽扩张**: 趋势加强
        
        ### 成交量分析
        - **价涨量增**: 🟢 健康上涨
        - **价涨量缩**: 🟡 上涨乏力
        - **价跌量增**: 🔴 恐慌抛售
        - **价跌量缩**: 🟡 下跌放缓
        """)
    
    with st.expander("💰 财务指标详解"):
        st.markdown("""
        ### 杜邦分析系统
        **ROE = 利润率 × 资产周转率 × 权益乘数**
        
        - **利润率**: 每1元销售收入的净利润
          - >15%: 优秀
          - 10-15%: 良好
          - 5-10%: 一般
          - <5%: 较差
        
        - **资产周转率**: 资产使用效率
          - >1.5: 高效
          - 1.0-1.5: 正常
          - 0.5-1.0: 偏低
          - <0.5: 低效
        
        - **权益乘数**: 财务杠杆水平
          - 1-2: 保守
          - 2-3: 适中
          - 3-5: 激进
          - >5: 高风险
        
        ### DCF估值模型参数
        - **增长率**: 未来收入增长预期
        - **折现率**: 投资要求回报率
        - **永续增长率**: 终值期增长率
        - **预测年限**: 详细预测期间
        
        ### 现金流分析
        - **经营现金流 > 净利润**: ✅ 质量良好
        - **经营现金流 < 净利润**: ❌ 需要关注
        - **自由现金流 > 0**: 有真实盈利能力
        - **自由现金流 < 0**: 资金紧张
        
        ### 财务健康指标
        - **流动比率**: 流动资产/流动负债
          - >2: 很安全
          - 1.5-2: 安全
          - 1-1.5: 一般
          - <1: 风险
        
        - **资产负债率**: 总负债/总资产
          - <30%: 保守
          - 30-60%: 适中
          - 60-80%: 偏高
          - >80%: 高风险
        """)
    
    with st.expander("🎯 投资策略建议"):
        st.markdown("""
        ### 价值投资策略
        **适合指标组合**:
        - Piotroski F-Score ≥ 7分
        - Altman Z-Score > 2.99
        - DCF安全边际 > 20%
        - PE < 行业平均
        
        **操作建议**:
        - 长期持有（1年以上）
        - 分批建仓
        - 重视基本面变化
        - 忽略短期波动
        
        ### 趋势投资策略
        **适合指标组合**:
        - 均线多头排列
        - MACD金叉
        - RSI 30-70区间
        - 成交量配合
        
        **操作建议**:
        - 顺势而为
        - 止损严格执行
        - 关注技术信号
        - 及时止盈
        
        ### 波段操作策略
        **适合指标组合**:
        - RSI超卖/超买
        - 布林带极值
        - 支撑阻力位
        - 高波动率
        
        **操作建议**:
        - 快进快出
        - 严格止损
        - 把握节奏
        - 控制仓位
        
        ### 防御性投资
        **适合市场环境**:
        - 市场不确定性高
        - 经济周期下行
        - 个股风险较大
        
        **选股标准**:
        - Altman Z-Score > 2.99
        - 稳定分红历史
        - 低Beta值
        - 防御性行业
        """)
    
    with st.expander("⚠️ 风险管理"):
        st.markdown("""
        ### 仓位管理原则
        - **单只股票**: 不超过总资产的10%
        - **同行业**: 不超过总资产的20%
        - **高风险股**: 不超过总资产的5%
        - **现金储备**: 保持10-20%现金
        
        ### 止损策略执行
        1. **技术止损**: 跌破关键支撑位
        2. **比例止损**: 亏损达到预设比例
        3. **时间止损**: 长期横盘无起色
        4. **基本面止损**: 基本面恶化
        
        ### 分散投资建议
        - **行业分散**: 投资3-5个不同行业
        - **地域分散**: 不同国家/地区市场
        - **时间分散**: 分批投入资金
        - **工具分散**: 股票+债券+其他资产
        
        ### 常见投资陷阱
        - ❌ 追涨杀跌
        - ❌ 重仓单只股票
        - ❌ 不设止损
        - ❌ 频繁交易
        - ❌ 情绪化决策
        - ❌ 忽视基本面
        - ❌ 盲目跟风
        
        ### 投资纪律要求
        ✅ 制定投资计划并严格执行
        ✅ 定期检视投资组合
        ✅ 持续学习和改进
        ✅ 保持理性和耐心
        ✅ 记录投资决策过程
        ✅ 及时总结经验教训
        """)
    
    with st.expander("💡 智能策略推荐"):
        st.markdown("""
        ### 🎓 策略选择指南
        
        **🔰 新手投资者**:
        - 固定比例法：简单易懂
        - 建议：止盈15%，止损8%
        
        **📊 技术分析者**:
        - 技术指标法：基于图表
        - 布林带策略最实用
        
        **🎯 进阶投资者**:
        - 波动率法：适应变化
        - 成本加码法：保护利润
        
        **⚡ 短线交易者**:
        - 波动率法组合使用
        - 快速响应市场
        
        ### 📈 系统推荐逻辑
        - **高波动股票** → 推荐波动率法
        - **有盈利时** → 推荐成本加码法
        - **技术形态明确** → 推荐技术指标法
        - **信号不明确** → 推荐固定比例法
        """)

# 主界面逻辑
if analyze_button and ticker:
    st.session_state.current_ticker = ticker
    st.session_state.show_analysis = True
    
    with st.spinner(f"正在获取 {ticker} 的数据..."):
        try:
            data = fetch_stock_data(ticker)
        except:
            data = fetch_stock_data_uncached(ticker)
    
    if data:
        current_price = data['info'].get('currentPrice', 0)
        st.session_state.current_price = current_price
        st.session_state.analysis_data = data

# 显示分析结果
if st.session_state.show_analysis and st.session_state.analysis_data is not None:
    data = st.session_state.analysis_data
    current_price = st.session_state.current_price
    ticker = st.session_state.current_ticker
    
    col1, col2, col3 = st.columns([1, 2, 1.5])
    
    # 左栏：基本信息
    with col1:
        st.subheader("📌 公司基本信息")
        info = data['info']
        
        st.metric("公司名称", info.get('longName', ticker))
        st.metric("当前股价", f"${current_price:.2f}")
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
        
        # DCF估值分析
        with st.expander("💎 DCF估值分析", expanded=True):
            dcf_value, dcf_params = calculate_dcf_valuation(data)
            
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
    
    # 右栏：技术分析和止盈止损模拟器
    with col3:
        st.subheader("📉 技术分析与建议")
        
        # 计算技术指标
        hist_data = data['hist_data'].copy()
        hist_data = calculate_technical_indicators(hist_data)
        
        # 价格走势图
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(hist_data.index[-180:], hist_data['Close'][-180:], label='Close', linewidth=2)
        if 'MA20' in hist_data.columns:
            ax.plot(hist_data.index[-180:], hist_data['MA20'][-180:], label='MA20', alpha=0.7)
        if 'MA60' in hist_data.columns:
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
        if 'MACD' in hist_data.columns:
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
        
        # 技术分析结论展示
        st.markdown("---")
        st.subheader("📊 技术指标快速解读")
        
        # 计算技术信号
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
                if 'MACD' in hist_data.columns and 'Signal' in hist_data.columns:
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
        
        # Altman Z-score 简洁展示
        st.markdown("---")
        z_score, status, color = calculate_altman_z_score(data)
        if z_score and z_score > 0:
            if color == "green":
                st.success(f"📊 破产风险评分（Altman Z-score）：{z_score:.2f} ✅ {status}")
            elif color == "orange":
                st.warning(f"📊 破产风险评分（Altman Z-score）：{z_score:.2f} ⚠️ {status}")
            else:
                st.error(f"📊 破产风险评分（Altman Z-score）：{z_score:.2f} 🚨 {status}")
        else:
            st.info("📊 破产风险评分：数据不足，无法计算")
        
        # 智能止盈止损模拟器（保持原有功能不变）
        st.markdown("---")
        st.subheader("💰 智能止盈止损模拟器")
        
        st.info(f"📊 当前分析股票：{ticker} | 实时价格：${current_price:.2f}")
        
        # 输入参数
        col_input1, col_input2 = st.columns(2)
        with col_input1:
            default_buy_price = current_price * 0.95
            buy_price = st.number_input(
                "买入价格 ($)", 
                min_value=0.01, 
                value=default_buy_price, 
                step=0.01, 
                key=f"buy_price_{ticker}"
            )
        with col_input2:
            position_size = st.number_input(
                "持仓数量", 
                min_value=1, 
                value=100, 
                step=1,
                key=f"position_size_{ticker}"
            )
        
        # 基础计算
        position_value = position_size * buy_price
        current_value = position_size * current_price
        pnl = current_value - position_value
        pnl_pct = (pnl / position_value) * 100 if position_value > 0 else 0
        
        # 四种策略标签页
        st.markdown("#### 🎯 选择止盈止损策略")
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 固定比例法", 
            "📈 技术指标法", 
            "📉 波动率法", 
            "🎯 成本加码法"
        ])
        
        # 策略1：固定比例法
        with tab1:
            st.write("**适用场景**: 大多数波动性股票，适合稳健型投资者")
            
            col1, col2 = st.columns(2)
            with col1:
                tp_pct = st.slider("止盈比例 (%)", 5, 50, 15, key=f"tp1_{ticker}")
            with col2:
                sl_pct = st.slider("止损比例 (%)", 3, 20, 10, key=f"sl1_{ticker}")
            
            stop_loss = buy_price * (1 - sl_pct / 100)
            take_profit = buy_price * (1 + tp_pct / 100)
            
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("💰 当前盈亏", f"${pnl:.2f}", f"{pnl_pct:+.2f}%")
            with col_m2:
                st.metric("🛡️ 止损价位", f"${stop_loss:.2f}")
            with col_m3:
                st.metric("🎯 止盈价位", f"${take_profit:.2f}")
            
            if current_price <= stop_loss:
                st.error("⚠️ 已触及止损线！")
            elif current_price >= take_profit:
                st.success("🎯 已达到止盈目标！")
            else:
                st.info("📊 持仓正常")
            
            # 风险收益分析
            risk_amount = position_size * (buy_price - stop_loss)
            reward_amount = position_size * (take_profit - buy_price)
            rr_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            st.caption(f"💡 风险收益比：1:{rr_ratio:.2f}")
        
        # 策略2：技术指标法
        with tab2:
            st.write("**适用场景**: 基于支撑阻力位、布林带等技术分析")
            
            # 计算技术位
            if len(hist_data) > 20:
                latest = hist_data.iloc[-1]
                support = hist_data['Low'].rolling(20).min().iloc[-1]
                resistance = hist_data['High'].rolling(20).max().iloc[-1]
                
                if 'BB_Lower' in hist_data.columns:
                    bb_lower = latest['BB_Lower']
                    bb_upper = latest['BB_Upper']
                else:
                    bb_lower = current_price * 0.95
                    bb_upper = current_price * 1.05
                
                tech_method = st.selectbox(
                    "技术指标方法",
                    ["布林带策略", "支撑阻力位", "均线支撑"],
                    key=f"tech_method_{ticker}"
                )
                
                if tech_method == "布林带策略":
                    tech_sl = bb_lower * 0.98
                    tech_tp = bb_upper * 1.02
                elif tech_method == "支撑阻力位":
                    tech_sl = support * 0.98
                    tech_tp = resistance * 1.02
                else:
                    ma20 = latest['MA20'] if 'MA20' in hist_data.columns else current_price * 0.98
                    tech_sl = ma20 * 0.98
                    tech_tp = current_price * 1.15
                
                col_t1, col_t2, col_t3 = st.columns(3)
                with col_t1:
                    st.metric("💰 当前盈亏", f"${pnl:.2f}", f"{pnl_pct:+.2f}%")
                with col_t2:
                    st.metric("🛡️ 技术止损", f"${tech_sl:.2f}")
                with col_t3:
                    st.metric("🎯 技术止盈", f"${tech_tp:.2f}")
                
                st.write(f"• 支撑位: ${support:.2f}")
                st.write(f"• 阻力位: ${resistance:.2f}")
            else:
                st.warning("数据不足，无法计算技术指标")
        
        # 策略3：波动率法
        with tab3:
            st.write("**适用场景**: 根据股票波动性调整，高波动股票设置更大空间")
            
            if len(hist_data) > 14:
                # 计算ATR
                high_low = hist_data['High'] - hist_data['Low']
                high_close = np.abs(hist_data['High'] - hist_data['Close'].shift())
                low_close = np.abs(hist_data['Low'] - hist_data['Close'].shift())
                tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr = tr.rolling(14).mean().iloc[-1]
                
                # 计算波动率
                returns = hist_data['Close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252) * 100
                
                atr_mult = st.slider("ATR倍数", 1.0, 4.0, 2.0, 0.1, key=f"atr_{ticker}")
                
                vol_sl = max(buy_price - atr * atr_mult, buy_price * 0.90)
                vol_tp = buy_price * 1.15
                
                col_v1, col_v2, col_v3 = st.columns(3)
                with col_v1:
                    st.metric("ATR", f"${atr:.2f}")
                with col_v2:
                    st.metric("年化波动率", f"{volatility:.1f}%")
                with col_v3:
                    vol_level = "高" if volatility > 30 else "中" if volatility > 20 else "低"
                    st.metric("波动等级", vol_level)
                
                col_vm1, col_vm2, col_vm3 = st.columns(3)
                with col_vm1:
                    st.metric("💰 当前盈亏", f"${pnl:.2f}", f"{pnl_pct:+.2f}%")
                with col_vm2:
                    st.metric("🛡️ ATR止损", f"${vol_sl:.2f}")
                with col_vm3:
                    st.metric("🎯 波动率止盈", f"${vol_tp:.2f}")
            else:
                st.warning("数据不足，无法计算波动率指标")
        
        # 策略4：成本加码法
        with tab4:
            st.write("**适用场景**: 根据盈利情况动态调整，保护利润追求更大收益")
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                profit_threshold = st.slider("利润阈值 (%)", 5, 30, 10, key=f"profit_{ticker}")
            with col_c2:
                trailing_dist = st.slider("追踪距离 (%)", 3, 15, 5, key=f"trail_{ticker}")
            
            threshold_price = buy_price * (1 + profit_threshold / 100)
            
            if current_price >= threshold_price:
                # 动态止损激活
                dynamic_sl = max(buy_price * 1.02, current_price * (1 - trailing_dist / 100))
                status = f"🟢 动态止损激活 (突破{profit_threshold}%)"
                dynamic_tp = buy_price * 1.25
            else:
                # 普通止损
                dynamic_sl = buy_price * 0.92
                need_rise = ((threshold_price - current_price) / current_price * 100)
                status = f"🔵 等待激活 (需上涨{need_rise:.1f}%)"
                dynamic_tp = threshold_price
            
            st.info(status)
            
            # 分阶段目标
            stage1 = threshold_price
            stage2 = buy_price * 1.20
            stage3 = buy_price * 1.35
            
            col_cm1, col_cm2, col_cm3 = st.columns(3)
            with col_cm1:
                st.metric("💰 当前盈亏", f"${pnl:.2f}", f"{pnl_pct:+.2f}%")
            with col_cm2:
                st.metric("🛡️ 动态止损", f"${dynamic_sl:.2f}")
            with col_cm3:
                st.metric("🎯 当前目标", f"${dynamic_tp:.2f}")
            
            st.markdown("**分阶段目标**")
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                s1_status = "✅" if current_price >= stage1 else "⏳"
                st.write(f"{s1_status} 阶段1: ${stage1:.2f}")
            with col_s2:
                s2_status = "✅" if current_price >= stage2 else "⏳"
                st.write(f"{s2_status} 阶段2: ${stage2:.2f}")
            with col_s3:
                s3_status = "✅" if current_price >= stage3 else "⏳"
                st.write(f"{s3_status} 阶段3: ${stage3:.2f}")
        
        # 策略推荐（简化版）
        st.markdown("---")
        st.markdown("#### 💡 当前推荐策略")
        
        try:
            returns = hist_data['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100
            
            if volatility > 30:
                st.info("🔥 **推荐波动率法** - 当前股票波动性较高")
            elif pnl_pct > 5:
                st.info("📈 **推荐成本加码法** - 当前有盈利，适合动态管理")
            elif len(hist_data) > 20 and 'BB_Middle' in hist_data.columns:
                st.info("📊 **推荐技术指标法** - 技术形态明确")
            else:
                st.info("🎯 **推荐固定比例法** - 市场信号不明确时最为稳健")
        except:
            st.info("🎯 **推荐固定比例法** - 适合大多数投资场景")
        
        # 风险提示
        st.warning("""
        ⚠️ **风险提示**: 所有策略仅供参考，实际投资需结合市场环境。
        止损是风险管理工具，执行纪律比策略更重要。投资有风险，入市需谨慎。
        """)

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
        - **技术分析**: 均线、MACD、RSI、布林带等技术指标
        
        ### 新增功能 - 四种止盈止损策略
        - **📊 固定比例法**: 设定固定止盈止损百分比，适合稳健投资
        - **📈 技术指标法**: 基于布林带、支撑阻力位等技术分析
        - **📉 波动率法**: 根据ATR和历史波动率动态调整
        - **🎯 成本加码法**: 动态止损和分阶段止盈，保护利润
        
        ### 注意事项
        - 本系统仅供参考，不构成投资建议
        - 请结合其他信息进行综合判断
        - 投资有风险，入市需谨慎
        """)
    
    with st.expander("🆕 新功能展示"):
        st.markdown("### v2.0 新增功能预览")
        
        st.subheader("技术分析图表")
        st.write("• 📈 价格走势图（包含均线MA20、MA60）")
        st.write("• 📊 MACD指标图（含金叉死叉信号）")
        st.write("• 🎯 技术指标状态实时监控")
        
        st.subheader("财务分析模块")
        st.write("• 🔍 Piotroski F-Score财务健康评分")
        st.write("• 📊 杜邦分析ROE分解")
        st.write("• 💰 Altman Z-Score破产风险评估")
        st.write("• 💎 DCF现金流折现估值")
        
        st.subheader("智能止盈止损系统")
        st.write("• 📊 固定比例法：简单实用")
        st.write("• 📈 技术指标法：专业分析")
        st.write("• 📉 波动率法：自适应调整")
        st.write("• 🎯 成本加码法：动态管理")
        
        st.info("输入股票代码后即可查看完整分析结果")
    
    with st.expander("🚀 系统特色"):
        st.markdown("""
        ### 📊 全面的分析维度
        - **基本面分析**: 财务健康度、盈利能力、估值水平
        - **技术面分析**: 趋势判断、信号识别、支撑阻力
        - **风险评估**: 破产风险、波动性分析、止损建议
        
        ### 🎯 智能化特性
        - **自动推荐**: 根据股票特性推荐最适合的策略
        - **实时计算**: 参数调整即时反馈
        - **可视化**: 直观的图表和状态显示
        
        ### 💡 用户友好
        - **分层设计**: 新手到专家都能找到适合的功能
        - **状态持久**: 参数调整不会重新加载
        - **详细说明**: 每个指标都有使用指导
        """)

# 页脚
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns([1, 2, 1])
with col_footer2:
    if st.button("🔙 返回首页 / 清除数据", type="secondary", use_container_width=True):
        st.session_state.show_analysis = False
        st.session_state.current_ticker = None
        st.session_state.current_price = 0
        st.session_state.analysis_data = None
        st.rerun()

st.markdown("💹 智能投资分析系统 v2.0 | 仅供参考，投资需谨慎")
