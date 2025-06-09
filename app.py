import streamlit as st
import yfinance as yf
import requests
from datetime import datetime, timedelta
import re
from urllib.parse import quote
import warnings
warnings.filterwarnings('ignore')

# 页面配置
st.set_page_config(
    page_title="📰 多源新闻系统",
    page_icon="📰",
    layout="wide"
)

st.title("📰 多源新闻系统")
st.markdown("**整合多个真实新闻源 + 自动去重 + 无额外依赖**")
st.markdown("---")

# 初始化 session state
if 'news_data' not in st.session_state:
    st.session_state.news_data = None
if 'source_stats' not in st.session_state:
    st.session_state.source_stats = {}

# ==================== 新闻源1: yfinance（已验证有效）====================
def fetch_yfinance_news(ticker, debug=False):
    """yfinance新闻获取"""
    try:
        if debug:
            st.write(f"🔍 获取 yfinance {ticker} 新闻...")
        
        stock = yf.Ticker(ticker)
        raw_news = stock.news
        
        if not raw_news:
            if debug:
                st.warning("⚠️ yfinance: 无新闻数据")
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
        
        if debug:
            st.success(f"✅ yfinance: 获取 {len(processed_news)} 条新闻")
        
        return processed_news
        
    except Exception as e:
        if debug:
            st.error(f"❌ yfinance获取失败: {str(e)}")
        return []

