# A-Share 使用指南

本文档说明如何使用 TradingAgents 分析 A 股股票。

---

## 1. 安装

### 1.1 克隆仓库

```bash
git clone https://github.com/sharkpicker/a-trading-agent.git
cd a-trading-agent
```

### 1.2 创建虚拟环境（推荐）

```bash
conda create -n tradingagents python=3.12
conda activate tradingagents
```

或

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 1.3 安装依赖

**基础安装（不含 A 股数据源）：**

```bash
pip install .
```

**完整安装（含 A 股数据源 mootdx + akshare）：**

```bash
pip install ".[china]"
```

> 注意：`[china]` 是可选依赖组，包含 mootdx 和 akshare。不安装则无法使用 A 股数据功能。

---

## 2. 配置

### 2.1 LLM API Key（必须）

TradingAgents 需要 LLM 来分析数据。选择你有的 API Key 并设置：

```bash
# 推荐：国内可用的大模型
export DASHSCOPE_CN_API_KEY=your_key_here    # 通义千问（国内）
export ZHIPU_CN_API_KEY=your_key_here        # GLM（智谱，国内）
export DEEPSEEK_API_KEY=your_key_here        # DeepSeek

# 或国际模型
export OPENAI_API_KEY=your_key_here
export ANTHROPIC_API_KEY=your_key_here
```

> 获取 API Key：
> - 通义千问：https://dashscope.console.aliyun.com/
> - 智谱 GLM：https://open.bigmodel.cn/
> - DeepSeek：https://platform.deepseek.com/

### 2.2 配置 A 股数据源（必须）

**方式一：环境变量（推荐）**

```bash
export TRADINGAGENTS_DATA_VENDORS='{"core_stock_apis":"china_stock","technical_indicators":"china_stock","fundamental_data":"china_stock","news_data":"china_stock","macro_data":"china_stock","prediction_markets":"polymarket"}'
```

**方式二：Python 代码中配置**

```python
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["data_vendors"] = {
    "core_stock_apis": "china_stock",
    "technical_indicators": "china_stock",
    "fundamental_data": "china_stock",
    "news_data": "china_stock",
    "macro_data": "china_stock",
    "prediction_markets": "polymarket",
}
```

**方式三：混合模式（A 股 + 美股）**

```bash
export TRADINGAGENTS_DATA_VENDORS='{"core_stock_apis":"china_stock,yfinance","fundamental_data":"china_stock,yfinance","news_data":"china_stock,yfinance","macro_data":"china_stock,fred","prediction_markets":"polymarket"}'
```

> 混合模式下，A 股代码自动走 china_stock，美股代码自动走 yfinance。

---

## 3. 运行

### 3.1 命令行方式（CLI）

```bash
# 交互式选择
python -m cli.main

# 直接分析指定 A 股
python -m cli.main --ticker 000001
python -m cli.main --ticker 600000
```

在 CLI 中：
1. 选择 `LLM Provider`（如 `dashscope` 或 `zhipu`）
2. 输入 A 股代码：`000001` 或 `600000`（自动识别为 A 股）
3. 选择分析日期
4. 等待分析结果

### 3.2 Python 代码方式

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 配置
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "dashscope"          # 或 "zhipu", "deepseek"
config["deep_think_llm"] = "qwen-max"         # 深度思考模型
config["quick_think_llm"] = "qwen-turbo"      # 快速任务模型

# A 股数据源配置
config["data_vendors"] = {
    "core_stock_apis": "china_stock",
    "technical_indicators": "china_stock",
    "fundamental_data": "china_stock",
    "news_data": "china_stock",
    "macro_data": "china_stock",
    "prediction_markets": "polymarket",
}

# 创建分析实例
ta = TradingAgentsGraph(debug=True, config=config)

# 分析 A 股（代码会自动识别为 A 股）
_, decision = ta.propagate("000001", "2026-06-17")  # 平安银行
print(decision)

