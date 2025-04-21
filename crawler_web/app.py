#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
爬虫Web应用
"""

import os
import sys
import csv  # CSV模块用于读取CSV文件

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
    
    if crawler_type not in ['steam', 'taptap', 'bilibili']:
        return jsonify({"success": False, "message": "不支持的爬虫类型"})
    
    # 重置状态
    crawler_status = {
        "running": True,
        "progress": 0,
        "log": ["正在启动爬虫..."],
        "type": crawler_type,
        "url": url
    }
    
    # 启动爬虫线程
    thread = threading.Thread(target=run_crawler, args=(crawler_type, url))
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

def run_crawler(crawler_type, url=''):
    """运行爬虫的线程函数"""
    global crawler_status
    
    # 更新初始状态
    crawler_status["log"].append("正在准备{}爬虫...".format(crawler_type))
    crawler_status["progress"] = 5
    
    try:
        if crawler_type == "steam":
            # 导入并运行Steam爬虫
            crawler_status["log"].append("正在导入Steam爬虫模块...")
            crawler_status["progress"] = 10
            from steam_crawler import SteamCrawler
            
            # 初始化爬虫
            crawler_status["log"].append("正在初始化爬虫...")
            crawler_status["progress"] = 15
            crawler = SteamCrawler(use_headless=True)
            
            # 更新日志
            crawler_status["log"].append("Steam爬虫已启动")
            crawler_status["progress"] = 20
            
            if url:
                crawler_status["log"].append("正在爬取Steam评论: {}".format(url))
                crawler_status["progress"] = 25
                try:
                    crawler_status["log"].append("开始提取评论数据...")
                    crawler_status["progress"] = 30
                    crawler.extract_comments(url)
                    crawler_status["progress"] = 90
                    crawler_status["log"].append('评论爬取完成！可以在"查看评论"页面查看结果')
                except Exception as e:
                    crawler_status["log"].append("爬取过程中出错: {}".format(str(e)))
            else:
                crawler_status["log"].append("未提供URL，请在输入框中填写Steam游戏评论URL")
                
        elif crawler_type == "taptap":
            # 导入并运行TapTap爬虫
            crawler_status["log"].append("正在导入TapTap爬虫模块...")
            crawler_status["progress"] = 10
            from tap_crawler import TapTapCrawler
            
            # 初始化爬虫
            crawler_status["log"].append("正在初始化爬虫...")
            crawler_status["progress"] = 15
            crawler = TapTapCrawler(use_headless=True)
            
            # 更新日志
            crawler_status["log"].append("TapTap爬虫已启动")
            crawler_status["progress"] = 20
            
            if url:
                crawler_status["log"].append("正在爬取TapTap评论: {}".format(url))
                crawler_status["progress"] = 25
                try:
                    crawler_status["log"].append("开始提取评论数据...")
                    crawler_status["progress"] = 30
                    crawler.extract_comments(url)
                    crawler_status["progress"] = 90
                    crawler_status["log"].append('评论爬取完成！可以在"查看评论"页面查看结果')
                except Exception as e:
                    crawler_status["log"].append("爬取过程中出错: {}".format(str(e)))
            else:
                crawler_status["log"].append("未提供URL，请在输入框中填写TapTap游戏URL")
            
        elif crawler_type == "bilibili":
            # 导入并运行Bilibili爬虫
            crawler_status["log"].append("正在导入Bilibili爬虫模块...")
            crawler_status["progress"] = 10
            from bili_crawler import BiliBiliCrawler
            
            # 初始化爬虫
            crawler_status["log"].append("正在初始化爬虫...")
            crawler_status["progress"] = 15
            crawler = BiliBiliCrawler(use_headless=True)
            
            # 更新日志
            crawler_status["log"].append("Bilibili爬虫已启动")
            crawler_status["progress"] = 20
            
            if url:
                crawler_status["log"].append("正在爬取Bilibili评论: {}".format(url))
                crawler_status["progress"] = 25
                try:
                    crawler_status["log"].append("开始提取评论数据...")
                    crawler_status["progress"] = 30
                    crawler.extract_comments(url)
                    crawler_status["progress"] = 90
                    crawler_status["log"].append('评论爬取完成！可以在"查看评论"页面查看结果')
                except Exception as e:
                    crawler_status["log"].append("爬取过程中出错: {}".format(str(e)))
            else:
                crawler_status["log"].append("未提供URL，请在输入框中填写Bilibili视频URL")
        
        # 更新进度到100%
        crawler_status["progress"] = 100
        crawler_status["log"].append("处理完成")
    
    except Exception as e:
        crawler_status["log"].append("错误：{}".format(str(e)))
    
    finally:
        crawler_status["running"] = False

def main():
    """主函数"""
    # 确保目录存在
    Path("output").mkdir(exist_ok=True)
    Path("cookies").mkdir(exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5002)

if __name__ == "__main__":
    main() 