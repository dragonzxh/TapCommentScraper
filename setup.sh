#!/bin/bash
# 游戏评论爬虫与分析工具安装脚本

echo "==============================================="
echo "游戏评论爬虫与分析工具 - 安装脚本"
echo "==============================================="
echo

# 检查Python
echo "正在检查Python环境..."
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "错误: 未找到Python。请先安装Python 3.8以上版本。"
    exit 1
fi

# 检查Python版本
PY_VERSION=$($PYTHON -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
echo "Python版本: $PY_VERSION"

# 确保Python版本>=3.8
$PYTHON -c "import sys; sys.exit(0) if sys.version_info >= (3, 8) else sys.exit(1)" || {
    echo "错误: 需要Python 3.8或更高版本，当前版本为 $PY_VERSION。"
    exit 1
}

# 创建虚拟环境
echo -e "\n创建Python虚拟环境..."
if [ -d "venv" ]; then
    echo "虚拟环境已存在，跳过创建步骤。"
else
    $PYTHON -m venv venv
    echo "已创建虚拟环境: venv"
fi

# 激活虚拟环境
echo -e "\n正在激活虚拟环境..."
case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
        source venv/Scripts/activate
        ;;
    *)
        source venv/bin/activate
        ;;
esac

# 安装依赖
echo -e "\n正在安装依赖..."
echo "注意: 使用更轻量级的依赖配置，使用内置csv模块替代pandas"
pip install --upgrade pip

# 尝试安装所有依赖
if pip install -r requirements.txt; then
    echo "所有依赖安装成功。"
else
    echo "某些依赖安装失败，尝试安装基本依赖..."
    
    # 创建临时无Pillow的依赖文件
    grep -v "pillow" requirements.txt > temp_requirements.txt
    
    # 安装基本依赖
    if pip install -r temp_requirements.txt; then
        echo "基本依赖安装成功，但Pillow安装失败。"
        echo "如果需要图片处理功能，请手动安装Pillow:"
        echo "- Mac: brew install libjpeg libtiff little-cms2 webp openjpeg"
        echo "  然后: pip install pillow"
        echo "- Ubuntu: sudo apt-get install libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libopenjp2-7-dev"
        echo "  然后: pip install pillow"
        echo "- Windows: 尝试使用预编译的二进制包: pip install pillow --only-binary :all:"
    else
        echo "基本依赖安装失败，请检查错误信息并解决问题。"
        exit 1
    fi
    
    # 清理临时文件
    rm temp_requirements.txt
fi

# 创建必要的目录
echo -e "\n创建工作目录..."
mkdir -p output
mkdir -p cookies
mkdir -p logs

# 检查Chrome浏览器
echo -e "\n检查Chrome浏览器..."
if command -v google-chrome &>/dev/null || command -v chrome &>/dev/null || [ -d "/Applications/Google Chrome.app" ] || [ -f "C:/Program Files/Google/Chrome/Application/chrome.exe" ] || [ -f "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe" ]; then
    echo "已检测到Chrome浏览器。"
else
    echo "警告: 未检测到Chrome浏览器。爬虫功能需要Chrome浏览器才能正常运行。"
    echo "请安装Chrome浏览器: https://www.google.com/chrome/"
fi

# 安装完成
echo -e "\n==============================================="
echo "安装完成!"
echo "==============================================="
echo
echo "使用以下命令启动Web界面:"
echo "$ source venv/bin/activate  # Windows: venv\\Scripts\\activate"
echo "$ python crawler_web_start.py"
echo
echo "或运行爬虫:"
echo "$ python steam_crawler.py"
echo
echo "访问Web界面: http://localhost:5000"
echo "===============================================" 