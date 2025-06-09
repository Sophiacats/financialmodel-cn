import streamlit as st
import yfinance as yf
import requests
import feedparser
from datetime import datetime, timedelta
import re
from urllib.parse import quote
import warnings
warnings.filterwarnings('ignore')

# 页面配置
st.set_page_config(
    page_title="📰 多源新闻集成系统",
    page_icon="📰",
    layout="wide"
)

st.title("📰 多源新闻集成系统")
st.markdown("**整合多个真实新闻源 + 去重 + 实时更新**")
st.markdown("---")

# 初始化 session state
if 'news_data' not in st.session_state:
    st.session_state.news_data = None
if 'source_stats' not in st.session_state:
    st.session_state.source_stats = {}

# ==================== 新闻源1: yfinance ====================
def fetch_yfinance_news(ticker, debug=False):
    """yfinance新闻获取（已验证有效）"""
    try:
        stock = yf.Ticker(ticker)
        raw_news = stock.news
        
        if not raw_news:
            return []
        
        processed_news = []
        for i, article in enumerate(raw_news):
            try:
                if not isinstance(article, dict):
                    continue
                
                # 处理新的API结构
                content_data = article.get('content', article)
                
                # 提取标题
                title = ''
                title_sources = [
                    content_data.get('title', ''),
                    content_data.get('headline', ''),
                    article.get('title', ''),
                ]
                
                for t in title_sources:
                    if t and len(str(t).strip()) > 10:
                        title = str(t).strip()
                        break
                
                if not title:
                    continue
                
                # 提取摘要
                summary = ''
                summary_sources = [
                    content_data.get('summary', ''),
                    content_data.get('description', ''),
                    article.get('summary', ''),
                ]
                
                for s in summary_sources:
                    if s and len(str(s).strip()) > 10:
                        summary = str(s).strip()
                        break
                
                # 提取URL
                url = ''
                url_sources = [
                    content_data.get('clickThroughUrl', {}).get('url', '') if isinstance(content_data.get('clickThroughUrl'), dict) else content_data.get('clickThroughUrl', ''),
                    content_data.get('link', ''),
                    article.get('link', ''),
                ]
                
                for u in url_sources:
                    if u and isinstance(u, str) and len(u) > 10:
                        url = u
                        break
                
                # 提取时间
                published_time = datetime.now() - timedelta(hours=i+1)
                time_sources = [
                    content_data.get('providerPublishTime'),
                    article.get('providerPublishTime'),
                ]
                
                for time_val in time_sources:
                    if time_val:
                        try:
                            published_time = datetime.fromtimestamp(time_val)
                            break
                        except:
                            continue
                
                processed_news.append({
                    'title': title,
                    'summary': summary or '暂无摘要',
                    'url': url,
                    'source': 'Yahoo Finance',
                    'published': published_time,
                    'method': 'yfinance'
                })
                
            except Exception as e:
                if debug:
                    st.error(f"yfinance处理第{i+1}条新闻失败: {str(e)}")
                continue
        
        return processed_news
        
    except Exception as e:
        if debug:
            st.error(f"yfinance获取失败: {str(e)}")
        return []

# ==================== 新闻源2: RSS源 ====================
def fetch_rss_news(ticker=None, debug=False):
    """RSS新闻源获取"""
    rss_sources = [
        {
            'name': 'Reuters Business',
            'url': 'http://feeds.reuters.com/reuters/businessNews',
            'encoding': 'utf-8'
        },
        {
            'name': 'MarketWatch',
            'url': 'https://feeds.marketwatch.com/marketwatch/topstories/',
            'encoding': 'utf-8'
        },
        {
            'name': 'CNN Business',
            'url': 'http://rss.cnn.com/rss/money_latest.rss',
            'encoding': 'utf-8'
        }
    ]
    
    all_rss_news = []
    
    for source in rss_sources:
        try:
            if debug:
                st.write(f"🔍 获取 {source['name']} RSS...")
            
            feed = feedparser.parse(source['url'])
            
            if not feed.entries:
                if debug:
                    st.warning(f"⚠️ {source['name']}: 无数据")
                continue
            
            source_news = []
            for entry in feed.entries[:5]:  # 每个源取5条
                try:
                    title = entry.get('title', '')
                    summary = entry.get('summary', '') or entry.get('description', '')
                    link = entry.get('link', '')
                    
                    # 如果指定了股票代码，过滤相关新闻
                    if ticker:
                        title_summary = (title + ' ' + summary).lower()
                        if ticker.lower() not in title_summary:
                            continue
                    
                    # 处理发布时间
                    published_time = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            published_time = datetime(*entry.published_parsed[:6])
                        except:
                            pass
                    
                    if title and len(title) > 10:
                        source_news.append({
                            'title': title,
                            'summary': summary[:300] + '...' if len(summary) > 300 else summary,
                            'url': link,
                            'source': source['name'],
                            'published': published_time,
                            'method': 'RSS'
                        })
                        
                except Exception as e:
                    continue
            
            all_rss_news.extend(source_news)
            
            if debug:
                st.success(f"✅ {source['name']}: 获取 {len(source_news)} 条新闻")
                
        except Exception as e:
            if debug:
                st.error(f"❌ {source['name']}: {str(e)}")
            continue
    
    return all_rss_news

