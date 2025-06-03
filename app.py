def generate_trading_recommendation(valuation_signals, technical_signals, current_price, dcf_value):
    """生成交易建议"""
    recommendation = {
        'action': 'HOLD',
        'confidence': 0,
        'reasons': [],
        'entry_range': (0, 0),
        'stop_loss': 0,
        'take_profit': (0, 0),
        'position_size': 0
    }
    
    buy_signals = 0
    sell_signals = 0
    
    # 检查买入条件
    # 估值条件
    if valuation_signals['undervalued'] or valuation_signals['pe_status'] == 'undervalued' or valuation_signals['pb_status'] == 'undervalued':
        buy_signals += 1
        recommendation['reasons'].append("估值处于低估区间")
    
    # 技术条件
    tech_buy_conditions = [
        (technical_signals['ma_golden_cross'], "10日均线上穿60日均线"),
        (technical_signals['macd_golden_cross'], "MACD金叉成立"),
        (technical_signals['rsi_oversold'], "RSI超卖且拐头向上"),
        (technical_signals['bb_breakout'], "突破布林带中轨且带宽扩张")
    ]
    
    tech_buy_count = sum([1 for condition, _ in tech_buy_conditions if condition])
    
    if tech_buy_count >= 2:
        buy_signals += 1
        recommendation['reasons'].extend([reason for condition, reason in tech_buy_conditions if condition])
    
    # 检查卖出条件
    # 估值条件
    if valuation_signals['overvalued'] or valuation_signals['pe_status'] == 'overvalued' or valuation_signals['pb_status'] == 'overvalued':
        sell_signals += 1
        recommendation['reasons'].append("估值处于高估区间")
    
    # 技术条件
    tech_sell_conditions = [
        (technical_signals['rsi_overbought'], "RSI超买"),
        (technical_signals['macd_death_cross'], "MACD死叉"),
        (technical_signals['volume_divergence'], "量价背离"),
        (technical_signals['ma_death_cross'], "均线死叉")
    ]
    
    tech_sell_count = sum([1 for condition, _ in tech_sell_conditions if condition])
    
    if tech_sell_count >= 2:
        sell_signals += 1
        recommendation['reasons'].extend([reason for condition, reason in tech_sell_conditions if condition])
    
    # 生成最终建议
    if buy_signals >= 2:
        recommendation['action'] = 'BUY'
        recommendation['confidence'] = min(buy_signals * 30 + tech_buy_count * 10, 90)
        
        # 计算入场区间（当前价格的±2%）
        recommendation['entry_range'] = (current_price * 0.98, current_price * 1.02)
        
        # 计算止损（-8%）
        recommendation['stop_loss'] = current_price * 0.92
        
        # 计算止盈目标
        if dcf_value and dcf_value > current_price:
            # 如果有DCF估值，使用估值作为目标
            recommendation['take_profit'] = (dcf_value * 0.95, dcf_value * 1.05)
        else:
            # 否则使用技术目标（15%-25%）
            recommendation['take_profit'] = (current_price * 1.15, current_price * 1.25)
        
        # Kelly公式计算仓位
        win_prob = 0.6 + (recommendation['confidence'] / 100) * 0.2
        recommendation['position_size'] = calculate_kelly_criterion(win_prob, 2.0) * 100
        
    elif sell_signals >= 2:
        recommendation['action'] = 'SELL'
        recommendation['confidence'] = min(sell_signals * 30 + tech_sell_count * 10, 90)
        recommendation['reasons'].insert(0, "建议减仓或清仓")
        
        # 卖出时也提供参考价位
        recommendation['entry_range'] = (current_price * 0.98, current_price * 1.02)
        recommendation['stop_loss'] = current_price * 1.08  # 反向止损
        recommendation['take_profit'] = (current_price * 0.90, current_price * 0.85)  # 目标回调位
        
    else:
        recommendation['action'] = 'HOLD'
        recommendation['confidence'] = 50
        recommendation['reasons'] = ["估值和技术信号不明确", "建议继续观察"]
        
        # HOLD时也提供参考价位
        recommendation['entry_range'] = (current_price * 0.95, current_price * 0.98)
        recommendation['stop_loss'] = current_price * 0.92
        if dcf_value and dcf_value > current_price:
            recommendation['take_profit'] = (dcf_value * 0.90, dcf_value)
        else:
            recommendation['take_profit'] = (current_price * 1.10, current_price * 1.20)
        
        # 计算观望时的参考仓位
        recommendation['position_size'] = 10.0  # 小仓位试探
    
    return recommendation

