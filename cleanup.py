#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
清理脚本
用于删除不需要的前端文件，只保留爬虫核心功能
"""

import os
import shutil
import sys

# 需要删除的目录
DIRS_TO_DELETE = [
    "src",
    "dist",
    "build",
    "node_modules",
    "public",
    ".vscode"
]

# 需要删除的文件类型
FILE_EXTENSIONS_TO_DELETE = [
    ".js",
    ".vue",
    ".json",
    ".html",
    ".css",
    ".scss",
    ".ts",
    ".tsx"
]

# 需要删除的特定文件
FILES_TO_DELETE = [
    "package.json",
    "package-lock.json",
    "vite.config.js",
    "vue.config.js",
    "tsconfig.json",
    "jsconfig.json",
    "babel.config.js",
    "webpack.config.js",
    "index.html",
    "remote_App.vue",
    "SteamCrawler.vue",
    "crawler.js"
]

# 需要保留的爬虫核心文件
FILES_TO_KEEP = [
    "steam_crawler.py",
    "tap_crawler.py",
    "bili_crawler.py",
    "crawler_base.py",
    "test_steam.py",
    "test_crawler.py",
    "requirements.txt",
    "requirements_clean.txt",
    "run_crawlers.py",
    "main.py",
    "Tapcomment.py",
    "Bilicomment.py",
    "README.md",
    "LICENSE",
    ".gitignore",
    "cleanup.py"
]

def is_file_to_delete(filename):
    """检查文件是否需要删除"""
    # 检查是否是需要保留的文件
    if filename in FILES_TO_KEEP:
        return False
    
    # 检查是否是需要删除的文件
    if filename in FILES_TO_DELETE:
        return True
    
    # 检查文件扩展名
    _, ext = os.path.splitext(filename)
    if ext.lower() in FILE_EXTENSIONS_TO_DELETE:
        return True
    
    return False

def cleanup():
    """清理不需要的前端文件"""
    print("开始清理不需要的前端文件...")
    
    # 获取当前目录
    current_dir = os.getcwd()
    print(f"当前目录: {current_dir}")
    
    # 删除目录
    for dir_name in DIRS_TO_DELETE:
        dir_path = os.path.join(current_dir, dir_name)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"删除目录: {dir_path}")
            try:
                shutil.rmtree(dir_path)
            except Exception as e:
                print(f"删除目录 {dir_path} 失败: {e}")
    
    # 遍历当前目录下的文件
    for filename in os.listdir(current_dir):
        file_path = os.path.join(current_dir, filename)
        
        # 跳过目录
        if os.path.isdir(file_path):
            continue
        
        # 检查文件是否需要删除
        if is_file_to_delete(filename):
            print(f"删除文件: {file_path}")
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"删除文件 {file_path} 失败: {e}")
    
    print("\n清理完成！保留了以下爬虫核心文件:")
    for filename in FILES_TO_KEEP:
        file_path = os.path.join(current_dir, filename)
        if os.path.exists(file_path):
            print(f"- {filename}")
    
    print("\n现在您可以使用以下命令安装依赖并运行爬虫:")
    print("pip install -r requirements_clean.txt")
    print("python run_crawlers.py --help")

if __name__ == "__main__":
    # 安全提示
    print("警告: 此脚本将删除所有前端相关文件，只保留爬虫核心功能")
    print("请确保您已备份重要数据！")
    
    response = input("是否继续? (y/n): ")
    if response.lower() != 'y':
        print("操作已取消")
        sys.exit(0)
    
    # 执行清理
    cleanup() 