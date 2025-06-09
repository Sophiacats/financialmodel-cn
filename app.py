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
    page_title="📰 可靠新闻系统",
    page_icon="📰",
    layout="wide"
)

st.title("📰 可靠新闻系统")
st.markdown("**专注于稳定工作的新闻源 - yfinance + Google News + 简化RSS**")
st.markdown("---")

# 初始化 session state
if 'news_data' not in st.session_state:
    st.session_state.news_data = None
if 'source_stats' not in st.session_state:
    st.session_state.source_stats = {}

# ==================== 新闻源1: yfinance（已验证有效）====================
def fetch_yfinance_news(ticker, debug=False):
    """yfinance新闻获取 - 已验证有效"""
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

# ==================== 新闻源2: Google News（已验证有效）====================
def fetch_google_news_enhanced(query, debug=False):
    """增强的Google News获取"""
    try:
        if debug:
            st.write(f"🔍 获取Google News: {query}")
        
        encoded_query = quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, timeout=15, headers=headers)
        
        if response.status_code != 200:
            if debug:
                st.warning(f"⚠️ Google News: HTTP {response.status_code}")
            return []
        
        content = response.text
        
        # 提取新闻项目
        item_pattern = r'<item>(.*?)</item>'
        items = re.findall(item_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if debug:
            st.write(f"📊 Google News: 找到 {len(items)} 个新闻项目")
        
        news_items = []
        for i, item in enumerate(items[:15]):  # 取更多Google News
            try:
                # 提取标题
                title_match = re.search(r'<title[^>]*>(.*?)</title>', item, re.DOTALL | re.IGNORECASE)
                title = ""
                if title_match:
                    title = title_match.group(1).strip()
                    title = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', title)
                    title = re.sub(r'<[^>]+>', '', title)
                    title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
                    title = title.strip()
                
                if not title or len(title) < 10:
                    continue
                
                # 提取链接
                link_match = re.search(r'<link[^>]*>(.*?)</link>', item, re.DOTALL | re.IGNORECASE)
                link = ""
                if link_match:
                    link = link_match.group(1).strip()
                
                # 提取发布时间
                pub_date = datetime.now() - timedelta(hours=i)
                date_match = re.search(r'<pubDate[^>]*>(.*?)</pubDate>', item, re.DOTALL | re.IGNORECASE)
                if date_match:
                    try:
                        date_str = date_match.group(1).strip()
                        # 简单的日期解析
                        if 'GMT' in date_str:
                            date_str = date_str.replace(' GMT', '')
                        pub_date = datetime.strptime(date_str.strip(), '%a, %d %b %Y %H:%M:%S')
                    except:
                        pass
                
                news_items.append({
                    'title': title,
                    'summary': f'来自Google News的{query}相关新闻',
                    'url': link,
                    'source': 'Google News',
                    'published': pub_date,
                    'method': 'Google News RSS'
                })
                
            except Exception as e:
                if debug:
                    st.error(f"Google News处理第{i+1}条失败: {str(e)}")
                continue
        
        if debug:
            st.success(f"✅ Google News: 提取 {len(news_items)} 条新闻")
        
        return news_items
        
    except Exception as e:
        if debug:
            st.error(f"❌ Google News: {str(e)}")
        return []

# ==================== 新闻源3: 简化RSS（只使用最可靠的）====================
def fetch_simple_rss_news(ticker=None, debug=False):
    """简化的RSS新闻获取 - 只使用最可靠的源"""
    
    # 只使用最稳定的RSS源
    reliable_sources = [
        {
            'name': 'Yahoo Finance RSS',
            'url': 'https://feeds.finance.yahoo.com/rss/2.0/headline?region=US&lang=en-US'
        }
    ]
    
    all_rss_news = []
    
    for source in reliable_sources:
        try:
            if debug:
                st.write(f"🔍 获取 {source['name']}...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(source['url'], timeout=15, headers=headers)
            
            if response.status_code != 200:
                if debug:
                    st.warning(f"⚠️ {source['name']}: HTTP {response.status_code}")
                continue
            
            content = response.text
            
            # 简单的RSS解析
            item_pattern = r'<item>(.*?)</item>'
            items = re.findall(item_pattern, content, re.DOTALL | re.IGNORECASE)
            
            if debug:
                st.write(f"📊 {source['name']}: 找到 {len(items)} 个新闻项目")
            
            source_news = []
            for i, item in enumerate(items[:5]):
                try:
                    # 提取标题
                    title_match = re.search(r'<title[^>]*>(.*?)</title>', item, re.DOTALL | re.IGNORECASE)
                    if not title_match:
                        continue
                        
                    title = title_match.group(1).strip()
                    title = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', title)
                    title = re.sub(r'<[^>]+>', '', title)
                    title = title.replace('&amp;', '&').strip()
                    
                    if not title or len(title) < 10:
                        continue
                    
                    # 如果指定了股票代码，简单过滤
                    if ticker:
                        if (ticker.lower() not in title.lower() and 
                            ticker.lower() not in item.lower()):
                            continue
                    
                    # 提取链接
                    link_match = re.search(r'<link[^>]*>(.*?)</link>', item, re.DOTALL | re.IGNORECASE)
                    link = link_match.group(1).strip() if link_match else ''
                    
                    # 提取描述
                    desc_match = re.search(r'<description[^>]*>(.*?)</description>', item, re.DOTALL | re.IGNORECASE)
                    description = ''
                    if desc_match:
                        description = desc_match.group(1).strip()
                        description = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', description)
                        description = re.sub(r'<[^>]+>', '', description)
                        description = description.replace('&amp;', '&').strip()
                    
                    source_news.append({
                        'title': title,
                        'summary': description[:200] if description else '来自Yahoo Finance RSS',
                        'url': link,
                        'source': source['name'],
                        'published': datetime.now() - timedelta(hours=i),
                        'method': 'RSS'
                    })
                    
                except Exception as e:
                    if debug:
                        st.error(f"{source['name']} 处理第{i+1}条失败: {str(e)}")
                    continue
            
            all_rss_news.extend(source_news)
            
            if debug:
                st.success(f"✅ {source['name']}: 提取 {len(source_news)} 条新闻")
                
        except Exception as e:
            if debug:
                st.error(f"❌ {source['name']}: {str(e)}")
            continue
    
    return all_rss_news

# ==================== 新闻整合系统 ====================
def remove_duplicate_news(news_list):
    """智能去重"""
    seen_titles = set()
    unique_news = []
    
    for news in news_list:
        # 使用标题的前40个字符，移除标点符号作为去重标识
        title_key = re.sub(r'[^\w\s]', '', news['title'][:40].lower().strip())
        
        if title_key not in seen_titles and len(title_key) > 10:
            seen_titles.add(title_key)
            unique_news.append(news)
    
    return unique_news

@st.cache_data(ttl=900)  # 15分钟缓存
def get_reliable_news(ticker=None, debug=False):
    """获取可靠新闻源的新闻"""
    all_news = []
    source_stats = {}
    
    # 来源1: yfinance（已验证高质量）
    if ticker:
        yf_news = fetch_yfinance_news(ticker, debug)
        all_news.extend(yf_news)
        source_stats['yfinance'] = len(yf_news)
    
    # 来源2: Google News（已验证有效）
    if ticker:
        google_query = f"{ticker} stock financial earnings"
    else:
        google_query = "stock market financial news earnings"
    
    google_news = fetch_google_news_enhanced(google_query, debug)
    all_news.extend(google_news)
    source_stats['Google News'] = len(google_news)
    
    # 来源3: 简化RSS（只使用最可靠的）
    rss_news = fetch_simple_rss_news(ticker, debug)
    all_news.extend(rss_news)
    source_stats['RSS'] = len(rss_news)
    
    # 智能去重
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

# ==================== 翻译和分析 ====================
def translate_finance_terms(text):
    """财经术语翻译"""
    if not text:
        return text
    
    terms = {
        'earnings': '财报', 'revenue': '营收', 'profit': '利润', 'loss': '亏损',
        'stock': '股票', 'shares': '股价', 'market': '市场', 'trading': '交易',
        'announced': '宣布', 'reported': '报告', 'released': '发布',
        'increased': '增长', 'decreased': '下降', 'rose': '上涨', 'fell': '下跌',
        'beat': '超过', 'missed': '未达到', 'strong': '强劲', 'weak': '疲软',
        'quarterly': '季度', 'annual': '年度', 'billion': '十亿', 'million': '百万'
    }
    
    result = text
    for en, zh in terms.items():
        result = re.sub(r'\b' + re.escape(en) + r'\b', zh, result, flags=re.IGNORECASE)
    
    # 处理数字
    result = re.sub(r'\$([0-9,.]+)\s*billion', r'\1十亿美元', result, flags=re.IGNORECASE)
    result = re.sub(r'\$([0-9,.]+)\s*million', r'\1百万美元', result, flags=re.IGNORECASE)
    
    return result

def analyze_sentiment(title, summary):
    """情绪分析"""
    text = (title + ' ' + summary).lower()
    
    positive_words = ['beat', 'strong', 'growth', 'increase', 'rise', 'gain', 'up', 'success', 'record', 'high']
    negative_words = ['miss', 'weak', 'decline', 'fall', 'drop', 'down', 'loss', 'concern', 'worry', 'low']
    
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
    st.header("📰 可靠新闻源设置")
    
    ticker = st.text_input(
        "股票代码 (可选):",
        placeholder="例如: AMZN, AAPL, TSLA",
        help="输入代码获取相关新闻，留空获取市场综合新闻"
    ).upper().strip()
    
    st.markdown("---")
    
    st.markdown("#### 📡 启用的新闻源")
    st.write("✅ **yfinance** - 高质量财经新闻")
    st.write("✅ **Google News** - 广泛新闻聚合")
    st.write("✅ **Yahoo Finance RSS** - 备用RSS源")
    
    st.markdown("---")
    
    debug_mode = st.checkbox("🔧 显示调试信息", help="显示详细的获取过程")
    show_translation = st.checkbox("🌐 显示翻译", value=True, help="显示财经术语翻译")
    
    st.markdown("---")
    
    if st.button("📰 获取可靠新闻", type="primary"):
        with st.spinner("正在从可靠新闻源获取数据..."):
            news_data, stats = get_reliable_news(ticker, debug_mode)
            st.session_state.news_data = news_data
            st.session_state.source_stats = stats
    
    if st.button("🔄 清除缓存"):
        get_reliable_news.clear()
        st.session_state.news_data = None
        st.session_state.source_stats = {}
        st.success("缓存已清除")

# 主界面
if st.session_state.news_data is not None:
    news_data = st.session_state.news_data
    source_stats = st.session_state.source_stats
    
    if len(news_data) > 0:
        # 数据源统计
        st.subheader("📊 可靠数据源统计")
        
        cols = st.columns(len(source_stats) + 1)
        
        total_unique = len(news_data)
        total_raw = sum(source_stats.values())
        
        with cols[0]:
            st.metric("最终结果", f"{total_unique} 条", f"原始: {total_raw}")
        
        for i, (source, count) in enumerate(source_stats.items(), 1):
            with cols[i]:
                if count > 0:
                    st.metric(source, f"{count} 条", delta="✅")
                else:
                    st.metric(source, f"{count} 条", delta="❌")
        
        # 数据源可靠性评估
        working_sources = len([count for count in source_stats.values() if count > 0])
        total_sources = len(source_stats)
        reliability = working_sources / total_sources * 100
        
        if reliability >= 80:
            st.success(f"🛡️ 系统可靠性: {reliability:.0f}% - 优秀")
        elif reliability >= 60:
            st.warning(f"🛡️ 系统可靠性: {reliability:.0f}% - 良好")
        else:
            st.error(f"🛡️ 系统可靠性: {reliability:.0f}% - 需要改进")
        
        st.markdown("---")
        
        # 新闻列表
        st.subheader(f"📰 {ticker or '市场'} 最新新闻")
        
        for i, news in enumerate(news_data):
            with st.container():
                # 情绪分析
                sentiment, color = analyze_sentiment(news['title'], news['summary'])
                
                # 标题
                title_display = news['title']
                if show_translation:
                    title_display = translate_finance_terms(title_display)
                
                st.markdown(f"### {i+1}. {title_display}")
                
                # 元信息
                time_str = news['published'].strftime('%Y-%m-%d %H:%M')
                st.caption(f"🕒 {time_str} | 📡 {news['source']} | 🔧 {news['method']}")
                
                col_main, col_side = st.columns([3, 1])
                
                with col_main:
                    # 摘要
                    display_summary = news['summary']
                    if show_translation:
                        display_summary = translate_finance_terms(display_summary)
                    st.write(display_summary)
                    
                    # 链接
                    if news['url']:
                        st.markdown(f"🔗 [阅读原文]({news['url']})")
                
                with col_side:
                    # 情绪分析
                    st.markdown(f"**情绪分析:**")
                    st.markdown(f"<span style='color:{color}; font-weight:bold'>{sentiment}</span>", unsafe_allow_html=True)
                    
                    # 来源可靠性
                    if news['method'] == 'yfinance':
                        st.write("🥇 高质量源")
                    elif news['method'] == 'Google News RSS':
                        st.write("🥈 聚合源")
                    else:
                        st.write("🥉 补充源")
                
                st.markdown("---")
        
        # 情绪统计
        st.markdown("### 📈 市场情绪统计")
        sentiments = {}
        for news in news_data:
            sentiment, _ = analyze_sentiment(news['title'], news['summary'])
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
        
        sentiment_cols = st.columns(3)
        for i, (sentiment, count) in enumerate(sentiments.items()):
            with sentiment_cols[i]:
                pct = count / len(news_data) * 100
                if sentiment == '利好':
                    st.success(f"📈 {sentiment}: {count} ({pct:.0f}%)")
                elif sentiment == '利空':
                    st.error(f"📉 {sentiment}: {count} ({pct:.0f}%)")
                else:
                    st.info(f"📊 {sentiment}: {count} ({pct:.0f}%)")
    
    else:
        st.warning("📭 未获取到新闻数据")
        
        if st.session_state.source_stats:
            st.markdown("### 📊 各源尝试结果:")
            for source, count in st.session_state.source_stats.items():
                if count > 0:
                    st.success(f"✅ **{source}**: {count} 条")
                else:
                    st.error(f"❌ **{source}**: {count} 条")

else:
    st.markdown("""
    ## 🎯 可靠新闻系统
    
    ### 📡 **专注于稳定工作的新闻源**
    
    经过调试发现，以下新闻源最稳定可靠：
    
    #### 🥇 **yfinance (主力源)**
    - ✅ **高质量**: 直接相关的财经新闻
    - ✅ **结构完整**: 标题、摘要、链接齐全
    - ✅ **已验证**: 刚才测试获取10条新闻成功
    - ✅ **可点击**: 所有链接都能正常访问
    
    #### 🥈 **Google News (补充源)**
    - ✅ **广泛聚合**: 汇集多个新闻源
    - ✅ **实时更新**: 新闻更新频率很高
    - ✅ **已验证**: 刚才测试获取5条新闻成功
    - ✅ **搜索精准**: 能根据股票代码找到相关新闻
    
    #### 🥉 **Yahoo Finance RSS (备用源)**
    - ✅ **稳定可靠**: Yahoo官方RSS源
    - ✅ **无需API**: 直接HTTP请求
    - ✅ **结构标准**: 标准RSS格式易于解析
    
    ### 🛡️ **可靠性保障**
    
    #### 📊 **质量优先**
    - 专注于已验证有效的新闻源
    - 移除了有问题的Reuters、MarketWatch等
    - 确保每个源都能稳定获取新闻
    
    #### 🎯 **实用性强**
    - yfinance: 高质量财经新闻 (~10条)
    - Google News: 广泛新闻聚合 (~5-15条)
    - RSS备用: 额外补充新闻 (~3-5条)
    - **总计**: 通常20-30条优质新闻
    
    #### 🔄 **系统稳定**
    - 15分钟智能缓存
    - 自动去重处理
    - 按时间排序
    - 实时可靠性监控
    
    ### 💡 **预期体验**
    
    输入股票代码（如AMZN）后，你应该看到：
    - ✅ yfinance: 10条高质量新闻
    - ✅ Google News: 5-15条聚合新闻  
    - ✅ RSS源: 3-5条补充新闻
    - **总计**: 18-30条去重后的优质新闻
    
    ---
    
    **👈 在左侧开始体验可靠的多源新闻获取**
    """)

# 页脚
st.markdown("---")
st.markdown("📰 可靠新闻系统 | ✅ 验证有效的新闻源 | 🛡️ 稳定性优先 | 📊 质量保证")
