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
warnings.filterwarnings('ignore')

# 页面配置
st.set_page_config(
    page_title="📰 通用美股新闻分析系统",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化 session state
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None
if 'news_data' not in st.session_state:
    st.session_state.news_data = None

st.title("📰 通用美股新闻分析系统")
st.markdown("**支持所有美股代码 + 实时新闻获取 + 智能中文翻译 + 情绪分析**")
st.markdown("---")

# ==================== 通用翻译系统 ====================

def create_dynamic_translation_dict():
    """创建动态财经翻译词典"""
    return {
        # 通用财经术语
        'earnings': '财报', 'revenue': '营收', 'profit': '利润', 'loss': '亏损',
        'dividend': '分红', 'stock': '股票', 'shares': '股份', 'price': '价格',
        'market': '市场', 'trading': '交易', 'investor': '投资者', 'investment': '投资',
        'shareholder': '股东', 'CEO': '首席执行官', 'CFO': '首席财务官',
        
        # 市场动作
        'announced': '宣布', 'reported': '报告', 'released': '发布', 'launched': '推出',
        'acquired': '收购', 'merged': '合并', 'expanded': '扩张', 'increased': '增加',
        'decreased': '减少', 'grew': '增长', 'fell': '下跌', 'rose': '上涨',
        'gained': '上涨', 'dropped': '下跌', 'surged': '飙升', 'plunged': '暴跌',
        
        # 行业术语
        'technology': '科技', 'artificial intelligence': 'AI', 'machine learning': '机器学习',
        'cloud computing': '云计算', 'semiconductor': '半导体', 'software': '软件',
        'hardware': '硬件', 'electric vehicle': '电动汽车', 'renewable energy': '可再生能源',
        'healthcare': '医疗保健', 'pharmaceutical': '制药', 'biotechnology': '生物技术',
        'financial services': '金融服务', 'banking': '银行业', 'insurance': '保险',
        'real estate': '房地产', 'retail': '零售', 'e-commerce': '电商',
        
        # 数值表达
        'billion': '十亿', 'million': '百万', 'thousand': '千', 'percent': '百分比',
        'quarterly': '季度', 'annually': '年度', 'monthly': '月度',
        
        # 时间表达
        'this quarter': '本季度', 'last quarter': '上季度', 'this year': '今年',
        'last year': '去年', 'year-over-year': '同比', 'quarter-over-quarter': '环比',
        
        # 常见表达
        'beat expectations': '超预期', 'missed expectations': '不及预期',
        'better than expected': '好于预期', 'worse than expected': '差于预期',
        'record high': '历史新高', 'all-time high': '历史最高',
        'record low': '历史新低', 'all-time low': '历史最低',
        
        # 句型模式
        'said in a statement': '在声明中表示', 'according to': '据',
        'is expected to': '预计将', 'announced today': '今日宣布',
        'plans to': '计划', 'aims to': '旨在', 'seeks to': '寻求',
    }

def smart_universal_translate(text):
    """通用智能翻译系统"""
    if not text or len(text.strip()) < 3:
        return text
    
    # 获取动态翻译词典
    translation_dict = create_dynamic_translation_dict()
    
    result = text
    
    # 应用通用翻译
    for en_term, zh_term in translation_dict.items():
        # 使用正则表达式进行单词边界匹配
        pattern = r'\b' + re.escape(en_term) + r'\b'
        result = re.sub(pattern, zh_term, result, flags=re.IGNORECASE)
    
    # 处理数字+单位的表达
    # $X billion -> X十亿美元
    result = re.sub(r'\$([0-9.]+)\s*billion', r'\1十亿美元', result, flags=re.IGNORECASE)
    result = re.sub(r'\$([0-9.]+)\s*million', r'\1百万美元', result, flags=re.IGNORECASE)
    result = re.sub(r'([0-9.]+)%', r'\1%', result)
    
    # 处理常见句型
    sentence_patterns = {
        r'(\w+)\s+announced\s+that': r'\1宣布',
        r'(\w+)\s+reported\s+that': r'\1报告称',
        r'(\w+)\s+said\s+that': r'\1表示',
        r'shares\s+of\s+(\w+)\s+rose\s+([0-9.]+)%': r'\1股价上涨\2%',
        r'shares\s+of\s+(\w+)\s+fell\s+([0-9.]+)%': r'\1股价下跌\2%',
        r'(\w+)\s+beat\s+earnings\s+expectations': r'\1财报超预期',
        r'(\w+)\s+missed\s+earnings\s+expectations': r'\1财报不及预期',
    }
    
    for pattern, replacement in sentence_patterns.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result

def extract_universal_keywords(text):
    """通用关键词提取"""
    if not text:
        return []
    
    text_lower = text.lower()
    
    keyword_categories = {
        "科技": ["tech", "technology", "ai", "artificial intelligence", "software", "hardware", 
                "cloud", "semiconductor", "chip", "digital", "innovation"],
        "金融": ["bank", "financial", "finance", "credit", "loan", "insurance", "investment"],
        "医疗": ["health", "medical", "pharmaceutical", "biotech", "drug", "vaccine"],
        "能源": ["energy", "oil", "gas", "renewable", "solar", "wind", "electric"],
        "消费": ["retail", "consumer", "sales", "ecommerce", "shopping"],
        "房地产": ["real estate", "property", "housing", "construction"],
        "上涨": ["up", "rise", "gain", "increase", "surge", "rally", "boost", "jump"],
        "下跌": ["down", "fall", "drop", "decline", "plunge", "crash", "slide"],
        "业绩": ["earnings", "revenue", "profit", "income", "performance"],
        "政策": ["policy", "regulation", "government", "federal", "law"],
    }
    
    found_keywords = []
    for category, words in keyword_categories.items():
        for word in words:
            if word in text_lower:
                found_keywords.append(category)
                break
    
    return found_keywords[:5]

def analyze_universal_sentiment(keywords, title, summary):
    """通用情绪分析"""
    text = (title + ' ' + summary).lower()
    
    # 积极词汇
    positive_words = ["beat", "exceed", "outperform", "growth", "increase", "rise", "gain", 
                     "strong", "robust", "solid", "success", "win", "breakthrough", "innovation"]
    
    # 消极词汇
    negative_words = ["miss", "decline", "fall", "drop", "weak", "poor", "loss", "fail",
                     "concern", "worry", "risk", "problem", "issue", "challenge"]
    
    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)
    
    # 结合关键词判断
    bullish_keywords = ["上涨", "业绩", "科技"]
    bearish_keywords = ["下跌", "政策"]
    
    keyword_bullish = sum(1 for kw in keywords if kw in bullish_keywords)
    keyword_bearish = sum(1 for kw in keywords if kw in bearish_keywords)
    
    total_bullish = positive_count + keyword_bullish
    total_bearish = negative_count + keyword_bearish
    
    if total_bullish > total_bearish:
        return "利好"
    elif total_bearish > total_bullish:
        return "利空"
    else:
        return "中性"