# ==================== 新闻源3: Google News ====================
def fetch_google_news(query, debug=False):
    """Google News RSS获取"""
    try:
        if debug:
            st.write(f"🔍 获取Google News: {query}")
        
        encoded_query = quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        feed = feedparser.parse(url)
        
        if not feed.entries:
            if debug:
                st.warning("⚠️ Google News: 无数据")
            return []
        
        google_news = []
        for entry in feed.entries[:8]:  # 取8条
            try:
                title = entry.get('title', '')
                summary = entry.get('summary', '') or '来自Google News'
                link = entry.get('link', '')
                
                # 处理发布时间
                published_time = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published_time = datetime(*entry.published_parsed[:6])
                    except:
                        pass
                
                if title and len(title) > 10:
                    google_news.append({
                        'title': title,
                        'summary': summary[:300] + '...' if len(summary) > 300 else summary,
                        'url': link,
                        'source': 'Google News',
                        'published': published_time,
                        'method': 'Google RSS'
                    })
                    
            except Exception as e:
                continue
        
        if debug:
            st.success(f"✅ Google News: 获取 {len(google_news)} 条新闻")
        
        return google_news
        
    except Exception as e:
        if debug:
            st.error(f"❌ Google News: {str(e)}")
        return []

# ==================== 新闻整合和去重 ====================
def remove_duplicate_news(news_list):
    """去除重复新闻"""
    seen_titles = set()
    unique_news = []
    
    for news in news_list:
        # 使用标题的前60个字符作为去重标识
        title_key = news['title'][:60].lower().strip()
        
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_news.append(news)
    
    return unique_news

@st.cache_data(ttl=900)  # 15分钟缓存
def get_comprehensive_news(ticker=None, debug=False):
    """获取所有来源的新闻并整合"""
    all_news = []
    source_stats = {}
    
    # 来源1: yfinance（如果有ticker）
    if ticker:
        yf_news = fetch_yfinance_news(ticker, debug)
        all_news.extend(yf_news)
        source_stats['yfinance'] = len(yf_news)
    
    # 来源2: RSS新闻源
    rss_news = fetch_rss_news(ticker, debug)
    all_news.extend(rss_news)
    source_stats['RSS'] = len(rss_news)
    
    # 来源3: Google News
    if ticker:
        google_query = f"{ticker} stock news"
    else:
        google_query = "stock market financial news"
    
    google_news = fetch_google_news(google_query, debug)
    all_news.extend(google_news)
    source_stats['Google News'] = len(google_news)
    
    # 去重
    unique_news = remove_duplicate_news(all_news)
    
    # 按时间排序
    unique_news.sort(key=lambda x: x['published'], reverse=True)
    
    # 统计信息
    total_before = len(all_news)
    total_after = len(unique_news)
    removed = total_before - total_after
    
    if debug:
        st.info(f"📊 总获取: {total_before} 条，去重后: {total_after} 条，移除重复: {removed} 条")
    
    return unique_news, source_stats

# ==================== 翻译和分析 ====================
def translate_finance_terms(text):
    """基础财经术语翻译"""
    if not text:
        return text
    
    terms = {
        'earnings': '财报', 'revenue': '营收', 'profit': '利润',
        'stock': '股票', 'shares': '股价', 'market': '市场',
        'announced': '宣布', 'reported': '报告', 'increased': '增长',
        'decreased': '下降', 'beat': '超过', 'missed': '未达到'
    }
    
    result = text
    for en, zh in terms.items():
        result = re.sub(r'\b' + re.escape(en) + r'\b', zh, result, flags=re.IGNORECASE)
    
    return result

def analyze_sentiment(title, summary):
    """简单情绪分析"""
    text = (title + ' ' + summary).lower()
    
    positive = ['beat', 'strong', 'growth', 'increase', 'rise', 'gain', 'success']
    negative = ['miss', 'weak', 'decline', 'fall', 'drop', 'loss', 'concern']
    
    pos_count = sum(1 for word in positive if word in text)
    neg_count = sum(1 for word in negative if word in text)
    
    if pos_count > neg_count:
        return '利好'
    elif neg_count > pos_count:
        return '利空'
    else:
        return '中性'

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("📰 多源新闻设置")
    
    ticker = st.text_input(
        "股票代码 (可选):",
        placeholder="例如: AAPL, TSLA...",
        help="输入具体代码获取相关新闻，留空获取市场综合新闻"
    ).upper().strip()
    
    st.markdown("---")
    
    debug_mode = st.checkbox("🔧 调试模式", help="显示详细获取过程")
    show_source = st.checkbox("📡 显示数据源", value=True, help="显示每条新闻的来源")
    
    st.markdown("---")
    
    if st.button("📰 获取多源新闻", type="primary"):
        with st.spinner("正在从多个真实新闻源获取数据..."):
            news_data, stats = get_comprehensive_news(ticker, debug_mode)
            st.session_state.news_data = news_data
            st.session_state.source_stats = stats
    
    if st.button("🔄 清除缓存"):
        get_comprehensive_news.clear()
        st.session_state.news_data = None
        st.session_state.source_stats = {}
        st.success("缓存已清除")