# ==================== 主程序 ====================
# 侧边栏输入
with st.sidebar:
    st.header("📊 分析参数设置")
    
    # 股票代码输入
    ticker = st.text_input("股票代码", "AAPL", help="输入股票代码，如：AAPL")
    
    # 市场选择（预留扩展）
    market = st.selectbox("市场选择", ["美股", "A股（待开发）"])
    
    # 分析按钮
    analyze_button = st.button("🔍 开始分析", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # 新增：止盈止损模拟器
    with st.expander("💰 止盈止损模拟器"):
        st.markdown("### 持仓盈亏计算")
        buy_price = st.number_input("买入价格 ($)", min_value=0.01, value=100.0, step=0.01)
        position_size = st.number_input("持仓数量", min_value=1, value=100, step=1)
        
        calculate_pnl = st.button("计算盈亏")
        
        if calculate_pnl:
            # 这里使用默认值，实际应该从data中获取
            current_price = 105.0  # 示例价格
            
            # 计算盈亏
            position_value = position_size * buy_price
            current_value = position_size * current_price
            pnl = current_value - position_value
            pnl_pct = (pnl / position_value) * 100
            
            # 止盈止损点
            stop_loss = buy_price * 0.9  # -10%
            take_profit = buy_price * 1.15  # +15%
            
            # 显示结果
            st.metric("当前盈亏", f"${pnl:.2f} ({pnl_pct:+.2f}%)")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("止损点 (-10%)", f"${stop_loss:.2f}")
            with col2:
                st.metric("止盈点 (+15%)", f"${take_profit:.2f}")
            
            # 根据盈亏给出建议
            if pnl_pct <= -10:
                st.error("⚠️ 已触及止损线！")
            elif pnl_pct >= 15:
                st.success("🎯 已达到止盈目标！")
            elif pnl_pct > 0:
                st.info(f"📈 盈利中，距离止盈还有 {15-pnl_pct:.1f}%")
            else:
                st.warning(f"📉 亏损中，距离止损还有 {-10-pnl_pct:.1f}%")
    
    st.markdown("---")
    
    # 新增：使用说明
    with st.expander("📘 使用说明"):
        st.markdown("""
        ### 如何解读各项数值指标
        
        **1. 安全边际（Margin of Safety）**
        - 正值：股价低于估值，存在低估
        - 负值：股价高于估值，存在高估
        - 建议：
          - \> 50%：强买入
          - 20-50%：买入
          - 0-20%：观察
          - < 0%：避免
        
        **2. 信心度（Confidence）**
        - \> 70%：高信心度
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
    
    # 联合建议表
    with st.expander("📊 投资决策参考表"):
        st.markdown("""
        | 安全边际 | 信心度 | 操作建议 |
        |---------|--------|----------|
        | >30%    | >70%   | ✅ 强买入 |
        | >0%     | >50%   | ⚠️ 观察  |
        | <0%     | ≈50%   | 🔍 观望  |
        | <0%     | <50%   | 🚫 回避  |
        """)
    
    st.markdown("---")
    st.markdown("### 说明")
    st.markdown("- 输入股票代码后点击分析")
    st.markdown("- 系统将自动获取数据并进行全面分析")
    st.markdown("- 分析包含基本面、技术面和估值模型")

# 主界面
if analyze_button and ticker:
    # 获取数据
    with st.spinner(f"正在获取 {ticker} 的数据..."):
        # 先尝试使用缓存版本
        try:
            data = fetch_stock_data(ticker)
        except:
            # 如果缓存失败，使用非缓存版本
            data = fetch_stock_data_uncached(ticker)
    
    if data:
        # 创建三列布局
        col1, col2, col3 = st.columns([1, 2, 1.5])
        
        # 左栏：公司基本信息
        with col1:
            st.subheader("📌 公司基本信息")
            info = data['info']
            
            # 公司信息卡片
            with st.container():
                st.metric("公司名称", info.get('longName', ticker))
                st.metric("当前股价", f"${info.get('currentPrice', 0):.2f}")
                st.metric("市值", f"${info.get('marketCap', 0)/1e9:.2f}B")
                st.metric("行业", info.get('industry', 'N/A'))
                st.metric("Beta", f"{info.get('beta', 0):.2f}")
                
                # 52周高低
                st.markdown("---")
                st.metric("52周最高", f"${info.get('fiftyTwoWeekHigh', 0):.2f}")
                st.metric("52周最低", f"${info.get('fiftyTwoWeekLow', 0):.2f}")
        
        # 中栏：分析结果
        with col2:
            st.subheader("📈 综合分析结果")
            
            # Piotroski F-Score
            with st.expander("🔍 Piotroski F-Score 分析", expanded=True):
                f_score, reasons = calculate_piotroski_score(data)
                
                # 评分展示
                score_color = "green" if f_score >= 7 else "orange" if f_score >= 4 else "red"
                st.markdown(f"### 得分: <span style='color:{score_color}; font-size:24px'>{f_score}/9</span>", unsafe_allow_html=True)
                
                # 评分解释
                for reason in reasons:
                    st.write(reason)
                
                # 建议
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
                    
                    # 新增：简洁的风险等级展示
                    if z_score > 2.99:
                        st.success("✅ 财务健康 - 企业财务状况良好，破产风险极低")
                    elif z_score >= 1.81:
                        st.warning("⚠️ 临界风险 - 企业处于灰色地带，需要密切关注")
                    else:
                        st.error("🚨 高破产风险 - 企业财务状况堪忧，投资需谨慎")
                    
                    # 评分标准说明
                    st.write("📊 评分标准:")
                    st.write("- Z > 2.99: 安全区域")
                    st.write("- 1.8 < Z < 2.99: 灰色区域")
                    st.write("- Z < 1.8: 危险区域")
            
            # 估值分析
            with st.expander("💎 估值分析", expanded=True):
                # DCF估值
                dcf_value, dcf_params = calculate_dcf_valuation(data)
                current_price = info.get('currentPrice', 0)
                
                if dcf_value and current_price > 0:
                    st.write("**DCF估值**")
                    col_x, col_y = st.columns(2)
                    with col_x:
                        st.metric("合理价值", f"${dcf_value:.2f}")
                        st.metric("当前价格", f"${current_price:.2f}")
                    with col_y:
                        margin = ((dcf_value - current_price) / dcf_value * 100) if dcf_value > 0 else 0
                        st.metric("安全边际", f"{margin:.2f}%")
                    
                    # 新增：DCF模型参数展示
                    if dcf_params:
                        with st.expander("📊 DCF模型参数详情"):
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
                            
                            # 显示逐年现金流
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
                
                # 相对估值
                st.write("**相对估值**")
                rel_val = calculate_relative_valuation(data)
                if rel_val:
                    col_m, col_n = st.columns(2)
                    with col_m:
                        pe_display = f"{rel_val['pe_ratio']:.2f}" if rel_val['pe_ratio'] > 0 else "N/A"
                        pb_display = f"{rel_val['pb_ratio']:.2f}" if rel_val['pb_ratio'] > 0 else "N/A"
                        st.metric("PE", pe_display)
                        st.metric("PB", pb_display)
                    with col_n:
                        st.metric("行业PE", f"{rel_val['industry_pe']:.2f}")
                        st.metric("行业PB", f"{rel_val['industry_pb']:.2f}")
                    
                    # 新增：历史估值分位图
                    if rel_val['pe_ratio'] > 0:
                        hist_val = calculate_historical_valuation_percentile(ticker, rel_val['pe_ratio'], rel_val['pb_ratio'])
                        if hist_val:
                            st.write("**历史估值分位**")
                            fig_hist = go.Figure()
                            
                            # 添加价格历史线
                            fig_hist.add_trace(go.Scatter(
                                x=hist_val['hist_prices'].index,
                                y=hist_val['hist_prices'].values,
                                mode='lines',
                                name='历史价格',
                                line=dict(color='blue', width=2)
                            ))
                            
                            # 添加当前价格标记
                            fig_hist.add_hline(y=current_price, line_dash="dash", line_color="red", 
                                             annotation_text=f"当前价格: ${current_price:.2f}")
                            
                            fig_hist.update_layout(
                                title=f"5年价格走势及当前位置（分位数: {hist_val['pe_percentile']:.1f}%）",
                                xaxis_title="日期",
                                yaxis_title="价格 ($)",
                                height=300
                            )
                            st.plotly_chart(fig_hist, use_container_width=True)
            
            # 新增：财务趋势分析
            with st.expander("📊 财务趋势分析", expanded=False):
                fin_trends = calculate_financial_trends(data)
                if fin_trends:
                    # 创建子图
                    fig_trends = go.Figure()
                    
                    # 添加营收趋势
                    fig_trends.add_trace(go.Bar(
                        name='营业收入',
                        x=fin_trends['years'],
                        y=[x/1e9 for x in fin_trends['revenues']],
                        yaxis='y',
                        marker_color='lightblue'
                    ))
                    
                    # 添加净利润趋势
                    fig_trends.add_trace(go.Bar(
                        name='净利润',
                        x=fin_trends['years'],
                        y=[x/1e9 for x in fin_trends['net_incomes']],
                        yaxis='y',
                        marker_color='lightgreen'
                    ))
                    
                    # 添加EPS趋势线
                    fig_trends.add_trace(go.Scatter(
                        name='每股收益(EPS)',
                        x=fin_trends['years'],
                        y=fin_trends['eps'],
                        yaxis='y2',
                        mode='lines+markers',
                        line=dict(color='red', width=3)
                    ))
                    
                    fig_trends.update_layout(
                        title='近3年财务趋势',
                        xaxis=dict(title='年份'),
                        yaxis=dict(title='金额（十亿美元）', side='left'),
                        yaxis2=dict(title='EPS ($)', overlaying='y', side='right'),
                        hovermode='x',
                        barmode='group',
                        height=400
                    )
                    
                    st.plotly_chart(fig_trends, use_container_width=True)
                else:
                    st.info("财务趋势数据不足")
        
        # 右栏：图表和建议
        with col3:
            st.subheader("📉 技术分析与建议")
            
            # 技术指标
            hist_data = data['hist_data'].copy()
            hist_data = calculate_technical_indicators(hist_data)
            
            # 价格走势图
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(hist_data.index[-180:], hist_data['Close'][-180:], label='Close', linewidth=2)
            ax.plot(hist_data.index[-180:], hist_data['MA20'][-180:], label='MA20', alpha=0.7)
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
            
            # 新增：自动买卖点建议模块
            st.markdown("---")
            st.subheader("💡 智能买卖点建议")
            
            # 获取DCF值（如果之前没有计算）
            if 'dcf_value' not in locals():
                dcf_value, _ = calculate_dcf_valuation(data)
            
            # 获取z_score
            if 'z_score' not in locals():
                z_score, _, _ = calculate_altman_z_score(data)
            
            # 分析信号
            valuation_signals = analyze_valuation_signals(data, dcf_value, current_price)
            technical_signals = analyze_technical_signals(hist_data)
            
            # 生成交易建议
            recommendation = generate_trading_recommendation(
                valuation_signals, 
                technical_signals, 
                current_price,
                dcf_value
            )
            
            # 显示建议卡片
            if recommendation['action'] == 'BUY':
                st.success(f"🟢 **强烈建议：{recommendation['action']}**")
                color_style = "background-color: #d4edda; padding: 15px; border-radius: 10px; border: 1px solid #c3e6cb;"
            elif recommendation['action'] == 'SELL':
                st.error(f"🔴 **强烈建议：{recommendation['action']}**")
                color_style = "background-color: #f8d7da; padding: 15px; border-radius: 10px; border: 1px solid #f5c6cb;"
            else:
                st.info(f"🔵 **建议：{recommendation['action']}**")
                color_style = "background-color: #d1ecf1; padding: 15px; border-radius: 10px; border: 1px solid #bee5eb;"
            
            # 详细信息展示
            with st.container():
                st.markdown(f'<div style="{color_style}">', unsafe_allow_html=True)
                
                # 基本信息
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("当前价格", f"${current_price:.2f}")
                    if dcf_value:
                        st.metric("合理估值", f"${dcf_value:.2f}")
                with col_b:
                    st.metric("安全边际", f"{valuation_signals['margin']:.1f}%")
                    st.metric("信心度", f"{recommendation['confidence']}%")
                
                # 信号原因
                st.markdown("**📊 判断依据：**")
                for reason in recommendation['reasons']:
                    st.write(f"• {reason}")
                
                # 操作建议 - 修复显示所有操作的建议
                st.markdown("**📍 操作建议：**")
                
                if recommendation['action'] == 'BUY':
                    st.write(f"• 🎯 建仓区间：${recommendation['entry_range'][0]:.2f} - ${recommendation['entry_range'][1]:.2f}")
                    st.write(f"• 🛡️ 止损价位：${recommendation['stop_loss']:.2f} (下跌{((current_price - recommendation['stop_loss'])/current_price*100):.1f}%)")
                    st.write(f"• 💰 止盈目标：${recommendation['take_profit'][0]:.2f} - ${recommendation['take_profit'][1]:.2f} (上涨{((recommendation['take_profit'][0] - current_price)/current_price*100):.1f}%-{((recommendation['take_profit'][1] - current_price)/current_price*100):.1f}%)")
                    st.write(f"• 📊 推荐仓位：{recommendation['position_size']:.1f}%")
                elif recommendation['action'] == 'SELL':
                    st.write(f"• 🔴 建议清仓或减仓")
                    st.write(f"• 📉 当前处于高估区域")
                    st.write(f"• ⚠️ 建议等待回调后再考虑")
                else:  # HOLD
                    st.write(f"• 🔵 建议继续持有观望")
                    st.write(f"• 📊 等待更明确的信号")
                    if dcf_value and current_price < dcf_value * 0.85:
                        buy_zone = (dcf_value * 0.75, dcf_value * 0.85)
                        st.write(f"• 💡 参考买入区间：${buy_zone[0]:.2f} - ${buy_zone[1]:.2f}")
                    if current_price > 0:
                        st.write(f"• 🛡️ 参考止损：${current_price * 0.92:.2f}")
                
                # 技术指标状态
                st.markdown("**📈 技术指标状态：**")
                latest = hist_data.iloc[-1]
                
                col_x, col_y = st.columns(2)
                with col_x:
                    if 'RSI' in hist_data.columns:
                        rsi_value = latest['RSI']
                        rsi_status = "超卖" if rsi_value < 30 else "超买" if rsi_value > 70 else "中性"
                        st.write(f"• RSI: {rsi_value:.1f} ({rsi_status})")
                    
                    if 'MACD' in hist_data.columns:
                        macd_status = "金叉" if technical_signals['macd_golden_cross'] else "死叉" if technical_signals['macd_death_cross'] else "中性"
                        st.write(f"• MACD: {macd_status}")
                
                with col_y:
                    if 'MA10' in hist_data.columns and 'MA60' in hist_data.columns:
                        ma_status = "多头" if latest['MA10'] > latest['MA60'] else "空头"
                        st.write(f"• 均线: {ma_status}")
                    
                    trend_status = "上升" if technical_signals['trend'] == 'bullish' else "下降"
                    st.write(f"• 趋势: {trend_status}")
                
                # 更新时间
                st.markdown("---")
                st.caption(f"⏰ 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 综合评分
            comprehensive = calculate_comprehensive_score(
                f_score, 
                z_score if z_score else 0,
                valuation_signals['margin'],
                technical_signals
            )
            
            st.markdown("---")
            st.subheader("🎯 智能投资评分")
            
            col_score1, col_score2, col_score3 = st.columns(3)
            with col_score1:
                st.metric("价值得分", f"{comprehensive['value_score']}/50")
            with col_score2:
                st.metric("技术得分", f"{comprehensive['tech_score']}/50")
            with col_score3:
                st.metric("综合得分", f"{comprehensive['total_score']}/100")
            
            # 最终建议
            if comprehensive['recommendation'] == 'BUY':
                st.success(f"🟢 **最终建议：{comprehensive['recommendation']}**")
            elif comprehensive['recommendation'] == 'SELL':
                st.error(f"🔴 **最终建议：{comprehensive['recommendation']}**")
            else:
                st.info(f"🔵 **最终建议：{comprehensive['recommendation']}**")
            
            # 新增：财务趋势图
            st.markdown("---")
            st.subheader("📊 财务趋势分析")
            
            fin_trends = calculate_financial_trends(data)
            if fin_trends:
                # 创建子图
                fig_trends = go.Figure()
                
                # 添加营收趋势
                fig_trends.add_trace(go.Bar(
                    name='营业收入',
                    x=fin_trends['years'],
                    y=[x/1e9 for x in fin_trends['revenues']],
                    yaxis='y',
                    marker_color='lightblue'
                ))
                
                # 添加净利润趋势
                fig_trends.add_trace(go.Bar(
                    name='净利润',
                    x=fin_trends['years'],
                    y=[x/1e9 for x in fin_trends['net_incomes']],
                    yaxis='y',
                    marker_color='lightgreen'
                ))
                
                # 添加EPS趋势线
                fig_trends.add_trace(go.Scatter(
                    name='每股收益(EPS)',
                    x=fin_trends['years'],
                    y=fin_trends['eps'],
                    yaxis='y2',
                    mode='lines+markers',
                    line=dict(color='red', width=3)
                ))
                
                fig_trends.update_layout(
                    title='近3年财务趋势',
                    xaxis=dict(title='年份'),
                    yaxis=dict(title='金额（十亿美元）', side='left'),
                    yaxis2=dict(title='EPS ($)', overlaying='y', side='right'),
                    hovermode='x',
                    barmode='group',
                    height=400
                )
                
                st.plotly_chart(fig_trends, use_container_width=True)
            else:
                st.info("财务趋势数据不足")
            
            # 新增：风险雷达图
            st.markdown("---")
            st.subheader("🎯 风险评估雷达图")
            
            risk_metrics = calculate_risk_metrics(data)
            if risk_metrics:
                categories = ['偿债能力', '波动性控制', '财务杠杆', '现金流增长', '盈利能力']
                values = [
                    risk_metrics['interest_coverage'],
                    risk_metrics['beta_score'],
                    risk_metrics['leverage_score'],
                    risk_metrics['fcf_growth_score'],
                    risk_metrics['profitability_score']
                ]
                
                fig_radar = go.Figure(data=go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name='风险评分'
                ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 10]
                        )
                    ),
                    showlegend=False,
                    title="风险指标评分（10分制）",
                    height=400
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)
                
                # 风险解读
                avg_risk_score = sum(values) / len(values)
                if avg_risk_score >= 7:
                    st.success("✅ 总体风险等级：低")
                elif avg_risk_score >= 5:
                    st.warning("⚠️ 总体风险等级：中")
                else:
                    st.error("🚨 总体风险等级：高")
            
            # 风险等级
            st.markdown("---")
            if info.get('beta', 1) > 1.5:
                risk_level = "高风险"
                risk_color = "red"
            elif info.get('beta', 1) > 1.0:
                risk_level = "中风险"
                risk_color = "orange"
            else:
                risk_level = "低风险"
                risk_color = "green"
            
            st.markdown(f"**风险等级**: <span style='color:{risk_color}'>{risk_level}</span>", unsafe_allow_html=True)
            st.caption(f"Beta: {info.get('beta', 'N/A')}")

else:
    # 默认展示
    st.info("👈 请在左侧输入股票代码并点击分析按钮开始")
    
    # 使用说明
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
        - **相对估值**: PE、PB等指标与行业对比
        - **技术分析**: 均线、MACD等技术指标
        - **Kelly公式**: 科学计算最优投资仓位
        
        ### 新增功能 (v2.0)
        - **DCF参数详情**: 展示估值模型的详细参数
        - **历史估值分位**: 当前估值在历史中的位置
        - **财务趋势图**: 营收、利润、EPS趋势
        - **风险雷达图**: 多维度风险评估
        - **智能评分系统**: 价值面+技术面综合评分
        - **止盈止损模拟器**: 计算盈亏和关键价位
        
        ### 注意事项
        - 本系统仅供参考，不构成投资建议
        - 请结合其他信息进行综合判断
        - 投资有风险，入市需谨慎
        """)
    
    # 新增：展示新功能示例
    with st.expander("🆕 新功能展示"):
        st.markdown("### v2.0 新增功能预览")
        
        # 示例：风险雷达图
        st.subheader("风险雷达图示例")
        categories = ['偿债能力', '波动性控制', '财务杠杆', '现金流增长', '盈利能力']
        values = [8, 7, 6, 5, 8]
        
        fig_demo = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='风险评分'
        ))
        
        fig_demo.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )
            ),
            showlegend=False,
            title="风险指标评分示例（10分制）",
            height=300
        )
        
        st.plotly_chart(fig_demo, use_container_width=True)
        
        # 示例：智能评分
        st.subheader("智能评分示例")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("价值得分", "35/50")
        with col2:
            st.metric("技术得分", "40/50")
        with col3:
            st.metric("综合得分", "75/100")
        
        st.info("输入股票代码后即可查看完整分析结果")
    
    # 预留扩展功能
    with st.expander("🚀 未来功能规划"):
        st.markdown("""
        - [ ] A股市场支持（集成tushare）
        - [ ] 一键导出PDF分析报告
        - [ ] 多股票对比分析
        - [ ] 自定义分析模型参数
        - [ ] 实时数据推送提醒
        - [ ] AI智能投资助手
        - [ ] 投资组合优化建议
        - [ ] 新闻情绪分析
        - [ ] 期权策略建议
        """)

