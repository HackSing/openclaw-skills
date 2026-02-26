---
name: allstock-data
description: A股全量数据查询技能。主推 adata SDK（多数据源融合），备用腾讯财经 HTTP API。覆盖股票基本信息、K线行情（日/周/月，支持复权）、实时行情、五档盘口、资金流向、概念板块、指数数据、ETF等。
---

# A股全量数据查询

支持两种数据获取方式：
1. **adata SDK（主推）**：开源 A 股量化数据库，多数据源融合，标准化 DataFrame 输出
2. **腾讯财经 HTTP API（备用）**：无需安装依赖，适合轻量快速查询

---

## 一、adata SDK（主推）

### 安装

```bash
pip install adata
# 或指定镜像源
pip install adata -i http://mirrors.aliyun.com/pypi/simple/
# 升级
pip install -U adata
```

### 代理设置（可选）

```python
import adata
adata.proxy(is_proxy=True, ip='60.167.21.27:1133')
```

---

### 1. 股票基本信息

#### 1.1 获取全部 A 股代码

```python
import adata
df = adata.stock.info.all_code()
# 返回字段: stock_code, short_name, exchange, list_date
```

#### 1.2 股本信息

```python
df = adata.stock.info.get_stock_shares(stock_code='000001', is_history=True)
# 返回字段: stock_code, change_date, total_shares, list_a_shares, change_reason 等
```

#### 1.3 申万行业分类

```python
df = adata.stock.info.get_industry_sw(stock_code='300033')
# 返回字段: stock_code, sw_code, industry_name, industry_type, source
```

---

### 2. K线行情

#### 2.1 日/周/月 K线

```python
df = adata.stock.market.get_market(
    stock_code='000001',
    k_type=1,           # 1=日K, 2=周K, 3=月K
    start_date='2024-01-01',
    adjust_type=1        # 0=不复权, 1=前复权, 2=后复权
)
# 返回字段: trade_time, open, close, high, low, volume, amount, pre_close, stock_code, trade_date 等
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `stock_code` | str | 股票代码，如 `'000001'` |
| `k_type` | int | K线类型：1=日, 2=周, 3=月 |
| `start_date` | str | 起始日期，格式 `'YYYY-MM-DD'` |
| `adjust_type` | int | 复权类型：0=不复权, 1=前复权, 2=后复权 |

---

### 3. 实时行情

#### 3.1 批量实时报价

```python
df = adata.stock.market.list_market_current(
    code_list=['000001', '600519', '000795']
)
# 返回字段: stock_code, short_name, price, change, change_pct, volume, amount
```

> 建议单次不超过 500 只股票。

#### 3.2 五档盘口

```python
df = adata.stock.market.get_market_five(stock_code='000001')
# 返回字段: stock_code, short_name, s1~s5(卖价), sv1~sv5(卖量), b1~b5(买价), bv1~bv5(买量)
```

---

### 4. 资金流向

```python
df = adata.stock.market.get_capital_flow(stock_code='000001')
# 返回个股资金流向数据（大单/中单/小单净流入等）
```

---

### 5. 概念板块

#### 5.1 全部概念列表（东方财富）

```python
df = adata.stock.info.all_concept_code_east()
# 返回字段: index_code, name, concept_code, source
```

#### 5.2 概念成分股

```python
df = adata.stock.info.concept_constituent_east(index_code='BK0493')
# 返回字段: stock_code, short_name
```

#### 5.3 单只股票所属概念

```python
# 东方财富
df = adata.stock.info.concept_east(stock_code='000001')

# 百度
df = adata.stock.info.concept_baidu(stock_code='000001')
```

#### 5.4 单只股票所属板块

```python
df = adata.stock.info.stock_plate_east(stock_code='000001')
```

---

### 6. 指数数据

#### 6.1 全部指数代码

```python
df = adata.stock.info.all_index_code()
# 返回字段: index_code, concept_code, name, source
```

#### 6.2 指数成分股

```python
df = adata.stock.info.index_constituent(index_code='000300')
# 返回字段: index_code, stock_code, short_name
```

---

### 7. 分红数据

```python
df = adata.stock.market.get_dividend(stock_code='000001')
# 返回历史分红信息
```

---

### 8. 概念/指数行情

```python
# 东方财富概念 K 线
df = adata.stock.market.get_market_concept_east(index_code='BK0493', k_type=1, start_date='2024-01-01')

# 概念实时行情
df = adata.stock.market.list_market_current_concept_east()

# 指数 K 线
df = adata.stock.market.get_market_index(index_code='000300', k_type=1, start_date='2024-01-01')
```

---

## 二、腾讯财经 HTTP API（备用）

适用于无法安装 `adata` 的轻量场景，直接通过 HTTP 获取实时行情。

### Base URL

```
http://qt.gtimg.cn/q=<stock_code>
```

### 股票代码规则

| 市场 | 代码前缀 | 示例 |
|------|----------|------|
| 上海主板 | sh600xxx | sh600560 |
| 科创板 | sh688xxx | sh688xxx |
| 深圳主板 | sz000xxx | sz000001 |
| 创业板 | sz300xxx | sz300xxx |
| 深圳ETF | sz159xxx | sz159326 |

### 常用指数代码

| 指数 | 代码 |
|------|------|
| 上证综指 | sh000001 |
| 深证成指 | sz399001 |
| 创业板指 | sz399006 |
| 沪深300 | sh000300 |

### 查询示例

```
# 单只
http://qt.gtimg.cn/q=sh600089

# 批量（逗号分隔）
http://qt.gtimg.cn/q=sh600089,sh600560,sz399001
```

### 返回数据解析

返回 `~` 分隔的字符串，关键字段索引：

| 索引 | 含义 |
|------|------|
| 1 | 股票名称 |
| 2 | 股票代码 |
| 3 | 当前价 |
| 4 | 开盘价 |
| 5 | 最低价 |
| 6 | 最高价 |
| 30 | 涨跌额 |
| 31 | 涨跌幅% |

### Python 解析示例

```python
import re
import urllib.request

def get_stock_data(code):
    url = f"http://qt.gtimg.cn/q={code}"
    with urllib.request.urlopen(url) as response:
        data = response.read().decode('gbk')
    match = re.search(r'="([^"]+)"', data)
    if not match:
        return None
    fields = match.group(1).split('~')
    return {
        'name': fields[1],
        'code': fields[2],
        'price': float(fields[3]),
        'open': float(fields[4]),
        'high': float(fields[5]),
        'low': float(fields[6]),
        'change': float(fields[30]),
        'change_pct': float(fields[31]),
    }

data = get_stock_data('sh600089')
print(f"{data['name']}: {data['price']} ({data['change_pct']}%)")
```

---

## 注意事项

1. **adata 优先**：功能更全、数据更可靠，建议优先使用
2. **编码问题**：腾讯财经 API 返回 GBK 编码，需正确解码
3. **数据延迟**：实时数据可能有 15 分钟延迟
4. **请求频率**：避免高频请求，adata 已内置多数据源容错
5. **涨跌幅**：使用 API 返回的字段，不要手动计算
6. **代理设置**：如遇接口限制，可通过 `adata.proxy()` 设置代理
