#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
爬虫Web应用
支持Chrome和Edge浏览器
"""

import os
import sys
import re
import time
import json
import glob
import csv  # 添加csv模块导入
import logging
import threading
import importlib.util
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from werkzeug.serving import make_server

# 添加项目根目录到系统路径，确保能够导入自定义模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 获取浏览器类型
BROWSER_TYPE = os.environ.get("STEAM_CRAWLER_BROWSER", "chrome").lower()

# 尝试导入爬虫模块
try:
    if BROWSER_TYPE == "edge":
        # 尝试导入Edge版本的爬虫
        try:
            from steam_simple_crawler_edge import SteamSimpleCrawlerEdge as SteamCrawler
            from steam_simple_crawler_edge import JsonDataWriter, CsvDataWriter
            print("已加载Edge版本的爬虫模块")
        except ImportError:
            print("警告：无法导入Edge版本的爬虫模块，回退到Chrome版本")
            from steam_simple_crawler import SteamSimpleCrawler as SteamCrawler
            from steam_simple_crawler import JsonDataWriter, CsvDataWriter
    else:
        # 默认使用Chrome版本的爬虫
        from steam_simple_crawler import SteamSimpleCrawler as SteamCrawler
        from steam_simple_crawler import JsonDataWriter, CsvDataWriter
        print("已加载Chrome版本的爬虫模块")
except ImportError:
    print("警告：无法导入steam_simple_crawler模块，部分功能可能不可用")

from flask.logging import default_handler

class RequestFilter(logging.Filter):
    def filter(self, record):
        """过滤掉对/api/status的请求日志"""
        return 'GET /api/status' not in record.getMessage()

# 应用过滤器到默认处理器
default_handler.addFilter(RequestFilter())

# CSV读取函数
def read_csv_file(file_path, encoding='utf-8-sig'):
    """使用csv模块读取CSV文件"""
    with open(file_path, 'r', encoding=encoding) as f:
        reader = csv.reader(f)
        headers = next(reader)  # 读取列名
        rows = list(reader)     # 读取所有行
    
    # 构建结构化数据
    result = {
        'columns': headers,
        'data': []
    }
    
    for row in rows:
        row_dict = {}
        for i, header in enumerate(headers):
            if i < len(row):
                row_dict[header] = row[i]
            else:
                row_dict[header] = ''
        result['data'].append(row_dict)
    
    return result

# 创建Flask应用
app = Flask(__name__)

# 爬虫任务状态
crawler_status = {
    "running": False,
    "progress": 0,
    "log": [],
    "type": None,
    "browser": BROWSER_TYPE  # 添加浏览器类型到状态中
}

# 年龄验证任务状态
age_verification_status = {
    "running": False,
    "log": [],
    "success": None,
    "browser": BROWSER_TYPE  # 添加浏览器类型到状态中
}

@app.route('/')
def index():
    """首页"""
    return render_template('index.html', browser_type=BROWSER_TYPE)

@app.route('/steam')
def steam_only():
    return render_template('steam_only.html', browser_type=BROWSER_TYPE)

# 创建禁止记录访问日志的装饰器
def no_access_log(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route('/api/status')
@no_access_log
def get_status():
    """获取爬虫状态"""
    return jsonify(crawler_status)

@app.route('/api/age_verification_status')
def get_age_verification_status():
    """获取年龄验证状态"""
    return jsonify(age_verification_status)

@app.route('/api/verify_age', methods=['POST'])
def verify_age():
    """处理年龄验证请求"""
    global age_verification_status
    
    if age_verification_status["running"]:
        return jsonify({"success": False, "message": "年龄验证已在运行中"})
    
    data = request.get_json()
    game_id = data.get('game_id', '')
    use_headless = data.get('headless', True)  # 获取无头模式设置，默认为True
    
    # 验证游戏ID
    if not game_id:
        return jsonify({"success": False, "message": "请输入有效的游戏ID"})
    
    # 重置状态
    age_verification_status = {
        "running": True,
        "log": ["正在启动年龄验证..."],
        "success": None,
        "headless": use_headless,  # 记录无头模式设置
        "browser": BROWSER_TYPE    # 添加浏览器类型
    }
    
    # 启动年龄验证线程
    thread = threading.Thread(target=run_age_verification, args=(game_id, use_headless))
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True})

def run_age_verification(game_id, use_headless=True):
    """运行年龄验证的线程函数"""
    global age_verification_status
    
    try:
        # 动态导入年龄验证模块
        age_verification_status["log"].append("正在导入年龄验证模块...")
        
        # 尝试导入项目根目录的age_verification模块
        spec = importlib.util.spec_from_file_location(
            "age_verification", 
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "age_verification.py")
        )
        age_verification = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(age_verification)
        
        age_verification_status["log"].append(f"开始处理游戏ID: {game_id}的年龄验证...")
        
        # 使用年龄验证模块处理
        result = age_verification.handle_age_verification_for_game(game_id, use_headless=use_headless, browser_type=BROWSER_TYPE)
        
        if result:
            age_verification_status["log"].append("年龄验证处理成功")
            age_verification_status["success"] = True
        else:
            age_verification_status["log"].append("年龄验证处理失败")
            age_verification_status["success"] = False
            
    except Exception as e:
        age_verification_status["log"].append(f"年龄验证过程中出错: {str(e)}")
        age_verification_status["success"] = False
    finally:
        age_verification_status["running"] = False

@app.route('/api/start', methods=['POST'])
def start_crawler():
    """启动爬虫"""
    global crawler_status
    
    if crawler_status["running"]:
        return jsonify({"success": False, "message": "爬虫已在运行中"})
    
    data = request.get_json()
    crawler_type = data.get('type')
    url = data.get('url', '')
    use_headless = data.get('headless', True)  # 获取无头模式设置，默认为True
    max_reviews = data.get('max_reviews', None)  # 获取最大评论数，默认为None（全部爬取）
    
    # 调试信息 - 输出接收到的参数
    print(f"DEBUG - API接收到的参数: type={crawler_type}, url={url}, headless={use_headless}, max_reviews={max_reviews}")
    
    # 验证爬虫类型
    if crawler_type not in ['steam', 'taptap', 'bilibili']:
        return jsonify({"success": False, "message": "不支持的爬虫类型"})
    
    # 验证URL格式
    if not url:
        return jsonify({"success": False, "message": "请输入有效的URL或ID"})
    
    # 重置爬虫状态
    crawler_status = {
        "running": True,
        "progress": 0,
        "log": [f"正在准备{crawler_type}爬虫... (使用 {BROWSER_TYPE.upper()} 浏览器)"],
        "type": crawler_type,
        "browser": BROWSER_TYPE  # 添加浏览器类型
    }
    
    # 启动爬虫线程
    thread = threading.Thread(target=run_crawler, args=(crawler_type, url, use_headless, max_reviews))
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True})

# 添加查看评论数据的路由
@app.route('/comments')
def list_comments():
    """查看已爬取的评论列表"""
    # 获取output目录下的所有CSV和JSON文件
    csv_files = glob.glob(os.path.join('output', '*.csv'))
    
    # 查找JSON评论文件（Steam评论通常保存为JSON格式）
    json_files = []
    for root, dirs, files in os.walk('output'):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    # 组合所有文件并排序
    all_files = csv_files + json_files
    all_files.sort(key=os.path.getmtime, reverse=True)  # 按修改时间排序
    
    files_data = []
    
    # 处理CSV文件
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) / 1024  # KB
        modified_time = time.ctime(os.path.getmtime(file_path))
        
        # 检查是否是Steam评论CSV文件
        is_steam_comment = False
        app_id = None
        comment_count = 0
        
        if "评论_" in filename:
            try:
                # 尝试读取CSV文件，获取评论数量
                with open(file_path, 'r', encoding='utf-8') as f:
                    # 跳过标题行
                    next(f)
                    # 计算行数
                    comment_count = sum(1 for _ in f)
                
                # 从文件名中提取app_id
                app_id_match = re.search(r'评论_(\d+)\.csv$', filename)
                if app_id_match:
                    app_id = app_id_match.group(1)
                    is_steam_comment = True
            except Exception as e:
                print(f"读取CSV文件出错: {e}")
        
        if is_steam_comment and app_id:
            # 这是Steam评论CSV文件
            game_title = filename.replace(f"_评论_{app_id}.csv", "")
            
            files_data.append({
                'path': f"csv_{app_id}",
                'filename': f"{game_title}",
                'type': 'csv_steam',
                'count': comment_count,
                'size': "{:.2f} KB".format(file_size),
                'modified': modified_time,
                'file': filename
            })
        else:
            # 普通CSV文件
            files_data.append({
                'path': file_path,
                'filename': filename,
                'type': 'csv',
                'size': "{:.2f} KB".format(file_size),
                'modified': modified_time
            })
    
    # 处理JSON游戏组
    json_game_groups = {}
    for file_path in json_files:
        # 获取父目录名（通常是app_ID格式）
        parent_dir = os.path.basename(os.path.dirname(file_path))
        
        if parent_dir.startswith('app_'):
            app_id = parent_dir.replace('app_', '')
            if app_id not in json_game_groups:
                json_game_groups[app_id] = []
            json_game_groups[app_id].append(file_path)
    
    for app_id, game_files in json_game_groups.items():
        # 计算这个游戏的所有评论文件大小总和
        total_size = sum(os.path.getsize(f) for f in game_files) / 1024  # KB
        # 获取最新的修改时间
        latest_time = max(os.path.getmtime(f) for f in game_files)
        modified_time = time.ctime(latest_time)
        
        # 尝试从第一个文件中获取游戏标题
        game_title = f"App {app_id}"
        try:
            if game_files:
                with open(game_files[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'game_title' in data:
                        game_title = data['game_title']
        except:
            pass
            
        files_data.append({
            'path': f"app_{app_id}",
            'filename': f"{game_title} (AppID: {app_id})",
            'type': 'json_group',
            'count': len(game_files),
            'size': "{:.2f} KB".format(total_size),
            'modified': modified_time
        })
    
    return render_template('comments.html', files=files_data)

@app.route('/comments/steam/<app_id>')
def view_steam_game_comments(app_id):
    """查看特定Steam游戏的评论"""
    game_dir = os.path.join('output', f'app_{app_id}')
    
    if not os.path.exists(game_dir):
        return render_template('error.html', error=f"找不到AppID为 {app_id} 的游戏评论数据")
    
    # 获取目录下所有JSON文件
    json_files = glob.glob(os.path.join(game_dir, '*.json'))
    json_files.sort(key=os.path.getmtime, reverse=True)  # 按修改时间排序
    
    # 分页处理
    page = request.args.get('page', 1, type=int)
    per_page = 20  # 每页显示的评论文件数量
    
    # 计算总页数
    total_items = len(json_files)
    pages = (total_items + per_page - 1) // per_page
    
    # 确保页码有效
    if page < 1:
        page = 1
    elif page > pages and pages > 0:
        page = pages
    
    # 提取当前页的数据
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    current_page_files = json_files[start_idx:end_idx]
    
    # 读取文件内容
    comments = []
    game_title = f"App {app_id}"
    
    for file_path in current_page_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                review = json.load(f)
                
                # 保存游戏标题
                if 'game_title' in review and game_title == f"App {app_id}":
                    game_title = review['game_title']
                
                # 添加文件路径以便后续操作
                review['_file_path'] = file_path
                comments.append(review)
        except Exception as e:
            comments.append({
                '_file_path': file_path,
                'error': str(e),
                'content': '读取文件出错'
            })
    
    return render_template('steam_comments.html', 
                         app_id=app_id,
                         game_title=game_title,
                         comments=comments,
                         total_comments=total_items,
                         pages=pages,
                         current_page=page)

@app.route('/comments/view/<path:file_path>')
def view_comment_file(file_path):
    """查看特定评论文件的内容，支持分页"""
    full_path = os.path.join('output', os.path.basename(file_path))
    page = request.args.get('page', 1, type=int)
    per_page = 50  # 每页显示的评论数
    
    try:
        # 尝试读取CSV文件内容
        if full_path.endswith('.csv'):
            # 使用csv模块读取CSV文件
            try:
                result = read_csv_file(full_path)
                comment_count = len(result['data'])
                
                # 计算总页数
                pages = (comment_count + per_page - 1) // per_page
                
                # 确保页码有效
                if page < 1:
                    page = 1
                elif page > pages and pages > 0:
                    page = pages
                
                # 提取当前页的数据
                start_idx = (page - 1) * per_page
                end_idx = min(start_idx + per_page, comment_count)
                current_page_data = result['data'][start_idx:end_idx]
                
                return render_template('comment_details.html', 
                                      filename=os.path.basename(full_path),
                                      comments=current_page_data,
                                      columns=result['columns'],
                                      comment_count=comment_count,
                                      pages=pages,
                                      current_page=page)
            except Exception as e:
                return render_template('comment_details.html',
                                      filename=os.path.basename(full_path),
                                      error=f"读取文件出错: {str(e)}")
        else:
            return render_template('comment_details.html',
                                  filename=os.path.basename(full_path),
                                  error="不支持的文件类型，仅支持CSV格式")
    except Exception as e:
        return render_template('comment_details.html',
                              filename=os.path.basename(full_path),
                              error="读取文件出错: {}".format(str(e)))

@app.route('/open_output_folder')
def open_output_folder():
    """打开output文件夹"""
    try:
        output_path = os.path.abspath('output')
        
        # 检测操作系统并使用适当的命令打开文件夹
        if sys.platform.startswith('darwin'):  # macOS
            subprocess.Popen(['open', output_path])
        elif sys.platform.startswith('win'):   # Windows
            subprocess.Popen(['explorer', output_path])
        else:  # Linux
            subprocess.Popen(['xdg-open', output_path])
            
        return jsonify({"success": True, "message": "已打开输出文件夹"})
    except Exception as e:
        return jsonify({"success": False, "message": f"打开文件夹失败: {str(e)}"})

def run_crawler(crawler_type, url='', use_headless=True, max_reviews=None):
    """运行爬虫的线程函数"""
    global crawler_status
    
    # 调试信息 - 输出线程接收到的参数
    print(f"DEBUG - run_crawler线程接收到的参数: type={crawler_type}, url={url}, headless={use_headless}, max_reviews={max_reviews}, browser={BROWSER_TYPE}")
    
    # 更新初始状态
    crawler_status["log"].append(f"正在准备{crawler_type}爬虫... (最大评论数: {max_reviews if max_reviews is not None else '无限制'})")
    crawler_status["log"].append("服务器状态：初始化爬虫环境")
    crawler_status["progress"] = 5
    
    try:
        if crawler_type == "steam":
            # 检查是否跳过登录检查
            skip_login = os.environ.get('SKIP_LOGIN_CHECK', '0') == '1'
            
            if skip_login:
                # 使用简化版爬虫（不需要登录）
                crawler_status["log"].append(f"使用简化版Steam爬虫（无需登录，使用 {BROWSER_TYPE.upper()} 浏览器）...")
                crawler_status["log"].append("服务器状态：加载简化版Steam爬虫依赖")
                crawler_status["progress"] = 10
                try:
                    # 根据浏览器类型选择爬虫
                    if BROWSER_TYPE == "edge":
                        try:
                            # 使用Edge版本的爬虫
                            from steam_simple_crawler_edge import SteamSimpleCrawlerEdge, CsvDataWriter
                            crawler_class = SteamSimpleCrawlerEdge
                            crawler_status["log"].append("已加载Edge版本的爬虫模块")
                        except ImportError:
                            # 回退到Chrome版本
                            from steam_simple_crawler import SteamSimpleCrawler, CsvDataWriter
                            crawler_class = SteamSimpleCrawler
                            crawler_status["log"].append("Edge版本爬虫模块不可用，回退到Chrome版本")
                    else:
                        # 默认使用Chrome版本
                        from steam_simple_crawler import SteamSimpleCrawler, CsvDataWriter
                        crawler_class = SteamSimpleCrawler
                    
                    # 初始化数据写入器
                    data_writer = CsvDataWriter()
                    
                    # 初始化爬虫
                    crawler_status["log"].append("正在初始化简化版爬虫...")
                    crawler_status["log"].append(f"服务器状态：创建{BROWSER_TYPE.upper()}浏览器实例")
                    crawler_status["progress"] = 15
                    crawler = crawler_class(use_headless=use_headless, data_writer=data_writer)
                    
                    # 更新日志
                    crawler_status["log"].append(f"简化版Steam爬虫已启动 (使用 {BROWSER_TYPE.upper()} 浏览器)")
                    crawler_status["log"].append("服务器状态：爬虫初始化完成")
                    crawler_status["progress"] = 20
                    
                    if url:
                        crawler_status["log"].append("正在爬取Steam评论: {}".format(url))
                        crawler_status["log"].append("服务器状态：正在访问目标网页")
                        crawler_status["progress"] = 25
                        try:
                            crawler_status["log"].append("第一阶段：开始滚动加载所有评论...")
                            crawler_status["log"].append("服务器状态：正在加载所有评论，请耐心等待")
                            crawler_status["progress"] = 30
                            
                            # 设置进度更新的回调函数
                            def progress_callback(phase, progress, message):
                                if phase == "scroll":
                                    # 滚动阶段的进度为30-60%
                                    crawler_status["progress"] = 30 + int(progress * 30)
                                    crawler_status["log"].append(f"滚动加载评论: {message}")
                                    
                                    # 检查是否找到了评论总数信息
                                    total_match = re.search(r'已加载 (\d+) 条评论', message)
                                    if total_match:
                                        total_count = int(total_match.group(1))
                                        if max_reviews is None or total_count < max_reviews:
                                            crawler_status["log"].append(f"检测到评论总数：{total_count}")
                                
                                elif phase == "extract":
                                    # 提取阶段的进度为60-100%
                                    crawler_status["progress"] = 60 + int(progress * 40)
                                    crawler_status["log"].append(f"提取评论数据: {message}")
                            
                            # 将回调函数传递给爬虫
                            crawler.set_progress_callback(progress_callback)
                            
                            result = crawler.run(url, max_reviews)
                            crawler_status["log"].append("数据提取完成")
                            crawler_status["log"].append("服务器状态：评论数据已保存到output目录")
                            crawler_status["progress"] = 100
                        except Exception as e:
                            crawler_status["log"].append("提取数据时出错: {}".format(str(e)))
                            crawler_status["log"].append("服务器状态：爬虫遇到错误，请检查URL是否有效")
                    else:
                        crawler_status["log"].append("未提供有效的Steam URL")
                        crawler_status["log"].append("服务器状态：需要有效的游戏URL才能继续")
                except Exception as e:
                    crawler_status["log"].append("导入或运行简化版爬虫出错: {}".format(str(e)))
                    crawler_status["log"].append("服务器状态：爬虫启动失败，尝试使用标准爬虫")
                    # 如果简化版爬虫失败，回退到标准爬虫
                    skip_login = False
            
            # 如果没有使用简化版爬虫或简化版爬虫失败，使用标准爬虫
            if not skip_login:
                # 导入并运行标准Steam爬虫
                crawler_status["log"].append("正在导入Steam爬虫模块...")
                crawler_status["log"].append("服务器状态：加载Steam爬虫依赖")
                crawler_status["progress"] = 10
                from steam_crawler import SteamCrawler
                
                # 创建一个被多个组件共享的浏览器实例
                shared_driver = None
                
                # 对于Steam爬虫，先统一处理登录和年龄验证
                if url and ("steamcommunity.com/app/" in url or "/app/" in url):
                    # 提取游戏ID
                    try:
                        app_id = url.split('/app/')[1].split('/')[0]
                        crawler_status["log"].append(f"提取的游戏ID: {app_id}")
                        
                        # 统一处理登录和年龄验证
                        crawler_status["log"].append("1. 检查登录状态和处理年龄验证...")
                        crawler_status["log"].append("服务器状态：准备验证流程")
                        
                        # 导入年龄验证模块
                        spec = importlib.util.spec_from_file_location(
                            "age_verification", 
                            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "age_verification.py")
                        )
                        
                        if spec:
                            age_verification = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(age_verification)
                            
                            # 使用同一个浏览器实例处理所有操作，避免重复启动浏览器
                            crawler_status["log"].append("2. 设置浏览器实例...")
                            # 创建共享的浏览器实例
                            shared_driver = age_verification.setup_driver(use_headless=use_headless)
                            
                            # 检查登录状态，确保自动加载cookies
                            crawler_status["log"].append("3. 加载已保存的cookies...")
                            age_verification.load_cookies(shared_driver)
                            
                            # 确认cookies已正确加载，刷新页面
                            crawler_status["log"].append("3.1 验证cookies是否正确加载...")
                            shared_driver.get("https://store.steampowered.com/")
                            time.sleep(3)  # 等待页面加载
                            
                            # 处理目标游戏的年龄验证
                            crawler_status["log"].append(f"4. 处理游戏 {app_id} 的年龄验证...")
                            verification_result = age_verification.handle_age_verification_for_game(
                                app_id, 
                                use_headless=use_headless,
                                existing_driver=shared_driver # 使用现有的浏览器实例
                            )
                            
                            if verification_result:
                                crawler_status["log"].append("✅ 年龄验证处理成功")
                            else:
                                crawler_status["log"].append("❌ 年龄验证处理失败，继续尝试爬取")
                            
                            # 保存最新的cookies
                            crawler_status["log"].append("5. 保存最新cookies...")
                            age_verification.save_cookies(shared_driver)
                            
                            # 不关闭浏览器，而是继续使用它
                            crawler_status["log"].append("6. 继续使用当前浏览器实例进行爬取...")
                        else:
                            crawler_status["log"].append("未找到age_verification模块，跳过预处理步骤")
                    except Exception as e:
                        crawler_status["log"].append(f"预处理过程中出错: {str(e)}")
                        crawler_status["log"].append("继续爬取评论，可能会受到年龄限制影响")
                
                # 初始化爬虫 - 使用已存在的浏览器实例（如果有）
                crawler_status["log"].append("正在初始化爬虫...")
                crawler_status["log"].append("服务器状态：准备爬虫实例")
                crawler_status["progress"] = 15
                
                if shared_driver:
                    crawler_status["log"].append("使用已创建的浏览器实例...")
                    crawler = SteamCrawler(use_headless=use_headless, existing_driver=shared_driver)
                else:
                    crawler_status["log"].append("创建新的浏览器实例...")
                    crawler = SteamCrawler(use_headless=use_headless)
                
                # 更新日志
                crawler_status["log"].append("Steam爬虫已启动")
                crawler_status["log"].append("服务器状态：爬虫初始化完成")
                crawler_status["progress"] = 20
                
                if url:
                    crawler_status["log"].append("正在爬取Steam评论: {}".format(url))
                    crawler_status["log"].append("服务器状态：正在访问目标网页")
                    crawler_status["progress"] = 25
                    try:
                        crawler_status["log"].append("第一阶段：开始滚动加载所有评论...")
                        crawler_status["log"].append("服务器状态：正在加载所有评论，请耐心等待")
                        crawler_status["progress"] = 30
                        
                        # 设置进度更新的回调函数
                        def progress_callback(phase, progress, message):
                            if phase == "scroll":
                                # 滚动阶段的进度为30-60%
                                crawler_status["progress"] = 30 + int(progress * 30)
                                crawler_status["log"].append(f"滚动加载评论: {message}")
                                
                                # 检查是否找到了评论总数信息
                                total_match = re.search(r'已加载 (\d+) 条评论', message)
                                if total_match:
                                    total_count = int(total_match.group(1))
                                    if max_reviews is None or total_count < max_reviews:
                                        crawler_status["log"].append(f"检测到评论总数：{total_count}")
                            
                            elif phase == "extract":
                                # 提取阶段的进度为60-100%
                                crawler_status["progress"] = 60 + int(progress * 40)
                                crawler_status["log"].append(f"提取评论数据: {message}")
                        
                        # 将回调函数传递给爬虫
                        crawler.set_progress_callback(progress_callback)
                        
                        result = crawler.run(url, max_reviews)
                        crawler_status["log"].append("数据提取完成")
                        crawler_status["log"].append("服务器状态：评论数据已保存到output目录")
                        crawler_status["progress"] = 100
                    except Exception as e:
                        crawler_status["log"].append("提取数据时出错: {}".format(str(e)))
                        crawler_status["log"].append("服务器状态：爬虫遇到错误，请检查URL是否有效")
                else:
                    crawler_status["log"].append("未提供有效的Steam URL")
                    crawler_status["log"].append("服务器状态：需要有效的游戏URL才能继续")
        
        elif crawler_type == "taptap":
            # 导入并运行TapTap爬虫
            crawler_status["log"].append("正在导入TapTap爬虫模块...")
            crawler_status["log"].append("服务器状态：加载TapTap爬虫依赖")
            crawler_status["progress"] = 10
            from tap_crawler import TapCrawler
            
            # 初始化爬虫
            crawler_status["log"].append("正在初始化爬虫...")
            crawler_status["log"].append("服务器状态：创建Chrome浏览器实例")
            crawler_status["progress"] = 15
            crawler = TapCrawler(use_headless=use_headless)
            
            # 更新日志
            crawler_status["log"].append("TapTap爬虫已启动")
            crawler_status["log"].append("服务器状态：爬虫初始化完成")
            crawler_status["progress"] = 20
            
            if url:
                crawler_status["log"].append("正在爬取TapTap评论: {}".format(url))
                crawler_status["log"].append("服务器状态：正在访问TapTap游戏页面")
                crawler_status["progress"] = 25
                try:
                    crawler_status["log"].append("开始提取评论数据...")
                    crawler_status["log"].append("服务器状态：页面滚动中，收集评论数据")
                    crawler_status["progress"] = 30
                    crawler.extract_comments(url)
                    crawler_status["log"].append("数据提取完成")
                    crawler_status["log"].append("服务器状态：TapTap评论数据已保存到output目录")
                    crawler_status["progress"] = 100
                except Exception as e:
                    crawler_status["log"].append("提取数据时出错: {}".format(str(e)))
                    crawler_status["log"].append("服务器状态：爬虫遇到错误，请检查URL是否有效")
            else:
                crawler_status["log"].append("未提供有效的TapTap URL")
                crawler_status["log"].append("服务器状态：需要有效的游戏URL才能继续")
        
        elif crawler_type == "bilibili":
            # 导入并运行Bilibili爬虫
            crawler_status["log"].append("正在导入Bilibili爬虫模块...")
            crawler_status["log"].append("服务器状态：加载Bilibili爬虫依赖")
            crawler_status["progress"] = 10
            from bili_crawler import BiliCrawler
            
            # 初始化爬虫
            crawler_status["log"].append("正在初始化爬虫...")
            crawler_status["log"].append("服务器状态：创建Chrome浏览器实例")
            crawler_status["progress"] = 15
            crawler = BiliCrawler(use_headless=use_headless)
            
            # 更新日志
            crawler_status["log"].append("Bilibili爬虫已启动")
            crawler_status["log"].append("服务器状态：爬虫初始化完成")
            crawler_status["progress"] = 20
            
            if url:
                crawler_status["log"].append("正在爬取Bilibili评论: {}".format(url))
                crawler_status["log"].append("服务器状态：正在访问Bilibili视频页面")
                crawler_status["progress"] = 25
                try:
                    crawler_status["log"].append("开始提取评论数据...")
                    crawler_status["log"].append("服务器状态：页面解析中，提取视频评论数据")
                    crawler_status["progress"] = 30
                    crawler.extract_comments(url)
                    crawler_status["log"].append("数据提取完成")
                    crawler_status["log"].append("服务器状态：Bilibili评论数据已保存到output目录")
                    crawler_status["progress"] = 100
                except Exception as e:
                    crawler_status["log"].append("提取数据时出错: {}".format(str(e)))
                    crawler_status["log"].append("服务器状态：爬虫遇到错误，请检查URL是否有效")
            else:
                crawler_status["log"].append("未提供有效的Bilibili URL")
                crawler_status["log"].append("服务器状态：需要有效的视频URL才能继续")
        
        else:
            crawler_status["log"].append("未知的爬虫类型: {}".format(crawler_type))
            crawler_status["log"].append("服务器状态：不支持的爬虫类型")
            
    except Exception as e:
        crawler_status["log"].append("爬虫运行出错: {}".format(str(e)))
        crawler_status["log"].append("服务器状态：爬虫启动失败，请检查系统环境")
    finally:
        crawler_status["running"] = False
        crawler_status["log"].append("爬虫任务结束")

def main():
    """启动Flask服务器"""
    print(f"使用 {BROWSER_TYPE.upper()} 浏览器启动爬虫服务...")
    
    # 设置服务器
    host = '0.0.0.0'  # 监听所有网络接口
    port = 5000
    
    # 启动服务器
    app.run(host=host, port=port, debug=False, threaded=True)

# 修改export_file函数，使其支持直接导出CSV文件
@app.route('/export_file')
def export_file():
    """将文件下载到用户指定位置"""
    filename = request.args.get('filename')
    if not filename:
        return jsonify({"success": False, "message": "文件名不能为空"}), 400
    
    # 使用项目根目录下的output文件夹
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(project_root, 'output', filename)
    
    if not os.path.exists(file_path):
        return jsonify({"success": False, "message": f"文件 {filename} 不存在"}), 404
    
    # 确定MIME类型
    mime_type = 'text/csv' if filename.endswith('.csv') else 'application/json'
    
    return send_file(
        file_path,
        mimetype=mime_type,
        as_attachment=True,
        download_name=filename
    )

# 修改export_game_comments函数，使其支持CSV格式
@app.route('/export_game_comments')
def export_game_comments():
    """将游戏评论导出为单个文件"""
    app_id = request.args.get('app_id')
    if not app_id:
        return jsonify({"success": False, "message": "AppID不能为空"}), 400
    
    # 使用项目根目录下的output文件夹
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, 'output')
    
    # 查找CSV文件 - 修改文件名模式以支持时间戳
    csv_file_pattern = f"*_评论_{app_id}_*.csv"  # 添加通配符以匹配时间戳
    csv_files = glob.glob(os.path.join(output_dir, csv_file_pattern))
    
    if csv_files:
        # 如果找到了CSV文件，按修改时间排序并返回最新的文件
        csv_files.sort(key=os.path.getmtime, reverse=True)  # 按修改时间排序
        csv_file = csv_files[0]  # 获取最新的文件
        return send_file(
            csv_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=os.path.basename(csv_file)
        )
    
    # 如果没有找到CSV文件，尝试查找JSON文件并合并
    game_dir = os.path.join(output_dir, f'app_{app_id}')
    if not os.path.exists(game_dir):
        return jsonify({"success": False, "message": f"AppID为 {app_id} 的游戏评论数据不存在"}), 404
    
    # 获取所有JSON文件
    json_files = glob.glob(os.path.join(game_dir, '*.json'))
    if not json_files:
        return jsonify({"success": False, "message": "没有找到评论数据文件"}), 404
    
    # 合并所有评论
    all_reviews = []
    game_title = f"App {app_id}"
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                review = json.load(f)
                
                # 获取游戏标题
                if 'game_title' in review and game_title == f"App {app_id}":
                    game_title = review['game_title']
                
                all_reviews.append(review)
        except Exception as e:
            app.logger.error(f"读取文件 {file_path} 出错: {str(e)}")
    
    # 创建导出文件
    safe_title = re.sub(r'[\\/:*?"<>|]', '_', game_title)  # 将不安全字符替换为下划线
    timestamp = time.strftime("%Y%m%d_%H%M%S")  # 添加时间戳
    export_filename = f"{safe_title}_评论_{app_id}_{timestamp}.csv"
    
    # 创建临时导出文件，使用项目根目录下的output文件夹
    export_path = os.path.join(output_dir, export_filename)
    
    try:
        # 将JSON评论转换为CSV格式
        headers = [
            'app_id', 'game_title', 'review_id', 'user_name', 'steam_id', 
            'content', 'recommended', 'posted_date', 'hours_played', 
            'helpful_count', 'total_votes', 'comment_count', 'crawl_time'
        ]
        
        with open(export_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for review in all_reviews:
                row_data = {}
                for header in headers:
                    row_data[header] = review.get(header, '')
                writer.writerow(row_data)
        
        return send_file(
            export_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=export_filename
        )
    except Exception as e:
        app.logger.error(f"导出文件出错: {str(e)}")
        return jsonify({"success": False, "message": f"导出失败: {str(e)}"}), 500

if __name__ == "__main__":
    main() 