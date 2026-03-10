---
name: imgCreator
description: 使用火山引擎 Seedream 4.5 模型生成图片。适用于：(1) 用户需要 AI 生成图片 (2) 文生图 (3) 图片创作
---

# imgCreator - 火山引擎图片生成

调用火山引擎 Seedream 4.5 模型生成图片。

## API 配置

- **Base URL**: `https://ark.cn-beijing.volces.com/api/v3/images/generations`
- **模型 ID**: `doubao-seedream-4-5-251128`
- **API Key**: `4819095d-77a7-4ef5-b8ce-ff672d57678d`

## 调用示例

### cURL

```bash
curl -X POST "https://ark.cn-beijing.volces.com/api/v3/images/generations" \
  -H "Authorization: Bearer 4819095d-77a7-4ef5-b8ce-ff672d57678d" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "doubao-seedream-4-5-251128",
    "prompt": "一只可爱的橘猫坐在窗台上，阳光透过窗户照进来",
    "image_size": "1024x1024",
    "num_images": 1
  }'
```

### Python

```python
import requests

def generate_image(prompt, image_size="1024x1024", num_images=1):
    url = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
    headers = {
        "Authorization": "Bearer 4819095d-77a7-4ef5-b8ce-ff672d57678d",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "doubao-seedream-4-5-251128",
        "prompt": prompt,
        "image_size": image_size,
        "num_images": num_images
    }
    
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    
    if result.get("code") == 0:
        image_url = result["data"]["images"][0]["url"]
        return image_url
    else:
        raise Exception(f"生成失败: {result.get('message')}")

# 使用示例
url = generate_image("一只可爱的橘猫坐在窗台上")
print(f"图片 URL: {url}")
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | string | 是 | 图片描述文本，支持中文 |
| model | string | 是 | 模型 ID: `doubao-seedream-4-5-251128` |
| image_size | string | 否 | 图片尺寸，默认 `1024x1024` |
| num_images | int | 否 | 生成数量，默认 1 |

## 支持的图片尺寸

- `1024x1024` - 方形
- `1024x1792` - 竖版
- `1792x1024` - 横版

## 响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "images": [
      {
        "url": "https://xxx.jpg"
      }
    ]
  }
}
```

## 发送图片到飞书

生成图片后，必须保存到 `/tmp/openclaw/` 目录才能通过飞书发送：

```python
# 生成图片后，复制到 /tmp/openclaw/
import shutil
output_path = "/tmp/openclaw/generated.jpg"
shutil.copy(generated_path, output_path)
```

然后使用 message 工具发送：
```json
{
  "action": "send",
  "channel": "feishu",
  "media": "/tmp/openclaw/generated.jpg",
  "message": "图片描述",
  "target": "user:用户ID"
}
```

## 注意事项

1. **API Key 安全**: 不要在客户端代码中暴露 API Key
2. **网络环境**: 确保服务器可访问 `ark.cn-beijing.volces.com`
3. **提示词优化**: 使用详细的中文描述可获得更好的生成效果
4. **错误处理**: 检查响应中的 `code` 字段，0 表示成功
5. **飞书发送**: 图片必须保存到 `/tmp/openclaw/` 目录
