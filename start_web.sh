#!/bin/bash

# 评论爬虫Web应用启动脚本

# 获取脚本所在的目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 切换到脚本所在目录
cd "$SCRIPT_DIR"

# 显示欢迎信息
echo "================================================="
echo "       评论爬虫Web应用启动器"
echo "================================================="
echo "正在启动服务..."
echo ""

# 检查虚拟环境是否存在
if [ -d "venv" ]; then
    # 激活虚拟环境
    source venv/bin/activate
    echo "✓ 已激活Python虚拟环境"
else
    echo "错误: 虚拟环境不存在!"
    echo "请先运行 setup.sh 脚本安装依赖"
    exit 1
fi

# 启动Web应用
echo "✓ 正在启动Web服务器..."
python crawler_web_start.py

# 脚本结束
echo ""
echo "Web服务器已关闭" 