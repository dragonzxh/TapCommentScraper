"""
Steam爬虫适配器 - 专门用于爬取Steam游戏评论
"""

from crawler_base import BaseCrawler, CsvWriter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import time
import json
import sys
import os
import pickle
from pathlib import Path
import csv
from datetime import datetime
import importlib.util

# 检查steam_cookies_helper是否存在
has_cookies_helper = os.path.exists("steam_cookies_helper.py")

class SteamCrawler(BaseCrawler):
    """Steam爬虫类，专门用于爬取Steam游戏评论"""
    
    def __init__(self, use_headless=False):
        """初始化Steam爬虫"""
        # 先设置类属性
        self.use_headless = use_headless
        self.data_writer = CsvWriter()
        self.load_more_text = "加载更多评测"
        self.sort_by = "评测有用程度"
        self.is_logged_in = False
        self.cookies_file = "steam_cookies.pkl"  # 默认的cookies文件名
        self.cookies_dir = "cookies"  # cookies目录
        self.max_retries = 3  # 最大重试次数
        self.scroll_pause_time = 1  # 滚动暂停时间
        self.batch_size = 10  # 每批处理的评论数量
        
        # 初始化进度
        self.progress = {
            "total_comments": 0,
            "processed_comments": 0,
            "current_batch": 0,
            "current_game_id": ""
        }
        
        # 初始化浏览器
        self.setup_driver()
        
        # 检查cookies路径
        self.cookies_path = os.path.join(self.cookies_dir, self.cookies_file)
        self.check_cookies_helper_file()
        
        # 尝试加载已保存的Cookie
        if self.load_cookies():
            print("成功加载已保存的Cookie")
            self.check_login_with_cookies()
        
    def setup_driver(self):
        """设置并初始化WebDriver"""
        options = webdriver.ChromeOptions()
        
        # 基本设置
        if self.use_headless:
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
        
        # 新增：增加内存和稳定性相关选项
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--window-size=1920,1080')  # 更大的窗口尺寸
        
        # 新增：绕过部分反爬虫机制
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 新增：尝试显式指定Chrome路径（如果存在）
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
        
        # 设置语言
        options.add_argument('--lang=zh-CN')
        
        # 设置用户代理
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # 禁用日志
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # 创建ChromeDriver
        try:
            print("正在初始化ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # 执行反检测JavaScript
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
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
                self.driver = webdriver.Chrome(options=options)
                print("备用方法初始化成功")
            except Exception as e2:
                print(f"备用方法也失败: {e2}")
                raise
        
        # 设置超时时间
        self.driver.set_page_load_timeout(60)  # 增加到60秒
        self.driver.set_script_timeout(60)
        self.driver.implicitly_wait(20)  # 增加到20秒
        
        print("浏览器初始化完成")
        
    def check_cookies_helper_file(self):
        """检查steam_cookies_helper.py文件是否存在，提示用户"""
        helper_file = "steam_cookies_helper.py"
        
        # 创建cookies目录（如果不存在）
        Path(self.cookies_dir).mkdir(exist_ok=True)
        
        if os.path.exists(helper_file):
            print(f"提示: 如果遇到年龄验证或评论加载问题，请运行 {helper_file} 获取cookies")
            
            # 检查cookies文件
            if os.path.exists(self.cookies_path):
                with open(self.cookies_path, "rb") as f:
                    try:
                        cookies = pickle.load(f)
                        print(f"已找到cookies文件，包含 {len(cookies)} 个cookie")
                    except Exception as e:
                        print(f"cookies文件损坏: {e}")
            else:
                print(f"未找到cookies文件，建议运行 {helper_file} 获取Steam登录状态")
        
    def save_cookies(self):
        """保存当前的Cookie到文件"""
        try:
            cookies = self.driver.get_cookies()
            Path(self.cookies_dir).mkdir(exist_ok=True)  # 创建cookies目录
            
            # 保存到标准路径
            with open(self.cookies_path, "wb") as f:
                pickle.dump(cookies, f)
            print(f"已保存 {len(cookies)} 个Cookies到 {self.cookies_path}")
            
            # 同时保存一份人类可读的cookies信息
            cookie_info_path = os.path.join(self.cookies_dir, "steam_cookies_info.txt")
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
            
            return True
        except Exception as e:
            print(f"保存Cookie时出错: {e}")
            return False
    
    def load_cookies(self):
        """从文件加载Cookie"""
        try:
            # 检查cookies_helper创建的cookies文件
            helper_cookies_path = os.path.join(self.cookies_dir, self.cookies_file)
            if os.path.exists(helper_cookies_path):
                print(f"使用 steam_cookies_helper.py 创建的cookies文件: {helper_cookies_path}")
                with open(helper_cookies_path, "rb") as f:
                    cookies = pickle.load(f)
            # 使用旧的cookies文件
            elif os.path.exists(os.path.join("cookies", self.cookies_file)):
                cookie_path = os.path.join("cookies", self.cookies_file)
                print(f"使用旧的cookies文件: {cookie_path}")
                with open(cookie_path, "rb") as f:
                    cookies = pickle.load(f)
            else:
                print("没有找到已保存的Cookie文件")
                return False
                
            # 访问Steam网站以设置Cookie
            self.driver.get("https://store.steampowered.com")
            time.sleep(2)
            
            # 添加Cookie
            success_count = 0
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                    success_count += 1
                except Exception as e:
                    print(f"添加Cookie时出错: {e}")
                    continue
            
            print(f"Cookie加载完成，成功添加 {success_count}/{len(cookies)} 个cookie")
            
            # 刷新页面以应用cookies
            self.driver.refresh()
            time.sleep(3)
            
            return True
        except Exception as e:
            print(f"加载Cookie时出错: {e}")
            return False
    
    def check_login_with_cookies(self):
        """使用已加载的Cookie检查登录状态"""
        try:
            print("正在验证Cookie登录状态...")
            self.driver.get("https://store.steampowered.com")
            time.sleep(3)
            
            if self.check_login_status():
                print("Cookie登录验证成功")
                self.is_logged_in = True
                return True
            else:
                print("Cookie已失效，需要重新登录")
                return False
        except Exception as e:
            print(f"验证Cookie登录状态时出错: {e}")
            return False
    
    def login(self, username, password):
        """登录Steam账号
        
        Args:
            username: Steam用户名
            password: Steam密码
            
        Returns:
            bool: 是否登录成功
        """
        try:
            # 如果已经登录，直接返回
            if self.is_logged_in:
                print("已经处于登录状态")
                return True
                
            print("开始Steam登录流程...")
            
            # 访问Steam登录页面
            login_url = "https://store.steampowered.com/login/"
            print(f"正在访问登录页面: {login_url}")
            self.driver.get(login_url)
            time.sleep(3)
            
            # 等待登录表单加载
            print("等待登录表单加载...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#responsive_page_template_content"))
            )
            
            # 输入用户名
            print("输入用户名...")
            username_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            username_field.clear()
            username_field.send_keys(username)
            time.sleep(1)
            
            # 输入密码
            print("输入密码...")
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(1)
            
            # 点击登录按钮
            print("点击登录按钮...")
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # 等待登录完成
            print("等待登录完成...")
            time.sleep(10)
            
            # 检查是否登录成功
            if self.check_login_status():
                print("登录成功！")
                self.is_logged_in = True
                # 保存Cookie以供下次使用
                self.save_cookies()
                return True
            else:
                print("登录失败，请检查用户名和密码")
                return False
                
        except Exception as e:
            print(f"登录过程出错: {e}")
            return False
    
    def check_login_status(self):
        """检查是否已登录
        
        Returns:
            bool: 是否已登录
        """
        try:
            # 检查是否存在登录后才会出现的元素
            account_indicators = [
                "#account_pulldown",
                ".playerAvatar",
                ".user_avatar",
                "#account_dropdown",
                ".supernav_container"
            ]
            
            for indicator in account_indicators:
                elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                if elements:
                    return True
            
            return False
        except Exception as e:
            print(f"检查登录状态时出错: {e}")
            return False
    
    def get_comment_selectors(self):
        """获取Steam评论元素的CSS选择器"""
        return [
            ".apphub_Card",
            ".review_box",
            ".review_container",
            "[class*='review']",
            "[class*='comment']"
        ]
    
    def normalize_url(self, url):
        """标准化URL格式，确保是Steam评测页面"""
        url = url.strip()  # 去除首尾空白
        
        # 如果是商店页面URL，转换为评论页面URL
        if "/app/" in url and "/reviews" not in url:
            app_id = self.extract_app_id(url)
            url = f"https://steamcommunity.com/app/{app_id}/reviews/"
            print(f"已将商店页面URL转换为评测页面URL: {url}")
        
        # 添加过滤参数
        if "?" not in url:
            url += "?"
        if "browsefilter=" not in url:
            url += "&browsefilter=toprated"  # 按最有用排序
        if "filterLanguage=" not in url:
            url += "&filterLanguage=schinese"  # 设置简体中文
        
        # 确保URL格式正确
        url = url.replace("?&", "?")
        
        print(f"最终访问的URL: {url}")
        return url
    
    def extract_app_id(self, url):
        """从URL中提取游戏的AppID"""
        # 从URL中提取AppID
        app_id_search = re.search(r'/app/(\d+)', url.lower())
        
        if app_id_search:
            app_id = app_id_search.group(1)
            print(f'开始爬取游戏ID: {app_id}')
            return app_id
        else:
            # 如果无法识别AppID，使用URL最后部分作为ID
            parts = url.rstrip('/').split('/')
            for part in parts:
                if part.isdigit():
                    return part
            
            raise ValueError(f"无法从URL中提取游戏ID: {url}")
    
    def set_review_language(self, language="schinese"):
        """设置评论显示语言"""
        try:
            print("尝试设置评论语言...")
            
            # 等待语言选择器加载
            language_selectors = [
                "#language_pulldown",
                ".language_pulldown",
                "[class*='language']",
                "[id*='language']"
            ]
            
            for selector in language_selectors:
                try:
                    # 等待元素可见
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    
                    # 找到语言选择器
                    language_selector = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if language_selector and language_selector.is_displayed():
                        print("找到语言选择器")
                        
                        # 点击打开语言下拉菜单
                        self.driver.execute_script("arguments[0].click();", language_selector)
                        time.sleep(2)
                        
                        # 查找语言选项
                        language_options = self.driver.find_elements(
                            By.CSS_SELECTOR,
                            ".popup_menu_item"
                        )
                        
                        # 遍历选项寻找简体中文
                        for option in language_options:
                            if "简体中文" in option.text:
                                print("找到简体中文选项")
                                self.driver.execute_script("arguments[0].click();", option)
                                time.sleep(3)  # 等待页面刷新
                                return True
                            
                        print("未找到简体中文选项，尝试其他方式...")
                        
                        # 如果没有找到简体中文，尝试通过URL参数设置语言
                        current_url = self.driver.current_url
                        if "?l=" not in current_url and "&l=" not in current_url:
                            if "?" in current_url:
                                new_url = current_url + "&l=schinese"
                            else:
                                new_url = current_url + "?l=schinese"
                            print(f"通过URL设置语言: {new_url}")
                            self.driver.get(new_url)
                            time.sleep(3)
                            return True
                            
                except Exception as e:
                    print(f"尝试选择器 {selector} 失败: {e}")
                    continue
            
            print("无法设置评论语言，继续使用默认语言")
            return False
            
        except Exception as e:
            print(f"设置评论语言时出错: {e}")
            return False
    
    def set_review_filter(self, review_type="positive"):
        """设置评论筛选条件"""
        try:
            # 尝试点击筛选按钮
            filter_button = self.driver.find_element(By.ID, "review_type_all")
            if filter_button:
                self.driver.execute_script("arguments[0].click();", filter_button)
                time.sleep(1)
                
                # 根据评论类型选择对应选项
                if review_type == "positive":
                    filter_option = self.driver.find_element(By.ID, "review_type_positive")
                elif review_type == "negative":
                    filter_option = self.driver.find_element(By.ID, "review_type_negative")
                else:
                    filter_option = self.driver.find_element(By.ID, "review_type_all")
                
                if filter_option:
                    self.driver.execute_script("arguments[0].click();", filter_option)
                    print(f"已将评论筛选设置为: {review_type}")
                    time.sleep(2)  # 等待页面刷新
                    return True
        except Exception as e:
            print(f"设置评论筛选条件时出错: {e}")
        
        return False
    
    def click_load_more(self):
        """通过滚动加载更多评论"""
        try:
            # 获取当前评论数量
            current_reviews = self.driver.find_elements(By.CSS_SELECTOR, ".apphub_Card")
            current_count = len(current_reviews)
            print(f"\n当前页面评论数: {current_count}")
            
            # 使用JavaScript滚动到底部
            scroll_script = """
            window.scrollTo({
                top: document.documentElement.scrollHeight,
                behavior: 'auto'
            });
            """
            self.driver.execute_script(scroll_script)
            time.sleep(self.scroll_pause_time)
            
            # 检查是否加载了新评论
            new_reviews = self.driver.find_elements(By.CSS_SELECTOR, ".apphub_Card")
            new_count = len(new_reviews)
            
            if new_count > current_count:
                print(f"成功加载新评论，当前共有 {new_count} 条评论")
                self.progress["total_comments"] = new_count
                return True
            else:
                print("未加载到新评论，可能已到达底部")
                return False
            
        except Exception as e:
            print(f"滚动加载评论时出错: {e}")
            return False
    
    def expand_all_reviews(self):
        """展开所有评论详情"""
        try:
            print("\n开始展开评论详情...")
            
            # 使用JavaScript批量展开评论
            expand_script = """
            function expandReviews() {
                var expandButtons = document.querySelectorAll('.view_more a, .view_more button, .view_more span');
                var expandedCount = 0;
                
                expandButtons.forEach(function(button) {
                    if (button.offsetParent !== null && 
                        (button.textContent.includes('展开') || 
                         button.textContent.includes('更多') || 
                         button.textContent.toLowerCase().includes('view') || 
                         button.textContent.toLowerCase().includes('more'))) {
                        button.click();
                        expandedCount++;
                    }
                });
                
                return expandedCount;
            }
            return expandReviews();
            """
            
            expanded_count = self.driver.execute_script(expand_script)
            print(f"已一次性展开 {expanded_count} 条评论")
            
            # 短暂等待DOM更新
            time.sleep(0.5)
            
            return expanded_count > 0
            
        except Exception as e:
            print(f"展开评论详情时出错: {e}")
            return False
    
    def handle_age_check(self):
        """处理年龄验证页面"""
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
            
            page_source_lower = self.driver.page_source.lower()
            age_verification_needed = any(indicator in page_source_lower for indicator in age_indicators)
            
            if age_verification_needed:
                print("检测到年龄验证页面，尝试处理...")
                
                # 方法1：尝试查找年龄选择下拉框
                age_selects = self.driver.find_elements(By.CSS_SELECTOR, "select[name='ageYear'], #ageYear, [id*='age']")
                if age_selects:
                    for age_select in age_selects:
                        if age_select.is_displayed():
                            # 选择1990年
                            self.driver.execute_script(
                                "arguments[0].value = '1990'",
                                age_select
                            )
                            print("已设置年龄为1990年")
                            time.sleep(1)
                            
                            # 点击查看页面按钮
                            view_buttons = self.driver.find_elements(
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
                                    self.driver.execute_script("arguments[0].click();", button)
                                    time.sleep(5)
                                    return True
                
                # 方法2：直接尝试点击可能的确认按钮
                view_buttons = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "a.btnv6_blue_hoverfade, .agegate_text_container.btns a, .agegate_btn_container .btn_blue"
                )
                for button in view_buttons:
                    button_text = button.text.lower()
                    if ("view" in button_text or 
                        "enter" in button_text or 
                        "proceed" in button_text or
                        "continue" in button_text or
                        "查看" in button_text or
                        "进入" in button_text):
                        print(f"直接点击按钮: {button.text}")
                        self.driver.execute_script("arguments[0].click();", button)
                        time.sleep(5)
                        return True
                
                print("尝试处理年龄验证失败，可能需要使用steam_cookies_helper.py工具获取登录状态")
                return False
            
            return False  # 没有检测到年龄验证页面
        except Exception as e:
            print(f"处理年龄验证时出错: {e}")
            return False
    
    def save_comments(self, comments, app_id, game_name=""):
        """保存评论到文件
        
        Args:
            comments: 评论数据列表
            app_id: 游戏ID
            game_name: 游戏名称
        """
        try:
            # 创建输出目录
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名，如果有游戏名称则加入文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            # 清理游戏名称中的非法字符
            if game_name and game_name != app_id:
                # 移除Windows文件名中的非法字符
                game_name = re.sub(r'[\\/*?:"<>|]', "", game_name)
                # 限制名称长度
                if len(game_name) > 50:
                    game_name = game_name[:47] + "..."
                file_prefix = f"{app_id}_{game_name}"
            else:
                file_prefix = app_id
                
            csv_filename = os.path.join(output_dir, f"{file_prefix}_comments_{timestamp}.csv")
            
            # 保存为CSV
            with open(csv_filename, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                # 写入表头
                writer.writerow(['编号', '用户名', '用户ID', '评分', '评论内容', '发布时间', '游戏时长', '有用数', '好笑数', '游戏ID', '游戏名称'])
                # 写入数据
                for i, comment in enumerate(comments, 1):
                    writer.writerow([
                        comment.get('index', i),
                        comment.get('username', ''),
                        comment.get('user_id', ''),
                        comment.get('rating', ''),
                        comment.get('content', ''),
                        comment.get('post_time', ''),
                        comment.get('play_time', ''),
                        comment.get('helpful_count', 0),
                        comment.get('funny_count', 0),
                        app_id,
                        game_name
                    ])
            
            print(f"\n评论已保存到: {csv_filename}")
            
            # 同时保存为TXT格式
            txt_filename = os.path.join(output_dir, f"{file_prefix}_comments_{timestamp}.txt")
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(f"游戏ID: {app_id}\n")
                if game_name and game_name != app_id:
                    f.write(f"游戏名称: {game_name}\n")
                f.write(f"爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"评论数量: {len(comments)}\n\n")
                f.write("="*50 + "\n\n")
                
                for i, comment in enumerate(comments, 1):
                    f.write(f"评论 #{i}\n")
                    f.write(f"用户名: {comment.get('username', '')}\n")
                    f.write(f"用户ID: {comment.get('user_id', '')}\n")
                    f.write(f"评分: {comment.get('rating', '')}\n")
                    f.write(f"发布时间: {comment.get('post_time', '')}\n")
                    f.write(f"游戏时长: {comment.get('play_time', '')}\n")
                    f.write(f"有用数: {comment.get('helpful_count', 0)}\n")
                    f.write(f"好笑数: {comment.get('funny_count', 0)}\n")
                    f.write(f"评论内容:\n{comment.get('content', '')}\n")
                    f.write("\n" + "-"*50 + "\n\n")
            
            print(f"评论已同时保存到: {txt_filename}")
            
        except Exception as e:
            print(f"保存评论时出错: {str(e)}")

    def extract_comments(self, url):
        """提取评论数据"""
        try:
            # 检查是否已登录
            if not self.is_logged_in:
                print("警告: 未登录状态下可能无法获取完整评论")
            else:
                print("已检测到登录状态，将能够访问更多内容")

            # 标准化URL
            if not url.endswith("/"):
                url += "/"
            
            # 获取游戏ID
            app_id = "unknown"
            match = re.search(r'/app/(\d+)', url)
            if match:
                app_id = match.group(1)
            
            # 获取游戏名称
            game_name = self.get_game_name(app_id)
            print(f"获取到游戏名称: {game_name}")
            
            # 设置筛选条件：热门评论+中文
            review_url = url
            if "?" not in review_url:
                review_url += "?browsefilter=toprated&filterLanguage=schinese"
            else:
                review_url += "&browsefilter=toprated&filterLanguage=schinese"
            
            print(f"最终访问的URL: {review_url}")
            print(f"开始爬取游戏ID: {app_id}")
            
            # 访问页面
            print(f"\n开始访问URL: {review_url}")
            self.driver.get(review_url)
            
            # 增加等待页面加载的时间
            time.sleep(10)  # 从原来的2秒增加到10秒
            
            # 处理可能出现的年龄验证页面
            if self.handle_age_check():
                print("成功处理年龄验证页面")
            
            # 确保评论已加载，增加超时时间
            try:
                print("等待评论元素加载...")
                WebDriverWait(self.driver, 30).until(  # 增加到30秒
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".apphub_Card"))
                )
            except Exception as e:
                print(f"评论未能加载: {e}")
                
                # 保存页面源码以便分析
                try:
                    error_log_path = f"error_log_page_{app_id}.html"
                    with open(error_log_path, "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    print(f"已保存页面源码到 {error_log_path} 以便分析问题")
                    
                    # 检查是否包含特定的错误信息
                    if "mature_content" in self.driver.page_source or "age_gate" in self.driver.page_source or "agecheck" in self.driver.page_source:
                        print("\n错误原因：页面需要年龄验证。请使用以下方法解决：")
                        print("1. 运行 python steam_cookies_helper.py")
                        print("2. 选择选项1：登录并保存Cookies")
                        print("3. 在打开的浏览器中登录您的Steam账号")
                        print("4. 完成年龄验证步骤")
                        print("5. 重新运行本爬虫")
                    elif "not available in your country" in self.driver.page_source.lower():
                        print("错误原因：该游戏在您的地区不可用")
                    elif "please select a language" in self.driver.page_source.lower():
                        print("错误原因：需要选择语言")
                    else:
                        print("未知错误，请检查错误日志页面")
                except Exception as save_e:
                    print(f"保存错误页面源码失败: {save_e}")
                
                return []
            
            # 获取初始评论数量
            reviews = self.driver.find_elements(By.CSS_SELECTOR, ".apphub_Card")
            initial_count = len(reviews)
            print(f"\n初始评论数量: {initial_count}")
            
            # 滚动加载更多评论
            all_comments = []
            batch_size = 10  # 每批处理的评论数
            target_count = 200  # 目标评论数量
            
            loaded_count = initial_count
            print(f"已加载 {loaded_count} 条评论")
            
            max_scroll_attempts = 15  # 增加滚动尝试次数
            no_new_reviews_count = 0
            
            # 滚动加载更多评论
            while loaded_count < target_count and no_new_reviews_count < max_scroll_attempts:
                # 滚动到页面底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)  # 等待内容加载
                
                # 重新获取评论
                reviews = self.driver.find_elements(By.CSS_SELECTOR, ".apphub_Card")
                print(f"\n当前页面评论数: {len(reviews)}")
                
                if len(reviews) > loaded_count:
                    print(f"成功加载新评论，当前共有 {len(reviews)} 条评论")
                    loaded_count = len(reviews)
                    print(f"已加载 {loaded_count} 条评论")
                    no_new_reviews_count = 0
                else:
                    no_new_reviews_count += 1
                    print("未加载到新评论，可能已到达底部")
            
            # 展开所有评论
            print("\n正在展开所有评论...")
            self.expand_all_reviews()
            
            # 重新获取评论，确保获取展开后的内容
            reviews = self.driver.find_elements(By.CSS_SELECTOR, ".apphub_Card")
            print(f"\n总共找到 {len(reviews)} 条评论")
            
            # 分批处理评论
            for i in range(0, len(reviews), batch_size):
                batch = reviews[i:i+batch_size]
                print(f"\n处理第 {i+1} 到 {i+len(batch)} 条评论")
                
                for review in batch:
                    try:
                        # 修改这里的函数调用，传递正确的参数
                        review_data = self.extract_review_data(review)
                        if review_data:
                            # 添加游戏ID和序号
                            review_data['game_id'] = app_id
                            review_data['index'] = len(all_comments) + 1
                            all_comments.append(review_data)
                    except Exception as e:
                        print(f"处理评论时出错: {str(e)}")
                        continue
                    
            print("-" * 50)  # 分隔线
            
            # 保存所有评论
            if all_comments:
                print(f"\n共爬取到 {len(all_comments)} 条评论，正在保存...")
                self.save_comments(all_comments, app_id, game_name)
                
            return all_comments
            
        except Exception as e:
            print(f"访问URL时出错: {str(e)}")
            return []
    
    def extract_review_data(self, review_element):
        """提取评论数据"""
        try:
            # 检查评论元素是否为空
            if review_element is None:
                print("警告: 遇到空的评论元素")
                return None
            
            # 提取用户信息
            try:
                user_element = review_element.find_element(By.CSS_SELECTOR, '.apphub_CardContentAuthorName a')
                if user_element:
                    username = user_element.text
                    user_id = user_element.get_attribute('href').split('/')[-1]
                else:
                    username = "未知用户"
                    user_id = "unknown"
            except Exception as e:
                print(f"提取用户信息时出错: {str(e)}")
                username = "未知用户"
                user_id = "unknown"

            # 提取评论内容
            try:
                content_element = review_element.find_element(By.CSS_SELECTOR, '.apphub_CardTextContent')
                if content_element:
                    content = content_element.text
                else:
                    content = "评论内容不可用"
            except Exception as e:
                print(f"提取评论内容时出错: {str(e)}")
                content = "评论内容不可用"

            # 提取评分信息
            try:
                rating_element = review_element.find_element(By.CSS_SELECTOR, '.title')
                if rating_element:
                    rating = rating_element.text
                else:
                    rating = "未知评分"
            except Exception as e:
                print(f"提取评分信息时出错: {str(e)}")
                rating = "未知评分"

            # 提取发布时间
            try:
                date_element = review_element.find_element(By.CSS_SELECTOR, '.date_posted')
                if date_element:
                    post_time = date_element.text.replace("发布于：", "").strip()
                else:
                    post_time = "未知时间"
            except Exception as e:
                print(f"提取发布时间时出错: {str(e)}")
                post_time = "未知时间"

            # 提取游戏时长
            try:
                hours_element = review_element.find_element(By.CSS_SELECTOR, '.hours')
                if hours_element:
                    play_time = hours_element.text
                else:
                    play_time = "未知时长"
            except Exception as e:
                print(f"提取游戏时长时出错: {str(e)}")
                play_time = "未知时长"

            # 提取有用和好笑
            try:
                vote_elements = review_element.find_elements(By.CSS_SELECTOR, '.found_helpful')
                if vote_elements and len(vote_elements) > 0:
                    vote_text = vote_elements[0].text
                    helpful_count = re.search(r'(\d+) 人中有 (\d+) 人.+有用', vote_text)
                    if helpful_count:
                        helpful_count = helpful_count.group(2)
                    else:
                        helpful_count = "0"
                        
                    funny_count = re.search(r'(\d+) 人觉得这篇评测很欢乐', vote_text)
                    if funny_count:
                        funny_count = funny_count.group(1)
                    else:
                        funny_count = "0"
                else:
                    helpful_count = "0"
                    funny_count = "0"
            except Exception as e:
                print(f"提取评价信息时出错: {str(e)}")
                helpful_count = "0"
                funny_count = "0"

            # 构造结果
            result = {
                'username': username,
                'user_id': user_id,
                'content': content,
                'rating': rating,
                'post_time': post_time,
                'play_time': play_time,
                'helpful_count': helpful_count,
                'funny_count': funny_count
            }
            
            print(f"\n[用户] {username} (ID: {user_id})")
            print(f"[评论内容]\n{content}")
            print(f"[评分] {rating}")
            print(f"[发布时间] {post_time}")
            print(f"[游戏时长] {play_time}")
            print(f"[有用数] {helpful_count}")
            
            return result
        
        except Exception as e:
            print(f"提取评论数据时出错: {str(e)}")
            return None
    
    def get_game_name(self, app_id):
        """获取游戏名称
        
        Args:
            app_id: 游戏ID
            
        Returns:
            str: 游戏名称
        """
        try:
            # 访问游戏商店页面
            store_url = f"https://store.steampowered.com/app/{app_id}/"
            print(f"正在访问游戏商店页面: {store_url}")
            
            # 打开一个新标签页
            self.driver.execute_script("window.open('');")
            # 切换到新标签页
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # 加载商店页面
            self.driver.get(store_url)
            time.sleep(2)
            
            # 处理年龄验证页面
            self.handle_age_check()
            
            # 尝试获取游戏标题
            title_selectors = [
                ".apphub_AppName",
                "#appHubAppName",
                ".game_title",
                ".game_name",
                ".pageheader",
                "h1", 
                ".game_description_title",
                "[itemprop='name']"
            ]
            
            game_name = ""
            for selector in title_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.text.strip():
                            game_name = element.text.strip()
                            break
                    if game_name:
                        break
                except Exception as e:
                    print(f"使用选择器 {selector} 提取游戏名称时出错: {e}")
                    continue
            
            # 关闭新标签页，切换回原标签页
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            if not game_name:
                print(f"无法获取游戏名称，将使用游戏ID代替")
                return app_id
                
            return game_name
            
        except Exception as e:
            print(f"获取游戏名称时出错: {e}")
            return app_id
    
    def close(self):
        """关闭浏览器"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("已关闭浏览器")
    
if __name__ == "__main__":
    try:
        # 创建Steam爬虫实例
        use_headless = input("是否使用无头模式运行浏览器(无界面，推荐用于解决闪退问题)? [y/n]: ").strip().lower() == 'y'
        crawler = SteamCrawler(use_headless)
        
        # 检查是否有专用的cookies辅助工具
        if os.path.exists("steam_cookies_helper.py"):
            use_helper = input("\n检测到steam_cookies_helper.py工具。是否先获取Steam cookies (推荐，解决年龄验证问题)? [y/n]: ").strip().lower() == 'y'
            if use_helper:
                print("\n请在新窗口中操作steam_cookies_helper.py工具...")
                if os.name == 'nt':  # Windows
                    os.system("start python steam_cookies_helper.py")
                else:  # macOS/Linux
                    os.system("python steam_cookies_helper.py &")
                input("\n在完成cookies获取后，按Enter继续爬虫操作...")
                # 重新加载cookies
                crawler = SteamCrawler(use_headless)
        
        # 添加登录选项
        need_login = input("\n是否需要登录Steam账号(推荐，可以解决年龄验证问题)? [y/n]: ").strip().lower() == 'y'
        if need_login:
            username = input("请输入Steam用户名: ")
            import getpass
            password = getpass.getpass("请输入Steam密码(输入时不会显示): ")
            login_success = crawler.login(username, password)
            if login_success:
                print("登录成功！已保存Cookie以便后续使用")
            else:
                print("登录失败，将以未登录状态继续")
        
        # 获取输入的URL
        url_input = input("\n请输入Steam游戏评论页面或商店页面URL(或直接输入游戏ID): ").strip()
        
        # 检查是否直接输入ID
        if url_input.isdigit():
            url = f"https://steamcommunity.com/app/{url_input}/reviews/?browsefilter=toprated&filterLanguage=schinese"
            print(f"已将游戏ID转换为URL: {url}")
        else:
            url = url_input
        
        # 创建输出目录
        if not os.path.exists("output"):
            os.makedirs("output")
            print("已创建output目录用于保存结果")
        
        print(f"\n开始爬取Steam评论，URL: {url}")
        comments = crawler.extract_comments(url)
        
        if not comments or len(comments) == 0:
            print("\n未能获取评论，可能原因：")
            print("1. 该游戏需要通过年龄验证")
            print("2. 该游戏可能没有评论或评论不可见")
            print("3. 网络连接问题或Steam服务器限制")
            print("\n解决方案：")
            print("1. 运行 python steam_cookies_helper.py 获取登录状态")
            print("2. 使用非无头模式，观察浏览器加载过程以诊断问题")
        
    except Exception as e:
        print(f"程序运行时发生未处理的异常: {e}")
        # 记录错误
        try:
            with open("error_log.txt", "a", encoding='utf-8') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - 未处理的异常: {str(e)}\n")
                
            # 导入traceback以获取完整堆栈信息
            import traceback
            with open("error_log.txt", "a", encoding='utf-8') as f:
                f.write(traceback.format_exc())
                f.write("\n\n")
        except:
            pass
    finally:
        print("\n正在关闭浏览器...")
        if 'crawler' in locals():
            crawler.close()
        print("程序执行完毕") 