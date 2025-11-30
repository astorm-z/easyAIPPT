#!/bin/bash

# Gemini 文本生成 API 测试脚本
# 用于测试大纲生成使用的 Gemini API

# 配置变量
API_KEY="your_api_key_here"
API_BASE_URL="https://generativelanguage.googleapis.com"
MODEL="gemini-1.5-pro"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Gemini 文本生成 API 测试 ===${NC}"
echo ""
echo "API Base URL: $API_BASE_URL"
echo "Model: $MODEL"
echo ""

# 测试请求
echo -e "${YELLOW}发送测试请求...${NC}"
echo ""

response=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_BASE_URL}/v1beta/models/${MODEL}:generateContent?key=${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [{
        "text": "请用一句话介绍人工智能。"
      }]
    }]
  }')

# 分离响应体和状态码
http_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | sed '$d')

echo -e "${YELLOW}HTTP 状态码: ${NC}$http_code"
echo ""

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ API 调用成功！${NC}"
    echo ""
    echo -e "${YELLOW}响应内容:${NC}"
    echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
else
    echo -e "${RED}✗ API 调用失败！${NC}"
    echo ""
    echo -e "${YELLOW}错误信息:${NC}"
    echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
fi

echo ""
echo -e "${YELLOW}=== 测试完成 ===${NC}"
