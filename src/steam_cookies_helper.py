#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Steam Cookies 获取和管理工具
用于解决Steam评论爬取时的年龄验证和登录问题
"""

import os
import pickle
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
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
    
    # 为macOS找到正确的Chrome路径
    if os.name == 'posix' and os.path.exists("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        print("使用macOS系统Chrome路径")
    
    try:
        print("正在初始化ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
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
            "#account_dropdown"
        ]
        
        login_success = False
        for indicator in account_indicators:
            elements = driver.find_elements(By.CSS_SELECTOR, indicator)
            if elements:
                login_success = True
                break
        
        if login_success:
            print("登录成功！正在访问主要Steam站点初始化会话...")
            
            # 访问主要Steam域名来初始化会话
            domains = [
                "https://store.steampowered.com/",
                "https://steamcommunity.com/",
                "https://steamcommunity.com/my/"  # 访问个人资料页面以完全激活会话
            ]
            
            for domain in domains:
                try:
                    print(f"访问 {domain}...")
                    driver.get(domain)
                    time.sleep(3)  # 等待页面加载和会话处理
                except Exception as e:
                    print(f"访问 {domain} 时出错: {e}")
            
            # 保存Cookies - 使用两种格式
            cookies = driver.get_cookies()
            
            # 检查是否包含关键的steamLoginSecure cookie
            has_login_secure = False
            for cookie in cookies:
                if cookie.get('name') == 'steamLoginSecure':
                    has_login_secure = True
                    print(f"√ 成功获取steamLoginSecure cookie (domain: {cookie.get('domain')})")
                    break
            
            if not has_login_secure:
                print("⚠️ 警告: 未获取到steamLoginSecure cookie，登录可能无效")
                print("请重新尝试登录过程")
                return False
            
            # 1. Pickle格式 (二进制)
            cookie_path = os.path.join("cookies", "steam_cookies.pkl")
            with open(cookie_path, "wb") as f:
                pickle.dump(cookies, f)
            print(f"Cookies已保存到: {cookie_path}")
            
            # 2. JSON格式 (文本格式，便于查看和编辑)
            json_path = os.path.join("cookies", "steam_cookies.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(cookies, f)
            print(f"Cookies已保存为JSON格式: {json_path}")
            
            # 保存人类可读的Cookies信息
            cookie_info_path = os.path.join("logs", "steam_cookies_info.txt")
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
                print("\n正在访问GTA5页面进行年龄验证...")
                driver.get("https://store.steampowered.com/app/271590/Grand_Theft_Auto_V/")
                time.sleep(3)
                
                # 检查最终结果
                if "agecheck" not in driver.current_url.lower():
                    print("已成功通过年龄验证！")
                else:
                    print("需要手动完成验证...")
                    input("在浏览器中手动完成年龄验证后，按Enter继续...")
                    
                    # 手动验证后，重新保存Cookies
                    cookies = driver.get_cookies()
                    with open(cookie_path, "wb") as f:
                        pickle.dump(cookies, f)
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(cookies, f)
                    print("手动验证后Cookies已更新！")
            
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
        
        # 检查是否存在steamLoginSecure cookie
        has_login_secure = False
        for cookie in cookies:
            if cookie.get('name') == 'steamLoginSecure':
                has_login_secure = True
                print(f"√ 检测到steamLoginSecure cookie (domain: {cookie.get('domain')})")
                break
        
        if not has_login_secure:
            print("⚠️ 警告: 未检测到steamLoginSecure cookie，可能无法正常登录")
            print("建议重新运行login_and_save_cookies()获取cookies")
            driver.quit()
            return
        
        for cookie in cookies:
            try:
                # 尝试使用简化的cookie添加方式
                simplified_cookie = {
                    'name': cookie.get('name'),
                    'value': cookie.get('value')
                }
                
                # 对于关键cookie，确保domain是正确的
                if cookie.get('name') in ['steamLoginSecure', 'sessionid'] and 'domain' in cookie:
                    domain = cookie.get('domain')
                    if 'steam' in domain:
                        simplified_cookie['domain'] = domain
                
                driver.add_cookie(simplified_cookie)
            except Exception as e:
                print(f"添加Cookie时出错，但将继续: {e}")
        
        # 刷新页面
        print("刷新页面应用Cookies...")
        driver.refresh()
        time.sleep(3)
        
        # 检查是否登录 - 寻找账户菜单
        account_indicators = [
            "#account_pulldown",
            ".playerAvatar",
            ".user_avatar",
            "#account_dropdown"
        ]
        
        login_success = False
        for indicator in account_indicators:
            elements = driver.find_elements(By.CSS_SELECTOR, indicator)
            if elements and len(elements) > 0 and elements[0].is_displayed():
                login_success = True
                print(f"✓ 找到登录状态指示器: {indicator}")
                break
        
        if login_success:
            print("✅ Cookies验证成功！您已登录")
            
            # 尝试访问用户资料页面确认登录状态
            try:
                print("\n尝试访问用户资料页面...")
                driver.get("https://steamcommunity.com/my/")
                time.sleep(3)
                
                if "login" not in driver.current_url.lower():
                    print("✅ 成功访问用户资料页面，确认登录有效")
                else:
                    print("❌ 无法访问用户资料页面，登录可能部分有效")
            except Exception as e:
                print(f"访问用户资料页面时出错: {e}")
            
            print("\nCookies测试完成！可以用于爬取Steam评论")
        else:
            print("❌ Cookies验证失败，未检测到登录状态")
            print("这可能意味着Cookies已过期或无效")
            print("建议重新运行login_and_save_cookies()函数获取最新Cookies")
    
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        print("\n正在关闭浏览器...")
        driver.quit()
        print("测试完成！")

if __name__ == "__main__":
    try:
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
    except Exception as e:
        print(f"\n程序遇到错误: {e}")
        print("如果您在Windows上看到中文乱码，请以管理员身份运行cmd并执行 'chcp 65001' 后重试") 