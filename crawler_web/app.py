#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
爬虫Web应用
"""

import os
import sys
import csv  # CSV模块用于读取CSV文件
import subprocess  # 用于打开文件夹

# 添加项目根目录到系统路径，确保能够导入自定义模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, redirect, url_for
import threading
import time
import json
from pathlib import Path
import glob

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
    "type": None
}

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """获取爬虫状态"""
    return jsonify(crawler_status)

@app.route('/api/start', methods=['POST'])
def start_crawler():
    """启动爬虫"""
    global crawler_status
    
    if crawler_status["running"]:
        return jsonify({"success": False, "message": "爬虫已在运行中"})
    
    data = request.get_json()
    crawler_type = data.get('type')
    url = data.get('url', '')
    
    # 验证爬虫类型
    if crawler_type not in ['steam', 'taptap', 'bilibili']:
        return jsonify({"success": False, "message": "不支持的爬虫类型"})
    
    # 验证URL格式
    if not url:
        return jsonify({"success": False, "message": "请输入有效的URL或ID"})
    
    # 格式化URL (如果用户只输入了ID)
    if crawler_type == 'steam' and not url.startswith('http'):
        # 如果只输入了数字ID，添加完整URL前缀
        if url.isdigit():
            url = f"https://steamcommunity.com/app/{url}/reviews/"
    
    elif crawler_type == 'taptap' and not url.startswith('http'):
        # 如果只输入了数字ID，添加完整URL前缀
        if url.isdigit():
            url = f"https://www.taptap.com/app/{url}"
    
    elif crawler_type == 'bilibili' and not url.startswith('http'):
        # 如果只输入了BV号，添加完整URL前缀
        if url.startswith('BV') or url.isdigit():
            url = f"https://www.bilibili.com/video/{url}"
    
    # 记录格式化后的URL
    formatted_url = url
    
    # 重置状态
    crawler_status = {
        "running": True,
        "progress": 0,
        "log": ["正在启动爬虫..."],
        "type": crawler_type,
        "url": formatted_url
    }
    
    # 启动爬虫线程
    thread = threading.Thread(target=run_crawler, args=(crawler_type, formatted_url))
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True})

# 添加查看评论数据的路由
@app.route('/comments')
def list_comments():
    """查看已爬取的评论列表"""
    # 获取output目录下的所有CSV文件
    csv_files = glob.glob(os.path.join('output', '*.csv'))
    csv_files.sort(key=os.path.getmtime, reverse=True)  # 按修改时间排序
    
    files_data = []
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) / 1024  # KB
        modified_time = time.ctime(os.path.getmtime(file_path))
        
        files_data.append({
            'path': file_path,
            'filename': filename,
            'size': "{:.2f} KB".format(file_size),
            'modified': modified_time
        })
    
    return render_template('comments.html', files=files_data)

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

def run_crawler(crawler_type, url=''):
    """运行爬虫的线程函数"""
    global crawler_status
    
    # 更新初始状态
    crawler_status["log"].append("正在准备{}爬虫...".format(crawler_type))
    crawler_status["log"].append("服务器状态：初始化爬虫环境")
    crawler_status["progress"] = 5
    
    try:
        if crawler_type == "steam":
            # 导入并运行Steam爬虫
            crawler_status["log"].append("正在导入Steam爬虫模块...")
            crawler_status["log"].append("服务器状态：加载Steam爬虫依赖")
            crawler_status["progress"] = 10
            from steam_crawler import SteamCrawler
            
            # 初始化爬虫
            crawler_status["log"].append("正在初始化爬虫...")
            crawler_status["log"].append("服务器状态：创建Chrome浏览器实例")
            crawler_status["progress"] = 15
            crawler = SteamCrawler(use_headless=True)
            
            # 更新日志
            crawler_status["log"].append("Steam爬虫已启动")
            crawler_status["log"].append("服务器状态：爬虫初始化完成")
            crawler_status["progress"] = 20
            
            if url:
                crawler_status["log"].append("正在爬取Steam评论: {}".format(url))
                crawler_status["log"].append("服务器状态：正在访问目标网页")
                crawler_status["progress"] = 25
                try:
                    crawler_status["log"].append("开始提取评论数据...")
                    crawler_status["log"].append("服务器状态：页面解析中，正在提取评论数据")
                    crawler_status["progress"] = 30
                    crawler.extract_comments(url)
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
            crawler = TapCrawler(use_headless=True)
            
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
            crawler = BiliCrawler(use_headless=True)
            
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
    """启动Flask应用"""
    # 确保目录存在
    Path("output").mkdir(exist_ok=True)
    Path("cookies").mkdir(exist_ok=True)
    
    # 修改为localhost，更好地支持Windows环境
    app.run(debug=True, host='localhost', port=5000)

if __name__ == "__main__":
    main() 