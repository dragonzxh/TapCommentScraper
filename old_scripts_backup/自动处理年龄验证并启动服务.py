#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自动处理年龄验证并启动Web服务工具
无需交互式选择，自动完成以下流程：
1. 获取Steam cookies（如果需要）
2. 自动处理年龄验证
3. 直接启动Web服务 (localhost:5000)
"""

import os
import sys
import time
import pickle
import subprocess
import webbrowser
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver(use_headless=True):
    """设置Chrome WebDriver"""
    options = webdriver.ChromeOptions()
    
    if use_headless:
        options.add_argument('--headless=new')
    else:
        # 在非headless模式下，设置窗口大小和位置
        options.add_argument('--window-size=1280,800')
        options.add_argument('--window-position=100,50')
        # 禁用扩展以提高稳定性
        options.add_argument('--disable-extensions')
        # 确保显示浏览器窗口
        options.add_experimental_option("detach", True)
        options.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
    
    # 基本设置
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # 绕过反爬虫
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('useAutomationExtension', False)
    
    # 设置用户代理
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        print("正在初始化Chrome浏览器...")
        # 确保使用最新版本的ChromeDriver
        service = Service(ChromeDriverManager(cache_valid_range=1).install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 执行反检测JavaScript
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
            '''
        })
        
        # 设置超时时间
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(60)
        driver.implicitly_wait(20)
        
        # 非headless模式下，最大化窗口
        if not use_headless:
            driver.maximize_window()
            print("已打开Chrome浏览器窗口")
        
        return driver
    except Exception as e:
        print(f"浏览器初始化失败: {e}")
        try:
            print("尝试备用方法...")
            if not use_headless:
                print("确保已安装Chrome浏览器并且版本与ChromeDriver兼容")
            driver = webdriver.Chrome(options=options)
            return driver
        except Exception as e2:
            print(f"备用方法也失败: {e2}")
            print("请确保已安装Chrome浏览器，并且系统环境允许显示GUI窗口")
            sys.exit(1)

def load_cookies(driver):
    """加载已保存的Cookies"""
    cookies_dir = "cookies"
    cookies_file = os.path.join(cookies_dir, "steam_cookies.pkl")
    
    # 确保cookies目录存在
    Path(cookies_dir).mkdir(exist_ok=True)
    
    if not os.path.exists(cookies_file):
        print("未找到保存的Cookies，将创建新的")
        return False
    
    try:
        print("正在加载Cookies...")
        # 先访问Steam网站
        driver.get("https://store.steampowered.com")
        time.sleep(2)
        
        # 加载Cookie
        with open(cookies_file, "rb") as f:
            cookies = pickle.load(f)
        
        success_count = 0
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
                success_count += 1
            except Exception as e:
                print(f"添加Cookie时出错: {e}")
        
        print(f"成功加载 {success_count}/{len(cookies)} 个Cookie")
        
        # 刷新页面应用cookies
        driver.refresh()
        time.sleep(3)
        
        return True
    except Exception as e:
        print(f"加载Cookies失败: {e}")
        return False

def save_cookies(driver):
    """保存当前的Cookie到文件"""
    try:
        cookies_dir = "cookies"
        cookies_file = os.path.join(cookies_dir, "steam_cookies.pkl")
        
        # 确保cookies目录存在
        Path(cookies_dir).mkdir(exist_ok=True)
        
        # 保存Cookies
        cookies = driver.get_cookies()
        with open(cookies_file, "wb") as f:
            pickle.dump(cookies, f)
        
        print(f"已保存 {len(cookies)} 个Cookie到 {cookies_file}")
        return True
    except Exception as e:
        print(f"保存Cookie失败: {e}")
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
        
        print("未检测到Steam登录状态")
        return False
    except Exception as e:
        print(f"检查登录状态时出错: {e}")
        return False

def handle_age_verification(driver):
    """自动处理年龄验证 - 此版本不再处理固定的游戏列表"""
    # 仅保存当前的Cookies
    save_cookies(driver)
    print("\n已保存当前的Cookies，Web服务会使用这些Cookies进行验证")

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
            # 在Unix系统上，使用nohup防止进程在终端关闭时停止
            subprocess.Popen(["nohup", "python3", "crawler_web_start.py", "&"], 
                            stdout=open("logs/web_server.log", "w"),
                            stderr=subprocess.STDOUT,
                            preexec_fn=os.setpgrp)
        
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
    try:
        print("=" * 60)
        print("自动启动Web服务工具")
        print("=" * 60)
        print("此工具将自动完成以下操作:")
        print("1. 加载Steam Cookies并验证登录状态")
        print("2. 保存Cookies供Web服务器使用")
        print("3. 启动Web服务器并打开浏览器")
        print("=" * 60)
        
        # 创建必要的目录
        for directory in ["cookies", "output", "logs"]:
            Path(directory).mkdir(exist_ok=True)
        
        # 确认是否使用无头模式
        use_headless = False  # 强制使用有头模式
        print(f"将使用{'无头' if use_headless else '有界面'}模式打开浏览器")
        
        # 启动浏览器
        driver = setup_driver(use_headless=use_headless)
        
        # 加载Cookies并检查登录状态
        cookies_loaded = load_cookies(driver)
        is_logged_in = check_login_status(driver)
        
        if not is_logged_in:
            print("\n未检测到Steam登录状态，请先在浏览器中登录Steam")
            print("正在打开Steam登录页面...")
            driver.get("https://store.steampowered.com/login/")
            
            # 等待用户登录
            print("\n请在浏览器中完成登录，然后按Enter继续...")
            input("(如果没有看到浏览器窗口，请检查任务栏或其他桌面空间)")
            
            # 重新检查登录状态
            is_logged_in = check_login_status(driver)
            if is_logged_in:
                print("登录成功！")
                save_cookies(driver)
            else:
                print("登录失败，程序无法继续")
                driver.quit()
                return
        
        # 保存cookies
        handle_age_verification(driver)
        
        # 关闭浏览器
        print("处理完成，正在关闭浏览器...")
        driver.quit()
        print("浏览器已关闭")
        
        # 启动Web服务器
        start_web_server()
        
        # 保持程序运行直到用户中断
        try:
            print("\n程序将保持运行状态。要退出请按Ctrl+C")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n程序已结束，但Web服务器仍在后台运行")
            print("可以继续访问 http://localhost:5000 使用Web界面")
    
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    
    except KeyboardInterrupt:
        print("\n程序已被用户中断")
    
    finally:
        print("程序结束")

if __name__ == "__main__":
    main() 