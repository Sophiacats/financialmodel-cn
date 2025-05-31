import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import math
import io
import base64
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# ==================== 配置和初始化 ====================
st.set_page_config(
    page_title="FinancialModel.cn - 专业金融建模平台",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 常量定义 ====================
class ModelConstants:
    """模型常量定义"""
    DEFAULT_WACC = 8.5
    DEFAULT_TERMINAL_GROWTH = 2.5
    DEFAULT_FCF_MARGIN = 10.0
    MIN_WACC = 0.1
    MAX_TERMINAL_GROWTH = 5.0
    DEFAULT_FORECAST_YEARS = 5
    
    CURRENCY_SYMBOLS = {"CNY": "￥", "USD": "$"}
    CURRENCY_UNITS = {"CNY": "万元", "USD": "万美元"}

# ==================== 样式和CSS ====================
def load_custom_css():
    """加载自定义CSS样式"""
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f2937;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin: 0.5rem 0;
    }
    .warning-box {
        background: #fef3c7;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f59e0b;
        margin: 1rem 0;
    }
    .success-box {
        background: #dcfce7;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10b981;
        margin: 1rem 0;
    }
    .info-box {
        background: #dbeafe;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    .coming-soon {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== 数据类定义 ====================
class CompanyData:
    """公司数据类"""
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '目标公司')
        self.stock_price = kwargs.get('stock_price', 45.60)
        self.total_shares = kwargs.get('total_shares', 12.5)
        self.net_profit = kwargs.get('net_profit', 35000)
        self.net_assets = kwargs.get('net_assets', 180000)
        self.ebitda = kwargs.get('ebitda', 65000)
        self.ebit = kwargs.get('ebit', 52000)
        self.cash = kwargs.get('cash', 25000)
        self.debt = kwargs.get('debt', 85000)
        self.growth_rate = kwargs.get('growth_rate', 12.5)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'name': self.name,
            'stock_price': self.stock_price,
            'total_shares': self.total_shares,
            'net_profit': self.net_profit,
            'net_assets': self.net_assets,
            'ebitda': self.ebitda,
            'ebit': self.ebit,
            'cash': self.cash,
            'debt': self.debt,
            'growth_rate': self.growth_rate
        }

class DCFData:
    """DCF数据类"""
    def __init__(self, **kwargs):
        self.company_name = kwargs.get('company_name', '目标公司')
        self.base_revenue = kwargs.get('base_revenue', 1000.0)
        self.base_fcf = kwargs.get('base_fcf', 100.0)
        self.revenue_growth_rates = kwargs.get('revenue_growth_rates', [15.0, 12.0, 10.0, 8.0, 6.0])
        self.fcf_margin = kwargs.get('fcf_margin', ModelConstants.DEFAULT_FCF_MARGIN)
        self.wacc = kwargs.get('wacc', ModelConstants.DEFAULT_WACC)
        self.terminal_growth = kwargs.get('terminal_growth', ModelConstants.DEFAULT_TERMINAL_GROWTH)
        self.forecast_years = kwargs.get('forecast_years', ModelConstants.DEFAULT_FORECAST_YEARS)
        self.shares_outstanding = kwargs.get('shares_outstanding', 100.0)
        self.cash = kwargs.get('cash', 50.0)
        self.debt = kwargs.get('debt', 200.0)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'company_name': self.company_name,
            'base_revenue': self.base_revenue,
            'base_fcf': self.base_fcf,
            'revenue_growth_rates': self.revenue_growth_rates,
            'fcf_margin': self.fcf_margin,
            'wacc': self.wacc,
            'terminal_growth': self.terminal_growth,
            'forecast_years': self.forecast_years,
            'shares_outstanding': self.shares_outstanding,
            'cash': self.cash,
            'debt': self.debt
        }

