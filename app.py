def basic_financial_translate(text):
    """增强的财经术语翻译"""
    if not text:
        return text
    
    # 大幅扩展的翻译词典
    financial_dict = {
        # 完整句式和短语
        'said in a statement': '在声明中表示',
        'according to': '据',
        'is expected to': '预计将',
        'announced today': '今日宣布',
        'announced that': '宣布',
        'reported earnings': '公布财报',
        'quarterly earnings': '季度财报',
        'earnings report': '财报',
        'shares rose': '股价上涨',
        'shares fell': '股价下跌',
        'shares gained': '股价上涨',
        'shares dropped': '股价下跌',
        'stock price': '股价',
        'market cap': '市值',
        'market value': '市值',
        'revenue growth': '营收增长',
        'quarterly results': '季度业绩',
        'financial results': '财务业绩',
        'net income': '净利润',
        'gross profit': '毛利润',
        'operating income': '营业利润',
        'cash flow': '现金流',
        'free cash flow': '自由现金流',
        'balance sheet': '资产负债表',
        'income statement': '损益表',
        'profit margin': '利润率',
        'return on investment': '投资回报率',
        'return on equity': '净资产收益率',
        'debt to equity': '负债权益比',
        'price to earnings': '市盈率',
        'earnings per share': '每股收益',
        'dividend yield': '股息收益率',
        'book value': '账面价值',
        'market capitalization': '市值',
        'enterprise value': '企业价值',
        'trading volume': '交易量',
        'market share': '市场份额',
        'competitive advantage': '竞争优势',
        'business model': '商业模式',
        'supply chain': '供应链',
        'product launch': '产品发布',
        'new product': '新产品',
        'product line': '产品线',
        'market expansion': '市场扩张',
        'global expansion': '全球扩张',
        'strategic partnership': '战略合作',
        'joint venture': '合资企业',
        'merger and acquisition': '并购',
        'acquisition deal': '收购交易',
        'regulatory approval': '监管批准',
        'regulatory filing': '监管申报',
        'sec filing': 'SEC申报',
        'insider trading': '内幕交易',
        'stock buyback': '股票回购',
        'share repurchase': '股份回购',
        'stock split': '股票拆分',
        'dividend payment': '分红派息',
        'special dividend': '特别分红',
        'stock offering': '股票发行',
        'initial public offering': '首次公开募股',
        'ipo': '首次公开募股',
        'follow-on offering': '后续发行',
        'private placement': '私募配售',
        'institutional investor': '机构投资者',
        'retail investor': '散户投资者',
        'hedge fund': '对冲基金',
        'mutual fund': '共同基金',
        'pension fund': '养老基金',
        'sovereign wealth fund': '主权财富基金',
        'investment bank': '投资银行',
        'commercial bank': '商业银行',
        'central bank': '央行',
        'federal reserve': '美联储',
        'interest rate': '利率',
        'inflation rate': '通胀率',
        'unemployment rate': '失业率',
        'gdp growth': 'GDP增长',
        'economic growth': '经济增长',
        'economic recession': '经济衰退',
        'economic recovery': '经济复苏',
        'economic expansion': '经济扩张',
        'bear market': '熊市',
        'bull market': '牛市',
        'market volatility': '市场波动',
        'market correction': '市场调整',
        'market rally': '市场反弹',
        'market decline': '市场下跌',
        'market crash': '市场崩盘',
        'stock exchange': '证券交易所',
        'nasdaq': '纳斯达克',
        'new york stock exchange': '纽约证券交易所',
        'dow jones': '道琼斯',
        'sp 500': '标普500',
        's&p 500': '标普500',
        'russell 2000': '罗素2000',
        'ftse 100': '富时100',
        'nikkei 225': '日经225',
        'hang seng': '恒生指数',
        'shanghai composite': '上证综指',
        
        # 公司名称（更全面）
        'Apple Inc': '苹果公司',
        'Apple': '苹果公司',
        'Tesla Inc': '特斯拉公司', 
        'Tesla': '特斯拉公司',
        'Microsoft Corporation': '微软公司',
        'Microsoft': '微软公司',
        'Amazon.com Inc': '亚马逊公司',
        'Amazon': '亚马逊公司',
        'Alphabet Inc': '谷歌母公司',
        'Google': '谷歌',
        'Meta Platforms': 'Meta平台公司',
        'Meta': 'Meta公司',
        'Facebook': '脸书',
        'NVIDIA Corporation': '英伟达公司',
        'NVIDIA': '英伟达',
        'Netflix Inc': '奈飞公司',
        'Netflix': '奈飞',
        'PayPal Holdings': 'PayPal公司',
        'PayPal': 'PayPal',
        'Adobe Inc': 'Adobe公司',
        'Salesforce': 'Salesforce公司',
        'Oracle Corporation': '甲骨文公司',
        'Oracle': '甲骨文',
        'Intel Corporation': '英特尔公司',
        'Intel': '英特尔',
        'Advanced Micro Devices': '超威半导体公司',
        'AMD': 'AMD',
        'Qualcomm': '高通公司',
        'Broadcom': '博通公司',
        'Taiwan Semiconductor': '台积电',
        'TSMC': '台积电',
        'Samsung': '三星公司',
        'Sony': '索尼公司',
        'Toyota': '丰田汽车',
        'Volkswagen': '大众汽车',
        'General Motors': '通用汽车',
        'Ford Motor': '福特汽车',
        'Johnson & Johnson': '强生公司',
        'Pfizer': '辉瑞公司',
        'Moderna': 'Moderna公司',
        'BioNTech': 'BioNTech公司',
        'Berkshire Hathaway': '伯克希尔哈撒韦',
        'JPMorgan Chase': '摩根大通',
        'Bank of America': '美国银行',
        'Wells Fargo': '富国银行',
        'Goldman Sachs': '高盛',
        'Morgan Stanley': '摩根士丹利',
        'BlackRock': '贝莱德',
        'Vanguard': '先锋集团',
        'Coca-Cola': '可口可乐',
        'PepsiCo': '百事公司',
        'Walmart': '沃尔玛',
        'Costco': '好市多',
        'Home Depot': '家得宝',
        'UPS': 'UPS公司',
        'FedEx': '联邦快递',
        'Disney': '迪士尼',
        'Comcast': '康卡斯特',
        'AT&T': 'AT&T公司',
        'Verizon': '威瑞森',
        'Exxon Mobil': '埃克森美孚',
        'Chevron': '雪佛龙',
        'ConocoPhillips': '康菲石油',
        
        # 股票代码
        'AAPL': '苹果(AAPL)',
        'TSLA': '特斯拉(TSLA)',
        'MSFT': '微软(MSFT)',
        'AMZN': '亚马逊(AMZN)',
        'GOOGL': '谷歌(GOOGL)',
        'GOOG': '谷歌(GOOG)',
        'META': 'Meta(META)',
        'NVDA': '英伟达(NVDA)',
        'NFLX': '奈飞(NFLX)',
        'PYPL': 'PayPal(PYPL)',
        'ADBE': 'Adobe(ADBE)',
        'CRM': 'Salesforce(CRM)',
        'ORCL': '甲骨文(ORCL)',
        'INTC': '英特尔(INTC)',
        'AMD': 'AMD(AMD)',
        'QCOM': '高通(QCOM)',
        'AVGO': '博通(AVGO)',
        'TSM': '台积电(TSM)',
        'JNJ': '强生(JNJ)',
        'PFE': '辉瑞(PFE)',
        'MRNA': 'Moderna(MRNA)',
        'BNTX': 'BioNTech(BNTX)',
        'BRK.A': '伯克希尔A(BRK.A)',
        'BRK.B': '伯克希尔B(BRK.B)',
        'JPM': '摩根大通(JPM)',
        'BAC': '美国银行(BAC)',
        'WFC': '富国银行(WFC)',
        'GS': '高盛(GS)',
        'MS': '摩根士丹利(MS)',
        'BLK': '贝莱德(BLK)',
        'KO': '可口可乐(KO)',
        'PEP': '百事(PEP)',
        'WMT': '沃尔玛(WMT)',
        'COST': '好市多(COST)',
        'HD': '家得宝(HD)',
        'UPS': 'UPS(UPS)',
        'FDX': '联邦快递(FDX)',
        'DIS': '迪士尼(DIS)',
        'CMCSA': '康卡斯特(CMCSA)',
        'T': 'AT&T(T)',
        'VZ': '威瑞森(VZ)',
        'XOM': '埃克森美孚(XOM)',
        'CVX': '雪佛龙(CVX)',
        'COP': '康菲石油(COP)',
        
        # 行业术语
        'artificial intelligence': '人工智能',
        'machine learning': '机器学习',
        'deep learning': '深度学习',
        'neural network': '神经网络',
        'big data': '大数据',
        'data analytics': '数据分析',
        'cloud computing': '云计算',
        'edge computing': '边缘计算',
        'quantum computing': '量子计算',
        'blockchain': '区块链',
        'cryptocurrency': '加密货币',
        'bitcoin': '比特币',
        'ethereum': '以太坊',
        'fintech': '金融科技',
        'digital transformation': '数字化转型',
        'automation': '自动化',
        'robotics': '机器人技术',
        'internet of things': '物联网',
        'iot': '物联网',
        '5g technology': '5G技术',
        '5g': '5G',
        'semiconductor': '半导体',
        'microchip': '微芯片',
        'processor': '处理器',
        'graphics card': '显卡',
        'memory chip': '内存芯片',
        'electric vehicle': '电动汽车',
        'autonomous driving': '自动驾驶',
        'self-driving car': '自动驾驶汽车',
        'battery technology': '电池技术',
        'lithium battery': '锂电池',
        'renewable energy': '可再生能源',
        'solar energy': '太阳能',
        'wind energy': '风能',
        'clean energy': '清洁能源',
        'energy storage': '储能',
        'smart grid': '智能电网',
        'biotechnology': '生物技术',
        'gene therapy': '基因治疗',
        'immunotherapy': '免疫疗法',
        'precision medicine': '精准医疗',
        'telemedicine': '远程医疗',
        'digital health': '数字健康',
        'medical device': '医疗设备',
        'pharmaceutical': '制药',
        'drug development': '药物开发',
        'clinical trial': '临床试验',
        'fda approval': 'FDA批准',
        'patent': '专利',
        'intellectual property': '知识产权',
        'research and development': '研发',
        'r&d': '研发',
        'innovation': '创新',
        'disruptive technology': '颠覆性技术',
        'startup': '初创公司',
        'unicorn': '独角兽企业',
        'venture capital': '风险投资',
        'private equity': '私募股权',
        'initial coin offering': '首次代币发行',
        'ico': '首次代币发行',
        'non-fungible token': '非同质化代币',
        'nft': 'NFT',
        'metaverse': '元宇宙',
        'virtual reality': '虚拟现实',
        'vr': 'VR',
        'augmented reality': '增强现实',
        'ar': 'AR',
        'mixed reality': '混合现实',
        'mr': 'MR',
        'gaming': '游戏',
        'esports': '电子竞技',
        'streaming service': '流媒体服务',
        'content creation': '内容创作',
        'social media': '社交媒体',
        'digital marketing': '数字营销',
        'e-commerce': '电子商务',
        'online retail': '在线零售',
        'marketplace': '市场平台',
        'supply chain': '供应链',
        'logistics': '物流',
        'fulfillment': '配送',
        'last mile delivery': '最后一公里配送',
        'drone delivery': '无人机配送',
        'warehouse automation': '仓储自动化',
        'inventory management': '库存管理',
        'customer experience': '客户体验',
        'user interface': '用户界面',
        'user experience': '用户体验',
        'ui': '用户界面',
        'ux': '用户体验',
        'software as a service': '软件即服务',
        'saas': 'SaaS',
        'platform as a service': '平台即服务',
        'paas': 'PaaS',
        'infrastructure as a service': '基础设施即服务',
        'iaas': 'IaaS',
        'api': '应用程序接口',
        'microservices': '微服务',
        'devops': 'DevOps',
        'agile development': '敏捷开发',
        'continuous integration': '持续集成',
        'continuous deployment': '持续部署',
        'cybersecurity': '网络安全',
        'data privacy': '数据隐私',
        'gdpr': 'GDPR',
        'compliance': '合规',
        'risk management': '风险管理',
        'corporate governance': '公司治理',
        'environmental social governance': '环境社会治理',
        'esg': 'ESG',
        'sustainability': '可持续性',
        'carbon footprint': '碳足迹',
        'carbon neutral': '碳中和',
        'net zero': '净零排放',
        'climate change': '气候变化',
        'green technology': '绿色技术',
        'circular economy': '循环经济',
        
        # 基础词汇
        'technology': '科技',
        'artificial intelligence': '人工智能',
        'AI': '人工智能',
        'revenue': '营收',
        'profit': '利润',
        'loss': '亏损',
        'dividend': '分红',
        'investment': '投资',
        'investor': '投资者',
        'shareholder': '股东',
        'CEO': '首席执行官',
        'CFO': '首席财务官',
        'CTO': '首席技术官',
        'COO': '首席运营官',
        'chairman': '董事长',
        'board of directors': '董事会',
        'executive': '高管',
        'management': '管理层',
        'employee': '员工',
        'workforce': '员工队伍',
        'layoff': '裁员',
        'hiring': '招聘',
        'talent acquisition': '人才招募',
        'human resources': '人力资源',
        'hr': '人力资源',
        'compensation': '薪酬',
        'salary': '薪水',
        'bonus': '奖金',
        'stock option': '股票期权',
        'equity': '股权',
        'vesting': '行权',
        'performance': '表现',
        'kpi': '关键绩效指标',
        'metric': '指标',
        'benchmark': '基准',
        'target': '目标',
        'forecast': '预测',
        'outlook': '展望',
        'guidance': '指导',
        'projection': '预期',
        'estimate': '估计',
        'consensus': '一致预期',
        'analyst': '分析师',
        'research': '研究',
        'rating': '评级',
        'recommendation': '建议',
        'upgrade': '上调评级',
        'downgrade': '下调评级',
        'buy': '买入',
        'sell': '卖出',
        'hold': '持有',
        'outperform': '跑赢大盘',
        'underperform': '跑输大盘',
        'neutral': '中性',
        'strong buy': '强烈买入',
        'strong sell': '强烈卖出',
        
        # 数值表达
        'billion': '十亿',
        'million': '百万',
        'trillion': '万亿',
        'thousand': '千',
        'percent': '百分比',
        'percentage': '百分比',
        'basis point': '基点',
        'bps': '基点',
        'year-over-year': '同比',
        'yoy': '同比',
        'quarter-over-quarter': '环比',
        'qoq': '环比',
        'month-over-month': '月环比',
        'mom': '月环比',
        'sequential': '环比',
        'annualized': '年化',
        'compound annual growth rate': '复合年增长率',
        'cagr': '复合年增长率',
        
        # 时间表达
        'this year': '今年',
        'last year': '去年',
        'next year': '明年',
        'this quarter': '本季度',
        'last quarter': '上季度',
        'next quarter': '下季度',
        'first quarter': '第一季度',
        'second quarter': '第二季度',
        'third quarter': '第三季度',
        'fourth quarter': '第四季度',
        'Q1': '第一季度',
        'Q2': '第二季度', 
        'Q3': '第三季度',
        'Q4': '第四季度',
        'fiscal year': '财年',
        'fy': '财年',
        'calendar year': '自然年',
        'cy': '自然年',
        'half year': '半年',
        'h1': '上半年',
        'h2': '下半年',
        'january': '一月',
        'february': '二月',
        'march': '三月',
        'april': '四月',
        'may': '五月',
        'june': '六月',
        'july': '七月',
        'august': '八月',
        'september': '九月',
        'october': '十月',
        'november': '十一月',
        'december': '十二月',
        'monday': '周一',
        'tuesday': '周二',
        'wednesday': '周三',
        'thursday': '周四',
        'friday': '周五',
        'saturday': '周六',
        'sunday': '周日',
        'today': '今天',
        'yesterday': '昨天',
        'tomorrow': '明天',
        'this week': '本周',
        'last week': '上周',
        'next week': '下周',
        'this month': '本月',
        'last month': '上月',
        'next month': '下月',
        'morning': '上午',
        'afternoon': '下午',
        'evening': '晚上',
        'night': '夜间',
        'dawn': '黎明',
        'dusk': '黄昏',
        
        # 市场动作
        'announced': '宣布',
        'reported': '报告',
        'released': '发布',
        'launched': '推出',
        'introduced': '推出',
        'unveiled': '公布',
        'revealed': '透露',
        'disclosed': '披露',
        'published': '发表',
        'issued': '发行',
        'filed': '提交',
        'submitted': '提交',
        'approved': '批准',
        'rejected': '拒绝',
        'denied': '否认',
        'confirmed': '确认',
        'verified': '验证',
        'validated': '验证',
        'signed': '签署',
        'agreed': '同意',
        'disagreed': '不同意',
        'negotiated': '谈判',
        'acquired': '收购',
        'merged': '合并',
        'divested': '剥离',
        'spun off': '分拆',
        'sold': '出售',
        'bought': '购买',
        'purchased': '采购',
        'invested': '投资',
        'funded': '资助',
        'financed': '融资',
        'raised': '筹集',
        'borrowed': '借款',
        'lent': '放贷',
        'defaulted': '违约',
        'restructured': '重组',
        'refinanced': '再融资',
        'liquidated': '清算',
        'bankrupt': '破产',
        'insolvent': '资不抵债',
        'delisted': '退市',
        'suspended': '暂停',
        'halted': '停牌',
        'resumed': '恢复',
        'expanded': '扩张',
        'contracted': '收缩',
        'grew': '增长',
        'declined': '下降',
        'increased': '增加',
        'decreased': '减少',
        'rose': '上升',
        'fell': '下跌',
        'jumped': '跳涨',
        'plunged': '暴跌',
        'soared': '飙升',
        'crashed': '崩盘',
        'surged': '激增',
        'tumbled': '大跌',
        'rallied': '反弹',
        'recovered': '恢复',
        'rebounded': '反弹',
        'corrected': '调整',
        'stabilized': '稳定',
        'fluctuated': '波动',
        'volatility': '波动性',
        'volatile': '波动的',
        'stable': '稳定的',
        'steady': '稳定的',
        'consistent': '一致的',
        'variable': '可变的',
        'unpredictable': '不可预测的',
        'cyclical': '周期性的',
        'seasonal': '季节性的',
        'trending': '趋势',
        'momentum': '动量',
        'acceleration': '加速',
        'deceleration': '减速',
        'peak': '峰值',
        'trough': '低谷',
        'bottom': '底部',
        'top': '顶部',
        'high': '高点',
        'low': '低点',
        'resistance': '阻力',
        'support': '支撑',
        'breakout': '突破',
        'breakdown': '跌破',
        'reversal': '反转',
        'continuation': '延续',
        'pattern': '模式',
        'trend': '趋势',
        'uptrend': '上升趋势',
        'downtrend': '下降趋势',
        'sideways': '横盘',
        'consolidation': '整理',
        'accumulation': '积累',
        'distribution': '分配',
        'oversold': '超卖',
        'overbought': '超买',
        'undervalued': '被低估',
        'overvalued': '被高估',
        'fair value': '公允价值',
        'intrinsic value': '内在价值',
        'fundamental analysis': '基本面分析',
        'technical analysis': '技术分析',
        'quantitative analysis': '量化分析',
        'due diligence': '尽职调查',
        'risk assessment': '风险评估',
        'stress test': '压力测试',
        'scenario analysis': '情景分析',
        'sensitivity analysis': '敏感性分析',
        'monte carlo': '蒙特卡洛',
        'backtesting': '回测',
        'optimization': '优化',
        'correlation': '相关性',
        'diversification': '多元化',
        'hedging': '对冲',
        'arbitrage': '套利',
        'speculation': '投机',
        'leverage': '杠杆',
        'margin': '保证金',
        'collateral': '抵押品',
        'liquidity': '流动性',
        'solvency': '偿付能力',
        'creditworthiness': '信用度',
        'default risk': '违约风险',
        'market risk': '市场风险',
        'credit risk': '信用风险',
        'operational risk': '操作风险',
        'systemic risk': '系统性风险',
        'idiosyncratic risk': '特异性风险',
        'regulatory risk': '监管风险',
        'geopolitical risk': '地缘政治风险',
        'inflation risk': '通胀风险',
        'interest rate risk': '利率风险',
        'currency risk': '汇率风险',
        'commodity risk': '商品风险',
        'event risk': '事件风险',
        'tail risk': '尾部风险',
        'black swan': '黑天鹅',
        'force majeure': '不可抗力',
        'act of god': '天灾',
        'natural disaster': '自然灾害',
        'pandemic': '大流行病',
        'epidemic': '流行病',
        'outbreak': '爆发',
        'quarantine': '隔离',
        'lockdown': '封锁',
        'restriction': '限制',
        'sanction': '制裁',
        'embargo': '禁运',
        'tariff': '关税',
        'trade war': '贸易战',
        'trade deal': '贸易协议',
        'free trade': '自由贸易',
        'protectionism': '保护主义',
        'globalization': '全球化',
        'supply chain disruption': '供应链中断',
        'shortage': '短缺',
        'surplus': '过剩',
        'inventory': '库存',
        'production': '生产',
        'manufacturing': '制造',
        'capacity': '产能',
        'utilization': '利用率',
        'efficiency': '效率',
        'productivity': '生产力',
        'quality': '质量',
        'standard': '标准',
        'certification': '认证',
        'compliance': '合规',
        'audit': '审计',
        'inspection': '检查',
        'regulation': '监管',
        'law': '法律',
        'legislation': '立法',
        'policy': '政策',
        'reform': '改革',
        'initiative': '倡议',
        'program': '项目',
        'project': '项目',
        'plan': '计划',
        'strategy': '策略',
        'objective': '目标',
        'goal': '目标',
        'mission': '使命',
        'vision': '愿景',
        'value': '价值',
        'principle': '原则',
        'ethics': '道德',
        'integrity': '诚信',
        'transparency': '透明度',
        'accountability': '问责制',
        'responsibility': '责任',
        'commitment': '承诺',
        'obligation': '义务',
        'duty': '职责',
        'role': '角色',
        'function': '功能',
        'purpose': '目的',
        'benefit': '利益',
        'advantage': '优势',
        'disadvantage': '劣势',
        'strength': '优势',
        'weakness': '弱点',
        'opportunity': '机会',
        'threat': '威胁',
        'challenge': '挑战',
        'problem': '问题',
        'solution': '解决方案',
        'alternative': '替代方案',
        'option': '选择',
        'choice': '选择',
        'decision': '决定',
        'conclusion': '结论',
        'result': '结果',
        'outcome': '结果',
        'consequence': '后果',
        'impact': '影响',
        'effect': '效果',
        'influence': '影响',
        'factor': '因素',
        'element': '要素',
        'component': '组成部分',
        'aspect': '方面',
        'dimension': '维度',
        'perspective': '观点',
        'viewpoint': '观点',
        'opinion': '意见',
        'belief': '信念',
        'assumption': '假设',
        'hypothesis': '假设',
        'theory': '理论',
        'concept': '概念',
        'idea': '想法',
        'notion': '概念',
        'thought': '想法',
        'consideration': '考虑',
        'factor': '因素',
        'variable': '变量',
        'parameter': '参数',
        'indicator': '指标',
        'measure': '衡量',
        'gauge': '衡量',
        'scale': '规模',
        'size': '大小',
        'magnitude': '规模',
        'extent': '程度',
        'degree': '程度',
        'level': '水平',
        'grade': '等级',
        'rank': '排名',
        'position': '位置',
        'status': '状态',
        'condition': '条件',
        'situation': '情况',
        'circumstance': '情况',
        'context': '背景',
        'environment': '环境',
        'setting': '环境',
        'atmosphere': '氛围',
        'climate': '气候',
        'culture': '文化',
        'tradition': '传统',
        'custom': '习俗',
        'practice': '实践',
        'procedure': '程序',
        'process': '过程',
        'method': '方法',
        'approach': '方法',
        'technique': '技术',
        'skill': '技能',
        'ability': '能力',
        'capability': '能力',
        'capacity': '能力',
        'potential': '潜力',
        'talent': '天赋',
        'expertise': '专业知识',
        'experience': '经验',
        'knowledge': '知识',
        'information': '信息',
        'data': '数据',
        'statistics': '统计',
        'figure': '数字',
        'number': '数量',
        'amount': '金额',
        'quantity': '数量',
        'volume': '数量',
        'total': '总计',
        'sum': '总和',
        'aggregate': '总计',
        'average': '平均',
        'mean': '平均值',
        'median': '中位数',
        'mode': '众数',
        'range': '范围',
        'variance': '方差',
        'deviation': '偏差',
        'correlation': '相关性',
        'relationship': '关系',
        'connection': '联系',
        'link': '链接',
        'association': '关联',
        'interaction': '互动',
        'communication': '沟通',
        'dialogue': '对话',
        'discussion': '讨论',
        'conversation': '对话',
        'meeting': '会议',
        'conference': '会议',
        'summit': '峰会',
        'forum': '论坛',
        'panel': '小组',
        'committee': '委员会',
        'board': '董事会',
        'council': '理事会',
        'assembly': '大会',
        'congress': '国会',
        'parliament': '议会',
        'government': '政府',
        'administration': '政府',
        'authority': '当局',
        'agency': '机构',
        'department': '部门',
        'ministry': '部',
        'bureau': '局',
        'office': '办公室',
        'division': '部门',
        'unit': '单位',
        'team': '团队',
        'group': '小组',
        'organization': '组织',
        'institution': '机构',
        'establishment': '机构',
        'entity': '实体',
        'body': '机构',
        'association': '协会',
        'society': '协会',
        'union': '联盟',
        'alliance': '联盟',
        'partnership': '合作',
        'collaboration': '合作',
        'cooperation': '合作',
        'coordination': '协调',
        'integration': '整合',
        'consolidation': '整合',
        'merger': '合并',
        'acquisition': '收购',
        'takeover': '收购',
        'buyout': '收购',
        'deal': '交易',
        'transaction': '交易',
        'agreement': '协议',
        'contract': '合同',
        'treaty': '条约',
        'accord': '协议',
        'pact': '协定',
        'understanding': '谅解',
        'arrangement': '安排',
        'settlement': '和解',
        'resolution': '解决',
        'compromise': '妥协',
        'negotiation': '谈判',
        'mediation': '调解',
        'arbitration': '仲裁',
        'litigation': '诉讼',
        'lawsuit': '诉讼',
        'trial': '审判',
        'hearing': '听证会',
        'verdict': '判决',
        'judgment': '判决',
        'ruling': '裁决',
        'decision': '决定',
        'order': '命令',
        'directive': '指令',
        'instruction': '指示',
        'guidance': '指导',
        'advice': '建议',
        'recommendation': '建议',
        'suggestion': '建议',
        'proposal': '提议',
        'offer': '提议',
        'bid': '投标',
        'tender': '招标',
        'auction': '拍卖',
        'sale': '销售',
        'purchase': '购买',
        'order': '订单',
        'delivery': '交付',
        'shipment': '装运',
        'transport': '运输',
        'logistics': '物流',
        'distribution': '分销',
        'retail': '零售',
        'wholesale': '批发',
        'channel': '渠道',
        'network': '网络',
        'platform': '平台',
        'marketplace': '市场',
        'exchange': '交易所',
        'trading': '交易',
        'market': '市场',
        'sector': '行业',
        'industry': '行业',
        'segment': '细分市场',
        'niche': '细分市场',
        'category': '类别',
        'class': '类别',
        'type': '类型',
        'kind': '种类',
        'variety': '品种',
        'model': '模型',
        'version': '版本',
        'edition': '版本',
        'generation': '代',
        'series': '系列',
        'line': '产品线',
        'range': '系列',
        'portfolio': '组合',
        'mix': '组合',
        'combination': '组合',
        'blend': '混合',
        'integration': '整合',
        'synthesis': '综合',
        'fusion': '融合',
        'merger': '合并',
        'convergence': '汇聚',
        'alignment': '对齐',
        'synchronization': '同步',
        'coordination': '协调',
        'harmony': '和谐',
        'balance': '平衡',
        'equilibrium': '平衡',
        'stability': '稳定性',
        'consistency': '一致性',
        'reliability': '可靠性',
        'durability': '耐用性',
        'quality': '质量',
        'performance': '性能',
        'efficiency': '效率',
        'effectiveness': '有效性',
        'productivity': '生产力',
        'profitability': '盈利能力',
        'viability': '可行性',
        'feasibility': '可行性',
        'sustainability': '可持续性',
        'scalability': '可扩展性',
        'flexibility': '灵活性',
        'adaptability': '适应性',
        'agility': '敏捷性',
        'responsiveness': '响应性',
        'innovation': '创新',
        'creativity': '创造力',
        'originality': '原创性',
        'uniqueness': '独特性',
        'distinction': '区别',
        'differentiation': '差异化',
        'competitive advantage': '竞争优势',
        'market position': '市场地位',
        'brand': '品牌',
        'reputation': '声誉',
        'image': '形象',
        'perception': '认知',
        'awareness': '认知度',
        'recognition': '认可',
        'acceptance': '接受',
        'approval': '批准',
        'endorsement': '支持',
        'support': '支持',
        'backing': '支持',
        'sponsorship': '赞助',
        'funding': '资金',
        'financing': '融资',
        'investment': '投资',
        'capital': '资本',
        'asset': '资产',
        'liability': '负债',
        'equity': '权益',
        'ownership': '所有权',
        'stake': '股份',
        'share': '股份',
        'stock': '股票',
        'security': '证券',
        'bond': '债券',
        'note': '票据',
        'bill': '票据',
        'certificate': '证书',
        'warrant': '权证',
        'option': '期权',
        'future': '期货',
        'derivative': '衍生品',
        'commodity': '商品',
        'currency': '货币',
        'exchange rate': '汇率',
        'interest rate': '利率',
        'yield': '收益率',
        'return': '回报',
        'gain': '收益',
        'loss': '损失',
        'profit': '利润',
        'income': '收入',
        'revenue': '营收',
        'sales': '销售',
        'turnover': '营业额',
        'earnings': '收益',
        'ebitda': 'EBITDA',
        'cash flow': '现金流',
        'margin': '利润率',
        'ratio': '比率',
        'multiple': '倍数',
        'valuation': '估值',
        'price': '价格',
        'cost': '成本',
        'expense': '费用',
        'budget': '预算',
        'allocation': '分配',
        'distribution': '分配',
        'dividend': '股息',
        'payout': '支付',
        'payment': '付款',
        'settlement': '结算',
        'clearance': '清算',
        'processing': '处理',
        'execution': '执行',
        'implementation': '实施',
        'deployment': '部署',
        'rollout': '推出',
        'launch': '启动',
        'introduction': '引入',
        'debut': '首次亮相',
        'premiere': '首映',
        'opening': '开幕',
        'start': '开始',
        'commencement': '开始',
        'initiation': '发起',
        'establishment': '建立',
        'foundation': '基础',
        'creation': '创建',
        'development': '发展',
        'progress': '进展',
        'advancement': '进步',
        'improvement': '改善',
        'enhancement': '增强',
        'upgrade': '升级',
        'update': '更新',
        'revision': '修订',
        'modification': '修改',
        'adjustment': '调整',
        'change': '变化',
        'transformation': '转变',
        'evolution': '演变',
        'transition': '过渡',
        'shift': '转变',
        'move': '移动',
        'migration': '迁移',
        'relocation': '重新定位',
        'expansion': '扩张',
        'growth': '增长',
        'extension': '扩展',
        'enlargement': '扩大',
        'increase': '增加',
        'rise': '上升',
        'climb': '攀升',
        'surge': '激增',
        'spike': '激增',
        'jump': '跳涨',
        'leap': '跳跃',
        'bound': '跳跃',
        'soar': '飙升',
        'rocket': '火箭般上升',
        'skyrocket': '飙升',
        'boom': '繁荣',
        'burst': '爆发',
        'explosion': '爆炸性增长',
        'breakthrough': '突破',
        'milestone': '里程碑',
        'achievement': '成就',
        'success': '成功',
        'victory': '胜利',
        'triumph': '胜利',
        'win': '胜利',
        'accomplishment': '成就',
        'attainment': '达到',
        'realization': '实现',
        'fulfillment': '实现',
        'completion': '完成',
        'finish': '完成',
        'conclusion': '结论',
        'end': '结束',
        'termination': '终止',
        'closure': '关闭',
        'shutdown': '关闭',
        'cessation': '停止',
        'halt': '停止',
        'pause': '暂停',
        'break': '中断',
        'interruption': '中断',
        'disruption': '中断',
        'disturbance': '干扰',
        'interference': '干扰',
        'obstacle': '障碍',
        'barrier': '障碍',
        'hurdle': '障碍',
        'impediment': '阻碍',
        'hindrance': '阻碍',
        'constraint': '约束',
        'limitation': '限制',
        'restriction': '限制',
        'regulation': '监管',
        'control': '控制',
        'management': '管理',
        'administration': '管理',
        'governance': '治理',
        'oversight': '监督',
        'supervision': '监督',
        'monitoring': '监控',
        'tracking': '跟踪',
        'observation': '观察',
        'surveillance': '监视',
        'inspection': '检查',
        'examination': '检查',
        'review': '审查',
        'assessment': '评估',
        'evaluation': '评估',
        'analysis': '分析',
        'study': '研究',
        'investigation': '调查',
        'inquiry': '询问',
        'survey': '调查',
        'poll': '民调',
        'census': '人口普查',
        'count': '计数',
        'tally': '计数',
        'calculation': '计算',
        'computation': '计算',
        'estimation': '估算',
        'approximation': '近似',
        'projection': '预测',
        'forecast': '预测',
        'prediction': '预测',
        'anticipation': '预期',
        'expectation': '期望',
        'prospect': '前景',
        'outlook': '前景',
        'future': '未来',
        'tomorrow': '明天',
        'ahead': '前方',
        'forward': '向前',
        'onward': '向前',
        'upward': '向上',
        'downward': '向下',
        'backward': '向后',
        'reverse': '反向',
        'opposite': '相反',
        'contrary': '相反',
        'inverse': '逆向',
        'negative': '负面',
        'positive': '正面',
        'favorable': '有利',
        'unfavorable': '不利',
        'beneficial': '有益',
        'detrimental': '有害',
        'advantageous': '有利',
        'disadvantageous': '不利',
        'profitable': '盈利',
        'unprofitable': '不盈利',
        'successful': '成功',
        'unsuccessful': '不成功',
        'effective': '有效',
        'ineffective': '无效',
        'efficient': '高效',
        'inefficient': '低效',
        'productive': '生产性',
        'unproductive': '非生产性',
        'constructive': '建设性',
        'destructive': '破坏性',
        'creative': '创造性',
        'innovative': '创新',
        'traditional': '传统',
        'conventional': '传统',
        'standard': '标准',
        'normal': '正常',
        'regular': '常规',
        'routine': '例行',
        'ordinary': '普通',
        'common': '普通',
        'typical': '典型',
        'usual': '通常',
        'customary': '习惯',
        'habitual': '习惯性',
        'frequent': '频繁',
        'occasional': '偶尔',
        'rare': '罕见',
        'unusual': '不寻常',
        'exceptional': '特殊',
        'extraordinary': '非凡',
        'remarkable': '显著',
        'notable': '值得注意',
        'significant': '重要',
        'important': '重要',
        'major': '主要',
        'minor': '次要',
        'primary': '主要',
        'secondary': '次要',
        'principal': '主要',
        'main': '主要',
        'central': '中心',
        'core': '核心',
        'key': '关键',
        'critical': '关键',
        'crucial': '关键',
        'vital': '至关重要',
        'essential': '必要',
        'necessary': '必要',
        'required': '需要',
        'mandatory': '强制',
        'compulsory': '强制',
        'optional': '可选',
        'voluntary': '自愿',
        'free': '自由',
        'independent': '独立',
        'autonomous': '自主',
        'self-sufficient': '自给自足',
        'sustainable': '可持续',
        'renewable': '可再生',
        'recyclable': '可回收',
        'biodegradable': '可生物降解',
        'environmentally friendly': '环保',
        'eco-friendly': '环保',
        'green': '绿色',
        'clean': '清洁',
        'pure': '纯净',
        'natural': '天然',
        'organic': '有机',
        'synthetic': '合成',
        'artificial': '人工',
        'man-made': '人造',
        'manufactured': '制造',
        'produced': '生产',
        'created': '创造',
        'generated': '产生',
        'formed': '形成',
        'established': '建立',
        'founded': '创立',
        'launched': '启动',
        'started': '开始',
        'initiated': '发起',
        'commenced': '开始',
        'begun': '开始',
        'opened': '开放',
        'closed': '关闭',
        'finished': '完成',
        'completed': '完成',
        'concluded': '结束',
        'ended': '结束',
        'terminated': '终止',
        'ceased': '停止',
        'stopped': '停止',
        'paused': '暂停',
        'suspended': '暂停',
        'postponed': '推迟',
        'delayed': '延迟',
        'accelerated': '加速',
        'expedited': '加快',
        'rushed': '匆忙',
        'hurried': '匆忙',
        'immediate': '立即',
        'instant': '即时',
        'prompt': '迅速',
        'quick': '快速',
        'fast': '快速',
        'rapid': '快速',
        'swift': '迅速',
        'speedy': '快速',
        'hasty': '匆忙',
        'slow': '缓慢',
        'gradual': '逐渐',
        'steady': '稳定',
        'constant': '恒定',
        'continuous': '连续',
        'ongoing': '持续',
        'persistent': '持续',
        'lasting': '持久',
        'permanent': '永久',
        'temporary': '临时',
        'interim': '临时',
        'provisional': '临时',
        'preliminary': '初步',
        'initial': '初始',
        'first': '第一',
        'final': '最终',
        'last': '最后',
        'ultimate': '最终',
        'latest': '最新',
        'newest': '最新',
        'recent': '最近',
        'current': '当前',
        'present': '目前',
        'existing': '现有',
        'previous': '以前',
        'former': '以前',
        'past': '过去',
        'historical': '历史',
        'ancient': '古老',
        'old': '旧',
        'new': '新',
        'fresh': '新鲜',
        'modern': '现代',
        'contemporary': '当代',
        'up-to-date': '最新',
        'outdated': '过时',
        'obsolete': '过时',
        'deprecated': '弃用',
        'legacy': '传统',
        'vintage': '老式',
        'classic': '经典',
        'timeless': '永恒',
        'eternal': '永恒',
        'everlasting': '永恒',
        'infinite': '无限',
        'unlimited': '无限',
        'boundless': '无界',
        'endless': '无尽',
        'limitless': '无限',
        'maximum': '最大',
        'minimum': '最小',
        'optimal': '最优',
        'ideal': '理想',
        'perfect': '完美',
        'flawless': '无缺陷',
        'excellent': '优秀',
        'outstanding': '杰出',
        'superior': '优越',
        'inferior': '劣质',
        'poor': '差',
        'bad': '坏',
        'good': '好',
        'great': '伟大',
        'amazing': '惊人',
        'incredible': '不可思议',
        'fantastic': '神奇',
        'wonderful': '精彩',
        'brilliant': '辉煌',
        'spectacular': '壮观',
        'impressive': '令人印象深刻',
        'remarkable': '显著',
        'noteworthy': '值得注意',
        'memorable': '难忘',
        'unforgettable': '难忘',
        'historic': '历史性',
        'landmark': '里程碑',
        'groundbreaking': '开创性',
        'pioneering': '开拓性',
        'revolutionary': '革命性',
        'transformative': '变革性',
        'disruptive': '颠覆性',
        'game-changing': '改变游戏规则',
        'paradigm-shifting': '范式转变'
    }
    
    result = text
    for en, zh in financial_dict.items():
        pattern = r'\b' + re.escape(en) + r'\b'
        result = re.sub(pattern, zh, result, flags=re.IGNORECASE)
    
    return result,
        'import streamlit as st
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

