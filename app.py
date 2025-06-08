import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import re
import requests
import time
warnings.filterwarnings('ignore')

# 页面配置
st.set_page_config(
    page_title="📰 财经新闻智能分析系统",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化 session state
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None
if 'news_data' not in st.session_state:
    st.session_state.news_data = None

st.title("📰 财经新闻智能分析系统")
st.markdown("**实时财经新闻 + 智能中文翻译 + 情绪分析 + 投资建议**")
st.markdown("---")

# ==================== 翻译和分析函数 ====================

def comprehensive_translate(text):
    """综合翻译：句型+词汇翻译"""
    if not text:
        return text
    
    # 先进行句型翻译
    sentence_patterns = {
        # 新闻开头常见句型
        r'(\w+)\s+announced\s+that': r'\1宣布',
        r'(\w+)\s+reported\s+that': r'\1报告称',
        r'(\w+)\s+said\s+that': r'\1表示',
        r'(\w+)\s+revealed\s+that': r'\1透露',
        r'(\w+)\s+disclosed\s+that': r'\1披露',
        r'(\w+)\s+confirmed\s+that': r'\1确认',
        r'according\s+to\s+(\w+)': r'据\1',
        
        # 财报相关句型
        r'(\w+)\s+posted\s+(\w+)\s+earnings': r'\1公布了\2财报',
        r'(\w+)\s+beat\s+earnings\s+expectations': r'\1财报超预期',
        r'(\w+)\s+missed\s+earnings\s+expectations': r'\1财报不及预期',
        r'(\w+)\s+reported\s+revenue\s+of\s+\$([0-9.]+)\s+billion': r'\1报告营收\2十亿美元',
        r'(\w+)\s+reported\s+revenue\s+of\s+\$([0-9.]+)\s+million': r'\1报告营收\2百万美元',
        r'revenue\s+increased\s+by\s+([0-9.]+)%': r'营收增长\1%',
        r'revenue\s+decreased\s+by\s+([0-9.]+)%': r'营收下降\1%',
        
        # 股价相关句型
        r'(\w+)\s+shares\s+rose\s+([0-9.]+)%': r'\1股价上涨\2%',
        r'(\w+)\s+shares\s+fell\s+([0-9.]+)%': r'\1股价下跌\2%',
        r'(\w+)\s+shares\s+gained\s+([0-9.]+)%': r'\1股价上涨\2%',
        r'(\w+)\s+shares\s+dropped\s+([0-9.]+)%': r'\1股价下跌\2%',
        r'shares\s+closed\s+at\s+\$([0-9.]+)': r'股价收于\1美元',
        
        # 公司行动句型
        r'(\w+)\s+will\s+acquire\s+(\w+)': r'\1将收购\2',
        r'(\w+)\s+acquired\s+(\w+)': r'\1收购了\2',
        r'(\w+)\s+launched\s+a?\s*new\s+(\w+)': r'\1推出新\2',
        r'(\w+)\s+introduced\s+(\w+)': r'\1推出\2',
        r'(\w+)\s+unveiled\s+(\w+)': r'\1发布\2',
        r'(\w+)\s+plans\s+to\s+(\w+)': r'\1计划\2',
        r'(\w+)\s+expects\s+to\s+(\w+)': r'\1预计将\2',
        r'(\w+)\s+is\s+expected\s+to\s+(\w+)': r'\1预计将\2',
        
        # 时间表达
        r'this\s+quarter': '本季度',
        r'last\s+quarter': '上季度',
        r'this\s+year': '今年',
        r'last\s+year': '去年',
        r'compared\s+to\s+last\s+year': '与去年相比',
        r'year-over-year': '同比',
        
        # 常见短语
        r'beat\s+expectations': '超预期',
        r'missed\s+expectations': '不及预期',
        r'better\s+than\s+expected': '好于预期',
        r'record\s+high': '历史新高',
        r'all-time\s+high': '历史最高',
        
        # 数字表达
        r'\$([0-9.]+)\s+billion': r'\1十亿美元',
        r'\$([0-9.]+)\s+million': r'\1百万美元',
        r'([0-9.]+)\s+billion': r'\1十亿',
        r'([0-9.]+)\s+million': r'\1百万',
        
        # 行业术语
        r'artificial\s+intelligence': '人工智能',
        r'machine\s+learning': '机器学习',
        r'cloud\s+computing': '云计算',
        r'electric\s+vehicles?': '电动汽车',
        r'renewable\s+energy': '可再生能源',
    }
    
    result = text
    
    # 应用句型翻译
    for pattern, replacement in sentence_patterns.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    # 然后应用基础词汇翻译
    result = basic_financial_translate(result)
    
    return result

def basic_financial_translate(text):
    """基础财经术语翻译"""
    if not text:
        return text
    
    financial_dict = {
        # 公司名称
        'Apple Inc': '苹果公司',
        'Apple': '苹果公司',
        'Tesla Inc': '特斯拉公司', 
        'Tesla': '特斯拉公司',
        'Microsoft Corporation': '微软公司',
        'Microsoft': '微软公司',
        'Amazon.com Inc': '亚马逊公司',
        'Amazon': '亚马逊公司',
        'Google': '谷歌',
        'Meta': 'Meta公司',
        'NVIDIA': '英伟达',
        'Netflix': '奈飞',
        'Facebook': '脸书',
        
        # 股票代码
        'AAPL': '苹果(AAPL)',
        'TSLA': '特斯拉(TSLA)',
        'MSFT': '微软(MSFT)',
        'AMZN': '亚马逊(AMZN)',
        'GOOGL': '谷歌(GOOGL)',
        'META': 'Meta(META)',
        'NVDA': '英伟达(NVDA)',
        'NFLX': '奈飞(NFLX)',
        
        # 财经术语
        'earnings report': '财报',
        'quarterly earnings': '季度财报',
        'revenue': '营收',
        'profit': '利润',
        'loss': '亏损',
        'dividend': '分红',
        'stock price': '股价',
        'market cap': '市值',
        'investment': '投资',
        'investor': '投资者',
        'shareholder': '股东',
        'CEO': '首席执行官',
        'CFO': '首席财务官',
        
        # 基础词汇
        'technology': '科技',
        'artificial intelligence': '人工智能',
        'AI': '人工智能',
        'semiconductor': '半导体',
        'electric vehicle': '电动汽车',
        'cloud computing': '云计算',
        'e-commerce': '电子商务',
        'streaming': '流媒体',
        
        # 数值表达
        'billion': '十亿',
        'million': '百万',
        'percent': '百分比',
        
        # 市场动作
        'announced': '宣布',
        'reported': '报告',
        'released': '发布',
        'launched': '推出',
        'acquired': '收购',
        'merged': '合并',
        
        # 其他常用词
        'growth': '增长',
        'decline': '下降',
        'increase': '增加',
        'decrease': '减少',
        'performance': '表现',
        'results': '结果',
        'forecast': '预测',
        'outlook': '展望',
        'guidance': '指导',
        'target': '目标',
        
        # 完整句式
        'said in a statement': '在声明中表示',
        'according to': '据',
        'is expected to': '预计将',
        'announced today': '今日宣布',
        'shares rose': '股价上涨',
        'shares fell': '股价下跌',
        'revenue growth': '营收增长',
        'net income': '净利润',
        'cash flow': '现金流',
        'market value': '市值',
        'stock market': '股市',
        'board of directors': '董事会',
        'supply chain': '供应链',
        'research and development': '研发',
        'initial public offering': '首次公开募股',
        'mergers and acquisitions': '并购',
    }
    
    result = text
    for en, zh in financial_dict.items():
        pattern = r'\b' + re.escape(en) + r'\b'
        result = re.sub(pattern, zh, result, flags=re.IGNORECASE)
    
    return result

def translate_with_google_alternative(text):
    """使用Google翻译的替代接口（快速版本）"""
    try:
        url = "https://translate.google.cn/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': 'en',
            'tl': 'zh',
            'dt': 't',
            'q': text[:500]
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=3)
        if response.status_code == 200:
            result = response.json()
            if result and len(result) > 0 and result[0]:
                translated_parts = []
                for item in result[0]:
                    if item and len(item) > 0 and item[0]:
                        translated_parts.append(item[0])
                if translated_parts:
                    return ''.join(translated_parts)
    except:
        pass
    return None

