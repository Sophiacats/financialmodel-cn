import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import re
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

def basic_translate(text):
    """基础中文翻译"""
    if not text:
        return text
    
    # 基础翻译词典
    translations = {
        'Apple': '苹果公司',
        'Tesla': '特斯拉',
        'Microsoft': '微软',
        'Amazon': '亚马逊',
        'Google': '谷歌',
        'Meta': 'Meta',
        'NVIDIA': '英伟达',
        'Netflix': '奈飞',
        'AAPL': '苹果(AAPL)',
        'TSLA': '特斯拉(TSLA)',
        'MSFT': '微软(MSFT)',
        'AMZN': '亚马逊(AMZN)',
        'GOOGL': '谷歌(GOOGL)',
        'META': 'Meta(META)',
        'NVDA': '英伟达(NVDA)',
        'NFLX': '奈飞(NFLX)',
        'earnings': '财报',
        'revenue': '营收',
        'profit': '利润',
        'shares': '股价',
        'stock': '股票',
        'market': '市场',
        'announced': '宣布',
        'reported': '报告',
        'billion': '十亿',
        'million': '百万',
        'AI': '人工智能',
        'technology': '科技',
        'growth': '增长'
    }
    
    result = text
    for en, zh in translations.items():
        result = re.sub(r'\b' + re.escape(en) + r'\b', zh, result, flags=re.IGNORECASE)
    
    return result

def fetch_financial_news(target_ticker=None):
    """获取财经新闻"""
    try:
        current_time = datetime.now()
        news_data = []
        
        # 获取目标股票新闻
        if target_ticker:
            try:
                ticker_obj = yf.Ticker(target_ticker)
                news = ticker_obj.news
                
                if news and len(news) > 0:
                    for i, article in enumerate(news[:5]):
                        try:
                            content = article.get('content', article)
                            
                            title = content.get('title', '') or article.get('title', '')
                            summary = content.get('summary', '') or content.get('description', '')
                            
                            # 获取链接
                            link = ''
                            if 'clickThroughUrl' in content and content['clickThroughUrl']:
                                link = content['clickThroughUrl'].get('url', '')
                            elif 'canonicalUrl' in content and content['canonicalUrl']:
                                link = content['canonicalUrl'].get('url', '')
                            
                            # 获取发布者
                            publisher = 'Unknown'
                            if 'provider' in content and content['provider']:
                                publisher = content['provider'].get('displayName', 'Unknown')
                            
                            # 获取时间
                            published_time = current_time - timedelta(hours=i+1)
                            pub_date_str = content.get('pubDate', '')
                            if pub_date_str:
                                try:
                                    if 'T' in pub_date_str and 'Z' in pub_date_str:
                                        published_time = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
                                except:
                                    pass
                            
                            if title and len(title.strip()) > 5:
                                # 翻译标题和摘要
                                translated_title = basic_translate(title)
                                translated_summary = basic_translate(summary) if summary else '暂无摘要'
                                
                                news_item = {
                                    "title": translated_title,
                                    "summary": translated_summary[:200] + '...' if len(translated_summary) > 200 else translated_summary,
                                    "published": published_time,
                                    "url": link or '',
                                    "source": publisher,
                                    "category": "company_specific",
                                    "keywords": ["科技", "市场"],
                                    "sentiment": "中性",
                                    "is_real": True
                                }
                                news_data.append(news_item)
                        except:
                            continue
            except:
                pass
        
        # 如果没有新闻，提供系统提示
        if len(news_data) == 0:
            return [{
                "title": "新闻获取服务暂时不可用",
                "summary": "由于技术原因，暂时无法获取实时财经新闻。请直接访问Yahoo Finance等财经网站获取最新市场信息。",
                "published": current_time,
                "url": "https://finance.yahoo.com",
                "source": "系统提示",
                "category": "system_info",
                "keywords": ["系统"],
                "sentiment": "中性",
                "is_real": False
            }]
        
        return news_data
        
    except Exception as e:
        return [{
            "title": "新闻获取服务出现错误",
            "summary": "无法获取新闻数据，请稍后重试。",
            "published": datetime.now(),
            "url": "",
            "source": "系统",
            "category": "system_info",
            "keywords": ["系统"],
            "sentiment": "中性",
            "is_real": False
        }]