# 页脚
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns([1, 2, 1])
with col_footer2:
    if st.button("🔙 返回首页 / 清除数据", type="secondary", use_container_width=True):
        st.rerun()

st.markdown("💹 智能投资分析系统 v2.0 | 仅供参考，投资需谨慎")import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime, timedelta
import warnings
import plotly.graph_objects as go
import plotly.express as px
warnings.filterwarnings('ignore')

# 技术分析库（如果没有安装，系统会自动使用备用方案）
try:
    import pandas_ta as ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 页面配置
st.set_page_config(
    page_title="💹 我的智能投资分析系统",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("💹 我的智能投资分析系统 v2.0")
st.markdown("---")

# ==================== 缓存函数 ====================
@st.cache_data(ttl=3600)
def fetch_stock_data(ticker):
    """获取股票数据"""
    try:
        stock = yf.Ticker(ticker)
        info = dict(stock.info)  # 转换为普通字典
        
        # 获取历史数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*2)
        hist_data = stock.history(start=start_date, end=end_date)
        
        # 获取财务数据
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        # 确保所有数据都是可序列化的
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

# 不使用缓存的版本，用于获取实时数据
def fetch_stock_data_uncached(ticker):
    """获取股票数据（不缓存版本）"""
    try:
        stock = yf.Ticker(ticker)
        info = dict(stock.info)
        
        # 获取历史数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*2)
        hist_data = stock.history(start=start_date, end=end_date)
        
        # 获取财务数据
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

# ==================== 分析模型函数 ====================
def calculate_piotroski_score(data):
    """计算Piotroski F-Score"""
    score = 0
    reasons = []
    
    try:
        financials = data['financials']
        balance_sheet = data['balance_sheet']
        cash_flow = data['cash_flow']
        
        # 检查数据是否为空
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
        # 由于yfinance数据限制，这里简化计算
        score += 3  # 给予基础分数
        reasons.append("📊 财务结构基础分: 3分")
        
    except Exception as e:
        st.warning(f"Piotroski Score计算部分指标失败: {str(e)}")
        return 0, ["❌ 计算过程出现错误"]
    
    return score, reasons

def calculate_dupont_analysis(data):
    """杜邦分析"""
    try:
        info = data['info']
        
        # 获取关键指标
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
        
        # 检查数据是否为空
        if balance_sheet.empty:
            return 0, "数据不足", "gray"
        
        # 获取必要数据，使用get方法避免KeyError
        total_assets = info.get('totalAssets', 0)
        
        # 安全获取资产负债表数据
        current_assets = 0
        current_liabilities = 0
        retained_earnings = 0
        total_liabilities = 0
        
        if not balance_sheet.empty and len(balance_sheet.columns) > 0:
            # 尝试不同的可能字段名
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
        
        # 如果总资产为0或负数，返回默认值
        if total_assets <= 0:
            return 0, "数据不足", "gray"
        
        # 计算Z-Score组成部分
        working_capital = current_assets - current_liabilities
        
        A = (working_capital / total_assets) * 1.2
        B = (retained_earnings / total_assets) * 1.4 if not pd.isna(retained_earnings) else 0
        C = (ebit / total_assets) * 3.3 if ebit > 0 else 0
        D = (market_cap / total_liabilities) * 0.6 if total_liabilities > 0 else 0
        E = (revenue / total_assets) * 1.0 if revenue > 0 else 0
        
        z_score = A + B + C + D + E
        
        # 处理异常值
        if pd.isna(z_score) or z_score < -10 or z_score > 10:
            z_score = 0
        
        # 判断财务健康状态
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
        
        # 检查数据是否为空
        if cash_flow.empty:
            return None, None
        
        # 获取自由现金流
        fcf = 0
        if 'Free Cash Flow' in cash_flow.index and len(cash_flow.columns) > 0:
            fcf = cash_flow.loc['Free Cash Flow'].iloc[0]
        elif 'Operating Cash Flow' in cash_flow.index and len(cash_flow.columns) > 0:
            # 如果没有自由现金流，使用经营现金流估算
            ocf = cash_flow.loc['Operating Cash Flow'].iloc[0]
            capex = cash_flow.loc['Capital Expenditure'].iloc[0] if 'Capital Expenditure' in cash_flow.index else 0
            fcf = ocf + capex  # capex通常是负数
        
        # 如果现金流为负或0，无法进行DCF估值
        if fcf <= 0:
            return None, None
        
        # 模型参数
        growth_rate = 0.05  # 5%增长率
        discount_rate = 0.10  # 10%折现率
        terminal_growth = 0.02  # 2%永续增长率
        forecast_years = 5
        
        # 计算各年现金流现值
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
        
        # 计算终值
        terminal_fcf = fcf * (1 + growth_rate) ** forecast_years * (1 + terminal_growth)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth)
        terminal_pv = terminal_value / (1 + discount_rate) ** forecast_years
        
        # 企业价值
        enterprise_value = dcf_value + terminal_pv
        
        # 计算每股价值
        shares = info.get('sharesOutstanding', 0)
        if shares <= 0:
            return None, None
            
        fair_value_per_share = enterprise_value / shares
        
        # 合理性检查
        if fair_value_per_share < 0 or fair_value_per_share > 10000:
            return None, None
        
        # 返回估值结果和详细参数
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

