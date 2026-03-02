# Seedream API 官方参考文档

> 来源：https://www.volcengine.com/docs/82379/1541523?lang=zh
> 更新日期：2026-03-01

## 支持的模型

| 模型 ID | 能力 |
|---------|------|
| doubao-seedream-5.0-lite | 文生图/图生图/组图，支持联网搜索 |
| doubao-seedream-4.5 | 文生图/图生图/组图 |
| doubao-seedream-4.0 | 文生图/图生图/组图 |
| doubao-seedream-3.0-t2i | 仅文生图 |
| doubao-seededit-3.0-i2i | 仅图生图 |

## 请求参数

### model `string` (必填)
模型 ID 或推理接入点 Endpoint ID。

### prompt `string` (必填)
图片描述文本，支持中英文。建议不超过 300 个汉字或 600 个英文单词。

### image `string/array` (可选)
输入参考图片，支持 URL 或 Base64 编码。
- 5.0-lite/4.5/4.0 支持 2-14 张参考图
- 图片格式：jpeg, png, webp, bmp, tiff, gif
- 宽高比范围：[1/16, 16]
- 大小≤10MB，总像素≤6000x6000

### size `string` (可选)

#### doubao-seedream-4.5 尺寸规格

**方式 1**：指定分辨率级别
- 可选值：`2K`、`4K`
- 配合 prompt 中自然语言描述宽高比

**方式 2**：指定精确宽高像素值
- 默认值：`2048x2048`
- 总像素取值范围：[2560x1440=3686400, 4096x4096=16777216]
- 宽高比取值范围：[1/16, 16]

> ⚠️ 需同时满足总像素和宽高比两个条件

**2K 推荐尺寸**：

| 宽高比 | 宽高像素值 |
|--------|-----------|
| 1:1 | 2048x2048 |
| 4:3 | 2304x1728 |
| 3:4 | 1728x2304 |
| 16:9 | 2848x1600 |
| 9:16 | 1600x2848 |
| 3:2 | 2496x1664 |
| 2:3 | 1664x2496 |
| 21:9 | 3136x1344 |

**4K 推荐尺寸**：

| 宽高比 | 宽高像素值 |
|--------|-----------|
| 1:1 | 4096x4096 |
| 3:4 | 3520x4704 |
| 4:3 | 4704x3520 |
| 16:9 | 5504x3040 |
| 9:16 | 3040x5504 |
| 2:3 | 3328x4992 |
| 3:2 | 4992x3328 |
| 21:9 | 6240x2656 |

### seed `integer` (可选, 默认 -1)
> 仅 3.0-t2i / seededit-3.0-i2i 支持

随机数种子，取值范围 [-1, 2147483647]。

### sequential_image_generation `string` (可选, 默认 disabled)
> 仅 5.0-lite/4.5/4.0 支持

控制组图功能。
- `auto`：模型自主判断是否返回组图
- `disabled`：关闭组图，只生成单张

### sequential_image_generation_options.max_images `integer` (可选, 默认 15)
> 仅 5.0-lite/4.5/4.0 支持

组图最多生成数量，取值 [1, 15]。输入参考图数+生成图数≤15。

### optimize_prompt_options.mode `string` (可选, 默认 standard)
> 仅 5.0-lite/4.5/4.0 支持

提示词优化模式。
- `standard`：标准模式，质量更高，耗时较长
- `fast`：快速模式，耗时更短，质量一般（5.0-lite/4.5 不支持）

### output_format `string` (可选, 默认 jpeg)
> 仅 5.0-lite 支持

输出图片格式：`png` 或 `jpeg`。

### response_format `string` (可选, 默认 url)
图片返回格式。
- `url`：返回下载链接（24 小时内有效）
- `b64_json`：返回 Base64 编码

### watermark `boolean` (可选, 默认 true)
是否添加"AI生成"水印。
- `false`：不添加
- `true`：右下角添加水印

### guidance_scale `float` (可选)
> 仅 3.0-t2i (默认 2.5) / seededit-3.0-i2i (默认 5.5) 支持
> 5.0-lite/4.5/4.0 不支持

文本权重，值越大与 prompt 相关性越强。取值 [1, 10]。

### stream `boolean` (可选, 默认 false)
> 仅 5.0-lite/4.5/4.0 支持

是否开启流式输出。

### tools `array of object` (可选)
> 仅 5.0-lite 支持

联网搜索工具配置：`{"type": "web_search"}`。

## 响应参数

### model `string`
使用的模型 ID。

### created `integer`
请求创建时间（Unix 时间戳秒）。

### data `array`
输出图片信息。

- data[].url `string` — 图片 URL（response_format=url 时）
- data[].b64_json `string` — Base64 数据（response_format=b64_json 时）
- data[].size `string` — 实际生成的宽高像素值，如 `2048x2048`
- data[].error.code — 单张图片错误码
- data[].error.message — 单张图片错误信息

### usage `object`
用量信息。

- usage.generated_images `integer` — 成功生成的图片张数
- usage.output_tokens `integer` — 消耗 token 数 = sum(图片长*图片宽)/256
- usage.total_tokens `integer` — 总 token 数（当前与 output_tokens 一致）
- usage.tool_usage.web_search `integer` — 联网搜索调用次数

### error `object`
请求级别错误信息。
- error.code `string`
- error.message `string`