def calculate_technical_indicators(hist_data):
    """计算技术指标"""
    try:
        hist_data['MA10'] = hist_data['Close'].rolling(window=10).mean()
        hist_data['MA20'] = hist_data['Close'].rolling(window=20).mean()
        hist_data['MA60'] = hist_data['Close'].rolling(window=60).mean()
        
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

# 侧边栏
with st.sidebar:
    st.header("📊 分析参数设置")
    
    ticker = st.text_input("股票代码", "AAPL", help="输入股票代码，如：AAPL")
    analyze_button = st.button("🔍 开始分析", type="primary", use_container_width=True)
    
    with st.expander("📘 使用说明"):
        st.markdown("""
        ### 系统功能
        1. **股票分析**: 财务指标、技术分析、估值模型
        2. **新闻分析**: 中文新闻翻译与分析
        3. **止盈止损**: 智能策略建议
        
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
                    st.info("DCF估值数据不足")
        
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
            
            # 止盈止损计算
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
        st.info("💡 自动翻译最新财经新闻为中文")
        
        # 获取新闻数据
        with st.spinner("正在获取和翻译新闻..."):
            news_data = fetch_financial_news(ticker)
        
        if len(news_data) == 0:
            st.warning("⚠️ 暂时无法获取新闻数据，请稍后重试")
        else:
            # 新闻统计
            total_news = len(news_data)
            real_news = len([n for n in news_data if n.get('is_real', True)])
            
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("📰 新闻总数", total_news)
            with col_stat2:
                st.metric("✅ 真实新闻", real_news)
            with col_stat3:
                st.metric("🔄 已翻译", total_news)
            
            st.markdown("---")
            
            # 显示新闻
            for i, news in enumerate(news_data):
                news_number = i + 1
                is_real = news.get('is_real', True)
                real_label = "✅ 真实新闻" if is_real else "📝 系统信息"
                
                st.markdown(f"""
                <div style="border: 2px solid #4CAF50; border-radius: 10px; padding: 15px; margin: 10px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="background-color: #4CAF50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">
                            {news_number}. {real_label}
                        </span>
                        <span style="font-size: 11px; color: #999;">📰 {news.get('source', '')}</span>
                    </div>
                    <p style="color: #666; margin: 10px 0;">{news.get('summary', '')}</p>
                    <p style="font-size: 12px; color: #999;">
                        📅 {news.get('published', datetime.now()).strftime('%Y-%m-%d %H:%M')}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # 新闻标题按钮
                news_url = news.get('url', '')
                news_title = news.get('title', '无标题')
                
                if news_url and news_url.startswith('http'):
                    st.markdown(f'<a href="{news_url}" target="_blank"><button style="background: #4CAF50; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: bold; width: 100%; margin: 10px 0;">🔗 {news_title}</button></a>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<button style="background: #999; color: white; border: none; padding: 12px 20px; border-radius: 8px; font-size: 14px; font-weight: bold; width: 100%; margin: 10px 0; opacity: 0.7;" disabled>📄 {news_title}</button>', unsafe_allow_html=True)
                
                st.markdown("---")
            
            st.markdown("### 📊 新闻来源说明")
            st.caption("📝 **数据来源**: Yahoo Finance等真实财经数据源")
            st.caption("🌐 **翻译服务**: 基础财经词汇翻译")
            st.caption("⚠️ **免责声明**: 所有分析仅供参考，不构成投资建议。")

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
        
        **📰 最新时事分析**
        - 自动获取真实财经新闻
        - 基础中文翻译功能
        - 新闻来源和时间显示
        
        ### 🚀 使用方法
        1. 在侧边栏输入股票代码（如AAPL、TSLA、MSFT等）
        2. 点击"🔍 开始分析"按钮
        3. 查看"📊 股票分析"标签页的财务和技术分析
        4. 切换到"📰 最新时事分析"查看翻译后的新闻
        
        ### 📋 注意事项
        - 新闻自动翻译关键财经词汇为中文
        - 本系统仅供参考，不构成投资建议
        - 投资有风险，入市需谨慎
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

st.markdown("💹 智能投资分析系统 v2.0 | 基础中文翻译 | 投资需谨慎")
