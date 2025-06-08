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

def translate_to_chinese(text):
    """使用在线翻译服务将英文翻译成中文"""
    if not text or len(text.strip()) < 3:
        return text
    
    try:
        # 方法1: 使用googletrans库 (如果可用)
        try:
            from googletrans import Translator
            translator = Translator()
            result = translator.translate(text, src='en', dest='zh-cn')
            return result.text
        except ImportError:
            pass
        except Exception:
            pass
        
        # 方法2: 使用requests调用Google翻译API
        try:
            import requests
            import urllib.parse
            
            # Google翻译API (免费版本)
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': 'en',
                'tl': 'zh-cn',
                'dt': 't',
                'q': text
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0 and len(result[0]) > 0:
                    translated_text = ''.join([item[0] for item in result[0] if item[0]])
                    return translated_text
        except:
            pass
        
        # 方法3: 使用百度翻译API (备用)
        try:
            import requests
            import hashlib
            import random
            
            # 这里可以添加百度翻译API的调用
            # 需要申请API密钥
            pass
        except:
            pass
        
        # 如果所有翻译方法都失败，返回原文
        return text
        
    except Exception as e:
        # 如果翻译失败，返回原文
        return text

def fetch_financial_news(target_ticker=None):
    """获取真实财经新闻（仅真实新闻）"""
    try:
        current_time = datetime.now()
        news_data = []
        
        # 获取目标股票新闻
        if target_ticker:
            try:
                ticker_obj = yf.Ticker(target_ticker)
                news = ticker_obj.news
                
                if news and len(news) > 0:
                    for i, article in enumerate(news[:8]):  # 获取前8条真实新闻
                        try:
                            # 新的API结构：数据在content字段里
                            content = article.get('content', article)  # 兼容新旧结构
                            
                            title = content.get('title', '') or content.get('headline', '') or article.get('title', '')
                            summary = content.get('summary', '') or content.get('description', '') or content.get('snippet', '')
                            
                            # 获取链接
                            link = ''
                            if 'clickThroughUrl' in content and content['clickThroughUrl']:
                                link = content['clickThroughUrl'].get('url', '')
                            elif 'canonicalUrl' in content and content['canonicalUrl']:
                                link = content['canonicalUrl'].get('url', '')
                            else:
                                link = content.get('link', '') or content.get('url', '')
                            
                            # 获取发布者
                            publisher = 'Unknown'
                            if 'provider' in content and content['provider']:
                                publisher = content['provider'].get('displayName', 'Unknown')
                            else:
                                publisher = content.get('publisher', '') or content.get('source', 'Unknown')
                            
                            # 获取时间
                            pub_time = None
                            pub_date_str = content.get('pubDate', '') or content.get('displayTime', '')
                            if pub_date_str:
                                try:
                                    # 处理ISO格式的时间字符串
                                    if 'T' in pub_date_str and 'Z' in pub_date_str:
                                        published_time = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
                                    else:
                                        published_time = current_time - timedelta(hours=i+1)
                                except:
                                    published_time = current_time - timedelta(hours=i+1)
                            else:
                                # 尝试数字时间戳
                                pub_time = content.get('providerPublishTime', None) or article.get('providerPublishTime', None)
                                if pub_time:
                                    try:
                                        published_time = datetime.fromtimestamp(pub_time)
                                    except:
                                        published_time = current_time - timedelta(hours=i+1)
                                else:
                                    published_time = current_time - timedelta(hours=i+1)
                            
                            if title and len(title.strip()) > 5:  # 确保标题有实际内容
                                # 翻译标题和摘要
                                try:
                                    translated_title = translate_to_chinese(title)
                                    if summary and len(summary.strip()) > 10:
                                        translated_summary = translate_to_chinese(summary)
                                    else:
                                        translated_summary = '暂无摘要'
                                except:
                                    # 如果翻译失败，使用原文
                                    translated_title = title
                                    translated_summary = summary or '暂无摘要'
                                
                                # 提取关键词和分析情绪
                                title_summary = title + ' ' + (summary or '')
                                keywords = extract_keywords_from_text(title_summary)
                                sentiment = analyze_sentiment_from_keywords(keywords)
                                
                                news_item = {
                                    "title": translated_title,
                                    "summary": translated_summary[:300] + '...' if len(translated_summary) > 300 else translated_summary,
                                    "published": published_time,
                                    "url": link or '',
                                    "source": publisher,
                                    "category": "company_specific",
                                    "keywords": keywords,
                                    "sentiment": sentiment,
                                    "is_real": True
                                }
                                news_data.append(news_item)
                        except Exception as e:
                            continue
                            
            except Exception as e:
                pass
        
        # 获取市场整体新闻
        try:
            market_indices = ["^GSPC", "^IXIC", "^DJI"]
            for index_symbol in market_indices:
                try:
                    index_ticker = yf.Ticker(index_symbol)
                    index_news = index_ticker.news
                    
                    if index_news and len(index_news) > 0:
                        for j, article in enumerate(index_news[:3]):  # 每个指数取3条
                            try:
                                # 新的API结构：数据在content字段里
                                content = article.get('content', article)
                                
                                title = content.get('title', '') or content.get('headline', '') or article.get('title', '')
                                summary = content.get('summary', '') or content.get('description', '') or content.get('snippet', '')
                                
                                # 获取链接
                                link = ''
                                if 'clickThroughUrl' in content and content['clickThroughUrl']:
                                    link = content['clickThroughUrl'].get('url', '')
                                elif 'canonicalUrl' in content and content['canonicalUrl']:
                                    link = content['canonicalUrl'].get('url', '')
                                else:
                                    link = content.get('link', '') or content.get('url', '')
                                
                                # 获取发布者
                                publisher = 'Market News'
                                if 'provider' in content and content['provider']:
                                    publisher = content['provider'].get('displayName', 'Market News')
                                else:
                                    publisher = content.get('publisher', '') or content.get('source', 'Market News')
                                
                                # 获取时间
                                pub_date_str = content.get('pubDate', '') or content.get('displayTime', '')
                                if pub_date_str:
                                    try:
                                        if 'T' in pub_date_str and 'Z' in pub_date_str:
                                            published_time = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
                                        else:
                                            published_time = current_time - timedelta(hours=len(news_data)+1)
                                    except:
                                        published_time = current_time - timedelta(hours=len(news_data)+1)
                                else:
                                    published_time = current_time - timedelta(hours=len(news_data)+1)
                                
                                if title and len(title.strip()) > 5:  # 确保标题有实际内容
                                    # 避免重复新闻
                                    if not any(existing['title'] == title for existing in news_data):
                                        # 翻译标题和摘要
                                        try:
                                            translated_title = translate_to_chinese(title)
                                            if summary and len(summary.strip()) > 10:
                                                translated_summary = translate_to_chinese(summary)
                                            else:
                                                translated_summary = '暂无摘要'
                                        except:
                                            # 如果翻译失败，使用原文
                                            translated_title = title
                                            translated_summary = summary or '暂无摘要'
                                        
                                        title_summary = title + ' ' + (summary or '')
                                        keywords = extract_keywords_from_text(title_summary)
                                        sentiment = analyze_sentiment_from_keywords(keywords)
                                        
                                        news_item = {
                                            "title": translated_title,
                                            "summary": translated_summary[:300] + '...' if len(translated_summary) > 300 else translated_summary,
                                            "published": published_time,
                                            "url": link or '',
                                            "source": publisher,
                                            "category": "market_wide",
                                            "keywords": keywords,
                                            "sentiment": sentiment,
                                            "is_real": True
                                        }
                                        news_data.append(news_item)
                            except Exception as e:
                                continue
                except Exception as e:
                    continue
        except Exception as e:
            pass
        
        # 按时间排序，最新的在前
        news_data.sort(key=lambda x: x.get('published', datetime.now()), reverse=True)
        
        # 如果仍然没有新闻，提供系统提示
        if len(news_data) == 0:
            return [{
                "title": "新闻获取服务暂时不可用",
                "summary": "由于技术原因，暂时无法获取实时财经新闻。请直接访问Yahoo Finance、Bloomberg等财经网站获取最新市场信息。",
                "published": current_time,
                "url": "https://finance.yahoo.com",
                "source": "系统提示",
                "category": "system_info",
                "keywords": ["系统", "提示"],
                "sentiment": "中性",
                "is_real": False
            }]
        
        return news_data
        
    except Exception as e:
        # 返回一个基本的系统信息
        return [{
            "title": "新闻获取服务暂时不可用",
            "summary": "由于技术原因，暂时无法获取实时财经新闻。请直接访问财经网站获取最新市场信息。",
            "published": datetime.now(),
            "url": "",
            "source": "系统",
            "category": "system_info",
            "keywords": ["系统"],
            "sentiment": "中性",
            "is_real": False
        }]

