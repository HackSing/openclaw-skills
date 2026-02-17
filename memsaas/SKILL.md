---
name: memsaas
description: MemSaaS 记忆层服务对接。用于用户冷启动、记忆读取、记忆写入、获取业务数据等操作。当需要对接 MemSaaS 系统时使用，包括：用户建档、记忆上下文读取、对话记忆处理、获取用户业务数据等。
---

# MemSaaS 对接

MemSaaS 是专为 AI Agent 打造的通用记忆层中间件，支持 Dify 自定义工具对接。

## 基础配置

**API Base URL**: `https://memsys-api-1076113452918.us-central1.run.app`

**鉴权方式**: 请求头 `x-api-key`

```python
from memsaas_client import MemSaaSClient

client = MemSaaSClient(api_key="你的APIKey")
```

---

## 核心接口

| 接口 | 用途 |
|------|------|
| `client.warmup(user_id, initial_biz_data)` | 用户冷启动/建档 |
| `client.get_context(user_id, query, scene)` | 记忆读取 |
| `client.process_memory(user_id, user_message, assistant_message)` | 记忆写入 |
| `client.get_domain_field(user_id, field)` | 获取业务数据 |
| `client.reset(user_id)` | 删除用户所有数据 |

---

## 使用示例

```python
from memsaas_client import MemSaaSClient

client = MemSaaSClient(api_key="你的APIKey")

# 对话前：获取记忆
context = client.get_context("aiware", "我最近睡眠质量怎么样？")
print(context["prompts"]["system"])

# 对话后：写入记忆
client.process_memory(
    "aiware",
    "我今天心情不好",
    "我理解你的感受，愿意和我聊聊吗？"
)

# 获取业务数据
health_data = client.get_domain_field("aiware", "sleep")
```

---

## 各接口参数

### warmup(user_id, initial_biz_data)
| 参数 | 必填 | 说明 |
|------|------|------|
| user_id | ✅ | 用户唯一标识 |
| initial_biz_data | ❌ | 初始业务数据 |

### get_context(user_id, query, scene)
| 参数 | 必填 | 说明 |
|------|------|------|
| user_id | ✅ | 用户唯一标识 |
| query | ✅ | 用户当前问题 |
| scene | ❌ | 场景标识 |

### process_memory(user_id, user_message, assistant_message)
| 参数 | 必填 | 说明 |
|------|------|------|
| user_id | ✅ | 用户唯一标识 |
| user_message | ✅ | 用户消息 |
| assistant_message | ✅ | AI 回复 |

### get_domain_field(user_id, field)
| 参数 | 必填 | 说明 |
|------|------|------|
| user_id | ✅ | 用户唯一标识 |
| field | ✅ | domain_data 字段名 |

---

## 快捷函数

不想创建客户端？直接用函数：

```python
from memsaas_client import get_memory_context, process_memory

# 记忆读取
ctx = get_memory_context("aiware", "你好")

# 记忆写入
process_memory("aiware", "用户说", "AI回复")
```
