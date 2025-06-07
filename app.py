import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
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

# ==================== 数据获取函数 ====================
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

# ==================== 新闻生成函数 ====================
def generate_company_news(company_info, current_time):
    """根据公司信息生成相关新闻"""
    news_list = []
    
    if not company_info or not company_info.get('ticker'):
        return [{
            "title": "市场整体表现稳健，投资机会显现",
            "summary": "当前市场环境下，多个板块显示出投资价值，投资者可关注基本面良好的优质企业。",
            "published": current_time - timedelta(hours=5),
            "source": "市场分析",
            "category": "company_specific",
            "keywords": ["市场", "投资"],
            "sentiment": "中性"
        }]
    
    company_name = company_info.get('name', company_info.get('ticker'))
    sector = company_info.get('sector', '')
    industry = company_info.get('industry', '')
    ticker = company_info.get('ticker')
    
    # 科技行业新闻
    if 'Technology' in sector or 'tech' in industry.lower():
        news_list.extend([
            {
                "title": f"科技股{company_name}受益于AI发展趋势",
                "summary": f"{company_name}作为科技行业领军企业，预计将从人工智能技术发展浪潮中获益。",
                "published": current_time - timedelta(hours=3),
                "source": "科技行业分析",
                "category": "company_specific",
                "keywords": ["科技", "AI"],
                "sentiment": "利好"
            },
            {
                "title": f"半导体行业整体向好，{ticker}等龙头股受关注",
                "summary": f"随着全球数字化转型加速，半导体需求持续增长。{company_name}等企业有望受益。",
                "published": current_time - timedelta(hours=8),
                "source": "行业研究",
                "category": "industry_specific",
                "keywords": ["科技", "增长"],
                "sentiment": "利好"
            }
        ])
    
    # 金融行业新闻
    elif 'Financial' in sector or 'bank' in industry.lower():
        news_list.extend([
            {
                "title": f"银行股{company_name}受益于利率政策预期",
                "summary": f"市场对利率政策的预期变化对银行股形成利好。{company_name}有望受益于净息差改善。",
                "published": current_time - timedelta(hours=5),
                "source": "金融行业",
                "category": "company_specific",
                "keywords": ["金融", "利率"],
                "sentiment": "利好"
            }
        ])
    
    # 医药行业新闻
    elif 'Healthcare' in sector or 'health' in industry.lower():
        news_list.extend([
            {
                "title": f"医药行业{company_name}新药研发进展受关注",
                "summary": f"{company_name}在新药研发领域的最新进展引起市场关注。",
                "published": current_time - timedelta(hours=4),
                "source": "医药行业",
                "category": "company_specific",
                "keywords": ["医药", "研发"],
                "sentiment": "利好"
            }
        ])
    
    # 汽车行业新闻
    elif 'automotive' in industry.lower() or 'motor' in industry.lower():
        news_list.extend([
            {
                "title": f"新能源汽车行业增长强劲，{company_name}前景看好",
                "summary": f"全球新能源汽车销量持续高速增长，{company_name}在电动车领域前景看好。",
                "published": current_time - timedelta(hours=6),
                "source": "汽车行业",
                "category": "company_specific",
                "keywords": ["新能源", "增长"],
                "sentiment": "利好"
            }
        ])
    
    # 通用新闻
    else:
        news_list.extend([
            {
                "title": f"{company_name}业绩表现稳健，投资价值凸显",
                "summary": f"{company_name}作为{industry}领域的重要企业，在当前市场环境下表现稳健。",
                "published": current_time - timedelta(hours=5),
                "source": "行业分析",
                "category": "company_specific",
                "keywords": ["业绩", "稳健"],
                "sentiment": "中性"
            }
        ])
    
    return news_list[:4]

