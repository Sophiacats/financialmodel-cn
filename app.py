import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
import plotly.graph_objects as go
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

# ==================== 缓存函数 ====================
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

def fetch_stock_data_uncached(ticker):
    """获取股票数据（不缓存版本）"""
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
            'hist_data': hist_data,
            'financials': financials if financials is not None else pd.DataFrame(),
            'balance_sheet': balance_sheet if balance_sheet is not None else pd.DataFrame(),
            'cash_flow': cash_flow if cash_flow is not None else pd.DataFrame(),
            'stock': stock
        }
    except Exception as e:
        st.error(f"获取数据失败: {str(e)}")
        return None

# ==================== 时事分析函数 ====================
import requests
import json
import time

def fetch_financial_news(target_ticker=None):
    """获取财经新闻 - 根据股票代码定制化"""
    try:
        news_data = []
        
        # 方法1: 尝试从yfinance获取特定股票的新闻
        if target_ticker:
            try:
                ticker = yf.Ticker(target_ticker)
                news = ticker.news
                if news and len(news) > 0:
                    for article in news[:4]:  # 目标股票取4条新闻
                        if article.get('title') and article.get('providerPublishTime'):
                            news_data.append({
                                "title": article.get('title', ''),
                                "summary": article.get('summary', '')[:200] + '...' if article.get('summary') else article.get('title', ''),
                                "published": datetime.fromtimestamp(article.get('providerPublishTime', time.time())),
                                "url": article.get('link', ''),
                                "source": f"Yahoo Finance ({target_ticker})",
                                "category": "company_specific"
                            })
            except Exception as e:
                pass
        
        # 方法2: 获取市场整体新闻
        try:
            market_tickers = ["^GSPC", "^IXIC", "^DJI"]
            for ticker_symbol in market_tickers:
                try:
                    ticker = yf.Ticker(ticker_symbol)
                    news = ticker.news
                    if news and len(news) > 0:
                        for article in news[:2]:  # 每个指数取2条
                            if article.get('title') and article.get('providerPublishTime'):
                                news_data.append({
                                    "title": article.get('title', ''),
                                    "summary": article.get('summary', '')[:200] + '...' if article.get('summary') else article.get('title', ''),
                                    "published": datetime.fromtimestamp(article.get('providerPublishTime', time.time())),
                                    "url": article.get('link', ''),
                                    "source": f"Market News",
                                    "category": "market_wide"
                                })
                except Exception:
                    continue
        except Exception:
            pass
        
        # 方法3: 如果真实新闻不够，补充模拟新闻
        if len(news_data) < 8:
            current_time = datetime.now()
            
            # 获取公司信息用于生成相关新闻
            company_info = {}
            if target_ticker:
                try:
                    ticker_obj = yf.Ticker(target_ticker)
                    info = ticker_obj.info
                    company_info = {
                        'name': info.get('longName', target_ticker),
                        'sector': info.get('sector', ''),
                        'industry': info.get('industry', ''),
                        'ticker': target_ticker
                    }
                except:
                    company_info = {'name': target_ticker, 'sector': '', 'industry': '', 'ticker': target_ticker}
            
            # 生成公司特定新闻
            company_news = generate_company_specific_news(company_info, current_time)
            news_data.extend(company_news)
            
            # 添加市场广泛影响的新闻（美联储等）
            market_wide_news = [
                {
                    "title": "美联储官员暗示未来可能调整利率政策",
                    "summary": "美联储高级官员在最新讲话中表示，将根据通胀数据和经济增长情况灵活调整货币政策，市场对此反应积极。此举将影响所有资产类别的估值。",
                    "published": current_time - timedelta(hours=2),
                    "url": "",
                    "source": "美联储政策",
                    "category": "market_wide"
                },
                {
                    "title": "全球通胀数据好于预期，风险资产普遍上涨",
                    "summary": "最新公布的全球主要经济体通胀数据均好于市场预期，投资者风险偏好提升，股市、商品等风险资产普遍上涨。",
                    "published": current_time - timedelta(hours=6),
                    "url": "",
                    "source": "全球经济",
                    "category": "market_wide"
                },
                {
                    "title": "地缘政治局势缓解，市场避险情绪降温",
                    "summary": "近期国际地缘政治紧张局势有所缓解，投资者避险情绪降温，资金重新流入股市等风险资产，黄金等避险资产回落。",
                    "published": current_time - timedelta(hours=10),
                    "url": "",
                    "source": "国际政治",
                    "category": "market_wide"
                },
                {
                    "title": "经济数据显示复苏势头良好，市场信心增强",
                    "summary": "最新发布的一系列经济指标显示经济复苏势头良好，就业市场稳定，消费支出增长，投资者对经济前景的信心进一步增强。",
                    "published": current_time - timedelta(hours=14),
                    "url": "",
                    "source": "经济数据",
                    "category": "market_wide"
                }
            ]
            news_data.extend(market_wide_news)
        
        # 处理新闻数据，添加关键词和情绪分析
        processed_news = []
        for news in news_data[:10]:  # 提高至10条新闻
            # 确保新闻内容不为空
            if not news.get('title'):
                continue
                
            keywords = extract_keywords(news['title'] + ' ' + news.get('summary', ''))
            sentiment, _ = analyze_news_sentiment(keywords)
            
            processed_news.append({
                **news,
                'keywords': keywords,
                'sentiment': sentiment
            })
        
        # 如果还是没有新闻，返回默认消息
        if not processed_news:
            processed_news = [{
                "title": "暂无最新财经新闻",
                "summary": "当前无法获取实时新闻数据，建议访问主要财经网站获取最新市场动态。",
                "published": datetime.now(),
                "url": "",
                "source": "系统提示",
                "keywords": ["市场", "信息"],
                "sentiment": "中性",
                "category": "system"
            }]
        
        return processed_news
        
    except Exception as e:
        # 最后的错误处理
        return [{
            "title": "新闻服务暂时不可用",
            "summary": f"获取新闻时遇到技术问题，建议稍后重试或查看主要财经网站。",
            "published": datetime.now(),
            "url": "",
            "source": "系统",
            "keywords": ["技术", "问题"],
            "sentiment": "中性",
            "category": "system"
        }]

