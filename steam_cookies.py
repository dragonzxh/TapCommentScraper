#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Steam Cookie管理模块 - 处理Cookie的保存、加载和验证
"""

import os
import json
import time
import pickle
from pathlib import Path
import re
import shutil

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 导入配置
from steam_config import (
    JSON_COOKIES_FILE as COOKIES_FILE_JSON, 
    COOKIES_FILE as COOKIES_FILE_PICKLE, 
    COOKIES_DIR,
    HELPER_FILE as HELPER_FILE_EXIST, 
    ACCOUNT_INDICATORS as LOGIN_INDICATORS, 
    STEAM_STORE_URL, STEAM_COMMUNITY_URL
)

# 定义URLs字典
STEAM_URLS = {
    "store": STEAM_STORE_URL,
    "community": STEAM_COMMUNITY_URL
}

# 预定义的JavaScript代码
ANTI_DETECTION_JS = '''
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
})
'''

def save_cookies(driver, json_file=COOKIES_FILE_JSON, pickle_file=COOKIES_FILE_PICKLE):
    """保存当前浏览器的Cookies到JSON和Pickle文件
    
    Args:
        driver: WebDriver实例
        json_file: JSON格式Cookie文件路径
        pickle_file: Pickle格式Cookie文件路径
        
    Returns:
        bool: 是否成功保存Cookies
    """
    # 确保存储目录存在
    os.makedirs(os.path.dirname(json_file), exist_ok=True)
    os.makedirs(os.path.dirname(pickle_file), exist_ok=True)
    
    try:
        # 获取当前Cookies
        cookies = driver.get_cookies()
        
        if not cookies:
            print("没有找到可用的Cookie！")
            return False
        
        # 保存为JSON格式
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2)
        
        # 保存为Pickle格式（提供更好的序列化兼容性）
        with open(pickle_file, 'wb') as f:
            pickle.dump(cookies, f)
        
        print(f"成功保存了 {len(cookies)} 个Cookies到文件")
        print(f"JSON文件: {json_file}")
        print(f"Pickle文件: {pickle_file}")
        return True
    except Exception as e:
        print(f"保存Cookies时出错: {e}")
        return False

def load_cookies(driver, domain="store.steampowered.com", 
                json_file=COOKIES_FILE_JSON, pickle_file=COOKIES_FILE_PICKLE):
    """从文件加载Cookies到浏览器
    
    Args:
        driver: WebDriver实例
        domain: 要加载Cookies的域名
        json_file: JSON格式Cookie文件路径
        pickle_file: Pickle格式Cookie文件路径
        
    Returns:
        int: 加载的Cookie数量，0表示失败
    """
    # 确保目标域名格式正确
    if not domain.startswith("http"):
        domain = f"https://{domain}"

    # 确保已经导航到目标域，否则无法设置Cookie
    current_url = driver.current_url
    if domain not in current_url:
        print(f"导航到 {domain} 以设置Cookies...")
        try:
            driver.get(domain)
            time.sleep(2)  # 等待页面加载
        except TimeoutException:
            print(f"加载 {domain} 超时，尝试继续...")
    
    # 提取当前域名，用于检验cookie是否适用
    current_domain = driver.current_url.split('//')[1].split('/')[0]
    print(f"当前域名: {current_domain}")
    
    # 优先尝试加载Pickle格式（更可靠）
    cookie_count = 0
    
    # 1. 尝试从Pickle文件加载
    if os.path.exists(pickle_file):
        try:
            with open(pickle_file, 'rb') as f:
                cookies = pickle.load(f)
            
            if cookies:
                for cookie in cookies:
                    try:
                        # 删除domain字段，让浏览器自动匹配当前域
                        if 'domain' in cookie:
                            del cookie['domain']
                        
                        # 删除不合规的属性，避免加载错误
                        if 'expiry' in cookie:
                            cookie['expiry'] = int(cookie['expiry'])
                        if 'sameSite' in cookie:
                            if cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                                del cookie['sameSite']
                        
                        driver.add_cookie(cookie)
                        cookie_count += 1
                    except Exception as e:
                        print(f"加载单个Cookie时出错 (Pickle): {e}")
                
                print(f"从Pickle文件加载了 {cookie_count} 个Cookies")
                if cookie_count > 0:
                    return cookie_count
        except Exception as e:
            print(f"加载Pickle格式Cookie文件时出错: {e}")
    
    # 2. 尝试从JSON文件加载
    if os.path.exists(json_file):
        try:
            cookie_count = 0
            with open(json_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            if cookies:
                for cookie in cookies:
                    try:
                        # 删除domain字段，让浏览器自动匹配当前域
                        if 'domain' in cookie:
                            del cookie['domain']
                        
                        # 删除不合规的属性，避免加载错误
                        if 'expiry' in cookie:
                            cookie['expiry'] = int(cookie['expiry'])
                        if 'sameSite' in cookie:
                            if cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                                del cookie['sameSite']
                        
                        driver.add_cookie(cookie)
                        cookie_count += 1
                    except Exception as e:
                        print(f"加载单个Cookie时出错 (JSON): {e}")
                
                print(f"从JSON文件加载了 {cookie_count} 个Cookies")
                return cookie_count
        except Exception as e:
            print(f"加载JSON格式Cookie文件时出错: {e}")
    
    if cookie_count == 0:
        print("未能加载任何Cookie，可能需要重新登录")
    
    return cookie_count

def verify_login_status(driver, url=None):
    """验证当前是否已登录Steam
    
    Args:
        driver: WebDriver实例
        url: 要检查的URL，如果为None则使用当前URL
        
    Returns:
        bool: 是否已登录
    """
    try:
        if url:
            try:
                driver.get(url)
                time.sleep(3)  # 等待页面加载完成
            except TimeoutException:
                print(f"加载 {url} 超时，尝试继续...")
        
        # 检查页面源代码中的登录状态指示器
        is_logged_in = False
        
        # 检查常见的登录状态指示器
        for indicator in LOGIN_INDICATORS:
            if indicator in driver.page_source:
                is_logged_in = True
                break
        
        # 如果上面的检查失败，尝试按钮或菜单检查
        if not is_logged_in:
            try:
                # 检查账户下拉菜单
                account_menu = driver.find_element(By.ID, "account_dropdown")
                if account_menu:
                    is_logged_in = True
            except NoSuchElementException:
                pass
        
        # 如果上述检查失败，尝试查找登录按钮（如存在则未登录）
        if not is_logged_in:
            try:
                login_buttons = driver.find_elements(
                    By.CSS_SELECTOR, 
                    ".global_action_link, .sign_in_link, a[href*='login']"
                )
                
                for button in login_buttons:
                    if "登录" in button.text or "login" in button.text.lower() or "sign in" in button.text.lower():
                        # 找到明确的登录按钮，说明未登录
                        return False
            except Exception:
                pass
        
        # 如果仍未确定，检查Cookies中的登录凭证
        if not is_logged_in:
            cookies = driver.get_cookies()
            for cookie in cookies:
                if cookie.get('name') == 'steamLoginSecure' and cookie.get('value', ''):
                    is_logged_in = True
                    break
        
        # 最后返回登录状态
        return is_logged_in
    
    except Exception as e:
        print(f"验证登录状态时出错: {e}")
        return False

def refresh_login(driver):
    """刷新登录状态 - 访问Steam商店和社区站点
    
    Args:
        driver: WebDriver实例
        
    Returns:
        bool: 是否成功刷新登录状态
    """
    try:
        success = True
        
        # 导入年龄验证处理模块（在函数内部导入，避免循环引用）
        from steam_driver import handle_age_check
        
        # 检查每个域的登录状态并刷新
        for domain_name, url in STEAM_URLS.items():
            if "store" in domain_name or "community" in domain_name:
                print(f"检查 {domain_name} 登录状态...")
                try:
                    driver.get(url)
                    time.sleep(3)
                except TimeoutException:
                    print(f"加载 {url} 超时，尝试继续...")
                
                # 处理可能的年龄验证
                try:
                    if handle_age_check(driver):
                        print(f"已处理 {domain_name} 的年龄验证")
                except Exception as e:
                    print(f"处理年龄验证时出错，但将继续: {e}")
                
                is_logged_in = verify_login_status(driver)
                if is_logged_in:
                    print(f"✓ {domain_name} 已成功登录")
                    # 保存截图记录登录状态
                    try:
                        screenshot_path = os.path.join(COOKIES_DIR, f"{domain_name}_logged_in.png")
                        driver.save_screenshot(screenshot_path)
                        print(f"已保存登录状态截图: {screenshot_path}")
                    except Exception as e:
                        print(f"保存截图时出错: {e}")
                else:
                    print(f"✗ {domain_name} 登录失败")
                    success = False
        
        return success
    except Exception as e:
        print(f"刷新登录状态时出错: {e}")
        return False

def create_cookies_helper_file(steam_login_secure_value=None, helper_dir=COOKIES_DIR):
    """创建一个辅助Cookie帮助脚本
    
    Args:
        steam_login_secure_value: 可选的steamLoginSecure值
        helper_dir: 保存Helper脚本的目录
        
    Returns:
        str: 创建的文件路径
    """
    try:
        # 确保目录存在
        os.makedirs(helper_dir, exist_ok=True)
        
        # 辅助脚本文件路径
        helper_path = os.path.join(helper_dir, "steam_cookies_helper.py")
        
        # 脚本内容模板
        helper_script = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Steam Cookies助手 - 帮助获取并保存Steam的登录Cookie
"""