def calculate_relative_valuation(data):
    """相对估值分析"""
    try:
        info = data['info']
        
        pe_ratio = info.get('trailingPE', 0)
        pb_ratio = info.get('priceToBook', 0)
        ev_ebitda = info.get('enterpriseToEbitda', 0)
        
        # 行业平均值（这里使用假设值，实际应用中应该从数据库获取）
        industry_pe = 20
        industry_pb = 3
        industry_ev_ebitda = 12
        
        return {
            'pe_ratio': pe_ratio,
            'pb_ratio': pb_ratio,
            'ev_ebitda': ev_ebitda,
            'industry_pe': industry_pe,
            'industry_pb': industry_pb,
            'industry_ev_ebitda': industry_ev_ebitda
        }
    except Exception as e:
        st.warning(f"相对估值计算失败: {str(e)}")
        return None

def calculate_technical_indicators(hist_data):
    """计算技术指标"""
    try:
        # 计算移动平均线
        hist_data['MA10'] = hist_data['Close'].rolling(window=10).mean()
        hist_data['MA20'] = hist_data['Close'].rolling(window=20).mean()
        hist_data['MA60'] = hist_data['Close'].rolling(window=60).mean()
        
        # 计算MACD
        exp1 = hist_data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist_data['Close'].ewm(span=26, adjust=False).mean()
        hist_data['MACD'] = exp1 - exp2
        hist_data['Signal'] = hist_data['MACD'].ewm(span=9, adjust=False).mean()
        hist_data['MACD_Histogram'] = hist_data['MACD'] - hist_data['Signal']
        
        # 计算RSI
        delta = hist_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist_data['RSI'] = 100 - (100 / (1 + rs))
        
        # 计算布林带
        hist_data['BB_Middle'] = hist_data['Close'].rolling(window=20).mean()
        bb_std = hist_data['Close'].rolling(window=20).std()
        hist_data['BB_Upper'] = hist_data['BB_Middle'] + (bb_std * 2)
        hist_data['BB_Lower'] = hist_data['BB_Middle'] - (bb_std * 2)
        hist_data['BB_Width'] = hist_data['BB_Upper'] - hist_data['BB_Lower']
        
        # 计算成交量移动平均
        hist_data['Volume_MA'] = hist_data['Volume'].rolling(window=20).mean()
        
        return hist_data
    except Exception as e:
        st.warning(f"技术指标计算失败: {str(e)}")
        return hist_data

