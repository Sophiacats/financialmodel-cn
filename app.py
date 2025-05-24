import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import math

# 页面配置
st.set_page_config(
    page_title="专业级相对估值模型 - FinancialModel.cn",
    page_icon="📊",
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
</style>
""", unsafe_allow_html=True)

# 标题区域
st.markdown('<h1 class="main-header">📊 专业级相对估值模型</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">PE/PB/EV/EBITDA 多维度估值分析系统 | FinancialModel.cn</p>', unsafe_allow_html=True)

# 侧边栏设置
st.sidebar.header("⚙️ 系统设置")
currency = st.sidebar.selectbox("💱 币种选择", ["CNY (人民币)", "USD (美元)"], index=0)
template_level = st.sidebar.selectbox("🎯 模板级别", ["入门版", "进阶版", "专业版"], index=1)

currency_symbol = "￥" if currency.startswith("CNY") else "$"
unit_text = "万元" if currency.startswith("CNY") else "万美元"

# 侧边栏功能导航
st.sidebar.header("🧭 功能导航")
selected_tab = st.sidebar.radio("选择功能模块", [
    "📈 估值计算",
    "📊 对比分析", 
    "📋 数据管理",
    "💡 投资建议",
    "📄 报告导出"
])

# 版权信息
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align: center; color: #6b7280; font-size: 0.8rem;">
    <p>© 2024 FinancialModel.cn</p>
    <p>专业金融估值工具</p>
</div>
""", unsafe_allow_html=True)

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
        {'name': '同行B', 'stock_price': 52.30, 'total_shares': 15.8, 'net_profit': 45000, 'net_assets': 220000, 'ebitda': 78000, 'ebit': 62000, 'cash': 35000, 'debt': 95000, 'growth_rate': 15.8},
        {'name': '同行C', 'stock_price': 41.20, 'total_shares': 9.5, 'net_profit': 30000, 'net_assets': 165000, 'ebitda': 58000, 'ebit': 48000, 'cash': 18000, 'debt': 72000, 'growth_rate': 8.9},
        {'name': '同行D', 'stock_price': 48.90, 'total_shares': 13.2, 'net_profit': 38000, 'net_assets': 195000, 'ebitda': 68000, 'ebit': 55000, 'cash': 28000, 'debt': 88000, 'growth_rate': 11.7}
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