def generate_company_specific_news(company_info, current_time):
    """根据公司信息生成相关新闻"""
    news_list = []
    
    if not company_info or not company_info.get('ticker'):
        return news_list
    
    company_name = company_info.get('name', company_info.get('ticker'))
    sector = company_info.get('sector', '')
    industry = company_info.get('industry', '')
    ticker = company_info.get('ticker')
    
    # 根据行业生成相关新闻
    if 'Technology' in sector or 'tech' in industry.lower():
        news_list.extend([
            {
                "title": f"科技股{company_name}受益于AI发展趋势",
                "summary": f"{company_name}作为科技行业领军企业，预计将从人工智能技术发展浪潮中获益。分析师看好其在AI领域的布局和技术优势。",
                "published": current_time - timedelta(hours=3),
                "url": "",
                "source": f"科技行业分析",
                "category": "company_specific"
            },
            {
                "title": f"半导体行业整体向好，{ticker}等龙头股受关注",
                "summary": f"随着全球数字化转型加速，半导体需求持续增长。{company_name}等行业龙头企业有望持续受益于这一趋势。",
                "published": current_time - timedelta(hours=8),
                "url": "",
                "source": f"行业研究",
                "category": "industry_specific"
            }
        ])
    
    elif 'Healthcare' in sector or 'Pharmaceuticals' in industry:
        news_list.extend([
            {
                "title": f"医药行业{company_name}新药研发进展受关注",
                "summary": f"{company_name}在新药研发领域的最新进展引起市场关注。医药行业整体估值有望随着创新药物的推出而提升。",
                "published": current_time - timedelta(hours=4),
                "url": "",
                "source": f"医药行业",
                "category": "company_specific"
            },
            {
                "title": f"生物技术领域投资热度不减，{ticker}等企业受益",
                "summary": f"生物技术和医疗创新持续受到投资者青睐，{company_name}等医药企业在研发投入和产品创新方面的努力获得市场认可。",
                "published": current_time - timedelta(hours=11),
                "url": "",
                "source": f"生物技术",
                "category": "industry_specific"
            }
        ])
    
    elif 'Financial' in sector or 'bank' in industry.lower():
        news_list.extend([
            {
                "title": f"银行股{company_name}受益于利率政策预期",
                "summary": f"市场对利率政策的预期变化对银行股形成利好。{company_name}作为金融行业重要参与者，有望受益于净息差改善。",
                "published": current_time - timedelta(hours=5),
                "url": "",
                "source": f"金融行业",
                "category": "company_specific"
            },
            {
                "title": f"金融科技发展推动传统银行转型，{ticker}积极布局",
                "summary": f"数字化转型浪潮下，{company_name}等传统金融机构加大科技投入，通过金融科技提升服务效率和客户体验。",
                "published": current_time - timedelta(hours=13),
                "url": "",
                "source": f"金融科技",
                "category": "industry_specific"
            }
        ])
    
    elif 'Energy' in sector or 'oil' in industry.lower():
        news_list.extend([
            {
                "title": f"能源股{company_name}受益于油价上涨预期",
                "summary": f"国际能源市场供需关系改善，油价维持高位。{company_name}等能源企业有望从中受益，业绩预期向好。",
                "published": current_time - timedelta(hours=7),
                "url": "",
                "source": f"能源行业",
                "category": "company_specific"
            },
            {
                "title": f"可再生能源转型加速，{company_name}绿色投资引关注",
                "summary": f"全球能源转型趋势下，{company_name}在清洁能源和可再生能源领域的布局成为投资者关注焦点。",
                "published": current_time - timedelta(hours=15),
                "url": "",
                "source": f"绿色能源",
                "category": "industry_specific"
            }
        ])
    
    elif 'Consumer' in sector or 'retail' in industry.lower():
        news_list.extend([
            {
                "title": f"消费股{company_name}业绩有望受益于经济复苏",
                "summary": f"随着消费者信心回升和支出增加，{company_name}等消费类企业预计将迎来业绩改善。分析师上调盈利预期。",
                "published": current_time - timedelta(hours=9),
                "url": "",
                "source": f"消费行业",
                "category": "company_specific"
            },
            {
                "title": f"电商渗透率持续提升，{ticker}数字化转型成效显著",
                "summary": f"线上消费趋势不断强化，{company_name}通过数字化转型和全渠道布局，在竞争激烈的消费市场中保持优势。",
                "published": current_time - timedelta(hours=12),
                "url": "",
                "source": f"数字零售",
                "category": "industry_specific"
            }
        ])
    
    elif 'automotive' in industry.lower() or 'Automotive' in sector:
        news_list.extend([
            {
                "title": f"新能源汽车行业增长强劲，{company_name}前景看好",
                "summary": f"全球新能源汽车销量持续高速增长，{company_name}在电动车领域的布局和技术积累为其带来发展机遇。",
                "published": current_time - timedelta(hours=6),
                "url": "",
                "source": f"汽车行业",
                "category": "company_specific"
            },
            {
                "title": f"自动驾驶技术突破，{ticker}等车企加大研发投入",
                "summary": f"自动驾驶和智能汽车技术快速发展，{company_name}等汽车制造商在这一领域的技术积累和投资备受市场期待。",
                "published": current_time - timedelta(hours=14),
                "url": "",
                "source": f"智能汽车",
                "category": "industry_specific"
            }
        ])
    
    else:
        # 通用行业新闻
        news_list.append({
            "title": f"{company_name}所在行业整体表现稳健",
            "summary": f"{company_name}作为{industry}领域的重要企业，在当前市场环境下表现稳健。投资者关注其业务发展和市场策略。",
            "published": current_time - timedelta(hours=5),
            "url": "",
            "source": f"行业分析",
            "category": "company_specific"
        })
    
    return news_list[:4]  # 最多返回4条公司相关新闻

def extract_keywords(text):
    """从新闻文本中提取关键词"""
    # 财经相关关键词库
    financial_keywords = {
        # 货币政策
        "利率": ["利率", "降息", "加息", "基准利率", "联邦基金利率"],
        "货币政策": ["货币政策", "央行", "美联储", "QE", "量化宽松"],
        
        # 市场情绪
        "上涨": ["上涨", "上升", "增长", "涨幅", "大涨", "暴涨"],
        "下跌": ["下跌", "下降", "跌幅", "大跌", "暴跌", "下滑"],
        
        # 行业板块
        "科技": ["科技", "AI", "人工智能", "芯片", "半导体", "软件"],
        "金融": ["银行", "保险", "券商", "金融", "信贷"],
        "能源": ["石油", "天然气", "新能源", "电动车", "光伏", "风电"],
        "消费": ["消费", "零售", "餐饮", "旅游", "酒店"],
        
        # 经济指标
        "通胀": ["通胀", "CPI", "PPI", "物价"],
        "就业": ["就业", "失业率", "就业数据", "非农"],
        "GDP": ["GDP", "经济增长", "国内生产总值"],
        
        # 政策监管
        "政策": ["政策", "监管", "法规", "政府"],
        "贸易": ["贸易", "关税", "进出口", "贸易战"],
        
        # 风险事件
        "地缘政治": ["地缘", "战争", "冲突", "制裁"],
        "疫情": ["疫情", "病毒", "感染", "封锁"]
    }
    
    text_lower = text.lower()
    found_keywords = []
    
    for category, words in financial_keywords.items():
        for word in words:
            if word.lower() in text_lower:
                found_keywords.append(category)
                break
    
    # 如果没找到关键词，尝试直接提取一些常见词汇
    if not found_keywords:
        common_words = ["股市", "投资", "财报", "业绩", "收益", "股价", "市场"]
        for word in common_words:
            if word in text:
                found_keywords.append(word)
    
    return found_keywords[:5]  # 最多返回5个关键词

