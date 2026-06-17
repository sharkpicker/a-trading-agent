# TradingAgents A股支持 - 实现计划

## 概述

为 TradingAgents 增加完整的 A 股数据支持，新增 `china_stock` vendor 接入现有路由体系。

---

## Phase 1: A股代码规范化 + 行情数据接口（3天）

### Task 1.1: 修改 symbol_utils.py 支持 A 股代码
- [ ] 在 `_ALIASES` 中增加 A 股代码规则映射
- [ ] 在 `normalize_symbol()` 中增加 A 股代码识别分支
- [ ] 实现 `_resolve_china_exchange_by_code()` 辅助函数
- [ ] 实现 `is_china_stock()` 判断函数
- [ ] 更新 `is_yahoo_safe()` 支持 A 股代码字符
- [ ] 添加单元测试

**文件**: `tradingagents/dataflows/symbol_utils.py`

### Task 1.2: 创建 china_stock 目录结构
- [ ] 创建 `tradingagents/dataflows/china_stock/__init__.py`
- [ ] 创建 `tradingagents/dataflows/china_stock/symbol_parser.py`
- [ ] 创建 `tradingagents/dataflows/china_stock/mootdx_client.py`
- [ ] 创建 `tradingagents/dataflows/china_stock/tencent_client.py`
- [ ] 创建 `tradingagents/dataflows/china_stock/errors.py`

### Task 1.3: 实现 mootdx 行情数据接口
- [ ] 实现 `get_stock_data_mootdx()` 函数
- [ ] 确保返回 CSV 格式与 yfinance 一致（Date, Open, High, Low, Close, Volume）
- [ ] 确保 header 格式一致
- [ ] 处理 mootdx 连接失败时的降级逻辑
- [ ] 添加单元测试

### Task 1.4: 实现腾讯财经备用接口
- [ ] 实现 `get_stock_data_tencent()` 函数
- [ ] 确保返回格式与 mootdx/yfinance 完全一致
- [ ] 处理网络超时和重试
- [ ] 添加单元测试

### Task 1.5: 实现 china_stock 统一的 get_stock_data
- [ ] 在 `__init__.py` 中实现 `get_stock_data()` 入口函数
- [ ] 实现主备切换逻辑（mootdx → 腾讯）
- [ ] 统一错误处理（NoMarketDataError）
- [ ] 添加集成测试

---

## Phase 2: 基本面数据接口（2天）

### Task 2.1: 实现 mootdx F10 基本面数据
- [ ] 实现 `get_fundamentals_china()` - 公司概况 + 主要财务指标
- [ ] 实现 `get_balance_sheet_china()` - 资产负债表
- [ ] 实现 `get_cashflow_china()` - 现金流量表
- [ ] 实现 `get_income_statement_china()` - 利润表
- [ ] 确保返回格式与 yfinance 一致（Label: Value 或 CSV）
- [ ] 添加单元测试

**文件**: `tradingagents/dataflows/china_stock/fundamentals.py`

### Task 2.2: 实现 get_fundamentals 入口函数
- [ ] 在 `__init__.py` 中统一导出
- [ ] 处理 mootdx finance 模块缺失的情况
- [ ] 添加集成测试

---

## Phase 3: 新闻 + 公告数据接口（2天）

### Task 3.1: 实现 akshare 新闻接口
- [ ] 实现 `get_news_china()` - 个股新闻
- [ ] 实现 `get_global_news_china()` - 宏观新闻（替换 global_news_queries 为 A 股相关）
- [ ] 实现 `get_insider_transactions_china()` - 大股东增减持
- [ ] 确保返回格式与 yfinance 一致
- [ ] 添加单元测试

**文件**: `tradingagents/dataflows/china_stock/news.py`

### Task 3.2: 实现 akshare 公告接口
- [ ] 实现 `get_announcements_china()` - 公司公告
- [ ] 添加单元测试

**文件**: `tradingagents/dataflows/china_stock/announcements.py`

---

## Phase 4: 宏观数据接口 + 路由层集成（2天）

### Task 4.1: 实现 akshare 宏观数据接口
- [ ] 实现 `get_macro_indicators_china()` - CPI、PPI、PMI、M2、LPR、失业率等
- [ ] 确保返回格式与 FRED 一致（Label: Value）
- [ ] 添加单元测试

**文件**: `tradingagents/dataflows/china_stock/macro.py`

### Task 4.2: 修改 interface.py 注册 china_stock vendor
- [ ] 导入所有 china_stock 数据函数
- [ ] 在 `VENDOR_LIST` 中增加 `"china_stock"`
- [ ] 在 `VENDOR_METHODS` 中为每个工具方法增加 `"china_stock"` 映射
- [ ] 确保 TOOLS_CATEGORIES 保持不变

**文件**: `tradingagents/dataflows/interface.py`

### Task 4.3: 修改 default_config.py
- [ ] 在 `data_vendors` 中增加 `"china_stock"` 选项注释
- [ ] 在 `benchmark_map` 中确认 `.SS` 和 `.SZ` 映射正确
- [ ] 更新 `global_news_queries` 为 A 股相关中文查询（可选）

**文件**: `tradingagents/default_config.py`

### Task 4.4: 修改 pyproject.toml
- [ ] 增加 `[project.optional-dependencies] china` 段
- [ ] 添加 `mootdx>=0.1.0` 和 `akshare>=1.10.0`

**文件**: `pyproject.toml`

### Task 4.5: 实现技术指标复用
- [ ] 确认 `get_indicators_china` 直接复用 `get_stock_stats_indicators_window`
- [ ] 验证 A 股 OHLCV 数据缓存格式正确

**文件**: `tradingagents/dataflows/china_stock/__init__.py`

---

## Phase 5: 测试 + 验证（3天）

### Task 5.1: 单元测试
- [ ] symbol_utils 测试（A 股代码规范化）
- [ ] mootdx_client 测试（mock）
- [ ] tencent_client 测试（mock）
- [ ] fundamentals 测试（mock）
- [ ] news 测试（mock）
- [ ] macro 测试（mock）

### Task 5.2: 集成测试
- [ ] 端到端 A 股分析流程测试
- [ ] 路由层 fallback 测试
- [ ] 美股功能回归测试

### Task 5.3: 代码审查
- [ ] 检查所有返回格式与 yfinance 一致
- [ ] 检查错误处理覆盖
- [ ] 检查类型注解完整
- [ ] 运行 ruff 格式化

---

## 依赖关系图

```
Phase 1 (代码规范化 + 行情)
    │
    ├──→ Phase 2 (基本面)
    │       │
    │       ├──→ Phase 3 (新闻 + 公告)
    │       │       │
    │       │       ├──→ Phase 4 (宏观 + 路由集成)
    │       │       │       │
    │       │       │       ├──→ Phase 5 (测试)
    │       │       │       │
    └──→ 所有 china_stock 模块完成后统一注册到 interface.py
```

## 关键约束

1. **数据类别**: 严格使用现有 6 个 TOOLS_CATEGORIES，不新增
2. **工具方法**: 严格使用现有 11 个方法名
3. **返回格式**: 与 yfinance/FRED 版本完全一致
4. **枚举值**: Buy/Sell/Hold/Overweight/Underweight 保持英文
5. **向后兼容**: 所有美股功能不受影响
