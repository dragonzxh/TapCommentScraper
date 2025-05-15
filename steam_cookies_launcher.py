#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Steam爬虫与Cookies工具启动器
方便用户选择运行不同的功能
"""

import os
import sys
import importlib.util
import subprocess
import time
from pathlib import Path

def check_module_installed(module_name):
    """检查模块是否已安装"""
    spec = importlib.util.find_spec(module_name)
    return spec is not None

def install_dependency(package):
    """安装依赖包"""
    print(f"正在安装依赖: {package}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    print(f"{package} 已安装")

def check_dependencies():
    """检查并安装必要的依赖"""
    required_packages = [
        "selenium",
        "webdriver_manager",
        "beautifulsoup4",
        "requests"
    ]
    
    for package in required_packages:
        if not check_module_installed(package):
            print(f"缺少依赖: {package}")
            try:
                install_dependency(package)
            except Exception as e:
                print(f"无法安装 {package}: {e}")
                return False
    
    return True

def create_directories():
    """创建必要的目录"""
    directories = ["cookies", "output", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"目录已就绪: {directory}")

def clear_screen():
    """清除屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def main_menu():
    """显示主菜单"""
    while True:
        clear_screen()
        print("=" * 60)
        print("Steam爬虫与Cookie工具")
        print("=" * 60)
        print("1. 运行Cookies获取工具（解决年龄验证问题）")
        print("2. 运行Steam评论爬虫")
        print("3. 测试已保存的Cookies")
        print("4. 帮助与说明")
        print("0. 退出")
        print("=" * 60)
        
        choice = input("\n请选择功能 [0-4]: ").strip()
        
        if choice == "1":
            run_cookies_helper()
        elif choice == "2":
            run_steam_crawler()
        elif choice == "3":
            test_cookies()
        elif choice == "4":
            show_help()
        elif choice == "0":
            print("感谢使用，再见！")
            break
        else:
            print("无效选择，请重试")
            time.sleep(1)

def run_cookies_helper():
    """运行Steam Cookies获取工具"""
    clear_screen()
    print("=" * 60)
    print("Steam Cookies获取工具")
    print("=" * 60)
    print("此工具用于解决Steam爬虫中的年龄验证问题")
    print("将会打开浏览器，引导您登录Steam并保存cookies")
    print("=" * 60)
    
    if not os.path.exists("steam_cookies_helper.py"):
        print("错误: 未找到steam_cookies_helper.py文件")
        print("请确保该文件存在于当前目录")
        input("按Enter键返回主菜单...")
        return
    
    input("按Enter键启动Cookies获取工具...")
    
    # 直接运行cookies获取工具，不使用后台或start方式
    try:
        # 导入并直接执行模块
        print("正在启动Steam Cookies工具...")
        
        # 方法1：直接使用importlib执行模块
        import importlib.util
        spec = importlib.util.spec_from_file_location("steam_cookies_helper", "steam_cookies_helper.py")
        cookies_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cookies_module)
        
    except Exception as e:
        print(f"启动工具时出错: {e}")
        print("尝试直接执行脚本...")
        
        # 方法2：使用os.system执行（不使用后台运行）
        if os.name == 'nt':  # Windows
            os.system("python steam_cookies_helper.py")
        else:  # macOS/Linux
            os.system("python3 steam_cookies_helper.py")
    
    input("\n操作完成，按Enter键返回主菜单...")

def run_steam_crawler():
    """运行Steam评论爬虫"""
    clear_screen()
    print("=" * 60)
    print("Steam评论爬虫")
    print("=" * 60)
    print("此工具用于爬取Steam游戏评论")
    print("=" * 60)
    
    if not os.path.exists("steam_crawler.py"):
        print("错误: 未找到steam_crawler.py文件")
        print("请确保该文件存在于当前目录")
        input("按Enter键返回主菜单...")
        return
    
    # 检查是否存在cookies
    cookies_path = os.path.join("cookies", "steam_cookies.pkl")
    if not os.path.exists(cookies_path):
        print("注意: 未检测到已保存的Steam cookies")
        print("这可能导致无法获取需要年龄验证的游戏评论")
        print("建议先运行选项1获取cookies")
        
        continue_anyway = input("\n是否仍要继续? [y/n]: ").strip().lower() == 'y'
        if not continue_anyway:
            return
    
    input("\n按Enter键启动Steam评论爬虫...")
    
    # 运行爬虫
    if os.name == 'nt':  # Windows
        os.system("python steam_crawler.py")
    else:  # macOS/Linux
        os.system("python3 steam_crawler.py")
    
    input("\n爬虫操作完成，按Enter键返回主菜单...")

