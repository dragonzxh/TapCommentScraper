#!/bin/bash

# 评论爬虫Web应用快速启动器 (macOS)
# 此文件可以放在桌面上，用户只需双击即可启动应用

# 获取脚本真实路径
REAL_SCRIPT_PATH="/Users/hippolyte/TapCommentScraper"

# 输出欢迎信息
echo "================================================="
echo "      评论爬虫Web应用 - 快速启动器"
echo "================================================="
echo "正在启动服务..."
echo ""

# 切换到项目目录
cd "$REAL_SCRIPT_PATH"

# 检查目录是否存在
if [ ! -d "$REAL_SCRIPT_PATH" ]; then
    echo "错误: 找不到项目目录!"
    echo "请确保项目已安装在: $REAL_SCRIPT_PATH"
    echo ""
    echo "按任意键退出..."
    read -n 1
    exit 1
fi

# 检查虚拟环境是否存在
if [ -d "venv" ]; then
    # 激活虚拟环境
    source venv/bin/activate
    echo "✓ 已激活Python虚拟环境"
else
    echo "错误: 虚拟环境不存在!"
    echo "请先运行 setup.sh 脚本安装依赖"
    echo ""
    echo "按任意键退出..."
    read -n 1
    exit 1
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