def translate_with_google_alternative(text):
    """使用Google翻译的替代接口（快速版本）"""
    try:
        import requests
        
        # 缩短超时时间，提高速度
        url = "https://translate.google.cn/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': 'en',
            'tl': 'zh',
            'dt': 't',
            'q': text[:500]  # 限制长度
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=3)  # 3秒超时
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

def translate_with_youdao(text):
    """使用有道翻译免费接口"""
    try:
        import requests
        
        url = "https://fanyi.youdao.com/translate"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://fanyi.youdao.com/',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        
        data = {
            'i': text,
            'from': 'en',
            'to': 'zh-CHS',
            'smartresult': 'dict',
            'client': 'fanyideskweb',
            'salt': str(int(time.time() * 1000)),
            'sign': hashlib.md5(('fanyideskweb' + text + str(int(time.time() * 1000)) + 'Ygy_4c=r#e#4EX^NUGUc5').encode()).hexdigest(),
            'ts': str(int(time.time() * 1000)),
            'bv': hashlib.md5('5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'.encode()).hexdigest(),
            'doctype': 'json',
            'version': '2.1',
            'keyfrom': 'fanyi.web',
            'action': 'FY_BY_REALTlME'
        }
        
        response = requests.post(url, headers=headers, data=data, timeout=8)
        if response.status_code == 200:
            result = response.json()
            if 'translateResult' in result and result['translateResult']:
                return result['translateResult'][0][0]['tgt']
    except:
        pass
    return None