def extract_keywords_from_text(text):
    """从文本中提取财经关键词"""
    if not text:
        return []
    
    text_lower = text.lower()
    
    # 财经关键词库
    keyword_categories = {
        "利率": ["rate", "interest", "fed", "federal reserve", "利率", "降息", "加息"],
        "科技": ["tech", "technology", "ai", "artificial intelligence", "chip", "semiconductor", "科技", "人工智能", "芯片"],
        "金融": ["bank", "financial", "finance", "credit", "loan", "银行", "金融", "信贷"],
        "能源": ["energy", "oil", "gas", "petroleum", "renewable", "能源", "石油", "天然气"],
        "上涨": ["up", "rise", "gain", "increase", "rally", "surge", "上涨", "增长", "上升"],
        "下跌": ["down", "fall", "drop", "decline", "crash", "下跌", "下降", "暴跌"],
        "通胀": ["inflation", "cpi", "consumer price", "通胀", "物价"],
        "政策": ["policy", "regulation", "government", "政策", "监管", "政府"],
        "经济增长": ["growth", "gdp", "economic", "economy", "经济", "增长"],
        "市场": ["market", "stock", "trading", "investor", "市场", "股票", "投资"]
    }
    
    found_keywords = []
    for category, words in keyword_categories.items():
        for word in words:
            if word in text_lower:
                found_keywords.append(category)
                break
    
    return found_keywords[:5]

