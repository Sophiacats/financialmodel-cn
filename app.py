import streamlit as st
import requests
import re
from datetime import datetime, timedelta
import json
from urllib.parse import quote

# 页面配置
st.set_page_config(
    page_title="📰 简单新闻获取器",
    page_icon="📰",
    layout="wide"
)

st.title("📰 简单新闻获取器")
st.markdown("**专注获取真实新闻 - 调试优先**")
st.markdown("---")

# 初始化 session state
if 'news_results' not in st.session_state:
    st.session_state.news_results = None
if 'debug_logs' not in st.session_state:
    st.session_state.debug_logs = []

def log_debug(message):
    """记录调试信息"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    st.session_state.debug_logs.append(f"[{timestamp}] {message}")

def test_basic_rss(url, source_name):
    """测试基本RSS获取"""
    log_debug(f"开始测试 {source_name}: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, timeout=15, headers=headers)
        log_debug(f"{source_name} - 状态码: {response.status_code}")
        log_debug(f"{source_name} - 内容长度: {len(response.text)}")
        
        if response.status_code != 200:
            log_debug(f"{source_name} - HTTP错误: {response.status_code}")
            return []
        
        content = response.text
        
        # 简单检查是否是RSS内容
        if not ('<rss' in content.lower() or '<feed' in content.lower() or '<channel' in content.lower()):
            log_debug(f"{source_name} - 不是有效的RSS内容")
            return []
        
        log_debug(f"{source_name} - 检测到有效RSS内容")
        
        # 使用正则表达式提取新闻项目
        news_items = extract_news_from_rss(content, source_name)
        log_debug(f"{source_name} - 提取到 {len(news_items)} 条新闻")
        
        return news_items
        
    except Exception as e:
        log_debug(f"{source_name} - 异常: {str(e)}")
        return []

def extract_news_from_rss(content, source_name):
    """从RSS内容中提取新闻"""
    news_items = []
    
    try:
        # 查找所有 <item> 标签
        item_pattern = r'<item>(.*?)</item>'
        items = re.findall(item_pattern, content, re.DOTALL | re.IGNORECASE)
        
        log_debug(f"{source_name} - 找到 {len(items)} 个item标签")
        
        for i, item in enumerate(items[:10]):  # 只取前10个
            try:
                # 提取标题
                title_match = re.search(r'<title[^>]*>(.*?)</title>', item, re.DOTALL | re.IGNORECASE)
                title = ""
                if title_match:
                    title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                    # 移除CDATA
                    title = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', title)
                
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
                        break
                
                # 提取链接
                link_match = re.search(r'<link[^>]*>(.*?)</link>', item, re.DOTALL | re.IGNORECASE)
                link = ""
                if link_match:
                    link = link_match.group(1).strip()
                
                # 提取发布时间
                date_patterns = [
                    r'<pubDate[^>]*>(.*?)</pubDate>',
                    r'<published[^>]*>(.*?)</published>',
                    r'<updated[^>]*>(.*?)</updated>'
                ]
                
                pub_date = datetime.now() - timedelta(hours=i)
                for pattern in date_patterns:
                    date_match = re.search(pattern, item, re.DOTALL | re.IGNORECASE)
                    if date_match:
                        try:
                            date_str = date_match.group(1).strip()
                            # 尝试解析常见的日期格式
                            pub_date = parse_rss_date(date_str)
                        except:
                            pass
                        break
                
                # 只添加有标题的新闻
                if title and len(title) > 10:
                    news_items.append({
                        'title': title[:200],  # 限制标题长度
                        'summary': description[:300] if description else '暂无摘要',
                        'link': link,
                        'source': source_name,
                        'published': pub_date
                    })
                    
            except Exception as e:
                log_debug(f"{source_name} - 处理item {i} 失败: {str(e)}")
                continue
    
    except Exception as e:
        log_debug(f"{source_name} - RSS解析失败: {str(e)}")
    
    return news_items

def parse_rss_date(date_str):
    """解析RSS日期"""
    try:
        # 移除常见的时区信息
        date_str = re.sub(r'\s+[A-Z]{3,4}$', '', date_str)
        
        # 尝试常见格式
        formats = [
            '%a, %d %b %Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%d %b %Y %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
                
        return datetime.now()
    except:
        return datetime.now()

def fetch_google_news_simple(query):
    """简单的Google News获取"""
    try:
        log_debug(f"开始获取Google News: {query}")
        
        # Google News RSS URL
        encoded_query = quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        return test_basic_rss(url, "Google News")
        
    except Exception as e:
        log_debug(f"Google News 获取失败: {str(e)}")
        return []

def get_all_news(ticker=None):
    """获取所有新闻源"""
    all_news = []
    
    # RSS新闻源列表
    rss_sources = [
        {
            'name': 'Yahoo Finance',
            'url': 'https://feeds.finance.yahoo.com/rss/2.0/headline?region=US&lang=en-US'
        },
        {
            'name': 'Reuters Business', 
            'url': 'http://feeds.reuters.com/reuters/businessNews'
        },
        {
            'name': 'MarketWatch',
            'url': 'https://feeds.marketwatch.com/marketwatch/topstories/'
        },
        {
            'name': 'CNN Money',
            'url': 'http://rss.cnn.com/rss/money_latest.rss'
        }
    ]
    
    # 如果有股票代码，也获取特定新闻
    if ticker:
        # 尝试特定股票的Yahoo Finance RSS
        ticker_rss = {
            'name': f'Yahoo Finance {ticker}',
            'url': f'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US'
        }
        rss_sources.insert(0, ticker_rss)
    
    # 获取RSS新闻
    for source in rss_sources:
        news = test_basic_rss(source['url'], source['name'])
        all_news.extend(news)
    
    # 获取Google News
    if ticker:
        google_query = f"{ticker} stock"
    else:
        google_query = "stock market news"
    
    google_news = fetch_google_news_simple(google_query)
    all_news.extend(google_news)
    
    # 按时间排序
    all_news.sort(key=lambda x: x['published'], reverse=True)
    
    return all_news

# 侧边栏
with st.sidebar:
    st.header("🔧 新闻获取测试")
    
    ticker = st.text_input("股票代码 (可选):", placeholder="例如: AAPL").upper().strip()
    
    st.markdown("---")
    
    if st.button("📰 开始获取新闻", type="primary"):
        st.session_state.debug_logs = []  # 清空调试日志
        
        with st.spinner("正在获取新闻..."):
            news_results = get_all_news(ticker)
            st.session_state.news_results = news_results
    
    if st.button("🔄 清除结果"):
        st.session_state.news_results = None
        st.session_state.debug_logs = []
    
    st.markdown("---")
    
    # 显示调试日志
    st.subheader("🔍 调试日志")
    if st.session_state.debug_logs:
        for log in st.session_state.debug_logs[-20:]:  # 只显示最后20条
            st.text(log)
    else:
        st.text("暂无调试信息")

# 主界面
if st.session_state.news_results is not None:
    news_results = st.session_state.news_results
    
    if len(news_results) > 0:
        st.success(f"✅ 成功获取 {len(news_results)} 条新闻！")
        
        # 按来源统计
        sources = {}
        for news in news_results:
            source = news['source']
            sources[source] = sources.get(source, 0) + 1
        
        st.markdown("### 📊 数据源统计")
        cols = st.columns(len(sources))
        for i, (source, count) in enumerate(sources.items()):
            with cols[i]:
                st.metric(source, count)
        
        st.markdown("---")
        
        # 显示新闻列表
        st.markdown("### 📰 新闻列表")
        
        for i, news in enumerate(news_results):
            with st.container():
                st.markdown(f"#### {i+1}. {news['title']}")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(news['summary'])
                    if news['link']:
                        st.markdown(f"🔗 [阅读原文]({news['link']})")
                
                with col2:
                    st.write(f"**来源:** {news['source']}")
                    st.write(f"**时间:** {news['published'].strftime('%Y-%m-%d %H:%M')}")
                
                st.markdown("---")
    
    else:
        st.error("❌ 未获取到任何新闻")
        
        st.markdown("### 🔍 调试信息")
        if st.session_state.debug_logs:
            for log in st.session_state.debug_logs:
                st.text(log)

else:
    st.markdown("""
    ## 🎯 简单新闻获取器
    
    这是一个专注于**调试和测试**的新闻获取系统：
    
    ### 📡 测试的新闻源
    
    1. **Yahoo Finance RSS** - 主要财经新闻
    2. **Reuters Business** - 路透社商业新闻  
    3. **MarketWatch** - 市场观察新闻
    4. **CNN Money** - CNN财经新闻
    5. **Google News** - 谷歌新闻搜索
    
    ### 🔧 调试功能
    
    - ✅ **详细日志** - 显示每个步骤的执行情况
    - 📊 **状态码检查** - 验证HTTP请求状态
    - 🔍 **内容验证** - 检查RSS格式有效性
    - 📈 **统计信息** - 显示各源获取的新闻数量
    
    ### 🚀 使用方法
    
    1. **可选输入股票代码** - 获取特定股票新闻
    2. **点击"开始获取新闻"** - 测试所有新闻源
    3. **查看调试日志** - 了解具体的执行过程
    4. **检查结果** - 查看成功获取的新闻
    
    ---
    
    **👈 在左侧开始测试新闻获取功能**
    
    这个版本专注于**诊断问题**，会显示详细的调试信息帮助发现获取失败的具体原因。
    """)

# 页脚
st.markdown("---")
st.markdown("📰 简单新闻获取器 | 🔧 调试优先 | 📊 详细日志 | 🎯 问题诊断")