def basic_financial_translate(text):
    """基础财经术语翻译"""
    if not text:
        return text
    
    financial_dict = {
        # 完整句式
        'said in a statement': '在声明中表示',
        'according to': '据',
        'is expected to': '预计将',
        'announced today': '今日宣布',
        'reported earnings': '公布财报',
        'shares rose': '股价上涨',
        'shares fell': '股价下跌',
        'market cap': '市值',
        'revenue growth': '营收增长',
        'quarterly results': '季度业绩',
        
        # 公司名称
        'Apple Inc': '苹果公司',
        'Apple': '苹果公司',
        'Tesla Inc': '特斯拉公司', 
        'Tesla': '特斯拉',
        'Microsoft': '微软',
        'Amazon': '亚马逊',
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
        'artificial intelligence': '人工智能',
        'AI': '人工智能',
        'quarterly earnings': '季度财报',
        'earnings report': '财报',
        'revenue': '营收',
        'profit': '利润',
        'loss': '亏损',
        'dividend': '分红',
        'stock price': '股价',
        'market value': '市值',
        'stock market': '股市',
        'investment': '投资',
        'investor': '投资者',
        'shareholder': '股东',
        'CEO': '首席执行官',
        'CFO': '首席财务官',
        
        # 行业术语
        'technology': '科技',
        'semiconductor': '半导体',
        'electric vehicle': '电动汽车',
        'cloud computing': '云计算',
        'e-commerce': '电子商务',
        'streaming': '流媒体',
        
        # 数值表达
        'billion': '十亿',
        'million': '百万',
        'trillion': '万亿',
        'percent': '百分比',
        
        # 时间表达
        'this year': '今年',
        'last year': '去年',
        'this quarter': '本季度',
        'last quarter': '上季度',
        
        # 市场动作
        'announced': '宣布',
        'reported': '报告',
        'released': '发布',
        'launched': '推出',
        'acquired': '收购',
        
        # 其他常用词
        'growth': '增长',
        'decline': '下降',
        'increase': '增加',
        'performance': '表现',
        'results': '结果',
        'forecast': '预测',
        'outlook': '展望'
    }
    
    result = text
    for en, zh in financial_dict.items():
        pattern = r'\b' + re.escape(en) + r'\b'
        result = re.sub(pattern, zh, result, flags=re.IGNORECASE)
    
    return result

