"""
基础爬虫框架 - 提供通用的爬虫功能
此模块包含爬取各类网站评论的通用功能和基础架构
"""

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pickle
import time
import os
import csv
import re
import json
import sys
import tempfile
import shutil
from abc import ABC, abstractmethod
import platform
import io
import random
import logging
import traceback
from datetime import datetime, timedelta
import urllib.parse
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
from tqdm import tqdm
from colorama import Fore, Style
import requests

class BaseCrawler(ABC):
    """爬虫基类，提供通用功能和抽象方法"""
    
    def __init__(self, use_headless=False, temp_dir=None):
        """
        初始化爬虫
        
        参数:
            use_headless: 是否使用无头模式
            temp_dir: 临时目录路径，如果为None则自动创建
        """
        self.mini_flag = True  # 用于标记是否需要处理迷你播放器
        
        # 创建临时目录
        if temp_dir is None:
            current_folder = os.path.dirname(os.path.abspath(__file__))
            self.temp_dir = tempfile.mkdtemp(dir=current_folder)
        else:
            self.temp_dir = temp_dir
        
        # 初始化浏览器
        self.driver = self._init_browser(use_headless)
        
        # 初始化进度
        self.progress = self._load_progress()
        
        # 确保logs目录存在
        os.makedirs("logs", exist_ok=True)
    
    def _init_browser(self, use_headless):
        """
        初始化浏览器
        
        参数:
            use_headless: 是否使用无头模式
        
        返回:
            WebDriver对象
        """
        chrome_options = Options()
        chrome_options.add_argument(f'--user-data-dir={self.temp_dir}')
        
        # 添加通用浏览器选项
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--start-maximized')
        
        # 添加无头模式
        if use_headless:
            print("已启用无头模式，浏览器将在后台运行...")
            chrome_options.add_argument('--headless=new')
        else:
            print("已禁用无头模式，浏览器将显示界面...")
        
        # 检测操作系统并设置Chrome路径
        os_name = platform.system()
        chrome_path = None
        
        if os_name == "Darwin":  # macOS
            print("检测到macOS系统")
            possible_mac_paths = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '/Applications/Google Chrome.app'
            ]
            for path in possible_mac_paths:
                if os.path.exists(path):
                    chrome_path = path
                    print(f"在Mac上找到Chrome: {chrome_path}")
                    break
        elif os_name == "Windows":
            print("检测到Windows系统")
            possible_win_paths = [
                'C:/Program Files/Google/Chrome/Application/chrome.exe',
                'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google/Chrome/Application/chrome.exe')
            ]
            for path in possible_win_paths:
                if os.path.exists(path):
                    chrome_path = path
                    print(f"在Windows上找到Chrome: {chrome_path}")
                    break
        else:
            print(f"检测到未支持的操作系统: {os_name}，将尝试使用默认设置")
        
        # 如果找到Chrome路径，添加到选项中
        if chrome_path:
            chrome_options.binary_location = chrome_path
            print(f"已设置Chrome路径: {chrome_path}")
        else:
            print("未找到Chrome安装路径，将尝试使用默认路径")
        
        # 尝试多种方式初始化浏览器
        driver = None
        try:
            # 方法1: 使用ChromeDriverManager并指定浏览器路径
            print("尝试初始化浏览器方式1...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("浏览器初始化成功 (方式1)")
        except Exception as e:
            print(f"初始化方式1失败: {e}")
            try:
                # 方法2: 直接使用webdriver.Chrome()
                print("尝试初始化浏览器方式2...")
                driver = webdriver.Chrome(options=chrome_options)
                print("浏览器初始化成功 (方式2)")
            except Exception as e:
                print(f"初始化方式2失败: {e}")
                try:
                    # 方法3: 使用service但不使用ChromeDriverManager
                    print("尝试初始化浏览器方式3...")
                    service = Service()
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    print("浏览器初始化成功 (方式3)")
                except Exception as e:
                    print(f"所有浏览器初始化方法都失败: {e}")
                    print("请确保已正确安装Chrome浏览器和匹配的ChromeDriver")
                    self.reset_progress()
                    sys.exit(1)
        
        return driver
    
    def _load_progress(self):
        """
        加载进度文件
        
        返回:
            进度数据字典
        """
        progress_file = os.path.join("logs", "progress.txt")
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "r", encoding='utf-8-sig') as f:
                    progress = json.load(f)
                print(f"成功加载进度文件: {progress}")
                return progress
            except Exception as e:
                print(f"读取进度文件时出错: {e}")
                print("创建新的进度记录...")
        
        # 默认进度
        return {"game_count": 0, "first_comment_index": 0, "sub_page": 0, "write_parent": 0, "last_game_id": ""}
    
    def save_progress(self, progress):
        """
        保存进度到文件
        
        参数:
            progress: 进度数据字典
        """
        max_retries = 50
        retries = 0

        while retries < max_retries:
            try:
                with open(os.path.join("logs", "progress.txt"), "w", encoding='utf-8') as f:
                    json.dump(progress, f)
                break  # 如果成功保存，跳出循环
            except PermissionError as e:
                retries += 1
                print(f"进度存档时，遇到权限错误Permission denied，文件可能被占用或无写入权限: {e}")
                print(f"等待10s后重试，将会重试50次... (尝试 {retries}/{max_retries})")
                time.sleep(10)  # 等待10秒后重试
        else:
            print("进度存档时遇到权限错误，且已达到最大重试次数50次，退出程序")
            self.reset_progress()
            sys.exit(1)
    
    def reset_progress(self):
        """重置进度文件中的所有计数值"""
        progress = {"game_count": 0, "first_comment_index": 0, "sub_page": 0, "write_parent": 0, "last_game_id": ""}
        try:
            self.save_progress(progress)
            print("已重置所有进度计数")
        except Exception as e:
            print(f"重置进度时出错: {e}")
    
    def write_error_log(self, message):
        """
        写入错误日志
        
        参数:
            message: 错误信息
        """
        with open(os.path.join("logs", "error_log.txt"), "a", encoding='utf-8') as file:
            file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    
    def save_cookies(self, cookies_file):
        """
        保存cookies到文件
        
        参数:
            cookies_file: Cookies文件路径
        """
        with open(cookies_file, 'wb') as f:
            pickle.dump(self.driver.get_cookies(), f)
    
    def load_cookies(self, cookies_file, domain='.taptap.cn'):
        """
        从文件加载cookies
        
        参数:
            cookies_file: Cookies文件路径
            domain: 默认域名
        
        返回:
            是否成功加载cookies
        """
        if os.path.exists(cookies_file):
            with open(cookies_file, 'rb') as f:
                cookies = pickle.load(f)
            for cookie in cookies:
                # 修复 Cookie 域名不匹配和过期问题
                if 'domain' in cookie:
                    # 确保域名与当前网站匹配
                    if cookie['domain'].startswith('.'):
                        cookie['domain'] = cookie['domain']
                    else:
                        cookie['domain'] = domain
                # 删除可能导致问题的 expiry 字段
                if 'expiry' in cookie:
                    del cookie['expiry']
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"添加Cookie时出错: {e}")
            return True
        return False
    
    def manual_login(self, cookies_file=None):
        """
        手动登录
        
        参数:
            cookies_file: 可选的cookies文件路径，用于保存登录状态
        """
        input("请登录，登录成功跳转后，按回车键继续...")
        if cookies_file:
            self.save_cookies(cookies_file)
        print("程序正在继续运行")
    
    def check_page_status(self):
        """
        检查页面状态
        
        返回:
            页面是否正常
        """
        try:
            self.driver.execute_script('javascript:void(0);')
            return True
        except Exception as e:
            print(f"检测页面状态时出错，尝试刷新页面重新加载: {e}")
            self.driver.refresh()
            time.sleep(5)
            return False
    
    def scroll_to_bottom(self, max_scroll_count=500, scroll_pause_time=3, max_scroll_time=1800):
        """
        滚动到页面底部以加载更多内容
        
        参数:
            max_scroll_count: 最大滚动次数
            scroll_pause_time: 每次滚动后等待时间
            max_scroll_time: 最大滚动时间（秒）
        
        返回:
            是否检测到评论
        """
        # 实现滚动逻辑
        comments_detected = False
        comments_detection_attempts = 0
        MAX_COMMENTS_DETECTION_ATTEMPTS = 2
        
        # 添加总体超时机制
        start_time = time.time()
        scroll_count = 0

        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
        except NoSuchWindowException:
            print("浏览器意外关闭...")
            raise

        # 先尝试预滚动到评论区，加快加载过程
        try:
            print("尝试直接滚动到评论区位置...")
            # 尝试查找评论区标记并滚动到那里
            comment_indicators = [
                "//div[contains(@class, 'comment')]", 
                "//h3[contains(text(), '评论')]",
                "//div[@id='comment']", 
                "//div[@id='comments')]",
                "//div[contains(@class, 'review')]",
                "//div[contains(@class, 'review-list')]",
                "//div[contains(@class, 'list')]"
            ]
            
            for indicator in comment_indicators:
                try:
                    comment_section = self.driver.find_elements(By.XPATH, indicator)
                    if comment_section and len(comment_section) > 0:
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", comment_section[0])
                        print(f"已找到并滚动到评论区 (使用 {indicator})")
                        time.sleep(2)  # 等待评论区加载
                        break
                except Exception:
                    continue
        except Exception as e:
            print(f"预滚动到评论区时出错: {e}")

        while scroll_count < max_scroll_count:
            # 检查是否超时
            if time.time() - start_time > max_scroll_time:
                print(f"已达到最大滚动时间限制({max_scroll_time}秒)，结束滚动")
                break
                
            try:
                self.driver.execute_script('javascript:void(0);')
            except Exception as e:
                print(f"检测页面状态时出错，尝试重新加载: {e}")
                self.driver.refresh()
                time.sleep(5)
                print("页面已刷新，继续滚动...")
                time.sleep(scroll_pause_time)
                continue

            try:
                self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                if self.mini_flag:
                    # 处理可能的迷你播放器
                    self.handle_mini_player()
                    self.mini_flag = False
            except NoSuchWindowException:
                print("浏览器意外关闭...")
                raise

            # 每次滚动都尝试检测评论，增加成功率
            print(f"滚动 {scroll_count + 1}/{max_scroll_count}，正在检测评论...")
            
            # 尝试检测评论元素
            comment_selectors = self.get_comment_selectors()
            
            for selector in comment_selectors:
                comment_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if comment_elements and len(comment_elements) > 0:
                    print(f"已检测到评论加载! 使用选择器 '{selector}' 找到 {len(comment_elements)} 条评论")
                    comments_detected = True
                    break
            
            if comments_detected:
                print("成功检测到评论，继续滚动以确保加载更多评论...")
                scroll_count += 1  # 继续滚动几次以确保加载更多评论
            
            time.sleep(scroll_pause_time)
            
            try:
                new_height = self.driver.execute_script("return document.documentElement.scrollHeight")
            except NoSuchWindowException:
                print("页面向下滚动时，浏览器意外关闭...")
                raise

            if new_height == last_height:
                print("页面高度不再增加，可能已滚动到底部")
                
                # 如果高度不再变化但还没检测到评论，额外等待一段时间并再次检查
                if not comments_detected and comments_detection_attempts < MAX_COMMENTS_DETECTION_ATTEMPTS:
                    print("页面已滚动到底但未检测到评论，等待额外时间...")
                    comments_detection_attempts += 1
                    time.sleep(scroll_pause_time * 2)  # 额外等待时间
                    
                    # 再次检查评论
                    for selector in comment_selectors:
                        comment_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if comment_elements and len(comment_elements) > 0:
                            print(f"在额外等待后检测到评论! 使用选择器 '{selector}'")
                            comments_detected = True
                            break
                    
                    if not comments_detected:
                        print(f"额外等待后仍未检测到评论 (尝试 {comments_detection_attempts}/{MAX_COMMENTS_DETECTION_ATTEMPTS})")
                        if comments_detection_attempts >= MAX_COMMENTS_DETECTION_ATTEMPTS:
                            print("达到最大检测尝试次数，继续处理...")
                            break
                else:
                    # 已经检测到评论或达到最大尝试次数，跳出循环
                    break
                
            last_height = new_height
            scroll_count += 1
            print(f'下滑滚动第{scroll_count}次 / 最大滚动{max_scroll_count}次')
        
        if comments_detected:
            print("已成功检测到评论加载！")
        else:
            print("警告：完成全部滚动后仍未明确检测到评论，将尝试直接处理页面...")
            # 尝试通过JavaScript直接获取页面内容
            try:
                print("尝试通过JavaScript获取页面评论内容...")
                self.driver.execute_script("""
                    console.log("页面上的评论相关元素:");
                    document.querySelectorAll('[class*="comment"],[class*="review"]').forEach(
                        el => console.log(el.tagName + '.' + Array.from(el.classList).join('.'))
                    );
                """)
            except Exception:
                pass

        # 最后再滚动一次到页面底部，确保加载所有内容
        try:
            self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(scroll_pause_time)  # 最后再等待一次
        except Exception:
            pass
        
        # 不管是否检测到评论，都继续处理
        return comments_detected
    
    def handle_mini_player(self):
        """处理迷你播放器，针对不同网站可重写此方法"""
        pass
    
    @abstractmethod
    def get_comment_selectors(self):
        """
        获取评论元素选择器列表
        
        返回:
            CSS选择器列表
        """
        pass
    
    @abstractmethod
    def extract_comments(self, url):
        """
        提取评论数据
        
        参数:
            url: 页面URL
        """
        pass
    
    def cleanup(self):
        """清理资源，关闭浏览器和清理临时文件"""
        try:
            print("正在关闭浏览器...")
            self.driver.quit()
            print("浏览器已关闭")
        except Exception as e:
            print(f"关闭浏览器时出错: {e}")
        
        # 等待更长时间确保浏览器进程完全退出
        print("等待完成，准备清理临时文件...")
        time.sleep(10)
        
        # 清理临时文件夹
        try:
            print(f"尝试清理临时文件夹 {self.temp_dir}...")
            if os.path.exists(self.temp_dir):
                # 尝试多次删除临时文件夹
                for attempt in range(3):
                    try:
                        shutil.rmtree(self.temp_dir, ignore_errors=True)
                        if not os.path.exists(self.temp_dir):
                            print("临时文件夹清理完成")
                            break
                        else:
                            print(f"清理临时文件夹尝试 {attempt+1}/3 失败，等待后重试...")
                            time.sleep(3)
                    except Exception as e:
                        print(f"清理临时文件夹尝试 {attempt+1}/3 出错: {e}")
                        time.sleep(3)
                
                # 如果仍然存在，提示用户手动删除
                if os.path.exists(self.temp_dir):
                    print(f"无法自动清理临时文件夹，您可以手动删除: {self.temp_dir}")
            else:
                print("临时文件夹不存在，无需清理")
        except Exception as e:
            print(f"清理临时文件夹时出错: {e}")
            print(f"您可以手动删除临时文件夹: {self.temp_dir}")
    
    def run(self, url_list_file='game_list.txt'):
        """
        运行爬虫
        
        参数:
            url_list_file: URL列表文件路径
        """
        try:
            # 读取URL列表
            if not os.path.exists(url_list_file):
                print(f"错误：未找到URL列表文件 '{url_list_file}'")
                print(f"请创建一个名为'{url_list_file}'的文件，每行包含一个URL")
                self.reset_progress()
                self.driver.quit()
                sys.exit(1)
            
            print(f"正在读取{url_list_file}文件...")
            with open(url_list_file, 'r', encoding='utf-8') as f:
                urls = f.read().splitlines()
            
            print(f"成功读取 {len(urls)} 个URL")
            for i, url in enumerate(urls):
                print(f"URL {i+1}: {url}")

            # 计算需要跳过的数量
            skip_count = self.progress["game_count"]
            print(f"根据进度文件，需要跳过 {skip_count} 个URL")

            # 处理每个URL
            for url in urls:
                # 如果需要跳过此URL，减少跳过计数并继续循环
                if skip_count > 0:
                    skip_count -= 1
                    continue
                
                try:
                    self.extract_comments(url)
                except Exception as e:
                    error_message = f"处理URL时发生错误: {str(e)}"
                    print(error_message)
                    self.write_error_log(error_message)
                    # 更新进度并继续下一个URL
                    self.progress["game_count"] += 1
                    self.save_progress(self.progress)
            
            print("所有URL处理完成！")
            # 完成后重置进度
            self.reset_progress()
            
        finally:
            # 确保资源被清理
            self.cleanup()

