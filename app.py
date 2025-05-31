# Excel模型下载（完整版本）
                                def create_dcf_excel():
                                    from io import BytesIO
                                    import pandas as pd
                                    
                                    output = BytesIO()
                                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                        # 1. 输入参数工作表
                                        input_data = pd.DataFrame({
                                            '参数名称': [
                                                '公司名称', '基期收入(百万)', '自由现金流率(%)', 'WACC(%)', 
                                                '永续增长率(%)', '预测年数', '流通股数(百万股)', 
                                                '现金(百万)', '债务(百万)', '分析师', '报告日期'
                                            ],
                                            '当前数值': [
                                                str(st.session_state.dcf_data['company_name']),
                                                float(st.session_state.dcf_data['base_revenue']),
                                                float(st.session_state.dcf_data['fcf_margin']),
                                                float(st.session_state.dcf_data['wacc']),
                                                float(st.session_state.dcf_data['terminal_growth']),
                                                int(st.session_state.dcf_data['forecast_years']),
                                                float(st.session_state.dcf_data['shares_outstanding']),
                                                float(st.session_state.dcf_data['cash']),
                                                float(st.session_state.dcf_data['debt']),
                                                '分析师姓名',
                                                datetime.now().strftime('%Y-%m-%d')
                                            ],
                                            '说明': [
                                                '目标公司名称',
                                                '最近一年的营业收入',
                                                '自由现金流占收入的比例',
                                                '加权平均资本成本',
                                                '永续期增长率',
                                                '详细预测的年数',
                                                '已发行流通股份数量',
                                                '现金及现金等价物',
                                                '总债务',
                                                '负责分析师',
                                                '模型生成日期'
                                            ]
                                        })
                                        input_data.to_excel(writer, sheet_name='输入参数', index=False)
                                        
                                        # 2. 收入增长率设置
                                        growth_data = []
                                        for i in range(st.session_state.dcf_data['forecast_years']):
                                            if i < len(st.session_state.dcf_data['revenue_growth_rates']):
                                                growth_rate = st.session_state.dcf_data['revenue_growth_rates'][i]
                                            else:
                                                growth_rate = st.session_state.dcf_data['revenue_growth_rates'][-1]
                                            growth_data.append({
                                                '年份': f'第{i+1}年',
                                                '收入增长率(%)': float(growth_rate),
                                                '说明': f'预测第{i+1}年的收入增长率'
                                            })
                                        
                                        growth_df = pd.DataFrame(growth_data)
                                        growth_df.to_excel(writer, sheet_name='增长率设置', index=False)
                                        
                                        # 3. 详细现金流预测
                                        years = list(range(1, st.session_state.dcf_data['forecast_years'] + 1))
                                        detailed_forecast = []
                                        revenue = float(st.session_state.dcf_data['base_revenue'])
                                        
                                        for i, year in enumerate(years):
                                            if i < len(st.session_state.dcf_data['revenue_growth_rates']):
                                                growth = float(st.session_state.dcf_data['revenue_growth_rates'][i]) / 100
                                            else:
                                                growth = float(st.session_state.dcf_data['revenue_growth_rates'][-1]) / 100
                                            
                                            revenue = revenue * (1 + growth)
                                            fcf = revenue * float(st.session_state.dcf_data['fcf_margin']) / 100
                                            discount_factor = 1 / ((1 + float(st.session_state.dcf_data['wacc'])/100) ** year)
                                            present_value = fcf * discount_factor
                                            
                                            detailed_forecast.append({
                                                '年份': f'第{year}年',
                                                '预测收入': round(revenue, 1),
                                                '收入增长率(%)': round(growth * 100, 1),
                                                '自由现金流': round(fcf, 1),
                                                '贴现因子': round(discount_factor, 4),
                                                '现值': round(present_value, 1)
                                            })
                                        
                                        forecast_df = pd.DataFrame(detailed_forecast)
                                        forecast_df.to_excel(writer, sheet_name='现金流预测', index=False)
                                        
                                        # 4. 终值计算详细步骤
                                        terminal_fcf = detailed_forecast[-1]['自由现金流'] * (1 + float(st.session_state.dcf_data['terminal_growth'])/100)
                                        terminal_value = terminal_fcf / (float(st.session_state.dcf_data['wacc'])/100 - float(st.session_state.dcf_data['terminal_growth'])/100)
                                        terminal_pv = terminal_value / ((1 + float(st.session_state.dcf_data['wacc'])/100) ** int(st.session_state.dcf_data['forecast_years']))
                                        
                                        terminal_calc = pd.DataFrame({
                                            '计算项目': [
                                                '最后一年自由现金流',
                                                '永续增长率(%)',
                                                '终值期自由现金流',
                                                'WACC(%)',
                                                '终值',
                                                '终值现值',
                                                '终值占企业价值比例(%)'
                                            ],
                                            '数值': [
                                                round(detailed_forecast[-1]['自由现金流'], 1),
                                                float(st.session_state.dcf_data['terminal_growth']),
                                                round(terminal_fcf, 1),
                                                float(st.session_state.dcf_data['wacc']),
                                                round(terminal_value, 1),
                                                round(terminal_pv, 1),
                                                round(terminal_pv / dcf_result['enterprise_value'] * 100, 1)
                                            ],
                                            '说明': [
                                                '来自现金流预测表',
                                                '输入参数',
                                                '最后一年FCF乘以增长率',
                                                '输入参数',
                                                '终值期FCF除以贴现率差',
                                                '终值的现值',
                                                '终值现值占企业价值比例'
                                            ]
                                        })
                                        terminal_calc.to_excel(writer, sheet_name='终值计算', index=False)
                                        
                                        # 5. 完整估值汇总
                                        valuation_summary = pd.DataFrame({
                                            '估值组成': [
                                                '预测期现金流现值',
                                                '终值现值',
                                                '企业价值(EV)',
                                                '加现金及等价物',
                                                '减总债务',
                                                '股权价值',
                                                '流通股数(百万股)',
                                                '每股内在价值'
                                            ],
                                            '金额(百万)': [
                                                round(dcf_result['total_pv_fcf'], 1),
                                                round(dcf_result['pv_terminal'], 1),
                                                round(dcf_result['enterprise_value'], 1),
                                                float(st.session_state.dcf_data['cash']),
                                                float(st.session_state.dcf_data['debt']),
                                                round(dcf_result['equity_value'], 1),
                                                float(st.session_state.dcf_data['shares_outstanding']),
                                                round(dcf_result['share_price'], 2)
                                            ],
                                            '占EV比例(%)': [
                                                round(dcf_result['total_pv_fcf'] / dcf_result['enterprise_value'] * 100, 1),
                                                round(dcf_result['pv_terminal'] / dcf_result['enterprise_value'] * 100, 1),
                                                100.0,
                                                0.0,
                                                0.0,
                                                0.0,
                                                0.0,
                                                0.0
                                            ]
                                        })
                                        valuation_summary.to_excel(writer, sheet_name='估值汇总', index=False)
                                        
                                        # 6. 敏感性分析矩阵
                                        wacc_range_values = [6.0, 7.0, 8.0, 8.5, 9.0, 10.0, 11.0]
                                        growth_range_values = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
                                        
                                        sensitivity_data = []
                                        for wacc in wacc_range_values:
                                            row_data = {'WACC': f"{wacc}%"}
                                            for growth in growth_range_values:
                                                temp_data = st.session_state.dcf_data.copy()
                                                temp_data['wacc'] = wacc
                                                temp_data['terminal_growth'] = growth
                                                result = calculate_dcf_valuation(temp_data)
                                                if result:
                                                    row_data[f"增长率{growth}%"] = round(result['share_price'], 2)
                                                else:
                                                    row_data[f"增长率{growth}%"] = 0.0
                                            sensitivity_data.append(row_data)
                                        
                                        sensitivity_df = pd.DataFrame(sensitivity_data)
                                        sensitivity_df.to_excel(writer, sheet_name='敏感性分析', index=False)
                                        
                                        # 7. 使用说明
                                        instructions = pd.DataFrame({
                                            'DCF模型使用指南': [
                                                '基本使用方法',
                                                '1. 在输import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import math
import io
import base64
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="FinancialModel.cn - 专业金融建模平台",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
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

# 标题区域
st.markdown('<h1 class="main-header">💰 FinancialModel.cn</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">专业金融建模与分析平台 | 让复杂的金融模型变得简单易用</p>', unsafe_allow_html=True)

# 侧边栏 - 主导航
st.sidebar.header("🧭 金融模型导航")

# 模型分类 - 现在有相对估值和DCF模型可用
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

# 选择主分类
selected_category = st.sidebar.selectbox(
    "选择模型分类",
    list(model_categories.keys()),
    index=0
)

# 选择具体模型
available_models = model_categories[selected_category]
selected_model = st.sidebar.selectbox(
    "选择具体模型",
    list(available_models.keys()),
    format_func=lambda x: f"{x} {available_models[x]}"
)

# 系统设置
st.sidebar.header("⚙️ 系统设置")
currency = st.sidebar.selectbox("💱 币种选择", ["CNY (人民币)", "USD (美元)"], index=0)
template_level = st.sidebar.selectbox("🎯 订阅级别", ["免费版", "专业版", "企业版"], index=1)

currency_symbol = "￥" if currency.startswith("CNY") else "$"
unit_text = "万元" if currency.startswith("CNY") else "万美元"

# 显示订阅信息
subscription_info = {
    "免费版": "🆓 每月3次分析 | 基础功能",
    "专业版": "⭐ 无限分析 | 完整功能 | 报告导出", 
    "企业版": "🏢 多用户 | API接口 | 定制服务"
}
st.sidebar.info(subscription_info[template_level])

# 版权信息
st.sidebar.markdown("---")
st.sidebar.markdown("© 2024 FinancialModel.cn")

# 主内容区域
if selected_model == "相对估值模型":
    # 这里是你完整的现有估值模型代码
    # 为了节省空间，我只放主要结构，你需要把完整的估值代码放在这里
    
    # 根据模板级别显示不同功能
    if template_level == "免费版":
        available_tabs = ["📈 估值计算", "📊 对比分析"]
        template_info = "🟡 免费版：基础PE/PB估值功能"
    elif template_level == "专业版":
        available_tabs = ["📈 估值计算", "📋 数据管理", "📊 对比分析", "💡 投资建议", "📄 报告导出"]
        template_info = "🔵 专业版：全功能 + 报告导出"
    else:  # 企业版
        available_tabs = ["📈 估值计算", "📋 数据管理", "📊 对比分析", "💡 投资建议", "📄 报告导出", "🔧 API接口"]
        template_info = "🟢 企业版：全功能 + API + 定制服务"

    # 显示模板信息
    st.info(template_info)

    # 功能导航
    selected_tab = st.selectbox("选择功能模块", available_tabs)

    # 初始化session state
    if 'target_company' not in st.session_state:
        st.session_state.target_company = {
            'name': '目标公司',
            'stock_price': 45.60,
            'total_shares': 12.5,
            'net_profit': 35000,
            'net_assets': 180000,
            'ebitda': 65000,
            'ebit': 52000,
            'cash': 25000,
            'debt': 85000,
            'growth_rate': 12.5
        }

    if 'comparable_companies' not in st.session_state:
        st.session_state.comparable_companies = [
            {'name': '同行A', 'stock_price': 38.50, 'total_shares': 10.2, 'net_profit': 28000, 'net_assets': 150000, 'ebitda': 55000, 'ebit': 42000, 'cash': 20000, 'debt': 70000, 'growth_rate': 10.2},
            {'name': '同行B', 'stock_price': 52.30, 'total_shares': 15.8, 'net_profit': 45000, 'net_assets': 220000, 'ebitda': 78000, 'ebit': 62000, 'cash': 35000, 'debt': 95000, 'growth_rate': 15.8}
        ]

    # 计算估值指标的函数
    def calculate_metrics(company_data):
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
                'peg': round((market_cap / (company_data['net_profit'] / 10000)) / company_data['growth_rate'], 2) if company_data['growth_rate'] > 0 and company_data['net_profit'] > 0 else 0
            }
            
            return metrics
        except:
            return {'market_cap': 0, 'enterprise_value': 0, 'pe': 0, 'pb': 0, 'ev_ebitda': 0, 'ev_ebit': 0, 'peg': 0}

    # 这里放你完整的估值模型代码
    # 包括所有的标签页功能：估值计算、数据管理、对比分析、投资建议、报告导出
    
    if selected_tab == "📈 估值计算":
        st.header("🎯 目标公司数据输入")
        
        # 简化展示 - 实际使用时放入你的完整代码
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.session_state.target_company['name'] = st.text_input("公司名称", st.session_state.target_company['name'])
            st.session_state.target_company['stock_price'] = st.number_input(f"股价 ({currency_symbol})", value=float(st.session_state.target_company['stock_price']), step=0.01, min_value=0.0)
            
        with col2:
            st.session_state.target_company['net_profit'] = st.number_input(f"净利润 ({unit_text})", value=float(st.session_state.target_company['net_profit']), step=1000.0)
            st.session_state.target_company['net_assets'] = st.number_input(f"净资产 ({unit_text})", value=float(st.session_state.target_company['net_assets']), step=1000.0, min_value=0.0)
            
        with col3:
            st.session_state.target_company['ebitda'] = st.number_input(f"EBITDA ({unit_text})", value=float(st.session_state.target_company['ebitda']), step=1000.0)
            st.session_state.target_company['growth_rate'] = st.number_input("净利润增长率 (%)", value=float(st.session_state.target_company['growth_rate']), step=0.1)

        # 计算目标公司指标
        target_metrics = calculate_metrics(st.session_state.target_company)
        
        # 显示核心估值指标
        st.header("🧮 核心估值指标")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #3b82f6; font-size: 2rem; margin: 0;">{target_metrics['pe']}</h3>
                <p style="margin: 0; color: #6b7280;">PE 市盈率</p>
                <small style="color: #9ca3af;">市值 ÷ 净利润</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #10b981; font-size: 2rem; margin: 0;">{target_metrics['pb']}</h3>
                <p style="margin: 0; color: #6b7280;">PB 市净率</p>
                <small style="color: #9ca3af;">市值 ÷ 净资产</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #8b5cf6; font-size: 2rem; margin: 0;">{target_metrics['ev_ebitda']}</h3>
                <p style="margin: 0; color: #6b7280;">EV/EBITDA</p>
                <small style="color: #9ca3af;">企业价值 ÷ EBITDA</small>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #f59e0b; font-size: 2rem; margin: 0;">{target_metrics['ev_ebit']}</h3>
                <p style="margin: 0; color: #6b7280;">EV/EBIT</p>
                <small style="color: #9ca3af;">企业价值 ÷ EBIT</small>
            </div>
            """, unsafe_allow_html=True)
            
        with col5:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #ef4444; font-size: 2rem; margin: 0;">{target_metrics['peg']}</h3>
                <p style="margin: 0; color: #6b7280;">PEG</p>
                <small style="color: #9ca3af;">PE ÷ 增长率</small>
            </div>
            """, unsafe_allow_html=True)
    
    elif selected_tab == "📋 数据管理":
        st.header("📝 可比公司数据管理")
        st.info("💡 这里放入你完整的数据管理代码")
        
    elif selected_tab == "📊 对比分析":
        st.header("🔍 同行业对比分析")
        st.info("💡 这里放入你完整的对比分析代码")
        
    elif selected_tab == "💡 投资建议":
        st.header("🧠 智能投资建议")
        st.info("💡 这里放入你完整的投资建议代码")
        
    elif selected_tab == "📄 报告导出":
        st.header("📋 专业估值分析报告")
        st.info("💡 这里放入你完整的报告导出代码")

elif selected_model == "DCF估值模型":
    # 根据模板级别显示不同功能
    if template_level == "免费版":
        dcf_tabs = ["📊 DCF计算", "📈 敏感性分析"]
        template_info = "🟡 免费版：基础DCF估值功能"
    elif template_level == "专业版":
        dcf_tabs = ["📊 DCF计算", "📈 敏感性分析", "📋 详细预测", "💡 估值建议", "📄 DCF报告"]
        template_info = "🔵 专业版：完整DCF + 详细分析"
    else:  # 企业版
        dcf_tabs = ["📊 DCF计算", "📈 敏感性分析", "📋 详细预测", "💡 估值建议", "📄 DCF报告", "🔧 模型导出"]
        template_info = "🟢 企业版：完整DCF + 模型导出"

    st.info(template_info)
    selected_dcf_tab = st.selectbox("选择DCF功能", dcf_tabs)

    # 初始化DCF数据
    if 'dcf_data' not in st.session_state:
        st.session_state.dcf_data = {
            'company_name': '目标公司',
            'base_revenue': 1000.0,  # 基期收入(百万)
            'base_fcf': 100.0,       # 基期自由现金流(百万)
            'revenue_growth_rates': [15.0, 12.0, 10.0, 8.0, 6.0],  # 前5年收入增长率
            'fcf_margin': 10.0,      # 自由现金流率
            'wacc': 8.5,             # 加权平均资本成本
            'terminal_growth': 2.5,   # 永续增长率
            'forecast_years': 5,      # 预测年数
            'shares_outstanding': 100.0,  # 流通股数(百万股)
            'cash': 50.0,             # 现金(百万)
            'debt': 200.0             # 债务(百万)
        }

    def calculate_dcf_valuation(data):
        """计算DCF估值"""
        try:
            # 预测期现金流
            forecasted_fcf = []
            revenue = data['base_revenue']
            
            for i in range(data['forecast_years']):
                if i < len(data['revenue_growth_rates']):
                    growth_rate = data['revenue_growth_rates'][i] / 100
                else:
                    growth_rate = data['revenue_growth_rates'][-1] / 100
                
                revenue = revenue * (1 + growth_rate)
                fcf = revenue * data['fcf_margin'] / 100
                forecasted_fcf.append(fcf)
            
            # 贴现预测期现金流
            wacc = data['wacc'] / 100
            pv_fcf = []
            total_pv_fcf = 0
            
            for i, fcf in enumerate(forecasted_fcf):
                pv = fcf / ((1 + wacc) ** (i + 1))
                pv_fcf.append(pv)
                total_pv_fcf += pv
            
            # 终值计算
            terminal_fcf = forecasted_fcf[-1] * (1 + data['terminal_growth'] / 100)
            terminal_value = terminal_fcf / (wacc - data['terminal_growth'] / 100)
            pv_terminal = terminal_value / ((1 + wacc) ** data['forecast_years'])
            
            # 企业价值和股权价值
            enterprise_value = total_pv_fcf + pv_terminal
            equity_value = enterprise_value + data['cash'] - data['debt']
            share_price = equity_value / data['shares_outstanding']
            
            return {
                'forecasted_fcf': forecasted_fcf,
                'pv_fcf': pv_fcf,
                'total_pv_fcf': total_pv_fcf,
                'terminal_value': terminal_value,
                'pv_terminal': pv_terminal,
                'enterprise_value': enterprise_value,
                'equity_value': equity_value,
                'share_price': share_price,
                'years': list(range(1, data['forecast_years'] + 1))
            }
        except:
            return None

    if selected_dcf_tab == "📊 DCF计算":
        st.header("🎯 DCF估值计算")
        
        # 基础数据输入
        st.subheader("📋 基础数据")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.session_state.dcf_data['company_name'] = st.text_input(
                "公司名称", st.session_state.dcf_data['company_name']
            )
            st.session_state.dcf_data['base_revenue'] = st.number_input(
                f"基期收入 (百万{currency_symbol})", 
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
                step=0.1, min_value=0.1
            )
            st.session_state.dcf_data['terminal_growth'] = st.number_input(
                "永续增长率 (%)", 
                value=float(st.session_state.dcf_data['terminal_growth']), 
                step=0.1, min_value=0.0
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
                f"现金 (百万{currency_symbol})", 
                value=float(st.session_state.dcf_data['cash']), 
                step=1.0, min_value=0.0
            )
            st.session_state.dcf_data['debt'] = st.number_input(
                f"债务 (百万{currency_symbol})", 
                value=float(st.session_state.dcf_data['debt']), 
                step=1.0, min_value=0.0
            )

        # 收入增长率设置
        st.subheader("📈 收入增长率预测")
        growth_cols = st.columns(st.session_state.dcf_data['forecast_years'])
        
        # 确保增长率列表长度匹配预测年数
        while len(st.session_state.dcf_data['revenue_growth_rates']) < st.session_state.dcf_data['forecast_years']:
            st.session_state.dcf_data['revenue_growth_rates'].append(5.0)
        
        for i in range(st.session_state.dcf_data['forecast_years']):
            with growth_cols[i]:
                st.session_state.dcf_data['revenue_growth_rates'][i] = st.number_input(
                    f"第{i+1}年 (%)", 
                    value=float(st.session_state.dcf_data['revenue_growth_rates'][i]), 
                    step=0.5, key=f"growth_{i}"
                )

        # 计算DCF估值
        dcf_result = calculate_dcf_valuation(st.session_state.dcf_data)
        
        if dcf_result:
            st.subheader("💰 估值结果")
            
            # 核心指标展示
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="color: #3b82f6; font-size: 2rem; margin: 0;">{currency_symbol}{dcf_result['enterprise_value']:.1f}M</h3>
                    <p style="margin: 0; color: #6b7280;">企业价值</p>
                    <small style="color: #9ca3af;">预测FCF现值 + 终值现值</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="color: #10b981; font-size: 2rem; margin: 0;">{currency_symbol}{dcf_result['equity_value']:.1f}M</h3>
                    <p style="margin: 0; color: #6b7280;">股权价值</p>
                    <small style="color: #9ca3af;">企业价值 - 净债务</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="color: #8b5cf6; font-size: 2rem; margin: 0;">{currency_symbol}{dcf_result['share_price']:.2f}</h3>
                    <p style="margin: 0; color: #6b7280;">每股价值</p>
                    <small style="color: #9ca3af;">股权价值 ÷ 流通股数</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                terminal_ratio = dcf_result['pv_terminal'] / dcf_result['enterprise_value'] * 100
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="color: #f59e0b; font-size: 2rem; margin: 0;">{terminal_ratio:.1f}%</h3>
                    <p style="margin: 0; color: #6b7280;">终值占比</p>
                    <small style="color: #9ca3af;">终值现值 ÷ 企业价值</small>
                </div>
                """, unsafe_allow_html=True)

            # 详细分解表格
            st.subheader("📊 估值分解")
            
            # 创建详细预测表
            forecast_df = pd.DataFrame({
                '年份': dcf_result['years'],
                f'自由现金流 (百万{currency_symbol})': [round(fcf, 1) for fcf in dcf_result['forecasted_fcf']],
                f'现值 (百万{currency_symbol})': [round(pv, 1) for pv in dcf_result['pv_fcf']],
                '贴现因子': [round(1/((1 + st.session_state.dcf_data['wacc']/100)**(i+1)), 3) for i in range(len(dcf_result['years']))]
            })
            
            st.dataframe(forecast_df, use_container_width=True)
            
            # 现金流图表
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
                yaxis_title=f'金额 (百万{currency_symbol})',
                barmode='group',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)

    elif selected_dcf_tab == "📈 敏感性分析":
        st.header("🔍 敏感性分析")
        
        if 'dcf_data' in st.session_state:
            st.subheader("📊 WACC vs 永续增长率敏感性")
            
            # 敏感性分析参数
            col1, col2 = st.columns(2)
            
            with col1:
                wacc_range = st.slider("WACC变动范围 (±%)", 1.0, 5.0, 2.0, 0.5)
                wacc_steps = st.selectbox("WACC步长数", [5, 7, 9], index=1)
            
            with col2:
                growth_range = st.slider("永续增长率变动范围 (±%)", 0.5, 3.0, 1.5, 0.25)
                growth_steps = st.selectbox("增长率步长数", [5, 7, 9], index=1)
            
            # 生成敏感性分析表
            base_wacc = st.session_state.dcf_data['wacc']
            base_growth = st.session_state.dcf_data['terminal_growth']
            
            wacc_values = np.linspace(base_wacc - wacc_range, base_wacc + wacc_range, wacc_steps)
            growth_values = np.linspace(base_growth - growth_range, base_growth + growth_range, growth_steps)
            
            sensitivity_matrix = []
            
            for wacc in wacc_values:
                row = []
                for growth in growth_values:
                    # 临时修改参数
                    temp_data = st.session_state.dcf_data.copy()
                    temp_data['wacc'] = wacc
                    temp_data['terminal_growth'] = growth
                    
                    result = calculate_dcf_valuation(temp_data)
                    if result:
                        row.append(result['share_price'])
                    else:
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
            styled_df = sensitivity_df.style.format(f"{currency_symbol}{{:.2f}}")
            st.dataframe(styled_df, use_container_width=True)
            
            # 热力图
            fig = px.imshow(
                sensitivity_matrix,
                x=[f"{g:.1f}%" for g in growth_values],
                y=[f"{w:.1f}%" for w in wacc_values],
                color_continuous_scale='RdYlGn',
                title='每股价值敏感性热力图',
                labels={'x': '永续增长率', 'y': 'WACC', 'color': f'每股价值({currency_symbol})'}
            )
            
            st.plotly_chart(fig, use_container_width=True)

    elif selected_dcf_tab == "📋 详细预测":
        st.header("📈 详细财务预测")
        
        if template_level == "免费版":
            st.warning("🔒 此功能需要专业版或企业版订阅")
        else:
            st.subheader("📊 详细财务建模")
            st.info("💡 专业版功能：详细的财务报表预测模型")
        
    elif selected_dcf_tab == "💡 估值建议":
        st.header("🧠 DCF估值建议")
        
        if template_level == "免费版":
            st.warning("🔒 此功能需要专业版或企业版订阅")
        else:
            st.info("💡 专业版功能：基于DCF结果的投资建议")
        
    elif selected_dcf_tab == "📄 DCF报告":
        st.header("📋 DCF估值报告")
        
        if template_level == "免费版":
            st.warning("🔒 此功能需要专业版或企业版订阅")
        else:
            if 'dcf_data' in st.session_state:
                dcf_result = calculate_dcf_valuation(st.session_state.dcf_data)
                
                if dcf_result:
                    st.subheader("📊 生成专业估值报告")
                    
                    # 报告参数设置
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        report_title = st.text_input("报告标题", f"{st.session_state.dcf_data['company_name']} DCF估值分析报告")
                        analyst_name = st.text_input("分析师", "FinancialModel.cn")
                        report_date = st.date_input("报告日期", datetime.now())
                    
                    with col2:
                        include_charts = st.checkbox("包含图表", True)
                        include_sensitivity = st.checkbox("包含敏感性分析", True)
                        report_language = st.selectbox("报告语言", ["中文", "English"], index=0)
                    
                    if st.button("🔄 生成报告", type="primary"):
                        with st.spinner("正在生成报告..."):
                            # 模拟报告生成
                            progress_bar = st.progress(0)
                            for i in range(100):
                                progress_bar.progress(i + 1)
                            
                            # 报告内容预览
                            st.success("✅ 报告生成完成！")
                            
                            # 创建专业的HTML报告
                            report_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title}</title>
    <style>
        @media print {{
            .no-print {{ display: none; }}
        }}
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #1f2937;
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #3b82f6;
            border-left: 4px solid #3b82f6;
            padding-left: 15px;
            font-size: 20px;
        }}
        .section h3 {{
            color: #1f2937;
            font-size: 16px;
            margin-top: 20px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
            text-align: center;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #3b82f6;
            margin-bottom: 5px;
        }}
        .metric-label {{
            color: #6b7280;
            font-size: 14px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #e5e7eb;
            padding: 12px;
            text-align: right;
        }}
        th {{
            background-color: #f3f4f6;
            font-weight: bold;
            color: #1f2937;
        }}
        .assumptions {{
            background: #dbeafe;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .risk-warning {{
            background: #fef3c7;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #f59e0b;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            color: #6b7280;
            font-size: 12px;
            margin-top: 40px;
            border-top: 1px solid #e5e7eb;
            padding-top: 20px;
        }}
        .print-button {{
            background: #3b82f6;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px;
        }}
        .print-button:hover {{
            background: #2563eb;
        }}
    </style>
</head>
<body>
    <div class="no-print" style="text-align: center; margin-bottom: 20px;">
        <button class="print-button" onclick="window.print()">🖨️ 打印/保存为PDF</button>
        <button class="print-button" onclick="downloadReport()">💾 下载HTML报告</button>
    </div>

    <div class="header">
        <h1>{report_title}</h1>
        <div class="meta">
            <p><strong>分析师:</strong> {analyst_name} | <strong>报告日期:</strong> {report_date}</p>
            <p><strong>生成平台:</strong> FinancialModel.cn 专业版</p>
        </div>
    </div>

    <div class="section">
        <h2>📋 执行摘要</h2>
        <p>基于贴现现金流(DCF)分析，{st.session_state.dcf_data['company_name']}的内在价值为<strong>{currency_symbol}{dcf_result['share_price']:.2f}每股</strong>。</p>
        
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
            <div class="metric-card">
                <div class="metric-value">{(dcf_result['pv_terminal'] / dcf_result['enterprise_value'] * 100):.1f}%</div>
                <div class="metric-label">终值占比</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>🔢 关键假设</h2>
        <div class="assumptions">
            <h3>核心估值参数</h3>
            <ul>
                <li><strong>加权平均资本成本(WACC):</strong> {st.session_state.dcf_data['wacc']:.1f}%</li>
                <li><strong>永续增长率:</strong> {st.session_state.dcf_data['terminal_growth']:.1f}%</li>
                <li><strong>预测期:</strong> {st.session_state.dcf_data['forecast_years']}年</li>
                <li><strong>自由现金流率:</strong> {st.session_state.dcf_data['fcf_margin']:.1f}%</li>
                <li><strong>基期收入:</strong> {st.session_state.dcf_data['base_revenue']:.1f}百万{currency_symbol}</li>
            </ul>
        </div>
    </div>

    <div class="section">
        <h2>📊 现金流预测与估值分解</h2>
        <table>
            <thead>
                <tr>
                    <th>年份</th>
                    <th>自由现金流(百万{currency_symbol})</th>
                    <th>贴现因子</th>
                    <th>现值(百万{currency_symbol})</th>
                </tr>
            </thead>
            <tbody>"""
                            
                            # 添加现金流预测表格数据
                            for i, year in enumerate(dcf_result['years']):
                                discount_factor = 1/((1 + st.session_state.dcf_data['wacc']/100)**(i+1))
                                report_html += f"""
                <tr>
                    <td>第{year}年</td>
                    <td>{dcf_result['forecasted_fcf'][i]:.1f}</td>
                    <td>{discount_factor:.3f}</td>
                    <td>{dcf_result['pv_fcf'][i]:.1f}</td>
                </tr>"""
                            
                            report_html += f"""
            </tbody>
        </table>
        
        <h3>估值汇总</h3>
        <table>
            <tbody>
                <tr><td>预测期现金流现值</td><td>{dcf_result['total_pv_fcf']:.1f}百万{currency_symbol}</td></tr>
                <tr><td>终值</td><td>{dcf_result['terminal_value']:.1f}百万{currency_symbol}</td></tr>
                <tr><td>终值现值</td><td>{dcf_result['pv_terminal']:.1f}百万{currency_symbol}</td></tr>
                <tr style="background-color: #e0f2fe;"><td><strong>企业价值</strong></td><td><strong>{dcf_result['enterprise_value']:.1f}百万{currency_symbol}</strong></td></tr>
                <tr><td>加: 现金及等价物</td><td>{st.session_state.dcf_data['cash']:.1f}百万{currency_symbol}</td></tr>
                <tr><td>减: 总债务</td><td>{st.session_state.dcf_data['debt']:.1f}百万{currency_symbol}</td></tr>
                <tr style="background-color: #e8f5e8;"><td><strong>股权价值</strong></td><td><strong>{dcf_result['equity_value']:.1f}百万{currency_symbol}</strong></td></tr>
                <tr><td>流通股数</td><td>{st.session_state.dcf_data['shares_outstanding']:.1f}百万股</td></tr>
                <tr style="background-color: #fff3cd;"><td><strong>每股内在价值</strong></td><td><strong>{currency_symbol}{dcf_result['share_price']:.2f}</strong></td></tr>
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>📈 收入增长率假设</h2>
        <table>
            <thead>
                <tr>
                    <th>年份</th>
                    <th>收入增长率(%)</th>
                    <th>预测收入(百万{currency_symbol})</th>
                </tr>
            </thead>
            <tbody>"""
                            
                            # 添加收入增长率表格
                            revenue = st.session_state.dcf_data['base_revenue']
                            for i in range(st.session_state.dcf_data['forecast_years']):
                                if i < len(st.session_state.dcf_data['revenue_growth_rates']):
                                    growth_rate = st.session_state.dcf_data['revenue_growth_rates'][i]
                                else:
                                    growth_rate = st.session_state.dcf_data['revenue_growth_rates'][-1]
                                
                                revenue = revenue * (1 + growth_rate/100)
                                report_html += f"""
                <tr>
                    <td>第{i+1}年</td>
                    <td>{growth_rate:.1f}%</td>
                    <td>{revenue:.1f}</td>
                </tr>"""
                            
                            report_html += f"""
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>⚠️ 风险提示</h2>
        <div class="risk-warning">
            <h3>重要声明</h3>
            <ul>
                <li>本DCF估值模型基于当前可获得的信息和合理假设</li>
                <li>实际投资结果可能因市场环境变化而与预期不符</li>
                <li>终值占企业价值比重为{(dcf_result['pv_terminal'] / dcf_result['enterprise_value'] * 100):.1f}%，需关注长期假设的合理性</li>
                <li>建议结合相对估值、同业比较等其他估值方法进行综合判断</li>
                <li>投资决策应考虑个人风险承受能力和投资目标</li>
            </ul>
        </div>
    </div>

    <div class="section">
        <h2>📝 方法论说明</h2>
        <h3>DCF模型原理</h3>
        <p>贴现现金流(DCF)估值法通过预测公司未来的自由现金流，并使用适当的贴现率将其折现至现值，从而得出公司的内在价值。</p>
        
        <h3>关键计算步骤</h3>
        <ol>
            <li><strong>预测自由现金流:</strong> 基于收入增长预测和现金流率假设</li>
            <li><strong>计算贴现率:</strong> 使用WACC作为贴现率</li>
            <li><strong>终值计算:</strong> 采用永续增长模型计算终值</li>
            <li><strong>估值汇总:</strong> 将预测期现金流现值与终值现值相加得到企业价值</li>
        </ol>
    </div>

    <div class="footer">
        <p>本报告由 <strong>FinancialModel.cn</strong> 专业金融建模平台生成</p>
        <p>生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')} | 版本: 专业版</p>
        <p>🚀 让复杂的金融模型变得简单易用 | 💡 为投资决策提供专业支持</p>
    </div>

    <script>
        function downloadReport() {{
            const blob = new Blob([document.documentElement.outerHTML], {{ type: 'text/html' }});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '{st.session_state.dcf_data['company_name']}_DCF报告_{report_date}.html';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }}
    </script>
</body>
</html>"""
                            
                            # 在Streamlit中显示HTML报告
                            st.components.v1.html(report_html, height=800, scrolling=True)
                            
                            # 提供在新窗口打开的选项
                            st.subheader("📥 报告选项")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                        # 7. 使用说明
                                        instructions = pd.DataFrame({
                                            'DCF模型使用指南': [
                                                '基本使用方法',
                                                '1. 在输入参数工作表中修改基础数据',
                                                '2. 在增长率设置中调整各年收入增长预期',
                                                '3. 查看现金流预测了解详细计算过程',
                                                '4. 在估值汇总中查看最终估值结果',
                                                '',
                                                '关键假设说明',
                                                'WACC应基于公司具体的资本结构计算',
                                                '永续增长率通常不应超过长期GDP增长率',
                                                '现金流预测基于收入增长和现金流率假设',
                                                '终值占企业价值的比例不应过高',
                                                '',
                                                '敏感性分析',
                                                '关注WACC和永续增长率变化对估值的影响',
                                                '建议进行多情景分析验证结果稳健性',
                                                '',
                                                '重要提醒',
                                                'DCF估值仅供参考需结合其他估值方法',
                                                '模型基于假设实际结果可能有差异',
                                                '投资决策需考虑多种因素和风险',
                                                '',
                                                f'模型生成时间 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                                                '生成平台 FinancialModel.cn 专业版'
                                            ]
                                        })
                                        instructions.to_excel(writer, sheet_name='使用说明', index=False)
                                    
                                    return output.getvalue()
                                
                                excel_data = create_dcf_excel()
                                
                                st.markdown("### 📊 Excel DCF模型")
                                st.info("完整的DCF模型，包含7个工作表：输入参数、增长率设置、现金流预测、终值计算、估值汇总、敏感性分析、使用说明")
                                st.download_button(
                                    label="📊 下载完整DCF模型", 
                                    data=excel_data,
                                    file_name=f"DCF模型_{st.session_state.dcf_data['company_name']}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            
                            with col2:
                                st.markdown("### 📊 PowerPoint演示")
                                st.info("点击下方按钮在新窗口打开演示文稿，然后使用浏览器的打印功能")
                                
                                # 使用更简单可靠的方法打开PPT
                                ppt_js = """
                                <script>
                                function openPPTReport() {
                                    var pptContent = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>""" + f"{st.session_state.dcf_data['company_name']} DCF估值演示" + """</title>
    <style>
        body { font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
        .slide { 
            width: 90%; max-width: 800px; margin: 20px auto; 
            background: white; padding: 40px; 
            border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            page-break-after: always;
        }
        .slide h1 { color: #3b82f6; text-align: center; font-size: 32px; margin-bottom: 20px; }
        .slide h2 { color: #1f2937; font-size: 24px; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }
        .highlight { background: #dbeafe; padding: 20px; border-radius: 8px; text-align: center; }
        .metrics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 20px 0; }
        .metric { background: #f8fafc; padding: 15px; border-radius: 8px; text-align: center; }
        .metric-value { font-size: 24px; font-weight: bold; color: #3b82f6; }
        .no-print { text-align: center; margin: 20px; }
        .print-btn { background: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        @media print { .no-print { display: none; } }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #e5e7eb; padding: 12px; text-align: center; }
        th { background-color: #f3f4f6; font-weight: bold; }
        .risk-box { background: #fef3c7; padding: 20px; border-radius: 8px; border-left: 4px solid #f59e0b; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="no-print">
        <button class="print-btn" onclick="window.print()">🖨️ 打印演示文稿</button>
    </div>

    <!-- 幻灯片1: 封面 -->
    <div class="slide">
        <h1>""" + f"{st.session_state.dcf_data['company_name']}" + """</h1>
        <h1>DCF估值分析演示</h1>
        <div class="highlight">
            <h2>分析师: """ + f"{analyst_name}" + """</h2>
            <h2>日期: """ + f"{report_date}" + """</h2>
            <p style="margin-top: 30px; color: #6b7280;">FinancialModel.cn 专业版</p>
        </div>
    </div>

    <!-- 幻灯片2: 执行摘要 -->
    <div class="slide">
        <h2>📋 执行摘要</h2>
        <div class="highlight">
            <h1>每股内在价值</h1>
            <div style="font-size: 48px; color: #10b981; margin: 20px 0;">
                """ + f"{currency_symbol}{dcf_result['share_price']:.2f}" + """
            </div>
        </div>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">""" + f"{currency_symbol}{dcf_result['enterprise_value']:.1f}M" + """</div>
                <div>企业价值</div>
            </div>
            <div class="metric">
                <div class="metric-value">""" + f"{currency_symbol}{dcf_result['equity_value']:.1f}M" + """</div>
                <div>股权价值</div>
            </div>
            <div class="metric">
                <div class="metric-value">""" + f"{currency_symbol}{dcf_result['total_pv_fcf']:.1f}M" + """</div>
                <div>预测期现金流现值</div>
            </div>
            <div class="metric">
                <div class="metric-value">""" + f"{(dcf_result['pv_terminal'] / dcf_result['enterprise_value'] * 100):.1f}%" + """</div>
                <div>终值占比</div>
            </div>
        </div>
    </div>

    <!-- 幻灯片3: 关键假设 -->
    <div class="slide">
        <h2>🔢 关键假设</h2>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">""" + f"{st.session_state.dcf_data['wacc']:.1f}%" + """</div>
                <div>WACC</div>
            </div>
            <div class="metric">
                <div class="metric-value">""" + f"{st.session_state.dcf_data['terminal_growth']:.1f}%" + """</div>
                <div>永续增长率</div>
            </div>
            <div class="metric">
                <div class="metric-value">""" + f"{st.session_state.dcf_data['forecast_years']}年" + """</div>
                <div>预测期</div>
            </div>
            <div class="metric">
                <div class="metric-value">""" + f"{st.session_state.dcf_data['fcf_margin']:.1f}%" + """</div>
                <div>自由现金流率</div>
            </div>
        </div>
        <div style="background: #dbeafe; padding: 20px; border-radius: 8px; margin-top: 20px;">
            <h3>收入增长率假设</h3>
            <table>
                <tr>
                    <th>年份</th>"""
                
                for i in range(st.session_state.dcf_data['forecast_years']):
                    ppt_js += f"""<th>第{i+1}年</th>"""
                
                ppt_js += """</tr>
                <tr>
                    <td><strong>增长率</strong></td>"""
                
                for i in range(st.session_state.dcf_data['forecast_years']):
                    if i < len(st.session_state.dcf_data['revenue_growth_rates']):
                        growth_rate = st.session_state.dcf_data['revenue_growth_rates'][i]
                    else:
                        growth_rate = st.session_state.dcf_data['revenue_growth_rates'][-1]
                    ppt_js += f"""<td>{growth_rate:.1f}%</td>"""
                
                ppt_js += """</tr>
            </table>
        </div>
    </div>

    <!-- 幻灯片4: 估值分解 -->
    <div class="slide">
        <h2>💰 估值分解</h2>
        <div style="background: #f8fafc; padding: 20px; border-radius: 8px;">
            <h3>现金流预测与现值</h3>
            <table>
                <tr>
                    <th>年份</th>
                    <th>自由现金流(M)</th>
                    <th>现值(M)</th>
                </tr>"""
                
                for i, year in enumerate(dcf_result['years']):
                    ppt_js += f"""
                <tr>
                    <td>第{year}年</td>
                    <td>{dcf_result['forecasted_fcf'][i]:.1f}</td>
                    <td>{dcf_result['pv_fcf'][i]:.1f}</td>
                </tr>"""
                
                ppt_js += f"""
            </table>
        </div>
        <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; margin-top: 20px; text-align: center;">
            <h3>估值汇总</h3>
            <p><strong>预测期现金流现值:</strong> """ + f"{currency_symbol}{dcf_result['total_pv_fcf']:.1f}M" + """</p>
            <p><strong>终值现值:</strong> """ + f"{currency_symbol}{dcf_result['pv_terminal']:.1f}M" + """</p>
            <p style="font-size: 24px; color: #10b981;"><strong>企业价值:</strong> """ + f"{currency_symbol}{dcf_result['enterprise_value']:.1f}M" + """</p>
            <hr>
            <p><strong>减去净债务:</strong> """ + f"{currency_symbol}{st.session_state.dcf_data['debt'] - st.session_state.dcf_data['cash']:.1f}M" + """</p>
            <p style="font-size: 24px; color: #3b82f6;"><strong>股权价值:</strong> """ + f"{currency_symbol}{dcf_result['equity_value']:.1f}M" + """</p>
        </div>
    </div>

    <!-- 幻灯片5: 风险提示 -->
    <div class="slide">
        <h2>⚠️ 风险提示与建议</h2>
        <div class="risk-box">
            <h3>关键风险因素</h3>
            <ul style="font-size: 18px; line-height: 1.8; text-align: left;">
                <li>DCF模型基于当前假设，实际结果可能不同</li>
                <li>终值占比""" + f"{(dcf_result['pv_terminal'] / dcf_result['enterprise_value'] * 100):.1f}%" + """，需关注长期预测准确性</li>
                <li>建议结合其他估值方法进行验证</li>
                <li>投资决策需考虑个人风险承受能力</li>
                <li>市场环境变化可能影响估值结果</li>
            </ul>
        </div>
        <div class="highlight" style="margin-top: 30px;">
            <h2>投资建议</h2>
            <p style="font-size: 20px;">基于DCF分析，目标价格 """ + f"{currency_symbol}{dcf_result['share_price']:.2f}" + """</p>
            <p>建议结合市场条件和其他估值方法综合判断</p>
        </div>
    </div>

    <!-- 幻灯片6: 模型说明 -->
    <div class="slide">
        <h2>📚 DCF模型说明</h2>
        <div style="background: #f8fafc; padding: 20px; border-radius: 8px;">
            <h3>贴现现金流估值法核心原理</h3>
            <ol style="font-size: 18px; line-height: 1.8;">
                <li><strong>预测自由现金流:</strong> 基于收入增长和现金流率假设</li>
                <li><strong>确定贴现率:</strong> 使用WACC反映投资风险</li>
                <li><strong>计算终值:</strong> 采用永续增长模型</li>
                <li><strong>求和现值:</strong> 预测期现金流现值 + 终值现值</li>
            </ol>
        </div>
        <div style="background: #dbeafe; padding: 20px; border-radius: 8px; margin-top: 20px;">
            <h3>模型优势与局限</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <h4>✅ 优势</h4>
                    <ul>
                        <li>理论基础扎实</li>
                        <li>考虑时间价值</li>
                        <li>关注现金流</li>
                    </ul>
                </div>
                <div>
                    <h4>⚠️ 局限</h4>
                    <ul>
                        <li>依赖预测假设</li>
                        <li>对参数敏感</li>
                        <li>需要专业判断</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</body>
</html>`;
                                    var newWindow = window.open('', '_blank');
                                    newWindow.document.write(pptContent);
                                    newWindow.document.close();
                                }
                                </script>
                                <button onclick="openPPTReport()" style="background: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                                    📊 打开PPT演示
                                </button>
                                """
                                st.components.v1.html(ppt_js, height=80)
                            
                            # 添加使用说明
                            st.markdown("---")
                            st.markdown("""
                            ### 📖 使用说明
                            
                            **PDF报告生成：**
                            - 使用上方的"🖨️ 打印/保存为PDF"按钮
                            - 在浏览器打印对话框中选择"保存为PDF"
                            
                            **PowerPoint演示生成步骤：**
                            1. 点击"📊 打开PPT演示"按钮  
                            2. 在新窗口中查看5页幻灯片内容
                            3. 使用浏览器打印功能保存为PDF
                            4. 可选择横向布局以适合演示格式
                            
                            **Excel模型：**
                            - 直接点击下载按钮获得真实的Excel文件
                            - 可在Excel中编辑参数和查看计算公式
                            """)
        
    elif selected_dcf_tab == "🔧 模型导出":
        st.header("💾 DCF模型导出")
        
        if template_level != "企业版":
            st.warning("🔒 此功能仅限企业版用户使用")
        else:
            st.info("💡 企业版功能：导出Excel DCF模型")

else:
    # 其他未开发的模型
    st.header(f"🚧 {selected_model}")
    
    st.markdown("""
    <div class="coming-soon">
        <h2>📋 功能规划中</h2>
        <p>该模型正在我们的开发计划中，敬请期待！</p>
        <p>想要优先体验？<strong>升级到企业版获得定制开发服务</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # 显示开发路线图
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

# 页脚统计和升级提示
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

st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 2rem 0;">
    <p>© 2024 <strong>FinancialModel.cn</strong> | 专业金融建模平台</p>
    <p>🚀 让复杂的金融模型变得简单易用 | 💡 为投资决策提供专业支持</p>
</div>
""", unsafe_allow_html=True)