# ==================== 核心计算引擎 ====================
class ValuationEngine:
    """估值计算引擎"""
    
    @staticmethod
    def calculate_relative_metrics(company_data: Dict) -> Dict:
        """计算相对估值指标"""
        try:
            market_cap = company_data['stock_price'] * company_data['total_shares']
            enterprise_value = market_cap + company_data['debt'] - company_data['cash']
            
            metrics = {
                'market_cap': round(market_cap, 2),
                'enterprise_value': round(enterprise_value, 2),
                'pe': round(market_cap / (company_data['net_profit'] / 10000), 2) if company_data['net_profit'] > 0 else 0,
                'pb': round(market_cap / (company_data['net_assets'] / 10000), 2) if company_data['net_assets'] > 0 else 0,
                'ev_ebitda': round(enterprise_value / (company_data['ebitda'] / 10000), 2) if company_data['ebitda'] > 0 else 0,
                'ev_ebit': round(enterprise_value / (company_data['ebit'] / 10000), 2) if company_data['ebit'] > 0 else 0,
                'peg': round((market_cap / (company_data['net_profit'] / 10000)) / company_data['growth_rate'], 2) 
                       if company_data['growth_rate'] > 0 and company_data['net_profit'] > 0 else 0
            }
            return metrics
        except Exception as e:
            logger.error(f"计算相对估值指标时出错: {e}")
            return {'market_cap': 0, 'enterprise_value': 0, 'pe': 0, 'pb': 0, 'ev_ebitda': 0, 'ev_ebit': 0, 'peg': 0}
    
    @staticmethod
    def calculate_dcf_valuation(dcf_data: DCFData) -> Optional[Dict]:
        """计算DCF估值"""
        try:
            # 预测期现金流
            forecasted_fcf = []
            revenue = dcf_data.base_revenue
            
            for i in range(dcf_data.forecast_years):
                if i < len(dcf_data.revenue_growth_rates):
                    growth_rate = dcf_data.revenue_growth_rates[i] / 100
                else:
                    growth_rate = dcf_data.revenue_growth_rates[-1] / 100
                
                revenue = revenue * (1 + growth_rate)
                fcf = revenue * dcf_data.fcf_margin / 100
                forecasted_fcf.append(fcf)
            
            # 贴现预测期现金流
            wacc = dcf_data.wacc / 100
            pv_fcf = []
            total_pv_fcf = 0
            
            for i, fcf in enumerate(forecasted_fcf):
                pv = fcf / ((1 + wacc) ** (i + 1))
                pv_fcf.append(pv)
                total_pv_fcf += pv
            
            # 终值计算
            terminal_fcf = forecasted_fcf[-1] * (1 + dcf_data.terminal_growth / 100)
            terminal_value = terminal_fcf / (wacc - dcf_data.terminal_growth / 100)
            pv_terminal = terminal_value / ((1 + wacc) ** dcf_data.forecast_years)
            
            # 企业价值和股权价值
            enterprise_value = total_pv_fcf + pv_terminal
            equity_value = enterprise_value + dcf_data.cash - dcf_data.debt
            share_price = equity_value / dcf_data.shares_outstanding
            
            return {
                'forecasted_fcf': forecasted_fcf,
                'pv_fcf': pv_fcf,
                'total_pv_fcf': total_pv_fcf,
                'terminal_value': terminal_value,
                'pv_terminal': pv_terminal,
                'enterprise_value': enterprise_value,
                'equity_value': equity_value,
                'share_price': share_price,
                'years': list(range(1, dcf_data.forecast_years + 1))
            }
        except Exception as e:
            logger.error(f"DCF估值计算错误: {e}")
            return None

# ==================== 数据管理器 ====================
class SessionStateManager:
    """Session State管理器"""
    
    @staticmethod
    def initialize_session_state():
        """初始化session state"""
        if 'target_company' not in st.session_state:
            st.session_state.target_company = CompanyData().to_dict()
        
        if 'comparable_companies' not in st.session_state:
            st.session_state.comparable_companies = [
                CompanyData(
                    name='同行A', stock_price=38.50, total_shares=10.2, 
                    net_profit=28000, net_assets=150000, ebitda=55000, 
                    ebit=42000, cash=20000, debt=70000, growth_rate=10.2
                ).to_dict(),
                CompanyData(
                    name='同行B', stock_price=52.30, total_shares=15.8, 
                    net_profit=45000, net_assets=220000, ebitda=78000, 
                    ebit=62000, cash=35000, debt=95000, growth_rate=15.8
                ).to_dict()
            ]
        
        if 'dcf_data' not in st.session_state:
            st.session_state.dcf_data = DCFData().to_dict()

