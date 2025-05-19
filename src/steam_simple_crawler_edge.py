#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Steam简化爬虫 - Edge浏览器版本 - 不需要登录，只处理年龄限制和内容警告
"""

import os
import sys
import time
import re
import json
import logging
import random
import csv
from datetime import datetime
from pathlib import Path
import argparse
import platform
import traceback

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    WebDriverException, StaleElementReferenceException
)

try:
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
    WEBDRIVER_MANAGER_INSTALLED = True
except ImportError:
    WEBDRIVER_MANAGER_INSTALLED = False

# 配置常量
OUTPUT_DIR = "output"
STEAM_STORE_URL = "https://store.steampowered.com/"
STEAM_COMMUNITY_URL = "https://steamcommunity.com/"
PAGE_LOAD_TIMEOUT = 30
SCRIPT_TIMEOUT = 30
IMPLICIT_WAIT = 5
SCROLL_PAUSE_TIME = 2
BATCH_SIZE = 10
MAX_RETRIES = 3

# 设置日志
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 创建一个日志文件名，包含日期和时间
log_file = log_dir / f"edge_crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SteamSimpleCrawlerEdge")

# 输出系统信息
logger.info(f"系统信息: {platform.platform()}")
logger.info(f"Python版本: {platform.python_version()}")
logger.info(f"WebDriver Manager已安装: {WEBDRIVER_MANAGER_INSTALLED}")

def setup_driver(use_headless=False):
    """设置并返回配置好的WebDriver
    
    Args:
        use_headless: 是否使用无头模式
        
    Returns:
        WebDriver实例
    """
    try:
        logger.info("初始化Edge WebDriver...")
        
        options = Options()
        
        # 无头模式配置
        if use_headless:
            options.add_argument('--headless=new')  # 新版Edge需要使用新的无头参数
        
        # 基本设置
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=zh-CN,zh,en-US,en')
        
        # 禁用图片加载以提高性能（可选）
        # options.add_argument('--blink-settings=imagesEnabled=false')
        
        # 设置反爬配置
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 创建和初始化WebDriver
        if WEBDRIVER_MANAGER_INSTALLED:
            try:
                logger.info("使用WebDriver Manager安装Edge驱动...")
                service = Service(EdgeChromiumDriverManager().install())
                driver = webdriver.Edge(service=service, options=options)
                logger.info("Edge WebDriver初始化成功")
            except Exception as e:
                logger.error(f"使用WebDriver Manager初始化Edge驱动失败: {e}")
                logger.error(traceback.format_exc())
                
                # 尝试使用默认方式初始化
                logger.info("尝试使用默认方式初始化Edge驱动...")
                driver = webdriver.Edge(options=options)
                logger.info("使用默认方式初始化Edge驱动成功")
        else:
            logger.warning("WebDriver Manager未安装，使用系统Edge Driver")
            driver = webdriver.Edge(options=options)
            logger.info("使用系统Edge驱动初始化成功")
        
        # 设置超时时间
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        driver.set_script_timeout(SCRIPT_TIMEOUT)
        
        # 设置窗口大小
        driver.set_window_size(1920, 1080)
        
        # 输出浏览器信息
        try:
            browser_version = driver.capabilities.get('browserVersion', 'unknown')
            driver_version = driver.capabilities.get('msedge', {}).get('msedgedriver', 'unknown')
            logger.info(f"Edge浏览器版本: {browser_version}")
            logger.info(f"Edge驱动版本: {driver_version}")
        except Exception as e:
            logger.warning(f"无法获取浏览器版本信息: {e}")
        
        # 隐藏浏览器指纹
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        
        logger.info("WebDriver初始化成功")
        return driver
        
    except Exception as e:
        logger.error(f"设置WebDriver失败: {e}")
        logger.error(traceback.format_exc())
        raise

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
        
        if not age_verification_needed:
            return False  # 不需要年龄验证
            
        logger.info("检测到年龄验证页面，尝试处理...")
        
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
            
            logger.info("已设置出生日期为1990年1月1日")
            time.sleep(1)
            
            # 点击查看页面按钮
            submit_button = driver.find_element(By.CSS_SELECTOR, ".btnv6_blue_hoverfade")
            driver.execute_script("arguments[0].click();", submit_button)
            logger.info("已点击提交按钮")
            time.sleep(3)
            return True
        except Exception as e:
            logger.debug(f"尝试方法1失败: {e}")
        
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
                        logger.info("已设置年龄为1990年")
                time.sleep(1)
                
                # 点击查看页面按钮
                view_buttons = driver.find_elements(
                    By.CSS_SELECTOR,
                    "a.btnv6_blue_hoverfade, [type='submit'], .agegate_text_container.btns a"
                )
                for button in view_buttons:
                    if button.is_displayed():
                        button_text = button.text.lower()
                        if ("view" in button_text or 
                            "enter" in button_text or 
                            "proceed" in button_text or
                            "continue" in button_text or
                            "查看" in button_text or
                            "进入" in button_text):
                            logger.info(f"点击按钮: {button.text}")
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(3)
                            return True
        except Exception as e:
            logger.warning(f"尝试方法2失败: {e}")
        
        # 方法3：简化年龄验证 - 直接点击确认按钮
        try:
            # 尝试找到"我已年满13岁"按钮（某些地区的简化验证）
            age_buttons = driver.find_elements(By.CSS_SELECTOR, 
                                        ".agegate_text_container.btns a, .agegate_btn_container .btn_blue")
            for button in age_buttons:
                if button.is_displayed():
                    logger.info(f"直接点击年龄确认按钮: {button.text}")
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(3)
                    return True
        except Exception as e:
            logger.warning(f"尝试方法3失败: {e}")
        
        # 方法4：通过URL参数绕过年龄验证
        try:
            # 某些情况下可以通过添加URL参数绕过验证
            current_url = driver.current_url
            if "?mature_content=1" not in current_url and "&mature_content=1" not in current_url:
                if "?" in current_url:
                    new_url = current_url + "&mature_content=1"
                else:
                    new_url = current_url + "?mature_content=1"
                logger.info(f"尝试通过URL参数绕过年龄验证: {new_url}")
                driver.get(new_url)
                time.sleep(3)
                
                # 检查是否仍在年龄验证页面
                if not any(indicator in driver.page_source.lower() for indicator in age_indicators):
                    logger.info("成功绕过年龄验证")
                    return True
        except Exception as e:
            logger.warning(f"尝试方法4失败: {e}")
        
        # 检查是否成功通过年龄验证
        time.sleep(IMPLICIT_WAIT)
        current_url = driver.current_url
        
        # 如果URL变化或者页面内容变化，可能表示已通过验证
        if "agecheck" not in current_url.lower() and not any(indicator in driver.page_source.lower() for indicator in age_indicators):
            logger.info("成功通过年龄验证")
            return True
        else:
            logger.warning("可能未能通过年龄验证")
            return False
            
    except Exception as e:
        logger.error(f"处理年龄验证出错: {e}")
        logger.error(traceback.format_exc())
        return False

def is_content_warning_page(driver):
    """检查当前是否在暴力色情内容警告页面
    
    Args:
        driver: WebDriver实例
        
    Returns:
        bool: 是否在内容警告页面
    """
    try:
        page_source = driver.page_source.lower()
        
        # 检查特定的Steam内容警告页面文本，更精确地匹配
        steam_specific_warnings = [
            "this game contains content you have asked not to see",
            "该游戏包含您不希望看到的内容",
            "内容警告",
            "content warning"
        ]
        
        for specific_warning in steam_specific_warnings:
            if specific_warning in page_source:
                logger.info(f"检测到特定的Steam内容警告页面: '{specific_warning}'")
                return True
        
        # 检查是否有View Community Hub按钮，这是内容警告页面的标志之一
        try:
            # 使用JavaScript检测特定按钮
            js_script = """
                var communityHubButton = false;
                // 检查文本内容
                var elements = document.querySelectorAll('a, button');
                for (var i = 0; i < elements.length; i++) {
                    var text = elements[i].textContent.trim().toLowerCase();
                    if (text.includes('view community hub') || 
                        text.includes('浏览社区中心') || 
                        text.includes('浏览社区内容') || 
                        text.includes('community hub')) {
                        return true;
                    }
                }
                return false;
            """
            has_community_hub_button = driver.execute_script(js_script)
            if has_community_hub_button:
                logger.info("通过按钮文本检测到内容警告页面")
                return True
        except Exception as e:
            logger.warning(f"检查View Community Hub按钮失败: {e}")
        
        # 检查常见的内容警告关键词
        content_warning_indicators = [
            "mature content", 
            "adult content",
            "violent content", 
            "sexual content",
            "violent or sexual content",
            "成人内容", 
            "暴力内容", 
            "色情内容",
            "确认年龄",
            "partially nudity",
            "some nudity",
            "sexual content",
            "血腥",
            "暴力",
            "性内容",
            "nudity"
        ]
        
        # 内容警告页面的特征是存在这些关键词和确认按钮
        for indicator in content_warning_indicators:
            if indicator in page_source:
                # 确认页面上有继续按钮或"View Community Hub"按钮
                continue_buttons = driver.find_elements(By.CSS_SELECTOR, 
                    "a.btn_green_white_innerfade, button.btn_green_steamui, " + 
                    ".btnv6_green_white_innerfade, .agecheck_continue_button, " + 
                    "a[href*='communitypage'], a[href*='community'], " + 
                    ".btn_blue_steamui")
                
                if continue_buttons and any(btn.is_displayed() for btn in continue_buttons):
                    logger.info(f"检测到内容警告页面特征: '{indicator}'")
                    return True
                
                # 检查是否有任何可能的确认按钮
                js_button_check = """
                    var possibleButtons = document.querySelectorAll('a, button');
                    for (var i = 0; i < possibleButtons.length; i++) {
                        var btn = possibleButtons[i];
                        var text = btn.textContent.trim().toLowerCase();
                        if ((text.includes('view') || text.includes('continue') || 
                             text.includes('proceed') || text.includes('确认') || 
                             text.includes('继续') || text.includes('浏览') ||
                             text.includes('社区中心')) && 
                            btn.offsetParent !== null) {
                            return true;
                        }
                    }
                    return false;
                """
                has_buttons = driver.execute_script(js_button_check)
                if has_buttons:
                    logger.info(f"通过按钮检测到内容警告页面特征: '{indicator}'")
                    return True
        
        # 检查URL参数是否包含内容警告相关参数
        current_url = driver.current_url.lower()
        if 'mature_content=1' in current_url or 'agecheck=1' in current_url:
            logger.info("URL参数显示这可能是内容警告页面")
            # 额外检查页面内容确认
            if '确认' in page_source or 'confirm' in page_source or 'view' in page_source:
                return True
        
        # 检查是否是简化版移动内容警告页面
        if ('want to update what type of content you see on steam' in page_source or
            '想要更新您在Steam上看到的内容类型' in page_source):
            logger.info("检测到移动版内容警告页面")
            return True
        
        return False
    except Exception as e:
        logger.error(f"检查内容警告页面时出错: {e}")
        return False

def handle_content_warning_page(driver):
    """处理暴力色情内容警告页面
    
    Args:
        driver: WebDriver实例
        
    Returns:
        bool: 是否成功处理
    """
    try:
        logger.info("尝试处理内容警告页面...")
        
        # 直接针对"浏览社区中心"按钮的点击策略
        try:
            # 首先尝试直接查找"浏览社区中心"按钮并点击
            js_target_button = """
                var buttonTexts = ['浏览社区中心', 'View Community Hub'];
                var buttons = document.querySelectorAll('a');
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    var text = btn.textContent.trim();
                    if (buttonTexts.some(t => text.includes(t)) && btn.offsetParent !== null) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            """
            direct_clicked = driver.execute_script(js_target_button)
            if direct_clicked:
                logger.info("成功直接点击'浏览社区中心'按钮")
                time.sleep(3)  # 等待页面加载
                return True
        except Exception as e:
            logger.warning(f"直接点击'浏览社区中心'按钮失败: {e}")
        
        # 更精确的选择器，包含Steam警告页面特有的按钮标识
        specific_selectors = [
            # View Community Hub按钮(浏览社区中心)的选择器
            "a[href*='communitypage']", 
            "a[href*='community']", 
            "a:contains('View Community Hub')", 
            "a:contains('浏览社区中心')",
            "a.view_community_hub", 
            "a.community_hub_btn"
        ]
        
        # 先尝试更精确的选择器
        button_clicked = False
        for selector in specific_selectors:
            try:
                # 使用JavaScript查找元素，解决某些选择器在Selenium中不支持的问题
                js_script = f"""
                    var btns = [];
                    if ('{selector}'.includes(':contains')) {{
                        // 处理:contains选择器
                        var text = '{selector}'.split("'")[1];
                        var elements = document.querySelectorAll('a');
                        for (var i = 0; i < elements.length; i++) {{
                            if (elements[i].textContent.includes(text)) {{
                                btns.push(elements[i]);
                            }}
                        }}
                    }} else {{
                        // 常规选择器
                        btns = document.querySelectorAll('{selector}');
                    }}
                    if (btns.length > 0) {{
                        for (var i = 0; i < btns.length; i++) {{
                            if (btns[i].offsetParent !== null && btns[i].style.display !== 'none') {{
                                btns[i].click();
                                return true;
                            }}
                        }}
                    }}
                    return false;
                """
                button_clicked = driver.execute_script(js_script)
                if button_clicked:
                    logger.info(f"成功通过精确选择器 '{selector}' 点击警告确认按钮")
                    time.sleep(3)  # 等待页面加载
                    break
            except Exception as e:
                logger.warning(f"尝试选择器 '{selector}' 失败: {e}")
        
        # 如果精确选择器未找到，尝试通过页面文本内容查找按钮
        if not button_clicked:
            try:
                # 查找包含特定文本的按钮
                text_keywords = ['View Community Hub', '浏览社区中心', 'Continue', '继续', 'View Page', '查看页面']
                js_find_by_text = """
                    var keywords = arguments[0];
                    var elements = document.querySelectorAll('a, button');
                    for (var i = 0; i < elements.length; i++) {
                        var elem = elements[i];
                        var text = elem.textContent.trim();
                        for (var j = 0; j < keywords.length; j++) {
                            if (text.includes(keywords[j]) && elem.offsetParent !== null) {
                                elem.click();
                                return true;
                            }
                        }
                    }
                    return false;
                """
                button_clicked = driver.execute_script(js_find_by_text, text_keywords)
                if button_clicked:
                    logger.info(f"成功通过文本内容匹配点击警告确认按钮")
                    time.sleep(3)  # 等待页面加载
                    return True
            except Exception as e:
                logger.warning(f"通过文本内容查找按钮失败: {e}")
        
        # 如果前两种方法都失败，尝试更通用的方法 - 点击任何可见的绿色/蓝色按钮
        if not button_clicked:
            try:
                # 点击任何可见的绿色/蓝色按钮（通常是确认按钮）
                js_click_any_button = """
                    var buttons = document.querySelectorAll('a.btn_green_white_innerfade, button.btn_green_steamui, .btnv6_green_white_innerfade, .agecheck_continue_button, a.btn_blue_steamui, button.btn_blue_steamui, .btnv6_blue_hoverfade');
                    for (var i = 0; i < buttons.length; i++) {
                        if (buttons[i].offsetParent !== null && buttons[i].style.display !== 'none') {
                            buttons[i].click();
                            return true;
                        }
                    }
                    return false;
                """
                button_clicked = driver.execute_script(js_click_any_button)
                if button_clicked:
                    logger.info("成功点击页面上的确认按钮")
                    time.sleep(3)  # 等待页面加载
                    return True
            except Exception as e:
                logger.warning(f"点击通用按钮失败: {e}")
        
        # 最后的尝试：点击任何可见的按钮或链接
        if not button_clicked:
            try:
                js_click_any_element = """
                    var elements = document.querySelectorAll('a, button');
                    for (var i = 0; i < elements.length; i++) {
                        var elem = elements[i];
                        if (elem.offsetParent !== null && 
                            elem.style.display !== 'none' && 
                            (elem.tagName === 'BUTTON' || 
                             (elem.tagName === 'A' && elem.href && !elem.href.includes('javascript:void(0)')))) {
                            elem.click();
                            return true;
                        }
                    }
                    return false;
                """
                button_clicked = driver.execute_script(js_click_any_element)
                if button_clicked:
                    logger.info("成功点击页面上的任意可点击元素")
                    time.sleep(3)  # 等待页面加载
                    return True
            except Exception as e:
                logger.warning(f"点击任意元素失败: {e}")
        
        logger.error("所有方法都无法处理内容警告页面")
        return False
    except Exception as e:
        logger.error(f"处理内容警告页面时出错: {e}")
        return False

class JsonDataWriter:
    """将爬取的数据写入JSON文件"""
    
    def __init__(self, output_dir=OUTPUT_DIR):
        """初始化数据写入器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        self.saved_files = []  # 记录所有保存的文件路径
    
    def write_review(self, review_data):
        """将评论数据写入文件
        
        Args:
            review_data: 评论数据
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
        if not review_data:
            logger.warning("尝试保存空的评论数据")
            return None
        
        try:
            # 根据游戏ID和评论ID创建文件名
            app_id = review_data.get('app_id', 'unknown')
            review_id = review_data.get('review_id', f"review_{int(time.time())}")
            
            # 创建游戏目录
            game_dir = os.path.join(self.output_dir, f"app_{app_id}")
            os.makedirs(game_dir, exist_ok=True)
            
            # 写入JSON文件
            file_path = os.path.join(game_dir, f"{review_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(review_data, f, ensure_ascii=False, indent=2)
                
            # 记录保存的文件
            self.saved_files.append(file_path)
            logger.info(f"成功保存评论数据到: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"保存评论数据失败: {e}")
            return None
    
    def get_saved_files(self):
        """获取所有已保存的文件列表
        
        Returns:
            list: 文件路径列表
        """
        return self.saved_files 

class CsvDataWriter:
    """将爬取的数据写入CSV文件"""
    
    def __init__(self, output_dir=OUTPUT_DIR, timestamp=None):
        """初始化数据写入器
        
        Args:
            output_dir: 输出目录
            timestamp: 文件名时间戳（可选）
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.saved_files = {}
        self.headers = [
            'app_id', 'game_title', 'review_id', 'user_name', 'steam_id', 
            'content', 'recommended', 'posted_date', 'hours_played', 
            'helpful_count', 'total_votes', 'comment_count', 'crawl_time'
        ]
        self.timestamp = timestamp or time.strftime("%Y%m%d_%H%M%S")
    
    def write_review(self, review_data):
        """将评论数据写入CSV文件
        
        Args:
            review_data: 评论数据
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
        if not review_data:
            logger.warning("尝试保存空的评论数据")
            return None
        
        try:
            app_id = review_data.get('app_id', 'unknown')
            game_title = review_data.get('game_title', f'App_{app_id}')
            safe_title = re.sub(r'[\\/:*?"<>|]', '_', game_title)
            # 使用实例的时间戳
            file_path = os.path.join(self.output_dir, f"{safe_title}_评论_{app_id}_{self.timestamp}.csv")
            file_exists = os.path.exists(file_path)
            with open(file_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                if not file_exists:
                    writer.writeheader()
                    self.saved_files[file_path] = 0
                row_data = {}
                for header in self.headers:
                    row_data[header] = review_data.get(header, '')
                writer.writerow(row_data)
                if file_path in self.saved_files:
                    self.saved_files[file_path] += 1
                else:
                    self.saved_files[file_path] = 1
            logger.info(f"成功保存评论数据到: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"保存评论数据失败: {e}")
            return None
    
    def get_saved_files(self):
        """获取所有已保存的文件列表
        
        Returns:
            dict: 文件路径及其对应的行数
        """
        return self.saved_files

class SteamSimpleCrawlerEdge:
    """简化版Steam爬虫类 - Edge浏览器版本 - 无需登录，只处理年龄限制和内容警告"""
    
    def __init__(self, use_headless=False, data_writer=None):
        """初始化Steam爬虫
        
        Args:
            use_headless: 是否使用无头模式
            data_writer: 数据写入器对象
        """
        # 初始化基本属性
        self.use_headless = use_headless
        self.driver = None
        self.data_writer = data_writer
        self.total_reviews_count = 0
        self.comments_count = 0
        self.successful_reviews = 0
        self.failed_reviews = 0
        
        # 进度回调函数
        self.progress_callback = None
        
        # 记录初始化信息
        logger.info(f"初始化Edge版本Steam爬虫，无头模式: {use_headless}")
        logger.info(f"数据写入器: {data_writer.__class__.__name__ if data_writer else 'None'}")
        
        # 记录操作系统信息
        logger.info(f"操作系统: {platform.system()} {platform.release()}")
        
        # 初始化WebDriver
        try:
            self.setup_driver()
        except Exception as e:
            logger.error(f"初始化WebDriver失败: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def set_progress_callback(self, callback_func):
        """设置进度回调函数
        
        Args:
            callback_func: 回调函数，接收三个参数：phase(阶段)、progress(进度0-1)、message(消息)
        """
        self.progress_callback = callback_func
        
    def report_progress(self, phase, progress, message):
        """报告当前进度
        
        Args:
            phase: 当前阶段，'scroll'或'extract'
            progress: 进度，0到1之间的浮点数
            message: 进度消息
        """
        if self.progress_callback:
            self.progress_callback(phase, progress, message)
    
    def setup_driver(self):
        """初始化WebDriver"""
        try:
            logger.info("设置Edge WebDriver...")
            self.driver = setup_driver(self.use_headless)
            logger.info("Edge WebDriver设置完成")
        except Exception as e:
            logger.error(f"设置WebDriver失败: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def close(self):
        """关闭爬虫和浏览器"""
        if self.driver:
            try:
                logger.info("关闭浏览器...")
                self.driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器出错: {e}")
                logger.error(traceback.format_exc())
    
    def handle_age_verification(self, app_id):
        """处理评论页面特有的年龄验证
        
        Args:
            app_id: 游戏AppID
            
        Returns:
            bool: 是否成功处理年龄验证
        """
        logger.info("开始处理评论页面的年龄验证...")
        
        try:
            # 评论页面可能有特殊的年龄验证表单
            # 检查页面内容
            page_source = self.driver.page_source.lower()
            
            # 确认是否需要年龄验证
            if "agecheck" not in page_source and "age verification" not in page_source:
                logger.info("未检测到年龄验证表单，无需处理")
                return True
            
            logger.info("检测到评论页面的年龄验证表单，尝试处理...")
            
            # 方法1: 查找并点击常见的成人内容验证选项（常见于评论页面）
            try:
                # 查找输入1990年的选择器
                year_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "select[name='ageYear'], select.ageYear, select#ageYear, [class*='year'], [id*='year'], [name*='year']")
                
                if year_elements:
                    for year_elem in year_elements:
                        if year_elem.is_displayed():
                            logger.info("找到年份选择框，设置为1990年")
                            self.driver.execute_script("arguments[0].value = '1990';", year_elem)
                            logger.info("已设置年龄为1990年")
                    
                    # 查找月份选择器
                    month_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                        "select[name='ageMonth'], select.ageMonth, select#ageMonth, [class*='month'], [id*='month'], [name*='month']")
                    
                    if month_elements:
                        for month_elem in month_elements:
                            if month_elem.is_displayed():
                                self.driver.execute_script("arguments[0].value = '1';", month_elem)
                                logger.info("已设置月份为1月")
                    
                    # 查找日期选择器
                    day_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                        "select[name='ageDay'], select.ageDay, select#ageDay, [class*='day'], [id*='day'], [name*='day']")
                    
                    if day_elements:
                        for day_elem in day_elements:
                            if day_elem.is_displayed():
                                self.driver.execute_script("arguments[0].value = '1';", day_elem)
                                logger.info("已设置日期为1日")
                    
                    # 查找提交按钮 - 评论页面的年龄验证按钮可能有不同的标识
                    submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                        "input[type='submit'], button[type='submit'], .btnv6_blue_hoverfade, .btn_blue_steamui, [class*='submit'], [class*='continue'], [class*='proceed']")
                    
                    for button in submit_buttons:
                        if button.is_displayed():
                            logger.info(f"找到提交按钮: {button.text if button.text else '(无文本)'}")
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(3)
                            logger.info("已点击提交按钮")
                            
                            # 检查是否已成功通过验证
                            if "agecheck" not in self.driver.current_url.lower() and "age verification" not in self.driver.page_source.lower():
                                logger.info("方法1成功：已通过评论页面的年龄验证")
                                return True
            except Exception as e:
                logger.warning(f"方法1处理评论页面年龄验证失败: {e}")
            
            # 方法2: 尝试点击任何可见的按钮（最后的手段）
            try:
                # 查找页面上所有可点击的按钮
                all_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                    "input[type='submit'], button, .btn, [class*='button'], a[href*='agecheck'], a[href*='proceed'], a[href*='continue']")
                
                for button in all_buttons:
                    if button.is_displayed():
                        button_text = button.text.lower() if button.text else ""
                        if ("view" in button_text or "enter" in button_text or 
                            "continue" in button_text or "proceed" in button_text or
                            "submit" in button_text or "确认" in button_text or 
                            "提交" in button_text or "查看" in button_text):
                            
                            logger.info(f"尝试点击按钮: {button.text if button.text else '(无文本)'}")
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(3)
                            
                            # 检查是否已成功通过验证
                            if "agecheck" not in self.driver.current_url.lower() and "age verification" not in self.driver.page_source.lower():
                                logger.info("方法2成功：已通过评论页面的年龄验证")
                                return True
            except Exception as e:
                logger.warning(f"方法2处理评论页面年龄验证失败: {e}")
            
            # 方法3: 尝试使用URL参数绕过年龄验证
            try:
                # 构造评论页面URL并添加mature_content参数
                reviews_url = f"https://steamcommunity.com/app/{app_id}/reviews/?browsefilter=toprated&mature_content=1"
                
                logger.info(f"尝试通过URL参数绕过年龄验证: {reviews_url}")
                self.driver.get(reviews_url)
                time.sleep(3)
                
                # 检查是否已成功通过验证
                if "agecheck" not in self.driver.current_url.lower() and "age verification" not in self.driver.page_source.lower():
                    logger.info("方法3成功：已通过URL参数绕过年龄验证")
                    return True
            except Exception as e:
                logger.warning(f"方法3处理评论页面年龄验证失败: {e}")
            
            logger.warning("所有年龄验证处理方法都已尝试但失败")
            return False
        
        except Exception as e:
            logger.error(f"处理评论页面年龄验证时出错: {e}")
            return False
    
    def extract_game_info(self):
        """从当前页面提取游戏信息
        
        Returns:
            dict: 游戏信息
        """
        game_info = {
            'title': '未知',
            'app_id': None,
            'url': self.driver.current_url,
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # 提取游戏标题
            try:
                title_elem = self.driver.find_element(By.CSS_SELECTOR, ".apphub_AppName")
                game_info['title'] = title_elem.text.strip()
            except NoSuchElementException:
                try:
                    # 备用标题选择器
                    title_elem = self.driver.find_element(By.CSS_SELECTOR, "#appHubAppName, .game_title, .game_area_title h1")
                    game_info['title'] = title_elem.text.strip()
                except:
                    logger.warning("未找到游戏标题")
            
            # 提取AppID
            app_id_match = re.search(r'/app/(\d+)', self.driver.current_url)
            if app_id_match:
                game_info['app_id'] = app_id_match.group(1)
            
            # 尝试提取其他游戏信息，如标签、发行日期等
            try:
                # 游戏标签
                tags = self.driver.find_elements(By.CSS_SELECTOR, ".app_tag")
                game_info['tags'] = [tag.text.strip() for tag in tags if tag.text.strip()]
            except:
                game_info['tags'] = []
            
            logger.info(f"成功提取游戏信息: {game_info['title']} (AppID: {game_info['app_id']})")
            return game_info
            
        except Exception as e:
            logger.error(f"提取游戏信息出错: {e}")
            return game_info

    def process_game_page(self, game_url, max_reviews=None):
        """处理游戏页面，爬取基本信息和评论
        
        Args:
            game_url: 游戏页面URL
            max_reviews: 最大爬取评论数，None表示无限制
            
        Returns:
            dict: 游戏基本信息
        """
        try:
            logger.info(f"处理游戏: {game_url}")
            
            # 提取AppID
            app_id = None
            app_id_match = re.search(r'/app/(\d+)', game_url)
            if app_id_match:
                app_id = app_id_match.group(1)
            elif game_url.isdigit():
                app_id = game_url
            
            # 初始化游戏信息
            game_info = {
                'title': '未知',
                'app_id': app_id,
                'url': game_url,
                'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 访问评论页面
            if app_id:
                # 构造评论页面URL
                reviews_url = f"https://steamcommunity.com/app/{app_id}/reviews/?browsefilter=toprated"
                logger.info(f"访问评论页面: {reviews_url}")
                
                try:
                    self.driver.get(reviews_url)
                    time.sleep(IMPLICIT_WAIT)
                    
                    # 处理可能的年龄验证
                    if handle_age_check(self.driver):
                        logger.info("已通过年龄验证")
                    
                    # 评论页面的特殊年龄验证处理
                    self.handle_age_verification(app_id)
                    
                    # 检查是否是内容警告页面
                    if is_content_warning_page(self.driver):
                        logger.info("检测到内容警告页面，尝试处理...")
                        if handle_content_warning_page(self.driver):
                            logger.info("成功处理内容警告页面")
                        else:
                            logger.warning("处理内容警告页面失败")
                    
                    # 确认是否成功加载评论页面
                    if "reviews" in self.driver.current_url.lower():
                        logger.info("成功加载评论页面")
                        # 尝试获取游戏标题
                        try:
                            title_elem = self.driver.find_element(By.CSS_SELECTOR, ".apphub_AppName")
                            game_info['title'] = title_elem.text.strip()
                            logger.info(f"从评论页面获取游戏标题: {game_info['title']}")
                        except:
                            logger.warning("无法从评论页面获取游戏标题")
                        
                        # 处理评论，传递max_reviews参数
                        self.process_reviews_page(reviews_url, game_info, max_reviews)
                        return game_info
                    else:
                        logger.warning("未能成功加载评论页面")
                except Exception as e:
                    logger.error(f"访问评论页面出错: {e}")
            else:
                logger.warning("无法提取AppID，无法处理游戏评论")
            
            return game_info
                
        except Exception as e:
            logger.error(f"处理游戏页面出错: {e}")
            return {}
    
    def process_reviews_page(self, reviews_url, game_info, max_reviews=None):
        """处理评论页面，爬取多条评论
        
        先加载所有评论，再一次性提取数据，评论超过5000条时分批处理
        
        Args:
            reviews_url: 评论页面URL
            game_info: 游戏基本信息
            max_reviews: 最大爬取评论数，None表示无限制
            
        Returns:
            int: 成功爬取的评论数
        """
        try:
            # 确认是否成功加载评论页面
            if "reviews" not in self.driver.current_url.lower():
                logger.error("未成功加载评论页面")
                
                # 检查是否仍在年龄验证页面
                if "agecheck" in self.driver.current_url.lower() or "age verification" in self.driver.page_source.lower():
                    logger.error("仍然处于年龄验证页面，无法访问评论")
                    return 0
                
                # 检查是否仍在内容警告页面
                if is_content_warning_page(self.driver):
                    logger.error("仍然处于内容警告页面，无法访问评论")
                    return 0
                
                return 0
            
            # 待处理的评论总数
            processed_count = 0
            batch_size = 5000  # 每批次处理的评论数量
            
            # 记录开始时间，用于日志
            start_time = time.time()
            
            # 第一阶段：滚动加载评论 --------------------------
            logger.info(f"第一阶段：滚动加载评论 (最大评论数限制: {max_reviews if max_reviews else '无限制'})")
            self.report_progress("scroll", 0.0, "开始加载评论")
            
            # 等待初始评论加载
            try:
                WebDriverWait(self.driver, PAGE_LOAD_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".apphub_Card"))
                )
            except TimeoutException:
                logger.warning("等待评论加载超时")
            
            last_reviews_count = 0
            same_count_times = 0  # 连续相同评论数的次数，用于判断是否已加载完所有评论
            scroll_count = 0
            
            # 记录滚动开始时间，用于计算滚动速度和估计剩余时间
            scroll_start_time = time.time()
            
            # 滚动循环 - 仅滚动必要的次数，直到满足加载条件
            while True:
                # 获取当前页面所有评论
                review_cards = self.driver.find_elements(By.CSS_SELECTOR, ".apphub_Card")
                current_reviews_count = len(review_cards)
                
                # 重要：如果设置了评论数限制，且已达到或超过目标数量，立即停止滚动
                if max_reviews is not None and current_reviews_count >= max_reviews:
                    logger.info(f"已达到目标评论数: {max_reviews}，停止滚动")
                    self.report_progress("scroll", 0.99, f"已加载 {current_reviews_count} 条评论，达到目标数量")
                    break
                
                # 计算并报告滚动进度
                if max_reviews is not None:
                    progress = min(current_reviews_count / max_reviews, 0.99)
                    self.report_progress("scroll", progress, f"已加载 {current_reviews_count} 条评论")
                else:
                    # 没有设置最大值时，根据滚动次数计算进度
                    progress = min(scroll_count / 200, 0.99)  # 假设200次滚动为满进度
                    self.report_progress("scroll", progress, f"已加载 {current_reviews_count} 条评论，滚动次数: {scroll_count}")
                
                # 计算滚动速度和估计剩余时间（仅当有增量时）
                if current_reviews_count > last_reviews_count and scroll_count > 0:
                    elapsed_time = time.time() - scroll_start_time
                    scroll_speed = current_reviews_count / elapsed_time if elapsed_time > 0 else 0
                    
                    # 如果设置了最大评论数
                    if max_reviews is not None:
                        remaining = max_reviews - current_reviews_count
                        if remaining > 0 and scroll_speed > 0:
                            est_time = remaining / scroll_speed
                            logger.info(f"当前加载速度: {scroll_speed:.1f}评论/秒，预计还需 {est_time/60:.1f}分钟")
                            self.report_progress("scroll", progress, f"加载速度: {scroll_speed:.1f}评论/秒，预计还需 {est_time/60:.1f}分钟")
                
                # 每100条评论显示一次日志
                if current_reviews_count // 100 > last_reviews_count // 100:
                    logger.info(f"已加载 {current_reviews_count} 条评论，滚动次数: {scroll_count}")
                
                # 判断是否已加载完所有评论
                if current_reviews_count == last_reviews_count:
                    same_count_times += 1
                    # 连续3次滚动后评论数量未增加，认为已加载完成
                    if same_count_times >= 3:
                        logger.info("连续多次滚动后评论数量未增加，认为已加载完所有评论")
                        break
                else:
                    same_count_times = 0  # 重置计数器
                
                # 记录当前评论数，用于下次比较
                last_reviews_count = current_reviews_count
                
                # 滚动到页面底部以加载更多评论
                try:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    
                    # 如果有指定的评论数限制，减少等待时间以加快处理
                    if max_reviews is not None:
                        wait_time = SCROLL_PAUSE_TIME * 0.5  # 对于有限制的爬取，减少等待时间
                    else:
                        wait_time = SCROLL_PAUSE_TIME
                        
                    time.sleep(wait_time)  # 等待加载
                    
                    # 尝试点击"显示更多评论"按钮（如果存在）
                    try:
                        load_more_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                            ".apphub_ShowMoreComments, .apphub_ShowMoreCommentsButton, .apphub_LoadMoreButton")
                        for btn in load_more_buttons:
                            if btn.is_displayed():
                                logger.info("点击'显示更多评论'按钮")
                                self.driver.execute_script("arguments[0].click();", btn)
                                time.sleep(wait_time)  # 等待加载
                    except:
                        pass  # 忽略按钮不存在的情况
                    
                except Exception as e:
                    logger.error(f"滚动加载更多评论出错: {e}")
                    break
                
                scroll_count += 1
                
                # 添加额外检查：如果设置了max_reviews，并且当前评论已达到目标数量的80%以上，减少等待时间，加快最后阶段
                if max_reviews is not None and current_reviews_count >= max_reviews * 0.8:
                    logger.info(f"已接近目标评论数，加快加载过程")
                    time.sleep(SCROLL_PAUSE_TIME * 0.25)  # 进一步缩短等待时间
                    
                # 安全措施：如果滚动过多次（超过max_reviews的10倍），强制退出循环
                if max_reviews is not None and scroll_count > max_reviews * 10:
                    logger.warning(f"滚动次数过多，强制退出滚动循环，已加载 {current_reviews_count} 条评论")
                    break
            
            # 滚动完成后，获取所有评论卡片
            all_review_cards = self.driver.find_elements(By.CSS_SELECTOR, ".apphub_Card")
            total_reviews = len(all_review_cards)
            
            # 应用最大评论数限制
            if max_reviews is not None and total_reviews > max_reviews:
                logger.info(f"评论数量超过限制，截取前 {max_reviews} 条")
                all_review_cards = all_review_cards[:max_reviews]
                total_reviews = len(all_review_cards)
            
            elapsed_time = time.time() - start_time
            logger.info(f"滚动完成，共加载 {total_reviews} 条评论，用时 {elapsed_time:.1f} 秒，开始提取数据")
            self.report_progress("scroll", 1.0, f"滚动完成，已加载 {total_reviews} 条评论，用时 {elapsed_time:.1f} 秒")
            
            # 第二阶段：提取评论数据 --------------------------
            logger.info("第二阶段：提取评论数据")
            self.report_progress("extract", 0.0, "开始提取评论数据")
            
            # 判断是否需要分批处理
            if total_reviews > batch_size:
                logger.info(f"评论数量超过 {batch_size}，将分批处理")
                self.report_progress("extract", 0.05, f"评论数量为 {total_reviews}，将分批处理")
                
                # 计算批次数
                num_batches = (total_reviews + batch_size - 1) // batch_size
                
                for batch_num in range(num_batches):
                    start_idx = batch_num * batch_size
                    end_idx = min(start_idx + batch_size, total_reviews)
                    batch_cards = all_review_cards[start_idx:end_idx]
                    
                    logger.info(f"处理第 {batch_num+1}/{num_batches} 批评论，数量: {len(batch_cards)}")
                    self.report_progress("extract", batch_num / num_batches, 
                                      f"处理第 {batch_num+1}/{num_batches} 批评论，数量: {len(batch_cards)}")
                    
                    # 处理这一批次的评论
                    batch_processed = self._process_review_batch(batch_cards, game_info, batch_num+1, num_batches)
                    processed_count += batch_processed
            else:
                # 数量较少，直接处理
                processed_count = self._process_review_batch(all_review_cards, game_info, 1, 1)
            
            logger.info(f"评论提取完成，共成功处理 {processed_count} 条评论")
            self.report_progress("extract", 1.0, f"评论提取完成，共处理 {processed_count} 条评论")
            return processed_count
            
        except Exception as e:
            logger.error(f"处理评论页面出错: {e}")
            self.report_progress("extract", 1.0, f"处理评论页面出错: {e}")
            return 0
    
    def _process_review_batch(self, review_cards, game_info, batch_num=1, total_batches=1):
        """处理一批评论卡片
        
        Args:
            review_cards: 评论卡片元素列表
            game_info: 游戏基本信息
            batch_num: 当前批次编号
            total_batches: 总批次数
            
        Returns:
            int: 成功处理的评论数
        """
        batch_size = len(review_cards)
        processed_count = 0
        
        # 处理每张评论卡片
        for i, card in enumerate(review_cards):
            try:
                # 计算总体进度百分比
                overall_progress = ((batch_num - 1) / total_batches) + ((i + 1) / batch_size / total_batches)
                overall_percent = min(round(overall_progress * 100), 100)
                
                # 每处理50条评论或处理到整百分比时输出日志
                if i % 50 == 0 or overall_percent % 10 == 0:
                    logger.info(f"批次 {batch_num}/{total_batches}: 已处理 {i}/{batch_size} 条评论，总进度: {overall_percent}%")
                    
                    # 报告进度
                    extract_progress = (batch_num - 1 + (i+1) / batch_size) / total_batches
                    extract_progress = min(extract_progress, 0.99)  # 确保不超过99%
                    self.report_progress("extract", extract_progress, 
                                      f"批次 {batch_num}/{total_batches}: 已处理 {i+1}/{batch_size} 条评论，总进度: {overall_percent}%")
                
                # 滚动到评论可见，确保DOM完全加载
                self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
                time.sleep(0.05)  # 很短暂的停顿，确保DOM渲染但不影响速度
                
                # 提取评论数据
                review_data = self.extract_review_data(card, game_info)
                if review_data:
                    # 保存评论数据
                    if self.data_writer:
                        self.data_writer.write_review(review_data)
                    processed_count += 1
                    self.successful_reviews += 1
                else:
                    self.failed_reviews += 1
                
            except Exception as e:
                logger.error(f"处理评论卡片出错: {e}")
                self.failed_reviews += 1
        
        logger.info(f"批次 {batch_num}/{total_batches} 完成，处理了 {processed_count}/{batch_size} 条评论")
        self.report_progress("extract", batch_num / total_batches, 
                          f"批次 {batch_num}/{total_batches} 完成，处理了 {processed_count}/{batch_size} 条评论")
        return processed_count
    
    def extract_review_data(self, review_card, game_info):
        """从评论卡片提取评论数据
        
        Args:
            review_card: WebElement，评论卡片元素
            game_info: dict，游戏基本信息
            
        Returns:
            dict: 评论数据，提取失败返回None
        """
        try:
            review_data = {
                'app_id': game_info.get('app_id'),
                'game_title': game_info.get('title'),
                'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 提取评论ID
            try:
                card_id = review_card.get_attribute("id")
                if card_id:
                    review_data['review_id'] = card_id
            except:
                review_data['review_id'] = f"unknown_{int(time.time())}_{random.randint(1000, 9999)}"
            
            # 提取用户信息
            try:
                user_elem = review_card.find_element(By.CSS_SELECTOR, ".apphub_CardContentAuthorName a")
                review_data['user_name'] = user_elem.text.strip()
                review_data['user_profile'] = user_elem.get_attribute("href")
                
                # 从用户资料URL中提取steamID
                steam_id_match = re.search(r'/profiles/(\d+)', review_data['user_profile'])
                if steam_id_match:
                    review_data['steam_id'] = steam_id_match.group(1)
            except:
                review_data['user_name'] = "未知用户"
            
            # 提取评论内容
            try:
                content_elem = review_card.find_element(By.CSS_SELECTOR, ".apphub_CardTextContent")
                review_data['content'] = content_elem.text.strip()
            except:
                review_data['content'] = ""
            
            # 提取评价（好评/差评）
            try:
                title_elem = review_card.find_element(By.CSS_SELECTOR, ".title")
                title_text = title_elem.text.lower()
                if "推荐" in title_text or "recommended" in title_text:
                    review_data['recommended'] = True
                elif "不推荐" in title_text or "not recommended" in title_text:
                    review_data['recommended'] = False
                else:
                    # 尝试从HTML类判断
                    if "voted_up" in review_card.get_attribute("class"):
                        review_data['recommended'] = True
                    elif "voted_down" in review_card.get_attribute("class"):
                        review_data['recommended'] = False
                    else:
                        review_data['recommended'] = None
            except:
                review_data['recommended'] = None
            
            # 提取评论日期
            try:
                date_elem = review_card.find_element(By.CSS_SELECTOR, ".date_posted")
                review_data['posted_date'] = date_elem.text.replace("Posted: ", "").strip()
            except:
                review_data['posted_date'] = ""
            
            # 提取游戏时长
            try:
                hours_text = review_card.find_element(By.CSS_SELECTOR, ".hours").text
                hours_match = re.search(r'(\d+\.?\d*)', hours_text)
                if hours_match:
                    review_data['hours_played'] = float(hours_match.group(1))
                else:
                    review_data['hours_played'] = 0
            except:
                review_data['hours_played'] = 0
            
            # 提取评论有用性
            try:
                helpful_elem = review_card.find_element(By.CSS_SELECTOR, ".found_helpful")
                helpful_text = helpful_elem.text
                helpful_match = re.search(r'(\d+).*?(\d+)', helpful_text)
                if helpful_match:
                    review_data['helpful_count'] = int(helpful_match.group(1))
                    review_data['total_votes'] = int(helpful_match.group(2))
                else:
                    review_data['helpful_count'] = 0
                    review_data['total_votes'] = 0
            except:
                review_data['helpful_count'] = 0
                review_data['total_votes'] = 0
            
            # 提取评论下的回复数量
            try:
                comment_button = review_card.find_element(By.CSS_SELECTOR, ".apphub_CardCommentButton")
                comment_text = comment_button.text.strip()
                comment_match = re.search(r'(\d+)', comment_text)
                if comment_match:
                    review_data['comment_count'] = int(comment_match.group(1))
                else:
                    review_data['comment_count'] = 0
            except:
                review_data['comment_count'] = 0
            
            if review_data.get('content'):
                logger.info(f"成功提取评论: {review_data['user_name'][:10]}... - {review_data['content'][:30]}...")
                return review_data
            else:
                logger.warning("评论内容为空，跳过")
                return None
                
        except Exception as e:
            logger.error(f"提取评论数据出错: {e}")
            return None
    
    def run(self, url=None, max_reviews=None):
        """运行爬虫，处理单个URL
        
        Args:
            url: 要爬取的游戏URL
            max_reviews: 最大爬取评论数，None表示无限制
            
        Returns:
            dict: 爬取结果统计信息
        """
        try:
            if not url:
                logger.error("未提供游戏URL，无法爬取")
                return None
            
            # 记录爬虫启动和参数
            logger.info(f"启动Edge爬虫，URL: {url}, 最大评论数: {max_reviews if max_reviews is not None else '无限制'}")
            
            # 提取AppID
            app_id = None
            app_id_match = re.search(r'/app/(\d+)', url)
            if app_id_match:
                app_id = app_id_match.group(1)
            elif url.isdigit():
                app_id = url
                url = f"https://steamcommunity.com/app/{app_id}/reviews/"
            
            logger.info(f"提取的AppID: {app_id}")
            
            # 处理游戏页面（这里面已经会处理评论）
            game_info = self.process_game_page(url, max_reviews)
            
            # 注意：process_game_page已经处理了评论，不需要再次处理
            
            # 输出统计信息
            logger.info("\n========== 爬取统计 ==========")
            logger.info(f"成功爬取评论数: {self.successful_reviews}")
            logger.info(f"失败的评论数: {self.failed_reviews}")
            logger.info("===========================")
            
            # 返回统计信息
            result = {
                "app_id": app_id,
                "game_title": game_info.get('title', '未知游戏'),
                "total_reviews": self.successful_reviews,
                "failed_reviews": self.failed_reviews,
                "status": "完成"
            }
            
            return result
        
        except Exception as e:
            logger.error(f"爬虫运行出错: {e}")
            logger.error(traceback.format_exc())
            return {
                "app_id": app_id if 'app_id' in locals() else None,
                "game_title": game_info.get('title', '未知游戏') if 'game_info' in locals() else '未知游戏',
                "total_reviews": self.successful_reviews,
                "failed_reviews": self.failed_reviews,
                "status": f"错误: {str(e)}"
            }
        finally:
            self.close()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='简化版Steam评论爬虫 - 无需登录')
    parser.add_argument('--url', type=str, required=True, help='要爬取的游戏URL或AppID')
    parser.add_argument('--headless', action='store_true', help='使用无头模式')
    parser.add_argument('--max-reviews', type=int, default=None, help='最大爬取评论数')
    parser.add_argument('--output', type=str, default=OUTPUT_DIR, help='输出目录')
    parser.add_argument('--format', type=str, choices=['json', 'csv'], default='csv', help='输出格式，默认为CSV')
    parser.add_argument('--timestamp', type=str, default=None, help='文件名时间戳（可选）')
    args = parser.parse_args()
    
    # 优先使用命令行参数，否则自动生成
    timestamp = args.timestamp or time.strftime("%Y%m%d_%H%M%S")
    # 根据格式选择数据写入器
    if args.format == 'json':
        data_writer = JsonDataWriter(args.output)
    else:
        data_writer = CsvDataWriter(args.output, timestamp=timestamp)
    
    # 初始化并运行爬虫
    crawler = SteamSimpleCrawlerEdge(use_headless=args.headless, data_writer=data_writer)
    result = crawler.run(args.url, args.max_reviews)
    
    if result:
        logger.info(f"成功爬取游戏: {result['game_title']} (AppID: {result['app_id']})")
        if isinstance(data_writer, CsvDataWriter):
            for file_path, count in data_writer.saved_files.items():
                logger.info(f"评论已保存到: {file_path} (共 {count} 条评论)")
        else:
            logger.info(f"爬取的评论已保存到: {args.output}/app_{result['app_id']}/")
    else:
        logger.error("爬取失败")

if __name__ == "__main__":
    main() 