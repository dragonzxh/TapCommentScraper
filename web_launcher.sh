#!/bin/bash

# 评论爬虫Web应用通用启动器
# 使用相对路径，可以从任何位置启动

# 获取脚本所在的目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 输出欢迎信息
echo "================================================="
echo "      评论爬虫Web应用 - 通用启动器"
echo "================================================="
echo "正在初始化..."
echo ""

# 切换到项目目录
cd "$SCRIPT_DIR"
echo "✓ 当前工作目录: $SCRIPT_DIR"

# 检查Python
echo "正在检查Python环境..."
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "错误: 未找到Python。请先安装Python 3.8以上版本。"
    echo ""
    echo "您可以使用brew安装Python:"
    echo "brew install python"
    echo ""
    echo "按任意键退出..."
    read -n 1
    exit 1
fi

# 检查Python版本
PY_VERSION=$($PYTHON -c "import sys; print(sys.version_info[0]*10+sys.version_info[1])")
if [[ $PY_VERSION -lt 38 ]]; then
    echo "错误: Python版本过低，需要Python 3.8或更高版本。"
    echo ""
    echo "按任意键退出..."
    read -n 1
    exit 1
fi
echo "✓ Python版本检查通过"

# 检查虚拟环境是否存在
if [ -d "venv" ]; then
    # 激活虚拟环境
    source venv/bin/activate
    echo "✓ 已激活Python虚拟环境"
else
    echo "未找到虚拟环境，正在为您自动安装..."
    echo "首次运行需要一些时间，请耐心等待..."
    echo ""
    
    # 执行setup
    if [ -f "setup.sh" ]; then
        bash setup.sh
        if [ $? -ne 0 ]; then
            echo ""
            echo "初始化失败！请尝试手动运行setup.sh，或查看上面的错误信息。"
            echo ""
            echo "按任意键退出..."
            read -n 1
            exit 1
        fi
    else
        # 创建虚拟环境
        echo "正在创建虚拟环境..."
        $PYTHON -m venv venv
        if [ $? -ne 0 ]; then
            echo "创建虚拟环境失败！"
            echo ""
            echo "按任意键退出..."
            read -n 1
            exit 1
        fi
        
        # 激活虚拟环境
        source venv/bin/activate
        
        # 安装依赖
        echo "正在安装必要依赖..."
        pip install --upgrade pip
        
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt
            if [ $? -ne 0 ]; then
                echo "部分依赖安装失败，但将继续尝试启动..."
            fi
        else
            echo "requirements.txt文件不存在，安装基本依赖..."
            pip install flask selenium beautifulsoup4 webdriver-manager
        fi
        
        # 创建必要目录
        mkdir -p output
        mkdir -p cookies
        mkdir -p logs
    fi
    
    echo "✓ 初始化完成！"
    echo ""
fi

# 检查启动脚本是否存在
if [ -f "crawler_web_start.py" ]; then
    # 启动Web应用
    echo "✓ 正在启动Web服务器..."
    echo "✓ 服务启动后，请在浏览器中访问: http://localhost:5000"
    echo ""
    python crawler_web_start.py
else
    echo "错误: 找不到启动脚本 crawler_web_start.py!"
    echo "请确保项目文件完整"
    echo ""
    echo "按任意键退出..."
    read -n 1
    exit 1
fi

# 脚本结束
echo ""
echo "Web服务器已关闭"
echo "按任意键退出..."
read -n 1 