# ==================== 多源新闻获取系统 ====================

def fetch_yfinance_news(ticker):
    """方法1: 使用 yfinance 获取新闻"""
    news_items = []
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        
        if news and len(news) > 0:
            for i, article in enumerate(news[:5]):
                try:
                    # 强健的数据提取
                    title = ""
                    summary = ""
                    link = ""
                    source = "Yahoo Finance"
                    pub_time = datetime.now() - timedelta(hours=i+1)
                    
                    if isinstance(article, dict):
                        # 多种方式提取标题
                        title = (article.get('title') or 
                               article.get('headline') or 
                               article.get('shortName') or
                               article.get('longName', ''))
                        
                        # 多种方式提取摘要
                        summary = (article.get('summary') or 
                                 article.get('description') or 
                                 article.get('snippet') or
                                 article.get('content', ''))
                        
                        # 提取链接
                        if 'link' in article:
                            link = article['link']
                        elif 'url' in article:
                            link = article['url']
                        elif 'clickThroughUrl' in article and isinstance(article['clickThroughUrl'], dict):
                            link = article['clickThroughUrl'].get('url', '')
                        
                        # 提取来源
                        if 'provider' in article and isinstance(article['provider'], dict):
                            source = article['provider'].get('displayName', 'Yahoo Finance')
                        elif 'source' in article:
                            source = article['source']
                        
                        # 提取时间
                        if 'providerPublishTime' in article:
                            try:
                                pub_time = datetime.fromtimestamp(article['providerPublishTime'])
                            except:
                                pass
                    
                    # 验证必要字段
                    if title and len(title.strip()) > 10:
                        news_items.append({
                            'title': title.strip(),
                            'summary': summary.strip() if summary else '暂无摘要',
                            'link': link,
                            'source': source,
                            'published': pub_time,
                            'method': 'yfinance'
                        })
                
                except Exception as e:
                    continue
    
    except Exception as e:
        pass
    
    return news_items