# ==================== UI组件 ====================
class UIComponents:
    """UI组件类"""
    
    @staticmethod
    def render_metric_card(title: str, value: str, subtitle: str = "", color: str = "#3b82f6"):
        """渲染指标卡片"""
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: {color}; font-size: 2rem; margin: 0;">{value}</h3>
            <p style="margin: 0; color: #6b7280;">{title}</p>
            <small style="color: #9ca3af;">{subtitle}</small>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_navigation_sidebar():
        """渲染导航侧边栏"""
        st.sidebar.header("🧭 金融模型导航")
        
        model_categories = {
            "📈 估值分析": {
                "相对估值模型": "✅ 已上线",
                "DCF估值模型": "✅ 已上线", 
                "股息贴现模型": "📋 规划中"
            },
            "📊 投资组合管理": {
                "现代投资组合理论": "📋 规划中",
                "资产配置模型": "📋 规划中",
                "风险平价模型": "📋 规划中"
            },
            "💰 债券分析": {
                "债券定价模型": "📋 规划中",
                "久期凸性计算": "📋 规划中",
                "收益率曲线": "📋 规划中"
            },
            "⚡ 期权期货": {
                "Black-Scholes模型": "📋 规划中",
                "二叉树定价": "📋 规划中",
                "期权Greeks": "📋 规划中"
            },
            "🛡️ 风险管理": {
                "VaR计算器": "📋 规划中",
                "压力测试模型": "📋 规划中",
                "相关性分析": "📋 规划中"
            }
        }
        
        selected_category = st.sidebar.selectbox(
            "选择模型分类",
            list(model_categories.keys()),
            index=0
        )
        
        available_models = model_categories[selected_category]
        selected_model = st.sidebar.selectbox(
            "选择具体模型",
            list(available_models.keys()),
            format_func=lambda x: f"{x} {available_models[x]}"
        )
        
        return selected_category, selected_model
    
    @staticmethod
    def render_system_settings():
        """渲染系统设置"""
        st.sidebar.header("⚙️ 系统设置")
        currency = st.sidebar.selectbox("💱 币种选择", ["CNY (人民币)", "USD (美元)"], index=0)
        template_level = st.sidebar.selectbox("🎯 订阅级别", ["免费版", "专业版", "企业版"], index=1)
        
        currency_symbol = ModelConstants.CURRENCY_SYMBOLS["CNY" if currency.startswith("CNY") else "USD"]
        unit_text = ModelConstants.CURRENCY_UNITS["CNY" if currency.startswith("CNY") else "USD"]
        
        subscription_info = {
            "免费版": "🆓 每月3次分析 | 基础功能",
            "专业版": "⭐ 无限分析 | 完整功能 | 报告导出", 
            "企业版": "🏢 多用户 | API接口 | 定制服务"
        }
        st.sidebar.info(subscription_info[template_level])
        
        return currency, currency_symbol, unit_text, template_level

# ==================== 估值模型实现 ====================
class RelativeValuationModel:
    """相对估值模型"""
    
    def __init__(self, currency_symbol: str, unit_text: str, template_level: str):
        self.currency_symbol = currency_symbol
        self.unit_text = unit_text
        self.template_level = template_level
    
    def render(self):
        """渲染相对估值模型界面"""
        available_tabs = self._get_available_tabs()
        template_info = self._get_template_info()
        
        st.info(template_info)
        selected_tab = st.selectbox("选择功能模块", available_tabs)
        
        if selected_tab == "📈 估值计算":
            self._render_valuation_calculation()
        elif selected_tab == "📋 数据管理":
            self._render_data_management()
        elif selected_tab == "📊 对比分析":
            self._render_comparison_analysis()
        elif selected_tab == "💡 投资建议":
            self._render_investment_advice()
        elif selected_tab == "📄 报告导出":
            self._render_report_export()
    
    def _get_available_tabs(self) -> List[str]:
        """获取可用标签页"""
        if self.template_level == "免费版":
            return ["📈 估值计算", "📊 对比分析"]
        elif self.template_level == "专业版":
            return ["📈 估值计算", "📋 数据管理", "📊 对比分析", "💡 投资建议", "📄 报告导出"]
        else:
            return ["📈 估值计算", "📋 数据管理", "📊 对比分析", "💡 投资建议", "📄 报告导出", "🔧 API接口"]
    
    def _get_template_info(self) -> str:
        """获取模板信息"""
        template_info_map = {
            "免费版": "🟡 免费版：基础PE/PB估值功能",
            "专业版": "🔵 专业版：全功能 + 报告导出",
            "企业版": "🟢 企业版：全功能 + API + 定制服务"
        }
        return template_info_map[self.template_level]
    
    def _render_valuation_calculation(self):
        """渲染估值计算界面"""
        st.header("🎯 目标公司数据输入")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.session_state.target_company['name'] = st.text_input(
                "公司名称", st.session_state.target_company['name']
            )
            st.session_state.target_company['stock_price'] = st.number_input(
                f"股价 ({self.currency_symbol})", 
                value=float(st.session_state.target_company['stock_price']), 
                step=0.01, min_value=0.0
            )
            
        with col2:
            st.session_state.target_company['net_profit'] = st.number_input(
                f"净利润 ({self.unit_text})", 
                value=float(st.session_state.target_company['net_profit']), 
                step=1000.0
            )
            st.session_state.target_company['net_assets'] = st.number_input(
                f"净资产 ({self.unit_text})", 
                value=float(st.session_state.target_company['net_assets']), 
                step=1000.0, min_value=0.0
            )
            
        with col3:
            st.session_state.target_company['ebitda'] = st.number_input(
                f"EBITDA ({self.unit_text})", 
                value=float(st.session_state.target_company['ebitda']), 
                step=1000.0
            )
            st.session_state.target_company['growth_rate'] = st.number_input(
                "净利润增长率 (%)", 
                value=float(st.session_state.target_company['growth_rate']), 
                step=0.1
            )

        # 计算和显示估值指标
        self._display_valuation_metrics()
    
    def _display_valuation_metrics(self):
        """显示估值指标"""
        target_metrics = ValuationEngine.calculate_relative_metrics(st.session_state.target_company)
        
        st.header("🧮 核心估值指标")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            UIComponents.render_metric_card("PE 市盈率", str(target_metrics['pe']), "市值 ÷ 净利润", "#3b82f6")
        
        with col2:
            UIComponents.render_metric_card("PB 市净率", str(target_metrics['pb']), "市值 ÷ 净资产", "#10b981")
        
        with col3:
            UIComponents.render_metric_card("EV/EBITDA", str(target_metrics['ev_ebitda']), "企业价值 ÷ EBITDA", "#8b5cf6")
            
        with col4:
            UIComponents.render_metric_card("EV/EBIT", str(target_metrics['ev_ebit']), "企业价值 ÷ EBIT", "#f59e0b")
            
        with col5:
            UIComponents.render_metric_card("PEG", str(target_metrics['peg']), "PE ÷ 增长率", "#ef4444")
    
    def _render_data_management(self):
        """渲染数据管理界面"""
        st.header("📝 可比公司数据管理")
        st.info("💡 数据管理功能：可比公司增删改查")
        
        # 这里可以添加完整的数据管理实现
    
    def _render_comparison_analysis(self):
        """渲染对比分析界面"""
        st.header("🔍 同行业对比分析")
        st.info("💡 对比分析功能：图表展示和分析")
        
        # 这里可以添加完整的对比分析实现
    
    def _render_investment_advice(self):
        """渲染投资建议界面"""
        st.header("🧠 智能投资建议")
        st.info("💡 投资建议功能：基于算法生成建议")
        
        # 这里可以添加完整的投资建议实现
    
    def _render_report_export(self):
        """渲染报告导出界面"""
        st.header("📋 专业估值分析报告")
        st.info("💡 报告导出功能：生成专业报告")
        
        # 这里可以添加完整的报告导出实现