# 分析另一只 A 股
_, decision = ta.propagate("600000", "2026-06-17")  # 浦发银行
print(decision)
```

### 3.3 支持的 A 股代码格式

| 输入格式 | 示例 | 说明 |
|---------|------|------|
| 纯数字代码 | `000001` | 自动识别交易所（000开头→深圳，600开头→上海） |
| 带后缀 | `000001.SZ` | 深圳 |
| 带后缀 | `600000.SS` | 上海 |
| 科创板 | `688001` | 自动识别为上海科创板 |
| 创业板 | `300001` | 自动识别为深圳创业板 |
| 北交所 | `430001` | 自动识别为北京交易所 |

---

## 4. 数据源说明

| 数据类型 | 数据源 | 备注 |
|---------|--------|------|
| 行情 OHLCV | mootdx（主）+ 腾讯财经（备） | 日线数据 |
| 技术指标 | stockstats（复用美股逻辑） | 基于 OHLCV 计算 |
| 基本面 | mootdx F10 | 公司概况、财务三表 |
| 个股新闻 | akshare | 东方财富新闻 |
| 宏观新闻 | akshare | CCTV 财经新闻 |
| 宏观指标 | akshare | CPI、PPI、PMI、LPR 等 |
| 大股东交易 | akshare | 增减持数据 |

---

## 5. 常见问题

### Q1: 安装 mootdx 失败？

```bash
# 尝试单独安装
pip install mootdx --break-system-packages

# 或使用 conda
conda install -c conda-forge mootdx
```

### Q2: akshare 安装后导入失败？

```bash
# akshare 依赖较多，建议完整安装
pip install akshare --upgrade --break-system-packages
```

### Q3: 分析 A 股时提示 "No market data"？

1. 确认已安装 `[china]` 依赖：`pip install ".[china]"`
2. 确认已配置 `data_vendors` 为 `china_stock`
3. 确认 A 股代码正确（6位数字）
4. 检查网络连接（mootdx 和 akshare 需要访问国内数据源）

### Q4: 可以同时分析美股和 A 股吗？

可以。使用混合模式配置：

```python
config["data_vendors"] = {
    "core_stock_apis": "china_stock,yfinance",
    "fundamental_data": "china_stock,yfinance",
    "news_data": "china_stock,yfinance",
    "macro_data": "china_stock,fred",
    "prediction_markets": "polymarket",
}
```

系统会根据代码自动路由：
- `000001` → china_stock
- `AAPL` → yfinance

### Q5: 使用国内 LLM 需要额外配置吗？

需要设置对应的 API Key 和选择正确的 provider：

```python
# 通义千问（国内）
config["llm_provider"] = "dashscope"
config["deep_think_llm"] = "qwen-max"

# 智谱 GLM（国内）
config["llm_provider"] = "zhipu"
config["deep_think_llm"] = "glm-4"

# DeepSeek
config["llm_provider"] = "deepseek"
config["deep_think_llm"] = "deepseek-chat"
```

---

## 6. 完整示例脚本

```python
#!/usr/bin/env python3
"""A-Share analysis example."""

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 1. 配置
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "dashscope"
config["deep_think_llm"] = "qwen-max"
config["quick_think_llm"] = "qwen-turbo"
config["output_language"] = "Chinese"

# 2. A 股数据源
config["data_vendors"] = {
    "core_stock_apis": "china_stock",
    "technical_indicators": "china_stock",
    "fundamental_data": "china_stock",
    "news_data": "china_stock",
    "macro_data": "china_stock",
    "prediction_markets": "polymarket",
}

# 3. 创建实例
ta = TradingAgentsGraph(debug=True, config=config)

# 4. 分析 A 股
stocks = ["000001", "600000", "300750", "688981"]
for stock in stocks:
    print(f"\n{'='*60}")
    print(f"Analyzing {stock}...")
    print(f"{'='*60}")
    _, decision = ta.propagate(stock, "2026-06-17")
    print(decision)
```

---

## 7. 许可证

本项目是 TradingAgents（TauricResearch）的衍生作品，遵循 Apache License 2.0。
详见 [LICENSE](./LICENSE) 和 [NOTICE](./NOTICE)。