def smart_translate(text):
    """智能翻译：优先使用综合翻译，短文本尝试在线翻译"""
    if not text or len(text.strip()) < 3:
        return text
    
    # 使用综合翻译
    translated = comprehensive_translate(text)
    
    # 如果翻译效果还是不够好，尝试在线翻译（仅限短文本）
    if len(text) < 200 and translated == text:
        try:
            online_result = translate_with_google_alternative(text)
            if online_result and len(online_result.strip()) > 5:
                return online_result
        except:
            pass
    
    return translated

def extract_keywords_from_text(text):
    """从文本中提取财经关键词"""
    if not text:
        return []
    
    text_lower = text.lower()
    
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
            "action": "建议关注相关概念股，适当增加仓位",
            "color": "green"
        }
    elif sentiment == "利空":
        return {
            "icon": "📉", 
            "advice": "风险因素，建议谨慎操作",
            "action": "降低风险敞口，关注防御性板块",
            "color": "red"
        }
    else:
        return {
            "icon": "📊",
            "advice": "中性影响，维持现有策略",
            "action": "密切关注后续发展，保持灵活操作",
            "color": "gray"
        }

# ==================== 新闻获取函数 ====================

def debug_yfinance_news(ticker):
    """调试 yfinance 新闻获取"""
    debug_info = {
        'ticker': ticker,
        'success': False,
        'error': None,
        'news_count': 0,
        'news_structure': None
    }
    
    try:
        stock = yf.Ticker(ticker)
        debug_info['stock_created'] = True
        
        # 获取基本信息验证连接
        info = stock.info
        debug_info['info_available'] = bool(info)
        debug_info['company_name'] = info.get('longName', 'N/A')
        
        # 获取新闻
        news = stock.news
        debug_info['news_type'] = str(type(news))
        
        if news:
            debug_info['news_count'] = len(news) if hasattr(news, '__len__') else 0
            if len(news) > 0:
                debug_info['success'] = True
                debug_info['first_news_keys'] = list(news[0].keys()) if isinstance(news[0], dict) else 'Not dict'
                # 检查第一条新闻的结构
                first_news = news[0]
                debug_info['news_structure'] = {
                    'has_title': 'title' in first_news if isinstance(first_news, dict) else False,
                    'has_summary': any(key in first_news for key in ['summary', 'description']) if isinstance(first_news, dict) else False,
                    'has_link': any(key in first_news for key in ['link', 'url']) if isinstance(first_news, dict) else False,
                    'keys': list(first_news.keys()) if isinstance(first_news, dict) else []
                }
    except Exception as e:
        debug_info['error'] = str(e)
    
    return debug_info

