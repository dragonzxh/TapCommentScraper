#!/bin/bash

# Steam评论爬虫Web服务启动脚本
# 设置UTF-8编码
export LANG=zh_CN.UTF-8

# 确定脚本所在目录，并切换到该目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================================"
echo "Steam评论爬虫Web服务启动脚本"
echo "========================================================"
echo "正在切换到目录: $SCRIPT_DIR"

# 检查Python3是否存在
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3。请安装Python 3.8或更高版本后再试。"
    echo "您可以从以下地址下载安装: https://www.python.org/downloads/"
    echo "或通过Homebrew安装: brew install python3"
    read -p "按任意键退出..."
    exit 1
fi

# 检查Python版本
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MINIMUM_VERSION="3.8"

# 比较版本号
if [ "$(printf '%s\n' "$MINIMUM_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$MINIMUM_VERSION" ]; then
    echo "错误: Python版本太低。需要Python $MINIMUM_VERSION或更高版本，当前版本为$PYTHON_VERSION"
    read -p "按任意键退出..."
    exit 1
fi

echo "使用Python版本: $PYTHON_VERSION"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "创建虚拟环境失败。将尝试直接运行脚本。"
    else
        echo "虚拟环境创建成功。"
    fi
fi

# 尝试激活虚拟环境
if [ -d "venv" ]; then
    echo "正在激活虚拟环境..."
    source venv/bin/activate
    if [ $? -ne 0 ]; then
        echo "激活虚拟环境失败。将尝试直接运行脚本。"
    fi
fi

# 确保必要的目录存在
mkdir -p cookies output logs

# 运行启动脚本
echo "正在启动服务..."
python3 启动服务.py

# 捕获退出状态
STATUS=$?

# 如果脚本非正常退出，保持终端窗口打开以查看错误信息
if [ $STATUS -ne 0 ]; then
    echo "服务启动失败，退出码: $STATUS"
    echo "请检查上面的错误信息"
    read -p "按Enter键退出..."
fi

# 完成后显示成功消息
echo "脚本执行完成"

# 如果是在虚拟环境中运行，请退出虚拟环境
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

# 保持终端窗口打开一段时间
sleep 5 