# 根据选择的标签页显示内容
if selected_tab == "📈 估值计算":
    
    # 目标公司数据输入
    st.header("🎯 目标公司数据输入")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.session_state.target_company['name'] = st.text_input("公司名称", st.session_state.target_company['name'])
        st.session_state.target_company['stock_price'] = st.number_input(f"股价 ({currency_symbol})", value=float(st.session_state.target_company['stock_price']), step=0.01, min_value=0.0)
        st.session_state.target_company['total_shares'] = st.number_input("总股本 (亿股)", value=float(st.session_state.target_company['total_shares']), step=0.1, min_value=0.0)
        
    with col2:
        st.session_state.target_company['net_profit'] = st.number_input(f"净利润 ({unit_text})", value=float(st.session_state.target_company['net_profit']), step=1000.0)
        st.session_state.target_company['net_assets'] = st.number_input(f"净资产 ({unit_text})", value=float(st.session_state.target_company['net_assets']), step=1000.0, min_value=0.0)
        st.session_state.target_company['ebitda'] = st.number_input(f"EBITDA ({unit_text})", value=float(st.session_state.target_company['ebitda']), step=1000.0)
        
    with col3:
        st.session_state.target_company['ebit'] = st.number_input(f"EBIT ({unit_text})", value=float(st.session_state.target_company['ebit']), step=1000.0)
        st.session_state.target_company['cash'] = st.number_input(f"现金 ({unit_text})", value=float(st.session_state.target_company['cash']), step=1000.0, min_value=0.0)
        st.session_state.target_company['debt'] = st.number_input(f"有息负债 ({unit_text})", value=float(st.session_state.target_company['debt']), step=1000.0, min_value=0.0)
    
    st.session_state.target_company['growth_rate'] = st.number_input("净利润增长率 (%)", value=float(st.session_state.target_company['growth_rate']), step=0.1)

    # 计算目标公司指标
    target_metrics = calculate_metrics(st.session_state.target_company)
    
    # 计算可比公司指标
    comparable_metrics = []
    for comp in st.session_state.comparable_companies:
        comparable_metrics.append(calculate_metrics(comp))
    
    # 计算行业平均值
    if comparable_metrics:
        valid_pe = [m['pe'] for m in comparable_metrics if m['pe'] > 0]
        valid_pb = [m['pb'] for m in comparable_metrics if m['pb'] > 0]
        valid_ev_ebitda = [m['ev_ebitda'] for m in comparable_metrics if m['ev_ebitda'] > 0]
        valid_ev_ebit = [m['ev_ebit'] for m in comparable_metrics if m['ev_ebit'] > 0]
        valid_peg = [m['peg'] for m in comparable_metrics if m['peg'] > 0]
        
        industry_avg = {
            'pe': round(np.mean(valid_pe), 2) if valid_pe else 0,
            'pb': round(np.mean(valid_pb), 2) if valid_pb else 0,
            'ev_ebitda': round(np.mean(valid_ev_ebitda), 2) if valid_ev_ebitda else 0,
            'ev_ebit': round(np.mean(valid_ev_ebit), 2) if valid_ev_ebit else 0,
            'peg': round(np.mean(valid_peg), 2) if valid_peg else 0
        }
    else:
        industry_avg = {'pe': 0, 'pb': 0, 'ev_ebitda': 0, 'ev_ebit': 0, 'peg': 0}

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
    
    # 基础财务数据
    st.header("📊 基础财务数据")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("市值", f"{currency_symbol}{target_metrics['market_cap']} 亿")
        st.metric("企业价值", f"{currency_symbol}{target_metrics['enterprise_value']} 亿")
        
    with col2:
        if st.session_state.target_company['net_assets'] > 0:
            roe = (st.session_state.target_company['net_profit'] / st.session_state.target_company['net_assets']) * 100
            st.metric("净资产收益率", f"{roe:.2f}%")
        
        total_assets = st.session_state.target_company['net_assets'] + st.session_state.target_company['debt']
        if total_assets > 0:
            roa = (st.session_state.target_company['net_profit'] / total_assets) * 100
            st.metric("总资产收益率", f"{roa:.2f}%")

