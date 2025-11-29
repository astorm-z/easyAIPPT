#!/bin/bash

# EasyAIPPT 启动脚本

echo "正在启动 EasyAIPPT..."

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "错误: .env 文件不存在"
    echo "请复制 .env.example 为 .env 并填写配置"
    exit 1
fi

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python 3"
    exit 1
fi

# 检查依赖是否安装
if [ ! -d "venv" ]; then
    echo "未找到虚拟环境，正在创建..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 启动应用
echo "启动 Flask 应用..."
python app.py