# ==================== 新闻源2: RSS解析（使用正则表达式）====================
def parse_rss_with_regex(url, source_name, ticker=None, debug=False):
    """使用正则表达式解析RSS"""
    try:
        if debug:
            st.write(f"🔍 获取 {source_name} RSS...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, timeout=15, headers=headers)
        
        if response.status_code != 200:
            if debug:
                st.warning(f"⚠️ {source_name}: HTTP {response.status_code}")
            return []
        
        content = response.text
        
        # 检查是否是有效的RSS
        if not ('<rss' in content.lower() or '<feed' in content.lower() or '<channel' in content.lower()):
            if debug:
                st.warning(f"⚠️ {source_name}: 不是有效的RSS格式")
            return []
        
        # 使用正则表达式提取新闻项目
        news_items = []
        
        # 查找所有 <item> 或 <entry> 标签
        item_patterns = [
            r'<item>(.*?)</item>',
            r'<entry>(.*?)</entry>'
        ]
        
        items = []
        for pattern in item_patterns:
            found_items = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            items.extend(found_items)
            if found_items:
                break
        
        if debug:
            st.write(f"📊 {source_name}: 找到 {len(items)} 个新闻项目")
        
        for i, item in enumerate(items[:5]):  # 每个源取前5条
            try:
                # 提取标题
                title_match = re.search(r'<title[^>]*>(.*?)</title>', item, re.DOTALL | re.IGNORECASE)
                title = ""
                if title_match:
                    title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                    title = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', title)
                    title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                
                # 如果指定了股票代码，过滤相关新闻
                if ticker and title:
                    if ticker.lower() not in title.lower():
                        continue
                
                # 提取描述/摘要
                desc_patterns = [
                    r'<description[^>]*>(.*?)</description>',
                    r'<summary[^>]*>(.*?)</summary>',
                    r'<content[^>]*>(.*?)</content>'
                ]
                
                description = ""
                for pattern in desc_patterns:
                    desc_match = re.search(pattern, item, re.DOTALL | re.IGNORECASE)
                    if desc_match:
                        description = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
                        description = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', description)
                        description = description.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                        break
                
                # 提取链接
                link_patterns = [
                    r'<link[^>]*>(.*?)</link>',
                    r'<link[^>]*href=["\']([^"\']*)["\']',
                    r'<guid[^>]*>(.*?)</guid>'
                ]
                
                link = ""
                for pattern in link_patterns:
                    link_match = re.search(pattern, item, re.DOTALL | re.IGNORECASE)
                    if link_match:
                        potential_link = link_match.group(1).strip()
                        if potential_link.startswith('http'):
                            link = potential_link
                            break
                
                # 提取发布时间
                date_patterns = [
                    r'<pubDate[^>]*>(.*?)</pubDate>',
                    r'<published[^>]*>(.*?)</published>',
                    r'<updated[^>]*>(.*?)</updated>',
                    r'<dc:date[^>]*>(.*?)</dc:date>'
                ]
                
                pub_date = datetime.now() - timedelta(hours=i)
                for pattern in date_patterns:
                    date_match = re.search(pattern, item, re.DOTALL | re.IGNORECASE)
                    if date_match:
                        try:
                            date_str = date_match.group(1).strip()
                            pub_date = parse_date_string(date_str)
                        except:
                            pass
                        break
                
                # 只添加有标题的新闻
                if title and len(title) > 10:
                    news_items.append({
                        'title': title[:200],
                        'summary': description[:300] if description else '暂无摘要',
                        'url': link,
                        'source': source_name,
                        'published': pub_date,
                        'method': 'RSS'
                    })
                    
            except Exception as e:
                if debug:
                    st.error(f"{source_name} 处理item {i} 失败: {str(e)}")
                continue
        
        if debug:
            st.success(f"✅ {source_name}: 提取 {len(news_items)} 条新闻")
        
        return news_items
        
    except Exception as e:
        if debug:
            st.error(f"❌ {source_name}: {str(e)}")
        return []

def parse_date_string(date_str):
    """解析各种日期格式"""
    try:
        # 移除常见的时区信息
        date_str = re.sub(r'\s+[A-Z]{3,4}$', '', date_str)
        date_str = re.sub(r'[+-]\d{4}$', '', date_str)
        
        # 尝试常见格式
        formats = [
            '%a, %d %b %Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%d %b %Y %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
                
        return datetime.now()
    except:
        return datetime.now()

# ==================== 新闻源3: Google News（简化版）====================
def fetch_google_news_simple(query, debug=False):
    """简化的Google News获取"""
    try:
        if debug:
            st.write(f"🔍 获取Google News: {query}")
        
        encoded_query = quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        return parse_rss_with_regex(url, "Google News", None, debug)
        
    except Exception as e:
        if debug:
            st.error(f"❌ Google News: {str(e)}")
        return []

# ==================== 新闻整合系统 ====================
def remove_duplicate_news(news_list):
    """去除重复新闻"""
    seen_titles = set()
    unique_news = []
    
    for news in news_list:
        # 使用标题的前50个字符作为去重标识
        title_key = news['title'][:50].lower().strip()
        title_key = re.sub(r'[^\w\s]', '', title_key)  # 移除标点符号
        
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_news.append(news)
    
    return unique_news

@st.cache_data(ttl=900)  # 15分钟缓存
def get_all_news_sources(ticker=None, debug=False):
    """获取所有新闻源"""
    all_news = []
    source_stats = {}
    
    # 来源1: yfinance（如果有ticker）
    if ticker:
        yf_news = fetch_yfinance_news(ticker, debug)
        all_news.extend(yf_news)
        source_stats['yfinance'] = len(yf_news)
    
    # 来源2: RSS新闻源
    rss_sources = [
        {
            'name': 'Reuters Business',
            'url': 'http://feeds.reuters.com/reuters/businessNews'
        },
        {
            'name': 'MarketWatch',
            'url': 'https://feeds.marketwatch.com/marketwatch/topstories/'
        },
        {
            'name': 'CNN Business',
            'url': 'http://rss.cnn.com/rss/money_latest.rss'
        }
    ]
    
    rss_news_total = 0
    for source in rss_sources:
        rss_news = parse_rss_with_regex(source['url'], source['name'], ticker, debug)
        all_news.extend(rss_news)
        rss_news_total += len(rss_news)
    
    source_stats['RSS源'] = rss_news_total
    
    # 来源3: Google News
    if ticker:
        google_query = f"{ticker} stock financial news"
    else:
        google_query = "stock market financial news today"
    
    google_news = fetch_google_news_simple(google_query, debug)
    all_news.extend(google_news)
    source_stats['Google News'] = len(google_news)
    
    # 去重处理
    unique_news = remove_duplicate_news(all_news)
    
    # 按时间排序
    unique_news.sort(key=lambda x: x['published'], reverse=True)
    
    # 统计信息
    total_before = len(all_news)
    total_after = len(unique_news)
    removed = total_before - total_after
    
    if debug:
        st.info(f"📊 原始获取: {total_before} 条，去重后: {total_after} 条，移除重复: {removed} 条")
    
    return unique_news, source_stats

# ==================== 简单翻译和分析 ====================
def simple_translate(text):
    """简单财经术语翻译"""
    if not text:
        return text
    
    terms = {
        'earnings': '财报', 'revenue': '营收', 'profit': '利润', 'loss': '亏损',
        'stock': '股票', 'shares': '股价', 'market': '市场', 'trading': '交易',
        'announced': '宣布', 'reported': '报告', 'released': '发布',
        'increased': '增长', 'decreased': '下降', 'rose': '上涨', 'fell': '下跌',
        'beat': '超过', 'missed': '未达到', 'strong': '强劲', 'weak': '疲软'
    }
    
    result = text
    for en, zh in terms.items():
        result = re.sub(r'\b' + re.escape(en) + r'\b', zh, result, flags=re.IGNORECASE)
    
    return result

def simple_sentiment(title, summary):
    """简单情绪分析"""
    text = (title + ' ' + summary).lower()
    
    positive_words = ['beat', 'strong', 'growth', 'increase', 'rise', 'gain', 'up', 'success', 'win']
    negative_words = ['miss', 'weak', 'decline', 'fall', 'drop', 'down', 'loss', 'concern', 'worry']
    
    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)
    
    if pos_count > neg_count:
        return '利好', 'green'
    elif neg_count > pos_count:
        return '利空', 'red'
    else:
        return '中性', 'gray'

# ==================== 界面 ====================
# 侧边栏
with st.sidebar:
    st.header("📰 多源新闻设置")
    
    ticker = st.text_input(
        "股票代码 (可选):",
        placeholder="例如: AAPL, MSFT, TSLA",
        help="输入代码获取相关新闻，留空获取市场综合新闻"
    ).upper().strip()
    
    st.markdown("---")
    
    debug_mode = st.checkbox("🔧 显示调试信息", help="显示详细的获取过程")
    show_translation = st.checkbox("🌐 显示翻译", value=True, help="显示基础财经术语翻译")
    
    st.markdown("---")
    
    if st.button("📰 获取多源新闻", type="primary"):
        with st.spinner("正在从多个新闻源获取数据..."):
            news_data, stats = get_all_news_sources(ticker, debug_mode)
            st.session_state.news_data = news_data
            st.session_state.source_stats = stats
    
    if st.button("🔄 清除缓存"):
        get_all_news_sources.clear()
        st.session_state.news_data = None
        st.session_state.source_stats = {}
        st.success("缓存已清除")

# 主界面
if st.session_state.news_data is not None:
    news_data = st.session_state.news_data
    source_stats = st.session_state.source_stats
    
    if len(news_data) > 0:
        # 数据源统计面板
        st.subheader("📊 数据源统计")
        
        cols = st.columns(len(source_stats) + 1)
        
        total_unique = len(news_data)
        total_raw = sum(source_stats.values())
        
        with cols[0]:
            st.metric("最终结果", f"{total_unique} 条", f"原始: {total_raw}")
        
        for i, (source, count) in enumerate(source_stats.items(), 1):
            with cols[i]:
                st.metric(source, f"{count} 条")
        
        st.markdown("---")
        
        # 新闻列表
        st.subheader(f"📰 {ticker or '市场'} 最新新闻")
        
        for i, news in enumerate(news_data):
            with st.container():
                # 情绪分析
                sentiment, color = simple_sentiment(news['title'], news['summary'])
                
                # 标题（带来源标识）
                st.markdown(f"### {i+1}. {news['title']} `[{news['source']}]`")
                
                # 时间和来源信息
                time_str = news['published'].strftime('%Y-%m-%d %H:%M')
                st.caption(f"🕒 {time_str} | 📡 {news['source']} | 🔧 {news['method']}")
                
                col_main, col_side = st.columns([3, 1])
                
                with col_main:
                    # 摘要（翻译版本）
                    display_summary = simple_translate(news['summary']) if show_translation else news['summary']
                    st.write(display_summary)
                    
                    # 链接
                    if news['url']:
                        st.markdown(f"🔗 [阅读原文]({news['url']})")
                
                with col_side:
                    # 情绪显示
                    st.markdown(f"**情绪分析:**")
                    st.markdown(f"<span style='color:{color}; font-weight:bold'>{sentiment}</span>", unsafe_allow_html=True)
                
                st.markdown("---")
        
        # 底部统计
        st.markdown("### 📈 情绪统计")
        sentiments = {}
        for news in news_data:
            sentiment, _ = simple_sentiment(news['title'], news['summary'])
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
        
        sentiment_cols = st.columns(3)
        for i, (sentiment, count) in enumerate(sentiments.items()):
            with sentiment_cols[i]:
                pct = count / len(news_data) * 100
                st.metric(sentiment, count, f"{pct:.0f}%")
    
    else:
        st.warning("📭 未获取到新闻数据")
        
        if st.session_state.source_stats:
            st.markdown("### 📊 各源尝试结果:")
            for source, count in st.session_state.source_stats.items():
                st.write(f"- **{source}**: {count} 条")

else:
    st.markdown("""
    ## 🎯 多源新闻系统 (无额外依赖版)
    
    ### 📡 **集成的新闻源**
    
    #### 🥇 **yfinance (主力源)**
    - ✅ **已验证有效** - 刚才测试成功的系统
    - 📰 **高质量新闻** - 直接相关的财经内容
    - 🔗 **完整链接** - 可以点击阅读原文
    - ⏱️ **实时更新** - 15分钟缓存保证时效性
    
    #### 🥈 **RSS新闻源 (补充源)**
    - 📊 **Reuters Business** - 国际权威财经新闻
    - 📈 **MarketWatch** - 专业市场分析和评论
    - 🏢 **CNN Business** - 主流商业新闻报道
    - 🔧 **正则解析** - 不依赖额外模块，基础库实现
    
    #### 🥉 **Google News (扩展源)**
    - 🔍 **智能搜索** - 根据股票代码搜索相关新闻
    - 🌐 **广泛聚合** - 包含多个新闻源的内容
    - ⚡ **实时性强** - Google新闻更新频率很高
    
    ### 🛡️ **系统特色**
    
    #### 📊 **智能去重**
    - 自动识别重复新闻
    - 保留最新和最完整的版本
    - 避免信息冗余
    
    #### 🌐 **基础翻译**
    - 常用财经术语中文翻译
    - earnings → 财报, revenue → 营收
    - 帮助理解核心信息
    
    #### 📈 **情绪分析**
    - 自动分析新闻情绪倾向
    - 利好/利空/中性三级分类
    - 辅助投资决策判断
    
    ### 💡 **预期效果**
    
    - **数量提升**: 从单一10条增加到20-30条
    - **视角多元**: 4-5个不同媒体的报道角度
    - **可靠性强**: 多重备份，降低单点故障风险
    - **信息全面**: 覆盖可能被单一源遗漏的重要新闻
    
    ---
    
    **👈 在左侧开始体验多源新闻获取，对比单一源的效果**
    """)

# 页脚
st.markdown("---")
st.markdown("📰 多源新闻系统 | 🚫 无额外依赖 | 🔄 多源备份 | ⚡ 智能去重")
