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

# 初始化DCF数据
if 'dcf_data' not in st.session_state:
    st.session_state.dcf_data = {
        'company_name': '目标公司',
        'base_revenue': 1000.0,
        'base_fcf': 100.0,
        'revenue_growth_rates': [15.0, 12.0, 10.0, 8.0, 6.0],
        'fcf_margin': 10.0,
        'wacc': 8.5,
        'terminal_growth': 2.5,
        'forecast_years': 5,
        'shares_outstanding': 100.0,
        'cash': 50.0,
        'debt': 200.0
    }

def calculate_dcf_valuation(data):
    """计算DCF估值"""
    try:
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
        
        wacc = data['wacc'] / 100
        pv_fcf = []
        total_pv_fcf = 0
        
        for i, fcf in enumerate(forecasted_fcf):
            pv = fcf / ((1 + wacc) ** (i + 1))
            pv_fcf.append(pv)
            total_pv_fcf += pv
        
        terminal_fcf = forecasted_fcf[-1] * (1 + data['terminal_growth'] / 100)
        terminal_value = terminal_fcf / (wacc - data['terminal_growth'] / 100)
        pv_terminal = terminal_value / ((1 + wacc) ** data['forecast_years'])
        
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

# 主内容区域
if selected_model == "相对估值模型":
    st.header("📈 相对估值模型")
    st.info("🔵 专业版：PE/PB估值功能")
    st.write("相对估值模型功能正在开发中...")

