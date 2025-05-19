#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Steam爬虫配置模块 - 包含常量和配置参数
"""

import os
from pathlib import Path

# 路径配置
COOKIES_DIR = "cookies"
COOKIES_FILE = "steam_cookies.pkl"
JSON_COOKIES_FILE = "steam_cookies.json"
COOKIES_INFO_FILE = "steam_cookies_info.txt"
HELPER_FILE = "steam_cookies_helper.py"
OUTPUT_DIR = "output"

# 创建必要的目录
Path(COOKIES_DIR).mkdir(exist_ok=True)
Path(OUTPUT_DIR).mkdir(exist_ok=True)

# 超时设置
PAGE_LOAD_TIMEOUT = 60  # 秒
SCRIPT_TIMEOUT = 60  # 秒
IMPLICIT_WAIT = 20  # 秒
SCROLL_PAUSE_TIME = 1  # 秒

# 批处理设置
BATCH_SIZE = 10  # 每批处理的评论数量
MAX_RETRIES = 3  # 最大重试次数

# Chrome路径 - 根据操作系统选择
CHROME_PATHS = {
    "windows": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
    ],
    "mac": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
}

# 用户代理
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# 确认是否检查到steam_cookies_helper
has_cookies_helper = os.path.exists(HELPER_FILE)

# Steam URL 设置
STEAM_STORE_URL = "https://store.steampowered.com"
STEAM_COMMUNITY_URL = "https://steamcommunity.com"
STEAM_LOGIN_URL = f"{STEAM_STORE_URL}/login/"

# 年龄验证游戏URL - 用于测试
AGE_VERIFICATION_GAME_URL = "https://store.steampowered.com/app/271590/Grand_Theft_Auto_V/"

# CSS选择器
ACCOUNT_INDICATORS = [
    "#account_pulldown",
    ".playerAvatar",
    ".user_avatar",
    "#account_dropdown"
]

# 游戏标题选择器
TITLE_SELECTORS = [
    ".apphub_AppName",
    "#appHubAppName",
    ".game_title",
    ".game_name",
    ".pageheader",
    "h1", 
    ".game_description_title",
    "[itemprop='name']"
] 