elif selected_tab == "📊 对比分析":
    
    st.header("🔍 同行业对比分析")
    
    # 计算所有公司的指标
    target_metrics = calculate_metrics(st.session_state.target_company)
    comparable_metrics = [calculate_metrics(comp) for comp in st.session_state.comparable_companies]
    
    # 对比表格
    comparison_data = []
    
    # 添加目标公司数据
    comparison_data.append({
        '公司': f"🎯 {st.session_state.target_company['name']}",
        'PE': f"{target_metrics['pe']:.2f}",
        'PB': f"{target_metrics['pb']:.2f}",
        'EV/EBITDA': f"{target_metrics['ev_ebitda']:.2f}",
        'EV/EBIT': f"{target_metrics['ev_ebit']:.2f}",
        'PEG': f"{target_metrics['peg']:.2f}",
        f'市值({currency_symbol}亿)': f"{target_metrics['market_cap']:.2f}"
    })
    
    # 添加可比公司数据
    for i, comp in enumerate(st.session_state.comparable_companies):
        metrics = comparable_metrics[i]
        comparison_data.append({
            '公司': comp['name'],
            'PE': f"{metrics['pe']:.2f}",
            'PB': f"{metrics['pb']:.2f}",
            'EV/EBITDA': f"{metrics['ev_ebitda']:.2f}",
            'EV/EBIT': f"{metrics['ev_ebit']:.2f}",
            'PEG': f"{metrics['peg']:.2f}",
            f'市值({currency_symbol}亿)': f"{metrics['market_cap']:.2f}"
        })
    
    # 计算并添加行业平均值
    if comparable_metrics:
        valid_pe = [m['pe'] for m in comparable_metrics if m['pe'] > 0]
        valid_pb = [m['pb'] for m in comparable_metrics if m['pb'] > 0]
        valid_ev_ebitda = [m['ev_ebitda'] for m in comparable_metrics if m['ev_ebitda'] > 0]
        valid_ev_ebit = [m['ev_ebit'] for m in comparable_metrics if m['ev_ebit'] > 0]
        valid_peg = [m['peg'] for m in comparable_metrics if m['peg'] > 0]
        valid_market_cap = [m['market_cap'] for m in comparable_metrics if m['market_cap'] > 0]
        
        industry_avg = {
            'pe': np.mean(valid_pe) if valid_pe else 0,
            'pb': np.mean(valid_pb) if valid_pb else 0,
            'ev_ebitda': np.mean(valid_ev_ebitda) if valid_ev_ebitda else 0,
            'ev_ebit': np.mean(valid_ev_ebit) if valid_ev_ebit else 0,
            'peg': np.mean(valid_peg) if valid_peg else 0,
            'market_cap': np.mean(valid_market_cap) if valid_market_cap else 0
        }
        
        comparison_data.append({
            '公司': '🏭 行业均值',
            'PE': f"{industry_avg['pe']:.2f}",
            'PB': f"{industry_avg['pb']:.2f}",
            'EV/EBITDA': f"{industry_avg['ev_ebitda']:.2f}",
            'EV/EBIT': f"{industry_avg['ev_ebit']:.2f}",
            'PEG': f"{industry_avg['peg']:.2f}",
            f'市值({currency_symbol}亿)': f"{industry_avg['market_cap']:.2f}"
        })
    
    # 显示对比表格
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)
    
    # 估值对比图表
    st.header("📈 估值对比图表")
    
    if comparable_metrics:
        col1, col2 = st.columns(2)
        
        with col1:
            # 雷达图
            categories = ['PE', 'PB', 'EV/EBITDA', 'EV/EBIT', 'PEG']
            target_values = [target_metrics['pe'], target_metrics['pb'], target_metrics['ev_ebitda'], target_metrics['ev_ebit'], target_metrics['peg']]
            industry_values = [industry_avg['pe'], industry_avg['pb'], industry_avg['ev_ebitda'], industry_avg['ev_ebit'], industry_avg['peg']]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=target_values,
                theta=categories,
                fill='toself',
                name='目标公司',
                line_color='#3b82f6'
            ))
            
            fig.add_trace(go.Scatterpolar(
                r=industry_values,
                theta=categories,
                fill='toself',
                name='行业均值',
                line_color='#10b981'
            ))
            
            max_value = max(max([v for v in target_values if v > 0], default=1), 
                           max([v for v in industry_values if v > 0], default=1))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max_value * 1.2]
                    )),
                showlegend=True,
                title="估值雷达图"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 柱状图
            metrics_data = pd.DataFrame({
                '指标': ['PE', 'PB', 'EV/EBITDA', 'EV/EBIT', 'PEG'],
                '目标公司': target_values,
                '行业均值': industry_values
            })
            
            fig = px.bar(metrics_data, x='指标', y=['目标公司', '行业均值'], 
                         title="估值指标对比", barmode='group',
                         color_discrete_map={'目标公司': '#3b82f6', '行业均值': '#10b981'})
            
            st.plotly_chart(fig, use_container_width=True)

