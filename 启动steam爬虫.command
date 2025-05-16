#!/bin/bash

# 设置目录变量
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "========================================="
echo "      Steam评论爬虫工具 - 一键启动      "
echo "========================================="
echo

# 检查Python是否已安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未检测到Python3，请先安装Python3"
    echo "您可以从 https://www.python.org/downloads/ 下载并安装"
    echo "按任意键退出..."
    read -n1 -s
    exit 1
fi

# 检查虚拟环境是否存在，如果不存在则创建
if [ ! -d "venv" ]; then
    echo "=== 首次运行安装 ==="
    echo "创建虚拟环境..."
    python3 -m venv venv
    
    if [ ! -d "venv" ]; then
        echo "错误: 虚拟环境创建失败"
        echo "按任意键退出..."
        read -n1 -s
        exit 1
    fi
    
    echo "激活虚拟环境..."
    source venv/bin/activate
    
    echo "安装依赖包..."
    pip install --upgrade pip
    pip install flask selenium beautifulsoup4 requests webdriver-manager
else
    echo "检测到已存在的虚拟环境，正在激活..."
    source venv/bin/activate
fi

# 确保output和cookies目录存在
mkdir -p output
mkdir -p cookies

# 检查Chrome浏览器是否安装
if ! "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version &> /dev/null; then
    echo "警告: 未检测到Chrome浏览器，爬虫可能无法正常工作"
    echo "请安装Chrome浏览器后再运行此脚本"
    echo "是否继续? [y/n]"
    read -n1 choice
    echo
    if [[ ! "$choice" =~ ^[Yy]$ ]]; then
        echo "已取消操作，按任意键退出..."
        read -n1 -s
        exit 1
    fi
fi

# 设置环境变量，告诉程序不要检查登录状态
export SKIP_LOGIN_CHECK=1

# 启动Flask服务器
echo "启动网页服务器..."
(python -m crawler_web.app) &

SERVER_PID=$!

# 等待服务器启动
echo "等待服务器启动..."
sleep 3

# 打开浏览器访问Steam独立页面
echo "正在打开网页..."
open http://localhost:5000/steam

echo
echo "Steam评论爬虫工具已启动！"
echo "请在浏览器中操作。完成后关闭此窗口即可停止服务器。"
echo

# 保持脚本运行，直到用户按Ctrl+C退出
read -p "按任意键停止服务器..." -n1 -s
echo
echo "正在停止服务器..."

# 停止Flask服务器进程
if [ -n "$SERVER_PID" ]; then
    kill $SERVER_PID 2>/dev/null
fi

# 确保所有Python进程都被停止
killall python 2>/dev/null
killall python3 2>/dev/null

echo "服务器已停止。" 