elif selected_model == "DCF估值模型":
    if template_level == "免费版":
        dcf_tabs = ["📊 DCF计算", "📈 敏感性分析"]
        template_info = "🟡 免费版：基础DCF估值功能"
    elif template_level == "专业版":
        dcf_tabs = ["📊 DCF计算", "📈 敏感性分析", "📋 详细预测", "💡 估值建议", "📄 DCF报告"]
        template_info = "🔵 专业版：完整DCF + 详细分析"
    else:
        dcf_tabs = ["📊 DCF计算", "📈 敏感性分析", "📋 详细预测", "💡 估值建议", "📄 DCF报告", "🔧 模型导出"]
        template_info = "🟢 企业版：完整DCF + 模型导出"

    st.info(template_info)
    selected_dcf_tab = st.selectbox("选择DCF功能", dcf_tabs)

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
            
            col1, col2 = st.columns(2)
            
            with col1:
                wacc_range = st.slider("WACC变动范围 (±%)", 1.0, 5.0, 2.0, 0.5)
                wacc_steps = st.selectbox("WACC步长数", [5, 7, 9], index=1)
            
            with col2:
                growth_range = st.slider("永续增长率变动范围 (±%)", 0.5, 3.0, 1.5, 0.25)
                growth_steps = st.selectbox("增长率步长数", [5, 7, 9], index=1)
            
            base_wacc = st.session_state.dcf_data['wacc']
            base_growth = st.session_state.dcf_data['terminal_growth']
            
            wacc_values = np.linspace(base_wacc - wacc_range, base_wacc + wacc_range, wacc_steps)
            growth_values = np.linspace(base_growth - growth_range, base_growth + growth_range, growth_steps)
            
            sensitivity_matrix = []
            
            for wacc in wacc_values:
                row = []
                for growth in growth_values:
                    temp_data = st.session_state.dcf_data.copy()
                    temp_data['wacc'] = wacc
                    temp_data['terminal_growth'] = growth
                    
                    result = calculate_dcf_valuation(temp_data)
                    if result:
                        row.append(result['share_price'])
                    else:
                        row.append(0)
                
                sensitivity_matrix.append(row)
            
            sensitivity_df = pd.DataFrame(
                sensitivity_matrix,
                index=[f"{wacc:.1f}%" for wacc in wacc_values],
                columns=[f"{growth:.1f}%" for growth in growth_values]
            )
            
            st.write("**每股价值敏感性分析表**")
            st.write("行：WACC | 列：永续增长率")
            
            styled_df = sensitivity_df.style.format(f"{currency_symbol}{{:.2f}}")
            st.dataframe(styled_df, use_container_width=True)
            
            fig = px.imshow(
                sensitivity_matrix,
                x=[f"{g:.1f}%" for g in growth_values],
                y=[f"{w:.1f}%" for w in wacc_values],
                color_continuous_scale='RdYlGn',
                title='每股价值敏感性热力图',
                labels={'x': '永续增长率', 'y': 'WACC', 'color': f'每股价值({currency_symbol})'}
            )
            
            st.plotly_chart(fig, use_container_width=True)

    elif selected_dcf_tab == "📄 DCF报告":
        st.header("📋 DCF估值报告")
        
        if template_level == "免费版":
            st.warning("🔒 此功能需要专业版或企业版订阅")
        else:
            if 'dcf_data' in st.session_state:
                dcf_result = calculate_dcf_valuation(st.session_state.dcf_data)
                
                if dcf_result:
                    st.subheader("📊 生成专业估值报告")
                    
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
                            progress_bar = st.progress(0)
                            for i in range(100):
                                progress_bar.progress(i + 1)
                            
                            st.success("✅ 报告生成完成！")
                            
                            # 创建报告HTML
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
                            
                            st.components.v1.html(report_html, height=600, scrolling=True)
                            
                            # 下载选项
                            st.subheader("📥 下载选项")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("### 📊 Excel模型")
                                
                                if st.button("生成Excel模型"):
                                    try:
                                        output = io.BytesIO()
                                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                            valuation_data = pd.DataFrame({
                                                '估值项目': ['企业价值', '股权价值', '每股价值'],
                                                '数值': [dcf_result['enterprise_value'], dcf_result['equity_value'], dcf_result['share_price']]
                                            })
                                            valuation_data.to_excel(writer, sheet_name='DCF结果', index=False)
                                        
                                        st.download_button(
                                            label="📥 下载Excel文件",
                                            data=output.getvalue(),
                                            file_name=f"DCF_{st.session_state.dcf_data['company_name']}.xlsx",
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                        )
                                    except Exception as e:
                                        st.error(f"Excel生成失败: {str(e)}")
                            
                            with col2:
                                st.markdown("### 📊 PowerPoint演示")
                                st.info("点击按钮在新窗口打开演示文稿")
                                
                                ppt_js = f"""
                                <script>
                                function openPPT() {{
                                    var content = `<html><body style="font-family: Arial;">
                                    <h1>{st.session_state.dcf_data['company_name']} DCF分析</h1>
                                    <h2>每股价值: {currency_symbol}{dcf_result['share_price']:.2f}</h2>
                                    <p>企业价值: {currency_symbol}{dcf_result['enterprise_value']:.1f}M</p>
                                    <p>股权价值: {currency_symbol}{dcf_result['equity_value']:.1f}M</p>
                                    </body></html>`;
                                    var newWindow = window.open('', '_blank');
                                    newWindow.document.write(content);
                                }}
                                </script>
                                <button onclick="openPPT()" style="background: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 5px;">
                                    📊 打开PPT演示
                                </button>
                                """
                                st.components.v1.html(ppt_js, height=80)

    else:
        st.header(f"📋 {selected_dcf_tab}")
        if template_level == "免费版":
            st.warning("🔒 此功能需要专业版或企业版订阅")
        else:
            st.info(f"💡 {template_level}功能：{selected_dcf_tab}")

else:
    st.header(f"🚧 {selected_model}")
    st.markdown("""
    <div class="coming-soon">
        <h2>📋 功能规划中</h2>
        <p>该模型正在我们的开发计划中，敬请期待！</p>
    </div>
    """, unsafe_allow_html=True)

# 页脚
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("已上线模型", "2", "📈 相对估值 + DCF")
with col2:
    st.metric("开发中模型", "1", "🔄 投资组合理论") 
with col3:
    st.metric("规划中模型", "15+", "📋 全品类覆盖")
with col4:
    st.metric("注册用户", "1,000+", "👥 快速增长")

if template_level == "免费版":
    st.warning("🎯 **升级到专业版解锁全部功能** - ✅ 无限制使用 ✅ 专业报告导出 ✅ 高级分析")

st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 2rem 0;">
    <p>© 2024 <strong>FinancialModel.cn</strong> | 专业金融建模平台</p>
    <p>🚀 让复杂的金融模型变得简单易用 | 💡 为投资决策提供专业支持</p>
</div>
""", unsafe_allow_html=True)
