#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Steam爬虫主模块 - 用于爬取Steam游戏评论
"""

import os
import sys
import time
import random
import json
import re
import logging
from datetime import datetime
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    WebDriverException, StaleElementReferenceException
)

# 导入模块化组件
from steam_config import (
    COOKIES_DIR, COOKIES_FILE, JSON_COOKIES_FILE,
    HELPER_FILE, STEAM_STORE_URL, STEAM_COMMUNITY_URL,
    OUTPUT_DIR, PAGE_LOAD_TIMEOUT, SCRIPT_TIMEOUT,
    IMPLICIT_WAIT, SCROLL_PAUSE_TIME, BATCH_SIZE,
    MAX_RETRIES, AGE_VERIFICATION_GAME_URL, ACCOUNT_INDICATORS
)
from steam_driver import setup_driver, handle_age_check
from steam_cookies import (
    save_cookies, load_cookies, verify_login_status, 
    refresh_login, create_cookies_helper_file
)
# 导入内容警告处理模块
from steam_content_warning_fix import is_content_warning_page, handle_content_warning_page

# 定义额外必要的常量
SCRAPE_COMMENTS = True  # 是否爬取评论回复

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("steam_crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SteamCrawler")

class SteamCrawler:
    """Steam爬虫类 - 负责爬取Steam游戏评论"""
    
    def __init__(self, use_headless=False, data_writer=None, cookies_file=None, existing_driver=None):
        """初始化Steam爬虫
        
        Args:
            use_headless: 是否使用无头模式
            data_writer: 数据写入器对象
            cookies_file: 自定义Cookie文件路径
            existing_driver: 已创建的WebDriver实例，如果提供则直接使用
        """
        # 初始化基本属性
        self.use_headless = use_headless
        self.driver = existing_driver  # 使用已创建的driver或None
        self.data_writer = data_writer
        self.total_reviews_count = 0
        self.comments_count = 0
        self.successful_reviews = 0
        self.failed_reviews = 0
        
        # Cookie设置
        if cookies_file:
            self.cookies_file_json = cookies_file
            self.cookies_file_pickle = cookies_file.replace('.json', '.pkl')
        else:
            self.cookies_file_json = os.path.join(COOKIES_DIR, JSON_COOKIES_FILE)
            self.cookies_file_pickle = os.path.join(COOKIES_DIR, COOKIES_FILE)
        
        # 确保Cookie目录存在
        os.makedirs(COOKIES_DIR, exist_ok=True)
        
        # 检查辅助文件是否存在
        if not os.path.exists(self.cookies_file_json) and not os.path.exists(HELPER_FILE):
            logger.info("创建Cookie辅助脚本...")
            self.create_cookies_helper_file()
        
        # 仅在没有提供driver时初始化WebDriver
        if self.driver is None:
            self.setup_driver()
        else:
            logger.info("使用已创建的WebDriver实例")
        
        # 尝试加载Cookie（仅在初始化新的driver时需要）
        if self.driver is not None and not existing_driver and (os.path.exists(self.cookies_file_json) or os.path.exists(self.cookies_file_pickle)):
            logger.info("尝试加载已保存的Cookie...")
            self.load_cookies()
        
    def setup_driver(self):
        """初始化WebDriver"""
        try:
            self.driver = setup_driver(self.use_headless)
        except Exception as e:
            logger.error(f"设置WebDriver失败: {e}")
            raise
    
    def load_cookies(self):
        """加载保存的Cookie"""
        try:
            if self.driver is None:
                logger.warning("WebDriver未初始化，无法加载Cookie")
                return False
                
            # 加载Cookie到store和community域
            domains = ["store.steampowered.com", "steamcommunity.com"]
            loaded_count = 0
            
            for domain in domains:
                logger.info(f"为 {domain} 加载Cookie...")
                count = load_cookies(
                    self.driver, domain, 
                    self.cookies_file_json, 
                    self.cookies_file_pickle
                )
                if count > 0:
                    logger.info(f"成功为 {domain} 加载了 {count} 个Cookie")
                    loaded_count += count
                else:
                    logger.warning(f"未能为 {domain} 加载Cookie")
            
            # 刷新登录状态
            if loaded_count > 0:
                logger.info("尝试刷新登录状态...")
                refresh_login(self.driver)
            
            return loaded_count > 0
            
        except Exception as e:
            logger.error(f"加载Cookie失败: {e}")
            return False
    
    def save_cookies(self):
        """保存当前的Cookie"""
        try:
            if self.driver is None:
                logger.warning("WebDriver未初始化，无法保存Cookie")
                return False
            
            # 确保Cookie目录存在
            os.makedirs(COOKIES_DIR, exist_ok=True)
            
            logger.info(f"保存Cookie到 {self.cookies_file_json} 和 {self.cookies_file_pickle}")
            return save_cookies(self.driver, self.cookies_file_json, self.cookies_file_pickle)
            
        except Exception as e:
            logger.error(f"保存Cookie失败: {e}")
            return False
    
    def create_cookies_helper_file(self):
        """创建Cookie辅助脚本"""
        try:
            helper_path = create_cookies_helper_file()
            if helper_path:
                logger.info(f"已创建Cookie辅助脚本: {helper_path}")
                logger.info("请运行该脚本并手动登录Steam以获取Cookie")
                return True
        except Exception as e:
            logger.error(f"创建Cookie辅助脚本失败: {e}")
            return False
    
    def is_logged_in(self, url=None):
        """检查是否已登录Steam"""
        return verify_login_status(self.driver, url)
    
    def close(self):
        """关闭爬虫和浏览器"""
        if self.driver:
            try:
                logger.info("关闭浏览器...")
                self.driver.quit()
            except Exception as e:
                logger.error(f"关闭浏览器出错: {e}")
    
    def process_game_page(self, game_url):
        """处理游戏页面，爬取基本信息和评论
        
        Args:
            game_url: 游戏页面URL
            
        Returns:
            dict: 游戏基本信息
        """
        try:
            logger.info(f"处理游戏: {game_url}")
            
            # 首先检查是否已登录
            logger.info("检查登录状态...")
            is_logged_in = self.is_logged_in()
            
            if not is_logged_in:
                logger.warning("检测到未登录状态，尝试重新加载cookies并刷新登录...")
                # 尝试加载cookies
                cookies_loaded = self.load_cookies()
                
                if cookies_loaded:
                    # 刷新登录状态
                    refresh_login(self.driver)
                    
                    # 再次检查登录状态
                    is_logged_in = self.is_logged_in()
                    if is_logged_in:
                        logger.info("成功恢复登录状态")
                    else:
                        logger.warning("尝试恢复登录状态失败，可能需要重新登录")
                        logger.info("建议运行 steam_cookies_helper.py 重新获取登录凭证")
            
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
            
            # 根据模式选择不同的处理方式
            if not self.use_headless:
                # 有头模式：直接访问评论页面
                if app_id:
                    # 构造评论页面URL
                    reviews_url = f"https://steamcommunity.com/app/{app_id}/reviews/?browsefilter=toprated"
                    logger.info(f"有头模式：直接访问评论页面: {reviews_url}")
                    
                    try:
                        self.driver.get(reviews_url)
                        time.sleep(IMPLICIT_WAIT)
                        
                        # 检查是否被重定向到登录页面
                        if "login" in self.driver.current_url.lower():
                            logger.warning("被重定向到登录页面，尝试重新登录...")
                            # 尝试再次加载cookies
                            self.load_cookies()
                            refresh_login(self.driver)
                            # 重新访问评论页面
                            self.driver.get(reviews_url)
                            time.sleep(IMPLICIT_WAIT)
                        
                        # 处理可能的年龄验证
                        if handle_age_check(self.driver):
                            logger.info("已通过年龄验证")
                        
                        # 检查是否成功加载评论页面
                        if "reviews" in self.driver.current_url.lower():
                            logger.info("成功加载评论页面")
                            # 尝试获取游戏标题
                            try:
                                title_elem = self.driver.find_element(By.CSS_SELECTOR, ".apphub_AppName")
                                game_info['title'] = title_elem.text.strip()
                                logger.info(f"从评论页面获取游戏标题: {game_info['title']}")
                            except:
                                logger.warning("无法从评论页面获取游戏标题")
                            
                            # 直接处理评论
                            self.process_reviews_page(self.driver.current_url, game_info)
                            return game_info
                        else:
                            logger.warning("未能成功加载评论页面，尝试常规流程")
                    except Exception as e:
                        logger.error(f"直接访问评论页面出错: {e}")
                        logger.warning("尝试常规流程")
                else:
                    logger.warning("无法提取AppID，尝试常规流程")
            
            # 无头模式或有头模式失败后的常规流程
            logger.info("使用常规流程处理游戏页面")
            
            # 构造游戏商店页面URL
            if app_id:
                store_url = f"https://store.steampowered.com/app/{app_id}"
            else:
                store_url = game_url
            
            logger.info(f"访问游戏商店页面: {store_url}")
            try:
                self.driver.get(store_url)
                time.sleep(IMPLICIT_WAIT)
            except TimeoutException:
                logger.warning(f"加载游戏页面超时: {store_url}")
            
            # 处理年龄验证
            if handle_age_check(self.driver):
                logger.info("已通过年龄验证")
            
            # 提取游戏信息
            game_info = self.extract_game_info()
            
            # 如果仍然没有AppID，尝试从URL提取
            if not game_info.get('app_id') and app_id:
                game_info['app_id'] = app_id
                logger.info(f"使用提取的AppID: {app_id}")
            
            # 获取评论页面URL
            if not game_info.get('app_id'):
                logger.error("未能获取游戏AppID，无法爬取评论")
                return game_info
            
            # 构造评论页面URL并访问
            reviews_url = f"https://steamcommunity.com/app/{game_info['app_id']}/reviews/?browsefilter=toprated"
            logger.info(f"访问评论页面: {reviews_url}")
            
            # 处理评论页面
            self.process_reviews_page(reviews_url, game_info)
            
            return game_info
                
        except Exception as e:
            logger.error(f"处理游戏页面出错: {e}")
            return {}
    
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
            
            # 提取开发商和发行商
            try:
                dev_elem = self.driver.find_elements(By.CSS_SELECTOR, "#developers_list a")
                game_info['developers'] = [dev.text.strip() for dev in dev_elem if dev.text.strip()]
            except:
                game_info['developers'] = []
            
            # 提取发行日期
            try:
                date_elem = self.driver.find_element(By.CSS_SELECTOR, ".date")
                game_info['release_date'] = date_elem.text.strip()
            except:
                game_info['release_date'] = ""
            
            logger.info(f"成功提取游戏信息: {game_info['title']} (AppID: {game_info['app_id']})")
            return game_info
            
        except Exception as e:
            logger.error(f"提取游戏信息出错: {e}")
            return game_info
    
    def process_reviews_page(self, reviews_url, game_info, max_reviews=None):
        """处理评论页面，爬取多条评论
        
        Args:
            reviews_url: 评论页面URL
            game_info: 游戏基本信息
            max_reviews: 最大爬取评论数，None表示无限制
            
        Returns:
            int: 成功爬取的评论数
        """
        try:
            # 在访问评论页面前检查登录状态
            logger.info("在访问评论页面前检查登录状态...")
            is_logged_in = self.is_logged_in()
            
            if not is_logged_in:
                logger.warning("检测到未登录状态，尝试重新加载cookies并刷新登录...")
                # 先访问Steam主页确保域名正确
                logger.info("访问Steam主页以初始化登录状态...")
                self.driver.get(STEAM_STORE_URL)
                time.sleep(IMPLICIT_WAIT)
                
                # 尝试加载cookies
                cookies_loaded = self.load_cookies()
                
                if cookies_loaded:
                    # 刷新登录状态
                    logger.info("成功加载cookies，刷新登录状态...")
                    refresh_login(self.driver)
                    
                    # 再次检查登录状态
                    is_logged_in = self.is_logged_in()
                    if is_logged_in:
                        logger.info("成功恢复登录状态")
                    else:
                        logger.warning("尝试恢复登录状态失败，可能需要重新登录")
                        logger.info("建议运行 steam_cookies_helper.py 重新获取登录凭证")
                else:
                    logger.warning("无法加载cookies，请确保cookies文件存在且有效")
            
            # 检查当前是否已经在评论页面
            current_is_reviews_page = False
            target_app_id = None
            current_app_id = None
            
            # 提取目标URL中的AppID
            target_app_id_match = re.search(r'/app/(\d+)', reviews_url)
            if target_app_id_match:
                target_app_id = target_app_id_match.group(1)
            
            # 检查当前页面状态
            if "reviews" in self.driver.current_url.lower():
                current_is_reviews_page = True
                # 提取当前URL中的AppID
                current_app_id_match = re.search(r'/app/(\d+)', self.driver.current_url)
                if current_app_id_match:
                    current_app_id = current_app_id_match.group(1)
            
            # 判断是否需要重新加载页面
            needs_reload = True
            
            # 如果当前已经在评论页面，且为同一游戏的评论，则无需重新加载
            if current_is_reviews_page and current_app_id and target_app_id and current_app_id == target_app_id:
                logger.info(f"已在目标游戏的评论页面 (AppID: {current_app_id})，无需重新加载")
                needs_reload = False
            
            # 如果需要重新加载页面
            if needs_reload:
                # 访问评论页面
                logger.info(f"访问评论页面: {reviews_url}")
                try:
                    self.driver.get(reviews_url)
                    time.sleep(IMPLICIT_WAIT)
                except TimeoutException:
                    logger.warning(f"加载评论页面超时: {reviews_url}")
                    
                # 处理可能的年龄验证
                if handle_age_check(self.driver):
                    logger.info("已通过评论页面的年龄验证")
                
                # 评论页面的特殊年龄验证处理
                self.handle_review_page_age_verification(reviews_url)
                
                # 检查是否是暴力色情内容警告页面
                if is_content_warning_page(self.driver):
                    logger.info("检测到暴力色情内容警告页面，尝试处理...")
                    if handle_content_warning_page(self.driver):
                        logger.info("成功处理内容警告页面")
                    else:
                        logger.warning("处理内容警告页面失败，可能需要手动登录再尝试")
            else:
                logger.info("已在评论页面，无需重新加载")
                
                # 即使已在评论页面，也检查是否需要年龄验证
                if "agecheck" in self.driver.page_source.lower() or "age verification" in self.driver.page_source.lower():
                    logger.info("检测到当前页面需要年龄验证，尝试处理...")
                    self.handle_review_page_age_verification(reviews_url)
                
                # 检查是否是暴力色情内容警告页面
                if is_content_warning_page(self.driver):
                    logger.info("检测到暴力色情内容警告页面，尝试处理...")
                    if handle_content_warning_page(self.driver):
                        logger.info("成功处理内容警告页面")
                    else:
                        logger.warning("处理内容警告页面失败，可能需要手动登录再尝试")
            
            # 确认是否成功加载评论页面
            if "reviews" not in self.driver.current_url.lower():
                logger.error("未成功加载评论页面")
                
                # 检查是否被重定向到登录页面
                if "login" in self.driver.current_url.lower() or "登录" in self.driver.page_source:
                    logger.error("被重定向到登录页面，请确保已正确登录Steam")
                    logger.info("建议运行 steam_cookies_helper.py 重新获取登录凭证")
                    return 0
                
                # 检查是否仍在年龄验证页面
                if "agecheck" in self.driver.current_url.lower() or "age verification" in self.driver.page_source.lower():
                    logger.error("仍然处于年龄验证页面，无法访问评论")
                    logger.info("建议手动登录Steam完成年龄验证后再尝试")
                    return 0
                
                # 检查是否仍在内容警告页面
                if is_content_warning_page(self.driver):
                    logger.error("仍然处于内容警告页面，无法访问评论")
                    logger.info("建议手动登录Steam并确认内容警告后再尝试")
                    return 0
                
                return 0
            
            processed_count = 0
            page_num = 1
            
            # 改用滚动加载方式处理评论
            logger.info("使用滚动加载方式处理Steam评论")
            last_reviews_count = 0
            same_count_times = 0  # 连续相同评论数的次数，用于判断是否已加载完所有评论
            
            # 等待初始评论加载
            try:
                WebDriverWait(self.driver, PAGE_LOAD_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".apphub_Card"))
                )
            except TimeoutException:
                logger.warning("等待评论加载超时")
            
            while True:
                # 获取当前页面所有评论
                review_cards = self.driver.find_elements(By.CSS_SELECTOR, ".apphub_Card")
                current_reviews_count = len(review_cards)
                logger.info(f"当前页面已加载 {current_reviews_count} 条评论")
                
                if not review_cards:
                    logger.warning("当前页面没有找到评论")
                    break
                
                # 处理新加载的评论，避免重复处理
                for i in range(last_reviews_count, current_reviews_count):
                    if max_reviews and processed_count >= max_reviews:
                        logger.info(f"已达到最大爬取评论数: {max_reviews}")
                        return processed_count
                    
                    try:
                        card = review_cards[i]
                        # 滚动到评论可见位置
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
                        time.sleep(0.5)  # 等待滚动完成
                        
                        # 提取评论数据
                        review_data = self.extract_review_data(card, game_info)
                        if review_data:
                            # 保存评论数据
                            if self.data_writer:
                                self.data_writer.write_review(review_data)
                            processed_count += 1
                            self.successful_reviews += 1
                            
                            # 每处理一批评论后保存一次Cookie
                            if processed_count % BATCH_SIZE == 0:
                                self.save_cookies()
                        else:
                            self.failed_reviews += 1
                        
                    except Exception as e:
                        logger.error(f"处理评论卡片出错: {e}")
                        self.failed_reviews += 1
                
                # 判断是否已加载完所有评论
                if current_reviews_count == last_reviews_count:
                    same_count_times += 1
                    if same_count_times >= 3:  # 连续3次滚动后评论数量未增加，认为已加载完成
                        logger.info("连续多次滚动后评论数量未增加，认为已加载完所有评论")
                        break
                else:
                    same_count_times = 0  # 重置计数器
                
                # 记录当前评论数，用于下次比较
                last_reviews_count = current_reviews_count
                
                # 滚动到页面底部以加载更多评论
                try:
                    logger.info("滚动到页面底部加载更多评论...")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(SCROLL_PAUSE_TIME)  # 等待加载
                    
                    # 尝试点击"显示更多评论"按钮（如果存在）
                    try:
                        load_more_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                            ".apphub_ShowMoreComments, .apphub_ShowMoreCommentsButton, .apphub_LoadMoreButton")
                        for btn in load_more_buttons:
                            if btn.is_displayed():
                                logger.info("点击'显示更多评论'按钮")
                                self.driver.execute_script("arguments[0].click();", btn)
                                time.sleep(SCROLL_PAUSE_TIME)  # 等待加载
                    except:
                        pass  # 忽略按钮不存在的情况
                    
                except Exception as e:
                    logger.error(f"滚动加载更多评论出错: {e}")
                    break
                
                # 为防止无限循环，设置最大滚动次数
                page_num += 1
                if page_num > 50:  # 最多滚动50次
                    logger.warning("已达到最大滚动次数限制(50)，停止加载更多评论")
                    break
            
            logger.info(f"共处理了 {processed_count} 条评论")
            return processed_count
            
        except Exception as e:
            logger.error(f"处理评论页面出错: {e}")
            return 0
    
    def handle_review_page_age_verification(self, reviews_url):
        """处理评论页面特有的年龄验证
        
        Args:
            reviews_url: 评论页面URL
            
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
                # 添加mature_content参数
                if "?" in reviews_url:
                    bypass_url = reviews_url + "&mature_content=1"
                else:
                    bypass_url = reviews_url + "?mature_content=1"
                
                logger.info(f"尝试通过URL参数绕过年龄验证: {bypass_url}")
                self.driver.get(bypass_url)
                time.sleep(3)
                
                # 检查是否已成功通过验证
                if "agecheck" not in self.driver.current_url.lower() and "age verification" not in self.driver.page_source.lower():
                    logger.info("方法3成功：已通过URL参数绕过年龄验证")
                    return True
            except Exception as e:
                logger.warning(f"方法3处理评论页面年龄验证失败: {e}")
            
            # 尝试查找并处理页面上的JavaScript弹窗确认
            try:
                # 尝试直接点击确认
                self.driver.execute_script("if(document.querySelectorAll('div.agegate_text_container.btns a').length > 0) document.querySelectorAll('div.agegate_text_container.btns a')[0].click();")
                time.sleep(1)
                
                # 执行通用的确认点击操作（尝试点击任何确认按钮）
                self.driver.execute_script("""
                    var elements = document.querySelectorAll('a, button, input[type="submit"], [role="button"]');
                    for(var i=0; i<elements.length; i++) {
                        var el = elements[i];
                        var text = el.textContent.toLowerCase();
                        if(text.includes('view') || text.includes('enter') || 
                           text.includes('continue') || text.includes('proceed') ||
                           text.includes('submit') || text.includes('确认') || 
                           text.includes('提交') || text.includes('查看')) {
                            el.click();
                            break;
                        }
                    }
                """)
                time.sleep(3)
                
                # 检查是否已成功通过验证
                if "agecheck" not in self.driver.current_url.lower() and "age verification" not in self.driver.page_source.lower():
                    logger.info("方法4成功：已通过JavaScript点击绕过年龄验证")
                    return True
            except Exception as e:
                logger.warning(f"方法4处理评论页面年龄验证失败: {e}")
            
            # 如果所有方法都失败，记录警告
            logger.warning("所有年龄验证处理方法都已尝试但失败，建议运行steam_cookies_helper.py手动登录并完成年龄验证")
            return False
        
        except Exception as e:
            logger.error(f"处理评论页面年龄验证时出错: {e}")
            return False
    
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
            
            # 检查是否有评论
            if review_data.get('content'):
                # 获取评论数
                try:
                    comment_button = review_card.find_element(By.CSS_SELECTOR, ".apphub_CardCommentButton")
                    comment_text = comment_button.text.strip()
                    comment_match = re.search(r'(\d+)', comment_text)
                    if comment_match:
                        comment_count = int(comment_match.group(1))
                        review_data['comment_count'] = comment_count
                        
                        # 如果有评论，并且配置允许爬取评论，则爬取评论
                        if comment_count > 0 and SCRAPE_COMMENTS:
                            comments = self.extract_review_comments(review_card, comment_count)
                            review_data['comments'] = comments
                            self.comments_count += len(comments)
                except:
                    review_data['comment_count'] = 0
                    review_data['comments'] = []
                
                logger.info(f"成功提取评论: {review_data['user_name'][:10]}... - {review_data['content'][:30]}...")
                return review_data
            else:
                logger.warning("评论内容为空，跳过")
                return None
                
        except Exception as e:
            logger.error(f"提取评论数据出错: {e}")
            return None
    
    def extract_review_comments(self, review_card, expected_count=0):
        """提取评论下的回复
        
        Args:
            review_card: WebElement，评论卡片元素
            expected_count: 预期的评论数
            
        Returns:
            list: 评论列表
        """
        comments = []
        
        try:
            # 点击评论按钮展开评论
            try:
                comment_button = review_card.find_element(By.CSS_SELECTOR, ".apphub_CardCommentButton")
                self.driver.execute_script("arguments[0].click();", comment_button)
                time.sleep(1)  # 等待评论加载
            except:
                logger.warning("未找到评论按钮")
                return comments
            
            # 等待评论加载
            try:
                WebDriverWait(self.driver, IMPLICIT_WAIT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".commentthread_comment"))
                )
            except TimeoutException:
                logger.warning("等待评论加载超时")
            
            # 如果评论过多，可能需要点击"查看更多评论"
            if expected_count > 5:  # Steam通常初始显示5条评论
                try:
                    more_comments_button = review_card.find_element(
                        By.CSS_SELECTOR, 
                        ".commentthread_comments_expansion_link"
                    )
                    self.driver.execute_script("arguments[0].click();", more_comments_button)
                    time.sleep(1)  # 等待更多评论加载
                except NoSuchElementException:
                    # 可能没有"查看更多"按钮
                    pass
                except Exception as e:
                    logger.error(f"加载更多评论出错: {e}")
            
            # 提取所有评论
            comment_elements = review_card.find_elements(By.CSS_SELECTOR, ".commentthread_comment")
            
            for i, comment_elem in enumerate(comment_elements):
                try:
                    comment_data = {}
                    
                    # 提取评论者信息
                    try:
                        author_elem = comment_elem.find_element(By.CSS_SELECTOR, ".commentthread_author_link")
                        comment_data['author'] = author_elem.text.strip()
                        comment_data['author_profile'] = author_elem.get_attribute("href")
                    except:
                        comment_data['author'] = "未知用户"
                    
                    # 提取评论内容
                    try:
                        text_elem = comment_elem.find_element(By.CSS_SELECTOR, ".commentthread_comment_text")
                        comment_data['text'] = text_elem.text.strip()
                    except:
                        comment_data['text'] = ""
                    
                    # 提取评论时间
                    try:
                        date_elem = comment_elem.find_element(By.CSS_SELECTOR, ".commentthread_comment_timestamp")
                        comment_data['timestamp'] = date_elem.text.strip()
                    except:
                        comment_data['timestamp'] = ""
                    
                    if comment_data.get('text'):
                        comments.append(comment_data)
                
                except Exception as e:
                    logger.error(f"提取单条评论出错: {e}")
            
            # 关闭评论区
            try:
                close_button = review_card.find_element(By.CSS_SELECTOR, ".forum_comment_reply_dialog_cancel")
                self.driver.execute_script("arguments[0].click();", close_button)
            except:
                # 没有关闭按钮，不影响功能
                pass
            
            logger.info(f"成功提取 {len(comments)} 条评论回复")
            return comments
            
        except Exception as e:
            logger.error(f"提取评论回复出错: {e}")
            return comments
    
    def extract_comments(self, url=None):
        """提取游戏评论的快捷方法，与TapCrawler接口兼容
        
        Args:
            url: 游戏URL，如果为None则使用当前页面
            
        Returns:
            list: 提取的评论列表
        """
        logger.info(f"提取Steam游戏评论: {url if url else '当前页面'}")
        
        try:
            # 确保有URL
            if not url and self.driver:
                url = self.driver.current_url
                logger.info(f"使用当前页面URL: {url}")
            
            if not url:
                logger.error("未提供URL且不在任何页面上")
                return []
            
            # 检查登录状态
            is_logged_in = self.is_logged_in()
            if not is_logged_in:
                logger.warning("检测到未登录状态，尝试重新加载cookies并刷新登录...")
                # 尝试加载cookies
                cookies_loaded = self.load_cookies()
                
                if cookies_loaded:
                    # 刷新登录状态
                    refresh_login(self.driver)
                    
                    # 再次检查登录状态
                    is_logged_in = self.is_logged_in()
                    if is_logged_in:
                        logger.info("成功恢复登录状态")
                    else:
                        logger.warning("尝试恢复登录状态失败，可能需要重新登录")
                        logger.info("建议运行 steam_cookies_helper.py 重新获取登录凭证")
                        return []
            
            # 提取AppID
            app_id = None
            app_id_match = re.search(r'/app/(\d+)', url)
            if app_id_match:
                app_id = app_id_match.group(1)
            elif url.isdigit():
                app_id = url
            
            # 标记是否已处理成功
            direct_access_success = False
            
            if app_id:
                logger.info(f"提取到游戏AppID: {app_id}")
                
                # 检查当前是否已经在游戏评论页面
                is_already_on_reviews_page = False
                if "reviews" in self.driver.current_url.lower():
                    current_app_id_match = re.search(r'/app/(\d+)', self.driver.current_url)
                    if current_app_id_match and current_app_id_match.group(1) == app_id:
                        logger.info(f"已经在目标游戏的评论页面 (AppID: {app_id})")
                        is_already_on_reviews_page = True
                
                # 有头模式或已在评论页面时直接处理
                if not self.use_headless or is_already_on_reviews_page:
                    reviews_url = f"https://steamcommunity.com/app/{app_id}/reviews/?browsefilter=toprated"
                    
                    if is_already_on_reviews_page:
                        logger.info("已在评论页面，直接处理评论数据")
                    else:
                        logger.info(f"有头模式：直接访问评论页面: {reviews_url}")
                    
                    try:
                        # 构造初始游戏信息
                        game_info = {
                            'title': '未知',
                            'app_id': app_id,
                            'url': url,
                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # 如果不在评论页面，则需要访问
                        if not is_already_on_reviews_page:
                            logger.info(f"访问评论页面: {reviews_url}")
                            self.driver.get(reviews_url)
                            time.sleep(IMPLICIT_WAIT)
                            
                            # 处理可能的年龄验证
                            if handle_age_check(self.driver):
                                logger.info("已通过评论页面的年龄验证")
                            
                            # 评论页面的特殊年龄验证处理
                            if "agecheck" in self.driver.page_source.lower() or "age verification" in self.driver.page_source.lower():
                                logger.info("检测到评论页面需要年龄验证，尝试特殊处理方法...")
                                self.handle_review_page_age_verification(reviews_url)
                            
                            # 检查是否是暴力色情内容警告页面
                            if is_content_warning_page(self.driver):
                                logger.info("检测到暴力色情内容警告页面，尝试处理...")
                                if handle_content_warning_page(self.driver):
                                    logger.info("成功处理内容警告页面")
                                else:
                                    logger.warning("处理内容警告页面失败，可能需要手动登录再尝试")
                        
                        # 确认是否成功加载评论页面
                        if "reviews" in self.driver.current_url.lower():
                            logger.info("当前页面已是评论页面，开始处理评论数据")
                            
                            # 尝试获取游戏标题（如果尚未获取）
                            if game_info['title'] == '未知':
                                try:
                                    title_elem = self.driver.find_element(By.CSS_SELECTOR, ".apphub_AppName")
                                    game_info['title'] = title_elem.text.strip()
                                    logger.info(f"从评论页面获取游戏标题: {game_info['title']}")
                                except:
                                    logger.warning("无法从评论页面获取游戏标题")
                            
                            # 处理评论页面
                            comments_count = self.process_reviews_page(reviews_url, game_info)
                            
                            # 如果成功处理了评论，标记为成功并立即返回结果
                            if comments_count > 0:
                                direct_access_success = True
                                logger.info(f"直接处理成功: 已处理 {comments_count} 条评论")
                                logger.info(f"成功爬取评论数: {self.successful_reviews}")
                                logger.info(f"评论回复总数: {self.comments_count}")
                                return [{"success": True, "count": comments_count}]
                            else:
                                logger.warning("直接处理评论页面未获取到评论，将尝试常规流程")
                        else:
                            logger.warning("未成功加载评论页面，将尝试常规流程")
                    except Exception as e:
                        logger.error(f"直接处理评论页面出错: {e}")
                        logger.warning("将尝试常规流程")
            
            # 只有在直接访问失败时才执行常规流程
            if not direct_access_success:
                logger.info("使用常规流程处理游戏页面和评论")
            
            # 处理游戏页面，获取基本信息
            game_info = self.process_game_page(url)
            
            if not game_info or not game_info.get('app_id'):
                logger.error("无法获取游戏信息或AppID")
                return []
            
            # 构建评论URL
            reviews_url = f"https://steamcommunity.com/app/{game_info['app_id']}/reviews/?browsefilter=toprated"
            logger.info(f"常规流程：访问评论页面: {reviews_url}")
            
            # 处理评论页面
            comments_count = self.process_reviews_page(reviews_url, game_info)
            
            logger.info(f"常规流程：已处理 {comments_count} 条评论")
            logger.info(f"成功爬取评论数: {self.successful_reviews}")
            logger.info(f"评论回复总数: {self.comments_count}")
            
            return [{"success": True, "count": comments_count}]
            
        except Exception as e:
            logger.error(f"提取数据时出错: {e}")
            return []
    
    def run(self, url=None):
        """运行爬虫，处理单个URL或测试模式
        
        Args:
            url: 要爬取的游戏URL，None则进入测试模式
        """
        try:
            # 如果没有提供URL，进入测试模式
            if not url:
                logger.info("进入测试模式")
                url = AGE_VERIFICATION_GAME_URL
            
            # 确保已登录
            if not os.path.exists(self.cookies_file_json) and not os.path.exists(self.cookies_file_pickle):
                logger.warning("Cookie文件不存在，建议先运行 steam_cookies_helper.py 获取Cookie")
            
            # 检查登录状态
            is_logged_in = self.is_logged_in()
            if not is_logged_in:
                logger.warning("检测到未登录状态，尝试重新加载cookies...")
                cookies_loaded = self.load_cookies()
                if cookies_loaded:
                    logger.info("已加载cookies，尝试刷新登录状态...")
                    refresh_login(self.driver)
            
            # 提取AppID
            app_id = None
            app_id_match = re.search(r'/app/(\d+)', url)
            if app_id_match:
                app_id = app_id_match.group(1)
            elif url.isdigit():
                app_id = url
                
            # 有头模式下直接访问评论页面
            direct_access_success = False  # 标志变量，用于跟踪直接访问是否成功
            
            # 检查当前是否已经在游戏评论页面
            is_already_on_reviews_page = False
            if app_id and "reviews" in self.driver.current_url.lower():
                current_app_id_match = re.search(r'/app/(\d+)', self.driver.current_url)
                if current_app_id_match and current_app_id_match.group(1) == app_id:
                    logger.info(f"已经在目标游戏的评论页面 (AppID: {app_id})")
                    is_already_on_reviews_page = True
            
            # 如果在有头模式下或已经在评论页面
            if (not self.use_headless and app_id) or is_already_on_reviews_page:
                try:
                    logger.info(f"有头模式：检测到AppID {app_id}，尝试直接访问评论页面")
                    reviews_url = f"https://steamcommunity.com/app/{app_id}/reviews/?browsefilter=toprated"
                    
                    # 构造游戏信息
                    game_info = {
                        'app_id': app_id,
                        'url': url,
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # 如果已经在评论页面，则不需要重新加载
                    if is_already_on_reviews_page:
                        logger.info("已在评论页面，直接处理评论数据")
                        
                        # 尝试获取游戏标题
                        try:
                            title_elem = self.driver.find_element(By.CSS_SELECTOR, ".apphub_AppName")
                            game_info['title'] = title_elem.text.strip()
                            logger.info(f"从评论页面获取游戏标题: {game_info['title']}")
                        except:
                            game_info['title'] = f"App {app_id}"
                            logger.warning("无法从评论页面获取游戏标题")
                    else:
                        # 直接访问评论页面
                        logger.info(f"访问评论页面: {reviews_url}")
                        self.driver.get(reviews_url)
                        time.sleep(IMPLICIT_WAIT)
                        
                        # 检查是否需要处理年龄验证
                        if handle_age_check(self.driver):
                            logger.info("已通过年龄验证")
                        
                        # 评论页面的特殊年龄验证处理
                        if "agecheck" in self.driver.page_source.lower() or "age verification" in self.driver.page_source.lower():
                            logger.info("检测到评论页面需要年龄验证，尝试特殊处理方法...")
                            self.handle_review_page_age_verification(reviews_url)
                        
                        # 检查是否被重定向到登录页面
                        if "login" in self.driver.current_url.lower():
                            logger.warning("被重定向到登录页面，尝试重新登录...")
                            self.load_cookies()
                            refresh_login(self.driver)
                            # 重新访问评论页面
                            self.driver.get(reviews_url)
                            time.sleep(IMPLICIT_WAIT)
                            
                            # 再次检查是否需要处理年龄验证
                            if "agecheck" in self.driver.page_source.lower() or "age verification" in self.driver.page_source.lower():
                                logger.info("重新登录后仍然需要年龄验证，再次尝试特殊处理方法...")
                                self.handle_review_page_age_verification(reviews_url)
                        
                        # 检查是否是内容警告页面
                        if is_content_warning_page(self.driver):
                            logger.info("检测到内容警告页面，尝试处理...")
                            if handle_content_warning_page(self.driver):
                                logger.info("成功处理内容警告页面")
                            else:
                                logger.warning("处理内容警告页面失败，可能需要手动确认")
                        
                        # 获取游戏标题（如果可能）
                        if "reviews" in self.driver.current_url.lower():
                            try:
                                title_elem = self.driver.find_element(By.CSS_SELECTOR, ".apphub_AppName")
                                game_info['title'] = title_elem.text.strip()
                                logger.info(f"从评论页面获取游戏标题: {game_info['title']}")
                            except:
                                game_info['title'] = f"App {app_id}"
                                logger.warning("无法从评论页面获取游戏标题")
                    
                    # 检查是否成功加载评论页面
                    if "reviews" in self.driver.current_url.lower():
                        logger.info("成功加载评论页面，开始处理评论")
                        
                        # 处理评论页面
                        comments_count = self.process_reviews_page(reviews_url, game_info)
                        
                        # 标记直接访问成功（如果获取到评论）
                        if comments_count > 0:
                            direct_access_success = True
                            logger.info(f"直接处理成功：已处理 {comments_count} 条评论")
                            
                            # 输出统计信息
                            logger.info("\n========== 爬取统计 ==========")
                            logger.info(f"成功爬取评论数: {self.successful_reviews}")
                            logger.info(f"失败的评论数: {self.failed_reviews}")
                            logger.info(f"评论回复总数: {self.comments_count}")
                            logger.info("===========================")
                            
                            # 如果成功获取评论，直接返回结果
                            return game_info
                        else:
                            logger.warning("直接处理评论页面未获取到评论，将尝试常规流程")
                    else:
                        logger.warning("未能成功加载评论页面，将尝试常规流程")
                except Exception as e:
                    logger.error(f"直接访问评论页面出错: {e}")
                    logger.warning("将尝试常规流程")
            
            # 只有当直接访问失败时，才执行常规流程
            if not direct_access_success:
                # 常规流程：处理游戏页面
                logger.info("使用常规流程处理游戏页面")
            game_info = self.process_game_page(url)
            
            # 输出统计信息
            logger.info("\n========== 爬取统计 ==========")
            logger.info(f"成功爬取评论数: {self.successful_reviews}")
            logger.info(f"失败的评论数: {self.failed_reviews}")
            logger.info(f"评论回复总数: {self.comments_count}")
            logger.info("===========================")
            
            return game_info
        
        except Exception as e:
            logger.error(f"爬虫运行出错: {e}")
            return None
        finally:
            self.close()
            
# 简单的数据写入器
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
    
    def save_as(self, review_data, new_dir):
        """将评论数据另存为到指定目录
        
        Args:
            review_data: 评论数据
            new_dir: 新的保存目录
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
        try:
            # 确保新目录存在
            os.makedirs(new_dir, exist_ok=True)
            
            # 临时更改输出目录
            original_dir = self.output_dir
            self.output_dir = new_dir
            
            # 写入文件
            file_path = self.write_review(review_data)
            
            # 恢复原始输出目录
            self.output_dir = original_dir
            
            return file_path
        except Exception as e:
            logger.error(f"另存为评论数据失败: {e}")
            return None
    
    def copy_to_dir(self, target_dir):
        """将所有已保存的文件复制到目标目录
        
        Args:
            target_dir: 目标目录
            
        Returns:
            int: 成功复制的文件数量
        """
        try:
            import shutil
            
            # 确保目标目录存在
            os.makedirs(target_dir, exist_ok=True)
            
            copied_count = 0
            for file_path in self.saved_files:
                if os.path.exists(file_path):
                    # 创建目标路径，保持相同的目录结构
                    rel_path = os.path.relpath(file_path, self.output_dir)
                    target_path = os.path.join(target_dir, rel_path)
                    
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    
                    # 复制文件
                    shutil.copy2(file_path, target_path)
                    copied_count += 1
                    logger.info(f"已复制: {file_path} -> {target_path}")
            
            logger.info(f"成功复制 {copied_count} 个文件到 {target_dir}")
            return copied_count
        except Exception as e:
            logger.error(f"复制文件失败: {e}")
            return 0
    
    def get_saved_files(self):
        """获取所有已保存的文件列表
        
        Returns:
            list: 文件路径列表
        """
        return self.saved_files

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Steam评论爬虫')
    parser.add_argument('--url', type=str, help='要爬取的游戏URL')
    parser.add_argument('--headless', action='store_true', help='使用无头模式')
    parser.add_argument('--max-reviews', type=int, default=None, help='最大爬取评论数')
    args = parser.parse_args()
    
    # 初始化数据写入器
    data_writer = JsonDataWriter()
    
    # 初始化爬虫
    crawler = SteamCrawler(use_headless=args.headless, data_writer=data_writer)
    
    # 运行爬虫
    url = args.url if args.url else None
    crawler.run(url)

if __name__ == "__main__":
    main() 