def smart_translate(text):
    """智能翻译：快速翻译策略"""
    if not text or len(text.strip()) < 3:
        return text
    
    # 首先使用快速的基础翻译
    translated = basic_financial_translate(text)
    
    # 如果基础翻译效果不好，尝试在线翻译（但有超时限制）
    if translated == text:  # 说明基础翻译没有效果
        try:
            # 只对较短的文本使用在线翻译
            if len(text) < 200:
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
        
        if fcf <= 0:
            return None, None
        
        # DCF参数
        growth_rate = 0.05
        discount_rate = 0.10
        terminal_growth = 0.02
        forecast_years = 5
        
        # 计算预测期现金流现值
        dcf_value = 0
        for i in range(1, forecast_years + 1):
            future_fcf = fcf * (1 + growth_rate) ** i
            pv = future_fcf / (1 + discount_rate) ** i
            dcf_value += pv
        
        # 计算终值
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
            
        return fair_value_per_share, {
            'growth_rate': growth_rate,
            'discount_rate': discount_rate,
            'terminal_growth': terminal_growth,
            'enterprise_value': enterprise_value
        }
    except Exception as e:
        return None, None

# 侧边栏
with st.sidebar:
    st.header("📊 分析参数设置")
    
    ticker = st.text_input("股票代码", "AAPL", help="输入股票代码，如：AAPL")
    analyze_button = st.button("🔍 开始分析", type="primary", use_container_width=True)
    
    with st.expander("📘 使用说明"):
        st.markdown("""
        ### 系统功能
        1. **股票分析**: 财务指标、技术分析、估值模型
        2. **新闻分析**: 中文新闻翻译与分析
        3. **止盈止损**: 智能策略建议
        
        ### 操作方法
        1. 输入股票代码（如AAPL、TSLA、MSFT）
        2. 点击"开始分析"
        3. 查看分析结果和新闻
        
        ### 注意事项
        - 新闻自动翻译为中文
        - 使用多个翻译源确保质量
        """)

