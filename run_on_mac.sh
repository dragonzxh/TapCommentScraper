#!/bin/bash
# 游戏评论爬虫启动脚本 (Mac)

echo "==============================================="
echo "游戏评论爬虫启动脚本 (Mac)"
echo "==============================================="
echo

# 检查Python
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "错误: 未找到Python。请先安装Python 3.8以上版本。"
    read -p "按回车键退出..."
    exit 1
fi

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "未找到虚拟环境，请先运行setup.sh安装"
    read -p "按回车键退出..."
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

echo "请选择要运行的爬虫:"
echo "1. Steam游戏评论爬虫"
echo "2. TapTap游戏评论爬虫"
echo "3. Bilibili视频评论爬虫"
echo "4. 所有爬虫"
echo "5. 启动Web界面"
echo "6. 退出"
echo

read -p "请输入选项 [1-6]: " choice

case $choice in
    1)
        echo
        echo "正在启动Steam爬虫..."
        python run_crawlers.py --steam
        ;;
    2)
        echo
        echo "正在启动TapTap爬虫..."
        python run_crawlers.py --taptap
        ;;
    3)
        echo
        echo "正在启动Bilibili爬虫..."
        python run_crawlers.py --bilibili
        ;;
    4)
        echo
        echo "正在启动所有爬虫..."
        python run_crawlers.py --all
        ;;
    5)
        echo
        echo "正在启动Web界面..."
        echo "请在浏览器中访问: http://localhost:5000"
        python crawler_web_start.py
        ;;
    6)
        echo
        echo "退出程序"
        exit 0
        ;;
    *)
        echo "无效选项，请重新运行脚本并选择1-6"
        ;;
esac

echo
echo "任务已完成，按回车键退出..."
read 