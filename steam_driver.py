#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Steam WebDriver模块 - 处理浏览器初始化和操作
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 导入配置
from steam_config import (
    CHROME_PATHS, USER_AGENT, PAGE_LOAD_TIMEOUT, 
    SCRIPT_TIMEOUT, IMPLICIT_WAIT
)

def setup_driver(use_headless=False):
    """设置并初始化WebDriver
    
    Args:
        use_headless (bool): 是否使用无头模式运行浏览器
        
    Returns:
        WebDriver: 初始化好的WebDriver实例
    """
    options = webdriver.ChromeOptions()
    
    # 基本设置
    if use_headless:
        options.add_argument('--headless=new')
    
    # 禁用各种可能导致问题的功能
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-renderer-backgrounding')
    
    # 内存和稳定性相关选项
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--window-size=1920,1080')
    
    # Cookie相关设置 - 提高cookie处理的兼容性
    options.add_argument('--enable-cookies')
    options.add_argument('--cookies-without-same-site-must-be-secure=false')
    options.add_argument('--disable-site-isolation-trials')
    
    # 添加更多隐私设置，避免cookie被清除或限制
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    options.add_argument('--disable-features=BlockThirdPartyCookies')
    options.add_argument('--disable-features=SameSiteByDefaultCookies')
    
    # 会话保持相关设置
    options.add_argument('--enable-file-cookies') 
    options.add_argument('--process-per-site')
    
    # 绕过部分反爬虫机制
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 尝试显式指定Chrome路径
    if os.name == 'nt':  # Windows
        for path in CHROME_PATHS["windows"]:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                options.binary_location = expanded_path
                print(f"使用Chrome路径: {expanded_path}")
                break
    elif os.name == 'posix' and os.path.exists(CHROME_PATHS["mac"]):
        options.binary_location = CHROME_PATHS["mac"]
        print("使用macOS系统Chrome路径")
    
    # 设置语言
    options.add_argument('--lang=zh-CN')
    
    # 设置用户代理
    options.add_argument(f'user-agent={USER_AGENT}')
    
    # 禁用日志
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # 创建ChromeDriver
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
    except Exception as e:
        print(f"ChromeDriver初始化失败: {e}")
        # 尝试使用备用方法初始化
        try:
            print("尝试备用方法初始化ChromeDriver...")
            driver = webdriver.Chrome(options=options)
            print("备用方法初始化成功")
        except Exception as e2:
            print(f"备用方法也失败: {e2}")
            raise
    
    # 设置超时时间
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    driver.set_script_timeout(SCRIPT_TIMEOUT)
    driver.implicitly_wait(IMPLICIT_WAIT)
    
    print("浏览器初始化完成")
    return driver

def handle_age_check(driver):
    """处理年龄验证页面
    
    Args:
        driver: WebDriver实例
        
    Returns:
        bool: 是否成功处理年龄验证
    """
    try:
        # 检查是否存在常见的年龄验证标记
        age_indicators = [
            "mature_content",
            "agecheck",
            "age_gate",
            "年龄验证",
            "age check",
            "mature content"
        ]
        
        page_source_lower = driver.page_source.lower()
        age_verification_needed = any(indicator in page_source_lower for indicator in age_indicators)
        
        if age_verification_needed:
            print("检测到年龄验证页面，尝试处理...")
            
            # 方法1：最新版的Steam年龄验证 - 日期选择器
            try:
                # 尝试找到日期选择器并设置
                day_select = driver.find_element(By.ID, "ageDay")
                month_select = driver.find_element(By.ID, "ageMonth")
                year_select = driver.find_element(By.ID, "ageYear")
                
                # 使用JavaScript设置日期为1990年1月1日
                driver.execute_script("arguments[0].value = '1';", day_select)
                driver.execute_script("arguments[0].value = 'January';", month_select)
                driver.execute_script("arguments[0].value = '1990';", year_select)
                
                print("已设置出生日期为1990年1月1日")
                time.sleep(1)
                
                # 点击查看页面按钮
                submit_button = driver.find_element(By.CSS_SELECTOR, ".btnv6_blue_hoverfade")
                driver.execute_script("arguments[0].click();", submit_button)
                print("已点击提交按钮")
                time.sleep(5)
                return True
            except Exception as e:
                print(f"尝试方法1失败: {e}")
            
            # 方法2：旧版Steam年龄验证 - 年份下拉框
            try:
                age_selects = driver.find_elements(By.CSS_SELECTOR, "select[name='ageYear'], #ageYear, [id*='age']")
                if age_selects:
                    for age_select in age_selects:
                        if age_select.is_displayed():
                            # 选择1990年
                            driver.execute_script(
                                "arguments[0].value = '1990'",
                                age_select
                            )
                            print("已设置年龄为1990年")
                    time.sleep(1)
                    
                    # 点击查看页面按钮
                    view_buttons = driver.find_elements(
                        By.CSS_SELECTOR,
                        "a.btnv6_blue_hoverfade, [type='submit'], .agegate_text_container.btns a"
                    )
                    for button in view_buttons:
                        button_text = button.text.lower()
                        if ("view" in button_text or 
                            "enter" in button_text or 
                            "proceed" in button_text or
                            "continue" in button_text or
                            "查看" in button_text or
                            "进入" in button_text):
                            print(f"点击按钮: {button.text}")
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(5)
                            return True
            except Exception as e:
                print(f"尝试方法2失败: {e}")
            
            # 方法3：简化年龄验证 - 直接点击确认按钮
            try:
                # 尝试找到"我已年满13岁"按钮（某些地区的简化验证）
                age_buttons = driver.find_elements(By.CSS_SELECTOR, 
                                            ".agegate_text_container.btns a, .agegate_btn_container .btn_blue")
                for button in age_buttons:
                    if button.is_displayed():
                        print(f"直接点击年龄确认按钮: {button.text}")
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(5)
                        return True
            except Exception as e:
                print(f"尝试方法3失败: {e}")
            
            # 方法4：通过URL参数绕过年龄验证
            try:
                # 某些情况下可以通过添加URL参数绕过验证
                current_url = driver.current_url
                if "?mature_content=1" not in current_url and "&mature_content=1" not in current_url:
                    if "?" in current_url:
                        new_url = current_url + "&mature_content=1"
                    else:
                        new_url = current_url + "?mature_content=1"
                    print(f"尝试通过URL参数绕过年龄验证: {new_url}")
                    driver.get(new_url)
                    time.sleep(5)
                    
                    # 检查是否仍在年龄验证页面
                    if not any(indicator in driver.page_source.lower() for indicator in age_indicators):
                        print("成功绕过年龄验证")
                        return True
            except Exception as e:
                print(f"尝试方法4失败: {e}")
            
            # 所有方法都失败
            print("\n所有年龄验证方法都失败，建议使用以下方法解决：")
            print("1. 运行 python steam_cookies_helper.py")
            print("2. 登录您的Steam账号并手动完成年龄验证")
            print("3. 保存Cookies后再次运行爬虫")
            return False
            
        return False  # 没有检测到年龄验证页面
    except Exception as e:
        print(f"处理年龄验证时出错: {e}")
        return False 