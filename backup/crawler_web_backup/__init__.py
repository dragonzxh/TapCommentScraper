#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
游戏评论爬虫Web应用包
"""

# Windows中文环境编码修复
import sys
import locale

# 设置控制台输出编码
try:
    if sys.platform.startswith('win'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    # Python 3.6及以下版本不支持reconfigure方法
    pass 