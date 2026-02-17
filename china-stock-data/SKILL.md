---
name: china-stock-data
description: Query A-share and US stock data via Tencent Finance API. Use when user needs real-time or historical stock quotes, indices, ETF prices, or market data for Chinese or US markets.
---

# China Stock Data

获取A股和美股实时行情数据。

## A股数据查询

### 基础URL
```
http://qt.gtimg.cn/q=<stock_code>
```

### 股票代码规则

| 市场 | 代码前缀 | 示例 |
|------|----------|------|
| 上海主板 | sh600xxx | sh600560（五洲新春） |
| 上海科创板 | sh688xxx | sh688xxx |
| 深圳主板 | sz000xxx | sz000001（平安银行） |
| 深圳创业板 | sz300xxx | sz300xxx |
| 深圳ETF | sz159xxx | sz159326（电网设备ETF） |

### 指数代码

| 指数 | 代码 |
|------|------|
| 上证指数 | sh000001 |
| 深证成指 | sz399001 |
| 创业板指 | sz399006 |
| 科创50 | sz399987 |
| 沪深300 | sh000300 |

### 查询示例

**单只股票：**
```
http://qt.gtimg.cn/q=sh600089
```

**多只股票（逗号分隔）：**
```
http://qt.gtimg.cn/q=sh600089,sh600560,sz399001
```

### 返回数据格式

返回数据为类JSON格式，字段以`~`分隔：

```
v_sh600089="1~特变电工~600089~28.75~28.92~28.63~1999256~...~-0.17~-0.59~..."
```

**关键字段索引：**

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
| 32 | 最高价 |
| 33 | 最低价 |

**注意**：API返回数据中已包含涨跌幅字段（索引31），优先使用该字段而非自行计算。

## 美股数据查询

腾讯财经API对美股支持有限，建议使用以下替代方案：

### 方案1：Yahoo Finance (推荐)

```bash
curl -s "https://query1.finance.yahoo.com/v8/finance/chart/AAPL"
```

### 方案2：Alpha Vantage (需要API Key)

```bash
curl -s "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=YOUR_KEY"
```

### 常用美股指数代码

| 指数 | Yahoo代码 |
|------|-----------|
| 道琼斯 | ^DJI |
| 纳斯达克 | ^IXIC |
| 标普500 | ^GSPC |

## 数据解析示例

### Python解析腾讯财经数据

```python
import re
import urllib.request

def get_stock_data(code):
    url = f"http://qt.gtimg.cn/q={code}"
    with urllib.request.urlopen(url) as response:
        data = response.read().decode('gbk')
    
    # 提取数据
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

# 使用示例
data = get_stock_data('sh600089')
print(f"{data['name']}: {data['price']} ({data['change_pct']}%)")
```

### 使用web_fetch工具

```python
# 获取多只股票数据
url = "http://qt.gtimg.cn/q=sh000001,sh600089,sz399001"
# 使用web_fetch获取数据，然后解析
```

## 注意事项

1. **编码问题**：腾讯财经返回GBK编码，需正确解码
2. **涨跌幅**：优先使用API返回的字段（索引31），避免自行计算误差
3. **数据延迟**：实时数据可能有15分钟延迟
4. **请求频率**：避免高频请求，建议批量查询
5. **错误处理**：无效代码返回`v_pv_none_match="1"`，需检查返回内容