@st.cache_data(ttl=1800)  # 缓存30分钟
def fetch_financial_news(target_ticker=None, debug_mode=False):
    """获取真实财经新闻"""
    current_time = datetime.now()
    news_data = []
    debug_results = []
    
    # 如果开启调试模式，先进行调试
    if debug_mode and target_ticker:
        debug_info = debug_yfinance_news(target_ticker)
        debug_results.append(debug_info)
        st.sidebar.write("🔍 调试信息:", debug_info)
    
    try:
        # 获取目标股票新闻
        if target_ticker:
            try:
                ticker_obj = yf.Ticker(target_ticker)
                
                # 尝试多种方式获取新闻
                news = None
                try:
                    news = ticker_obj.news
                except Exception as e1:
                    st.sidebar.warning(f"方法1失败: {str(e1)}")
                    try:
                        # 备选方法：直接调用
                        news = getattr(ticker_obj, 'news', None)
                    except Exception as e2:
                        st.sidebar.warning(f"方法2失败: {str(e2)}")
                
                    st.sidebar.success(f"✅ 成功获取 {target_ticker} 新闻: {len(news)} 条")
                    
                    for i, article in enumerate(news[:8]):
                        try:
                            # 更强健的数据结构处理
                            content = article if isinstance(article, dict) else {}
                            
                            # 多种方式获取标题
                            title = (content.get('title', '') or 
                                   content.get('headline', '') or 
                                   content.get('shortName', '') or
                                   content.get('longName', ''))
                            
                            # 多种方式获取摘要
                            summary = (content.get('summary', '') or 
                                     content.get('description', '') or 
                                     content.get('snippet', '') or
                                     content.get('content', ''))
                            
                            # 获取链接 - 更全面的尝试
                            link = ''
                            for url_key in ['link', 'url', 'clickThroughUrl', 'canonicalUrl']:
                                if url_key in content:
                                    url_val = content[url_key]
                                    if isinstance(url_val, dict):
                                        link = url_val.get('url', '')
                                    elif isinstance(url_val, str):
                                        link = url_val
                                    if link:
                                        break
                            
                            # 获取发布者
                            publisher = 'Unknown'
                            if 'provider' in content and isinstance(content['provider'], dict):
                                publisher = content['provider'].get('displayName', 'Unknown')
                            else:
                                publisher = content.get('publisher', content.get('source', 'Unknown'))
                            
                            # 时间处理 - 更强健
                            published_time = current_time - timedelta(hours=i+1)
                            
                            # 尝试多个时间字段
                            time_fields = ['providerPublishTime', 'pubDate', 'displayTime', 'publishedAt']
                            for time_field in time_fields:
                                if time_field in content and content[time_field]:
                                    try:
                                        time_val = content[time_field]
                                        if isinstance(time_val, (int, float)):
                                            published_time = datetime.fromtimestamp(time_val)
                                        elif isinstance(time_val, str):
                                            if 'T' in time_val and 'Z' in time_val:
                                                published_time = datetime.fromisoformat(time_val.replace('Z', '+00:00')).replace(tzinfo=None)
                                        break
                                    except:
                                        continue
                            
                            if title and len(title.strip()) > 5:
                                # 翻译处理
                                try:
                                    translated_title = smart_translate(title)
                                    if summary and len(summary.strip()) > 10:
                                        if len(summary) > 400:
                                            summary = summary[:400] + "..."
                                        translated_summary = smart_translate(summary)
                                    else:
                                        translated_summary = '暂无摘要'
                                except Exception as e:
                                    translated_title = basic_financial_translate(title)
                                    translated_summary = basic_financial_translate(summary) if summary else '暂无摘要'
                                
                                # 关键词和情绪分析
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
                                    "is_real": True,
                                    "ticker": target_ticker
                                }
                                news_data.append(news_item)
                        except Exception as e:
                            if debug_mode:
                                st.sidebar.error(f"处理第{i+1}条新闻失败: {str(e)}")
                            continue
                else:
                    st.sidebar.warning(f"⚠️ {target_ticker} 返回的新闻为空")
                    
            except Exception as e:
                error_msg = f"获取 {target_ticker} 新闻时出错: {str(e)}"
                st.sidebar.error(error_msg)
                if debug_mode:
                    st.sidebar.write("详细错误信息:", str(e))
        # 获取市场整体新闻 - 简化版本，优先保证基本功能
        if len(news_data) < 3:  # 如果个股新闻不足，补充市场新闻
            try:
                market_indices = ["^GSPC", "^IXIC"]  # 减少指数数量，提高成功率
                for index_symbol in market_indices:
                    try:
                        index_ticker = yf.Ticker(index_symbol)
                        index_news = getattr(index_ticker, 'news', [])
                        
                        if index_news and len(index_news) > 0:
                            st.sidebar.info(f"✅ 获取到 {index_symbol} 市场新闻: {len(index_news)} 条")
                            
                            for j, article in enumerate(index_news[:2]):  # 每个指数只取2条
                                try:
                                    content = article if isinstance(article, dict) else {}
                                    
                                    title = (content.get('title', '') or 
                                           content.get('headline', '') or 
                                           f"市场新闻 {j+1}")
                                    
                                    summary = (content.get('summary', '') or 
                                             content.get('description', '') or 
                                             content.get('snippet', '') or
                                             '市场相关新闻摘要')
                                    
                                    # 避免重复新闻
                                    if not any(existing['title'] == title for existing in news_data):
                                        try:
                                            translated_title = smart_translate(title)
                                            translated_summary = smart_translate(summary) if len(summary) > 10 else '市场新闻摘要'
                                        except:
                                            translated_title = basic_financial_translate(title)
                                            translated_summary = basic_financial_translate(summary) if summary else '市场新闻摘要'
                                        
                                        title_summary = title + ' ' + (summary or '')
                                        keywords = extract_keywords_from_text(title_summary)
                                        sentiment = analyze_sentiment_from_keywords(keywords)
                                        
                                        news_item = {
                                            "title": translated_title,
                                            "summary": translated_summary[:300] + '...' if len(translated_summary) > 300 else translated_summary,
                                            "published": current_time - timedelta(hours=len(news_data)+1),
                                            "url": '',
                                            "source": f"{index_symbol} Market News",
                                            "category": "market_wide",
                                            "keywords": keywords,
                                            "sentiment": sentiment,
                                            "is_real": True,
                                            "ticker": index_symbol
                                        }
                                        news_data.append(news_item)
                                except Exception as e:
                                    if debug_mode:
                                        st.sidebar.error(f"处理市场新闻失败: {str(e)}")
                                    continue
                        else:
                            st.sidebar.warning(f"⚠️ {index_symbol} 无市场新闻")
                    except Exception as e:
                        if debug_mode:
                            st.sidebar.error(f"获取 {index_symbol} 失败: {str(e)}")
                        continue
            except Exception as e:
                if debug_mode:
                    st.sidebar.error(f"市场新闻获取整体失败: {str(e)}")
        
        # 按时间排序
        news_data.sort(key=lambda x: x.get('published', datetime.now()), reverse=True)
        
        # 如果仍然没有新闻，检查网络连接并提供备选方案
        if len(news_data) == 0:
            # 尝试简单的网络测试
            try:
                import requests
                response = requests.get('https://finance.yahoo.com', timeout=5)
                if response.status_code == 200:
                    connection_status = "网络连接正常，可能是API限制"
                else:
                    connection_status = f"网络响应异常: {response.status_code}"
            except:
                connection_status = "网络连接可能存在问题"
            
            return [{
                "title": "新闻获取服务暂时不可用",
                "summary": f"技术诊断: {connection_status}。建议: 1) 检查网络连接 2) 稍后重试 3) 访问Yahoo Finance、Bloomberg等网站获取最新信息",
                "published": current_time,
                "url": "https://finance.yahoo.com",
                "source": "系统诊断",
                "category": "system_info",
                "keywords": ["系统", "网络", "诊断"],
                "sentiment": "中性",
                "is_real": False,
                "ticker": ""
            }]
        
        st.sidebar.success(f"✅ 成功获取 {len(news_data)} 条新闻")
        return news_data
        
    except Exception as e:
        error_details = f"新闻获取系统错误: {str(e)}"
        st.sidebar.error(error_details)
        
        return [{
            "title": "系统错误 - 新闻服务暂时不可用",
            "summary": f"错误详情: {error_details}。请稍后重试或联系技术支持。",
            "published": datetime.now(),
            "url": "",
            "source": "系统错误",
            "category": "system_error",
            "keywords": ["系统", "错误"],
            "sentiment": "中性",
            "is_real": False,
            "ticker": ""
        }]

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("📰 新闻分析设置")
    
    # 股票选择
    popular_stocks = {
        "市场综合新闻": "",
        "Apple (AAPL)": "AAPL",
        "Microsoft (MSFT)": "MSFT", 
        "Tesla (TSLA)": "TSLA",
        "Amazon (AMZN)": "AMZN",
        "Google (GOOGL)": "GOOGL",
        "Meta (META)": "META",
        "NVIDIA (NVDA)": "NVDA",
        "Netflix (NFLX)": "NFLX"
    }
    
    selected_stock = st.selectbox(
        "选择关注股票:",
        options=list(popular_stocks.keys()),
        index=0
    )
    
    # 或者手动输入股票代码
    manual_ticker = st.text_input(
        "或输入股票代码:",
        placeholder="例如: AAPL, TSLA, MSFT"
    ).upper()
    
    # 确定要分析的股票
    if manual_ticker:
        ticker = manual_ticker
    else:
        ticker = popular_stocks[selected_stock]
    
    # 新闻筛选选项
    st.markdown("---")
    st.subheader("🔍 新闻筛选")
    
    sentiment_filter = st.selectbox(
        "情绪筛选:",
        ["全部", "利好", "利空", "中性"]
    )
    
    time_filter = st.selectbox(
        "时间筛选:",
        ["全部", "今日", "近3天", "一周内"]
    )
    
    keyword_filter = st.multiselect(
        "关键词筛选:",
        ["科技", "金融", "能源", "上涨", "下跌", "利率", "通胀", "政策", "经济增长", "市场"]
    )
    
    # 调试模式选项
    st.markdown("---")
    st.subheader("🔧 高级选项")
    
    debug_mode = st.checkbox("🐛 启用调试模式", help="显示详细的错误信息和API调用状态")
    
    if debug_mode:
        st.info("调试模式已启用，将显示详细诊断信息")
    
    # 获取新闻按钮
    if st.button("🔍 获取最新新闻", type="primary"):
        st.session_state.selected_ticker = ticker
        with st.spinner("正在获取最新财经新闻..."):
            news_data = fetch_financial_news(ticker if ticker else None, debug_mode=debug_mode)
            st.session_state.news_data = news_data
    
    # 清除缓存按钮
    if st.button("🔄 刷新新闻"):
        fetch_financial_news.clear()
        st.session_state.news_data = None
        st.success("缓存已清除，请重新获取新闻")
        st.rerun()
    
    # 网络诊断工具
    if st.button("🌐 网络诊断"):
        with st.spinner("正在诊断网络连接..."):
            try:
                import requests
                
                # 测试主要财经网站连接
                test_sites = [
                    ("Yahoo Finance", "https://finance.yahoo.com"),
                    ("Google", "https://www.google.com"),
                    ("YFinance API", "https://query1.finance.yahoo.com")
                ]
                
                results = []
                for name, url in test_sites:
                    try:
                        response = requests.get(url, timeout=5)
                        if response.status_code == 200:
                            results.append(f"✅ {name}: 连接正常")
                        else:
                            results.append(f"⚠️ {name}: HTTP {response.status_code}")
                    except Exception as e:
                        results.append(f"❌ {name}: {str(e)}")
                
                for result in results:
                    st.write(result)
                    
            except Exception as e:
                st.error(f"诊断工具出错: {str(e)}")
    
    st.markdown("---")
    st.markdown("### 📊 使用说明")
    st.markdown("""
    **功能特色:**
    - 🔄 实时获取Yahoo Finance新闻
    - 🌐 智能中文翻译
    - 🎯 关键词提取
    - 📈 情绪分析
    - 💡 投资建议
    
    **使用步骤:**
    1. 选择关注股票或输入代码
    2. 设置筛选条件
    3. 点击获取最新新闻
    4. 查看分析结果
    """)

