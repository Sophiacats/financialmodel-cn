# 📊 专业级相对估值模型 - FinancialModel.cn

## 🌟 项目简介

这是一个专业级的股票相对估值分析工具，基于Streamlit构建，提供PE/PB/EV/EBITDA等多维度估值分析功能。

### ✨ 核心功能

- 📈 **多指标估值计算**: PE、PB、EV/EBITDA、EV/EBIT、PEG
- 📊 **同行业对比分析**: 可比公司数据管理和对比
- 📋 **数据管理**: 灵活的公司数据增删改
- 💡 **智能投资建议**: 基于估值分析的投资建议
- 📄 **报告导出**: Excel数据和分析报告导出

### 🎯 适用用户

- 📈 投资分析师
- 🏢 企业财务人员  
- 🎓 金融专业学生
- 💼 投资顾问
- 📊 量化研究员

## 🚀 在线体验

访问: **[FinancialModel.cn](https://financialmodel.cn)** 

## 🛠️ 技术栈

- **前端框架**: Streamlit
- **数据处理**: Pandas, Numpy
- **图表可视化**: Plotly
- **部署平台**: Streamlit Cloud

## 📦 安装部署

### 本地运行

1. **克隆仓库**
```bash
git clone https://github.com/your-username/financial-model-saas.git
cd financial-model-saas
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行应用**
```bash
streamlit run app.py
```

4. **访问应用**
```
本地地址: http://localhost:8501
```

### 云端部署

本项目已配置好Streamlit Cloud自动部署：

1. Fork本仓库到你的GitHub账号
2. 访问 [share.streamlit.io](https://share.streamlit.io)
3. 连接GitHub仓库并部署

## 📖 使用指南

### 1. 基础估值计算

1. **输入目标公司数据**
   - 公司名称、股价、总股本
   - 净利润、净资产、EBITDA/EBIT
   - 现金、有息负债、增长率

2. **查看估值指标**
   - PE（市盈率）= 市值 ÷ 净利润
   - PB（市净率）= 市值 ÷ 净资产
   - EV/EBITDA = 企业价值 ÷ EBITDA
   - PEG = PE ÷ 增长率

### 2. 同行业对比

1. **添加可比公司**: 在数据管理页面添加同行公司数据
2. **对比分析**: 查看估值雷达图和柱状图对比
3. **行业基准**: 自动计算行业平均水平

### 3. 投资建议

系统基于以下逻辑生成投资建议：
- PE水平 vs 行业均值
- PEG比率分析（<1为优秀）
- PB安全边际评估
- 综合评级：买入/谨慎乐观/中性/规避

### 4. 报告导出

- **Excel数据**: 包含所有公司估值指标对比
- **分析报告**: Markdown格式的详细分析报告

## 🔧 配置说明

### 环境变量

创建 `.env` 文件（可选）：
```env
# 应用配置
APP_TITLE=专业级相对估值模型
APP_DOMAIN=financialmodel.cn

# 主题配置  
THEME_PRIMARY_COLOR=#3b82f6
THEME_BACKGROUND_COLOR=#ffffff
```

### Streamlit配置

`.streamlit/config.toml` 文件已包含优化配置：
- 主题颜色
- 服务器设置
- 浏览器配置

## 📊 模型说明

### 估值指标公式

| 指标 | 公式 | 说明 |
|------|------|------|
| PE | 市值 ÷ 净利润 | 市盈率，反映投资回收期 |
| PB | 市值 ÷ 净资产 | 市净率，反映账面价值倍数 |
| EV/EBITDA | 企业价值 ÷ EBITDA | 考虑负债的盈利能力倍数 |
| EV/EBIT | 企业价值 ÷ EBIT | 税前利润倍数 |
| PEG | PE ÷ 增长率 | 考虑成长性的PE修正 |

### 企业价值计算

```
企业价值(EV) = 市值 + 有息负债 - 现金
市值 = 股价 × 总股本
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置

1. Fork本仓库
2. 创建特性分支: `git checkout -b feature/新功能`
3. 提交更改: `git commit -m '添加新功能'`
4. 推送分支: `git push origin feature/新功能`
5. 提交Pull Request

### 代码规范

- 使用Python PEP 8编码规范
- 添加必要的注释和文档
- 确保代码通过测试

## 📈 路线图

### 近期计划 (v1.1)
- [ ] 添加DCF估值模型
- [ ] 增加历史估值趋势图
- [ ] 支持批量导入数据
- [ ] 用户登录和数据保存

### 中期计划 (v1.5)
- [ ] 债券估值工具
- [ ] 期权定价计算器
- [ ] API接口开发
- [ ] 移动端优化

### 长期规划 (v2.0)
- [ ] 多语言支持
- [ ] 实时数据接入
- [ ] 机器学习预测
- [ ] 企业级功能

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 📞 联系我们

- 🌐 **官网**: [FinancialModel.cn](https://financialmodel.cn)
- 📧 **邮箱**: contact@financialmodel.cn
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/financial-model-saas/issues)

## 🙏 致谢

感谢以下开源项目：
- [Streamlit](https://streamlit.io/) - 优秀的Python Web应用框架
- [Plotly](https://plotly.com/) - 强大的交互式图表库
- [Pandas](https://pandas.pydata.org/) - 数据处理工具

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个Star！⭐**

[🚀 在线体验](https://financialmodel.cn) | [📖 使用文档](https://docs.financialmodel.cn) | [💬 反馈建议](https://github.com/your-username/financial-model-saas/issues)

</div>
