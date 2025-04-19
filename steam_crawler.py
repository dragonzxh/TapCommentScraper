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
        self.cookies_file = "steam_cookies.pkl"
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
        
        # 设置窗口大小和位置
        options.add_argument('--window-size=1366,768')
        options.add_argument('--window-position=0,0')
        
        # 添加必要的功能支持
        options.add_argument('--enable-javascript')
        options.add_argument('--enable-cookies')
        options.add_argument('--enable-application-cache')
        options.add_argument('--enable-dom-storage')
        
        # 设置语言
        options.add_argument('--lang=zh-CN')
        
        # 设置用户代理
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # 禁用日志
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # 创建ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # 设置超时时间
        self.driver.set_page_load_timeout(30)
        self.driver.set_script_timeout(30)
        self.driver.implicitly_wait(10)
        
        # 不再最大化窗口
        # self.driver.maximize_window()
        
        print("浏览器初始化完成")
        
    def save_cookies(self):
        """保存当前的Cookie到文件"""
        try:
            cookies = self.driver.get_cookies()
            Path("cookies").mkdir(exist_ok=True)  # 创建cookies目录
            cookie_path = os.path.join("cookies", self.cookies_file)
            with open(cookie_path, "wb") as f:
                pickle.dump(cookies, f)
            print("Cookie已保存")
            return True
        except Exception as e:
            print(f"保存Cookie时出错: {e}")
            return False
    
    def load_cookies(self):
        """从文件加载Cookie"""
        try:
            cookie_path = os.path.join("cookies", self.cookies_file)
            if not os.path.exists(cookie_path):
                print("没有找到已保存的Cookie文件")
                return False
                
            with open(cookie_path, "rb") as f:
                cookies = pickle.load(f)
                
            # 访问Steam网站以设置Cookie
            self.driver.get("https://store.steampowered.com")
            time.sleep(2)
            
            # 添加Cookie
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"添加Cookie时出错: {e}")
                    continue
            
            print("Cookie加载完成")
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
            # 检查是否存在年龄选择下拉框
            age_selectors = [
                "select[name='ageYear']",
                "#ageYear",
                "[id*='age']"
            ]
            
            for selector in age_selectors:
                try:
                    age_select = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if age_select:
                        # 选择1990年
                        self.driver.execute_script(
                            "arguments[0].value = '1990'",
                            age_select
                        )
                        time.sleep(1)
                        
                        # 点击查看页面按钮
                        view_buttons = self.driver.find_elements(
                            By.CSS_SELECTOR,
                            "a.btnv6_blue_hoverfade, [type='submit']"
                        )
                        for button in view_buttons:
                            if "查看" in button.text or "view" in button.text.lower():
                                button.click()
                                time.sleep(3)
                                return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"处理年龄验证时出错: {e}")
            return False
    
    def save_comments(self, comments, app_id):
        """保存评论到文件
        
        Args:
            comments: 评论数据列表
            app_id: 游戏ID
        """
        try:
            # 创建输出目录
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            csv_filename = os.path.join(output_dir, f"{app_id}_comments_{timestamp}.csv")
            
            # 保存为CSV
            with open(csv_filename, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                # 写入表头
                writer.writerow(['编号', '用户名', '用户ID', '评分', '评论内容', '发布时间', '游戏时长', '有用数', '好笑数', '游戏ID'])
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
                        app_id
                    ])
            
            print(f"\n评论已保存到: {csv_filename}")
            
            # 同时保存为TXT格式
            txt_filename = os.path.join(output_dir, f"{app_id}_comments_{timestamp}.txt")
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(f"游戏ID: {app_id}\n")
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

            # 标准化URL
            if not url.endswith("/"):
                url += "/"
            
            # 获取游戏ID
            app_id = "unknown"
            match = re.search(r'/app/(\d+)', url)
            if match:
                app_id = match.group(1)
            
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
            
            # 等待页面加载
            time.sleep(2)
            
            # 确保评论已加载
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".apphub_Card"))
                )
            except Exception:
                print("超时: 评论未能加载")
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
                self.save_comments(all_comments, app_id)
                
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
        
        # 直接使用文明7的评论页面URL
        url = "https://steamcommunity.com/app/1295660/reviews/?browsefilter=toprated&snr=1_5_100010_&filterLanguage=schinese"
        print(f"\n开始爬取文明7评论，URL: {url}")
        crawler.extract_comments(url)
        
    except Exception as e:
        print(f"程序运行时发生未处理的异常: {e}")
        # 记录错误
        try:
            with open("error_log.txt", "a", encoding='utf-8') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - 未处理的异常: {str(e)}\n")
        except:
            pass
    finally:
        print("\n正在关闭浏览器...")
        if 'crawler' in locals():
            crawler.close()
        print("程序执行完毕") 