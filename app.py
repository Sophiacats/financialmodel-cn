import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 页面配置
st.set_page_config(
    page_title="💹 我的智能投资分析系统",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("💹 我的智能投资分析系统")
st.markdown("---")

# ==================== 缓存函数 ====================
@st.cache_data(ttl=3600)
def fetch_stock_data(ticker):
    """获取股票数据"""
    try:
        stock = yf.Ticker(ticker)
        info = dict(stock.info)  # 转换为普通字典
        
        # 获取历史数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*2)
        hist_data = stock.history(start=start_date, end=end_date)
        
        # 获取财务数据
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        # 确保所有数据都是可序列化的
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

# 不使用缓存的版本，用于获取实时数据
def fetch_stock_data_uncached(ticker):
    """获取股票数据（不缓存版本）"""
    try:
        stock = yf.Ticker(ticker)
        info = dict(stock.info)
        
        # 获取历史数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*2)
        hist_data = stock.history(start=start_date, end=end_date)
        
        # 获取财务数据
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
        
        # 检查数据是否为空
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
        # 由于yfinance数据限制，这里简化计算
        score += 3  # 给予基础分数
        reasons.append("📊 财务结构基础分: 3分")
        
    except Exception as e:
        st.warning(f"Piotroski Score计算部分指标失败: {str(e)}")
        return 0, ["❌ 计算过程出现错误"]
    
    return score, reasons

def calculate_dupont_analysis(data):
    """杜邦分析"""
    try:
        info = data['info']
        
        # 获取关键指标
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
        
        # 检查数据是否为空
        if balance_sheet.empty:
            return 0, "数据不足", "gray"
        
        # 获取必要数据，使用get方法避免KeyError
        total_assets = info.get('totalAssets', 0)
        
        # 安全获取资产负债表数据
        current_assets = 0
        current_liabilities = 0
        retained_earnings = 0
        total_liabilities = 0
        
        if not balance_sheet.empty and len(balance_sheet.columns) > 0:
            # 尝试不同的可能字段名
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
        
        # 如果总资产为0或负数，返回默认值
        if total_assets <= 0:
            return 0, "数据不足", "gray"
        
        # 计算Z-Score组成部分
        working_capital = current_assets - current_liabilities
        
        A = (working_capital / total_assets) * 1.2
        B = (retained_earnings / total_assets) * 1.4 if not pd.isna(retained_earnings) else 0
        C = (ebit / total_assets) * 3.3 if ebit > 0 else 0
        D = (market_cap / total_liabilities) * 0.6 if total_liabilities > 0 else 0
        E = (revenue / total_assets) * 1.0 if revenue > 0 else 0
        
        z_score = A + B + C + D + E
        
        # 处理异常值
        if pd.isna(z_score) or z_score < -10 or z_score > 10:
            z_score = 0
        
        # 判断财务健康状态
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
        
        # 检查数据是否为空
        if cash_flow.empty:
            return None
        
        # 获取自由现金流
        fcf = 0
        if 'Free Cash Flow' in cash_flow.index and len(cash_flow.columns) > 0:
            fcf = cash_flow.loc['Free Cash Flow'].iloc[0]
        elif 'Operating Cash Flow' in cash_flow.index and len(cash_flow.columns) > 0:
            # 如果没有自由现金流，使用经营现金流估算
            ocf = cash_flow.loc['Operating Cash Flow'].iloc[0]
            capex = cash_flow.loc['Capital Expenditure'].iloc[0] if 'Capital Expenditure' in cash_flow.index else 0
            fcf = ocf + capex  # capex通常是负数
        
        # 如果现金流为负或0，无法进行DCF估值
        if fcf <= 0:
            return None
        
        # 假设增长率和折现率
        growth_rate = 0.05  # 5%增长率
        discount_rate = 0.10  # 10%折现率
        terminal_growth = 0.02  # 2%永续增长率
        
        # 计算5年现金流现值
        dcf_value = 0
        for i in range(1, 6):
            future_fcf = fcf * (1 + growth_rate) ** i
            pv = future_fcf / (1 + discount_rate) ** i
            dcf_value += pv
        
        # 计算终值
        terminal_fcf = fcf * (1 + growth_rate) ** 5 * (1 + terminal_growth)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth)
        terminal_pv = terminal_value / (1 + discount_rate) ** 5
        
        # 企业价值
        enterprise_value = dcf_value + terminal_pv
        
        # 计算每股价值
        shares = info.get('sharesOutstanding', 0)
        if shares <= 0:
            return None
            
        fair_value_per_share = enterprise_value / shares
        
        # 合理性检查
        if fair_value_per_share < 0 or fair_value_per_share > 10000:
            return None
            
        return fair_value_per_share
    except Exception as e:
        st.warning(f"DCF估值计算失败: {str(e)}")
        return None

