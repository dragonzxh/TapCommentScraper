#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
爬虫Web服务器启动脚本
"""

import sys
import os

# 将当前目录添加到模块搜索路径
sys.path.insert(0, os.path.abspath('.'))

# 导入应用并启动
from crawler_web.app import main

if __name__ == "__main__":
    main()