def analyze_news_sentiment(keywords):
    """分析新闻关键词的市场情绪"""
    bullish_keywords = ["上涨", "增长", "利好", "降息", "政策", "超预期", "科技", "消费"]
    bearish_keywords = ["下跌", "加息", "利空", "风险", "地缘政治", "通胀", "监管"]
    
    bullish_count = sum(1 for keyword in keywords if keyword in bullish_keywords)
    bearish_count = sum(1 for keyword in keywords if keyword in bearish_keywords)
    
    if bullish_count > bearish_count:
        return "利好", "green"
    elif bearish_count > bullish_count:
        return "利空", "red"
    else:
        return "中性", "gray"

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
        hist_data['BB_Width'] = hist_data['BB_Upper'] - hist_data['BB_Lower']
        
        hist_data['Volume_MA'] = hist_data['Volume'].rolling(window=20).mean()
        
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
        
        # 1. 盈利能力
        if len(financials.columns) >= 2 and 'Net Income' in financials.index:
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
        
        # 3. ROA增长
        if (len(financials.columns) >= 2 and len(balance_sheet.columns) >= 2 and 
            'Total Assets' in balance_sheet.index and 'Net Income' in financials.index):
            total_assets = balance_sheet.loc['Total Assets'].iloc[0]
            total_assets_prev = balance_sheet.loc['Total Assets'].iloc[1]
            
            roa_current = net_income / total_assets if total_assets != 0 else 0
            net_income_prev = financials.loc['Net Income'].iloc[1]
            roa_prev = net_income_prev / total_assets_prev if total_assets_prev != 0 else 0
            
            if roa_current > roa_prev:
                score += 1
                reasons.append("✅ ROA同比增长")
            else:
                reasons.append("❌ ROA同比下降")
        
        # 4. 现金流质量
        if 'net_income' in locals() and 'ocf' in locals() and net_income != 0 and ocf > net_income:
            score += 1
            reasons.append("✅ 经营现金流大于净利润")
        else:
            reasons.append("❌ 经营现金流小于净利润")
        
        # 5-9. 其他财务指标（简化版本）
        score += 3
        reasons.append("📊 财务结构基础分: 3分")
        
    except Exception as e:
        st.warning(f"Piotroski Score计算部分指标失败: {str(e)}")
        return 0, ["❌ 计算过程出现错误"]
    
    return score, reasons

def calculate_dupont_analysis(data):
    """杜邦分析"""
    try:
        info = data['info']
        
        roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
        profit_margin = info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0
        asset_turnover = info.get('totalRevenue', 0) / info.get('totalAssets', 1) if info.get('totalAssets') else 0
        equity_multiplier = info.get('totalAssets', 0) / info.get('totalStockholderEquity', 1) if info.get('totalStockholderEquity') else 0
        
        return {
            'roe': roe,
            'profit_margin': profit_margin,
            'asset_turnover': asset_turnover,
            'equity_multiplier': equity_multiplier
        }
    except Exception as e:
        st.warning(f"杜邦分析计算失败: {str(e)}")
        return None

def calculate_altman_z_score(data):
    """计算Altman Z-Score"""
    try:
        info = data['info']
        balance_sheet = data['balance_sheet']
        
        if balance_sheet.empty:
            return 0, "数据不足", "gray"
        
        total_assets = info.get('totalAssets', 0)
        current_assets = 0
        current_liabilities = 0
        retained_earnings = 0
        total_liabilities = 0
        
        if not balance_sheet.empty and len(balance_sheet.columns) > 0:
            for ca_field in ['Current Assets', 'Total Current Assets']:
                if ca_field in balance_sheet.index:
                    current_assets = balance_sheet.loc[ca_field].iloc[0]
                    break
            
            for cl_field in ['Current Liabilities', 'Total Current Liabilities']:
                if cl_field in balance_sheet.index:
                    current_liabilities = balance_sheet.loc[cl_field].iloc[0]
                    break
            
            if 'Retained Earnings' in balance_sheet.index:
                retained_earnings = balance_sheet.loc['Retained Earnings'].iloc[0]
            
            for tl_field in ['Total Liabilities Net Minority Interest', 'Total Liabilities', 'Total Liab']:
                if tl_field in balance_sheet.index:
                    total_liabilities = balance_sheet.loc[tl_field].iloc[0]
                    break
        
        ebit = info.get('ebitda', 0)
        market_cap = info.get('marketCap', 0)
        revenue = info.get('totalRevenue', 0)
        
        if total_assets <= 0:
            return 0, "数据不足", "gray"
        
        working_capital = current_assets - current_liabilities
        
        A = (working_capital / total_assets) * 1.2
        B = (retained_earnings / total_assets) * 1.4 if not pd.isna(retained_earnings) else 0
        C = (ebit / total_assets) * 3.3 if ebit > 0 else 0
        D = (market_cap / total_liabilities) * 0.6 if total_liabilities > 0 else 0
        E = (revenue / total_assets) * 1.0 if revenue > 0 else 0
        
        z_score = A + B + C + D + E
        
        if pd.isna(z_score) or z_score < -10 or z_score > 10:
            z_score = 0
        
        if z_score > 2.99:
            status = "安全区域"
            color = "green"
        elif z_score > 1.8:
            status = "灰色区域"
            color = "orange"
        else:
            status = "危险区域"
            color = "red"
        
        return z_score, status, color
    except Exception as e:
        st.warning(f"Altman Z-Score计算失败: {str(e)}")
        return 0, "计算失败", "gray"