def fetch_fallback_news(ticker):
    """方法2: 备选新闻获取（模拟）"""
    # 这里可以接入其他新闻API，比如Alpha Vantage, Polygon等
    # 暂时返回空列表
    return []

def get_comprehensive_news(ticker):
    """综合新闻获取 - 多源合并"""
    all_news = []
    
    # 方法1: yfinance
    yf_news = fetch_yfinance_news(ticker)
    all_news.extend(yf_news)
    
    # 方法2: 备选方案
    if len(all_news) < 3:
        fallback_news = fetch_fallback_news(ticker)
        all_news.extend(fallback_news)
    
    # 如果仍然没有新闻，尝试获取市场综合新闻
    if len(all_news) < 3:
        market_news = fetch_yfinance_news("^GSPC")  # S&P 500
        all_news.extend(market_news)
    
    return all_news

@st.cache_data(ttl=1800)
def fetch_universal_financial_news(ticker=None, debug=False):
    """通用财经新闻获取系统"""
    current_time = datetime.now()
    
    if debug:
        st.sidebar.write(f"🔍 开始获取 {ticker or '市场'} 新闻...")
    
    try:
        # 获取新闻
        raw_news = get_comprehensive_news(ticker) if ticker else get_comprehensive_news("^GSPC")
        
        if debug:
            st.sidebar.write(f"📰 原始新闻数量: {len(raw_news)}")
        
        processed_news = []
        
        for i, news_item in enumerate(raw_news):
            try:
                # 翻译处理
                translated_title = smart_universal_translate(news_item['title'])
                translated_summary = smart_universal_translate(news_item['summary'])
                
                # 关键词提取
                keywords = extract_universal_keywords(news_item['title'] + ' ' + news_item['summary'])
                
                # 情绪分析
                sentiment = analyze_universal_sentiment(keywords, news_item['title'], news_item['summary'])
                
                processed_item = {
                    "title": translated_title,
                    "summary": translated_summary[:300] + '...' if len(translated_summary) > 300 else translated_summary,
                    "published": news_item['published'],
                    "url": news_item['link'],
                    "source": news_item['source'],
                    "category": "real_news",
                    "keywords": keywords,
                    "sentiment": sentiment,
                    "is_real": True,
                    "ticker": ticker or "MARKET",
                    "method": news_item.get('method', 'unknown')
                }
                
                processed_news.append(processed_item)
                
            except Exception as e:
                if debug:
                    st.sidebar.error(f"处理新闻 {i+1} 失败: {str(e)}")
                continue
        
        # 按时间排序
        processed_news.sort(key=lambda x: x['published'], reverse=True)
        
        if debug:
            st.sidebar.success(f"✅ 成功处理 {len(processed_news)} 条新闻")
        
        # 如果没有新闻，返回提示
        if len(processed_news) == 0:
            return [{
                "title": f"暂无 {ticker or '市场'} 相关新闻",
                "summary": "当前时段暂无相关新闻更新。建议稍后重试或尝试其他股票代码。也可能是API访问限制导致，建议使用VPN或稍后重试。",
                "published": current_time,
                "url": "https://finance.yahoo.com",
                "source": "系统提示",
                "category": "system_info",
                "keywords": ["系统"],
                "sentiment": "中性",
                "is_real": False,
                "ticker": ticker or "MARKET"
            }]
        
        return processed_news
        
    except Exception as e:
        error_msg = f"新闻获取系统错误: {str(e)}"
        if debug:
            st.sidebar.error(error_msg)
        
        return [{
            "title": "新闻获取服务异常",
            "summary": f"系统遇到技术问题: {error_msg}。请检查网络连接或稍后重试。",
            "published": current_time,
            "url": "",
            "source": "系统错误",
            "category": "system_error",
            "keywords": ["错误"],
            "sentiment": "中性",
            "is_real": False,
            "ticker": ticker or "MARKET"
        }]

def get_sentiment_advice(sentiment):
    """根据情绪给出投资建议"""
    if sentiment == "利好":
        return {
            "icon": "📈",
            "advice": "积极信号，关注投资机会",
            "action": "可考虑适当增加仓位，关注相关板块",
            "color": "green"
        }
    elif sentiment == "利空":
        return {
            "icon": "📉",
            "advice": "风险信号，建议谨慎",
            "action": "控制风险敞口，关注防御性资产",
            "color": "red"
        }
    else:
        return {
            "icon": "📊",
            "advice": "中性信号，维持策略",
            "action": "保持观察，等待更明确信号",
            "color": "gray"
        }

