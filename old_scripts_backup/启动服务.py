#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
启动Steam评论爬虫Web服务的脚本
自动完成以下流程：
1. 登录Steam账号并获取Cookies
2. 自动处理年龄验证
3. 启动Web服务 (localhost:5000)
"""

import os
import sys
import subprocess
import time
import webbrowser
import json
import pickle
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def create_directories():
    """创建必要的目录"""
    directories = ["cookies", "output", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"确保目录存在: {directory}")

def setup_driver(use_headless=False):
    """设置并初始化WebDriver"""
    options = Options()
    
    if use_headless:
        options.add_argument('--headless=new')
    else:
        # 在非headless模式下，设置窗口大小和位置
        options.add_argument('--window-size=1280,800')
        options.add_argument('--window-position=100,50')
        
    # 基本设置
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # 添加反检测参数
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 设置用户代理
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36')
    
    try:
        print("初始化Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 设置页面加载超时
        driver.set_page_load_timeout(30)
        
        # 执行JavaScript来绕过反爬虫检测
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("WebDriver初始化成功")
        return driver
    except Exception as e:
        print(f"初始化WebDriver时出错: {str(e)}")
        raise

def save_cookies(driver):
    """保存cookies到文件（同时保存多种格式）"""
    try:
        # 创建cookies目录
        Path("cookies").mkdir(exist_ok=True)
        
        cookies = driver.get_cookies()
        print(f"获取到 {len(cookies)} 个cookies")
        
        # 保存为JSON格式
        with open(os.path.join('cookies', 'steam_cookies.json'), 'w') as f:
            json.dump(cookies, f)
        
        # 同时保存为pickle格式以兼容旧代码
        with open(os.path.join('cookies', 'steam_cookies.pkl'), 'wb') as f:
            pickle.dump(cookies, f)
            
        print(f"已成功保存cookies到文件")
        return True
    except Exception as e:
        print(f"保存cookies时出错: {str(e)}")
        return False

def check_login_status(driver):
    """检查是否已登录Steam"""
    try:
        # 访问Steam主页
        driver.get("https://store.steampowered.com")
        time.sleep(3)
        
        # 检查是否存在登录后才会出现的元素
        account_indicators = [
            "#account_pulldown",
            ".playerAvatar",
            ".user_avatar",
            "#account_dropdown",
            ".supernav_container"
        ]
        
        for indicator in account_indicators:
            elements = driver.find_elements(By.CSS_SELECTOR, indicator)
            if elements and any(e.is_displayed() for e in elements):
                print("已检测到Steam登录状态")
                return True
        
        print("未检测到Steam登录状态，需要登录")
        return False
    except Exception as e:
        print(f"检查登录状态时出错: {str(e)}")
        return False

def steam_login(driver):
    """打开Steam登录界面，等待用户手动登录"""
    try:
        print("\n需要登录Steam账号以获取必要的cookies和验证年龄限制")
        print("即将打开浏览器窗口，请在窗口中登录您的Steam账号")
        
        # 打开Steam登录页面
        driver.get("https://store.steampowered.com/login/")
        
        # 等待用户登录完成
        print("\n请在浏览器窗口中登录Steam账号")
        print("登录后请勿关闭浏览器窗口，程序将自动检测登录状态")
        
        # 等待登录按钮消失或账户下拉菜单出现
        max_wait_time = 300  # 最长等待5分钟
        check_interval = 5  # 每5秒检查一次
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            if check_login_status(driver):
                print("登录成功！")
                # 保存cookies以供后续使用
                save_cookies(driver)
                return True
                
            print(f"等待登录中...已等待 {elapsed_time} 秒")
            time.sleep(check_interval)
            elapsed_time += check_interval
        
        print("等待登录超时，请重新运行程序并尝试登录")
        return False
        
    except Exception as e:
        print(f"登录过程出错: {str(e)}")
        return False

def handle_age_verification(driver):
    """使用age_verification模块处理Steam游戏的年龄验证"""
    try:
        # 导入age_verification模块
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "age_verification", 
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "age_verification.py")
        )
        
        if not spec:
            print("未找到age_verification模块，无法处理年龄验证")
            return False
            
        age_verification = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(age_verification)
        
        # 验证几个常见的需要年龄验证的游戏
        test_games = [
            {"id": "271590", "name": "GTA5"},
            {"id": "1091500", "name": "赛博朋克2077"},
            {"id": "3014080", "name": "传送门：革命"}  # 您访问的游戏
        ]
        
        success_count = 0
        
        for game in test_games:
            print(f"\n尝试处理 {game['name']} (ID: {game['id']}) 的年龄验证")
            result = age_verification.handle_age_verification_for_game(game['id'], use_headless=False)
            
            if result:
                print(f"✅ {game['name']} 年龄验证成功")
                success_count += 1
            else:
                print(f"❌ {game['name']} 年龄验证失败")
        
        print(f"\n共处理 {len(test_games)} 款游戏的年龄验证，成功 {success_count} 款")
        return success_count > 0
        
    except Exception as e:
        print(f"年龄验证处理出错: {str(e)}")
        return False

def start_web_server():
    """启动Web服务器并打开浏览器"""
    try:
        print("\n正在启动Web服务器...")
        
        # 检查crawler_web_start.py是否存在
        if not os.path.exists("crawler_web_start.py"):
            print("错误: 未找到Web服务启动脚本 crawler_web_start.py")
            return False
        
        # 创建子进程运行Web服务
        if os.name == 'nt':  # Windows
            # 在Windows上，使用启动窗口运行服务器
            subprocess.Popen(["python", "crawler_web_start.py"], 
                            creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:  # macOS/Linux
            # 创建logs目录
            Path("logs").mkdir(exist_ok=True)
            
            # 在Unix系统上，使用nohup防止进程在终端关闭时停止
            subprocess.Popen(["python3", "crawler_web_start.py"], 
                            stdout=open("logs/web_server.log", "w"),
                            stderr=subprocess.STDOUT)
        
        print("Web服务器已启动，等待服务就绪...")
        time.sleep(5)  # 等待服务器启动
        
        # 打开浏览器访问Web界面
        url = "http://localhost:5000"
        print(f"正在浏览器中打开: {url}")
        webbrowser.open(url)
        
        print("\n服务已启动，可以在浏览器中访问 http://localhost:5000")
        print("按Ctrl+C可以结束此程序，但Web服务器将继续在后台运行")
        return True
    
    except Exception as e:
        print(f"启动Web服务器失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("Steam评论爬虫Web服务启动工具")
    print("=" * 60)
    
    # 创建必要的目录
    create_directories()
    
    # 初始化浏览器
    driver = None
    try:
        driver = setup_driver(use_headless=False)
        
        # 1. 检查登录状态，如果未登录则登录
        if not check_login_status(driver):
            print("需要登录Steam账号")
            if not steam_login(driver):
                print("登录失败，无法继续")
                return
        else:
            print("已经处于登录状态，继续处理")
            # 即使已登录，也保存一次cookies确保最新
            save_cookies(driver)
        
        # 2. 处理游戏年龄验证
        print("\n开始处理游戏年龄验证...")
        handle_age_verification(driver)
        
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
    finally:
        # 关闭浏览器
        if driver:
            print("关闭浏览器...")
            driver.quit()
    
    # 3. 启动Web服务
    start_web_server()
    
    print("\n服务已启动完成。请在浏览器中使用体验。")
    print("=" * 60)
    
    try:
        # 保持程序运行，等待用户手动结束
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n程序已通过Ctrl+C结束，但Web服务会继续在后台运行")

if __name__ == "__main__":
    main() 