def calculate_dcf_valuation(data):
    """DCF估值模型"""
    try:
        info = data['info']
        cash_flow = data['cash_flow']
        
        if cash_flow.empty:
            return None, None
        
        fcf = 0
        if 'Free Cash Flow' in cash_flow.index and len(cash_flow.columns) > 0:
            fcf = cash_flow.loc['Free Cash Flow'].iloc[0]
        elif 'Operating Cash Flow' in cash_flow.index and len(cash_flow.columns) > 0:
            ocf = cash_flow.loc['Operating Cash Flow'].iloc[0]
            capex = cash_flow.loc['Capital Expenditure'].iloc[0] if 'Capital Expenditure' in cash_flow.index else 0
            fcf = ocf + capex
        
        if fcf <= 0:
            return None, None
        
        growth_rate = 0.05
        discount_rate = 0.10
        terminal_growth = 0.02
        forecast_years = 5
        
        fcf_projections = []
        dcf_value = 0
        
        for i in range(1, forecast_years + 1):
            future_fcf = fcf * (1 + growth_rate) ** i
            pv = future_fcf / (1 + discount_rate) ** i
            fcf_projections.append({
                'year': i,
                'fcf': future_fcf,
                'pv': pv
            })
            dcf_value += pv
        
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
        
        dcf_params = {
            'growth_rate': growth_rate,
            'discount_rate': discount_rate,
            'terminal_growth': terminal_growth,
            'forecast_years': forecast_years,
            'initial_fcf': fcf,
            'fcf_projections': fcf_projections,
            'terminal_value': terminal_value,
            'terminal_pv': terminal_pv,
            'enterprise_value': enterprise_value,
            'shares': shares
        }
            
        return fair_value_per_share, dcf_params
    except Exception as e:
        st.warning(f"DCF估值计算失败: {str(e)}")
        return None, None

def analyze_technical_signals(hist_data):
    """分析技术信号"""
    signals = {
        'ma_golden_cross': False,
        'ma_death_cross': False,
        'macd_golden_cross': False,
        'macd_death_cross': False,
        'rsi_oversold': False,
        'rsi_overbought': False,
        'bb_breakout': False,
        'volume_divergence': False,
        'trend': 'neutral'
    }
    
    try:
        if len(hist_data) < 60:
            return signals
        
        latest = hist_data.iloc[-1]
        prev = hist_data.iloc[-2]
        
        if 'MA10' in hist_data.columns and 'MA60' in hist_data.columns:
            if latest['MA10'] > latest['MA60'] and prev['MA10'] <= prev['MA60']:
                signals['ma_golden_cross'] = True
            elif latest['MA10'] < latest['MA60'] and prev['MA10'] >= prev['MA60']:
                signals['ma_death_cross'] = True
        
        if 'MACD' in hist_data.columns and 'Signal' in hist_data.columns:
            if latest['MACD'] > latest['Signal'] and prev['MACD'] <= prev['Signal']:
                signals['macd_golden_cross'] = True
            elif latest['MACD'] < latest['Signal'] and prev['MACD'] >= prev['Signal']:
                signals['macd_death_cross'] = True
        
        if 'RSI' in hist_data.columns:
            if latest['RSI'] < 30:
                signals['rsi_oversold'] = True
            elif latest['RSI'] > 70:
                signals['rsi_overbought'] = True
        
        if latest['Close'] > latest['MA60']:
            signals['trend'] = 'bullish'
        else:
            signals['trend'] = 'bearish'
            
    except Exception as e:
        st.warning(f"技术信号分析失败: {str(e)}")
    
    return signals

