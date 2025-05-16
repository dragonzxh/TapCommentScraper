#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Steam游戏年龄验证处理模块
自动处理Steam游戏的年龄验证要求
"""

import os
import time
import json
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('age_verification')

# 确保cookies目录存在
Path("cookies").mkdir(exist_ok=True)

def setup_driver(use_headless=True):
    """设置并返回Chrome WebDriver"""
    chrome_options = Options()
    
    if use_headless:
        chrome_options.add_argument('--headless')
    
    # 添加反检测参数
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    
    # 设置用户代理
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36')
    
    # 添加实验性选项
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 设置页面加载超时
        driver.set_page_load_timeout(30)
        
        # 执行JavaScript来绕过反爬虫检测
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("WebDriver已成功初始化")
        return driver
    except Exception as e:
        logger.error(f"初始化WebDriver时出错: {str(e)}")
        raise

def load_cookies(driver):
    """从cookies目录加载保存的cookies"""
    try:
        cookies_file = os.path.join('cookies', 'steam_cookies.json')
        # 检查json格式的cookies
        if os.path.exists(cookies_file):
            logger.info("找到cookies文件，准备加载")
            
            # 先访问Steam域名页面再添加cookies
            logger.info("访问Steam网站以准备添加cookies...")
            driver.get("https://store.steampowered.com")
            time.sleep(3)
            
            with open(cookies_file, 'r') as f:
                cookies = json.load(f)
            
            for cookie in cookies:
                # 删除不兼容的属性
                if 'sameSite' in cookie:
                    if cookie['sameSite'] == 'unspecified':
                        cookie['sameSite'] = 'Strict'
                if 'expiry' in cookie:
                    del cookie['expiry']
                
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"添加cookie出错 {cookie}: {str(e)}")
            
            logger.info(f"已加载 {len(cookies)} 个cookies")
            
            # 刷新页面应用cookies
            driver.refresh()
            time.sleep(3)
            
            return True
        
        # 检查pickle格式的cookies
        pickle_file = os.path.join('cookies', 'steam_cookies.pkl')
        if os.path.exists(pickle_file):
            import pickle
            logger.info("找到pickle格式cookies文件，准备加载")
            
            # 先访问Steam域名页面再添加cookies
            logger.info("访问Steam网站以准备添加cookies...")
            driver.get("https://store.steampowered.com")
            time.sleep(3)
            
            with open(pickle_file, 'rb') as f:
                cookies = pickle.load(f)
            
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"添加cookie出错: {str(e)}")
            
            logger.info(f"已加载 {len(cookies)} 个cookies")
            
            # 刷新页面应用cookies
            driver.refresh()
            time.sleep(3)
            
            return True
            
        logger.info("未找到保存的cookies")
        return False
    except Exception as e:
        logger.error(f"加载cookies时出错: {str(e)}")
        return False

def save_cookies(driver):
    """保存当前cookies到文件"""
    try:
        # 保存为JSON格式
        cookies = driver.get_cookies()
        with open(os.path.join('cookies', 'steam_cookies.json'), 'w') as f:
            json.dump(cookies, f)
        
        # 同时保存为pickle格式以兼容旧代码
        import pickle
        with open(os.path.join('cookies', 'steam_cookies.pkl'), 'wb') as f:
            pickle.dump(cookies, f)
            
        logger.info(f"已保存当前cookies到两种格式文件，共{len(cookies)}个cookie")
        return True
    except Exception as e:
        logger.error(f"保存cookies时出错: {str(e)}")
        return False

def handle_age_verification_for_game(game_url, use_headless=True, existing_driver=None):
    """处理特定游戏的年龄验证
    
    Args:
        game_url (str): 游戏URL或AppID
        use_headless (bool): 是否使用无头模式，默认为True
        existing_driver: 已存在的WebDriver实例，如果提供则使用它而不是创建新的
    
    Returns:
        tuple: (bool, webdriver) 第一个元素表示是否成功处理了年龄验证，第二个元素是WebDriver实例
    """
    # 处理输入的游戏URL或AppID
    if game_url.isdigit():
        game_url = f"https://store.steampowered.com/app/{game_url}"
    elif "steamcommunity.com" in game_url:
        # 将URL从评论页面转换为商店页面
        app_id = game_url.split('/app/')[1].split('/')[0]
        game_url = f"https://store.steampowered.com/app/{app_id}"
    elif "store.steampowered.com" not in game_url:
        logger.error(f"无效的Steam游戏URL: {game_url}")
        return False, None
    
    logger.info(f"开始处理游戏年龄验证: {game_url}")
    
    driver = None
    verification_success = False
    should_close_driver = False
    
    try:
        # 使用提供的driver或创建新的
        if existing_driver:
            driver = existing_driver
            logger.info("使用提供的WebDriver实例")
        else:
            driver = setup_driver(use_headless=use_headless)
            should_close_driver = True
            logger.info("创建了新的WebDriver实例")
            
            # 如果是新创建的driver，需要加载cookies
            load_cookies(driver)
        
        # 访问游戏页面
        logger.info(f"访问游戏页面: {game_url}")
        driver.get(game_url)
        time.sleep(3)
        
        # 检查是否有年龄验证页面
        page_source = driver.page_source.lower()
        current_url = driver.current_url.lower()
        
        # 检查是否已经有年龄验证
        if "agecheck" in current_url or "age-gate" in page_source or "agegate" in page_source:
            logger.info("检测到年龄验证页面，开始处理...")
            
            # 尝试多种方法绕过年龄验证
            
            # 方法1: 使用日期选择
            try:
                logger.info("尝试方法1: 使用日期选择")
                
                # 选择日，月，年
                # 检查是否有选择日期的下拉框
                day_select = driver.find_elements(By.ID, "ageDay")
                month_select = driver.find_elements(By.ID, "ageMonth")
                year_select = driver.find_elements(By.ID, "ageYear")
                
                if day_select and month_select and year_select:
                    # 执行JavaScript选择日期（1990年1月1日）
                    driver.execute_script("""
                        document.getElementById('ageDay').value = '1';
                        document.getElementById('ageMonth').value = '1';
                        document.getElementById('ageYear').value = '1990';
                    """)
                    
                    # 查找并点击提交按钮
                    submit_button = None
                    possible_buttons = driver.find_elements(By.CSS_SELECTOR, "a.btnv6_blue_hoverfade, input[type='submit'], button[type='submit']")
                    
                    for button in possible_buttons:
                        if "view page" in button.text.lower() or "进入" in button.text or "提交" in button.text:
                            submit_button = button
                            break
                    
                    if submit_button:
                        submit_button.click()
                        time.sleep(3)
                        verification_success = True
                        logger.info("方法1成功：已通过日期选择完成年龄验证")
                    else:
                        logger.warning("方法1失败：未找到提交按钮")
            except Exception as e:
                logger.warning(f"方法1失败: {e}")
            
            # 方法2: 选择年份下拉框
            if not verification_success:
                try:
                    logger.info("尝试方法2: 选择年份下拉框")
                    year_dropdown = driver.find_element(By.NAME, "ageYear")
                    driver.execute_script("arguments[0].value = '1990'", year_dropdown)
                    
                    # 查找并点击View Page按钮
                    view_buttons = driver.find_elements(By.XPATH, "//a[contains(text(), 'View Page') or contains(text(), '查看页面') or contains(text(), '进入')]")
                    if view_buttons:
                        view_buttons[0].click()
                        time.sleep(3)
                        verification_success = True
                        logger.info("方法2成功：已通过选择年份完成年龄验证")
                    else:
                        logger.warning("方法2失败：未找到View Page按钮")
                except Exception as e:
                    logger.warning(f"方法2失败: {str(e)}")
            
            # 方法3: 使用复选框和按钮
            if not verification_success:
                try:
                    logger.info("尝试方法3: 使用复选框和按钮")
                    # 尝试点击"我已满18岁"的按钮
                    adult_buttons = driver.find_elements(By.XPATH, 
                                                      "//a[contains(text(), '18') or contains(text(), 'Enter') or contains(text(), '进入') or contains(text(), '继续')]")
                    if adult_buttons:
                        adult_buttons[0].click()
                        time.sleep(3)
                        verification_success = True
                        logger.info("方法3成功：已点击年龄确认按钮")
                    else:
                        logger.warning("方法3失败：未找到年龄确认按钮")
                except Exception as e:
                    logger.warning(f"方法3失败: {str(e)}")
            
            # 方法4: 通过修改URL绕过年龄验证
            if not verification_success:
                try:
                    logger.info("尝试方法4: 通过修改URL绕过年龄验证")
                    
                    # 通常游戏URL格式: https://store.steampowered.com/app/[appid]/[game_name]
                    if "/app/" in game_url:
                        app_id = game_url.split('/app/')[1].split('/')[0]
                        # 添加bypass参数
                        modified_url = f"https://store.steampowered.com/app/{app_id}?mature_content=1"
                        driver.get(modified_url)
                        time.sleep(3)
                        
                        # 检查是否成功绕过
                        if "agecheck" not in driver.current_url.lower():
                            verification_success = True
                            logger.info("方法4成功：已通过修改URL绕过年龄验证")
                        else:
                            logger.warning("方法4失败：修改URL未能绕过年龄验证")
                except Exception as e:
                    logger.warning(f"方法4失败: {str(e)}")
        else:
            logger.info("没有检测到年龄验证页面，游戏不需要年龄验证或已经完成验证")
            verification_success = True
        
        # 保存处理后的cookies以备将来使用
        if verification_success:
            save_cookies(driver)
        
        # 返回验证结果和driver实例
        return verification_success, driver
        
    except Exception as e:
        logger.error(f"处理年龄验证时出错: {e}")
        # 如果处理过程中出错，仍然返回driver实例，方便调用者处理
        return False, driver
    finally:
        # 仅当需要关闭driver且发生错误时才关闭
        # 正常情况下，我们希望返回driver以便后续使用
        if should_close_driver and not verification_success:
            try:
                driver.quit()
                logger.info("由于验证失败，已关闭自动创建的WebDriver")
            except Exception as e:
                logger.error(f"关闭WebDriver失败: {e}")
                pass

# 测试代码
if __name__ == "__main__":
    # 测试处理GTA5的年龄验证（AppID: 271590）
    result, driver = handle_age_verification_for_game("271590")
    print(f"年龄验证处理结果: {'成功' if result else '失败'}")
    print("处理日志:")
    for handler in logger.handlers:
        if hasattr(handler, 'stream'):
            handler.flush() 