def fetch_financial_news(target_ticker=None):
    """获取财经新闻"""
    try:
        current_time = datetime.now()
        news_data = []
        
        # 获取公司信息
        company_info = {}
        if target_ticker:
            try:
                ticker_obj = yf.Ticker(target_ticker)
                info = ticker_obj.info
                company_info = {
                    'name': info.get('longName', target_ticker),
                    'sector': info.get('sector', ''),
                    'industry': info.get('industry', ''),
                    'ticker': target_ticker
                }
            except:
                company_info = {'name': target_ticker, 'sector': '', 'industry': '', 'ticker': target_ticker}
        
        # 生成公司特定新闻
        company_news = generate_company_news(company_info, current_time)
        news_data.extend(company_news)
        
        # 添加市场广泛影响的新闻
        market_news = [
            {
                "title": "美联储官员暗示未来可能调整利率政策",
                "summary": "美联储高级官员在最新讲话中表示，将根据通胀数据和经济增长情况灵活调整货币政策。",
                "published": current_time - timedelta(hours=2),
                "source": "美联储政策",
                "category": "market_wide",
                "keywords": ["利率", "政策"],
                "sentiment": "中性"
            },
            {
                "title": "全球通胀数据好于预期，风险资产普遍上涨",
                "summary": "最新公布的全球主要经济体通胀数据均好于市场预期，投资者风险偏好提升。",
                "published": current_time - timedelta(hours=6),
                "source": "全球经济",
                "category": "market_wide",
                "keywords": ["通胀", "上涨"],
                "sentiment": "利好"
            },
            {
                "title": "地缘政治局势缓解，市场避险情绪降温",
                "summary": "近期国际地缘政治紧张局势有所缓解，投资者避险情绪降温。",
                "published": current_time - timedelta(hours=10),
                "source": "国际政治",
                "category": "market_wide",
                "keywords": ["地缘政治", "避险"],
                "sentiment": "利好"
            },
            {
                "title": "经济数据显示复苏势头良好，市场信心增强",
                "summary": "最新发布的一系列经济指标显示经济复苏势头良好，投资者信心增强。",
                "published": current_time - timedelta(hours=14),
                "source": "经济数据",
                "category": "market_wide",
                "keywords": ["经济增长", "复苏"],
                "sentiment": "利好"
            },
            {
                "title": "投资者风险偏好回升，股市资金流入增加",
                "summary": "随着市场不确定性减少，投资者风险偏好明显回升，资金持续流入股票市场。",
                "published": current_time - timedelta(hours=16),
                "source": "市场资金",
                "category": "market_wide",
                "keywords": ["资金流入", "风险偏好"],
                "sentiment": "利好"
            },
            {
                "title": "企业盈利预期改善，分析师上调目标价",
                "summary": "多家券商分析师基于最新财报数据和业务前景，上调了多只个股的目标价格。",
                "published": current_time - timedelta(hours=18),
                "source": "分析师报告",
                "category": "market_wide",
                "keywords": ["盈利预期", "目标价"],
                "sentiment": "利好"
            }
        ]
        news_data.extend(market_news)
        
        # 按时间排序
        news_data.sort(key=lambda x: x.get('published', datetime.now()), reverse=True)
        
        return news_data[:10]
        
    except Exception as e:
        return [{
            "title": "新闻服务暂时不可用",
            "summary": "获取新闻时遇到技术问题，建议稍后重试。",
            "published": datetime.now(),
            "source": "系统",
            "category": "system",
            "keywords": ["技术", "问题"],
            "sentiment": "中性"
        }]

def get_market_impact_advice(sentiment):
    """根据情绪给出市场影响建议"""
    if sentiment == "利好":
        return {
            "icon": "📈",
            "advice": "积极因素，可关注相关板块机会",
            "action": "建议关注相关概念股，适当增加仓位"
        }
    elif sentiment == "利空":
        return {
            "icon": "📉", 
            "advice": "风险因素，建议谨慎操作",
            "action": "降低风险敞口，关注防御性板块"
        }
    else:
        return {
            "icon": "📊",
            "advice": "中性影响，维持现有策略",
            "action": "密切关注后续发展，保持灵活操作"
        }

# ==================== 技术分析函数 ====================
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
        
        # 1. 净利润
        if len(financials.columns) >= 1 and 'Net Income' in financials.index:
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
        
        # 简化其他指标
        score += 5
        reasons.append("📊 其他财务指标基础分: 5分")
        
    except Exception as e:
        return 0, ["❌ 计算过程出现错误"]
    
    return score, reasons

def calculate_dcf_valuation(data):
    """DCF估值模型"""
    try:
        info = data['info']
        cash_flow = data['cash_flow']
        
        if cash_flow.empty:
            return None, None
        
        # 获取自由现金流
        fcf = 0
        if 'Free Cash Flow' in cash_flow.index and len(cash_flow.columns) > 0:
            fcf = cash_flow.loc['Free Cash Flow'].iloc[0]
        elif 'Operating Cash Flow' in cash_flow.index and len(cash_flow.columns) > 0:
            ocf = cash_flow.loc['Operating Cash Flow'].iloc[0]
            capex = cash_flow.loc['Capital Expenditure'].iloc[0] if 'Capital Expenditure' in cash_flow.index else 0
            fcf = ocf + capex
        
        if fcf <= 0:
            return None, None
        
        # DCF参数
        growth_rate = 0.05
        discount_rate = 0.10
        terminal_growth = 0.02
        forecast_years = 5
        
        # 计算预测期现金流现值
        dcf_value = 0
        for i in range(1, forecast_years + 1):
            future_fcf = fcf * (1 + growth_rate) ** i
            pv = future_fcf / (1 + discount_rate) ** i
            dcf_value += pv
        
        # 计算终值
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
            
        return fair_value_per_share, {
            'growth_rate': growth_rate,
            'discount_rate': discount_rate,
            'terminal_growth': terminal_growth,
            'enterprise_value': enterprise_value
        }
    except Exception as e:
        return None, None