# ==================== 主界面 ====================
if st.session_state.news_data is not None:
    news_data = st.session_state.news_data
    source_stats = st.session_state.source_stats
    
    if len(news_data) > 0:
        # 数据源统计
        st.subheader("📊 数据源统计")
        
        cols = st.columns(len(source_stats) + 1)
        
        total_raw = sum(source_stats.values())
        with cols[0]:
            st.metric("总计", f"{len(news_data)} 条", f"原始: {total_raw}")
        
        for i, (source, count) in enumerate(source_stats.items(), 1):
            with cols[i]:
                st.metric(source, f"{count} 条")
        
        # 情绪分析统计
        sentiments = {}
        for news in news_data:
            sentiment = analyze_sentiment(news['title'], news['summary'])
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
        
        if sentiments:
            st.subheader("📈 市场情绪分析")
            sentiment_cols = st.columns(3)
            
            colors = {'利好': 'green', '利空': 'red', '中性': 'gray'}
            for i, (sentiment, count) in enumerate(sentiments.items()):
                with sentiment_cols[i % 3]:
                    pct = count / len(news_data) * 100
                    st.metric(sentiment, count, f"{pct:.0f}%")
        
        st.markdown("---")
        
        # 新闻列表
        st.subheader(f"📰 {ticker or '市场'} 最新新闻 ({len(news_data)} 条)")
        
        for i, news in enumerate(news_data):
            with st.container():
                # 标题
                title_display = news['title']
                if show_source:
                    title_display += f" [{news['source']}]"
                
                st.markdown(f"### {i+1}. {title_display}")
                
                # 元信息
                time_str = news['published'].strftime('%Y-%m-%d %H:%M')
                method_info = f" | 方法: {news['method']}" if show_source else ""
                st.caption(f"🕒 {time_str} | 📡 {news['source']}{method_info}")
                
                # 内容
                col_main, col_side = st.columns([3, 1])
                
                with col_main:
                    # 显示摘要（带基础翻译）
                    translated_summary = translate_finance_terms(news['summary'])
                    st.write(translated_summary)
                    
                    if news['url']:
                        st.markdown(f"🔗 [阅读原文]({news['url']})")
                
                with col_side:
                    # 情绪分析
                    sentiment = analyze_sentiment(news['title'], news['summary'])
                    color_map = {'利好': 'green', '利空': 'red', '中性': 'gray'}
                    st.markdown(f"**情绪:** <span style='color:{color_map[sentiment]}'>{sentiment}</span>", unsafe_allow_html=True)
                
                st.markdown("---")
    
    else:
        st.warning("📭 未获取到新闻数据")
        if st.session_state.source_stats:
            st.write("数据源尝试结果:")
            for source, count in st.session_state.source_stats.items():
                st.write(f"- {source}: {count} 条")

else:
    st.markdown("""
    ## 🎯 多源新闻集成系统
    
    ### 📡 **整合多个真实新闻源**
    
    #### 🥇 **主要源 - yfinance**
    - ✅ **高质量**: 直接相关的财经新闻
    - ✅ **结构化**: 数据完整，包含链接
    - ✅ **实时性**: 更新及时
    - ⚠️ **局限性**: 仅Yahoo Finance视角
    
    #### 🥈 **补充源 - RSS**
    - 📰 **Reuters**: 权威国际财经新闻
    - 📊 **MarketWatch**: 专业市场分析
    - 🏢 **CNN Business**: 主流商业新闻
    - ✅ **多元化**: 不同媒体视角
    
    #### 🥉 **扩展源 - Google News**
    - 🔍 **全面搜索**: 聚合多个新闻源
    - 🌐 **广覆盖**: 包含小众但重要的新闻
    - ⚡ **实时性**: Google新闻更新很快
    
    ### 🛡️ **系统优势**
    
    #### 📊 **可靠性**
    - **多重备份**: 一个源失效不影响整体
    - **自动去重**: 避免重复新闻
    - **智能排序**: 按时间和重要性排列
    
    #### 🎯 **全面性**
    - **不同视角**: 多个媒体的报道角度
    - **更多数量**: 通常能获取20-30条新闻
    - **互补信息**: 某些新闻只在特定源出现
    
    ### 💡 **使用建议**
    
    - **个股新闻**: 输入股票代码获取相关新闻
    - **市场新闻**: 留空获取综合市场新闻  
    - **对比验证**: 同一事件的多源报道增加可信度
    - **时效把握**: 关注发布时间，最新消息最重要
    
    ---
    
    **👈 在左侧开始体验多源新闻获取**
    """)

# 页脚
st.markdown("---")
st.markdown("📰 多源新闻集成系统 | 🔄 yfinance + RSS + Google News | 🚫 去重处理 | ⚡ 实时更新")