import os
import sys
import json
import time
import pickle
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("缺少必要的Python库，正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium", "webdriver-manager"])
    
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

def login_and_save_cookies():
    """手动登录并保存Cookies"""
    # 询问是否使用无头模式
    headless = input("是否使用无头模式? [y/N]: ").lower() == 'y'
    
    print("正在初始化浏览器...")
    options = webdriver.ChromeOptions()
    
    if headless:
        options.add_argument('--headless=new')
    
    # 基本设置
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--window-size=1920,1080')
    
    # Cookie相关设置
    options.add_argument('--enable-cookies')
    options.add_argument('--disable-site-isolation-trials')
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    options.add_argument('--disable-features=BlockThirdPartyCookies')
    
    # 反爬设置
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        # 初始化浏览器
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 执行反检测JavaScript
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        
        # 打开Steam登录页面
        print("打开Steam登录页面...")
        driver.get('https://store.steampowered.com/login/')
        
        # 提示用户手动登录
        print("请在打开的浏览器窗口中手动登录Steam。")
        print("提示: 勾选'记住我'选项以获取持久会话。")
        print("登录成功后，脚本将自动保存Cookie。")
        
        # 等待用户登录（最多等待5分钟）
        max_wait = 300  # 秒
        login_success = False
        
        print(f"等待登录，最多等待 {max_wait//60} 分钟...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            # 检查是否已登录
            cookies = driver.get_cookies()
            logged_in = any(c.get('name') == 'steamLoginSecure' and c.get('value', '') for c in cookies)
            
            if logged_in:
                login_success = True
                print("检测到成功登录！")
                break
            
            # 每5秒检查一次
            time.sleep(5)
        
        if not login_success:
            print("登录等待超时。如果您已登录，请尝试按ENTER继续。")
            input("按ENTER继续...")
        
        # 访问Steam社区网站以激活该域的Cookie
        print("正在访问Steam社区网站以激活Cookie...")
        driver.get('https://steamcommunity.com/')
        time.sleep(3)
        
        # 再次访问商店网站以确保Cookie完全激活
        print("正在访问Steam商店网站以确保Cookie完全激活...")
        driver.get('https://store.steampowered.com/')
        time.sleep(3)
        
        # 保存Cookie
        cookies_dir = 'cookies'
        os.makedirs(cookies_dir, exist_ok=True)
        
        json_path = os.path.join(cookies_dir, 'steam_cookies.json')
        pickle_path = os.path.join(cookies_dir, 'steam_cookies.pkl')
        
        cookies = driver.get_cookies()
        
        # 检查steamLoginSecure是否存在
        has_login_secure = any(c.get('name') == 'steamLoginSecure' and c.get('value', '') for c in cookies)
        
        if has_login_secure:
            # 保存为JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2)
            
            # 保存为Pickle
            with open(pickle_path, 'wb') as f:
                pickle.dump(cookies, f)
            
            # 保存截图
            screenshot_path = os.path.join(cookies_dir, 'steam_logged_in.png')
            driver.save_screenshot(screenshot_path)
            
            print(f"成功保存了 {len(cookies)} 个Cookie!")
            print(f"JSON文件: {json_path}")
            print(f"Pickle文件: {pickle_path}")
            print(f"登录状态截图: {screenshot_path}")
            
            # 显示重要的Cookie
            for cookie in cookies:
                if cookie.get('name') in ['steamLoginSecure', 'sessionid']:
                    print(f"找到重要Cookie: {cookie.get('name')}")
        else:
            print("警告: 未找到steamLoginSecure Cookie，可能未成功登录!")
            print("请确保您已在浏览器中完成登录流程。")
    
    except Exception as e:
        print(f"发生错误: {e}")
    
    finally:
        input("按ENTER关闭浏览器...")
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    print("===== Steam Cookie助手 =====")
    print("本工具帮助您获取Steam网站的Cookie")
    print("这些Cookie将用于爬虫的登录")
    print("============================")
    
    login_and_save_cookies()
'''
        
        # 处理自定义的steamLoginSecure值
        if steam_login_secure_value:
            # 创建cookie设置代码
            cookie_setup_code = "# 直接设置提供的steamLoginSecure Cookie\n"
            cookie_setup_code += "print(\"使用提供的steamLoginSecure值设置Cookie...\")\n"
            cookie_setup_code += "driver.add_cookie({\n"
            cookie_setup_code += "    'name': 'steamLoginSecure',\n"
            cookie_setup_code += f"    'value': '{steam_login_secure_value}',\n"
            cookie_setup_code += "    'domain': '.steampowered.com',\n"
            cookie_setup_code += "    'path': '/'\n"
            cookie_setup_code += "})\n"
            cookie_setup_code += "login_success = True\n"
            cookie_setup_code += "time.sleep(2)\n"
            
            # 替换原有的手动登录提示
            helper_script = helper_script.replace("# 提示用户手动登录\nprint(\"请在打开的浏览器窗口中手动登录Steam。\")", cookie_setup_code)
        
        # 写入辅助脚本文件
        with open(helper_path, 'w', encoding='utf-8') as f:
            f.write(helper_script)
        
        # 设置执行权限
        try:
            os.chmod(helper_path, 0o755)  # rwx r-x r-x
        except:
            pass  # Windows系统可能会失败，但无关紧要
        
        print(f"已创建Cookie助手脚本: {helper_path}")
        return helper_path
        
    except Exception as e:
        print(f"创建Cookie助手脚本时出错: {e}")
        return None 