# ==================== 主界面 ====================
if st.session_state.news_data is not None:
    news_data = st.session_state.news_data
    
    # 应用筛选条件
    filtered_news = news_data.copy()
    
    # 情绪筛选
    if sentiment_filter != "全部":
        filtered_news = [news for news in filtered_news if news['sentiment'] == sentiment_filter]
    
    # 时间筛选
    if time_filter != "全部":
        now = datetime.now()
        if time_filter == "今日":
            filtered_news = [news for news in filtered_news if news['published'].date() == now.date()]
        elif time_filter == "近3天":
            filtered_news = [news for news in filtered_news if (now - news['published']).days <= 3]
        elif time_filter == "一周内":
            filtered_news = [news for news in filtered_news if (now - news['published']).days <= 7]
    
    # 关键词筛选
    if keyword_filter:
        filtered_news = [news for news in filtered_news if any(kw in news['keywords'] for kw in keyword_filter)]
    
    # 显示统计信息
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_news = len(filtered_news)
        st.metric("📰 新闻总数", total_news)
    
    with col2:
        bullish_count = len([n for n in filtered_news if n['sentiment'] == '利好'])
        st.metric("📈 利好新闻", bullish_count, delta=f"{bullish_count/total_news*100:.0f}%" if total_news > 0 else "0%")
    
    with col3:
        bearish_count = len([n for n in filtered_news if n['sentiment'] == '利空'])
        st.metric("📉 利空新闻", bearish_count, delta=f"{bearish_count/total_news*100:.0f}%" if total_news > 0 else "0%")
    
    with col4:
        neutral_count = len([n for n in filtered_news if n['sentiment'] == '中性'])
        st.metric("📊 中性新闻", neutral_count, delta=f"{neutral_count/total_news*100:.0f}%" if total_news > 0 else "0%")
    
    # 情绪分析总结
    if total_news > 0:
        if bullish_count > bearish_count:
            overall_sentiment = "整体偏向利好"
            sentiment_color = "green"
            sentiment_icon = "📈"
        elif bearish_count > bullish_count:
            overall_sentiment = "整体偏向利空"
            sentiment_color = "red"
            sentiment_icon = "📉"
        else:
            overall_sentiment = "情绪相对平衡"
            sentiment_color = "gray"
            sentiment_icon = "📊"
        
        st.markdown(f"### {sentiment_icon} 市场情绪总结: <span style='color:{sentiment_color}'>{overall_sentiment}</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 显示新闻列表
    if len(filtered_news) > 0:
        st.subheader(f"📰 最新财经新闻 ({len(filtered_news)} 条)")
        
        for i, news in enumerate(filtered_news):
            # 获取情绪建议
            impact_info = get_market_impact_advice(news['sentiment'])
            
            with st.container():
                # 新闻卡片样式
                col_main, col_side = st.columns([3, 1])
                
                with col_main:
                    # 标题和时间
                    time_str = news['published'].strftime('%Y-%m-%d %H:%M')
                    if news['is_real']:
                        st.markdown(f"### 📰 {news['title']}")
                    else:
                        st.markdown(f"### ℹ️ {news['title']}")
                    
                    st.caption(f"🕒 {time_str} | 📰 {news['source']}")
                    
                    # 摘要
                    st.write(news['summary'])
                    
                    # 关键词
                    if news['keywords']:
                        keywords_str = " ".join([f"`{kw}`" for kw in news['keywords']])
                        st.markdown(f"**🔍 关键词:** {keywords_str}")
                    
                    # 链接
                    if news['url']:
                        st.markdown(f"🔗 [阅读原文]({news['url']})")
                
                with col_side:
                    # 情绪分析
                    sentiment_color = impact_info['color']
                    st.markdown(f"### {impact_info['icon']}")
                    st.markdown(f"**<span style='color:{sentiment_color}'>{news['sentiment']}</span>**", unsafe_allow_html=True)
                    
                    # 投资建议
                    st.write(f"**📋 影响:**")
                    st.write(impact_info['advice'])
                    
                    st.write(f"**💡 建议:**")
                    st.write(impact_info['action'])
                
                st.markdown("---")
    
    else:
        st.info("📭 根据当前筛选条件，暂无相关新闻")

else:
    # 欢迎页面
    st.markdown("""
    ## 🎯 功能介绍
    
    ### 📰 实时新闻获取
    - 📡 从Yahoo Finance获取最新财经新闻
    - 🎯 支持特定股票新闻和市场整体新闻
    - 🔄 自动更新，确保信息时效性
    
    ### 🌐 智能中文翻译
    - 📝 专业财经术语翻译
    - 🔤 英文句型结构转换
    - 🎯 上下文语境理解
    - 🚀 快速响应翻译
    
    ### 📊 情绪分析系统
    - 🔍 关键词自动提取
    - 📈 多维度情绪分析
    - 💡 投资影响评估
    - 🎯 操作建议生成
    
    ### 🔧 高级筛选功能
    - 😊 按情绪筛选 (利好/利空/中性)
    - 📅 按时间筛选 (今日/近期/一周)
    - 🏷️ 按关键词筛选
    - 📊 统计分析展示
    
    ---
    
    **👈 请在左侧选择股票并点击"获取最新新闻"开始使用**
    
    **⚠️ 免责声明:** 本系统仅供参考，不构成投资建议。投资有风险，决策需谨慎。
    """)
    
    # 示例展示
    with st.expander("🎬 功能演示"):
        st.markdown("""
        ### 📊 新闻展示示例
        
        **标题:** 苹果公司宣布新一代AI芯片技术突破
        
        **摘要:** 苹果公司在最新财报中透露，其自研的M4芯片在AI处理能力方面取得重大突破，预计将显著提升Mac和iPad产品的人工智能表现...
        
        **关键词:** `科技` `人工智能` `芯片` `上涨`
        
        **情绪分析:** 📈 利好
        
        **投资建议:** 积极因素，可关注相关板块机会。建议关注相关概念股，适当增加仓位。
        
        ---
        
        ### 🔍 智能翻译示例
        
        **原文:** "Apple announced that its Q3 revenue increased by 15% year-over-year, beating expectations."
        
        **智能翻译:** "苹果宣布其第三季度营收同比增长15%，超预期。"
        
        **关键词提取:** 苹果、营收增长、超预期、上涨
        
        **情绪判断:** 利好 → 推荐关注
        """)

# 页脚
st.markdown("---")
st.markdown("📰 财经新闻智能分析系统 | 🔄 实时新闻 | 🌐 智能翻译 | 📊 情绪分析 | 💡 投资建议")
