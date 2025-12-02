#!/bin/bash

# Netclip 快速启动脚本

echo "🚀 启动 Netclip 协作编辑平台..."
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

# 检查是否已安装依赖
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

echo "🔧 激活虚拟环境..."
source venv/bin/activate

echo "📚 安装依赖包..."
pip install -q -r requirements.txt

echo ""
echo "✅ 环境准备完成！"
echo ""
echo "🌐 启动服务器在 http://localhost:8080"
echo "🔑 管理后台: http://localhost:8080/admin (密码: admin123)"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动服务器
python3 server.py