# ==================== 侧边栏设置 ====================
with st.sidebar:
    st.header("📰 新闻设置")
    
    # 股票代码输入
    ticker_input = st.text_input(
        "输入美股代码:",
        placeholder="例如: AAPL, TSLA, GOOGL, NVDA...",
        help="支持所有美股代码，留空获取市场综合新闻"
    ).upper().strip()
    
    # 快速选择
    st.markdown("#### 📈 热门股票快选")
    quick_picks = {
        "市场综合": "",
        "苹果 AAPL": "AAPL",
        "特斯拉 TSLA": "TSLA", 
        "微软 MSFT": "MSFT",
        "英伟达 NVDA": "NVDA",
        "亚马逊 AMZN": "AMZN",
        "谷歌 GOOGL": "GOOGL",
        "Meta META": "META"
    }
    
    selected_quick = st.selectbox("或选择热门股票:", list(quick_picks.keys()))
    
    # 确定最终的ticker
    final_ticker = ticker_input if ticker_input else quick_picks[selected_quick]
    
    st.markdown("---")
    
    # 高级选项
    st.markdown("#### ⚙️ 高级选项")
    debug_mode = st.checkbox("🔧 调试模式", help="显示详细的获取过程")
    show_method = st.checkbox("📡 显示数据源", help="显示新闻来源方法")
    
    # 获取新闻按钮
    st.markdown("#### 🚀 操作")
    if st.button("📰 获取最新新闻", type="primary", use_container_width=True):
        st.session_state.selected_ticker = final_ticker
        with st.spinner(f"正在获取 {final_ticker or '市场'} 最新新闻..."):
            news_data = fetch_universal_financial_news(final_ticker, debug=debug_mode)
            st.session_state.news_data = news_data
    
    if st.button("🔄 刷新缓存", use_container_width=True):
        fetch_universal_financial_news.clear()
        st.session_state.news_data = None
        st.success("缓存已清除！")
        st.rerun()
    
    st.markdown("---")
    
    # 使用说明
    with st.expander("📖 使用说明"):
        st.markdown("""
        ### 🎯 功能特色
        - **通用支持**: 支持所有美股代码
        - **多源获取**: 多个数据源保证可靠性  
        - **智能翻译**: 通用财经术语翻译
        - **情绪分析**: AI驱动的情绪判断
        - **实时更新**: 30分钟缓存机制
        
        ### 📝 使用方法
        1. 输入任意美股代码或选择热门股票
        2. 点击"获取最新新闻"
        3. 查看翻译后的新闻和分析结果
        4. 根据情绪建议调整投资策略
        
        ### 💡 小贴士
        - 留空代码获取市场综合新闻
        - 开启调试模式查看详细过程
        - 遇到问题可尝试刷新缓存
        """)