def test_cookies():
    """测试已保存的Cookies"""
    clear_screen()
    print("=" * 60)
    print("Steam Cookies测试")
    print("=" * 60)
    
    cookies_path = os.path.join("cookies", "steam_cookies.pkl")
    if not os.path.exists(cookies_path):
        print("错误: 未找到已保存的Steam cookies")
        print("请先运行选项1获取cookies")
        input("按Enter键返回主菜单...")
        return
    
    if not os.path.exists("steam_cookies_helper.py"):
        print("错误: 未找到steam_cookies_helper.py文件")
        print("请确保该文件存在于当前目录")
        input("按Enter键返回主菜单...")
        return
    
    print("将启动Cookies测试功能，检查已保存的cookies是否有效")
    input("按Enter键开始测试...")
    
    # 导入cookies辅助工具并运行测试
    try:
        sys.path.append(os.getcwd())
        import steam_cookies_helper
        steam_cookies_helper.test_cookies()
    except Exception as e:
        print(f"测试过程中出错: {e}")
        print("尝试直接启动测试工具...")
        
        # 备用方法：直接启动测试工具
        try:
            exec_code = """
import steam_cookies_helper
steam_cookies_helper.test_cookies()
            """
            exec(exec_code)
        except Exception as e2:
            print(f"备用方法也失败: {e2}")
            
            # 最后尝试：使用命令行运行
            if os.name == 'nt':  # Windows
                os.system('python -c "import steam_cookies_helper; steam_cookies_helper.test_cookies()"')
            else:  # macOS/Linux
                os.system('python3 -c "import steam_cookies_helper; steam_cookies_helper.test_cookies()"')
    
    input("\n测试完成，按Enter键返回主菜单...")

def show_help():
    """显示帮助信息"""
    clear_screen()
    print("=" * 60)
    print("Steam爬虫与Cookie工具 - 帮助说明")
    print("=" * 60)
    print("这套工具用于爬取Steam游戏评论，特别是解决年龄验证问题")
    print("\n使用步骤:")
    print("1. 首先运行「Cookies获取工具」，登录您的Steam账号")
    print("   - 这将保存登录状态，用于绕过年龄验证")
    print("   - 如果您需要爬取有年龄限制的游戏，务必完成此步骤")
    print("\n2. 运行「Steam评论爬虫」获取游戏评论")
    print("   - 可以输入游戏ID或完整的评论页面URL")
    print("   - 爬取结果会保存在output目录下")
    print("\n3. 如果遇到问题，可使用「测试已保存的Cookies」功能")
    print("   - 这将检查您的登录状态是否有效")
    print("   - 可测试特定游戏的评论是否能正常获取")
    print("\n常见问题:")
    print("Q: 为什么有些游戏评论无法获取？")
    print("A: 可能是该游戏需要年龄验证，请先使用Cookies获取工具")
    print("\nQ: 爬虫报错或崩溃怎么办？")
    print("A: 可以尝试以下方法:")
    print("   - 使用非无头模式运行，观察浏览器加载情况")
    print("   - 检查Chrome浏览器版本是否兼容")
    print("   - 查看error_log.txt了解详细错误信息")
    print("\nQ: cookies失效怎么办？")
    print("A: Steam cookies通常有效期较长，但如果失效，请重新运行Cookies获取工具")
    print("=" * 60)
    
    input("\n按Enter键返回主菜单...")

if __name__ == "__main__":
    print("初始化中...")
    
    # 检查依赖
    if not check_dependencies():
        print("缺少必要的依赖，程序无法正常运行")
        print("请手动安装以下包: selenium, webdriver_manager, beautifulsoup4, requests")
        input("按Enter键退出...")
        sys.exit(1)
    
    # 创建必要的目录
    create_directories()
    
    # 显示主菜单
    main_menu() 