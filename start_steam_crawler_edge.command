#!/bin/bash

# Steam评论爬虫一键启动脚本 - Edge浏览器版 - macOS版
# 设置UTF-8编码
export LANG=zh_CN.UTF-8

# 设置工作目录为脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 创建日志目录
mkdir -p logs

# 创建调试日志文件
DEBUG_LOG="logs/edge_crawler_debug_$(date +%Y%m%d_%H%M%S).log"

# 开始记录调试信息
echo "[$(date)] 开始执行脚本" > "$DEBUG_LOG"
echo "[$(date)] 当前目录: $(pwd)" >> "$DEBUG_LOG"

echo "========================================================"
echo "    Steam评论爬虫启动工具 - Edge浏览器版 - macOS版"
echo "========================================================"
echo "正在切换到目录: $(pwd)"

# 检查Python安装
echo "检查Python安装..."
echo "[$(date)] 检查Python安装..." >> "$DEBUG_LOG"
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python，请先安装Python 3.8或更高版本"
    echo "[$(date)] [错误] 未找到Python" >> "$DEBUG_LOG"
    echo "您可以从以下地址下载安装: https://www.python.org/downloads/"
    echo "或通过Homebrew安装: brew install python3"
    read -p "按任意键退出..."
    exit 1
fi

# 输出Python版本信息
echo "[$(date)] Python版本信息:" >> "$DEBUG_LOG"
python3 --version >> "$DEBUG_LOG" 2>&1

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

# 确保必要的目录存在
for dir in "cookies" "output" "logs"; do
    mkdir -p "$dir"
    echo "确保目录存在: $dir"
done

# 检查虚拟环境
echo "检查虚拟环境..."
echo "[$(date)] 检查虚拟环境..." >> "$DEBUG_LOG"
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    echo "[$(date)] 创建虚拟环境..." >> "$DEBUG_LOG"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[错误] 创建虚拟环境失败"
        echo "[$(date)] [错误] 创建虚拟环境失败" >> "$DEBUG_LOG"
        echo "警告: 创建虚拟环境失败，将使用系统Python继续"
    else
        echo "虚拟环境创建成功"
        echo "[$(date)] 虚拟环境创建成功" >> "$DEBUG_LOG"
    fi
    
    source venv/bin/activate
    
    echo "安装依赖项..."
    echo "[$(date)] 安装依赖项..." >> "$DEBUG_LOG"
    pip install --upgrade pip >> "$DEBUG_LOG" 2>&1
    pip install flask selenium beautifulsoup4 requests webdriver-manager >> "$DEBUG_LOG" 2>&1
    if [ $? -ne 0 ]; then
        echo "[错误] 安装依赖项失败"
        echo "[$(date)] [错误] 安装依赖项失败" >> "$DEBUG_LOG"
        echo "警告: 安装依赖时出现错误，请查看 logs/pip_install.log"
    else
        echo "依赖检查完成"
        echo "[$(date)] 依赖检查完成" >> "$DEBUG_LOG"
    fi
else
    echo "检测到已有虚拟环境，激活中..."
    echo "[$(date)] 激活已有虚拟环境..." >> "$DEBUG_LOG"
    source venv/bin/activate
fi

# 检查并安装依赖
if [ -f "requirements.txt" ]; then
    echo "检查并安装依赖..."
    echo "[$(date)] 检查并安装依赖..." >> "$DEBUG_LOG"
    pip install -r requirements.txt > logs/pip_install.log 2>&1
    if [ $? -ne 0 ]; then
        echo "[警告] 安装依赖时出现错误，请查看 logs/pip_install.log"
        echo "[$(date)] [警告] 安装依赖时出现错误，请查看 logs/pip_install.log" >> "$DEBUG_LOG"
    else
        echo "依赖检查完成"
        echo "[$(date)] 依赖检查完成" >> "$DEBUG_LOG"
    fi
fi

# 确保安装了webdriver-manager
echo "确保安装了webdriver-manager..."
echo "[$(date)] 确保安装了webdriver-manager..." >> "$DEBUG_LOG"
pip install webdriver-manager > logs/webdriver_install.log 2>&1

