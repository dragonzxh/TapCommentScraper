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
    
    try:
        print("正在初始化Chrome浏览器...")
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
        
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(60)
        driver.implicitly_wait(20)
        
        return driver
    except Exception as e:
        print(f"浏览器初始化失败: {e}")
        try:
            print("尝试备用方法...")
            driver = webdriver.Chrome(options=options)
            return driver
        except Exception as e2:
            print(f"备用方法也失败: {e2}")
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
    """自动处理多个需要年龄验证的游戏"""
    # 需要年龄验证的游戏列表
    age_restricted_games = [
        {"name": "GTA5", "url": "https://store.steampowered.com/app/271590/Grand_Theft_Auto_V/"},
        {"name": "赛博朋克2077", "url": "https://store.steampowered.com/app/1091500/Cyberpunk_2077/"},
        {"name": "巫师3", "url": "https://store.steampowered.com/app/292030/The_Witcher_3_Wild_Hunt/"},
        {"name": "只狼", "url": "https://store.steampowered.com/app/814380/Sekiro_Shadows_Die_Twice__GOTY_Edition/"},
        {"name": "鬼泣5", "url": "https://store.steampowered.com/app/601150/Devil_May_Cry_5/"}
    ]
    
    for game in age_restricted_games:
        try:
            print(f"\n正在处理游戏 {game['name']} 的年龄验证...")
            driver.get(game["url"])
            time.sleep(3)
            
            # 检查是否需要年龄验证
            age_indicators = ["mature_content", "agecheck", "age_gate", "年龄验证"]
            page_source_lower = driver.page_source.lower()
            
            if any(indicator in page_source_lower for indicator in age_indicators):
                print(f"检测到 {game['name']} 需要年龄验证，尝试处理...")
                
                # 方法1：最新版Steam的三选择框验证
                try:
                    day_select = driver.find_element(By.ID, "ageDay")
                    month_select = driver.find_element(By.ID, "ageMonth")
                    year_select = driver.find_element(By.ID, "ageYear")
                    
                    driver.execute_script("arguments[0].value = '1';", day_select)
                    driver.execute_script("arguments[0].value = 'January';", month_select)
                    driver.execute_script("arguments[0].value = '1990';", year_select)
                    
                    submit_button = driver.find_element(By.CSS_SELECTOR, ".btnv6_blue_hoverfade")
                    driver.execute_script("arguments[0].click();", submit_button)
                    time.sleep(5)
                    
                    # 验证是否成功
                    if "agecheck" not in driver.current_url.lower():
                        print(f"{game['name']} 年龄验证成功！")
                        save_cookies(driver)  # 保存更新的Cookies
                except Exception as e:
                    print(f"方法1失败: {e}")
                
                # 方法2：旧版Steam的年份选择
                if "agecheck" in driver.current_url.lower() or any(indicator in driver.page_source.lower() for indicator in age_indicators):
                    try:
                        age_selects = driver.find_elements(By.CSS_SELECTOR, "select[name='ageYear']")
                        if age_selects:
                            for age_select in age_selects:
                                if age_select.is_displayed():
                                    driver.execute_script("arguments[0].value = '1990'", age_select)
                                    
                                    view_buttons = driver.find_elements(By.CSS_SELECTOR, "a.btnv6_blue_hoverfade, [type='submit']")
                                    for button in view_buttons:
                                        if button.is_displayed():
                                            driver.execute_script("arguments[0].click();", button)
                                            time.sleep(5)
                                            
                                            # 验证是否成功
                                            if "agecheck" not in driver.current_url.lower():
                                                print(f"{game['name']} 年龄验证成功！")
                                                save_cookies(driver)  # 保存更新的Cookies
                                                break
                    except Exception as e:
                        print(f"方法2失败: {e}")
                
                # 方法3：简化的按钮点击验证
                if "agecheck" in driver.current_url.lower() or any(indicator in driver.page_source.lower() for indicator in age_indicators):
                    try:
                        buttons = driver.find_elements(By.CSS_SELECTOR, ".agegate_text_container.btns a, .agegate_btn_container .btn_blue")
                        for button in buttons:
                            if button.is_displayed():
                                driver.execute_script("arguments[0].click();", button)
                                time.sleep(5)
                                
                                # 验证是否成功
                                if "agecheck" not in driver.current_url.lower():
                                    print(f"{game['name']} 年龄验证成功！")
                                    save_cookies(driver)  # 保存更新的Cookies
                                    break
                    except Exception as e:
                        print(f"方法3失败: {e}")
                
                # 方法4：URL参数绕过
                if "agecheck" in driver.current_url.lower() or any(indicator in driver.page_source.lower() for indicator in age_indicators):
                    try:
                        current_url = driver.current_url
                        if "?mature_content=1" not in current_url and "&mature_content=1" not in current_url:
                            if "?" in current_url:
                                new_url = current_url + "&mature_content=1"
                            else:
                                new_url = current_url + "?mature_content=1"
                            
                            driver.get(new_url)
                            time.sleep(5)
                            
                            # 验证是否成功
                            if not any(indicator in driver.page_source.lower() for indicator in age_indicators):
                                print(f"{game['name']} 使用URL参数绕过年龄验证成功！")
                                save_cookies(driver)  # 保存更新的Cookies
                    except Exception as e:
                        print(f"方法4失败: {e}")
            else:
                print(f"{game['name']} 不需要年龄验证，继续处理下一个游戏")
        
        except Exception as e:
            print(f"处理 {game['name']} 时出错: {e}")
    
    # 重新保存最终的Cookies
    save_cookies(driver)
    print("\n已完成所有游戏的年龄验证处理")

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
        print("自动处理年龄验证并启动Web服务工具")
        print("=" * 60)
        print("此工具将自动完成以下操作:")
        print("1. 加载Steam Cookies并验证登录状态")
        print("2. 自动处理多个游戏的年龄验证")
        print("3. 保存更新后的Cookies")
        print("4. 启动Web服务器并打开浏览器")
        print("=" * 60)
        
        # 创建必要的目录
        for directory in ["cookies", "output", "logs"]:
            Path(directory).mkdir(exist_ok=True)
        
        # 启动浏览器
        driver = setup_driver(use_headless=False)  # 使用有界面模式方便查看进度
        
        # 加载Cookies并检查登录状态
        cookies_loaded = load_cookies(driver)
        is_logged_in = check_login_status(driver)
        
        if not is_logged_in:
            print("\n未检测到Steam登录状态，请先在浏览器中登录Steam")
            print("正在打开Steam登录页面...")
            driver.get("https://store.steampowered.com/login/")
            
            input("\n请在浏览器中完成登录，然后按Enter继续...")
            
            # 重新检查登录状态
            is_logged_in = check_login_status(driver)
            if is_logged_in:
                print("登录成功！")
                save_cookies(driver)
            else:
                print("登录失败，程序无法继续")
                driver.quit()
                return
        
        # 处理年龄验证
        handle_age_verification(driver)
        
        # 关闭浏览器
        driver.quit()
        print("浏览器已关闭")
        
        # 启动Web服务器
        start_web_server()
        
        # 保持程序运行直到用户中断
        try:
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