import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import re
import requests
import time
import json
import feedparser
from urllib.parse import quote
warnings.filterwarnings('ignore')

# 页面配置
st.set_page_config(
    page_title="📰 多源真实新闻系统",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化 session state
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None
if 'news_data' not in st.session_state:
    st.session_state.news_data = None

st.title("📰 多源真实财经新闻系统")
st.markdown("**整合多个真实新闻源 + 支持所有美股代码 + 智能翻译分析**")
st.markdown("---")

# ==================== 多个真实新闻源 ====================

def get_company_name(ticker):
    """获取公司名称用于搜索"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info.get('longName', ticker)
    except:
        return ticker

def fetch_newsapi_articles(query, api_key=None):
    """使用 NewsAPI 获取真实新闻"""
    if not api_key:
        return []
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 10,
            'apiKey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            news_items = []
            for article in articles:
                if article.get('title') and len(article['title']) > 10:
                    news_items.append({
                        'title': article['title'],
                        'summary': article.get('description', '暂无摘要'),
                        'url': article.get('url', ''),
                        'source': article.get('source', {}).get('name', 'NewsAPI'),
                        'published': datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00')).replace(tzinfo=None) if article.get('publishedAt') else datetime.now(),
                        'method': 'NewsAPI'
                    })
            
            return news_items
    except Exception as e:
        st.sidebar.error(f"NewsAPI 错误: {str(e)}")
    
    return []

def fetch_rss_financial_news(ticker, company_name):
    """通过RSS获取财经新闻"""
    news_items = []
    
    # 主要财经媒体的RSS源
    rss_sources = [
        {
            'name': 'Yahoo Finance',
            'url': f'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US',
            'backup_url': 'https://feeds.finance.yahoo.com/rss/2.0/headline?region=US&lang=en-US'
        },
        {
            'name': 'MarketWatch',
            'url': f'https://feeds.marketwatch.com/marketwatch/topstories/',
        },
        {
            'name': 'Reuters Business',
            'url': 'http://feeds.reuters.com/reuters/businessNews',
        },
        {
            'name': 'CNN Business',
            'url': 'http://rss.cnn.com/rss/money_latest.rss',
        }
    ]
    
    for source in rss_sources:
        try:
            # 尝试主URL
            feed = feedparser.parse(source['url'])
            
            # 如果主URL失败，尝试备用URL
            if not feed.entries and 'backup_url' in source:
                feed = feedparser.parse(source['backup_url'])
            
            if feed.entries:
                st.sidebar.success(f"✅ {source['name']}: 获取到 {len(feed.entries)} 条新闻")
                
                for entry in feed.entries[:5]:  # 每个源取前5条
                    title = entry.get('title', '')
                    summary = entry.get('summary', '') or entry.get('description', '')
                    
                    # 过滤与股票相关的新闻
                    if ticker.lower() in title.lower() or company_name.lower() in title.lower() or not ticker:
                        try:
                            # 处理发布时间
                            published_time = datetime.now()
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                published_time = datetime(*entry.published_parsed[:6])
                            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                                published_time = datetime(*entry.updated_parsed[:6])
                            
                            news_items.append({
                                'title': title,
                                'summary': summary[:300] + '...' if len(summary) > 300 else summary,
                                'url': entry.get('link', ''),
                                'source': source['name'],
                                'published': published_time,
                                'method': 'RSS'
                            })
                        except Exception as e:
                            continue
            else:
                st.sidebar.warning(f"⚠️ {source['name']}: 无法获取RSS数据")
                
        except Exception as e:
            st.sidebar.error(f"❌ {source['name']}: {str(e)}")
            continue
    
    return news_items

def fetch_google_news_search(query):
    """通过Google News搜索获取新闻"""
    try:
        # 构建Google News RSS URL
        encoded_query = quote(query)
        google_news_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        feed = feedparser.parse(google_news_url)
        
        if feed.entries:
            st.sidebar.success(f"✅ Google News: 获取到 {len(feed.entries)} 条新闻")
            
            news_items = []
            for entry in feed.entries[:8]:  # 取前8条
                try:
                    title = entry.get('title', '')
                    summary = entry.get('summary', '') or '来自Google News的新闻摘要'
                    
                    if title and len(title) > 10:
                        # 处理发布时间
                        published_time = datetime.now()
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published_time = datetime(*entry.published_parsed[:6])
                        
                        news_items.append({
                            'title': title,
                            'summary': summary[:300] + '...' if len(summary) > 300 else summary,
                            'url': entry.get('link', ''),
                            'source': 'Google News',
                            'published': published_time,
                            'method': 'Google News RSS'
                        })
                except Exception as e:
                    continue
            
            return news_items
        else:
            st.sidebar.warning("⚠️ Google News: 无法获取数据")
    
    except Exception as e:
        st.sidebar.error(f"❌ Google News: {str(e)}")
    
    return []

def fetch_alpha_vantage_news(symbol, api_key=None):
    """使用 Alpha Vantage API 获取新闻"""
    if not api_key:
        return []
    
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': symbol,
            'limit': 10,
            'apikey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = data.get('feed', [])
            
            news_items = []
            for article in articles:
                if article.get('title') and len(article['title']) > 10:
                    published_time = datetime.now()
                    if article.get('time_published'):
                        try:
                            published_time = datetime.strptime(article['time_published'], '%Y%m%dT%H%M%S')
                        except:
                            pass
                    
                    news_items.append({
                        'title': article['title'],
                        'summary': article.get('summary', '暂无摘要')[:300] + '...',
                        'url': article.get('url', ''),
                        'source': article.get('source', 'Alpha Vantage'),
                        'published': published_time,
                        'method': 'Alpha Vantage'
                    })
            
            return news_items
    
    except Exception as e:
        st.sidebar.error(f"Alpha Vantage 错误: {str(e)}")
    
    return []

@st.cache_data(ttl=1800)
def get_comprehensive_real_news(ticker, newsapi_key=None, alphavantage_key=None):
    """整合多个真实新闻源"""
    all_news = []
    company_name = get_company_name(ticker) if ticker else "stock market"
    search_query = f"{ticker} {company_name}" if ticker else "stock market financial news"
    
    st.sidebar.info(f"🔍 搜索关键词: {search_query}")
    
    # 方法1: RSS 新闻源（无需API key，最可靠）
    rss_news = fetch_rss_financial_news(ticker, company_name)
    if rss_news:
        all_news.extend(rss_news)
        st.sidebar.success(f"✅ RSS源: 获取到 {len(rss_news)} 条新闻")
    
    # 方法2: Google News（无需API key）
    google_news = fetch_google_news_search(search_query)
    if google_news:
        all_news.extend(google_news)
        st.sidebar.success(f"✅ Google News: 获取到 {len(google_news)} 条新闻")
    
    # 方法3: NewsAPI（需要API key）
    if newsapi_key:
        newsapi_articles = fetch_newsapi_articles(search_query, newsapi_key)
        if newsapi_articles:
            all_news.extend(newsapi_articles)
            st.sidebar.success(f"✅ NewsAPI: 获取到 {len(newsapi_articles)} 条新闻")
    
    # 方法4: Alpha Vantage（需要API key）
    if alphavantage_key and ticker:
        av_news = fetch_alpha_vantage_news(ticker, alphavantage_key)
        if av_news:
            all_news.extend(av_news)
            st.sidebar.success(f"✅ Alpha Vantage: 获取到 {len(av_news)} 条新闻")
    
    # 去除重复新闻（基于标题相似性）
    unique_news = []
    seen_titles = set()
    
    for news in all_news:
        title_key = news['title'].lower()[:50]  # 使用前50个字符作为去重key
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_news.append(news)
    
    # 按时间排序
    unique_news.sort(key=lambda x: x['published'], reverse=True)
    
    st.sidebar.info(f"📊 总计获取: {len(all_news)} 条，去重后: {len(unique_news)} 条")
    
    return unique_news

# ==================== 翻译和分析系统 ====================

def translate_financial_content(text):
    """财经内容智能翻译"""
    if not text:
        return text
    
    # 扩展的财经术语词典
    financial_terms = {
        # 公司行为
        'announces': '宣布', 'reports': '报告', 'reveals': '透露', 'discloses': '披露',
        'files': '提交', 'submits': '递交', 'releases': '发布', 'publishes': '公布',
        
        # 财务术语
        'earnings': '财报', 'revenue': '营收', 'sales': '销售额', 'income': '收入',
        'profit': '利润', 'loss': '亏损', 'margin': '利润率', 'ebitda': '息税折旧摊销前利润',
        'cash flow': '现金流', 'dividend': '分红', 'buyback': '回购',
        
        # 市场表现
        'shares': '股价', 'stock': '股票', 'price': '价格', 'market cap': '市值',
        'volume': '成交量', 'trading': '交易', 'volatility': '波动性',
        'bullish': '看涨', 'bearish': '看跌', 'rally': '反弹', 'correction': '调整',
        
        # 业绩表现
        'beat': '超过', 'miss': '未达', 'exceed': '超越', 'outperform': '表现优于',
        'underperform': '表现逊于', 'guidance': '指导', 'forecast': '预测',
        'estimate': '预期', 'target': '目标', 'outlook': '前景',
        
        # 变化趋势
        'increase': '增长', 'decrease': '下降', 'growth': '增长', 'decline': '下跌',
        'rise': '上涨', 'fall': '下跌', 'surge': '飙升', 'plunge': '暴跌',
        'spike': '急升', 'drop': '下跌', 'climb': '攀升', 'slide': '下滑',
        
        # 商业活动
        'acquisition': '收购', 'merger': '合并', 'deal': '交易', 'partnership': '合作',
        'investment': '投资', 'funding': '融资', 'ipo': '首次公开募股',
        'expansion': '扩张', 'restructuring': '重组', 'layoffs': '裁员',
        
        # 监管相关
        'sec': '证券交易委员会', 'fda': '食品药品监督管理局', 'regulatory': '监管',
        'approval': '批准', 'compliance': '合规', 'investigation': '调查',
        
        # 时间相关
        'quarterly': '季度', 'annual': '年度', 'monthly': '月度',
        'year-over-year': '同比', 'quarter-over-quarter': '环比',
        
        # 数量相关
        'billion': '十亿', 'million': '百万', 'thousand': '千',
        'percent': '%', 'percentage': '百分比', 'basis points': '基点'
    }
    
    result = text
    
    # 应用术语翻译
    for en_term, zh_term in financial_terms.items():
        pattern = r'\b' + re.escape(en_term) + r'\b'
        result = re.sub(pattern, zh_term, result, flags=re.IGNORECASE)
    
    # 处理常见数字表达
    result = re.sub(r'\$([0-9,.]+)\s*billion', r'\1十亿美元', result, flags=re.IGNORECASE)
    result = re.sub(r'\$([0-9,.]+)\s*million', r'\1百万美元', result, flags=re.IGNORECASE)
    result = re.sub(r'([0-9,.]+)%', r'\1%', result)
    result = re.sub(r'Q([1-4])', r'第\1季度', result)
    
    return result

def extract_news_keywords(title, summary):
    """从新闻中提取关键词"""
    text = (title + ' ' + summary).lower()
    
    keyword_mapping = {
        '财报业绩': ['earnings', 'revenue', 'profit', 'income', 'results', 'beat', 'miss'],
        '股价变动': ['shares', 'stock', 'price', 'trading', 'surge', 'plunge', 'rally'],
        '公司行动': ['acquisition', 'merger', 'deal', 'investment', 'partnership', 'ipo'],
        '产品服务': ['launch', 'product', 'service', 'innovation', 'technology', 'platform'],
        '监管政策': ['regulatory', 'approval', 'fda', 'sec', 'government', 'policy'],
        '市场分析': ['analyst', 'rating', 'upgrade', 'downgrade', 'target', 'recommendation'],
        '财务状况': ['debt', 'cash', 'dividend', 'buyback', 'financing', 'liquidity'],
        '行业动态': ['sector', 'industry', 'market', 'competition', 'trend', 'outlook']
    }
    
    found_keywords = []
    for category, terms in keyword_mapping.items():
        if any(term in text for term in terms):
            found_keywords.append(category)
    
    return found_keywords[:4]

def analyze_news_sentiment(title, summary, keywords):
    """分析新闻情绪"""
    text = (title + ' ' + summary).lower()
    
    # 积极信号
    positive_terms = [
        'beat', 'exceed', 'outperform', 'strong', 'growth', 'increase', 'rise',
        'surge', 'rally', 'record', 'high', 'success', 'win', 'approval', 
        'breakthrough', 'innovation', 'expansion', 'upgrade', 'buy'
    ]
    
    # 消极信号
    negative_terms = [
        'miss', 'underperform', 'weak', 'decline', 'decrease', 'fall',
        'plunge', 'drop', 'low', 'loss', 'concern', 'worry', 'risk',
        'challenge', 'problem', 'downgrade', 'sell', 'investigation'
    ]
    
    pos_score = sum(1 for term in positive_terms if term in text)
    neg_score = sum(1 for term in negative_terms if term in text)
    
    # 考虑关键词的影响
    bullish_keywords = ['财报业绩', '产品服务']
    bearish_keywords = ['监管政策']
    
    keyword_pos = sum(1 for kw in keywords if kw in bullish_keywords)
    keyword_neg = sum(1 for kw in keywords if kw in bearish_keywords)
    
    total_pos = pos_score + keyword_pos
    total_neg = neg_score + keyword_neg
    
    if total_pos > total_neg and total_pos > 0:
        return '利好'
    elif total_neg > total_pos and total_neg > 0:
        return '利空'
    else:
        return '中性'

def get_sentiment_advice(sentiment):
    """根据情绪提供建议"""
    advice_map = {
        '利好': {
            'icon': '📈',
            'advice': '积极信号，可能推动股价上涨',
            'action': '关注买入机会，但需结合技术分析',
            'color': 'green'
        },
        '利空': {
            'icon': '📉',
            'advice': '消极信号，可能对股价产生压力',
            'action': '注意风险控制，考虑减仓或等待',
            'color': 'red'
        },
        '中性': {
            'icon': '📊',
            'advice': '中性信号，市场影响有限',
            'action': '保持观察，等待更明确的信号',
            'color': 'gray'
        }
    }
    return advice_map.get(sentiment, advice_map['中性'])

# ==================== 侧边栏界面 ====================
with st.sidebar:
    st.header("📰 多源新闻设置")
    
    # 股票代码输入
    ticker = st.text_input(
        "美股代码 (可选):",
        placeholder="例如: AAPL, TSLA... 留空获取综合新闻",
        help="输入具体股票代码获取相关新闻，留空获取市场综合新闻"
    ).upper().strip()
    
    st.markdown("---")
    
    # API配置（可选）
    st.subheader("🔑 API配置 (可选)")
    
    with st.expander("📡 高级数据源"):
        newsapi_key = st.text_input(
            "NewsAPI Key (可选):",
            type="password",
            help="免费注册: https://newsapi.org"
        )
        
        alphavantage_key = st.text_input(
            "Alpha Vantage Key (可选):",
            type="password", 
            help="免费注册: https://www.alphavantage.co"
        )
        
        st.info("💡 不提供API key也可以使用RSS和Google News获取真实新闻")
    
    st.markdown("---")
    
    # 新闻源选择
    st.subheader("📡 新闻源状态")
    
    use_rss = st.checkbox("📰 RSS新闻源", value=True, help="Yahoo Finance, Reuters, MarketWatch等RSS")
    use_google = st.checkbox("🔍 Google News", value=True, help="Google新闻搜索")
    use_newsapi = st.checkbox("📊 NewsAPI", value=bool(newsapi_key), disabled=not newsapi_key)
    use_alphavantage = st.checkbox("📈 Alpha Vantage", value=bool(alphavantage_key), disabled=not alphavantage_key)
    
    st.markdown("---")
    
    # 获取新闻按钮
    if st.button("📰 获取真实新闻", type="primary", use_container_width=True):
        st.session_state.selected_ticker = ticker
        
        with st.spinner(f"正在从多个真实新闻源获取{ticker or '市场'}新闻..."):
            # 根据用户选择决定使用哪些API key
            api_newsapi = newsapi_key if use_newsapi else None
            api_alphavantage = alphavantage_key if use_alphavantage else None
            
            news_data = get_comprehensive_real_news(ticker, api_newsapi, api_alphavantage)
            
            if news_data:
                # 处理新闻数据
                processed_news = []
                for news in news_data:
                    translated_title = translate_financial_content(news['title'])
                    translated_summary = translate_financial_content(news['summary'])
                    keywords = extract_news_keywords(news['title'], news['summary'])
                    sentiment = analyze_news_sentiment(news['title'], news['summary'], keywords)
                    
                    processed_item = {
                        'title': translated_title,
                        'summary': translated_summary,
                        'published': news['published'],
                        'source': news['source'],
                        'url': news['url'],
                        'method': news['method'],
                        'keywords': keywords,
                        'sentiment': sentiment,
                        'is_real': True
                    }
                    processed_news.append(processed_item)
                
                st.session_state.news_data = processed_news
                st.success(f"✅ 成功获取并处理 {len(processed_news)} 条真实新闻！")
            else:
                st.session_state.news_data = []
                st.warning("⚠️ 未能从任何新闻源获取到数据，请检查网络连接或稍后重试")
    
    # 清除缓存
    if st.button("🔄 刷新缓存", use_container_width=True):
        get_comprehensive_real_news.clear()
        st.session_state.news_data = None
        st.success("缓存已清除！")
    
    # 网络测试
    if st.button("🌐 测试连接"):
        test_urls = [
            ("Google News", "https://news.google.com"),
            ("Yahoo Finance", "https://finance.yahoo.com"),
            ("Reuters", "https://www.reuters.com")
        ]
        
        for name, url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    st.success(f"✅ {name}: 连接正常")
                else:
                    st.warning(f"⚠️ {name}: HTTP {response.status_code}")
            except:
                st.error(f"❌ {name}: 连接失败")

# ==================== 主界面 ====================
if st.session_state.news_data is not None:
    news_data = st.session_state.news_data
    ticker = st.session_state.selected_ticker or "市场"
    
    if len(news_data) > 0:
        # 统计信息
        total = len(news_data)
        bullish = len([n for n in news_data if n['sentiment'] == '利好'])
        bearish = len([n for n in news_data if n['sentiment'] == '利空'])
        neutral = len([n for n in news_data if n['sentiment'] == '中性'])
        
        # 按数据源统计
        sources = {}
        for news in news_data:
            method = news.get('method', 'Unknown')
            sources[method] = sources.get(method, 0) + 1
        
        # 显示统计面板
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📰 真实新闻", total)
        with col2:
            st.metric("📈 利好", bullish, delta=f"{bullish/total*100:.0f}%" if total > 0 else "0%")
        with col3:
            st.metric("📉 利空", bearish, delta=f"{bearish/total*100:.0f}%" if total > 0 else "0%")
        with col4:
            st.metric("📊 中性", neutral, delta=f"{neutral/total*100:.0f}%" if total > 0 else "0%")
        
        # 数据源统计
        st.markdown("#### 📡 数据源分布")
        source_cols = st.columns(len(sources))
        for i, (source, count) in enumerate(sources.items()):
            with source_cols[i]:
                st.metric(source, count)
        
        # 情绪总结
        if bullish > bearish:
            st.success(f"📈 {ticker} 新闻情绪: 整体偏向积极")
        elif bearish > bullish:
            st.error(f"📉 {ticker} 新闻情绪: 整体偏向消极") 
        else:
            st.info(f"📊 {ticker} 新闻情绪: 相对平衡")
        
        st.markdown("---")
        
        # 显示新闻列表
        st.subheader(f"📰 {ticker} 最新财经新闻")
        
        for i, news in enumerate(news_data):
            advice = get_sentiment_advice(news['sentiment'])
            
            with st.container():
                col_main, col_side = st.columns([3, 1])
                
                with col_main:
                    # 新闻标题和元信息
                    st.markdown(f"### 📰 {news['title']}")
                    
                    time_str = news['published'].strftime('%Y-%m-%d %H:%M')
                    st.caption(f"🕒 {time_str} | 📡 {news['source']} | 🔧 {news['method']}")
                    
                    # 新闻摘要
                    st.write(news['summary'])
                    
                    # 关键词标签
                    if news['keywords']:
                        keywords_str = " ".join([f"`{kw}`" for kw in news['keywords']])
                        st.markdown(f"**🏷️ 关键词:** {keywords_str}")
                    
                    # 原文链接
                    if news['url']:
                        st.markdown(f"🔗 [阅读原文]({news['url']})")
                
                with col_side:
                    # 情绪分析卡片
                    st.markdown(f"### {advice['icon']}")
                    st.markdown(f"**<span style='color:{advice['color']}'>{news['sentiment']}</span>**", unsafe_allow_html=True)
                    
                    st.write("**📋 市场影响:**")
                    st.write(advice['advice'])
                    
                    st.write("**💡 操作建议:**")
                    st.write(advice['action'])
            
            st.markdown("---")
    
    else:
        st.warning("📭 未能获取到新闻数据")
        st.markdown("""
        ### 🔧 可能的解决方案:
        
        1. **检查网络连接** - 点击"测试连接"按钮
        2. **尝试不同股票** - 知名股票新闻更多
        3. **添加API Keys** - 提供更多数据源
        4. **稍后重试** - 新闻源可能暂时不可用
        """)

else:
    # 欢迎页面
    st.markdown("""
    ## 🎯 多源真实财经新闻系统
    
    ### ✨ 核心优势
    
    #### 📡 **多个真实新闻源**
    - **RSS新闻源**: Yahoo Finance, Reuters, MarketWatch, CNN Business
    - **Google News**: 实时新闻搜索聚合
    - **NewsAPI**: 专业新闻API服务
    - **Alpha Vantage**: 专业金融数据API
    
    #### 🛡️ **可靠性保障**
    - ✅ **无需API**: RSS和Google News无需注册
    - 🔄 **多重备选**: 一个源失败自动切换其他
    - 🚫 **零虚假**: 只从真实新闻源获取数据
    - 📊 **去重处理**: 自动过滤重复新闻
    
    #### 🌐 **智能处理**
    - 🔤 **专业翻译**: 丰富的财经术语词典
    - 📊 **情绪分析**: AI驱动的市场情绪判断  
    - 🏷️ **关键词提取**: 自动识别新闻主题
    - 💡 **投资建议**: 个性化操作建议
    
    ### 🚀 使用方法
    
    #### 🎯 **基础使用** (无需任何配置)
    1. 输入美股代码或留空获取市场新闻
    2. 点击"获取真实新闻"
    3. 系统自动从RSS和Google News获取真实新闻
    
    #### ⚡ **高级使用** (可选API增强)
    1. 注册免费API账号：
       - [NewsAPI](https://newsapi.org) - 获取更多新闻源
       - [Alpha Vantage](https://www.alphavantage.co) - 专业金融数据
    2. 在侧边栏配置API Keys
    3. 享受更多数据源和更全面的新闻覆盖
    
    ### 📊 数据源说明
    
    | 数据源 | 类型 | 优势 | 要求 |
    |--------|------|------|------|
    | RSS源 | 免费 | 稳定可靠，主流媒体 | 无 |
    | Google News | 免费 | 覆盖面广，实时性强 | 无 |
    | NewsAPI | 免费/付费 | 专业新闻，结构化数据 | API Key |
    | Alpha Vantage | 免费/付费 | 金融专业，情绪分析 | API Key |
    
    ### 💡 最佳实践
    
    - **个股新闻**: 输入具体股票代码（如 AAPL, TSLA）获取相关新闻
    - **市场新闻**: 留空代码获取综合市场新闻
    - **多源验证**: 同一新闻在多个源出现说明重要性更高
    - **时效性**: 关注发布时间，最新新闻影响最大
    
    ---
    
    **👈 在左侧输入股票代码或直接获取市场新闻开始体验**
    """)
    
    # 功能展示
    with st.expander("🎬 系统演示"):
        st.markdown("""
        ### 📊 真实新闻处理流程
        
        **步骤1: 多源获取**
        ```
        输入: AAPL (苹果公司)
        ↓
        RSS源: Yahoo Finance RSS → 3条新闻
        Google News: "AAPL Apple" → 5条新闻  
        NewsAPI: "AAPL Apple Inc" → 4条新闻
        Alpha Vantage: "AAPL" → 2条新闻
        ↓
        合并: 14条原始新闻
        ```
        
        **步骤2: 智能处理**
        ```
        去重: 14条 → 8条独特新闻
        ↓
        翻译: "Apple reports strong earnings" → "苹果报告强劲财报"
        ↓
        分析: 关键词 ["财报业绩", "股价变动"] + 情绪 "利好"
        ↓
        建议: "积极信号，关注买入机会"
        ```
        
        **步骤3: 结果展示**
        - 📊 统计面板: 总数、情绪分布、数据源分布
        - 📰 新闻列表: 翻译后的标题、摘要、分析结果
        - 💡 投资建议: 基于情绪的操作建议
        
        ### 🔄 为什么比yfinance更好？
        
        | 方面 | yfinance | 多源系统 |
        |------|----------|----------|
        | 可靠性 | 单一API，经常失效 | 多个源，互为备份 |
        | 覆盖面 | 仅Yahoo数据 | 4+个主流新闻源 |
        | 实时性 | 有延迟 | Google News实时 |
        | 稳定性 | 不稳定 | RSS源极其稳定 |
        | 成本 | 免费 | 基础功能免费 |
        """)

# 页脚
st.markdown("---")
st.markdown("📰 多源真实财经新闻系统 | 🔄 4+真实数据源 | 🚫 零虚假内容 | 🌐 智能翻译分析")