def calculate_relative_valuation(data):
    """相对估值分析"""
    try:
        info = data['info']
        
        pe_ratio = info.get('trailingPE', 0)
        pb_ratio = info.get('priceToBook', 0)
        ev_ebitda = info.get('enterpriseToEbitda', 0)
        
        # 行业平均值（这里使用假设值，实际应用中应该从数据库获取）
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
        # 计算移动平均线
        hist_data['MA20'] = hist_data['Close'].rolling(window=20).mean()
        hist_data['MA60'] = hist_data['Close'].rolling(window=60).mean()
        
        # 计算MACD
        exp1 = hist_data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist_data['Close'].ewm(span=26, adjust=False).mean()
        hist_data['MACD'] = exp1 - exp2
        hist_data['Signal'] = hist_data['MACD'].ewm(span=9, adjust=False).mean()
        hist_data['MACD_Histogram'] = hist_data['MACD'] - hist_data['Signal']
        
        # 计算RSI
        delta = hist_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist_data['RSI'] = 100 - (100 / (1 + rs))
        
        return hist_data
    except Exception as e:
        st.warning(f"技术指标计算失败: {str(e)}")
        return hist_data

def calculate_kelly_criterion(win_prob, win_loss_ratio):
    """Kelly公式计算推荐仓位"""
    f = (win_prob * win_loss_ratio - (1 - win_prob)) / win_loss_ratio
    return max(0, min(f, 0.25))  # 限制最大仓位为25%

