---
name: feishu-user
description: Feishu document operations (User Access Token version). Supports automatic token refresh. Use when you need to read, create, write, or append Feishu documents.
---

# Feishu Document Operations (User Access Token)

飞书文档操作客户端，支持自动刷新 Token。使用用户访问令牌认证。

## Install Dependencies

```bash
pip install requests
```

## Quick Start (Recommended: Auto Refresh)

```python
from feishu_client import FeishuClient, load_token_manager

# 方式1: 使用 TokenManager 自动刷新 (推荐)
manager = load_token_manager("YOUR_APP_ID", "YOUR_APP_SECRET")
client = FeishuClient(manager=manager)

# 读取文档 (如果 token 过期会自动刷新)
content = client.read_doc("doc_token")

# 方式2: 手动传入 token
client = FeishuClient(user_access_token="u-xxx")
```

## Get User Access Token

### Step 1: Get App Credentials from Feishu Open Platform

Prepare:
- **APP_ID** - App ID (飞书开放平台应用设置)
- **APP_SECRET** - App Secret (飞书开放平台应用设置)
- **REDIRECT_URI** - 授权回调地址

Enable permissions:
- `docx:document` - 文档操作
- `drive:drive.search:readonly` - 云盘搜索
- `search:docs:read` - 文档搜索

### Step 2: Generate Authorization URL

```bash
python feishu_token.py --app-id YOUR_APP_ID --app-secret YOUR_SECRET --url
```

### Step 3: Exchange for Token

授权后在回调地址拿到 code，然后：

```bash
python feishu_token.py --app-id YOUR_APP_ID --app-secret YOUR_SECRET --code YOUR_CODE
```

Token 会自动保存到 `~/.config/claw-feishu-user/config.json`

---

## Auto Refresh (推荐)

### 为什么需要自动刷新？

用户 access_token 有效期为 2 小时，过期后 API 会返回错误码 `99991663`。

使用 `TokenManager` 可以在 token 过期时自动刷新，无需手动处理。

### 使用方法

```python
from feishu_client import FeishuClient, load_token_manager

# 加载 TokenManager (会自动读取配置中的 app_id 和 app_secret)
manager = load_token_manager("YOUR_APP_ID", "YOUR_APP_SECRET")

# 创建客户端
client = FeishuClient(manager=manager)

# 使用 - 如果 token 过期会自动刷新并重试
content = client.read_doc("doc_token")
client.write_doc("doc_token", "# New Content")
client.append_doc("doc_token", "## More content")
```

### 手动刷新 Token

```bash
# 自动从配置读取并刷新
python feishu_token.py --refresh

# 或指定参数
python feishu_token.py --app-id YOUR_APP_ID --app-secret YOUR_SECRET --refresh
```

---

## Usage Examples

```python
from feishu_client import FeishuClient, load_token_manager

# 初始化 (推荐使用 TokenManager)
manager = load_token_manager("cli_xxx", "secret_xxx")
client = FeishuClient(manager=manager)

# 读取文档
content = client.read_doc("doc_token")
print(content)

# 创建文档
new_token = client.create_doc("My New Document")
print(f"New document: {new_token}")

# 写入文档
client.write_doc("doc_token", "# Title\n\nContent")

# 追加内容
client.append_doc("doc_token", "## New Section\n\nMore content")

# 列出所有块
blocks = client.list_blocks("doc_token")
for block in blocks:
    print(block)

# 获取指定块
block = client.get_block("doc_token", "block_id")

# 更新块
client.update_block("doc_token", "block_id", "New content")

# 删除整个文档
client.delete_doc("doc_token")
```

---

## Convenience Functions

```python
from feishu_client import read_document, create_document, write_document, append_document, load_token_manager

# 使用 TokenManager (推荐)
manager = load_token_manager("cli_xxx", "secret_xxx")

# 读取
content = read_document("doc_token", manager=manager)

# 创建
new_token = create_document("Title", manager=manager)

# 写入
write_document("doc_token", "# Content", manager=manager)

# 追加
append_document("doc_token", "## More", manager=manager)
```

---

## API Reference

### FeishuClient

| Method | Description |
|--------|-------------|
| `read_doc(doc_token)` | 读取文档内容 |
| `create_doc(title, folder_token)` | 创建新文档 |
| `write_doc(doc_token, content)` | 写入文档 (覆盖) |
| `append_doc(doc_token, content)` | 追加内容到末尾 |
| `list_blocks(doc_token)` | 列出所有块 |
| `get_block(doc_token, block_id)` | 获取指定块 |
| `update_block(doc_token, block_id, content)` | 更新块内容 |
| `delete_block(doc_token, block_id)` | 删除块 (不支持) |
| `delete_doc(doc_token)` | 删除整个文档 |

### TokenManager

| Method | Description |
|--------|-------------|
| `load_token_manager(app_id, app_secret)` | 创建 TokenManager |
| `get_token()` | 获取当前 token |
| `refresh_access_token()` | 刷新 token |
| `authorize_with_code(code)` | 使用授权码获取 token |

---

## Notes

1. **Token 过期处理**: 使用 `TokenManager` 会在 token 过期时自动刷新
2. **配置保存**: token 保存在 `~/.config/claw-feishu-user/config.json`
3. **权限要求**: 授权 URL 中的 scope 必须在飞书开放平台启用
4. **删除权限**: 删除文档需要 `space:document:delete` 权限

## Known Issues

1. **删除块 API 不支持** - 飞书文档 API 不支持删除单个块，请使用 `delete_doc()` 删除整个文档
2. **追加内容格式** - payload 必须使用 `block_type: 2` 和 `text.elements` 结构
3. **提取块文本的正确方式** - 常见错误是 `block.get('heading1', {}).get('text')`，正确方式是：
   - 先获取块详情 API: `GET /documents/{doc_token}/blocks/{block_id}`
   - 从返回的 `block` 对象中提取：
     - heading1/heading2/heading3: `block.get('text', {}).get('elements')`
     - paragraph: `block.get('paragraph', {}).get('elements')`
     - bullet: `block.get('bullet', {}).get('elements')`
   - 然后遍历 elements 数组，从每个 `text_run` 中提取 `content`
   ```python
   # 正确示例
   block = client.get_block(doc_token, block_id)
   text_obj = block.get('heading1', {}) or block.get('paragraph', {})
   elements = text_obj.get('elements', [])
   for elem in elements:
       content = elem.get('text_run', {}).get('content', '')
   ```

---

## Related Links

- Feishu Open Platform: https://open.feishu.cn
- Document API: https://open.feishu.cn/document/ukTMukTMukTM/uADOwUjLwgDMzCM4ATm

---

## 更新文档流程

由于飞书文档 API 不支持直接更新/删除块，推荐使用"删除+新建"流程：

```python
from feishu_client import FeishuClient, load_token_manager

manager = load_token_manager("cli_xxx", "secret_xxx")
client = FeishuClient(manager=manager)

# 1. 删除旧文档
old_token = "HUZNdVJZJoDyaMx0VGOczm7snF6"
client.delete_doc(old_token)

# 2. 创建新文档
new_token = client.create_doc("New Title")

# 3. 写入新内容
new_content = """# 新标题

新内容..."""
client.write_doc(new_token, new_content)

print(f"新文档: https://feishu.cn/docx/{new_token}")
```

**注意**：删除文档需要 `space:document:delete` 权限
