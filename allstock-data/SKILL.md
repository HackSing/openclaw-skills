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

### 1.4 K 线历史数据（实战验证）

**核心API（已验证可用）：**
```
http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=<市场代码><股票代码>,<周期>,,,,<复权类型>
```

**简化的参数格式（实战推荐）：**
```
param=sh600519,month,,,50,qfq
param=sh600519,day,,,60,qfq
param=sh688111,week,,,30,qfq
```

**参数详解：**

| 参数 | 说明 | 有效值 | 示例 |
|------|------|--------|------|
| 股票代码 | 市场+代码 | `sh600519` (沪市), `sh600519` (深市), `sh688111` (创业板) | `sh600519` |
| 周期 | K线周期 | `day`=日线, `week`=周线, `month`=月线 | `month` |
| 数据条数 | 获取数量 | 默认约60-320条（不同周期上限不同） | `50`, `60`, `100`, `320` |
| 复权类型 | 价格调整 | `qfq`=前复权（推荐）, `hfq`=后复权, 省略=不复权 | `qfq` |

**注意：**
1. **不需要 `_var` 参数**：简化调用，直接使用param参数
2. **使用http而非https**：`http://web.ifzq.gtimg.cn/`
3. **实时数据**：包含当天最新数据

**实战示例（以FinPilot经验验证）：**

```bash
# 贵州茅台月K线 - 用于判断大趋势阶段
curl -s "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600519,month,,,50,qfq"

# 科创50周K线 - 判断中期趋势
curl -s "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh688111,week,,,30,qfq"

# 沪深300ETF日K线 - 短期操作参考
curl -s "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh510300,day,,,60,qfq"

# 上证指数周K线 - 大盘分析
curl -s "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh000001,week,,,50"
```

**返回格式解析：**
```json
{
  "code": 0,                    // 0=成功，非0=失败
  "msg": "",                    // 错误信息
  "data": {
    "sh600519": {
      "qfqmonth": [             // 数据key: 复权类型+周期
        ["2025-10-31", "25.450", "25.450", "26.280", "23.450", "123456"],
        // [日期, 开盘价, 收盘价, 最高价, 最低价, 成交量]      
      ]
    }
  }
}
```

**K线数据映射：**
```python
# 数据格式：[日期, 开盘, 收盘, 最高, 最低, 成交量]
kline = ["2026-02-27", "46.70", "46.36", "48.88", "45.68", "214470"]
# 对应：     date      open    close   high    low     volume
```

**Python实战解析函数：**

```python
import urllib.request
import json

def get_kline_data(stock_code, period="day", count=60, adjust="qfq"):
    """获取K线数据的实战函数（已验证）"""
    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={stock_code},{period},,,{count},{adjust}"
    
    try:
        response = urllib.request.urlopen(url, timeout=10)
        data = response.read().decode('utf-8')
        json_data = json.loads(data)
        
        if json_data["code"] == 0:
            key = f"{adjust}{period}"  # qfqday, qfqweek, qfqmonth
            klines = json_data["data"][stock_code][key]
            
            # 转换为更易用的格式
            result = []
            for k in klines:
                item = {
                    "date": k[0],
                    "open": float(k[1]),
                    "close": float(k[2]),
                    "high": float(k[3]),
                    "low": float(k[4]),
                    "volume": int(float(k[5])) if k[5].isdigit() else int(float(k[5]))
                }
                result.append(item)
            
            print(f"✅ 成功获取 {stock_code} 的 {len(result)} 条{period}K线")
            return result
        else:
            print(f"❌ 获取失败: {json_data['msg']}")
            return None
            
    except Exception as e:
        print(f"❌ 请求错误: {e}")
        return None
```

**技术分析应用场景：**

| 分析目标 | 推荐K线周期 | 用途 |
|----------|-------------|------|
| 六阶段判断 | `month` (月K) | 判断大趋势阶段（一、二、四） |
| 支撑阻力 | `day` (日K) + `week` (周K) | 寻找关键价格位置 |
| 止损设置 | `day` (日K) | 基于前期低点设置技术止损 |
| 量价分析 | `day` (日K) | 分析成交量与价格关系 |
| 趋势确认 | `week` (周K) | 确认中期趋势方向 |

**实战技巧：**
1. **月K看阶段**：年涨幅>30%处于阶段二主升浪
2. **周K看趋势**：连续3周上涨为中期趋势向上
3. **日K看操作**：结合分时图进行当日操作

**错误处理：**
- `{"code":1,"msg":"bad params"}`: 参数错误，检查股票代码格式
- 无数据返回：股票代码错误或API限制
- 连接超时：网络问题，重试或检查代理
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
