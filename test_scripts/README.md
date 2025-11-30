# Gemini API 测试脚本

这些脚本用于测试第三方 Gemini API 是否正常工作。

## 文件说明

- `test_gemini_text.sh` - 测试文本生成 API（用于大纲生成）
- `test_gemini_image.sh` - 测试图片生成 API（用于 PPT 页面生成）

## 使用方法

### 1. 配置 API Key

编辑脚本文件，修改以下变量：

```bash
API_KEY="your_api_key_here"          # 替换为你的 API Key
API_BASE_URL="https://your-api.com"  # 如果使用代理，修改此 URL
MODEL="gemini-1.5-pro"               # 如果需要，修改模型名称
```

### 2. 赋予执行权限

```bash
chmod +x test_scripts/*.sh
```

### 3. 运行测试

#### 测试文本生成 API

```bash
./test_scripts/test_gemini_text.sh
```

#### 测试图片生成 API

```bash
./test_scripts/test_gemini_image.sh
```

## 直接使用 curl 命令

如果你不想使用脚本，也可以直接使用 curl 命令：

### 测试文本生成

```bash
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [{
        "text": "请用一句话介绍人工智能。"
      }]
    }]
  }'
```

### 测试图片生成

```bash
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent?key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [{
        "text": "生成一张简约风格的PPT封面图片，主题是人工智能，使用蓝色和白色配色。"
      }]
    }],
    "generationConfig": {
      "responseModalities": ["IMAGE"],
      "imageConfig": {
        "aspectRatio": "16:9",
        "imageSize": "2K"
      }
    }
  }'
```

## 测试代理 API

如果你使用的是代理服务，只需修改 `API_BASE_URL`：

```bash
# 例如使用自定义代理
API_BASE_URL="https://your-proxy.com"

# 测试文本生成
curl -X POST "${API_BASE_URL}/v1beta/models/gemini-1.5-pro:generateContent?key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [{
        "text": "测试消息"
      }]
    }]
  }'
```

## 响应说明

### 成功响应

- HTTP 状态码：200
- 响应体包含生成的内容

**文本生成响应示例：**
```json
{
  "candidates": [{
    "content": {
      "parts": [{
        "text": "人工智能是..."
      }]
    }
  }]
}
```

**图片生成响应示例：**
```json
{
  "candidates": [{
    "content": {
      "parts": [{
        "inlineData": {
          "mimeType": "image/png",
          "data": "base64_encoded_image_data..."
        }
      }]
    }
  }]
}
```

### 失败响应

- HTTP 状态码：400/401/403/500 等
- 响应体包含错误信息

**错误响应示例：**
```json
{
  "error": {
    "code": 401,
    "message": "API key not valid",
    "status": "UNAUTHENTICATED"
  }
}
```

## 常见问题

### 1. API Key 无效

错误信息：`API key not valid`

解决方法：
- 检查 API Key 是否正确
- 确认 API Key 是否已激活
- 检查 API Key 是否有相应的权限

### 2. 模型不存在

错误信息：`Model not found`

解决方法：
- 检查模型名称是否正确
- 确认你的 API Key 是否有访问该模型的权限
- 尝试使用其他可用的模型

### 3. 配额超限

错误信息：`Quota exceeded`

解决方法：
- 检查 API 配额是否用完
- 等待配额重置
- 升级 API 套餐

### 4. 网络连接问题

错误信息：`Could not resolve host` 或 `Connection timeout`

解决方法：
- 检查网络连接
- 确认 API Base URL 是否正确
- 如果在中国大陆，可能需要使用代理

## 在项目中使用

测试成功后，将配置信息填入项目的 `.env` 文件：

```bash
# 文本生成配置
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-pro
GEMINI_API_BASE_URL=https://generativelanguage.googleapis.com

# 图片生成配置
BANANA_API_KEY=your_api_key_here
BANANA_MODEL=gemini-3-pro-image-preview
BANANA_API_BASE_URL=https://generativelanguage.googleapis.com
```

如果使用代理，修改对应的 `API_BASE_URL`。
