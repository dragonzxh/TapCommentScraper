#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
print("Python版本:", sys.version)

try:
    import selenium
    print("selenium已安装, 版本:", selenium.__version__)
except ImportError:
    print("selenium未安装")

try:
    import webdriver_manager
    print("webdriver_manager已安装")
except ImportError:
    print("webdriver_manager未安装") 