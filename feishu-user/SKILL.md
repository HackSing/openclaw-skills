---
name: feishu-user
description: 飞书文档操作（用户访问令牌版）。使用用户访问令牌认证的飞书文档操作技能。不依赖插件，直接通过 REST API 操作飞书文档。当需要读取、创建、写入、追加飞书文档时使用。
---

# Feishu User

使用用户访问令牌认证的飞书文档操作技能。不依赖插件，直接通过 REST API 调用飞书开放平台。

## 安装依赖

```bash
pip install requests
```

## 快速开始

```python
from feishu_client import FeishuClient

# 初始化客户端
client = FeishuClient(user_access_token="u-xxx")
```

## 获取用户访问令牌

### Step 1: 在飞书开放平台启用权限

需要以下权限：
- `docx:document` - 文档操作
- `drive:drive.search:readonly` - 云盘搜索
- `search:docs:read` - 文档搜索

### Step 2: 生成授权链接

```
https://accounts.feishu.cn/open-apis/authen/v1/authorize?client_id={YOUR_APP_ID}&response_type=code&redirect_uri={YOUR_REDIRECT_URI}&scope=docx%3Adocument%20drive%3Adrive.search%3Areadonly%20search%3Adocs%3Aread
```

### Step 3: 换取令牌

```bash
curl -X POST "https://open.feishu.cn/open-apis/authen/v1/access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "authorization_code",
    "code": "{YOUR_CODE}",
    "app_id": "{YOUR_APP_ID}",
    "app_secret": "{YOUR_APP_SECRET}"
  }'
```

返回的 `access_token` 即为 `user_access_token`。

---

## 使用示例

```python
from feishu_client import FeishuClient

# 初始化
client = FeishuClient(user_access_token="u-xxx")

# 读取文档
content = client.read_doc("doc_token")
print(content)

# 创建文档
new_token = client.create_doc("我的新文档")
print(f"新文档: {new_token}")

# 写入文档
client.write_doc("doc_token", "# 标题\n\n内容")

# 追加内容
client.append_doc("doc_token", "## 新章节\n\n更多内容")

# 列出所有块
blocks = client.list_blocks("doc_token")
for block in blocks:
    print(block)

# 获取指定块
block = client.get_block("doc_token", "block_id")

# 更新块
client.update_block("doc_token", "block_id", "新内容")

# 删除块
client.delete_block("doc_token", "block_id")
```

---

## 便捷函数

不想创建客户端？直接用函数：

```python
from feishu_client import read_document, create_document, write_document, append_document

# 读取
content = read_document("doc_token", user_access_token="u-xxx")

# 创建
new_token = create_document("标题", user_access_token="u-xxx")

# 写入
write_document("doc_token", "# 内容", user_access_token="u-xxx")

# 追加
append_document("doc_token", "## 更多", user_access_token="u-xxx")
```

---

## API 参考

### FeishuClient

| 方法 | 说明 |
|------|------|
| `read_doc(doc_token)` | 读取文档内容 |
| `create_doc(title, folder_token)` | 创建新文档 |
| `write_doc(doc_token, content)` | 写入文档（覆盖） |
| `append_doc(doc_token, content)` | 追加内容到末尾 |
| `list_blocks(doc_token)` | 列出所有块 |
| `get_block(doc_token, block_id)` | 获取指定块 |
| `update_block(doc_token, block_id, content)` | 更新块内容 |
| `delete_block(doc_token, block_id)` | 删除块 |

---

## 注意事项

1. `user_access_token` 有有效期，需要定期刷新
2. 授权链接中的 `scope` 权限必须在飞书开放平台启用
3. 此技能使用用户身份访问个人云文档

---

## 相关链接

- 飞书开放平台: https://open.feishu.cn
- 文档 API: https://open.feishu.cn/document/ukTMukTMukTM/uADOwUjLwgDMzCM4ATm

---

## Token 自动刷新

提供 `feishu_token.py` 脚本用于自动刷新 token。

### 安装依赖

```bash
pip install requests
```

### 首次授权

```bash
# 1. 生成授权链接
python feishu_token.py --app-id YOUR_APP_ID --app-secret YOUR_SECRET --redirect-uri YOUR_REDIRECT_URI --url
```

用户访问授权链接后，会回调到 `YOUR_REDIRECT_URI?code=XXX`

```bash
# 2. 使用授权码获取 token
python feishu_token.py --app-id YOUR_APP_ID --app-secret YOUR_SECRET --code AUTH_CODE
```

Token 会自动保存到 `~/.config/claw-feishu-user/config.json`

### 刷新 Token

```bash
python feishu_token.py --app-id YOUR_APP_ID --app-secret YOUR_SECRET --refresh
```

### 在代码中使用

```python
import json
import os

# 读取缓存的 token
config_path = os.path.expanduser("~/.config/claw-feishu-user/config.json")
with open(config_path) as f:
    config = json.load(f)

# 使用 token
client = FeishuClient(user_access_token=config["access_token"])
```