# 数据写入器接口
class DataWriter(ABC):
    """数据写入器抽象基类"""
    
    @abstractmethod
    def write(self, data, filename):
        """
        写入数据到文件
        
        参数:
            data: 要写入的数据
            filename: 文件名
        """
        pass

class CsvWriter(DataWriter):
    """CSV数据写入器"""
    
    def write(self, data, filename):
        """
        写入数据到CSV文件
        
        参数:
            data: 要写入的数据行（字典列表）
            filename: CSV文件名
        """
        file_exists = os.path.isfile(filename)
        max_retries = 50
        retries = 0

        while retries < max_retries:
            try:
                mode = 'a' if file_exists else 'w'
                with open(filename, mode, newline='', encoding='utf-8') as f:
                    if data:
                        fieldnames = data[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        if not file_exists:
                            writer.writeheader()
                        for row in data:
                            writer.writerow(row)
                break
            except PermissionError as e:
                retries += 1
                print(f"将爬取到的数据写入CSV时，遇到权限错误Permission denied，文件可能被占用或无写入权限: {e}")
                print(f"等待10s后重试，将会重试50次... (尝试 {retries}/{max_retries})")
                time.sleep(10)  # 等待10秒后重试
        else:
            print("将爬取到的数据写入CSV时遇到权限错误，且已达到最大重试次数50次，退出程序")
            sys.exit(1)

class ExcelWriter(DataWriter):
    """使用CSV写入数据（原Excel格式改为CSV）"""
    
    def write(self, data, filename):
        """将数据写入文件，如果文件存在则追加，否则创建新文件"""
        # 将Excel文件名改为CSV
        filename = filename.replace('.xlsx', '.csv')
        file_exists = os.path.isfile(filename)
        max_retries = 50
        retries = 0

        while retries < max_retries:
            try:
                if file_exists:
                    # 如果文件存在，读取现有数据并追加
                    try:
                        # 读取现有的CSV文件
                        existing_data = []
                        with open(filename, 'r', encoding='utf-8', newline='') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                existing_data.append(row)
                        
                        # 合并现有数据和新数据
                        combined_data = existing_data + data
                        
                        # 保存合并后的数据
                        if combined_data:
                            fieldnames = combined_data[0].keys()
                            with open(filename, 'w', encoding='utf-8', newline='') as f:
                                writer = csv.DictWriter(f, fieldnames=fieldnames)
                                writer.writeheader()
                                writer.writerows(combined_data)
                    except Exception as e:
                        print(f"读取或更新CSV文件时出错: {e}")
                        # 如果读取失败，创建新文件
                        if data:
                            fieldnames = data[0].keys()
                            with open(filename, 'w', encoding='utf-8', newline='') as f:
                                writer = csv.DictWriter(f, fieldnames=fieldnames)
                                writer.writeheader()
                                writer.writerows(data)
                else:
                    # 如果文件不存在，创建新文件
                    if data:
                        fieldnames = data[0].keys()
                        with open(filename, 'w', encoding='utf-8', newline='') as f:
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(data)
                break  # 如果成功写入，跳出循环
            except PermissionError as e:
                retries += 1
                print(f"将爬取到的数据写入CSV时，遇到权限错误Permission denied，文件可能被占用或无写入权限: {e}")
                print(f"等待10s后重试，将会重试50次... (尝试 {retries}/{max_retries})")
                time.sleep(10)  # 等待10秒后重试
        else:
            print("将爬取到的数据写入CSV时遇到权限错误，且已达到最大重试次数50次，退出程序")
            sys.exit(1)

# 辅助函数
def ask_yes_no_question(question):
    """
    询问用户是/否问题
    
    参数:
        question: 问题文本
    
    返回:
        布尔值表示用户回答
    """
    response = input(f"{question} [y/n]: ").strip().lower()
    return response == 'y' or response == 'yes' 