elif selected_tab == "📋 数据管理":
    
    st.header("📝 可比公司数据管理")
    
    # 添加新公司
    with st.expander("➕ 添加新的可比公司"):
        with st.form("add_company"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                new_name = st.text_input("公司名称", value=f"同行{chr(65 + len(st.session_state.comparable_companies))}")
                new_price = st.number_input("股价", value=40.0, step=0.01, min_value=0.0)
                new_shares = st.number_input("总股本(亿股)", value=10.0, step=0.1, min_value=0.0)
                
            with col2:
                new_profit = st.number_input("净利润(万元)", value=30000.0, step=1000.0)
                new_assets = st.number_input("净资产(万元)", value=150000.0, step=1000.0, min_value=0.0)
                new_ebitda = st.number_input("EBITDA(万元)", value=50000.0, step=1000.0)
                
            with col3:
                new_ebit = st.number_input("EBIT(万元)", value=40000.0, step=1000.0)
                new_cash = st.number_input("现金(万元)", value=20000.0, step=1000.0, min_value=0.0)
                new_debt = st.number_input("有息负债(万元)", value=70000.0, step=1000.0, min_value=0.0)
            
            new_growth = st.number_input("增长率(%)", value=10.0, step=0.1)
            
            if st.form_submit_button("添加公司"):
                new_company = {
                    'name': new_name,
                    'stock_price': new_price,
                    'total_shares': new_shares,
                    'net_profit': new_profit,
                    'net_assets': new_assets,
                    'ebitda': new_ebitda,
                    'ebit': new_ebit,
                    'cash': new_cash,
                    'debt': new_debt,
                    'growth_rate': new_growth
                }
                st.session_state.comparable_companies.append(new_company)
                st.success(f"已添加 {new_name}！")
                st.rerun()
    
    # 编辑现有公司
    st.subheader("📊 当前可比公司列表")
    
    for i, comp in enumerate(st.session_state.comparable_companies):
        with st.expander(f"编辑 {comp['name']}"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                comp['name'] = st.text_input(f"公司名称_{i}", value=comp['name'], key=f"name_{i}")
                comp['stock_price'] = st.number_input(f"股价_{i}", value=float(comp['stock_price']), step=0.01, min_value=0.0, key=f"price_{i}")
                comp['total_shares'] = st.number_input(f"总股本_{i}", value=float(comp['total_shares']), step=0.1, min_value=0.0, key=f"shares_{i}")
                
            with col2:
                comp['net_profit'] = st.number_input(f"净利润_{i}", value=float(comp['net_profit']), step=1000.0, key=f"profit_{i}")
                comp['net_assets'] = st.number_input(f"净资产_{i}", value=float(comp['net_assets']), step=1000.0, min_value=0.0, key=f"assets_{i}")
                comp['ebitda'] = st.number_input(f"EBITDA_{i}", value=float(comp['ebitda']), step=1000.0, key=f"ebitda_{i}")
                
            with col3:
                comp['ebit'] = st.number_input(f"EBIT_{i}", value=float(comp['ebit']), step=1000.0, key=f"ebit_{i}")
                comp['cash'] = st.number_input(f"现金_{i}", value=float(comp['cash']), step=1000.0, min_value=0.0, key=f"cash_{i}")
                comp['debt'] = st.number_input(f"有息负债_{i}", value=float(comp['debt']), step=1000.0, min_value=0.0, key=f"debt_{i}")
                
            with col4:
                comp['growth_rate'] = st.number_input(f"增长率_{i}", value=float(comp['growth_rate']), step=0.1, key=f"growth_{i}")
                
                if st.button(f"🗑️ 删除 {comp['name']}", key=f"delete_{i}"):
                    st.session_state.comparable_companies.pop(i)
                    st.success(f"已删除 {comp['name']}！")
                    st.rerun()

elif selected_tab == "💡 投资建议":
    
    st.header("🧠 智能投资建议")
    
    # 计算指标
    target_metrics = calculate_metrics(st.session_state.target_company)
    comparable_metrics = [calculate_metrics(comp) for comp in st.session_state.comparable_companies]
    
    if comparable_metrics:
        valid_pe = [m['pe'] for m in comparable_metrics if m['pe'] > 0]
        valid_pb = [m['pb'] for m in comparable_metrics if m['pb'] > 0]
        valid_ev_ebitda = [m['ev_ebitda'] for m in comparable_metrics if m['ev_ebitda'] > 0]
        valid_peg = [m['peg'] for m in comparable_metrics if m['peg'] > 0]
        
        industry_avg = {
            'pe': np.mean(valid_pe) if valid_pe else 0,
            'pb': np.mean(valid_pb) if valid_pb else 0,
            'ev_ebitda': np.mean(valid_ev_ebitda) if valid_ev_ebitda else 0,
            'peg': np.mean(valid_peg) if valid_peg else 0
        }
        
        # 生成投资建议
        positive_signals = 0
        total_signals = 0
        advice_text = ""
        
        # PE分析
        if industry_avg['pe'] > 0:
            total_signals += 1
            if target_metrics['pe'] > 0 and target_metrics['pe'] < industry_avg['pe']:
                advice_text += f"当前公司PE为{target_metrics['pe']:.2f}，低于行业均值{industry_avg['pe']:.2f}，处于相对低估区间；"
                positive_signals += 1
            elif target_metrics['pe'] > 0:
                advice_text += f"当前公司PE为{target_metrics['pe']:.2f}，高于行业均值{industry_avg['pe']:.2f}，估值偏高；"
        
        # PB分析
        if industry_avg['pb'] > 0:
            total_signals += 1
            if target_metrics['pb'] > 0 and target_metrics['pb'] < industry_avg['pb']:
                advice_text += "PB低于同行均值，账面价值具有安全边际；"
                positive_signals += 1
            elif target_metrics['pb'] > 0 and abs(target_metrics['pb'] - industry_avg['pb']) / industry_avg['pb'] < 0.1:
                advice_text += "PB与同行持平；"
                positive_signals += 0.5
            else:
                advice_text += "PB高于同行均值，需关注资产质量；"
        
        # PEG分析
        if target_metrics['peg'] > 0:
            total_signals += 1
            if 0 < target_metrics['peg'] < 1:
                advice_text += f"PEG为{target_metrics['peg']:.2f}，小于1，成长性估值具有吸引力。"
                positive_signals += 1
            elif 1 <= target_metrics['peg'] < 1.5:
                advice_text += f"PEG为{target_metrics['peg']:.2f}，成长性估值合理。"
                positive_signals += 0.5
            else:
                advice_text += f"PEG为{target_metrics['peg']:.2f}，成长性估值偏高，需谨慎。"
        
        # 综合评级
        if total_signals > 0:
            score_ratio = positive_signals / total_signals
            if score_ratio >= 0.8:
                rating = "🟢 买入推荐"
                rating_color = "#10b981"
            elif score_ratio >= 0.6:
                rating = "🟡 谨慎乐观"
                rating_color = "#f59e0b"
            elif score_ratio >= 0.4:
                rating = "🟠 中性观望"
                rating_color = "#f97316"
            else:
                rating = "🔴 规避风险"
                rating_color = "#ef4444"
        else:
            rating = "⚪ 数据不足"
            rating_color = "#6b7280"
            advice_text = "可比公司数据不足，无法进行有效的相对估值分析。"
        
        # 显示综合分析结论
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; border-left: 4px solid {rating_color}; margin: 1rem 0;">
            <h3 style="color: {rating_color}; margin: 0 0 1rem 0;">{rating}</h3>
            <p style="color: #374151; margin: 0; line-height: 1.6;">{advice_text}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 详细分析
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="success-box"><h4>📈 优势分析</h4>', unsafe_allow_html=True)
            advantages = []
            if target_metrics['pe'] > 0 and industry_avg['pe'] > 0 and target_metrics['pe'] < industry_avg['pe']:
                advantages.append("• PE估值相对较低")
            if 0 < target_metrics['peg'] < 1:
                advantages.append("• PEG小于1，成长性佳")
            if st.session_state.target_company['growth_rate'] > 10:
                advantages.append("• 净利润增长率较高")
            if target_metrics['pb'] > 0 and industry_avg['pb'] > 0 and target_metrics['pb'] < industry_avg['pb']:
                advantages.append("• PB低于行业均值")
            
            if advantages:
                for adv in advantages:
                    st.markdown(adv)
            else:
                st.markdown("• 暂无明显估值优势")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="warning-box"><h4>⚠️ 风险提示</h4>', unsafe_allow_html=True)
            risks = []
            if target_metrics['pe'] > 0 and industry_avg['pe'] > 0 and target_metrics['pe'] > industry_avg['pe']:
                risks.append("• PE估值偏高")
            if target_metrics['peg'] > 1.5:
                risks.append("• PEG过高，成长性不足")
            if st.session_state.target_company['growth_rate'] < 5:
                risks.append("• 增长率较低")
            risks.append("• 需关注行业周期性")
            
            for risk in risks:
                st.markdown(risk)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="info-box"><h4>🎯 操作建议</h4>', unsafe_allow_html=True)
            recommendations = [
                "• 建议结合基本面分析",
                "• 关注季报业绩变化", 
                "• 参考技术面支撑位",
                "• 设置合理止损点"
            ]
            for rec in recommendations:
                st.markdown(rec)
            st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        st.warning("请先在'数据管理'页面添加可比公司数据")
    
    # 免责声明
    st.markdown("""
    <div style="background: #dbeafe; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #3b82f6; margin: 2rem 0;">
        <p style="margin: 0; color: #1e40af; font-size: 0.9rem;">
            <strong>⚠️ 免责声明：</strong>本分析工具仅供参考，不构成投资建议。投资有风险，决策需谨慎。
            实际投资前请咨询专业投资顾问并进行深入的基本面分析。
        </p>
    </div>
    """, unsafe_allow_html=True)

elif selected_tab == "📄 报告导出":
    
    st.header("📋 估值分析报告")
    
    # 计算所有指标
    target_metrics = calculate_metrics(st.session_state.target_company)
    comparable_metrics = [calculate_metrics(comp) for comp in st.session_state.comparable_companies]
    
    # 生成报告内容
    report_content = f"""
# {st.session_state.target_company['name']} 估值分析报告

## 📊 核心估值指标

- **PE (市盈率)**: {target_metrics['pe']:.2f}
- **PB (市净率)**: {target_metrics['pb']:.2f}  
- **EV/EBITDA**: {target_metrics['ev_ebitda']:.2f}
- **EV/EBIT**: {target_metrics['ev_ebit']:.2f}
- **PEG**: {target_metrics['peg']:.2f}

## 💰 基础财务数据

- **市值**: {currency_symbol}{target_metrics['market_cap']:.2f} 亿
- **企业价值**: {currency_symbol}{target_metrics['enterprise_value']:.2f} 亿
- **净利润**: {currency_symbol}{st.session_state.target_company['net_profit']/10000:.2f} 亿
- **净资产**: {currency_symbol}{st.session_state.target_company['net_assets']/10000:.2f} 亿
- **净利润增长率**: {st.session_state.target_company['growth_rate']:.1f}%

## 🏭 同行业对比

"""
    
    if comparable_metrics:
        valid_pe = [m['pe'] for m in comparable_metrics if m['pe'] > 0]
        valid_pb = [m['pb'] for m in comparable_metrics if m['pb'] > 0]
        valid_ev_ebitda = [m['ev_ebitda'] for m in comparable_metrics if m['ev_ebitda'] > 0]
        
        if valid_pe:
            avg_pe = np.mean(valid_pe)
            report_content += f"- **行业平均PE**: {avg_pe:.2f} (目标公司: {target_metrics['pe']:.2f})\n"
        if valid_pb:
            avg_pb = np.mean(valid_pb)
            report_content += f"- **行业平均PB**: {avg_pb:.2f} (目标公司: {target_metrics['pb']:.2f})\n"
        if valid_ev_ebitda:
            avg_ev_ebitda = np.mean(valid_ev_ebitda)
            report_content += f"- **行业平均EV/EBITDA**: {avg_ev_ebitda:.2f} (目标公司: {target_metrics['ev_ebitda']:.2f})\n"
    
    report_content += f"""

## 📈 投资建议

基于相对估值分析，建议投资者综合考虑以下因素：

1. **估值水平**: 对比同行业公司进行相对估值判断
2. **成长性**: 关注公司的盈利增长可持续性  
3. **财务质量**: 分析公司的资产负债结构
4. **行业趋势**: 考虑所处行业的发展前景

---

*报告生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*  
*数据来源: FinancialModel.cn 专业估值分析系统*
"""
    
    # 显示报告内容
    st.markdown(report_content)
    
    # 导出功能
    col1, col2 = st.columns(2)
    
    with col1:
        # 创建Excel数据
        excel_data = {
            '公司名称': [st.session_state.target_company['name']] + [comp['name'] for comp in st.session_state.comparable_companies],
            'PE': [target_metrics['pe']] + [calculate_metrics(comp)['pe'] for comp in st.session_state.comparable_companies],
            'PB': [target_metrics['pb']] + [calculate_metrics(comp)['pb'] for comp in st.session_state.comparable_companies],
            'EV/EBITDA': [target_metrics['ev_ebitda']] + [calculate_metrics(comp)['ev_ebitda'] for comp in st.session_state.comparable_companies],
            '市值(亿)': [target_metrics['market_cap']] + [calculate_metrics(comp)['market_cap'] for comp in st.session_state.comparable_companies]
        }
        
        excel_df = pd.DataFrame(excel_data)
        
        # 转换为CSV格式用于下载
        csv = excel_df.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            label="📊 下载Excel数据",
            data=csv,
            file_name=f"{st.session_state.target_company['name']}_估值分析_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        st.download_button(
            label="📄 下载分析报告",
            data=report_content,
            file_name=f"{st.session_state.target_company['name']}_估值报告_{pd.Timestamp.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )

# 页脚
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 2rem 0;">
    <p>© 2024 <strong>FinancialModel.cn</strong> | 专业金融估值工具平台</p>
    <p>🚀 让复杂的金融模型变得简单易用 | 💡 为投资决策提供专业支持</p>
</div>
""", unsafe_allow_html=True)