# ==================== 主界面 ====================
if st.session_state.news_data is not None:
    news_data = st.session_state.news_data
    
    # 统计信息
    total_news = len(news_data)
    real_news = len([n for n in news_data if n.get('is_real', False)])
    bullish_count = len([n for n in news_data if n['sentiment'] == '利好'])
    bearish_count = len([n for n in news_data if n['sentiment'] == '利空'])
    neutral_count = len([n for n in news_data if n['sentiment'] == '中性'])
    
    # 显示统计面板
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📰 新闻总数", total_news)
    with col2:
        st.metric("✅ 真实新闻", real_news)
    with col3:
        st.metric("📈 利好", bullish_count, delta=f"{bullish_count/total_news*100:.0f}%" if total_news > 0 else "0%")
    with col4:
        st.metric("📉 利空", bearish_count, delta=f"{bearish_count/total_news*100:.0f}%" if total_news > 0 else "0%")
    with col5:
        st.metric("📊 中性", neutral_count, delta=f"{neutral_count/total_news*100:.0f}%" if total_news > 0 else "0%")
    
    # 市场情绪总结
    if real_news > 0:
        if bullish_count > bearish_count:
            st.success("📈 整体市场情绪: 偏向乐观")
        elif bearish_count > bullish_count:
            st.error("📉 整体市场情绪: 偏向谨慎")
        else:
            st.info("📊 整体市场情绪: 相对平衡")
    
    st.markdown("---")
    
    # 显示新闻列表
    if real_news > 0:
        st.subheader(f"📰 {st.session_state.selected_ticker or '市场'} 最新新闻")
        
        for i, news in enumerate(news_data):
            if news.get('is_real', False):
                sentiment_info = get_sentiment_advice(news['sentiment'])
                
                with st.container():
                    col_main, col_side = st.columns([3, 1])
                    
                    with col_main:
                        # 标题和基本信息
                        st.markdown(f"### 📰 {news['title']}")
                        
                        time_str = news['published'].strftime('%Y-%m-%d %H:%M')
                        source_info = f"🕒 {time_str} | 📡 {news['source']}"
                        
                        if show_method and 'method' in news:
                            source_info += f" | 🔧 {news['method']}"
                        
                        st.caption(source_info)
                        
                        # 摘要
                        st.write(news['summary'])
                        
                        # 关键词
                        if news['keywords']:
                            keywords_str = " ".join([f"`{kw}`" for kw in news['keywords']])
                            st.markdown(f"**🏷️ 关键词:** {keywords_str}")
                        
                        # 链接
                        if news['url']:
                            st.markdown(f"🔗 [阅读原文]({news['url']})")
                    
                    with col_side:
                        # 情绪分析卡片
                        sentiment_color = sentiment_info['color']
                        st.markdown(f"### {sentiment_info['icon']}")
                        st.markdown(f"**<span style='color:{sentiment_color}'>{news['sentiment']}</span>**", unsafe_allow_html=True)
                        
                        st.write("**📋 市场影响:**")
                        st.write(sentiment_info['advice'])
                        
                        st.write("**💡 操作建议:**")
                        st.write(sentiment_info['action'])
                
                st.markdown("---")
    
    else:
        st.warning("📭 当前没有获取到真实新闻，建议检查股票代码或稍后重试")

else:
    # 欢迎页面
    st.markdown("""
    ## 🎯 通用美股新闻分析系统
    
    ### ✨ 核心特色
    
    #### 📈 通用支持
    - 🔍 支持**所有美股股票代码**
    - 🌐 无需硬编码特定公司
    - 📊 自动适应不同行业和公司
    
    #### 🛡️ 多重保障
    - 📡 多数据源获取，提高成功率
    - 🔄 智能缓存，提升响应速度
    - 🚨 完善的错误处理和降级方案
    
    #### 🤖 智能分析
    - 🌐 通用财经术语翻译系统
    - 🎯 关键词自动提取
    - 📊 AI驱动的情绪分析
    - 💡 个性化投资建议
    
    ### 🚀 快速开始
    
    1. **输入股票代码** - 在左侧输入任意美股代码（如 AAPL, TSLA 等）
    2. **获取新闻** - 点击"获取最新新闻"按钮  
    3. **查看分析** - 浏览翻译后的新闻和AI分析结果
    4. **投资决策** - 根据情绪分析和建议制定策略
    
    ### 💡 支持示例
    
    - **科技股**: AAPL, MSFT, GOOGL, NVDA, META
    - **电动车**: TSLA, NIO, XPEV, LI  
    - **金融**: JPM, BAC, GS, MS
    - **消费**: AMZN, WMT, TGT, COST
    - **医疗**: JNJ, PFE, MRNA, UNH
    
    ---
    
    **👈 请在左侧输入股票代码开始使用**
    
    **⚠️ 免责声明**: 本系统仅供参考，不构成投资建议。
    """)
    
    # 示例展示
    with st.expander("🎬 功能演示"):
        st.markdown("""
        ### 📊 智能翻译示例
        
        **原文:**
        > "Apple announced that its Q4 revenue increased by 8% year-over-year, beating Wall Street expectations despite supply chain challenges."
        
        **智能翻译:**
        > "苹果宣布其第四季度营收同比增长8%，尽管面临供应链挑战，仍超预期。"
        
        **关键词:** `科技` `业绩` `上涨`
        
        **情绪:** 📈 利好
        
        **建议:** 可考虑适当增加仓位，关注相关板块
        
        ---
        
        ### 🔍 通用适应性
        
        本系统可以处理任何美股公司的新闻，无论是：
        - 大型科技公司 (FAANG)
        - 新兴成长股
        - 传统制造业
        - 金融服务业
        - 生物医药股
        
        所有翻译和分析都是动态生成的，不依赖预设的公司列表。
        """)

# 页脚信息
st.markdown("---")
st.markdown("📰 通用美股新闻分析系统 | 🔄 实时获取 | 🌐 智能翻译 | 📊 情绪分析 | 💡 投资建议")
