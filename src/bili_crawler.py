"""
B站爬虫适配器 - 专门用于爬取哔哩哔哩网站的评论
"""

from crawler_base import BaseCrawler, CsvWriter
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import time
import sys
import os

class BiliCrawler(BaseCrawler):
    """B站爬虫类，专门用于爬取哔哩哔哩网站的评论"""
    
    def __init__(self, use_headless=False):
        """初始化B站爬虫"""
        super().__init__(use_headless)
        self.data_writer = CsvWriter()
        # 默认使用CSV格式保存数据，适用于B站的大量评论
    
    def get_comment_selectors(self):
        """获取B站评论元素的CSS选择器"""
        return [
            ".reply-item",
            ".comment-item",
            ".list-item",
            ".reply-wrap .item",
            "[class*='reply-item']",
            "[class*='comment-item']"
        ]
    
    def handle_mini_player(self):
        """处理B站特有的迷你播放器"""
        try:
            # 尝试查找标题为"点击关闭迷你播放器"的元素
            close_buttons = []
            try:
                # 尝试查找标题为"点击关闭迷你播放器"的元素
                close_buttons.extend(self.driver.find_elements(By.XPATH, '//div[@title="点击关闭迷你播放器"]'))
                # 尝试查找类名含有mini-player的元素附近的关闭按钮
                close_buttons.extend(self.driver.find_elements(By.XPATH, '//div[contains(@class, "mini-player")]//div[contains(@class, "close")]'))
                # 尝试查找包含"关闭"字样的按钮
                close_buttons.extend(self.driver.find_elements(By.XPATH, '//div[contains(@class, "close-btn")]'))
            except Exception:
                pass
                
            # 如果找到了任何可能的关闭按钮，尝试点击第一个
            if close_buttons and len(close_buttons) > 0:
                try:
                    self.driver.execute_script("arguments[0].click();", close_buttons[0])
                    print("成功关闭迷你播放器")
                    return True
                except Exception:
                    pass
                    
            # 如果特定方法都失败了，尝试通过JavaScript处理
            try:
                # 尝试使用JavaScript隐藏可能的迷你播放器
                self.driver.execute_script('''
                    let miniPlayers = document.querySelectorAll('div[class*="mini-player"]');
                    for(let i=0; i<miniPlayers.length; i++) {
                        miniPlayers[i].style.display = 'none';
                    }
                ''')
                return True
            except Exception:
                pass
                
            return False
        except Exception as e:
            print(f"[这不影响程序正常运行] 未找到关闭按钮或无法关闭悬浮小窗")
            return False
    
    def extract_video_id(self, url):
        """从URL中提取视频ID"""
        # 从URL中提取视频ID
        video_id_search = re.search(r'bilibili\.com/video/(\w+)', url.lower())
        if not video_id_search:
            video_id_search = re.search(r'b23\.tv/(\w+)', url.lower())
            
        if video_id_search:
            video_id = video_id_search.group(1)
            print(f'开始爬取第{self.progress["game_count"]+1}个视频{video_id}')
            return video_id
        else:
            # 如果无法识别视频ID，使用URL最后部分作为ID
            parts = url.rstrip('/').split('/')
            video_id = parts[-1]
            
            print(f'第{self.progress["game_count"] + 1}个视频：无法从 URL {url} 中提取标准video_id，使用 {video_id} 作为标识')
            return video_id
    
    def normalize_url(self, url):
        """标准化URL格式"""
        url = url.strip()  # 去除首尾空白
        
        # 处理短链接
        if 'b23.tv' in url:
            print("检测到B站短链接，尝试解析完整链接...")
            try:
                self.driver.get(url)
                time.sleep(2)  # 等待重定向
                url = self.driver.current_url
                print(f"已解析为完整链接: {url}")
            except Exception as e:
                print(f"解析短链接时出错: {e}")
        
        # 确保URL格式正确
        if not url.startswith("http"):
            url = "https://" + url
        
        # 确保URL没有重复协议前缀
        url_check = re.match(r'^(https?://)(?:https?://)+(.+)$', url)
        if url_check:
            url = url_check.group(1) + url_check.group(2)
            print(f"修复了重复协议前缀，URL现在是: {url}")
            
        # 添加展开评论区参数
        if "?" not in url:
            url += "?t=0"
        else:
            url += "&t=0"
            
        print(f"最终访问的URL: {url}")
        return url
    
    def extract_comments(self, url):
        """提取B站视频评论数据"""
        # 标准化URL
        url = self.normalize_url(url)
        
        # 提取视频ID
        video_id = self.extract_video_id(url)
        
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
                # 记录错误并跳过此视频
                error_message = f"处理视频 {self.progress['game_count'] + 1} URL {url} 时发生错误: {e}"
                self.write_error_log(error_message)
                # 更新进度并继续下一个视频
                self.progress["game_count"] += 1
                self.save_progress(self.progress)
                return
        
        # 获取视频标题
        video_title = self.get_video_title()
        print(f"获取到视频标题: {video_title}")
        
        # 处理迷你播放器
        self.handle_mini_player()
        
        # 尝试等待视频评论区出现
        try:
            # 先等待页面完全加载
            time.sleep(5)
            
            # 等待评论区元素出现
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'comment')]"))
            )
        except Exception as e:
            print(f"等待评论区出现时出错: {e}")
        
        # 在爬取评论之前滚动到页面底部
        print("开始滚动页面以加载评论...")
        comments_found = self.scroll_to_bottom(max_scroll_count=45, scroll_pause_time=4)
        if not comments_found:
            print("警告：未检测到评论，但仍将尝试提取页面内容")
        
        # 保存页面源码以供分析
        try:
            print("保存页面源码以供分析...")
            with open(f"source_{video_id}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"已保存页面源码到 source_{video_id}.html 文件")
            print(f"当前页面URL: {self.driver.current_url}")
        except Exception as e:
            print(f"保存源码失败: {e}")
        
        # 查找评论元素
        reply_items = self.driver.find_elements(By.CSS_SELECTOR, '.reply-item')
        if not reply_items or len(reply_items) == 0:
            error_message = f'第{self.progress["game_count"] + 1}个视频被跳过：ID {video_id} URL {url} 没有找到评论'
            print(error_message)
            self.write_error_log(error_message)
            self.progress["game_count"] += 1
            self.save_progress(self.progress)
            return
        
        print(f"找到 {len(reply_items)} 条一级评论，开始处理...")
        
        # 创建文件名
        if video_title and video_title != video_id:
            # 清理视频标题中的非法字符
            video_title = re.sub(r'[\\/*?:"<>|]', "", video_title)
            # 限制标题长度
            if len(video_title) > 50:
                video_title = video_title[:47] + "..."
            csv_filename = f"{video_id}_{video_title}_comments.csv"
        else:
            csv_filename = f"{video_id}_comments.csv"
        
        # 初始化列表存储评论数据
        comments_data = []
        
        # 处理一级评论
        for i, reply_item in enumerate(reply_items):
            try:
                # 检查是否继续之前的进度
                if i < self.progress.get("first_comment_index", 0):
                    continue
                
                # 更新当前处理的评论索引
                self.progress["first_comment_index"] = i
                self.save_progress(self.progress)
                
                # 提取一级评论数据
                comment_data = self.extract_reply_item(reply_item, i, video_id)
                if comment_data:
                    comments_data.append(comment_data)
                
                # 尝试点击"查看更多"按钮获取二级评论
                try:
                    # 检查是否有二级评论
                    view_more_buttons = reply_item.find_elements(By.CSS_SELECTOR, ".view-more")
                    if view_more_buttons and len(view_more_buttons) > 0:
                        for view_more_button in view_more_buttons:
                            # 尝试点击查看更多按钮
                            if "查看" in view_more_button.text:
                                self.driver.execute_script("arguments[0].scrollIntoView();", view_more_button)
                                self.driver.execute_script("window.scrollBy(0, -100);")
                                view_more_button.click()
                                time.sleep(2)  # 等待二级评论加载
                                
                                # 提取二级评论
                                sub_comments_data = self.extract_sub_comments(i, video_id, comment_data['用户名'], comment_data['用户ID'])
                                if sub_comments_data:
                                    comments_data.extend(sub_comments_data)
                                break
                except Exception as e:
                    print(f"处理二级评论时出错: {e}")
                
                # 每10条评论保存一次
                if (i + 1) % 10 == 0 or i == len(reply_items) - 1:
                    # 保存到CSV文件
                    self.data_writer.write(comments_data, csv_filename)
                    print(f"已处理 {i+1}/{len(reply_items)} 条评论并保存结果")
                    comments_data = []  # 清空已保存的数据
            
            except Exception as e:
                error_message = f"处理第 {i+1} 条评论时出错: {str(e)}"
                print(error_message)
                self.write_error_log(error_message)
                self.progress["first_comment_index"] = i + 1
                self.save_progress(self.progress)
        
        # 处理完成，重置评论索引并增加视频计数
        self.progress["first_comment_index"] = 0
        self.progress["game_count"] += 1
        self.save_progress(self.progress)
        
        print(f"视频 {video_id} 的评论处理完成")
    
    def extract_reply_item(self, reply_item, index, video_id):
        """提取一级评论数据"""
        try:
            # 提取用户名
            username_element = reply_item.find_element(By.CSS_SELECTOR, ".user-name")
            username = username_element.text
            
            # 尝试提取用户ID
            user_id = ""
            try:
                user_link = username_element.get_attribute("href")
                if user_link:
                    id_match = re.search(r'space\.bilibili\.com/(\d+)', user_link)
                    if id_match:
                        user_id = id_match.group(1)
            except Exception:
                pass
            
            # 提取评论内容
            content_element = reply_item.find_element(By.CSS_SELECTOR, ".reply-content")
            content = content_element.text
            
            # 提取时间
            time_text = ""
            try:
                time_element = reply_item.find_element(By.CSS_SELECTOR, ".reply-time")
                time_text = time_element.text
            except Exception:
                pass
            
            # 提取点赞数
            likes = "0"
            try:
                like_element = reply_item.find_element(By.CSS_SELECTOR, ".like-count")
                likes = like_element.text.strip()
                if not likes or not likes.isdigit():
                    likes = "0"
            except Exception:
                pass
            
            # 返回评论数据
            return {
                '编号': index + 1,
                '隶属关系': '一级评论',
                '被评论者昵称': '',
                '被评论者ID': '',
                '用户名': username,
                '用户ID': user_id,
                '评论内容': content,
                '发布时间': time_text,
                '点赞数': likes
            }
        
        except Exception as e:
            print(f"提取一级评论数据失败: {e}")
            return None
    
    def extract_sub_comments(self, parent_index, video_id, parent_nickname, parent_user_id):
        """提取二级评论数据"""
        sub_comments_data = []
        
        try:
            # 获取当前评论项的所有二级评论
            sub_replies = self.driver.find_elements(By.CSS_SELECTOR, f".reply-item:nth-child({parent_index + 1}) .sub-reply-item")
            
            if not sub_replies or len(sub_replies) == 0:
                print(f"未找到评论项 {parent_index + 1} 的二级评论")
                return []
            
            print(f"发现 {len(sub_replies)} 条二级评论")
            
            # 提取每条二级评论
            for j, sub_reply in enumerate(sub_replies):
                try:
                    # 提取用户名
                    username_element = sub_reply.find_element(By.CSS_SELECTOR, ".user-name")
                    username = username_element.text
                    
                    # 尝试提取用户ID
                    user_id = ""
                    try:
                        user_link = username_element.get_attribute("href")
                        if user_link:
                            id_match = re.search(r'space\.bilibili\.com/(\d+)', user_link)
                            if id_match:
                                user_id = id_match.group(1)
                    except Exception:
                        pass
                    
                    # 提取评论内容
                    content_element = sub_reply.find_element(By.CSS_SELECTOR, ".reply-content")
                    content = content_element.text
                    
                    # 提取时间
                    time_text = ""
                    try:
                        time_element = sub_reply.find_element(By.CSS_SELECTOR, ".reply-time")
                        time_text = time_element.text
                    except Exception:
                        pass
                    
                    # 提取点赞数
                    likes = "0"
                    try:
                        like_element = sub_reply.find_element(By.CSS_SELECTOR, ".like-count")
                        likes = like_element.text.strip()
                        if not likes or not likes.isdigit():
                            likes = "0"
                    except Exception:
                        pass
                    
                    # 添加二级评论数据
                    sub_comments_data.append({
                        '编号': f"{parent_index + 1}.{j + 1}",
                        '隶属关系': '二级评论',
                        '被评论者昵称': parent_nickname,
                        '被评论者ID': parent_user_id,
                        '用户名': username,
                        '用户ID': user_id,
                        '评论内容': content,
                        '发布时间': time_text,
                        '点赞数': likes
                    })
                
                except Exception as e:
                    print(f"提取二级评论数据失败: {e}")
            
            return sub_comments_data
        
        except Exception as e:
            print(f"获取二级评论失败: {e}")
            return []

    def get_video_title(self):
        """获取B站视频标题
        
        Returns:
            str: 视频标题
        """
        try:
            # 尝试获取视频标题
            title_selectors = [
                "h1.video-title",
                ".video-title",
                ".title",
                ".tit",
                "h1",
                ".video-info-title",
                "[data-title]",
                ".head-title",
                ".media-title",
                "[class*='title']:not([class*='sub']):not([class*='meta'])"
            ]
            
            video_title = ""
            for selector in title_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.text.strip():
                            video_title = element.text.strip()
                            print(f"使用选择器 {selector} 找到视频标题: {video_title}")
                            break
                    if video_title:
                        break
                except Exception as e:
                    continue
            
            # 尝试从页面标题中提取
            if not video_title:
                try:
                    page_title = self.driver.title
                    if page_title:
                        # 移除页面标题中的常见后缀
                        video_title = re.sub(r'_哔哩哔哩.*$|_bilibili.*$|\s*-\s*bilibili$', '', page_title).strip()
                        print(f"从页面标题中找到视频标题: {video_title}")
                except Exception as e:
                    pass
            
            if not video_title:
                print(f"无法获取视频标题，将使用视频ID代替")
                return ""
                
            return video_title
            
        except Exception as e:
            print(f"获取视频标题时出错: {e}")
            return ""

if __name__ == "__main__":
    try:
        # 创建B站爬虫实例
        use_headless = input("是否使用无头模式运行浏览器(无界面，推荐用于解决闪退问题)? [y/n]: ").strip().lower() == 'y'
        crawler = BiliCrawler(use_headless)
        
        # 运行爬虫
        crawler.run('video_list.txt')  # B站使用video_list.txt作为URL列表文件
    except Exception as e:
        print(f"程序运行时发生未处理的异常: {e}")
        # 记录错误
        try:
            with open("error_log.txt", "a", encoding='utf-8') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - 未处理的异常: {str(e)}\n")
        except:
            pass 