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
        
        **2. 技术信号**
        - 金叉：买入信号
        - 死叉：卖出信号
        - RSI > 70：超买
        - RSI < 30：超卖
        
        **3. Piotroski F-score**
        - 7-9分：优秀
        - 4-6分：中等
        - 0-3分：较差
        """)

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
                    st.info("🎯 **推荐固定比例法** - 市场信号不明确时最为稳健")
                
                # 使用建议
                st.markdown("#### 🎓 策略选择指南")
                col_guide1, col_guide2 = st.columns(2)
                with col_guide1:
                    st.markdown("""
                    **🔰 新手投资者**:
                    - 固定比例法：简单易懂
                    - 建议：止盈15%，止损8%
                    
                    **📊 技术分析者**:
                    - 技术指标法：基于图表
                    - 布林带策略最实用
                    """)
                
                with col_guide2:
                    st.markdown("""
                    **🎯 进阶投资者**:
                    - 波动率法：适应变化
                    - 成本加码法：保护利润
                    
                    **⚡ 短线交易者**:
                    - 波动率法组合使用
                    - 快速响应市场
                    """)
                
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
    
    with st.expander("🆕 四种策略详解"):
        st.markdown("""
        ### 📊 固定比例法
        - **原理**: 设定固定的止盈/止损百分比
        - **优点**: 简单易懂，风险可控
        - **适用**: 稳健型投资者，大多数股票
        - **设置**: 如+15%止盈，-10%止损
        
        ### 📈 技术指标法  
        - **原理**: 基于技术分析设置关键位置
        - **包含**: 布林带、支撑阻力位、均线支撑
        - **优点**: 结合市场技术形态
        - **适用**: 有技术分析基础的投资者
        
        ### 📉 波动率法
        - **原理**: 根据股票波动性动态调整
        - **核心**: ATR指标和历史波动率
        - **优点**: 自适应市场变化
        - **适用**: 高波动性股票，专业投资者
        
        ### 🎯 成本加码法
        - **原理**: 根据盈利情况动态调整止损
        - **特色**: 分阶段止盈，保护利润
        - **优点**: 最大化收益，降低回撤
        - **适用**: 趋势行情，进阶投资者
        """)

# 页脚
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns([1, 2, 1])
with col_footer2:
    if st.button("🔙 返回首页 / 清除数据", type="secondary", use_container_width=True):
        st.rerun()

st.markdown("💹 智能投资分析系统 v2.0 | 仅供参考，投资需谨慎")error("💡 建议: 财务状况较差，投资风险较高")
            
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
            
            # 智能止盈止损模拟器 - 四种策略
            st.markdown("---")
            st.subheader("💰 智能止盈止损模拟器")
            
            with st.container():
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
                
                # 策略2：技术指标法
                with tab2:
                    st.write("**适用场景**: 基于支撑阻力位、布林带等技术分析")
                    
                    # 计算技术位
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
                
                # 策略3：波动率法
                with tab3:
                    st.write("**适用场景**: 根据股票波动性调整，高波动股票设置更大空间")
                    
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
                
                # 策略推荐
                st.markdown("---")
                st.markdown("#### 💡 智能策略推荐")
                
                technical_signals = analyze_technical_signals(hist_data)
                returns = hist_data['Close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252) * 100
                
                if volatility > 30:
                    st.info("🔥 **推荐波动率法** - 当前股票波动性较高")
                elif technical_signals['trend'] == 'bullish' and pnl_pct > 5:
                    st.info("📈 **推荐成本加码法** - 当前上升趋势且有盈利")
                elif 'BB_Middle' in hist_data.columns and current_price > hist_data['BB_Middle'].iloc[-1]:
                    st.info("📊 **推荐技术指标法** - 技术形态明确")
                else:
                    st.
