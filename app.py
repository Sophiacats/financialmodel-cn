import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
import hashlib
import random
import time
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
        import requests
        
        url = "https://translate.google.cn/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': 'en',
            'tl': 'zh',
            'dt': 't',
            'q': text[:500]
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0'
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
    """智能翻译：优先使用综合翻译"""
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
                    for i, article in enumerate(news[:8]):
                        try:
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
                            publisher = 'Unknown'
                            if 'provider' in content and content['provider']:
                                publisher = content['provider'].get('displayName', 'Unknown')
                            else:
                                publisher = content.get('publisher', '') or content.get('source', 'Unknown')
                            
                            # 获取时间
                            pub_date_str = content.get('pubDate', '') or content.get('displayTime', '')
                            if pub_date_str:
                                try:
                                    if 'T' in pub_date_str and 'Z' in pub_date_str:
                                        published_time = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
                                    else:
                                        published_time = current_time - timedelta(hours=i+1)
                                except:
                                    published_time = current_time - timedelta(hours=i+1)
                            else:
                                pub_time = content.get('providerPublishTime', None) or article.get('providerPublishTime', None)
                                if pub_time:
                                    try:
                                        published_time = datetime.fromtimestamp(pub_time)
                                    except:
                                        published_time = current_time - timedelta(hours=i+1)
                                else:
                                    published_time = current_time - timedelta(hours=i+1)
                            
                            if title and len(title.strip()) > 5:
                                # 翻译标题和摘要
                                try:
                                    translated_title = smart_translate(title)
                                    if summary and len(summary.strip()) > 10:
                                        if len(summary) > 400:
                                            summary = summary[:400] + "..."
                                        translated_summary = smart_translate(summary)
                                    else:
                                        translated_summary = '暂无摘要'
                                except:
                                    translated_title = basic_financial_translate(title)
                                    translated_summary = basic_financial_translate(summary) if summary else '暂无摘要'
                                
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
                        for j, article in enumerate(index_news[:3]):
                            try:
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
                                
                                if title and len(title.strip()) > 5:
                                    # 避免重复新闻
                                    if not any(existing['title'] == title for existing in news_data):
                                        try:
                                            translated_title = smart_translate(title)
                                            if summary and len(summary.strip()) > 10:
                                                if len(summary) > 400:
                                                    summary = summary[:400] + "..."
                                                translated_summary = smart_translate(summary)
                                            else:
                                                translated_summary = '暂无摘要'
                                        except:
                                            translated_title = basic_financial_translate(title)
                                            translated_summary = basic_financial_translate(summary) if summary else '暂无摘要'
                                        
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