# 主界面逻辑
if analyze_button and ticker:
    st.session_state.current_ticker = ticker
    st.session_state.show_analysis = True
    
    with st.spinner(f"正在获取 {ticker} 的数据..."):
        data = fetch_stock_data(ticker)
    
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
        col1, col2, col3 = st.columns([1, 2, 1])
        
        # 左栏：基本信息
        with col1:
            st.subheader("📌 公司基本信息")
            info = data['info']
            
            st.metric("公司名称", info.get('longName', ticker))
            st.metric("当前股价", f"${current_price:.2f}")
            st.metric("市值", f"${info.get('marketCap', 0)/1e9:.2f}B")
            st.metric("行业", info.get('industry', 'N/A'))
            st.metric("Beta", f"{info.get('beta', 0):.2f}")
        
        # 中栏：财务分析
        with col2:
            st.subheader("📈 财务分析")
            
            # Piotroski F-Score
            with st.expander("🔍 Piotroski F-Score 分析", expanded=True):
                f_score, reasons = calculate_piotroski_score(data)
                
                score_color = "green" if f_score >= 7 else "orange" if f_score >= 4 else "red"
                st.markdown(f"### 得分: <span style='color:{score_color}; font-size:24px'>{f_score}/9</span>", unsafe_allow_html=True)
                
                for reason in reasons:
                    st.write(reason)
            
            # DCF估值分析
            with st.expander("💎 DCF估值分析", expanded=True):
                dcf_value, dcf_params = calculate_dcf_valuation(data)
                
                if dcf_value and current_price > 0:
                    col_x, col_y = st.columns(2)
                    with col_x:
                        st.metric("合理价值", f"${dcf_value:.2f}")
                        st.metric("当前价格", f"${current_price:.2f}")
                    with col_y:
                        margin = ((dcf_value - current_price) / dcf_value * 100) if dcf_value > 0 else 0
                        st.metric("安全边际", f"{margin:.2f}%")
                        
                        if margin > 20:
                            st.success("📈 明显低估")
                        elif margin > 0:
                            st.info("📊 合理估值")
                        else:
                            st.warning("📉 可能高估")
                else:
                    st.info("DCF估值数据不足")
        
        # 右栏：技术分析
        with col3:
            st.subheader("📉 技术分析")
            
            # 计算技术指标
            hist_data = data['hist_data'].copy()
            hist_data = calculate_technical_indicators(hist_data)
            
            if len(hist_data) > 0:
                latest = hist_data.iloc[-1]
                
                # RSI状态
                if 'RSI' in hist_data.columns:
                    rsi_value = latest['RSI']
                    if rsi_value > 70:
                        st.error(f"⚠️ RSI: {rsi_value:.1f} (超买)")
                    elif rsi_value < 30:
                        st.success(f"💡 RSI: {rsi_value:.1f} (超卖)")
                    else:
                        st.info(f"📊 RSI: {rsi_value:.1f} (正常)")
                
                # 均线状态
                if 'MA10' in hist_data.columns and 'MA60' in hist_data.columns:
                    if latest['MA10'] > latest['MA60']:
                        st.info("📈 均线：多头排列")
                    else:
                        st.warning("📉 均线：空头排列")
            
            # 简化的止盈止损计算
            st.markdown("### 💰 止盈止损建议")
            
            default_buy_price = current_price * 0.95
            buy_price = st.number_input(
                "假设买入价格 ($)", 
                min_value=0.01, 
                value=default_buy_price, 
                step=0.01
            )
            
            # 固定比例法
            stop_loss = buy_price * 0.90  # 10%止损
            take_profit = buy_price * 1.15  # 15%止盈
            
            col_sl, col_tp = st.columns(2)
            with col_sl:
                st.metric("🛡️ 建议止损", f"${stop_loss:.2f}")
            with col_tp:
                st.metric("🎯 建议止盈", f"${take_profit:.2f}")
            
            # 当前状态
            if current_price <= stop_loss:
                st.error("⚠️ 已触及止损线！")
            elif current_price >= take_profit:
                st.success("🎯 已达到止盈目标！")
            else:
                st.info("📊 持仓正常")
    
    with main_tab2:
        st.subheader("📰 最新时事分析")
        st.info("💡 自动翻译最新财经新闻为中文")
        
        # 获取新闻数据
        with st.spinner("正在获取和翻译新闻..."):
            news_data = fetch_financial_news(ticker)
        
        if len(news_data) == 0:
            st.warning("⚠️ 暂时无法获取新闻数据，请稍后重试")
            st.info("💡 建议直接访问财经网站获取最新市场动态")
        else:
            # 新闻统计
            total_news = len(news_data)
            company_news = len([n for n in news_data if n.get('category') == 'company_specific'])
            market_news = len([n for n in news_data if n.get('category') == 'market_wide'])
            
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("📰 翻译新闻", total_news)
            with col_stat2:
                st.metric("🏢 公司相关", company_news)
            with col_stat3:
                st.metric("🌍 市场影响", market_news)
            
            st.markdown("---")
            
            # 分页设置
            news_per_page = 5
            total_pages = (len(news_data) + news_per_page - 1) // news_per_page
            
            # 初始化当前页
            if 'current_news_page' not in st.session_state:
                st.session_state.current_news_page = 1
            
            # 确保页数在有效范围内
            if st.session_state.current_news_page > total_pages:
                st.session_state.current_news_page = total_pages
            if st.session_state.current_news_page < 1:
                st.session_state.current_news_page = 1
            
            current_page = st.session_state.current_news_page
            
            # 计算当前页新闻
            start_idx = (current_page - 1) * news_per_page
            end_idx = min(start_idx + news_per_page, len(news_data))
            current_news = news_data[start_idx:end_idx]
            
            st.markdown(f"### 📄 第 {current_page} 页 (显示第 {start_idx + 1}-{end_idx} 条新闻)")
            
            # 显示新闻
            for i, news in enumerate(current_news):
                category = news.get('category', 'general')
                
                # 设置边框颜色
                if category == 'company_specific':
                    border_color = "#4CAF50"  # 绿色
                elif category == 'market_wide':
                    border_color = "#2196F3"  # 蓝色
                else:
                    border_color = "#FF9800"  # 橙色
                
                # 分类标签
                category_labels = {
                    'company_specific': f'🏢 {ticker}相关',
                    'market_wide': '🌍 市场影响',
                    'industry_specific': '🏭 行业动态'
                }
                category_label = category_labels.get(category, '📰 一般新闻')
                
                news_number = start_idx + i + 1
                is_real = news.get('is_real', True)
                real_label = "✅ 真实新闻" if is_real else "📝 系统信息"
                
                st.markdown(f"""
                <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 15px; margin: 10px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="background-color: {border_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">
                            {news_number}. {category_label} | {real_label}
                        </span>
                        <span style="font-size: 11px; color: #999;">📰 {news.get('source', '')}</span>
                    </div>
                    <p style="color: #666; margin: 10px 0;">{news.get('summary', '')}</p>
                    <p style="font-size: 12px; color: #999;">
                        📅 {news.get('published', datetime.now()).strftime('%Y-%m-%d %H:%M')} | 
                        🏷️ 关键词: {', '.join(news.get('keywords', []))}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # 新闻标题按钮
                news_url = news.get('url', '')
                news_title = news.get('title', '无标题')
                
                if news_url and news_url.startswith('http'):
                    st.markdown(f'<a href="{news_url}" target="_blank"><button style="background: linear-gradient(45deg, {border_color}, {border_color}dd); color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: bold; width: 100%; margin: 10px 0;">🔗 {news_title}</button></a>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<button style="background: linear-gradient(45deg, #999, #777); color: white; border: none; padding: 12px 20px; border-radius: 8px; font-size: 14px; font-weight: bold; width: 100%; margin: 10px 0; opacity: 0.7; cursor: not-allowed;" disabled>📄 {news_title}</button>', unsafe_allow_html=True)
                
                # 市场影响分析
                col_sentiment, col_impact = st.columns([1, 2])
                
                with col_sentiment:
                    sentiment = news.get('sentiment', '中性')
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
            
            # 页面底部的翻页按钮
            if total_pages > 1:
                st.markdown("### 📄 页面导航")
                
                nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1, 1, 1, 1, 1])
                
                with nav_col1:
                    if current_page > 1:
                        if st.button("⬅️ 上一页", key="prev_page_btn", use_container_width=True):
                            st.session_state.current_news_page = current_page - 1
                            st.rerun()
                    else:
                        st.button("⬅️ 上一页", key="prev_page_btn_disabled", disabled=True, use_container_width=True)
                
                with nav_col2:
                    if st.button("📖 第1页", key="page_1_btn", use_container_width=True, 
                               type="primary" if current_page == 1 else "secondary"):
                        st.session_state.current_news_page = 1
                        st.rerun()
                
                with nav_col3:
                    st.markdown(f"<div style='text-align: center; padding: 10px; font-weight: bold; color: #666;'>第 {current_page} / {total_pages} 页</div>", unsafe_allow_html=True)
                
                with nav_col4:
                    if total_pages >= 2:
                        if st.button("📄 第2页", key="page_2_btn", use_container_width=True,
                                   type="primary" if current_page == 2 else "secondary"):
                            st.session_state.current_news_page = 2
                            st.rerun()
                    else:
                        st.button("📄 第2页", key="page_2_btn_disabled", disabled=True, use_container_width=True)
                
                with nav_col5:
                    if current_page < total_pages:
                        if st.button("下一页 ➡️", key="next_page_btn", use_container_width=True):
                            st.session_state.current_news_page = current_page + 1
                            st.rerun()
                    else:
                        st.button("下一页 ➡️", key="next_page_btn_disabled", disabled=True, use_container_width=True)
                
                st.markdown("---")
                progress_text = f"🔖 当前浏览: 第{current_page}页，共{total_pages}页 | 显示新闻 {start_idx + 1}-{end_idx} / {len(news_data)}"
                st.info(progress_text)
            
            # 整体市场情绪分析
            st.subheader("📊 整体市场情绪分析")
            
            bullish_count = sum(1 for news in news_data if news.get('sentiment') == '利好')
            bearish_count = sum(1 for news in news_data if news.get('sentiment') == '利空')
            neutral_count = sum(1 for news in news_data if news.get('sentiment') == '中性')
            
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            with col_stats1:
                st.metric("📈 利好消息", bullish_count)
            with col_stats2:
                st.metric("📉 利空消息", bearish_count)
            with col_stats3:
                st.metric("📊 中性消息", neutral_count)
            
            # 整体建议
            if bullish_count > bearish_count:
                st.success("🟢 **整体市场情绪**: 偏向乐观")
                st.info("💡 **投资建议**: 市场利好因素较多，可适当关注优质标的投资机会。")
            elif bearish_count > bullish_count:
                st.error("🔴 **整体市场情绪**: 偏向谨慎")
                st.warning("⚠️ **投资建议**: 市场风险因素增加，建议降低仓位，关注防御性资产。")
            else:
                st.info("🟡 **整体市场情绪**: 相对平衡")
                st.info("📊 **投资建议**: 市场情绪相对平衡，建议保持现有投资策略。")
            
            # 关键词分析
            st.subheader("🔍 热点关键词")
            all_keywords = []
            for news in news_data:
                all_keywords.extend(news.get('keywords', []))
            
            keyword_count = {}
            for keyword in all_keywords:
                keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
            
            sorted_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)[:8]
            
            cols = st.columns(4)
            for i, (keyword, count) in enumerate(sorted_keywords):
                with cols[i % 4]:
                    st.metric(f"🏷️ {keyword}", f"{count}次")
            
            # 投资建议
            st.subheader("💡 基于时事的投资提醒")
            
            suggestions = []
            for keyword, count in sorted_keywords:
                if keyword in ["利率", "降息"]:
                    suggestions.append("🟢 关注利率敏感行业：房地产、银行、基建等")
                elif keyword in ["科技", "AI"]:
                    suggestions.append("🔵 关注科技成长股：人工智能、芯片、软件等")
                elif keyword in ["新能源"]:
                    suggestions.append("⚡ 关注新能源产业链：电动车、光伏、电池等")
            
            unique_suggestions = list(set(suggestions))
            for suggestion in unique_suggestions[:5]:
                st.write(suggestion)
            
            st.markdown("---")
            st.caption("📝 **数据来源**: 基于Yahoo Finance等真实财经数据源")
            st.caption("🌐 **翻译服务**: 使用Google翻译、有道翻译等专业服务")
            st.caption("⚠️ **免责声明**: 所有分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。")

else:
    st.info("👈 请在左侧输入股票代码并点击分析按钮开始")
    
    with st.expander("📖 系统功能介绍"):
        st.markdown("""
        ### 🎯 主要功能
        
        **📊 股票分析**
        - 公司基本信息展示
        - Piotroski F-Score财务健康评分
        - DCF估值模型计算安全边际
        - 技术指标分析（RSI、均线等）
        - 智能止盈止损建议
        
        **📰 最新时事分析**
        - 自动获取真实财经新闻
        - 多源专业翻译服务（Google、有道等）
        - 智能分页浏览（每页5条）
        - 自动情绪分析（利好/利空/中性）
        - 市场影响评估和操作建议
        - 热点关键词统计
        - 整体市场情绪分析
        
        ### 🚀 使用方法
        1. 在侧边栏输入股票代码（如AAPL、TSLA、MSFT等）
        2. 点击"🔍 开始分析"按钮
        3. 查看"📊 股票分析"标签页的财务和技术分析
        4. 切换到"📰 最新时事分析"查看翻译后的新闻
        5. 使用分页功能浏览所有新闻内容
        
        ### 📋 注意事项
        - 新闻自动翻译为中文，便于阅读
        - 使用多个翻译源确保翻译质量
        - 本系统仅供参考，不构成投资建议
        - 投资有风险，入市需谨慎
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

st.markdown("💹 智能投资分析系统 v2.0 | 中文新闻翻译 | 投资需谨慎")
