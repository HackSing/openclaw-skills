---
name: imgCreator
description: AI 图片生成技能。内置场景化提示词强化模板，适用于所有生图场景：(1) 火山引擎 Seedream API 调用 (2) 内置 generate_image 工具（Nanobanana 2）(3) 任何需要生成图片的任务。使用前必须先識别场景并套用对应模板强化 Prompt。
---

# imgCreator - AI 图片生成

内置场景化提示词强化规则，适用于所有图片生成工具。

> **重要**：无论使用哪种生图方式（火山引擎 API 或内置 generate_image 工具），都必须先按本文档的场景模板强化 Prompt，再调用生成。

## 使用流程

```
用户描述 → 场景识别 → 模板强化 → 最终 Prompt → API 调用
```

**核心原则**：不要直接使用用户的原始描述调用 API。必须先识别场景，套用对应模板强化 Prompt，再调用。

---

## 场景模板

### 1. 社交媒体封面（social_cover）

**适用**：推特、小红书、公众号等平台的封面图 / 头图

| 平台 | 推荐尺寸 | 说明 |
|------|---------|------|
| 推特 | `3200x1280`（原生 5:2） | 无需裁切 |
| 公众号 | `3008x1280`（原生 2.35:1） | 无需裁切 |
| 小红书 | `1728x2304`（原生 3:4） | 无需裁切 |

**强化规则**：
- 追加风格词：`clean composition, high contrast, professional, modern design`
- 追加负面约束：`no watermark, no text overlay, no human figures unless specified`
- 追加构图词：`leave space for text overlay`（封面需要留白给标题用）
- 使用英文 Prompt 效果更好（Seedream 对英文描述的理解力更强）

**模板**：
```
[用户核心描述]. 
Style: clean, modern, professional, high contrast, [dark/light] background.
Composition: leave clear space for text overlay at [top/bottom/center].
Negative: no watermark, no text, no human figures, no clutter.
```

**示例**：
```
用户输入: "科技路由器主题封面"
强化后: "A futuristic glowing network router node emitting colorful light paths to multiple AI chips of different sizes on dark navy background. Style: clean, modern, professional, high contrast, dark background. Composition: leave clear space for text overlay at top and bottom. Negative: no watermark, no text, no human figures, no clutter."
```

---

### 2. 信息图 / 数据可视化（infographic）

**适用**：数据图表、流程图、对比图

**推荐尺寸**：`1024x1024`（方形）或 `1024x1792`（竖版长图）

**强化规则**：
- 追加风格词：`sleek dashboard UI, data visualization, neon glow on dark background`
- 描述要具体到图表类型（bar chart, pie chart, flow diagram）
- 用颜色编码区分数据层级（green=低, yellow=中, red=高）
- 不要要求精确文字，改用"labeled segments"或"color-coded sections"

**⚠️ 局限性**：AI 图片模型无法准确生成文字。如果信息图需要精确的数据标注和文字标签，建议使用 HTML/CSS 代码生成，而不是用本工具。

**模板**：
```
A sleek data visualization [图表类型] on dark background.
[具体数据描述，用颜色和大小代替文字].
Style: modern dashboard UI, neon glow effect, clean layout.
Negative: no realistic photos, no people, no watermark.
```

---

### 3. 对比图（comparison）

**适用**：Before/After、功能对比、版本对比

**推荐尺寸**：`1024x1024`（方形）或 `1792x1024`（横版双栏）

**强化规则**：
- 明确要求左右分栏或上下分栏
- 使用对比色：失败=红色/暗色，成功=绿色/亮色
- 追加结构词：`split vertically/horizontally, clear dividing line`
- 使用通用符号（❌/✅、红/绿）代替文字标注

**模板**：
```
A clean before-and-after comparison image, [dark/light] background.
Split vertically into two halves with a clear dividing line.
LEFT ([Before 描述], red/dark tones, ❌ icon).
RIGHT ([After 描述], green/bright tones, ✅ icon).
Style: tech infographic, clear visual contrast, minimal.
Negative: no people, no watermark, no clutter.
```

---

### 4. 产品展示 / Logo（product）

**适用**：App 图标、产品截图配图、品牌视觉

**推荐尺寸**：`1024x1024`

**强化规则**：
- 追加风格词：`centered composition, clean background, product photography style`
- 品牌色优先，明确指定色值或色系
- 简洁 > 复杂，元素不超过 3 个

**模板**：
```
[产品/Logo 描述], centered on [背景色] background.
Style: minimal, clean, professional brand aesthetic, [品牌色系].
Negative: no text, no watermark, no busy background.
```

---

### 5. 氛围背景图（atmosphere）

**适用**：文章配图、PPT 背景、桌面壁纸

**推荐尺寸**：根据用途选择

**强化规则**：
- 这是最适合 AI 图片模型的场景
- 追加风格词：`atmospheric, cinematic lighting, depth of field`
- 不要求具体布局，让模型自由发挥
- 抽象 > 具象

**模板**：
```
[氛围描述], [色调] tones.
Style: atmospheric, cinematic lighting, depth of field, dreamy, abstract.
Negative: no text, no watermark, no people unless specified.
```

---

## 通用 Prompt 规则

### 语言选择
- **英文 Prompt 优先**：Seedream 对英文的理解更精准
- 如果用户给的是中文描述，先翻译成英文再补充强化词