def calculate_kelly_criterion(win_prob, win_loss_ratio):
    """Kelly公式计算推荐仓位"""
    f = (win_prob * win_loss_ratio - (1 - win_prob)) / win_loss_ratio
    return max(0, min(f, 0.25))  # 限制最大仓位为25%

def calculate_historical_valuation_percentile(ticker, current_pe, current_pb):
    """计算历史估值分位"""
    try:
        # 获取5年历史数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*5)
        
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date, interval="1mo")
        
        # 简化处理：使用价格变化来估算历史PE变化
        # 实际应用中应该获取历史财务数据
        price_percentile = (hist['Close'] < hist['Close'].iloc[-1]).sum() / len(hist) * 100
        
        return {
            'pe_percentile': price_percentile,
            'pb_percentile': price_percentile * 0.9,  # 简化估算
            'hist_prices': hist['Close']
        }
    except:
        return None

def calculate_financial_trends(data):
    """计算财务趋势"""
    try:
        financials = data['financials']
        info = data['info']
        
        if financials.empty or len(financials.columns) < 3:
            return None
        
        # 获取最近3年数据
        years = []
        revenues = []
        net_incomes = []
        eps_values = []
        
        for i in range(min(3, len(financials.columns))):
            year = datetime.now().year - i
            years.append(str(year))
            
            revenue = financials.loc['Total Revenue'].iloc[i] if 'Total Revenue' in financials.index else 0
            net_income = financials.loc['Net Income'].iloc[i] if 'Net Income' in financials.index else 0
            
            revenues.append(revenue)
            net_incomes.append(net_income)
            
            shares = info.get('sharesOutstanding', 1)
            eps = net_income / shares if shares > 0 else 0
            eps_values.append(eps)
        
        return {
            'years': years[::-1],
            'revenues': revenues[::-1],
            'net_incomes': net_incomes[::-1],
            'eps': eps_values[::-1]
        }
    except:
        return None