class DCFValuationModel:
    """DCF估值模型"""
    
    def __init__(self, currency_symbol: str, unit_text: str, template_level: str):
        self.currency_symbol = currency_symbol
        self.unit_text = unit_text
        self.template_level = template_level
    
    def render(self):
        """渲染DCF估值模型界面"""
        dcf_tabs = self._get_dcf_tabs()
        template_info = self._get_dcf_template_info()
        
        st.info(template_info)
        selected_dcf_tab = st.selectbox("选择DCF功能", dcf_tabs)

        if selected_dcf_tab == "📊 DCF计算":
            self._render_dcf_calculation()
        elif selected_dcf_tab == "📈 敏感性分析":
            self._render_sensitivity_analysis()
        # 其他标签页的实现...
    
    def _get_dcf_tabs(self) -> List[str]:
        """获取DCF标签页"""
        if self.template_level == "免费版":
            return ["📊 DCF计算", "📈 敏感性分析"]
        elif self.template_level == "专业版":
            return ["📊 DCF计算", "📈 敏感性分析", "📋 详细预测", "💡 估值建议", "📄 DCF报告"]
        else:
            return ["📊 DCF计算", "📈 敏感性分析", "📋 详细预测", "💡 估值建议", "📄 DCF报告", "🔧 模型导出"]
    
    def _get_dcf_template_info(self) -> str:
        """获取DCF模板信息"""
        template_info_map = {
            "免费版": "🟡 免费版：基础DCF估值功能",
            "专业版": "🔵 专业版：完整DCF + 详细分析",
            "企业版": "🟢 企业版：完整DCF + 模型导出"
        }
        return template_info_map[self.template_level]
    
    def _render_dcf_calculation(self):
        """渲染DCF计算界面"""
        st.header("🎯 DCF估值计算")
        
        # 基础数据输入
        self._render_basic_data_input()
        
        # 收入增长率设置
        self._render_growth_rate_settings()
        
        # 计算和显示DCF结果
        self._calculate_and_display_dcf()
    
    def _render_basic_data_input(self):
        """渲染基础数据输入"""
        st.subheader("📋 基础数据")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.session_state.dcf_data['company_name'] = st.text_input(
                "公司名称", st.session_state.dcf_data['company_name']
            )
            st.session_state.dcf_data['base_revenue'] = st.number_input(
                f"基期收入 (百万{self.currency_symbol})", 
                value=float(st.session_state.dcf_data['base_revenue']), 
                step=10.0, min_value=0.0
            )
            st.session_state.dcf_data['fcf_margin'] = st.number_input(
                "自由现金流率 (%)", 
                value=float(st.session_state.dcf_data['fcf_margin']), 
                step=0.1, min_value=0.0
            )
        
        with col2:
            st.session_state.dcf_data['wacc'] = st.number_input(
                "WACC (%)", 
                value=float(st.session_state.dcf_data['wacc']), 
                step=0.1, min_value=ModelConstants.MIN_WACC
            )
            st.session_state.dcf_data['terminal_growth'] = st.number_input(
                "永续增长率 (%)", 
                value=float(st.session_state.dcf_data['terminal_growth']), 
                step=0.1, min_value=0.0, max_value=ModelConstants.MAX_TERMINAL_GROWTH
            )
            st.session_state.dcf_data['forecast_years'] = st.selectbox(
                "预测年数", [3, 5, 7, 10], 
                index=1
            )
        
        with col3:
            st.session_state.dcf_data['shares_outstanding'] = st.number_input(
                "流通股数 (百万股)", 
                value=float(st.session_state.dcf_data['shares_outstanding']), 
                step=1.0, min_value=0.1
            )
            st.session_state.dcf_data['cash'] = st.number_input(
                f"现金 (百万{self.currency_symbol})", 
                value=float(st.session_state.dcf_data['cash']), 
                step=1.0, min_value=0.0
            )
            st.session_state.dcf_data['debt'] = st.number_input(
                f"债务 (百万{self.currency_symbol})", 
                value=float(st.session_state.dcf_data['debt']), 
                step=1.0, min_value=0.0
            )
    
    def _render_growth_rate_settings(self):
        """渲染收入增长率设置"""
        st.subheader("📈 收入增长率预测")
        forecast_years = st.session_state.dcf_data['forecast_years']
        growth_cols = st.columns(forecast_years)
        
        # 确保增长率列表长度匹配预测年数
        while len(st.session_state.dcf_data['revenue_growth_rates']) < forecast_years:
            st.session_state.dcf_data['revenue_growth_rates'].append(5.0)
        
        # 如果列表太长，截断它
        if len(st.session_state.dcf_data['revenue_growth_rates']) > forecast_years:
            st.session_state.dcf_data['revenue_growth_rates'] = st.session_state.dcf_data['revenue_growth_rates'][:forecast_years]
        
        for i in range(forecast_years):
            with growth_cols[i]:
                st.session_state.dcf_data['revenue_growth_rates'][i] = st.number_input(
                    f"第{i+1}年 (%)", 
                    value=float(st.session_state.dcf_data['revenue_growth_rates'][i]), 
                    step=0.5, key=f"growth_{i}"
                )
    
    def _calculate_and_display_dcf(self):
        """计算并显示DCF结果"""
        # 验证输入数据
        is_valid, errors = DataValidator.validate_dcf_inputs(st.session_state.dcf_data)
        
        if not is_valid:
            st.error("输入数据有误：")
            for error in errors:
                st.error(f"• {error}")
            return
        
        # 创建DCF数据对象并计算
        dcf_data_obj = DCFData(**st.session_state.dcf_data)
        dcf_result = ValuationEngine.calculate_dcf_valuation(dcf_data_obj)
        
        if dcf_result:
            self._display_dcf_results(dcf_result)
            self._display_dcf_charts(dcf_result)
        else:
            st.error("DCF计算失败，请检查输入参数")
    def _display_dcf_results(self, dcf_result: Dict):
        """显示DCF结果"""
        st.subheader("💰 估值结果")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            UIComponents.render_metric_card(
                "企业价值", 
                f"{self.currency_symbol}{dcf_result['enterprise_value']:.1f}M",
                "预测FCF现值 + 终值现值", 
                "#3b82f6"
            )
        
        with col2:
            UIComponents.render_metric_card(
                "股权价值", 
                f"{self.currency_symbol}{dcf_result['equity_value']:.1f}M",
                "企业价值 - 净债务", 
                "#10b981"
            )
        
        with col3:
            UIComponents.render_metric_card(
                "每股价值", 
                f"{self.currency_symbol}{dcf_result['share_price']:.2f}",
                "股权价值 ÷ 流通股数", 
                "#8b5cf6"
            )
        
        with col4:
            terminal_ratio = dcf_result['pv_terminal'] / dcf_result['enterprise_value'] * 100
            UIComponents.render_metric_card(
                "终值占比", 
                f"{terminal_ratio:.1f}%",
                "终值现值 ÷ 企业价值", 
                "#f59e0b"
            )

        # 详细分解表格
        st.subheader("📊 估值分解")
        self._display_dcf_breakdown_table(dcf_result)
    
    def _display_dcf_breakdown_table(self, dcf_result: Dict):
        """显示DCF分解表格"""
        forecast_df = pd.DataFrame({
            '年份': dcf_result['years'],
            f'自由现金流 (百万{self.currency_symbol})': [round(fcf, 1) for fcf in dcf_result['forecasted_fcf']],
            f'现值 (百万{self.currency_symbol})': [round(pv, 1) for pv in dcf_result['pv_fcf']],
            '贴现因子': [round(1/((1 + st.session_state.dcf_data['wacc']/100)**(i+1)), 3) 
                       for i in range(len(dcf_result['years']))]
        })
        
        st.dataframe(forecast_df, use_container_width=True)
    
    def _display_dcf_charts(self, dcf_result: Dict):
        """显示DCF图表"""
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=dcf_result['years'],
            y=dcf_result['forecasted_fcf'],
            name='预测自由现金流',
            marker_color='#3b82f6'
        ))
        
        fig.add_trace(go.Bar(
            x=dcf_result['years'],
            y=dcf_result['pv_fcf'],
            name='现值',
            marker_color='#10b981'
        ))
        
        fig.update_layout(
            title='自由现金流预测与现值',
            xaxis_title='年份',
            yaxis_title=f'金额 (百万{self.currency_symbol})',
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_sensitivity_analysis(self):
        """渲染敏感性分析"""
        st.header("🔍 敏感性分析")
        
        if self.template_level == "免费版":
            st.warning("🔒 此功能需要专业版或企业版订阅")
            return
        
        st.subheader("📊 WACC vs 永续增长率敏感性")
        
        # 敏感性分析参数
        col1, col2 = st.columns(2)
        
        with col1:
            wacc_range = st.slider("WACC变动范围 (±%)", 1.0, 5.0, 2.0, 0.5)
            wacc_steps = st.selectbox("WACC步长数", [5, 7, 9], index=1)
        
        with col2:
            growth_range = st.slider("永续增长率变动范围 (±%)", 0.5, 3.0, 1.5, 0.25)
            growth_steps = st.selectbox("增长率步长数", [5, 7, 9], index=1)
        
        # 生成和显示敏感性分析
        self._generate_sensitivity_analysis(wacc_range, wacc_steps, growth_range, growth_steps)
    
    def _generate_sensitivity_analysis(self, wacc_range: float, wacc_steps: int, 
                                     growth_range: float, growth_steps: int):
        """生成敏感性分析"""
        base_wacc = st.session_state.dcf_data['wacc']
        base_growth = st.session_state.dcf_data['terminal_growth']
        
        wacc_values = np.linspace(base_wacc - wacc_range, base_wacc + wacc_range, wacc_steps)
        growth_values = np.linspace(base_growth - growth_range, base_growth + growth_range, growth_steps)
        
        sensitivity_matrix = []
        
        for wacc in wacc_values:
            row = []
            for growth in growth_values:
                # 确保创建完整的副本
                temp_data = st.session_state.dcf_data.copy()
                temp_data['wacc'] = float(wacc)
                temp_data['terminal_growth'] = float(growth)
                
                try:
                    dcf_data_obj = DCFData(**temp_data)
                    result = ValuationEngine.calculate_dcf_valuation(dcf_data_obj)
                    if result and 'share_price' in result:
                        row.append(result['share_price'])
                    else:
                        row.append(0)
                except Exception as e:
                    logger.error(f"敏感性分析计算错误: {e}")
                    row.append(0)
            
            sensitivity_matrix.append(row)
        
        # 创建敏感性表格
        sensitivity_df = pd.DataFrame(
            sensitivity_matrix,
            index=[f"{wacc:.1f}%" for wacc in wacc_values],
            columns=[f"{growth:.1f}%" for growth in growth_values]
        )
        
        st.write("**每股价值敏感性分析表**")
        st.write("行：WACC | 列：永续增长率")
        
        # 格式化显示
        styled_df = sensitivity_df.style.format(f"{self.currency_symbol}{{:.2f}}")
        st.dataframe(styled_df, use_container_width=True)
        
        # 热力图
        fig = px.imshow(
            sensitivity_matrix,
            x=[f"{g:.1f}%" for g in growth_values],
            y=[f"{w:.1f}%" for w in wacc_values],
            color_continuous_scale='RdYlGn',
            title='每股价值敏感性热力图',
            labels={'x': '永续增长率', 'y': 'WACC', 'color': f'每股价值({self.currency_symbol})'}
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ==================== 报告生成器 ====================
class ReportGenerator:
    """报告生成器"""
    
    @staticmethod
    def generate_dcf_html_report(dcf_data: Dict, dcf_result: Dict, 
                                currency_symbol: str, analyst_name: str, 
                                report_date: str) -> str:
        """生成DCF HTML报告"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{dcf_data['company_name']} DCF估值分析报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }}
        .header {{ text-align: center; border-bottom: 3px solid #3b82f6; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ color: #1f2937; font-size: 28px; margin-bottom: 10px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f8fafc; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #3b82f6; margin-bottom: 5px; }}
        .print-button {{ background: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
        @media print {{ .no-print {{ display: none; }} }}
    </style>
</head>
<body>
    <div class="no-print" style="text-align: center; margin-bottom: 20px;">
        <button class="print-button" onclick="window.print()">🖨️ 打印/保存为PDF</button>
    </div>

    <div class="header">
        <h1>{dcf_data['company_name']} DCF估值分析报告</h1>
        <p><strong>分析师:</strong> {analyst_name} | <strong>报告日期:</strong> {report_date}</p>
        <p><strong>生成平台:</strong> FinancialModel.cn 专业版</p>
    </div>

    <div class="section">
        <h2>📋 执行摘要</h2>
        <p>基于贴现现金流(DCF)分析，{dcf_data['company_name']}的内在价值为<strong>{currency_symbol}{dcf_result['share_price']:.2f}每股</strong>。</p>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{currency_symbol}{dcf_result['enterprise_value']:.1f}M</div>
                <div class="metric-label">企业价值</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{currency_symbol}{dcf_result['equity_value']:.1f}M</div>
                <div class="metric-label">股权价值</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{currency_symbol}{dcf_result['share_price']:.2f}</div>
                <div class="metric-label">每股内在价值</div>
            </div>
        </div>
    </div>
</body>
</html>"""

    @staticmethod
    def create_excel_dcf_model(dcf_data: Dict, dcf_result: Dict) -> bytes:
        """创建Excel DCF模型"""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 输入参数工作表
            input_data = pd.DataFrame({
                '参数名称': ['公司名称', '基期收入(百万)', 'WACC(%)', '永续增长率(%)', '预测年数'],
                '当前数值': [
                    dcf_data['company_name'],
                    dcf_data['base_revenue'],
                    dcf_data['wacc'],
                    dcf_data['terminal_growth'],
                    dcf_data['forecast_years']
                ]
            })
            input_data.to_excel(writer, sheet_name='输入参数', index=False)
            
            # 现金流预测工作表
            if dcf_result:
                forecast_df = pd.DataFrame({
                    '年份': dcf_result['years'],
                    '预测自由现金流': dcf_result['forecasted_fcf'],
                    '现值': dcf_result['pv_fcf']
                })
                forecast_df.to_excel(writer, sheet_name='现金流预测', index=False)
                
                # 估值结果工作表
                valuation_df = pd.DataFrame({
                    '估值项目': ['企业价值', '股权价值', '每股价值'],
                    '金额': [
                        dcf_result['enterprise_value'],
                        dcf_result['equity_value'],
                        dcf_result['share_price']
                    ]
                })
                valuation_df.to_excel(writer, sheet_name='估值结果', index=False)
        
        return output.getvalue()

# ==================== 错误处理和验证 ====================
class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_dcf_inputs(dcf_data: Dict) -> Tuple[bool, List[str]]:
        """验证DCF输入数据"""
        errors = []
        
        try:
            wacc = float(dcf_data.get('wacc', 0))
            terminal_growth = float(dcf_data.get('terminal_growth', 0))
            base_revenue = float(dcf_data.get('base_revenue', 0))
            shares_outstanding = float(dcf_data.get('shares_outstanding', 0))
            
            if wacc <= 0:
                errors.append("WACC必须大于0")
            
            if terminal_growth < 0 or terminal_growth > ModelConstants.MAX_TERMINAL_GROWTH:
                errors.append(f"永续增长率应在0-{ModelConstants.MAX_TERMINAL_GROWTH}%之间")
            
            if wacc <= terminal_growth:
                errors.append("WACC必须大于永续增长率")
            
            if base_revenue <= 0:
                errors.append("基期收入必须大于0")
            
            if shares_outstanding <= 0:
                errors.append("流通股数必须大于0")
                
        except (ValueError, TypeError) as e:
            errors.append(f"数据格式错误: {str(e)}")
        
        return len(errors) == 0, errors

# ==================== 主应用程序 ====================
class FinancialModelApp:
    """金融建模应用主类"""
    
    def __init__(self):
        self.ui_components = UIComponents()
        self.session_manager = SessionStateManager()
        
    def run(self):
        """运行应用程序"""
        # 加载样式
        load_custom_css()
        
        # 初始化session state
        self.session_manager.initialize_session_state()
        
        # 渲染标题
        self._render_header()
        
        # 渲染导航和设置
        selected_category, selected_model = self.ui_components.render_navigation_sidebar()
        currency, currency_symbol, unit_text, template_level = self.ui_components.render_system_settings()
        
        # 渲染版权信息
        self._render_sidebar_footer()
        
        # 渲染主内容
        self._render_main_content(selected_model, currency_symbol, unit_text, template_level)
        
        # 渲染页脚
        self._render_footer(template_level)
    
    def _render_header(self):
        """渲染页面头部"""
        st.markdown('<h1 class="main-header">💰 FinancialModel.cn</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">专业金融建模与分析平台 | 让复杂的金融模型变得简单易用</p>', unsafe_allow_html=True)
    
    def _render_sidebar_footer(self):
        """渲染侧边栏页脚"""
        st.sidebar.markdown("---")
        st.sidebar.markdown("© 2024 FinancialModel.cn")
    
    def _render_main_content(self, selected_model: str, currency_symbol: str, 
                           unit_text: str, template_level: str):
        """渲染主要内容区域"""
        if selected_model == "相对估值模型":
            relative_model = RelativeValuationModel(currency_symbol, unit_text, template_level)
            relative_model.render()
        elif selected_model == "DCF估值模型":
            dcf_model = DCFValuationModel(currency_symbol, unit_text, template_level)
            dcf_model.render()
        else:
            self._render_coming_soon(selected_model)
    
    def _render_coming_soon(self, model_name: str):
        """渲染即将推出页面"""
        st.header(f"🚧 {model_name}")
        
        st.markdown("""
        <div class="coming-soon">
            <h2>📋 功能规划中</h2>
            <p>该模型正在我们的开发计划中，敬请期待！</p>
            <p>想要优先体验？<strong>升级到企业版获得定制开发服务</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # 显示开发路线图
        self._render_roadmap()
    
    def _render_roadmap(self):
        """渲染开发路线图"""
        st.subheader("🗓️ 开发路线图")
        
        roadmap_data = {
            "Q4 2024": ["✅ 相对估值模型", "✅ DCF估值模型", "🔄 投资组合理论"],
            "Q1 2025": ["📋 债券定价模型", "📋 Black-Scholes期权", "📋 VaR风险管理"],
            "Q2 2025": ["📋 财务比率分析", "📋 信用分析模型", "📋 宏观经济模型"]
        }
        
        for quarter, features in roadmap_data.items():
            with st.expander(f"📅 {quarter}"):
                for feature in features:
                    st.write(feature)
    
    def _render_footer(self, template_level: str):
        """渲染页脚"""
        st.markdown("---")
        
        # 统计信息
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("已上线模型", "2", "📈 相对估值 + DCF")
        with col2:
            st.metric("开发中模型", "1", "🔄 投资组合理论") 
        with col3:
            st.metric("规划中模型", "15+", "📋 全品类覆盖")
        with col4:
            st.metric("注册用户", "1,000+", "👥 快速增长")
        
        # 升级提示
        self._render_upgrade_prompts(template_level)
        
        # 版权信息
        st.markdown("""
        <div style="text-align: center; color: #6b7280; padding: 2rem 0;">
            <p>© 2024 <strong>FinancialModel.cn</strong> | 专业金融建模平台</p>
            <p>🚀 让复杂的金融模型变得简单易用 | 💡 为投资决策提供专业支持</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_upgrade_prompts(self, template_level: str):
        """渲染升级提示"""
        if template_level == "免费版":
            st.warning("""
            🎯 **升级到专业版解锁全部功能：**
            - ✅ 无限制使用所有模型
            - ✅ 专业报告导出(Excel/PDF)
            - ✅ 高级图表分析
            - ✅ 优先客服支持
            - ✅ 新模型优先体验
            
            💰 **专业版仅需 ¥199/月 | 企业版 ¥999/月**
            """)
        elif template_level == "专业版":
            st.info("""
            🏢 **企业版专享功能：**
            - ✅ 多用户团队协作
            - ✅ API接口调用
            - ✅ 定制模型开发
            - ✅ 专属客户经理
            - ✅ 私有化部署选项
            
            💼 **企业版 ¥999/月，支持团队使用**
            """)

# ==================== 程序入口 ====================
def main():
    """主函数"""
    try:
        app = FinancialModelApp()
        app.run()
    except Exception as e:
        logger.error(f"应用程序运行时发生错误: {e}")
        st.error("系统出现错误，请刷新页面重试")
        
        # 在开发模式下显示详细错误信息
        if st.checkbox("显示详细错误信息"):
            st.exception(e)

if __name__ == "__main__":
    main()
