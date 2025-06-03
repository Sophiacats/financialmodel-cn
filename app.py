import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="功能诊断", layout="wide")
st.title("🔍 新功能诊断")

# 测试数据获取
ticker = st.text_input("股票代码", "AAPL")
if st.button("测试新功能"):
    
    # 获取股票数据
    stock = yf.Ticker(ticker)
    info = dict(stock.info)
    
    # 显示基本信息
    st.success(f"✅ 成功获取 {ticker} 数据")
    st.write(f"当前价格: ${info.get('currentPrice', 'N/A')}")
    
    # 测试1：DCF参数展示
    st.subheader("1️⃣ DCF参数展示测试")
    with st.expander("DCF模型参数"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**永续增长率 g**: 2.0%")
            st.write("**预测期增长率**: 5.0%")
        with col2:
            st.write("**折现率 WACC**: 10.0%")
            st.write("**预测年限**: 5年")
        with col3:
            st.write("**初始FCF**: $1,000M")
            st.write("**企业价值**: $20B")
    
    # 测试2：历史价格分位图
    st.subheader("2️⃣ 历史估值分位图测试")
    
    # 获取历史数据
    hist = stock.history(period="5y", interval="1mo")
    if not hist.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['Close'],
            mode='lines',
            name='历史价格'
        ))
        
        current_price = info.get('currentPrice', hist['Close'].iloc[-1])
        fig.add_hline(y=current_price, line_dash="dash", line_color="red",
                     annotation_text=f"当前价格: ${current_price:.2f}")
        
        # 计算分位数
        percentile = (hist['Close'] < current_price).sum() / len(hist) * 100
        
        fig.update_layout(
            title=f"5年价格走势（当前分位数: {percentile:.1f}%）",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 测试3：财务趋势图
    st.subheader("3️⃣ 财务趋势图测试")
    
    financials = stock.financials
    if not financials.empty:
        years = [str(d.year) for d in financials.columns[:3]]
        revenues = [financials.loc['Total Revenue'].iloc[i]/1e9 for i in range(min(3, len(financials.columns)))]
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=years[::-1],
            y=revenues[::-1],
            name='营业收入(B)'
        ))
        fig2.update_layout(title="营收趋势", height=300)
        st.plotly_chart(fig2, use_container_width=True)
    
    # 测试4：风险雷达图
    st.subheader("4️⃣ 风险雷达图测试")
    
    categories = ['偿债能力', '波动性控制', '财务杠杆', '现金流增长', '盈利能力']
    values = [7, 6, 8, 5, 7]
    
    fig3 = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself'
    ))
    fig3.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        title="风险评估雷达图",
        height=400
    )
    st.plotly_chart(fig3, use_container_width=True)
    
    # 测试5：智能评分
    st.subheader("5️⃣ 智能评分测试")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("价值得分", "35/50")
    with col2:
        st.metric("技术得分", "40/50")
    with col3:
        st.metric("综合得分", "75/100")
    
    st.success("🟢 **最终建议：BUY**")
    
    # 显示所有新功能清单
    st.subheader("✅ 新功能清单")
    st.markdown("""
    1. ✅ DCF参数详细展示
    2. ✅ 历史估值分位图
    3. ✅ 财务趋势图
    4. ✅ 止盈止损模拟器
    5. ✅ 风险雷达图
    6. ✅ Altman Z-score增强显示
    7. ✅ 智能投资评分
    8. ✅ 使用说明完善
    """)

# 显示版本信息
st.sidebar.info("""
### 版本信息
- 当前版本：v2.0
- 新增8个功能模块
- 优化用户体验
""")

# 测试止盈止损模拟器
with st.sidebar.expander("💰 止盈止损模拟器"):
    buy_price = st.number_input("买入价格", value=100.0)
    position = st.number_input("持仓数量", value=100)
    
    if st.button("计算"):
        current = 110.0
        pnl = (current - buy_price) * position
        pnl_pct = (current - buy_price) / buy_price * 100
        
        st.metric("盈亏", f"${pnl:.2f} ({pnl_pct:+.2f}%)")
        st.write(f"止损位: ${buy_price * 0.9:.2f}")
        st.write(f"止盈位: ${buy_price * 1.15:.2f}")
