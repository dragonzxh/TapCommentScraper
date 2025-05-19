"""
TapTap爬虫适配器 - 专门用于爬取TapTap网站的评论
"""

from crawler_base import BaseCrawler, ExcelWriter
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import time
import sys
import os

class TapCrawler(BaseCrawler):
    """TapTap爬虫类，专门用于爬取TapTap网站的评论"""
    
    def __init__(self, use_headless=False):
        """初始化TapTap爬虫"""
        super().__init__(use_headless)
        self.data_writer = ExcelWriter()
    
    def get_comment_selectors(self):
        """获取TapTap网站评论元素的CSS选择器"""
        return [
            ".comment-item", 
            ".review-item",
            ".comment-list .item",
            "[class*='comment-item']",
            "[class*='review-item']",
            ".review-item-wrap",  # TapTap特定的评论包装器
            ".app-comments-wrap *",  # 评论区内的所有元素
            ".comment-container *"  # 评论容器内的所有元素
        ]
    
    def extract_game_id(self, url):
        """从URL中提取游戏ID"""
        # 从URL中提取游戏ID，但不修改原始URL
        game_id_search = re.search(r'taptap\.(?:com|cn)/app/(\d+)', url.lower())
        if not game_id_search:
            # 尝试其他可能的URL格式
            game_id_search = re.search(r'app/(\d+)', url.lower())
            
        if game_id_search:
            game_id = game_id_search.group(1)
            print(f'开始爬取第{self.progress["game_count"]+1}个游戏{game_id}')
            return game_id
        else:
            # 如果无法识别游戏ID，使用URL最后部分作为ID
            parts = url.rstrip('/').split('/')
            for part in parts:
                if part.isdigit():
                    game_id = part
                    break
            else:
                game_id = f"game_{self.progress['game_count'] + 1}"
            
            print(f'第{self.progress["game_count"] + 1}个游戏：无法从 URL {url} 中提取标准game_id，使用 {game_id} 作为标识')
            return game_id
    
    def normalize_url(self, url):
        """标准化URL格式"""
        # 保存原始URL
        original_url = url
        
        # 确保URL格式正确
        url = url.strip()  # 去除首尾空白
        
        # 删除URL中的不可见字符
        url = re.sub(r'[\u200b-\u200f\ufeff]', '', url)
        
        # 标准化URL格式，保留完整路径和查询参数
        if not url.startswith("http"):
            if url.startswith("www."):
                url = "https://" + url
            elif not url.startswith("taptap"):
                # 如果不是以taptap开头，加上标准前缀
                if "taptap.cn" not in url and "taptap.com" not in url:
                    url = "https://www.taptap.cn/" + url.lstrip('/')
                else:
                    url = "https://" + url
            else:
                url = "https://www." + url
        
        # 确保URL没有重复协议前缀
        url_check = re.match(r'^(https?://)(?:https?://)+(.+)$', url)
        if url_check:
            url = url_check.group(1) + url_check.group(2)
            print(f"修复了重复协议前缀，URL现在是: {url}")
            
        # 如果URL不包含taptap.cn，可能格式不正确
        if "taptap.cn" not in url and "taptap.com" not in url:
            print(f"警告: URL {url} 可能不是TapTap链接")
            
        print(f"最终访问的URL: {url}")
        return url
    
    def extract_comments(self, url):
        """提取TapTap游戏评论数据"""
        # 标准化URL
        url = self.normalize_url(url)
        
        # 提取游戏ID
        game_id = self.extract_game_id(url)
        
        # 获取游戏名称
        game_name = self.get_game_name(url, game_id)
        print(f"获取到游戏名称: {game_name}")
        
        # 设置页面加载超时时间
        self.driver.set_page_load_timeout(90)  # 增加到90秒超时
        try:
            print(f"正在访问URL: {url}")
            self.driver.get(url)
            print("页面加载成功")
        except Exception as e:
            print(f"访问URL时出错: {e}")
            # 尝试备用方法访问URL
            try:
                print("尝试备用方法访问URL...")
                self.driver.execute_script(f"window.location.href = '{url}';")
                time.sleep(5)  # 等待JavaScript导航完成
                print("使用JavaScript导航完成")
            except Exception as e2:
                print(f"备用方法也失败: {e2}")
                # 记录错误并跳过此游戏
                error_message = f"处理游戏 {self.progress['game_count'] + 1} URL {url} 时发生错误: {e}"
                self.write_error_log(error_message)
                # 更新进度并继续下一个游戏
                self.progress["game_count"] += 1
                self.save_progress(self.progress)
                return
        
        # 在爬取评论之前滚动到页面底部
        print("开始滚动页面以加载评论...")
        comments_found = self.scroll_to_bottom()
        if not comments_found:
            print("警告：未检测到评论，但仍将尝试提取页面内容")
        
        # 保存页面源码以供分析
        try:
            print("保存页面源码以供分析...")
            with open(f"source_{game_id}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"已保存页面源码到 source_{game_id}.html 文件")
            print(f"当前页面URL: {self.driver.current_url}")
        except Exception as e:
            print(f"保存源码失败: {e}")
        
        # 识别评论容器
        comment_found, all_reply_items = self.find_comment_elements()
        
        # 检查是否成功获取了评论
        if not all_reply_items or len(all_reply_items) == 0:
            error_message = f'第{self.progress["game_count"] + 1}个游戏被跳过：ID {game_id} URL {url}找到了评论元素但无法提取内容'
            print(error_message)
            self.write_error_log(error_message)
            self.progress["game_count"] += 1
            self.save_progress(self.progress)
            return
        
        print(f"开始处理 {len(all_reply_items)} 条评论...")
        
        # 创建文件名
        if game_name and game_name != game_id:
            # 清理游戏名称中的非法字符
            game_name = re.sub(r'[\\/*?:"<>|]', "", game_name)
            # 限制名称长度
            if len(game_name) > 50:
                game_name = game_name[:47] + "..."
            excel_filename = f"{game_id}_{game_name}_comments.xlsx"
        else:
            excel_filename = f"{game_id}_comments.xlsx"
        
        # 初始化计数器
        total_comments = len(all_reply_items)
        processed_comments = 0
        
        # 检查是否是继续之前的进度
        start_index = 0
        if self.progress["first_comment_index"] > 0 and game_id == str(self.progress.get("last_game_id", "")):
            start_index = self.progress["first_comment_index"]
            print(f"继续上次进度，从第 {start_index + 1} 条评论开始处理...")
        
        # 处理评论数据
        comments_data = []
        
        # 单独处理每条评论
        for i, reply_item in enumerate(all_reply_items):
            # 跳过已处理的评论
            if i < start_index:
                continue
            
            try:
                # 提取评论数据
                comment_data = self.extract_comment_data(reply_item, i, url)
                
                if comment_data:
                    comments_data.append(comment_data)
                    processed_comments += 1
                    print(f"已提取第 {i+1} 条评论")
                
                # 每处理10条评论更新一次进度
                if (i + 1) % 10 == 0:
                    self.progress["first_comment_index"] = i + 1
                    self.progress["last_game_id"] = game_id
                    self.save_progress(self.progress)
                    
                    # 每10条评论保存一次数据，避免数据丢失
                    try:
                        self.data_writer.write(comments_data, excel_filename)
                        print(f"已处理 {i+1}/{total_comments} 条评论 ({((i+1)/total_comments*100):.1f}%)并保存临时结果")
                        comments_data = []  # 清空已保存的数据
                    except Exception as e:
                        print(f"保存临时Excel文件时出错: {e}")
                        self.write_error_log(f"保存临时Excel {excel_filename} 时出错: {e}")
            
            except Exception as e:
                error_message = f"处理第 {i+1} 条评论时出错: {str(e)}"
                print(error_message)
                self.write_error_log(error_message)
                # 保存当前进度并继续
                self.progress["first_comment_index"] = i + 1
                self.progress["last_game_id"] = game_id
                self.save_progress(self.progress)
        
        # 处理完成，重置评论索引并增加游戏计数
        print(f"成功处理了 {processed_comments}/{total_comments} 条评论")
        self.progress["first_comment_index"] = 0
        self.progress["game_count"] += 1
        self.progress["last_game_id"] = ""
        self.save_progress(self.progress)
        
        # 保存剩余数据
        if comments_data:
            try:
                self.data_writer.write(comments_data, excel_filename)
                print(f"已成功保存剩余 {len(comments_data)} 条评论到 {excel_filename}")
            except Exception as e:
                print(f"保存最终Excel文件时出错: {e}")
                self.write_error_log(f"保存最终Excel {excel_filename} 时出错: {e}")
    
    def find_comment_elements(self):
        """查找评论元素"""
        # 识别评论容器
        comment_containers = [
            ".comment-list",  # 常见的评论容器
            ".reviews-container",  # 评测容器
            "#comments",  # 评论区ID
            "#reviews",  # 评测区ID
            "[id*='comment']",  # 包含comment的ID
            "[class*='comment']",  # 包含comment的类
            "[class*='review']",  # 包含review的类
            ".app-comments-wrap",  # TapTap特定评论包装
            ".review-feed-wrap"  # 评测列表包装
        ]
        
        container_found = False
        for container in comment_containers:
            container_elements = self.driver.find_elements(By.CSS_SELECTOR, container)
            if container_elements and len(container_elements) > 0:
                print(f"找到评论容器! 使用选择器: {container}")
                container_found = True
                
                # 检查容器内的内容
                container_html = container_elements[0].get_attribute('innerHTML')
                if container_html:
                    print(f"评论容器HTML长度: {len(container_html)}")
                    
                    # 尝试在容器内查找评论元素
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", container_elements[0])
                    time.sleep(3)  # 等待评论加载
                    break
        
        # 更新评论元素选择器，匹配TapTap最新版本
        comment_selectors = [
            ".comment-item",  # 常见的评论项
            ".review-item",  # 评测项
            ".comment-list .item",  # 嵌套的评论项
            ".review-list .item",  # 嵌套的评测项
            "[class*='comment-item']",  # 部分匹配类名
            "[class*='review-item']",  # 部分匹配评测项
            ".taptap-comment .comment-item",  # TapTap特定的评论项
            ".community-content .comment",  # 社区内容评论
            ".review-item-wrap",  # 评测项包装
            ".app-comments-wrap *",  # 评论区内所有元素
            ".review-item-card"  # 评测卡片
        ]
        
        # 更详细的日志
        print(f"开始尝试定位评论元素...")
        
        comment_found = False
        all_reply_items = []
        
        for selector in comment_selectors:
            try:
                # 尝试多次定位评论元素，有时需要等待JavaScript执行
                for attempt in range(3):
                    comment_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if comment_elements and len(comment_elements) > 0:
                        print(f"找到评论元素！使用选择器: {selector}，找到 {len(comment_elements)} 个评论")
                        comment_found = True
                        
                        # 尝试将视图滚动到第一个评论
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", comment_elements[0])
                        time.sleep(2)  # 等待视图变更
                        
                        # 获取页面源码，用BeautifulSoup解析
                        soup = BeautifulSoup(self.driver.page_source, "html.parser")
                        
                        # 根据找到的选择器选择正确的解析方法
                        all_reply_items = soup.select(selector)
                        
                        # 如果找到了评论但列表为空，尝试其他方法提取
                        if not all_reply_items or len(all_reply_items) == 0:
                            print(f"警告：虽然在DOM中找到了评论元素，但无法用BeautifulSoup提取。尝试其他方法...")
                            
                            # 尝试直接从评论元素获取数据
                            print("尝试直接从浏览器DOM获取评论数据...")
                            all_reply_items = []
                            
                            for idx, comment_element in enumerate(comment_elements[:20]):  # 限制为前20个避免过长
                                try:
                                    comment_html = comment_element.get_attribute('outerHTML')
                                    comment_soup = BeautifulSoup(comment_html, "html.parser")
                                    all_reply_items.append(comment_soup)
                                except Exception as e:
                                    print(f"无法获取第{idx+1}个评论的HTML: {e}")
                        
                        # 输出找到的评论数量
                        print(f"成功提取到 {len(all_reply_items)} 条评论")
                        break
                    else:
                        print(f"尝试{attempt+1}/3: 未找到评论元素，使用选择器: {selector}")
                        time.sleep(2)  # 再等待一些时间
                
                if comment_found:
                    break
            except Exception as e:
                print(f"尝试选择器 '{selector}' 时出错: {e}")
        
        return comment_found, all_reply_items
    
    def extract_comment_data(self, reply_item, index, url):
        """从评论元素中提取数据"""
        comment_id = f"comment_{index+1}"
        username = ""
        comment_content = ""
        comment_time = ""
        like_count = "0"
        
        # 尝试多种选择器提取用户名
        username_selectors = [
            ".name", ".username", ".user-name", ".nickname", 
            "[class*='user'] [class*='name']", "[class*='author']",
            ".user", ".author", ".commentator-name"
        ]
        
        for selector in username_selectors:
            username_tag = reply_item.select_one(selector)
            if username_tag and username_tag.text.strip():
                username = username_tag.text.strip()
                break
        
        # 尝试多种选择器提取评论内容
        content_selectors = [
            ".review-content", 
            ".comment-content", 
            ".desc", 
            ".content", 
            ".text",
            "p.text",
            ".body",
            ".review-item > div > p",
            "[class*='content']:not([class*='author']):not([class*='time']):not([class*='user'])"
        ]
        
        for selector in content_selectors:
            content_tag = reply_item.select_one(selector)
            if content_tag and content_tag.text.strip():
                comment_content = content_tag.text.strip()
                # 清理评论内容（去除多余空格和换行符）
                comment_content = re.sub(r'\s+', ' ', comment_content)
                break

        # 如果依然没找到评论内容，尝试查找所有段落标签
        if not comment_content:
            paragraphs = reply_item.find_all("p")
            if paragraphs and len(paragraphs) > 0:
                # 获取所有段落的文本，并拼接
                texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                if texts:
                    comment_content = " ".join(texts)
        
        # 尝试获取TapTap特有的评测内容结构
        if not comment_content:
            try:
                # 查找评测内容的特定元素
                rating_summary = reply_item.select_one(".rating-summary")
                desc_elements = reply_item.select(".desc, .text, .content")
                
                texts = []
                if rating_summary and rating_summary.get_text(strip=True):
                    texts.append(rating_summary.get_text(strip=True))
                
                for elem in desc_elements:
                    if elem.get_text(strip=True):
                        texts.append(elem.get_text(strip=True))
                
                if texts:
                    comment_content = " ".join(texts)
            except Exception as e:
                print(f"提取TapTap特定评测结构时出错: {e}")
        
        # 如果仍然没找到评论内容，尝试获取整个评论项的文本
        if not comment_content:
            all_text = reply_item.get_text(strip=True)
            if username and all_text:
                # 尝试去除用户名、时间、点赞数等元素，保留核心内容
                # 先移除用户名
                content_text = all_text.replace(username, '', 1).strip()
                
                # 移除时间相关文本
                time_patterns = [
                    r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}',
                    r'\d{1,2}[-/月]\d{1,2}',
                    r'\d+\s*分钟前', 
                    r'\d+\s*小时前', 
                    r'\d+\s*天前'
                ]
                
                for pattern in time_patterns:
                    content_text = re.sub(pattern, '', content_text)
                
                # 移除点赞数相关文本
                like_patterns = [r'\d+\s*赞', r'赞\s*\d+']
                for pattern in like_patterns:
                    content_text = re.sub(pattern, '', content_text)
                
                comment_content = content_text.strip()
            else:
                comment_content = all_text
        
        # 确保评论内容和用户名不同
        if comment_content == username:
            comment_content = "无法提取评论内容"
        
        # 尝试多种选择器提取评论时间
        time_selectors = [
            ".time", ".date", ".timestamp", ".publish-time", 
            "[class*='time']", "[class*='date']", "[datetime]", 
            ".meta time", ".info time"
        ]
        
        for selector in time_selectors:
            time_tag = reply_item.select_one(selector)
            if time_tag:
                comment_time = time_tag.text.strip()
                break
        
        # 尝试提取日期属性
        if not comment_time:
            date_attrs = ["datetime", "data-time", "title"]
            for date_attr in date_attrs:
                try:
                    elements_with_date = reply_item.select(f"[{date_attr}]")
                    for elem in elements_with_date:
                        date_text = elem.get(date_attr)
                        if date_text and re.search(r'\d{4}[-/年]\d{1,2}[-/月]|\d{1,2}[-/月]\d{1,2}|分钟前|小时前|天前', date_text):
                            comment_time = date_text
                            break
                    if comment_time:
                        break
                except Exception:
                    pass
        
        # 尝试多种选择器提取点赞数
        like_selectors = [
            ".like-count", ".thumbs-up", ".like-num", ".like", 
            "[class*='like']", "[class*='vote']", ".vote-count", 
            "[class*='upvote']", ".upvote", "[data-like-count]"
        ]
        
        for selector in like_selectors:
            like_tag = reply_item.select_one(selector)
            if like_tag:
                like_text = like_tag.text.strip()
                # 尝试提取数字
                like_match = re.search(r'\d+', like_text)
                if like_match:
                    like_count = like_match.group()
                    break
        
        # 如果无法从元素中提取点赞数，尝试从属性中提取
        if like_count == "0":
            like_attrs = ["data-like-count", "data-votes", "data-count"]
            for like_attr in like_attrs:
                try:
                    elements_with_like = reply_item.select(f"[{like_attr}]")
                    for elem in elements_with_like:
                        like_attr_value = elem.get(like_attr)
                        if like_attr_value and like_attr_value.isdigit():
                            like_count = like_attr_value
                            break
                    if like_count != "0":
                        break
                except Exception:
                    pass
        
        # 检查是否成功提取到评论内容
        if not comment_content:
            print(f"警告: 第 {index+1} 条评论无法提取内容")
            return None
        
        # 返回评论数据
        return {
            '评论ID': comment_id,
            '用户名': username,
            '评论内容': comment_content,
            '评论时间': comment_time,
            '点赞数': like_count,
            'URL': url
        }

    def get_game_name(self, url, game_id):
        """获取游戏名称
        
        Args:
            url: 游戏URL
            game_id: 游戏ID
            
        Returns:
            str: 游戏名称
        """
        try:
            # 如果URL没有指向游戏页面，则构造游戏页面URL
            if "taptap.cn/app/" not in url and "taptap.com/app/" not in url:
                url = f"https://www.taptap.cn/app/{game_id}"
                
            # 已经在游戏页面，尝试获取标题
            print(f"正在从当前页面获取游戏名称...")
                
            # 尝试从当前页面获取游戏名称
            title_selectors = [
                "h1.app-header-title",
                ".app-header-title",
                ".title",
                ".header-title",
                ".name",
                "h1.title",
                "h1",
                ".app-name",
                "[class*='title']:not([class*='sub']):not([class*='meta'])",
                "[class*='name']:not([class*='user']):not([class*='author'])"
            ]
            
            game_name = ""
            for selector in title_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.text.strip():
                            game_name = element.text.strip()
                            print(f"使用选择器 {selector} 找到游戏名称: {game_name}")
                            break
                    if game_name:
                        break
                except Exception as e:
                    continue
            
            # 如果当前页面找不到游戏名称，尝试访问游戏主页面
            if not game_name:
                print(f"当前页面未找到游戏名称，尝试访问游戏主页...")
                
                # 打开新标签页访问游戏主页
                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                game_url = f"https://www.taptap.cn/app/{game_id}"
                
                try:
                    self.driver.get(game_url)
                    time.sleep(3)  # 等待页面加载
                    
                    # 再次尝试获取游戏名称
                    for selector in title_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                if element.is_displayed() and element.text.strip():
                                    game_name = element.text.strip()
                                    print(f"从游戏主页使用选择器 {selector} 找到游戏名称: {game_name}")
                                    break
                            if game_name:
                                break
                        except Exception:
                            continue
                finally:
                    # 关闭新标签页，切回原来的标签页
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            
            if not game_name:
                print(f"无法获取游戏名称，将使用游戏ID代替")
                return game_id
                
            return game_name
            
        except Exception as e:
            print(f"获取游戏名称时出错: {e}")
            return game_id

if __name__ == "__main__":
    try:
        # 创建TapTap爬虫实例
        use_headless = input("是否使用无头模式运行浏览器(无界面，推荐用于解决闪退问题)? [y/n]: ").strip().lower() == 'y'
        crawler = TapCrawler(use_headless)
        
        # 运行爬虫
        crawler.run()
    except Exception as e:
        print(f"程序运行时发生未处理的异常: {e}")
        # 记录错误
        try:
            with open(os.path.join("logs", "error_log.txt"), "a", encoding='utf-8') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - 未处理的异常: {str(e)}\n")
        except:
            pass 