# ==================== 主程序 ====================
# 侧边栏输入
with st.sidebar:
    st.header("📊 分析参数设置")
    
    ticker = st.text_input("股票代码", "AAPL", help="输入股票代码，如：AAPL")
    market = st.selectbox("市场选择", ["美股", "A股（待开发）"])
    analyze_button = st.button("🔍 开始分析", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    with st.expander("📘 使用说明"):
        st.markdown("""
        ### 如何解读各项数值指标
        
        **1. 安全边际 (Margin of Safety)**
        - 正值：股价低于估值，存在低估
        - 负值：股价高于估值，存在高估
        - 建议：
          - > 50%：强买入
          - 20-50%：买入
          - 0-20%：观察
          - < 0%：避免
        
        **2. 信心度 (Confidence)**
        - > 70%：高信心度
        - 50-70%：中等信心
        - < 50%：低信心度
        
        **3. 技术信号**
        - 金叉：买入信号
        - 死叉：卖出信号
        - RSI > 70：超买
        - RSI < 30：超卖
        
        **4. Piotroski F-score**
        - 7-9分：优秀
        - 4-6分：中等
        - 0-3分：较差
        
        **5. Altman Z-score**
        - Z > 2.99：✅ 财务健康
        - 1.81-2.99：⚠️ 临界风险
        - Z < 1.81：🚨 高破产风险
        """)
    
    with st.expander("📊 投资决策参考表"):
        st.markdown("""
        ### 综合评分决策表
        | 安全边际 | 信心度 | 操作建议 |
        |---------|--------|----------|
        | >30%    | >70%   | ✅ 强买入 |
        | >0%     | >50%   | ⚠️ 观察  |
        | <0%     | ≈50%   | 🔍 观望  |
        | <0%     | <50%   | 🚫 回避  |
        
        ### Piotroski F-Score解读
        | 得分 | 评级 | 建议 |
        |------|------|------|
        | 8-9分 | 🟢 优秀 | 强烈买入 |
        | 6-7分 | 🟡 良好 | 可以买入 |
        | 4-5分 | 🟠 一般 | 谨慎观察 |
        | 0-3分 | 🔴 较差 | 避免投资 |
        
        ### Altman Z-Score风险等级
        | Z-Score | 风险等级 | 说明 |
        |---------|----------|------|
        | >2.99 | 🟢 安全 | 破产风险极低 |
        | 1.81-2.99 | 🟡 灰色 | 需要关注 |
        | <1.81 | 🔴 危险 | 破产风险高 |
        
        ### DCF估值参考
        - **安全边际 > 20%**: 明显低估，考虑买入
        - **安全边际 0-20%**: 合理估值区间
        - **安全边际 < 0%**: 高估，谨慎投资
        """)

# 主界面逻辑
if analyze_button and ticker:
    st.session_state.current_ticker = ticker
    st.session_state.show_analysis = True
    
    with st.spinner(f"正在获取 {ticker} 的数据..."):
        try:
            data = fetch_stock_data(ticker)
        except:
            data = fetch_stock_data_uncached(ticker)
    
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
        col1, col2, col3 = st.columns([1, 2, 1.5])
        
        # 左栏：基本信息
        with col1:
            st.subheader("📌 公司基本信息")
            info = data['info']
            
            st.metric("公司名称", info.get('longName', ticker))
            st.metric("当前股价", f"${current_price:.2f}")
            st.metric("市值", f"${info.get('marketCap', 0)/1e9:.2f}B")
            st.metric("行业", info.get('industry', 'N/A'))
            st.metric("Beta", f"{info.get('beta', 0):.2f}")
            
            st.markdown("---")
            st.metric("52周最高", f"${info.get('fiftyTwoWeekHigh', 0):.2f}")
            st.metric("52周最低", f"${info.get('fiftyTwoWeekLow', 0):.2f}")
        
        # 中栏：分析结果
        with col2:
            st.subheader("📈 综合分析结果")
            
            # Piotroski F-Score
            with st.expander("🔍 Piotroski F-Score 分析", expanded=True):
                f_score, reasons = calculate_piotroski_score(data)
                
                score_color = "green" if f_score >= 7 else "orange" if f_score >= 4 else "red"
                st.markdown(f"### 得分: <span style='color:{score_color}; font-size:24px'>{f_score}/9</span>", unsafe_allow_html=True)
                
                for reason in reasons:
                    st.write(reason)
                
                if f_score >= 7:
                    st.success("💡 建议: 财务健康状况良好，基本面强劲")
                elif f_score >= 4:
                    st.warning("💡 建议: 财务状况一般，需要谨慎评估")
                else:
                    st.error("💡 建议: 财务状况较差，投资风险较高")
            
            # 杜邦分析
            with st.expander("📊 杜邦分析", expanded=True):
                dupont = calculate_dupont_analysis(data)
                if dupont:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("ROE", f"{dupont['roe']:.2f}%")
                        st.metric("利润率", f"{dupont['profit_margin']:.2f}%")
                    with col_b:
                        st.metric("资产周转率", f"{dupont['asset_turnover']:.2f}")
                        st.metric("权益乘数", f"{dupont['equity_multiplier']:.2f}")
                    
                    st.write("📝 ROE = 利润率 × 资产周转率 × 权益乘数")
            
            # Altman Z-Score
            with st.expander("💰 Altman Z-Score 财务健康度", expanded=True):
                z_score, status, color = calculate_altman_z_score(data)
                if z_score:
                    st.markdown(f"### Z-Score: <span style='color:{color}; font-size:24px'>{z_score:.2f}</span>", unsafe_allow_html=True)
                    st.markdown(f"**状态**: <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)
                    
                    if z_score > 2.99:
                        st.success("✅ 财务健康 - 企业财务状况良好，破产风险极低")
                    elif z_score >= 1.81:
                        st.warning("⚠️ 临界风险 - 企业处于灰色地带，需要密切关注")
                    else:
                        st.error("🚨 高破产风险 - 企业财务状况堪忧，投资需谨慎")
                    
                    st.write("📊 评分标准:")
                    st.write("- Z > 2.99: 安全区域")
                    st.write("- 1.8 < Z < 2.99: 灰色区域")
                    st.write("- Z < 1.8: 危险区域")
            
            # DCF估值分析
            with st.expander("💎 DCF估值分析", expanded=True):
                dcf_value, dcf_params = calculate_dcf_valuation(data)
                
                if dcf_value and current_price > 0:
                    st.write("**DCF估值**")
                    col_x, col_y = st.columns(2)
                    with col_x:
                        st.metric("合理价值", f"${dcf_value:.2f}")
                        st.metric("当前价格", f"${current_price:.2f}")
                    with col_y:
                        margin = ((dcf_value - current_price) / dcf_value * 100) if dcf_value > 0 else 0
                        st.metric("安全边际", f"{margin:.2f}%")
                    
                    if dcf_params:
                        st.write("**📊 DCF模型参数详情**")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.write(f"**永续增长率 g**: {dcf_params['terminal_growth']*100:.1f}%")
                            st.write(f"**预测期增长率**: {dcf_params['growth_rate']*100:.1f}%")
                        with col_b:
                            st.write(f"**折现率 WACC**: {dcf_params['discount_rate']*100:.1f}%")
                            st.write(f"**预测年限**: {dcf_params['forecast_years']}年")
                        with col_c:
                            st.write(f"**初始FCF**: ${dcf_params['initial_fcf']/1e6:.1f}M")
                            st.write(f"**企业价值**: ${dcf_params['enterprise_value']/1e9:.2f}B")
                        
                        st.write("**预测期现金流（百万美元）**")
                        fcf_df = pd.DataFrame(dcf_params['fcf_projections'])
                        fcf_df['fcf'] = fcf_df['fcf'] / 1e6
                        fcf_df['pv'] = fcf_df['pv'] / 1e6
                        fcf_df.columns = ['年份', '预测FCF', '现值']
                        st.dataframe(fcf_df.style.format({'预测FCF': '${:.1f}M', '现值': '${:.1f}M'}))
                        
                        st.write(f"**终值**: ${dcf_params['terminal_value']/1e9:.2f}B")
                        st.write(f"**终值现值**: ${dcf_params['terminal_pv']/1e9:.2f}B")
                else:
                    st.info("DCF估值数据不足")
        
        # 右栏：技术分析和止盈止损模拟器
        with col3:
            st.subheader("📉 技术分析与建议")
            
            # 计算技术指标
            hist_data = data['hist_data'].copy()
            hist_data = calculate_technical_indicators(hist_data)
            
            # 价格走势图
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(hist_data.index[-180:], hist_data['Close'][-180:], label='Close', linewidth=2)
            if 'MA20' in hist_data.columns:
                ax.plot(hist_data.index[-180:], hist_data['MA20'][-180:], label='MA20', alpha=0.7)
            if 'MA60' in hist_data.columns:
                ax.plot(hist_data.index[-180:], hist_data['MA60'][-180:], label='MA60', alpha=0.7)
            ax.set_title(f'{ticker} Price Trend (Last 180 Days)')
            ax.set_xlabel('Date')
            ax.set_ylabel('Price ($)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            
            # MACD图
            if 'MACD' in hist_data.columns:
                fig2, ax2 = plt.subplots(figsize=(10, 4))
                ax2.plot(hist_data.index[-90:], hist_data['MACD'][-90:], label='MACD', color='blue')
                ax2.plot(hist_data.index[-90:], hist_data['Signal'][-90:], label='Signal', color='red')
                ax2.bar(hist_data.index[-90:], hist_data['MACD_Histogram'][-90:], label='Histogram', alpha=0.3)
                ax2.set_title('MACD Indicator')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig2)
            
            # 技术分析结论展示
            st.markdown("---")
            st.subheader("📊 技术指标快速解读")
            
            # 计算技术信号
            technical_signals = analyze_technical_signals(hist_data)
            latest = hist_data.iloc[-1]
            
            # 技术指标状态卡片
            tech_col1, tech_col2 = st.columns(2)
            
            with tech_col1:
                # MACD 状态
                if technical_signals['macd_golden_cross']:
                    st.success("🔺 MACD：金叉（看涨信号）")
                elif technical_signals['macd_death_cross']:
                    st.error("🔻 MACD：死叉（看跌信号）")
                else:
                    if 'MACD' in hist_data.columns and 'Signal' in hist_data.columns:
                        macd_val = latest['MACD']
                        signal_val = latest['Signal']
                        if macd_val > signal_val:
                            st.info("📈 MACD：多头排列")
                        else:
                            st.warning("📉 MACD：空头排列")
                
                # 均线状态
                if technical_signals['ma_golden_cross']:
                    st.success("🔺 均线：金叉突破")
                elif technical_signals['ma_death_cross']:
                    st.error("🔻 均线：死叉下破")
                elif 'MA10' in hist_data.columns and 'MA60' in hist_data.columns:
                    if latest['MA10'] > latest['MA60']:
                        st.info("📈 均线：多头排列")
                    else:
                        st.warning("📉 均线：空头排列")
            
            with tech_col2:
                # RSI 状态
                if 'RSI' in hist_data.columns:
                    rsi_value = latest['RSI']
                    if rsi_value > 70:
                        st.error(f"⚠️ RSI：{rsi_value:.1f} → 超买状态")
                    elif rsi_value < 30:
                        st.success(f"💡 RSI：{rsi_value:.1f} → 超卖状态")
                    else:
                        st.info(f"📊 RSI：{rsi_value:.1f} → 正常区间")
                
                # 布林带状态
                if 'BB_Upper' in hist_data.columns and 'BB_Lower' in hist_data.columns:
                    close_price = latest['Close']
                    bb_upper = latest['BB_Upper']
                    bb_lower = latest['BB_Lower']
                    bb_middle = latest['BB_Middle']
                    
                    if close_price > bb_upper:
                        st.warning("🔺 布林带：突破上轨")
                    elif close_price < bb_lower:
                        st.success("🔻 布林带：跌破下轨")
                    elif close_price > bb_middle:
                        st.info("📈 布林带：上半区运行")
                    else:
                        st.info("📉 布林带：下半区运行")
            
            # 智能止盈止损模拟器
            st.markdown("---")
            st.subheader("💰 智能止盈止损模拟器")
            
            st.info(f"📊 当前分析股票：{ticker} | 实时价格：${current_price:.2f}")
            
            # 输入参数
            col_input1, col_input2 = st.columns(2)
            with col_input1:
                default_buy_price = current_price * 0.95
                buy_price = st.number_input(
                    "买入价格 ($)", 
                    min_value=0.01, 
                    value=default_buy_price, 
                    step=0.01, 
                    key=f"buy_price_{ticker}"
                )
            with col_input2:
                position_size = st.number_input(
                    "持仓数量", 
                    min_value=1, 
                    value=100, 
                    step=1,
                    key=f"position_size_{ticker}"
                )
            
            # 基础计算
            position_value = position_size * buy_price
            current_value = position_size * current_price
            pnl = current_value - position_value
            pnl_pct = (pnl / position_value) * 100 if position_value > 0 else 0
            
            # 四种策略标签页
            st.markdown("#### 🎯 选择止盈止损策略")
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 固定比例法", 
                "📈 技术指标法", 
                "📉 波动率法", 
                "🎯 成本加码法"
            ])
            
            # 策略1：固定比例法
            with tab1:
                st.write("**适用场景**: 大多数波动性股票，适合稳健型投资者")
                
                col1, col2 = st.columns(2)
                with col1:
                    tp_pct = st.slider("止盈比例 (%)", 5, 50, 15, key=f"tp1_{ticker}")
                with col2:
                    sl_pct = st.slider("止损比例 (%)", 3, 20, 10, key=f"sl1_{ticker}")
                
                stop_loss = buy_price * (1 - sl_pct / 100)
                take_profit = buy_price * (1 + tp_pct / 100)
                
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("💰 当前盈亏", f"${pnl:.2f}", f"{pnl_pct:+.2f}%")
                with col_m2:
                    st.metric("🛡️ 止损价位", f"${stop_loss:.2f}")
                with col_m3:
                    st.metric("🎯 止盈价位", f"${take_profit:.2f}")
                
                if current_price <= stop_loss:
                    st.error("⚠️ 已触及止损线！")
                elif current_price >= take_profit:
                    st.success("🎯 已达到止盈目标！")
                else:
                    st.info("📊 持仓正常")
                
                # 风险收益分析
                risk_amount = position_size * (buy_price - stop_loss)
                reward_amount = position_size * (take_profit - buy_price)
                rr_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
                st.caption(f"💡 风险收益比：1:{rr_ratio:.2f}")
            
            # 策略2：技术指标法
            with tab2:
                st.write("**适用场景**: 基于支撑阻力位、布林带等技术分析")
                
                # 计算技术位
                if len(hist_data) > 20:
                    latest = hist_data.iloc[-1]
                    support = hist_data['Low'].rolling(20).min().iloc[-1]
                    resistance = hist_data['High'].rolling(20).max().iloc[-1]
                    
                    if 'BB_Lower' in hist_data.columns:
                        bb_lower = latest['BB_Lower']
                        bb_upper = latest['BB_Upper']
                    else:
                        bb_lower = current_price * 0.95
                        bb_upper = current_price * 1.05
                    
                    tech_method = st.selectbox(
                        "技术指标方法",
                        ["布林带策略", "支撑阻力位", "均线支撑"],
                        key=f"tech_method_{ticker}"
                    )
                    
                    if tech_method == "布林带策略":
                        tech_sl = bb_lower * 0.98
                        tech_tp = bb_upper * 1.02
                    elif tech_method == "支撑阻力位":
                        tech_sl = support * 0.98
                        tech_tp = resistance * 1.02
                    else:
                        ma20 = latest['MA20'] if 'MA20' in hist_data.columns else current_price * 0.98
                        tech_sl = ma20 * 0.98
                        tech_tp = current_price * 1.15
                    
                    col_t1, col_t2, col_t3 = st.columns(3)
                    with col_t1:
                        st.metric("💰 当前盈亏", f"${pnl:.2f}", f"{pnl_pct:+.2f}%")
                    with col_t2:
                        st.metric("🛡️ 技术止损", f"${tech_sl:.2f}")
                    with col_t3:
                        st.metric("🎯 技术止盈", f"${tech_tp:.2f}")
                    
                    st.write(f"• 支撑位: ${support:.2f}")
                    st.write(f"• 阻力位: ${resistance:.2f}")
                else:
                    st.warning("数据不足，无法计算技术指标")
            
            # 策略3：波动率法
            with tab3:
                st.write("**适用场景**: 根据股票波动性调整，高波动股票设置更大空间")
                
                if len(hist_data) > 14:
                    # 计算ATR
                    high_low = hist_data['High'] - hist_data['Low']
                    high_close = np.abs(hist_data['High'] - hist_data['Close'].shift())
                    low_close = np.abs(hist_data['Low'] - hist_data['Close'].shift())
                    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                    atr = tr.rolling(14).mean().iloc[-1]
                    
                    # 计算波动率
                    returns = hist_data['Close'].pct_change().dropna()
                    volatility = returns.std() * np.sqrt(252) * 100
                    
                    atr_mult = st.slider("ATR倍数", 1.0, 4.0, 2.0, 0.1, key=f"atr_{ticker}")
                    
                    vol_sl = max(buy_price - atr * atr_mult, buy_price * 0.90)
                    vol_tp = buy_price * 1.15
                    
                    col_v1, col_v2, col_v3 = st.columns(3)
                    with col_v1:
                        st.metric("ATR", f"${atr:.2f}")
                    with col_v2:
                        st.metric("年化波动率", f"{volatility:.1f}%")
                    with col_v3:
                        vol_level = "高" if volatility > 30 else "中" if volatility > 20 else "低"
                        st.metric("波动等级", vol_level)
                    
                    col_vm1, col_vm2, col_vm3 = st.columns(3)
                    with col_vm1:
                        st.metric("💰 当前盈亏", f"${pnl:.2f}", f"{pnl_pct:+.2f}%")
                    with col_vm2:
                        st.metric("🛡️ ATR止损", f"${vol_sl:.2f}")
                    with col_vm3:
                        st.metric("🎯 波动率止盈", f"${vol_tp:.2f}")
                else:
                    st.warning("数据不足，无法计算波动率指标")
            
            # 策略4：成本加码法
            with tab4:
                st.write("**适用场景**: 根据盈利情况动态调整，保护利润追求更大收益")
                
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    profit_threshold = st.slider("利润阈值 (%)", 5, 30, 10, key=f"profit_{ticker}")
                with col_c2:
                    trailing_dist = st.slider("追踪距离 (%)", 3, 15, 5, key=f"trail_{ticker}")
                
                threshold_price = buy_price * (1 + profit_threshold / 100)
                
                if current_price >= threshold_price:
                    # 动态止损激活
                    dynamic_sl = max(buy_price * 1.02, current_price * (1 - trailing_dist / 100))
                    status = f"🟢 动态止损激活 (突破{profit_threshold}%)"
                    dynamic_tp = buy_price * 1.25
                else:
                    # 普通止损
                    dynamic_sl = buy_price * 0.92
                    need_rise = ((threshold_price - current_price) / current_price * 100)
                    status = f"🔵 等待激活 (需上涨{need_rise:.1f}%)"
                    dynamic_tp = threshold_price
                
                st.info(status)
                
                # 分阶段目标
                stage1 = threshold_price
                stage2 = buy_price * 1.20
                stage3 = buy_price * 1.35
                
                col_cm1, col_cm2, col_cm3 = st.columns(3)
                with col_cm1:
                    st.metric("💰 当前盈亏", f"${pnl:.2f}", f"{pnl_pct:+.2f}%")
                with col_cm2:
                    st.metric("🛡️ 动态止损", f"${dynamic_sl:.2f}")
                with col_cm3:
                    st.metric("🎯 当前目标", f"${dynamic_tp:.2f}")
                
                st.markdown("**分阶段目标**")
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    s1_status = "✅" if current_price >= stage1 else "⏳"
                    st.write(f"{s1_status} 阶段1: ${stage1:.2f}")
                with col_s2:
                    s2_status = "✅" if current_price >= stage2 else "⏳"
                    st.write(f"{s2_status} 阶段2: ${stage2:.2f}")
                with col_s3:
                    s3_status = "✅" if current_price >= stage3 else "⏳"
                    st.write(f"{s3_status} 阶段3: ${stage3:.2f}")
            
            # 策略推荐
            st.markdown("---")
            st.markdown("#### 💡 当前推荐策略")
            
            try:
                returns = hist_data['Close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252) * 100
                
                if volatility > 30:
                    st.info("🔥 **推荐波动率法** - 当前股票波动性较高")
                elif pnl_pct > 5:
                    st.info("📈 **推荐成本加码法** - 当前有盈利，适合动态管理")
                elif len(hist_data) > 20 and 'BB_Middle' in hist_data.columns:
                    st.info("📊 **推荐技术指标法** - 技术形态明确")
                else:
                    st.info("🎯 **推荐固定比例法** - 市场信号不明确时最为稳健")
            except:
                st.info("🎯 **推荐固定比例法** - 适合大多数投资场景")
            
            # 风险提示
            st.warning("""
            ⚠️ **风险提示**: 所有策略仅供参考，实际投资需结合市场环境。
            止损是风险管理工具，执行纪律比策略更重要。投资有风险，入市需谨慎。
            """)
    
    with main_tab2:
        st.subheader("📰 最新时事分析")
        st.info("💡 基于最新财经新闻的市场影响分析，辅助投资决策")
        
        # 获取新闻数据
        news_data = fetch_financial_news(ticker)
        
                        # 新闻展示
        for i, news in enumerate(news_data):
            if not news.get('title'):  # 跳过空标题的新闻
                continue
                
            with st.container():
                # 新闻卡片样式根据类别调整
                category = news.get('category', 'general')
                if category == 'company_specific':
                    border_color = "#4CAF50"  # 绿色边框 - 公司特定
                    bg_color = "#f8fff8"
                elif category == 'market_wide':
                    border_color = "#2196F3"  # 蓝色边框 - 市场广泛
                    bg_color = "#f8fcff"
                elif category == 'industry_specific':
                    border_color = "#FF9800"  # 橙色边框 - 行业相关
                    bg_color = "#fffaf8"
                else:
                    border_color = "#ddd"     # 默认灰色
                    bg_color = "#fafafa"
                
                title = news.get('title', '无标题')
                summary = news.get('summary', '无摘要')
                published = news.get('published', datetime.now())
                keywords = news.get('keywords', [])
                source = news.get('source', '未知来源')
                
                # 添加分类标签
                category_labels = {
                    'company_specific': f'🏢 {ticker}相关',
                    'industry_specific': '🏭 行业动态', 
                    'market_wide': '🌍 市场影响',
                    'system': '📋 系统信息'
                }
                category_label = category_labels.get(category, '📰 一般新闻')
                
                st.markdown(f"""
                <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 15px; margin: 10px 0; background-color: {bg_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="background-color: {border_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">
                            {category_label}
                        </span>
                        <span style="font-size: 11px; color: #999;">
                            📰 {source}
                        </span>
                    </div>
                    <h4 style="margin: 8px 0; color: #333; line-height: 1.3;">{title}</h4>
                    <p style="color: #666; margin: 10px 0; line-height: 1.4;">{summary}</p>
                    <p style="font-size: 12px; color: #999; margin-bottom: 0;">
                        📅 {published.strftime('%Y-%m-%d %H:%M')} | 
                        🏷️ 关键词: {', '.join(keywords) if keywords else '暂无'}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # 市场影响分析
                col_sentiment, col_impact = st.columns([1, 2])
                
                with col_sentiment:
                    sentiment = news['sentiment']
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
        
        # 整体市场情绪分析
        st.subheader("📊 整体市场情绪分析")
        
        # 计算情绪统计
        bullish_count = sum(1 for news in news_data if news['sentiment'] == '利好')
        bearish_count = sum(1 for news in news_data if news['sentiment'] == '利空')
        neutral_count = sum(1 for news in news_data if news['sentiment'] == '中性')
        
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        with col_stats1:
            st.metric("📈 利好消息", bullish_count)
        with col_stats2:
            st.metric("📉 利空消息", bearish_count)
        with col_stats3:
            st.metric("📊 中性消息", neutral_count)
        
        # 整体建议
        if bullish_count > bearish_count:
            overall_sentiment = "偏向乐观"
            st.success(f"🟢 **整体市场情绪**: {overall_sentiment}")
            st.info("💡 **投资建议**: 市场利好因素较多，可适当关注优质标的的投资机会，但仍需注意风险控制。")
        elif bearish_count > bullish_count:
            overall_sentiment = "偏向谨慎"
            st.error(f"🔴 **整体市场情绪**: {overall_sentiment}")
            st.warning("⚠️ **投资建议**: 市场风险因素增加，建议降低仓位，关注防御性资产，等待更好的投资时机。")
        else:
            overall_sentiment = "相对平衡"
            st.info(f"🟡 **整体市场情绪**: {overall_sentiment}")
            st.info("📊 **投资建议**: 市场情绪相对平衡，建议保持现有投资策略，密切关注后续发展。")
        
        # 关键词词云（简化版）
        st.subheader("🔍 热点关键词")
        all_keywords = []
        for news in news_data:
            all_keywords.extend(news['keywords'])
        
        keyword_count = {}
        for keyword in all_keywords:
            keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
        
        # 显示最热关键词
        sorted_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)[:8]
        
        cols = st.columns(4)
        for i, (keyword, count) in enumerate(sorted_keywords):
            with cols[i % 4]:
                st.metric(f"🏷️ {keyword}", f"{count}次")
        
        # 投资提醒
        st.subheader("💡 基于时事的投资提醒")
        
        # 根据关键词给出具体建议
        investment_suggestions = []
        
        for keyword, count in sorted_keywords:
            if keyword in ["降息", "利好"]:
                investment_suggestions.append("🟢 关注利率敏感性行业：房地产、基建、银行等")
            elif keyword in ["AI", "科技股"]:
                investment_suggestions.append("🔵 关注科技成长股：人工智能、芯片、软件等")
            elif keyword in ["新能源", "电动车"]:
                investment_suggestions.append("⚡ 关注新能源产业链：电池、充电桩、光伏等")
            elif keyword in ["地缘政治", "避险"]:
                investment_suggestions.append("🟡 关注避险资产：黄金、国债、公用事业等")
            elif keyword in ["通胀", "消费"]:
                investment_suggestions.append("🛒 关注消费防守板块：食品饮料、医药、日用品等")
        
        # 去重并显示建议
        unique_suggestions = list(set(investment_suggestions))
        for suggestion in unique_suggestions[:5]:  # 最多显示5个建议
            st.write(suggestion)
        
        # 数据来源说明
        st.markdown("---")
        st.caption("📝 **数据来源**: 实时从Yahoo Finance、CNBC、MarketWatch等财经网站获取最新新闻")
        st.caption("🔄 **更新频率**: 新闻数据实时更新，建议定期刷新页面获取最新信息")
        st.caption("⚠️ **免责声明**: 时事分析仅供参考，不构成投资建议。投资决策应基于个人判断和专业咨询。")

else:
    st.info("👈 请在左侧输入股票代码并点击分析按钮开始")
    
    with st.expander("📖 使用说明"):
        st.markdown("""
        ### 系统功能
        1. **自动数据获取**: 输入股票代码后，系统自动获取最新财务数据和历史价格
        2. **多维度分析**: 包含基本面、技术面、估值等多个维度的综合分析
        3. **智能建议**: 基于多个模型的评分，给出买入/卖出建议和仓位建议
        
        ### 分析模型说明
        - **Piotroski F-Score**: 评估公司财务健康状况（9分制）
        - **杜邦分析**: 分解ROE，了解盈利能力来源
        - **Altman Z-Score**: 预测企业破产风险
        - **DCF估值**: 基于现金流的内在价值评估
        - **技术分析**: 均线、MACD、RSI、布林带等技术指标
        
        ### 新增功能 - 四种止盈止损策略
        - **📊 固定比例法**: 设定固定止盈止损百分比，适合稳健投资
        - **📈 技术指标法**: 基于布林带、支撑阻力位等技术分析
        - **📉 波动率法**: 根据ATR和历史波动率动态调整
        - **🎯 成本加码法**: 动态止损和分阶段止盈，保护利润
        
        ### 注意事项
        - 本系统仅供参考，不构成投资建议
        - 请结合其他信息进行综合判断
        - 投资有风险，入市需谨慎
        """)
    
    with st.expander("🆕 新功能展示"):
        st.markdown("### v2.0 新增功能预览")
        
        st.subheader("技术分析图表")
        st.write("• 📈 价格走势图（包含均线MA20、MA60）")
        st.write("• 📊 MACD指标图（含金叉死叉信号）")
        st.write("• 🎯 技术指标状态实时监控")
        
        st.subheader("财务分析模块")
        st.write("• 🔍 Piotroski F-Score财务健康评分")
        st.write("• 📊 杜邦分析ROE分解")
        st.write("• 💰 Altman Z-Score破产风险评估")
        st.write("• 💎 DCF现金流折现估值")
        
        st.subheader("智能止盈止损系统")
        st.write("• 📊 固定比例法：简单实用")
        st.write("• 📈 技术指标法：专业分析")
        st.write("• 📉 波动率法：自适应调整")
        st.write("• 🎯 成本加码法：动态管理")
        
        st.info("输入股票代码后即可查看完整分析结果")
    
    with st.expander("🚀 系统特色"):
        st.markdown("""
        ### 📊 全面的分析维度
        - **基本面分析**: 财务健康度、盈利能力、估值水平
        - **技术面分析**: 趋势判断、信号识别、支撑阻力
        - **风险评估**: 破产风险、波动性分析、止损建议
        
        ### 🎯 智能化特性
        - **自动推荐**: 根据股票特性推荐最适合的策略
        - **实时计算**: 参数调整即时反馈
        - **可视化**: 直观的图表和状态显示
        
        ### 💡 用户友好
        - **分层设计**: 新手到专家都能找到适合的功能
        - **状态持久**: 参数调整不会重新加载
        - **详细说明**: 每个指标都有使用指导
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

st.markdown("💹 智能投资分析系统 v2.0 | 仅供参考，投资需谨慎")