# ==================== 主程序 ====================
# 侧边栏输入
with st.sidebar:
    st.header("📊 分析参数设置")
    
    # 股票代码输入
    ticker = st.text_input("股票代码", "AAPL", help="输入股票代码，如：AAPL")
    
    # 市场选择（预留扩展）
    market = st.selectbox("市场选择", ["美股", "A股（待开发）"])
    
    # 分析按钮
    analyze_button = st.button("🔍 开始分析", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 说明")
    st.markdown("- 输入股票代码后点击分析")
    st.markdown("- 系统将自动获取数据并进行全面分析")
    st.markdown("- 分析包含基本面、技术面和估值模型")

# 主界面
if analyze_button and ticker:
    # 获取数据
    with st.spinner(f"正在获取 {ticker} 的数据..."):
        # 先尝试使用缓存版本
        try:
            data = fetch_stock_data(ticker)
        except:
            # 如果缓存失败，使用非缓存版本
            data = fetch_stock_data_uncached(ticker)
    
    if data:
        # 创建三列布局
        col1, col2, col3 = st.columns([1, 2, 1.5])
        
        # 左栏：公司基本信息
        with col1:
            st.subheader("📌 公司基本信息")
            info = data['info']
            
            # 公司信息卡片
            with st.container():
                st.metric("公司名称", info.get('longName', ticker))
                st.metric("当前股价", f"${info.get('currentPrice', 0):.2f}")
                st.metric("市值", f"${info.get('marketCap', 0)/1e9:.2f}B")
                st.metric("行业", info.get('industry', 'N/A'))
                st.metric("Beta", f"{info.get('beta', 0):.2f}")
                
                # 52周高低
                st.markdown("---")
                st.metric("52周最高", f"${info.get('fiftyTwoWeekHigh', 0):.2f}")
                st.metric("52周最低", f"${info.get('fiftyTwoWeekLow', 0):.2f}")
        
        # 中栏：分析结果
        with col2:
            st.subheader("📈 综合分析结果")
            
            # Piotroski F-Score
            with st.expander("🔍 Piotroski F-Score 分析", expanded=True):
                f_score, reasons = calculate_piotroski_score(data)
                
                # 评分展示
                score_color = "green" if f_score >= 7 else "orange" if f_score >= 4 else "red"
                st.markdown(f"### 得分: <span style='color:{score_color}; font-size:24px'>{f_score}/9</span>", unsafe_allow_html=True)
                
                # 评分解释
                for reason in reasons:
                    st.write(reason)
                
                # 建议
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
                    
                    # 评分标准说明
                    st.write("📊 评分标准:")
                    st.write("- Z > 2.99: 安全区域")
                    st.write("- 1.8 < Z < 2.99: 灰色区域")
                    st.write("- Z < 1.8: 危险区域")
            
            # 估值分析
            with st.expander("💎 估值分析", expanded=True):
                # DCF估值
                dcf_value = calculate_dcf_valuation(data)
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
                else:
                    st.info("DCF估值数据不足")
                
                # 相对估值
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
        
        # 右栏：图表和建议
        with col3:
            st.subheader("📉 技术分析与建议")
            
            # 技术指标
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
            
            # 投资建议卡片
            st.markdown("---")
            st.subheader("🎯 投资建议")
            
            # 综合评分
            total_score = 0
            
            # 基本面评分
            if f_score >= 7:
                total_score += 40
            elif f_score >= 4:
                total_score += 20
            else:
                total_score += 0
            
            # 估值评分
            if dcf_value and current_price > 0:
                margin = ((dcf_value - current_price) / dcf_value * 100)
                if margin > 20:
                    total_score += 30
                elif margin > 0:
                    total_score += 15
            
            # 技术面评分
            if not hist_data.empty and len(hist_data) > 60:
                latest_close = hist_data['Close'].iloc[-1]
                ma20 = hist_data['MA20'].iloc[-1] if 'MA20' in hist_data.columns and not pd.isna(hist_data['MA20'].iloc[-1]) else latest_close
                ma60 = hist_data['MA60'].iloc[-1] if 'MA60' in hist_data.columns and not pd.isna(hist_data['MA60'].iloc[-1]) else latest_close
                
                if latest_close > ma20 > ma60:
                    total_score += 30
                elif latest_close > ma20:
                    total_score += 15
            
            # 最终建议
            if total_score >= 70:
                st.success("🟢 **强烈买入**")
                st.write("基本面强劲，估值合理，技术面向好")
                win_prob = 0.65
            elif total_score >= 50:
                st.warning("🟡 **谨慎买入**")
                st.write("整体情况良好，但需注意风险")
                win_prob = 0.55
            elif total_score >= 30:
                st.info("🔵 **持有观望**")
                st.write("暂无明确信号，建议继续观察")
                win_prob = 0.50
            else:
                st.error("🔴 **卖出/回避**")
                st.write("风险较高，不建议买入")
                win_prob = 0.40
            
            # Kelly公式仓位建议
            win_loss_ratio = 2.0  # 假设盈亏比为2:1
            kelly_position = calculate_kelly_criterion(win_prob, win_loss_ratio)
            
            st.markdown("---")
            st.metric("推荐仓位", f"{kelly_position*100:.1f}%")
            st.caption("基于Kelly公式计算")
            
            # 风险等级
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

else:
    # 默认展示
    st.info("👈 请在左侧输入股票代码并点击分析按钮开始")
    
    # 使用说明
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
        
        ### 注意事项
        - 本系统仅供参考，不构成投资建议
        - 请结合其他信息进行综合判断
        - 投资有风险，入市需谨慎
        """)
    
    # 预留扩展功能
    with st.expander("🚀 未来功能规划"):
        st.markdown("""
        - [ ] A股市场支持（集成tushare）
        - [ ] 一键导出PDF分析报告
        - [ ] 多股票对比分析
        - [ ] 自定义分析模型参数
        - [ ] 实时数据推送提醒
        - [ ] AI智能投资助手
        - [ ] 投资组合优化建议
        """)

# 页脚
st.markdown("---")
st.markdown("💹 智能投资分析系统 v1.0 | 仅供参考，投资需谨慎")
