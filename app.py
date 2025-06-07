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
        
        return {
            'info': info,
            'hist_data': hist_data.copy()
        }
    except Exception as e:
        st.error(f"获取数据失败: {str(e)}")
        return None

def calculate_technical_indicators(hist_data):
    """计算技术指标"""
    try:
        hist_data['MA20'] = hist_data['Close'].rolling(window=20).mean()
        hist_data['MA60'] = hist_data['Close'].rolling(window=60).mean()
        
        hist_data['BB_Middle'] = hist_data['Close'].rolling(window=20).mean()
        bb_std = hist_data['Close'].rolling(window=20).std()
        hist_data['BB_Upper'] = hist_data['BB_Middle'] + (bb_std * 2)
        hist_data['BB_Lower'] = hist_data['BB_Middle'] - (bb_std * 2)
        
        return hist_data
    except Exception as e:
        st.warning(f"技术指标计算失败: {str(e)}")
        return hist_data

# ==================== 主程序 ====================
# 侧边栏输入
with st.sidebar:
    st.header("📊 分析参数设置")
    
    ticker = st.text_input("股票代码", "AAPL", help="输入股票代码，如：AAPL")
    analyze_button = st.button("🔍 开始分析", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    with st.expander("📘 使用说明"):
        st.markdown("""
        ### 四种止盈止损策略
        
        **📊 固定比例法**: 设定固定止盈止损比例
        **📈 技术指标法**: 基于布林带、支撑阻力位
        **📉 波动率法**: 根据ATR动态调整
        **🎯 成本加码法**: 动态止损保护利润
        """)

# 主界面逻辑
if analyze_button and ticker:
    st.session_state.current_ticker = ticker
    st.session_state.show_analysis = True
    
    with st.spinner(f"正在获取 {ticker} 的数据..."):
        data = fetch_stock_data(ticker)
    
    if data:
        current_price = data['info'].get('currentPrice', 0)
        st.session_state.current_price = current_price
        st.session_state.analysis_data = data

# 显示分析结果
if st.session_state.show_analysis and st.session_state.analysis_data is not None:
    data = st.session_state.analysis_data
    current_price = st.session_state.current_price
    ticker = st.session_state.current_ticker
    
    col1, col2 = st.columns([1, 2])
    
    # 左栏：基本信息
    with col1:
        st.subheader("📌 公司基本信息")
        info = data['info']
        
        st.metric("公司名称", info.get('longName', ticker))
        st.metric("当前股价", f"${current_price:.2f}")
        st.metric("市值", f"${info.get('marketCap', 0)/1e9:.2f}B")
        st.metric("行业", info.get('industry', 'N/A'))
    
    # 右栏：止盈止损模拟器
    with col2:
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
        
        # 计算技术指标
        hist_data = data['hist_data'].copy()
        hist_data = calculate_technical_indicators(hist_data)
        
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
        
        # 策略推荐和使用指南
        st.markdown("---")
        st.markdown("#### 💡 智能策略推荐")
        
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
        ### 四种止盈止损策略详解
        
        **📊 固定比例法**
        - 设定固定的止盈/止损百分比
        - 适合稳健型投资者
        - 如+15%止盈，-10%止损
        
        **📈 技术指标法**  
        - 基于布林带、支撑阻力位等
        - 结合市场技术形态
        - 适合有技术分析基础的投资者
        
        **📉 波动率法**
        - 根据ATR和历史波动率调整
        - 自适应市场变化
        - 适合高波动性股票
        
        **🎯 成本加码法**
        - 根据盈利情况动态调整止损
        - 分阶段止盈，保护利润
        - 适合趋势行情
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
