#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
爬虫Web服务器启动脚本
"""

import sys
import os

# 检查Python版本
if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 6):
    print("错误: 需要Python 3.6或更高版本")
    print("当前Python版本: {}.{}.{}".format(sys.version_info[0], sys.version_info[1], sys.version_info[2]))
    print("请使用Python 3.6+运行此程序，例如: python3 crawler_web_start.py")
    sys.exit(1)

# 将当前目录添加到模块搜索路径
sys.path.insert(0, os.path.abspath('.'))

# 将crawler_web目录添加到模块搜索路径
crawler_web_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crawler_web')
sys.path.insert(0, crawler_web_path)

try:
    # 直接导入app模块中的main函数
    from app import main
except ImportError as e:
    print("错误: 无法导入模块 - {}".format(e))
    print("\n尝试以下解决方案:")
    print("1. 确保已激活虚拟环境: source venv/bin/activate (Linux/Mac) 或 venv\\Scripts\\activate (Windows)")
    print("2. 尝试直接运行app.py: cd crawler_web && python app.py")
    print("3. 检查是否已安装所有依赖: pip install -r requirements.txt")
    print("4. 详细安装说明请参考USAGE.md文件")
    sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("启动服务器时出错: {}".format(e))
        print("请检查是否已安装所有依赖和系统要求")
        sys.exit(1)