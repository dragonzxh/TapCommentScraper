#!/bin/bash

# Steam评论爬虫一键启动脚本 - macOS版
# 设置UTF-8编码
export LANG=zh_CN.UTF-8

# 确定脚本所在目录，并切换到该目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================================"
echo "        Steam评论爬虫启动工具 - macOS版"
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

# 确保必要的目录存在
for dir in "cookies" "output" "logs"; do
    mkdir -p "$dir"
    echo "确保目录存在: $dir"
done

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "未检测到虚拟环境，尝试创建..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "警告: 创建虚拟环境失败，将使用系统Python继续"
    else
        echo "虚拟环境创建成功"
    fi
fi

# 尝试激活虚拟环境
if [ -d "venv" ]; then
    echo "正在激活虚拟环境..."
    source venv/bin/activate
    if [ $? -ne 0 ]; then
        echo "警告: 激活虚拟环境失败，将使用系统Python继续"
    else
        echo "虚拟环境已激活"
    fi
fi

# 检查并安装依赖
if [ -f "requirements.txt" ]; then
    echo "检查并安装依赖..."
    pip install -r requirements.txt > logs/pip_install.log 2>&1
    if [ $? -ne 0 ]; then
        echo "警告: 安装依赖时出现错误，请查看 logs/pip_install.log"
    else
        echo "依赖检查完成"
    fi
fi

echo ""
echo "========================================================"
echo "启动爬虫Web服务..."
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
}
trap cleanup EXIT

# 运行爬虫服务 - 使用完整路径并添加禁用缓存参数
python3 -B "$SCRIPT_DIR/crawler_web_start.py"

# 捕获退出状态
STATUS=$?

# 如果程序异常退出，保持终端窗口打开
if [ $STATUS -ne 0 ]; then
    echo ""
    echo "程序异常退出，错误代码: $STATUS"
    echo "请检查上方错误信息"
    read -p "按Enter键退出..."
fi

# 如果在虚拟环境中，退出虚拟环境
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

echo "程序执行完毕" 