---
name: allstock-data
description: A股/港股/美股行情查询技能。默认使用腾讯财经 HTTP API（轻量、无需安装），可选 adata SDK（更全量数据）。支持实时行情、K线历史、盘口分析等。
---

# 股票数据查询

支持两种数据获取方式，**默认使用腾讯财经 HTTP API**：

1. **腾讯财经 HTTP API（默认）** - 轻量、无需安装、无需代理
2. **adata SDK（可选）** - 更全量的数据，需要安装和可能的代理

---

## 一、腾讯财经 HTTP API（默认）

### 1.1 A 股实时行情

**接口：**
```
http://qt.gtimg.cn/q=<stock_code>
```

**股票代码规则：**

| 市场 | 代码前缀 | 示例 |
|------|---------|------|
| 上海主板 | sh600xxx | sh600519 茅台 |
| 科创板 | sh688xxx | sh688111 |
| 深圳主板 | sz000xxx | sz000001 平安银行 |
| 创业板 | sz300xxx | sz300033 |
| ETF | sz159xxx | sz159919 |

**指数代码：**

| 指数 | 代码 |
|------|------|
| 上证指数 | sh000001 |
| 深证成指 | sz399001 |
| 创业板指 | sz399006 |
| 科创50 | sz399987 |
| 沪深300 | sh000300 |

**示例：**
```bash
# 单只股票
curl -s "http://qt.gtimg.cn/q=sh600519"

# 多只股票
curl -s "http://qt.gtimg.cn/q=sh600519,sh000001,sz399001"
```

**返回字段：**
```
v_sh600519="1~贵州茅台~600519~1460.00~1466.21~1466.99~14146~6374~7772~..."
         ~  股票名称 ~  开盘  ~   最高  ~   最低  ~ 成交量
```

| 索引 | 含义 |
|------|------|
| 0 | 市场代码 |
| 1 | 股票名称 |
| 2 | 股票代码 |
| 3 | 当前价格 |
| 4 | 开盘价 |
| 5 | 最低价 |
| 6 | 最高价 |
| 30 | 涨跌额 |
| 31 | 涨跌幅(%) |

---

### 1.2 港股实时行情

**接口：**
```
http://qt.gtimg.cn/q=hk<股票代码>
```

**示例：**
```bash
# 腾讯控股
curl -s "http://qt.gtimg.cn/q=hk00700"

# 阿里巴巴
curl -s "http://qt.gtimg.cn/q=hk09988"
```

---

### 1.3 美股实时行情

**接口：**
```
http://qt.gtimg.cn/q=us<股票代码>
```

**示例：**
```bash
# 苹果
curl -s "http://qt.gtimg.cn/q=usAAPL"

# 特斯拉
curl -s "http://qt.gtimg.cn/q=usTSLA"

# 英伟达
curl -s "http://qt.gtimg.cn/q=usNVDA"
```

---

### 1.4 K 线历史数据

**接口：**
```
https://web.ifzq.gtimg.cn/appstock/app/fqkline/get
```

**参数：**
| 参数 | 说明 |
|------|------|
| `_var` | 变量名，如 `kline_dayqfq` |
| `param` | 股票代码,K线类型,开始日期,结束日期,数量,复权类型 |

**K线类型：** `day`(日) / `week`(周) / `month`(月)

**复权类型：** `qfqa`(前复权) / `qfq`(后复权) / 空(不复权)

**示例：**
```bash
# 茅台日K线（最近10天，前复权）
curl -s "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayqfq&param=sh600519,day,,,10,qfqa"

# 平安银行周K线（最近5周）
curl -s "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_weekqfq&param=sz000001,week,,,5,qfqa"

# 创业板指月K线（最近3月）
curl -s "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_monthqfq&param=sz399006,month,,,3,qfqa"
```

**返回格式：**
```json
{"day": [["2026-02-27", "1466.99", "1461.19", "1476.21", "1456.01", "13534"], ...]}
                 日期         开盘      收盘      最高      最低      成交量
```

---

### 1.5 盘口分析

**接口：**
```
http://qt.gtimg.cn/q=s_pk<股票代码>
```

**示例：**
```bash
curl -s "http://qt.gtimg.cn/q=s_pksh600519"
```

**返回：** 内盘占比、外盘占比等

---

## 二、adata SDK（可选）

adata 是开源的 A 股量化数据库，提供更全面的数据。需要安装和可能的代理。

### 安装

```bash
pip install adata
```

### 代理设置（如需）

```python
import adata
adata.proxy(is_proxy=True, ip='your-proxy-ip:port')
```

### 功能列表

| 功能 | 说明 |
|------|------|
| 股票基本信息 | 全部A股代码、股本信息、申万行业分类 |
| K线行情 | 日/周/月K，支持前复权/后复权 |
| 实时行情 | 批量实时报价 |
| 五档盘口 | 买卖盘口数据 |
| 资金流向 | 个股资金流向 |
| 概念板块 | 概念板块数据 |
| 指数数据 | 主要指数行情 |
| ETF | ETF行情 |

### 使用示例

```python
import adata

# 获取全部A股代码
df = adata.stock.info.all_code()

# 获取K线
df = adata.stock.market.get_market(
    stock_code='000001',
    k_type=1,           # 1=日K, 2=周K, 3=月K
    start_date='2024-01-01',
    adjust_type=1        # 0=不复权, 1=前复权, 2=后复权
)

# 实时行情
df = adata.stock.market.list_market_current(
    code_list=['000001', '600519']
)
```

---

## 三、使用场景选择

| 场景 | 推荐方案 |
|------|---------|
| 快速查询单只股票价格 | 腾讯财经 API |
| 获取K线历史数据 | 腾讯财经 API |
| 批量行情查询 | 腾讯财经 API |
| 资金流向数据 | adata SDK |
| 完整财务数据 | adata SDK |
| 概念板块分析 | adata SDK |
| 五档盘口 | 腾讯财经 API 或 adata SDK |

---

## 四、注意事项

1. **编码**：腾讯财经返回 GBK 编码，需要正确解码
2. **涨跌幅**：使用 API 返回的字段(index 31)，不要自行计算
3. **数据延迟**：实时数据可能有 15 分钟延迟
4. **请求频率**：避免高频请求，建议批量查询
5. **错误处理**：无效代码返回 `v_pv_none_match="1"`
