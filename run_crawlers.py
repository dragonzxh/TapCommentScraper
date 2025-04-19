#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
爬虫运行脚本
本脚本用于运行Steam、TapTap和Bilibili爬虫
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path

def ensure_dir_exists(directory):
    """确保目录存在"""
    Path(directory).mkdir(parents=True, exist_ok=True)
    print(f"目录已准备: {directory}")

def run_steam_crawler():
    """运行Steam爬虫"""
    print("\n==================== 开始运行Steam爬虫 ====================")
    try:
        # 检查game_list.txt是否存在，如果不存在则创建一个示例文件
        if not os.path.exists("game_list.txt"):
            with open("game_list.txt", "w", encoding="utf-8") as f:
                f.write("https://steamcommunity.com/app/1295660/reviews/?browsefilter=toprated&snr=1_5_100010_&filterLanguage=schinese\n")
            print("已创建game_list.txt文件，包含示例游戏链接")
        
        # 引入steam_crawler模块
        from steam_crawler import SteamCrawler
        
        # 创建爬虫实例并运行
        crawler = SteamCrawler(use_headless=False)
        
        # 检查是否已登录
        if not crawler.is_logged_in:
            print("Steam Cookie验证失败，需要重新登录")
            username = input("请输入Steam用户名: ")
            password = input("请输入Steam密码: ")
            
            if not crawler.login(username, password):
                print("登录失败，无法继续爬取")
                return False
        
        # 从game_list.txt读取游戏URL列表
        print("从game_list.txt读取游戏URL...")
        with open("game_list.txt", "r", encoding="utf-8") as f:
            game_urls = [line.strip() for line in f if line.strip()]
        
        if not game_urls:
            print("game_list.txt中没有找到游戏URL")
            return False
        
        print(f"找到 {len(game_urls)} 个游戏URL")
        
        # 爬取每个游戏的评论
        for i, url in enumerate(game_urls, 1):
            print(f"\n正在爬取第 {i}/{len(game_urls)} 个游戏: {url}")
            try:
                crawler.extract_comments(url)
            except Exception as e:
                print(f"爬取 {url} 失败: {e}")
        
        crawler.close()
        print("\nSteam爬虫运行完成")
        return True
    
    except Exception as e:
        print(f"Steam爬虫运行出错: {e}")
        return False

def run_taptap_crawler():
    """运行TapTap爬虫"""
    print("\n==================== 开始运行TapTap爬虫 ====================")
    try:
        # 引入tap_crawler模块
        from tap_crawler import TapTapCrawler
        
        # 创建并运行爬虫
        crawler = TapTapCrawler(use_headless=False)
        crawler.run()
        print("\nTapTap爬虫运行完成")
        return True
    
    except Exception as e:
        print(f"TapTap爬虫运行出错: {e}")
        return False

def run_bilibili_crawler():
    """运行Bilibili爬虫"""
    print("\n==================== 开始运行Bilibili爬虫 ====================")
    try:
        # 引入bili_crawler模块
        from bili_crawler import BiliBiliCrawler
        
        # 创建并运行爬虫
        crawler = BiliBiliCrawler(use_headless=False)
        crawler.run()
        print("\nBilibili爬虫运行完成")
        return True
    
    except Exception as e:
        print(f"Bilibili爬虫运行出错: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="游戏评论爬虫运行脚本")
    parser.add_argument("--steam", action="store_true", help="运行Steam爬虫")
    parser.add_argument("--taptap", action="store_true", help="运行TapTap爬虫")
    parser.add_argument("--bilibili", action="store_true", help="运行Bilibili爬虫")
    parser.add_argument("--all", action="store_true", help="运行所有爬虫")
    
    args = parser.parse_args()
    
    # 如果没有指定参数，显示帮助信息
    if not (args.steam or args.taptap or args.bilibili or args.all):
        parser.print_help()
        return
    
    # 创建输出目录
    ensure_dir_exists("output")
    
    # 根据参数运行相应的爬虫
    if args.all or args.steam:
        run_steam_crawler()
    
    if args.all or args.taptap:
        run_taptap_crawler()
    
    if args.all or args.bilibili:
        run_bilibili_crawler()
    
    print("\n所有爬虫任务已完成！")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行时出错: {e}")
    finally:
        print("\n程序退出") 