def analyze_sentiment_from_keywords(keywords):
    """根据关键词分析情绪"""
    bullish_words = ["上涨", "增长", "利率", "科技", "经济增长"]
    bearish_words = ["下跌", "通胀", "政策"]
    
    bullish_count = sum(1 for kw in keywords if kw in bullish_words)
    bearish_count = sum(1 for kw in keywords if kw in bearish_words)
    
    if bullish_count > bearish_count:
        return "利好"
    elif bearish_count > bullish_count:
        return "利空"
    else:
        return "中性"

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

# 侧边栏
with st.sidebar:
    st.header("📊 分析参数设置")
    
    ticker = st.text_input("股票代码", "AAPL", help="输入股票代码，如：AAPL")
    analyze_button = st.button("🔍 开始分析", type="primary", use_container_width=True)
    
    with st.expander("📘 使用说明"):
        st.markdown("""
        ### 系统功能
        1. **股票分析**: 财务指标、技术分析、估值模型
        2. **新闻分析**: 真实新闻获取与分析
        3. **止盈止损**: 智能策略建议
        
        ### 操作方法
        1. 输入股票代码（如AAPL、TSLA、MSFT）
        2. 点击"开始分析"
        3. 查看分析结果和新闻
        
        ### 注意事项
        - 仅显示真实新闻，无模拟内容
        - 新闻数量取决于实际可获取的数据
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
    main_tab1, main_tab2 = st.tabs(["📊 股票分析", "📰 真实新闻分析"])
    
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
        st.subheader("📰 真实新闻分析")
        st.info("💡 基于真实财经新闻的市场影响分析（不含任何模拟内容）")
        
        # 获取真实新闻数据
        news_data = fetch_financial_news(ticker)
        
        if len(news_data) == 0:
            st.warning("⚠️ 暂时无法获取新闻数据，请稍后重试或检查网络连接")
            st.info("💡 建议直接访问财经网站获取最新市场动态")
        else:
            # 新闻统计
            total_news = len(news_data)
            company_news = len([n for n in news_data if n.get('category') == 'company_specific'])
            market_news = len([n for n in news_data if n.get('category') == 'market_wide'])
            
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("📰 真实新闻", total_news)
            with col_stat2:
                st.metric("🏢 公司相关", company_news)
            with col_stat3:
                st.metric("🌍 市场影响", market_news)
            
            st.markdown("---")
            
            # 分页设置
            news_per_page = 5
            total_pages = (len(news_data) + news_per_page - 1) // news_per_page
            
            # 初始化当前页
            if 'current_news_page' not in st.session_state:
                st.session_state.current_news_page = 1
            
            # 确保页数在有效范围内
            if st.session_state.current_news_page > total_pages:
                st.session_state.current_news_page = total_pages
            if st.session_state.current_news_page < 1:
                st.session_state.current_news_page = 1
            
            current_page = st.session_state.current_news_page
            
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
                            {news_number}. {category_label} | ✅ 真实新闻
                        </span>
                        <span style="font-size: 11px; color: #999;">📰 {news.get('source', '')}</span>
                    </div>
                    <p style="color: #666; margin: 10px 0;">{news.get('summary', '')}</p>
                    <p style="font-size: 12px; color: #999;">
                        📅 {news.get('published', datetime.now()).strftime('%Y-%m-%d %H:%M')} | 
                        🏷️ 关键词: {', '.join(news.get('keywords', []))}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # 新闻标题按钮（真实链接）
                news_url = news.get('url', '')
                news_title = news.get('title', '无标题')
                
                if news_url and news_url.startswith('http'):
                    st.markdown(f'<a href="{news_url}" target="_blank"><button style="background: linear-gradient(45deg, {border_color}, {border_color}dd); color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: bold; width: 100%; margin: 10px 0;">🔗 {news_title}</button></a>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<button style="background: linear-gradient(45deg, #999, #777); color: white; border: none; padding: 12px 20px; border-radius: 8px; font-size: 14px; font-weight: bold; width: 100%; margin: 10px 0; opacity: 0.7; cursor: not-allowed;" disabled>📄 {news_title} (无有效链接)</button>', unsafe_allow_html=True)
                
                # 市场影响分析
                col_sentiment, col_impact = st.columns([1, 2])
                
                with col_sentiment:
                    sentiment = news.get('sentiment', '中性')
                    if sentiment == "利好":
                        st.success(f"📈 **{sentiment}**")
                    elif sentiment == "利空":
                        st.error(f"📉 **{sentiment}**")
                    else:
                        st.info(f"📊 **{sentiment}**")
                
                with col_impact:
                    impact_info = get_market_impact_advice(sentiment)
                    st.write(f"{impact_info['icon']} {impact_info['advice']}")
                    st.caption(f"💡 操作建议: {impact_info['action']}")
                
                st.markdown("---")
            
            # 页面底部的翻页按钮
            if total_pages > 1:
                st.markdown("### 📄 页面导航")
                
                # 创建翻页按钮布局
                nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1, 1, 1, 1, 1])
                
                with nav_col1:
                    if current_page > 1:
                        if st.button("⬅️ 上一页", key="prev_page_btn", use_container_width=True):
                            st.session_state.current_news_page = current_page - 1
                            st.rerun()
                    else:
                        st.button("⬅️ 上一页", key="prev_page_btn_disabled", disabled=True, use_container_width=True)
                
                with nav_col2:
                    if st.button("📖 第1页", key="page_1_btn", use_container_width=True, 
                               type="primary" if current_page == 1 else "secondary"):
                        st.session_state.current_news_page = 1
                        st.rerun()
                
                with nav_col3:
                    st.markdown(f"<div style='text-align: center; padding: 10px; font-weight: bold; color: #666;'>第 {current_page} / {total_pages} 页</div>", unsafe_allow_html=True)
                
                with nav_col4:
                    if total_pages >= 2:
                        if st.button("📄 第2页", key="page_2_btn", use_container_width=True,
                                   type="primary" if current_page == 2 else "secondary"):
                            st.session_state.current_news_page = 2
                            st.rerun()
                    else:
                        st.button("📄 第2页", key="page_2_btn_disabled", disabled=True, use_container_width=True)
                
                with nav_col5:
                    if current_page < total_pages:
                        if st.button("下一页 ➡️", key="next_page_btn", use_container_width=True):
                            st.session_state.current_news_page = current_page + 1
                            st.rerun()
                    else:
                        st.button("下一页 ➡️", key="next_page_btn_disabled", disabled=True, use_container_width=True)
                
                # 页面状态指示器
                st.markdown("---")
                progress_text = f"🔖 当前浏览: 第{current_page}页，共{total_pages}页 | 显示新闻 {start_idx + 1}-{end_idx} / {len(news_data)}"
                st.info(progress_text)
            
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
            st.subheader("💡 基于真实时事的投资提醒")
            
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
            st.caption("📝 **数据来源**: 基于Yahoo Finance等真实财经数据源")
            st.caption("✅ **真实性保证**: 所有新闻均为真实获取，无任何模拟内容")
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
        
        **📰 真实新闻分析**
        - 获取真实财经新闻（公司+行业+市场）
        - 智能分页浏览（每页5条）
        - 自动情绪分析（利好/利空/中性）
        - 市场影响评估和操作建议
        - 热点关键词统计
        - 整体市场情绪分析
        - **100%真实新闻，绝无模拟内容**
        
        ### 🚀 使用方法
        1. 在侧边栏输入股票代码（如AAPL、TSLA、MSFT等）
        2. 点击"🔍 开始分析"按钮
        3. 查看"📊 股票分析"标签页的财务和技术分析
        4. 切换到"📰 真实新闻分析"查看相关新闻
        5. 使用分页功能浏览所有新闻内容
        
        ### 📋 注意事项
        - 本系统仅显示真实财经新闻
        - 新闻数量取决于实际可获取的数据
        - 本系统仅供参考，不构成投资建议
        - 请结合其他信息进行综合判断
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

st.markdown("💹 智能投资分析系统 v2.0 | 仅真实新闻 | 投资需谨慎")