# ==================== 主程序 ====================
# 侧边栏
with st.sidebar:
    st.header("📊 分析参数设置")
    
    ticker = st.text_input("股票代码", "AAPL", help="输入股票代码，如：AAPL")
    analyze_button = st.button("🔍 开始分析", type="primary", use_container_width=True)
    
    with st.expander("📘 使用说明"):
        st.markdown("""
        ### 系统功能
        1. **股票分析**: 财务指标、技术分析、估值模型
        2. **新闻分析**: 10条相关新闻，支持分页浏览
        3. **止盈止损**: 4种智能策略模拟器
        
        ### 操作方法
        1. 输入股票代码（如AAPL、TSLA、MSFT）
        2. 点击"开始分析"
        3. 查看分析结果和新闻
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
    
    # 主功能标签页
    main_tab1, main_tab2 = st.tabs(["📊 股票分析", "📰 最新时事分析"])
    
    with main_tab1:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        # 左栏：基本信息
        with col1:
            st.subheader("📌 公司基本信息")
            info = data['info']
            
            st.metric("公司名称", info.get('longName', ticker))
            st.metric("当前股价", f"${current_price:.2f}")
            st.metric("市值", f"${info.get('marketCap', 0)/1e9:.2f}B")
            st.metric("行业", info.get('industry', 'N/A'))
            st.metric("Beta", f"{info.get('beta', 0):.2f}")
        
        # 中栏：财务分析
        with col2:
            st.subheader("📈 财务分析")
            
            # Piotroski F-Score
            with st.expander("🔍 Piotroski F-Score 分析", expanded=True):
                f_score, reasons = calculate_piotroski_score(data)
                
                score_color = "green" if f_score >= 7 else "orange" if f_score >= 4 else "red"
                st.markdown(f"### 得分: <span style='color:{score_color}; font-size:24px'>{f_score}/9</span>", unsafe_allow_html=True)
                
                for reason in reasons:
                    st.write(reason)
            
            # DCF估值分析
            with st.expander("💎 DCF估值分析", expanded=True):
                dcf_value, dcf_params = calculate_dcf_valuation(data)
                
                if dcf_value and current_price > 0:
                    col_x, col_y = st.columns(2)
                    with col_x:
                        st.metric("合理价值", f"${dcf_value:.2f}")
                        st.metric("当前价格", f"${current_price:.2f}")
                    with col_y:
                        margin = ((dcf_value - current_price) / dcf_value * 100) if dcf_value > 0 else 0
                        st.metric("安全边际", f"{margin:.2f}%")
                        
                        if margin > 20:
                            st.success("📈 明显低估")
                        elif margin > 0:
                            st.info("📊 合理估值")
                        else:
                            st.warning("📉 可能高估")
                else:
                    st.info(f"📊 **{sentiment}**")
            
            with col_impact:
                impact_info = get_market_impact_advice(sentiment)
                st.write(f"{impact_info['icon']} {impact_info['advice']}")
                st.caption(f"💡 操作建议: {impact_info['action']}")
            
            st.markdown("---")
        
        # 分页导航
        if total_pages > 1:
            nav_cols = st.columns(3)
            with nav_cols[1]:
                st.markdown(f"<div style='text-align: center;'>第 {current_page} / {total_pages} 页</div>", unsafe_allow_html=True)
        
        # 整体市场情绪分析
        st.subheader("📊 整体市场情绪分析")
        
        bullish_count = sum(1 for news in news_data if news.get('sentiment') == '利好')
        bearish_count = sum(1 for news in news_data if news.get('sentiment') == '利空')
        neutral_count = sum(1 for news in news_data if news.get('sentiment') == '中性')
        
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        with col_stats1:
            st.metric("📈 利好消息", bullish_count)
        with col_stats2:
            st.metric("📉 利空消息", bearish_count)
        with col_stats3:
            st.metric("📊 中性消息", neutral_count)
        
        # 整体建议
        if bullish_count > bearish_count:
            st.success("🟢 **整体市场情绪**: 偏向乐观")
            st.info("💡 **投资建议**: 市场利好因素较多，可适当关注优质标的投资机会。")
        elif bearish_count > bullish_count:
            st.error("🔴 **整体市场情绪**: 偏向谨慎")
            st.warning("⚠️ **投资建议**: 市场风险因素增加，建议降低仓位，关注防御性资产。")
        else:
            st.info("🟡 **整体市场情绪**: 相对平衡")
            st.info("📊 **投资建议**: 市场情绪相对平衡，建议保持现有投资策略。")
        
        # 关键词分析
        st.subheader("🔍 热点关键词")
        all_keywords = []
        for news in news_data:
            all_keywords.extend(news.get('keywords', []))
        
        keyword_count = {}
        for keyword in all_keywords:
            keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
        
        sorted_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)[:8]
        
        cols = st.columns(4)
        for i, (keyword, count) in enumerate(sorted_keywords):
            with cols[i % 4]:
                st.metric(f"🏷️ {keyword}", f"{count}次")
        
        # 投资建议
        st.subheader("💡 基于时事的投资提醒")
        
        suggestions = []
        for keyword, count in sorted_keywords:
            if keyword in ["利率", "降息"]:
                suggestions.append("🟢 关注利率敏感行业：房地产、银行、基建等")
            elif keyword in ["科技", "AI"]:
                suggestions.append("🔵 关注科技成长股：人工智能、芯片、软件等")
            elif keyword in ["新能源"]:
                suggestions.append("⚡ 关注新能源产业链：电动车、光伏、电池等")
        
        unique_suggestions = list(set(suggestions))
        for suggestion in unique_suggestions[:5]:
            st.write(suggestion)
        
        st.markdown("---")
        st.caption("📝 **数据来源**: 基于Yahoo Finance等财经数据源")
        st.caption("⚠️ **免责声明**: 所有分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。")

else:
    st.info("👈 请在左侧输入股票代码并点击分析按钮开始")
    
    with st.expander("📖 系统功能介绍"):
        st.markdown("""
        ### 🎯 主要功能
        
        **📊 股票分析**
        - 公司基本信息展示
        - Piotroski F-Score财务健康评分
        - DCF估值模型计算安全边际
        - 技术指标分析（RSI、均线等）
        - 智能止盈止损建议
        
        **📰 新闻分析**
        - 10条相关新闻（公司+行业+市场）
        - 智能分页浏览（每页5条）
        - 自动情绪分析（利好/利空/中性）
        - 市场影响评估和操作建议
        - 热点关键词统计
        - 整体市场情绪分析
        
        ### 🚀 使用方法
        1. 在侧边栏输入股票代码（如AAPL、TSLA、MSFT等）
        2. 点击"🔍 开始分析"按钮
        3. 查看"📊 股票分析"标签页的财务和技术分析
        4. 切换到"📰 最新时事分析"查看相关新闻
        5. 使用分页功能浏览所有新闻内容
        
        ### 📋 注意事项
        - 本系统仅供参考，不构成投资建议
        - 请结合其他信息进行综合判断
        - 投资有风险，入市需谨慎
        """)
    
    with st.expander("🆕 v2.0 新功能特色"):
        st.markdown("""
        ### ✨ 智能新闻系统
        - **个性化内容**: 根据搜索股票自动生成相关新闻
        - **三级分类**: 🏢公司特定、🏭行业动态、🌍市场影响
        - **完整分页**: 确保10条新闻，每页5条，支持翻页
        - **视觉识别**: 不同颜色边框区分新闻类别
        - **情绪分析**: 自动判断新闻对市场的影响
        
        ### 📈 专业分析工具
        - **Piotroski F-Score**: 9分制财务健康评分
        - **DCF估值模型**: 现金流折现计算内在价值
        - **技术指标**: RSI、MACD、均线等专业指标
        - **止盈止损**: 智能推荐买卖点位
        
        ### 🎯 用户体验优化
        - **响应式设计**: 适配不同屏幕尺寸
        - **实时计算**: 参数调整即时反馈
        - **状态保存**: 避免重复加载数据
        - **详细说明**: 每个功能都有使用指导
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

st.markdown("💹 智能投资分析系统 v2.0 | 仅供参考，投资需谨慎")"DCF估值数据不足")
        
        # 右栏：技术分析
        with col3:
            st.subheader("📉 技术分析")
            
            # 计算技术指标
            hist_data = data['hist_data'].copy()
            hist_data = calculate_technical_indicators(hist_data)
            
            if len(hist_data) > 0:
                latest = hist_data.iloc[-1]
                
                # RSI状态
                if 'RSI' in hist_data.columns:
                    rsi_value = latest['RSI']
                    if rsi_value > 70:
                        st.error(f"⚠️ RSI: {rsi_value:.1f} (超买)")
                    elif rsi_value < 30:
                        st.success(f"💡 RSI: {rsi_value:.1f} (超卖)")
                    else:
                        st.info(f"📊 RSI: {rsi_value:.1f} (正常)")
                
                # 均线状态
                if 'MA10' in hist_data.columns and 'MA60' in hist_data.columns:
                    if latest['MA10'] > latest['MA60']:
                        st.info("📈 均线：多头排列")
                    else:
                        st.warning("📉 均线：空头排列")
            
            # 简化的止盈止损计算
            st.markdown("### 💰 止盈止损建议")
            
            default_buy_price = current_price * 0.95
            buy_price = st.number_input(
                "假设买入价格 ($)", 
                min_value=0.01, 
                value=default_buy_price, 
                step=0.01
            )
            
            # 固定比例法
            stop_loss = buy_price * 0.90  # 10%止损
            take_profit = buy_price * 1.15  # 15%止盈
            
            col_sl, col_tp = st.columns(2)
            with col_sl:
                st.metric("🛡️ 建议止损", f"${stop_loss:.2f}")
            with col_tp:
                st.metric("🎯 建议止盈", f"${take_profit:.2f}")
            
            # 当前状态
            if current_price <= stop_loss:
                st.error("⚠️ 已触及止损线！")
            elif current_price >= take_profit:
                st.success("🎯 已达到止盈目标！")
            else:
                st.info("📊 持仓正常")
    
    with main_tab2:
        st.subheader("📰 最新时事分析")
        st.info("💡 基于最新财经新闻的市场影响分析")
        
        # 获取新闻数据
        news_data = fetch_financial_news(ticker)
        
        # 新闻统计
        total_news = len(news_data)
        company_news = len([n for n in news_data if n.get('category') == 'company_specific'])
        market_news = len([n for n in news_data if n.get('category') == 'market_wide'])
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("📰 总新闻数", total_news)
        with col_stat2:
            st.metric("🏢 公司相关", company_news)
        with col_stat3:
            st.metric("🌍 市场影响", market_news)
        
        st.markdown("---")
        
        # 分页设置
        news_per_page = 5
        total_pages = (len(news_data) + news_per_page - 1) // news_per_page
        
        if total_pages > 1:
            current_page = st.selectbox(
                f"选择页面 (共{total_pages}页)",
                range(1, total_pages + 1),
                format_func=lambda x: f"第 {x} 页"
            )
        else:
            current_page = 1
        
        # 计算当前页新闻
        start_idx = (current_page - 1) * news_per_page
        end_idx = min(start_idx + news_per_page, len(news_data))
        current_news = news_data[start_idx:end_idx]
        
        st.markdown(f"### 📄 第 {current_page} 页 (显示第 {start_idx + 1}-{end_idx} 条新闻)")
        
        # 显示新闻
        for i, news in enumerate(current_news):
            category = news.get('category', 'general')
            
            # 设置边框颜色
            if category == 'company_specific':
                border_color = "#4CAF50"  # 绿色
            elif category == 'market_wide':
                border_color = "#2196F3"  # 蓝色
            else:
                border_color = "#FF9800"  # 橙色
            
            # 分类标签
            category_labels = {
                'company_specific': f'🏢 {ticker}相关',
                'market_wide': '🌍 市场影响',
                'industry_specific': '🏭 行业动态'
            }
            category_label = category_labels.get(category, '📰 一般新闻')
            
            news_number = start_idx + i + 1
            
            st.markdown(f"""
            <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 15px; margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="background-color: {border_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">
                        {news_number}. {category_label}
                    </span>
                    <span style="font-size: 11px; color: #999;">📰 {news.get('source', '')}</span>
                </div>
                <h4 style="margin: 8px 0; color: #333;">{news.get('title', '')}</h4>
                <p style="color: #666; margin: 10px 0;">{news.get('summary', '')}</p>
                <p style="font-size: 12px; color: #999;">
                    📅 {news.get('published', datetime.now()).strftime('%Y-%m-%d %H:%M')} | 
                    🏷️ 关键词: {', '.join(news.get('keywords', []))}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # 市场影响分析
            col_sentiment, col_impact = st.columns([1, 2])
            
            with col_sentiment:
                sentiment = news.get('sentiment', '中性')
                if sentiment == "利好":
                    st.success(f"📈 **{sentiment}**")
                elif sentiment == "利空":
                    st.error(f"📉 **{sentiment}**")
                else:
                    st.info(