def calculate_risk_metrics(data):
    """计算风险指标"""
    try:
        info = data['info']
        financials = data['financials']
        balance_sheet = data['balance_sheet']
        
        # 1. 偿债能力 - Interest Coverage Ratio
        ebit = info.get('ebitda', 0)
        interest_expense = financials.loc['Interest Expense'].iloc[0] if 'Interest Expense' in financials.index and not financials.empty else 1
        interest_coverage = abs(ebit / interest_expense) if interest_expense != 0 else 10
        interest_coverage = min(interest_coverage, 10)  # 上限10
        
        # 2. 波动性 - Beta
        beta = info.get('beta', 1)
        beta_score = max(0, 10 - beta * 5)  # Beta越低分数越高
        
        # 3. 财务杠杆 - 资产负债率
        total_assets = info.get('totalAssets', 1)
        total_debt = info.get('totalDebt', 0)
        debt_ratio = total_debt / total_assets if total_assets > 0 else 0
        leverage_score = max(0, 10 - debt_ratio * 10)
        
        # 4. 现金流增长
        fcf_growth_score = 5  # 默认中等分数
        
        # 5. 盈利能力 - 净利率
        profit_margin = info.get('profitMargins', 0) * 100
        profitability_score = min(profit_margin, 10)
        
        return {
            'interest_coverage': interest_coverage,
            'beta_score': beta_score,
            'leverage_score': leverage_score,
            'fcf_growth_score': fcf_growth_score,
            'profitability_score': profitability_score
        }
    except:
        return None