# 检查Microsoft Edge浏览器是否安装
echo "检查Microsoft Edge浏览器..."
echo "[$(date)] 检查Microsoft Edge浏览器..." >> "$DEBUG_LOG"
if [ ! -d "/Applications/Microsoft Edge.app" ]; then
    echo "[警告] 未检测到Microsoft Edge浏览器"
    echo "[$(date)] [警告] 未检测到Microsoft Edge浏览器" >> "$DEBUG_LOG"
    echo "警告: 未检测到Microsoft Edge浏览器，爬虫可能无法正常工作"
    echo "请安装Microsoft Edge浏览器后再运行此脚本"
    echo "您可以从以下地址下载: https://www.microsoft.com/edge"
    echo "是否继续? [y/n]"
    read -n1 choice
    echo
    echo "[$(date)] 用户选择: $choice" >> "$DEBUG_LOG"
    if [[ ! "$choice" =~ ^[Yy]$ ]]; then
        echo "已取消操作，按任意键退出..."
        echo "[$(date)] 用户选择退出程序" >> "$DEBUG_LOG"
        read -n1 -s
        exit 1
    fi
else
    echo "Microsoft Edge浏览器已安装"
    echo "[$(date)] Microsoft Edge浏览器已安装" >> "$DEBUG_LOG"
    
    # 获取Edge版本信息
    EDGE_VERSION=$(/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge --version 2>/dev/null)
    if [ -n "$EDGE_VERSION" ]; then
        echo "Edge版本: $EDGE_VERSION"
        echo "[$(date)] Edge版本: $EDGE_VERSION" >> "$DEBUG_LOG"
    else
        echo "无法获取Edge版本信息"
        echo "[$(date)] 无法获取Edge版本信息" >> "$DEBUG_LOG"
    fi
fi

echo ""
echo "========================================================"
echo "启动爬虫Web服务 (Edge浏览器版)..."
echo "========================================================"
echo ""

# 检查是否已经有实例在运行
LOCK_FILE="$SCRIPT_DIR/.crawler_lock"
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if ps -p $PID > /dev/null; then
        echo "检测到爬虫服务已经在运行中 (PID: $PID)"
        echo "如需重启，请先关闭现有进程或删除锁文件: $LOCK_FILE"
        read -p "按Enter键退出..."
        exit 1
    else
        echo "发现过期的锁文件，将删除并继续启动"
        rm -f "$LOCK_FILE"
    fi
fi

# 创建锁文件
echo $$ > "$LOCK_FILE"

# 设置退出时清理锁文件
cleanup() {
    echo "清理锁文件..."
    rm -f "$LOCK_FILE"
    
    # 如果在虚拟环境中，退出虚拟环境
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate
    fi
    
    # 确保所有Python进程都被停止
    killall python 2>/dev/null
    killall python3 2>/dev/null
    
    echo "程序执行完毕"
}
trap cleanup EXIT

# 设置环境变量，告诉程序不要检查登录状态
export SKIP_LOGIN_CHECK=1
echo "[$(date)] 设置环境变量SKIP_LOGIN_CHECK=1" >> "$DEBUG_LOG"

# 运行爬虫服务 - 使用Edge浏览器
echo "正在使用Edge浏览器启动爬虫服务..."
echo "[$(date)] 正在使用Edge浏览器启动爬虫服务..." >> "$DEBUG_LOG"
python3 -B "$SCRIPT_DIR/src/crawler_web_start.py" --browser edge >> "$DEBUG_LOG" 2>&1

# 打开浏览器访问Steam独立页面
echo "正在打开网页..."
echo "[$(date)] 正在打开网页..." >> "$DEBUG_LOG"
open http://localhost:5000/steam

# 捕获退出状态
STATUS=$?

# 如果程序异常退出，保持终端窗口打开
if [ $STATUS -ne 0 ]; then
    echo ""
    echo "程序异常退出，错误代码: $STATUS"
    echo "请检查上方错误信息"
    echo "[$(date)] 程序异常退出，错误代码: $STATUS" >> "$DEBUG_LOG"
    read -p "按Enter键退出..."
fi 