### 必须避免的坑
1. **不要要求生成精确文字** — AI 模型无法准确渲染文字，会出现乱码
2. **不要堆砌过多元素** — 描述越复杂，偏差越大。单张图聚焦 1-2 个核心元素
3. **不要描述精确布局** — "左上角放X、右下角放Y"这类空间指令模型很难遵循
4. **不要省略负面约束** — 不加"no people"就可能随机出现人物

### 质量提升词库
根据需要从以下词库中选取追加：

| 类别 | 词汇 |
|------|------|
| 质量 | `high resolution, 4K, detailed, sharp focus, professional` |
| 光效 | `soft lighting, neon glow, cinematic lighting, natural light, backlit` |
| 风格 | `flat vector, 3D render, photorealistic, watercolor, minimalist` |
| 构图 | `centered, rule of thirds, symmetrical, wide shot, close-up` |
| 色调 | `vibrant colors, muted tones, monochrome, warm palette, cool palette` |

---

## API 配置

- **Base URL**: `https://ark.cn-beijing.volces.com/api/v3/images/generations`
- **模型 ID**: `doubao-seedream-4-5-251128`
- **API Key**: `4819095d-77a7-4ef5-b8ce-ff672d57678d`

## 调用示例

### Python

```python
import requests

def generate_image(prompt, size="2048x2048", watermark=False):
    url = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
    headers = {
        "Authorization": "Bearer 4819095d-77a7-4ef5-b8ce-ff672d57678d",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "doubao-seedream-4-5-251128",
        "prompt": prompt,
        "size": size,
        "watermark": watermark,
        "optimize_prompt_options": {"mode": "standard"}
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    result = response.json()
    
    data = result.get("data")
    if isinstance(data, list) and len(data) > 0 and data[0].get("url"):
        return data[0]["url"]
    else:
        raise Exception(f"生成失败: {result}")

# 使用示例
url = generate_image("一只可爱的橘猫坐在窗台上", size="1728x2304")
print(f"图片 URL: {url}")
```

## 支持的图片尺寸

> **重要**：参数名是 `size`（不是 `image_size`）。传错参数名 API 不会报错，而是静默回退到 2048x2048。
>
> 也可以传 `2K` 或 `4K`，配合 prompt 中描述宽高比让模型自动决定尺寸。

### 2K 推荐尺寸

| 比例 | size 值 | 用途 |
|------|---------|------|
| 1:1 | `2048x2048` | 方形产品图 |
| 3:4 | `1728x2304` | 小红书竖图 |
| 4:3 | `2304x1728` | 横版配图 |
| 9:16 | `1600x2848` | 手机壁纸、长图 |
| 16:9 | `2848x1600` | 推特、公众号封面 |
| 2:3 | `1664x2496` | 竖版海报 |
| 3:2 | `2496x1664` | 横版海报 |
| 21:9 | `3136x1344` | 超宽横幅 |

### 4K 推荐尺寸

| 比例 | size 值 | 用途 |
|------|---------|------|
| 1:1 | `4096x4096` | 高清方形 |
| 3:4 | `3520x4704` | 高清竖图 |
| 4:3 | `4704x3520` | 高清横图 |
| 16:9 | `5504x3040` | 高清宽屏 |

> 总像素取值范围 2K: [3686400, 16777216]，宽高比 [1/16, 16]，可自定义任意尺寸。

## 实际响应格式

```json
{
  "model": "doubao-seedream-4-5-251128",
  "created": 1772341973,
  "data": [
    {
      "url": "https://ark-content-generation-v2-cn-beijing.tos-cn-beijing.volces.com/...",
      "size": "2048x2048"
    }
  ],
  "usage": {
    "generated_images": 1,
    "output_tokens": 16384,
    "total_tokens": 16384
  }
}
```

## 注意事项

1. **API Key 安全**: 不要在客户端代码中暴露 API Key
2. **网络环境**: 确保可访问 `ark.cn-beijing.volces.com`
3. **超时设置**: 生图耗时较长，建议 timeout≥120s
4. **错误处理**: 检查 `data` 列表是否存在且非空
5. **URL 有效期**: 返回的图片 URL 24 小时内有效，需及时下载保存
6. **飞书发送**: 图片保存到 `/tmp/openclaw/` 后通过 message 工具发送
7. **提示词优化**: 设置 `optimize_prompt_options.mode` 为 `standard` 可自动优化 prompt

## 参考文档

- [Seedream API 官方参考](resources/seedream_api_reference.md) — 完整请求/响应参数说明
- [火山引擎官方文档](https://www.volcengine.com/docs/82379/1541523?lang=zh)

## Prompt 示例库

- [平台图片规格与推荐风格](examples/platforms.md) — 各平台尺寸速查 + 风格方向索引
- [精准文字信息卡](examples/text_card.md) — 含精确中文文字的数据表格、步骤卡、对比卡（推荐）

## 更新日志

- **2026-03-01 v3**: 根据官方文档修正 `size` 参数名和完整尺寸表，补充 `optimize_prompt_options` / `watermark` 等参数，新增 `resources/` 官方参考文档
- **2026-03-01 v2**: 新增场景化提示词强化模板，修复 API 响应格式文档