def calculate_comprehensive_score(f_score, z_score, valuation_margin, technical_signals):
    """计算综合评分"""
    # 价值得分（50分）
    value_score = 0
    if f_score >= 7:
        value_score += 20
    elif f_score >= 4:
        value_score += 10
    
    if z_score and z_score > 2.99:
        value_score += 15
    elif z_score and z_score > 1.8:
        value_score += 5
    
    if valuation_margin > 20:
        value_score += 15
    elif valuation_margin > 0:
        value_score += 7
    
    # 技术得分（50分）
    tech_score = 0
    if technical_signals['ma_golden_cross']:
        tech_score += 15
    if technical_signals['macd_golden_cross']:
        tech_score += 15
    if technical_signals['rsi_oversold']:
        tech_score += 10
    if technical_signals['bb_breakout']:
        tech_score += 10
    
    total_score = value_score + tech_score
    
    if total_score >= 70:
        recommendation = "BUY"
    elif total_score >= 40:
        recommendation = "HOLD"
    else:
        recommendation = "SELL"
    
    return {
        'value_score': value_score,
        'tech_score': tech_score,
        'total_score': total_score,
        'recommendation': recommendation
    }

def analyze_valuation_signals(data, dcf_value, current_price):
    """分析估值信号"""
    valuation_signals = {
        'undervalued': False,
        'overvalued': False,
        'margin': 0,
        'pe_status': 'neutral',
        'pb_status': 'neutral'
    }
    
    try:
        info = data['info']
        
        # DCF估值分析
        if dcf_value and current_price > 0:
            margin = ((dcf_value - current_price) / dcf_value * 100)
            valuation_signals['margin'] = margin
            
            if margin > 20:  # 低估20%以上
                valuation_signals['undervalued'] = True
            elif margin < -20:  # 高估20%以上
                valuation_signals['overvalued'] = True
        
        # PE/PB相对估值分析
        pe_ratio = info.get('trailingPE', 0)
        pb_ratio = info.get('priceToBook', 0)
        
        # 这里使用行业平均值作为参考（实际应用中应该获取历史数据）
        if pe_ratio > 0 and pe_ratio < 15:
            valuation_signals['pe_status'] = 'undervalued'
        elif pe_ratio > 30:
            valuation_signals['pe_status'] = 'overvalued'
            
        if pb_ratio > 0 and pb_ratio < 1.5:
            valuation_signals['pb_status'] = 'undervalued'
        elif pb_ratio > 5:
            valuation_signals['pb_status'] = 'overvalued'
    
    except Exception as e:
        st.warning(f"估值信号分析失败: {str(e)}")
    
    return valuation_signals

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
        
        # 获取最近的数据
        latest = hist_data.iloc[-1]
        prev = hist_data.iloc[-2]
        
        # 移动均线信号
        if 'MA10' in hist_data.columns and 'MA60' in hist_data.columns:
            if latest['MA10'] > latest['MA60'] and prev['MA10'] <= prev['MA60']:
                signals['ma_golden_cross'] = True
            elif latest['MA10'] < latest['MA60'] and prev['MA10'] >= prev['MA60']:
                signals['ma_death_cross'] = True
        
        # MACD信号
        if 'MACD' in hist_data.columns and 'Signal' in hist_data.columns:
            if latest['MACD'] > latest['Signal'] and prev['MACD'] <= prev['Signal']:
                signals['macd_golden_cross'] = True
            elif latest['MACD'] < latest['Signal'] and prev['MACD'] >= prev['Signal']:
                signals['macd_death_cross'] = True
        
        # RSI信号
        if 'RSI' in hist_data.columns:
            rsi_recent = hist_data['RSI'].iloc[-5:]  # 最近5天
            if latest['RSI'] < 30:
                signals['rsi_oversold'] = True
            elif latest['RSI'] > 70:
                signals['rsi_overbought'] = True
            
            # 检查RSI是否拐头向上
            if len(rsi_recent) >= 3 and rsi_recent.iloc[-1] > rsi_recent.iloc[-2] < rsi_recent.iloc[-3]:
                if latest['RSI'] < 40:
                    signals['rsi_oversold'] = True
        
        # 布林带信号
        if 'BB_Middle' in hist_data.columns:
            if latest['Close'] > latest['BB_Middle'] and prev['Close'] <= prev['BB_Middle']:
                # 检查布林带是否扩张
                bb_width_change = (latest['BB_Width'] - hist_data['BB_Width'].iloc[-5]) / hist_data['BB_Width'].iloc[-5]
                if bb_width_change > 0.1:  # 布林带扩张10%以上
                    signals['bb_breakout'] = True
        
        # 成交量背离检查
        if 'Volume_MA' in hist_data.columns:
            recent_prices = hist_data['Close'].iloc[-5:]
            recent_volumes = hist_data['Volume'].iloc[-5:]
            
            # 价格上涨但成交量下降
            if recent_prices.iloc[-1] > recent_prices.iloc[0] and recent_volumes.iloc[-1] < recent_volumes.iloc[0]:
                signals['volume_divergence'] = True
        
        # 判断总体趋势
        if latest['Close'] > latest['MA60']:
            signals['trend'] = 'bullish'
        else:
            signals['trend'] = 'bearish'
            
    except Exception as e:
        st.warning(f"技术信号分析失败: {str(e)}")
    
    return signals

def generate_trading_recommendation(valuation_signals, technical_signals, current_price, dcf_value):
    """生成交易建议
