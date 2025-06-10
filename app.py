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
    page_title="📰 增强翻译新闻系统",
    page_icon="📰",
    layout="wide"
)

st.title("📰 增强翻译新闻系统")
st.markdown("**智能中文翻译 + 30条真实新闻 + 自然语言处理**")
st.markdown("---")

# 初始化 session state
if 'news_data' not in st.session_state:
    st.session_state.news_data = None
if 'source_stats' not in st.session_state:
    st.session_state.source_stats = {}

# ==================== 增强翻译系统 ====================

class EnhancedFinancialTranslator:
    """增强版财经翻译器"""
    
    def __init__(self):
        # 扩展财经词汇库
        self.financial_vocab = {
            # 公司行为动词
            'reported': '发布', 'announced': '宣布', 'revealed': '透露', 'disclosed': '披露',
            'released': '发布', 'published': '公布', 'filed': '提交', 'submitted': '递交',
            'confirmed': '确认', 'denied': '否认', 'warned': '警告', 'projected': '预计',
            
            # 财务术语
            'earnings': '财报', 'revenue': '营收', 'sales': '销售额', 'income': '收入',
            'profit': '利润', 'loss': '亏损', 'margin': '利润率', 'ebitda': 'EBITDA',
            'cash flow': '现金流', 'free cash flow': '自由现金流', 'dividend': '分红',
            'buyback': '回购', 'acquisition': '收购', 'merger': '合并',
            
            # 市场表现
            'stock': '股票', 'shares': '股价', 'share price': '股价', 'market cap': '市值
