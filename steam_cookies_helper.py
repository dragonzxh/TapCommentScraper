#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Steam Cookies 获取和管理工具
用于解决Steam评论爬取时的年龄验证和登录问题
"""

import os
import pickle
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path

def setup_driver(use_headless=False):
    """设置Chrome WebDriver"""
    options = webdriver.ChromeOptions()
    
    if use_headless:
        options.add_argument('--headless=new')
    
    # 基本设置
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    # 绕过反爬虫
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 设置用户代理
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 尝试显式指定Chrome路径
    import os
    if os.name == 'nt':  # Windows
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
        ]
        for path in chrome_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                options.binary_location = expanded_path
                print(f"使用Chrome路径: {expanded_path}")
                break
    elif os.name == 'posix' and os.path.exists("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        print("使用macOS系统Chrome路径")
    
    try:
        print("正在初始化ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 执行反检测JavaScript
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
            '''
        })
        
        print("ChromeDriver初始化成功")
        
        # 设置超时时间
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(60)
        driver.implicitly_wait(20)
        
        return driver
    except Exception as e:
        print(f"ChromeDriver初始化失败: {e}")
        try:
            print("尝试备用方法初始化ChromeDriver...")
            driver = webdriver.Chrome(options=options)
            print("备用方法初始化成功")
            return driver
        except Exception as e2:
            print(f"备用方法也失败: {e2}")
            raise

def login_and_save_cookies():
    """登录Steam并保存Cookies"""
    print("=" * 60)
    print("Steam Cookies 获取工具")
    print("=" * 60)
    print("此工具用于获取Steam Cookies，解决爬虫中的年龄验证问题")
    print("")
    
    # 询问是否使用无头模式
    use_headless = input("是否使用无头模式？推荐使用有头模式查看登录过程 [y/n]: ").strip().lower() == 'y'
    
    # 创建cookies目录
    Path("cookies").mkdir(exist_ok=True)
    
    # 初始化浏览器
    driver = setup_driver(use_headless)
    
    try:
        # 访问Steam登录页面
        print("\n正在访问Steam登录页面...")
        driver.get("https://store.steampowered.com/login/")
        time.sleep(3)
        
        # 等待用户输入登录信息
        print("\n请在浏览器中手动完成登录，然后按Enter继续...")
        input()
        
        # 检查是否登录成功
        print("检查登录状态...")
        account_indicators = [
            "#account_pulldown",
            ".playerAvatar",
            ".user_avatar",
            "#account_dropdown",
            ".supernav_container"
        ]
        
        login_success = False
        for indicator in account_indicators:
            elements = driver.find_elements(By.CSS_SELECTOR, indicator)
            if elements:
                login_success = True
                break
        
        if login_success:
            print("登录成功！")
            
            # 保存Cookies
            cookies = driver.get_cookies()
            cookie_path = os.path.join("cookies", "steam_cookies.pkl")
            with open(cookie_path, "wb") as f:
                pickle.dump(cookies, f)
            print(f"Cookies已保存到: {cookie_path}")
            
            # 保存人类可读的Cookies信息
            cookie_info_path = os.path.join("cookies", "steam_cookies_info.txt")
            with open(cookie_info_path, "w", encoding="utf-8") as f:
                f.write(f"保存时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"总计 {len(cookies)} 个Cookies\n\n")
                for i, cookie in enumerate(cookies, 1):
                    f.write(f"Cookie {i}:\n")
                    f.write(f"  名称: {cookie.get('name')}\n")
                    f.write(f"  域: {cookie.get('domain')}\n")
                    f.write(f"  路径: {cookie.get('path')}\n")
                    f.write(f"  过期时间: {cookie.get('expiry', 'Session')}\n")
                    f.write(f"  HttpOnly: {cookie.get('httpOnly', False)}\n")
                    f.write(f"  安全: {cookie.get('secure', False)}\n\n")
            print(f"Cookies详细信息已保存到: {cookie_info_path}")
            
            # 访问年龄验证游戏
            verify_age = input("\n是否访问年龄验证游戏以通过年龄验证？ [y/n]: ").strip().lower() == 'y'
            if verify_age:
                print("\n正在访问年龄验证游戏...")
                driver.get("https://store.steampowered.com/app/271590/Grand_Theft_Auto_V/")  # GTA5，需要年龄验证的游戏
                time.sleep(3)
                
                # 尝试通过年龄验证
                try:
                    # 尝试查找年龄选择下拉框
                    age_selects = driver.find_elements(By.CSS_SELECTOR, "select[name='ageYear']")
                    if age_selects:
                        print("检测到年龄验证页面，尝试选择年龄...")
                        driver.execute_script("document.querySelector('select[name=\"ageYear\"]').value = '1990'")
                        view_buttons = driver.find_elements(By.CSS_SELECTOR, "a.btnv6_blue_hoverfade")
                        for button in view_buttons:
                            if "view" in button.text.lower():
                                driver.execute_script("arguments[0].click();", button)
                                time.sleep(5)  # 等待页面加载
                                print("年龄验证完成！")
                                
                                # 重新保存Cookies（可能更新了验证相关Cookie）
                                cookies = driver.get_cookies()
                                with open(cookie_path, "wb") as f:
                                    pickle.dump(cookies, f)
                                print("Cookies已更新!")
                                break
                    else:
                        print("未检测到年龄验证页面，可能已经通过验证")
                except Exception as e:
                    print(f"处理年龄验证时出错: {e}")
            
            print("\nCookies获取完成！现在您可以使用这些Cookies爬取Steam评论，包括需要年龄验证的游戏")
            print("在爬虫启动前，cookies将自动加载")
            
        else:
            print("无法检测到登录状态，请确认您已成功登录")
            print("您可以重新运行此工具再次尝试")
            
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        print("\n正在关闭浏览器...")
        driver.quit()
        print("完成！")

def test_cookies():
    """测试已保存的Cookies是否有效"""
    print("=" * 60)
    print("Steam Cookies 测试工具")
    print("=" * 60)
    
    # 检查Cookies文件是否存在
    cookie_path = os.path.join("cookies", "steam_cookies.pkl")
    if not os.path.exists(cookie_path):
        print("错误: 未找到Cookies文件")
        print("请先运行login_and_save_cookies()函数获取Cookies")
        return
    
    # 询问是否使用无头模式
    use_headless = input("是否使用无头模式？推荐使用有头模式查看验证过程 [y/n]: ").strip().lower() == 'y'
    
    # 初始化浏览器
    driver = setup_driver(use_headless)
    
    try:
        # 先访问Steam主页
        print("\n正在访问Steam主页...")
        driver.get("https://store.steampowered.com")
        time.sleep(2)
        
        # 加载Cookies
        print("正在加载Cookies...")
        with open(cookie_path, "rb") as f:
            cookies = pickle.load(f)
        
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"添加Cookie时出错，但将继续: {e}")
        
        # 刷新页面
        print("刷新页面应用Cookies...")
        driver.refresh()
        time.sleep(3)
        
        # 检查是否登录
        account_indicators = [
            "#account_pulldown",
            ".playerAvatar",
            ".user_avatar",
            "#account_dropdown",
            ".supernav_container"
        ]
        
        login_success = False
        for indicator in account_indicators:
            elements = driver.find_elements(By.CSS_SELECTOR, indicator)
            if elements:
                login_success = True
                break
        
        if login_success:
            print("Cookies验证成功！您已登录")
            
            # 输入游戏ID进行测试
            game_id = input("\n请输入要测试的游戏ID（例如，3014080）: ").strip()
            
            # 访问游戏评论页面
            review_url = f"https://steamcommunity.com/app/{game_id}/reviews/?browsefilter=toprated&filterLanguage=schinese"
            print(f"\n正在访问游戏评论页面: {review_url}")
            driver.get(review_url)
            time.sleep(5)
            
            # 检查是否能够访问评论
            reviews = driver.find_elements(By.CSS_SELECTOR, ".apphub_Card")
            if reviews:
                print(f"成功加载评论！找到 {len(reviews)} 条评论")
                print("Cookies有效，可以正常爬取此游戏的评论")
            else:
                print("未找到评论元素，可能需要额外处理")
                
                # 检查是否需要年龄验证
                if "mature_content" in driver.page_source or "agecheck" in driver.page_source:
                    print("检测到年龄验证页面，您可能需要先手动通过年龄验证，或使用login_and_save_cookies()中的年龄验证功能")
                else:
                    print("未检测到年龄验证页面，可能是评论加载失败或其他问题")
                    # 保存页面源码以供分析
                    error_log_path = f"error_log_page_{game_id}.html"
                    with open(error_log_path, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    print(f"已保存页面源码到 {error_log_path} 以便分析问题")
        else:
            print("Cookies验证失败，未检测到登录状态")
            print("这可能意味着Cookies已过期或无效")
            print("建议重新运行login_and_save_cookies()函数获取最新Cookies")
    
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        print("\n正在关闭浏览器...")
        driver.quit()
        print("测试完成！")

if __name__ == "__main__":
    print("Steam Cookies工具")
    print("1. 登录并保存Cookies")
    print("2. 测试已保存的Cookies")
    print("3. 退出")
    
    choice = input("\n请选择操作 [1/2/3]: ").strip()
    
    if choice == "1":
        login_and_save_cookies()
    elif choice == "2":
        test_cookies()
    else:
        print("已退出") 