#!/bin/bash

# 设置UTF-8编码
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# 欢迎信息
echo "==============================================="
echo "Steam Cookies获取工具启动中..."
echo "==============================================="

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 切换到脚本所在目录
cd "$SCRIPT_DIR"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python，请安装Python 3.8或更高版本"
    echo "您可以从 https://www.python.org/downloads/ 下载安装"
    echo "或使用 Homebrew 安装：brew install python3"
    read -p "按回车键退出..."
    exit 1
fi

# 检查Python版本
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
    echo "[错误] Python版本过低：$PYTHON_VERSION，需要3.8或更高版本"
    read -p "按回车键退出..."
    exit 1
fi

# 检查并创建虚拟环境
if [ ! -d "venv" ]; then
    echo "初次运行，创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[错误] 创建虚拟环境失败"
        read -p "按回车键退出..."
        exit 1
    fi
fi

# 确保有正确的执行权限
chmod +x venv/bin/activate

# 激活虚拟环境
source venv/bin/activate

# 检查并安装依赖
if ! pip show selenium &> /dev/null || ! pip show webdriver-manager &> /dev/null; then
    echo "正在安装必要的依赖..."
    pip install selenium webdriver-manager
    if [ $? -ne 0 ]; then
        echo "[错误] 安装依赖失败"
        read -p "按回车键退出..."
        exit 1
    fi
fi

# 检查并创建必要的目录
mkdir -p cookies output logs

# 直接启动Steam Cookies Helper
echo "正在启动Steam Cookies Helper工具..."
python3 steam_cookies_helper.py

# 如果发生错误，保持窗口打开
if [ $? -ne 0 ]; then
    echo ""
    echo "[错误] 程序执行异常，请查看上方错误信息"
    read -p "按回车键退出..."
    exit 1
fi

# 退出虚拟环境
deactivate

echo "程序已完成执行，可以关闭窗口"
read -p "按回车键退出..."
exit 0 