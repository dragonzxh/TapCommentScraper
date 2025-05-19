#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
爬虫Web服务器启动脚本 - 简化版本
只需要运行此脚本即可启动服务
支持Chrome和Edge浏览器
"""

import sys
import os
import argparse
from pathlib import Path
import webbrowser
import time

# 检查Python版本
if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 6):
    print("错误: 需要Python 3.6或更高版本")
    print("当前Python版本: {}.{}.{}".format(sys.version_info[0], sys.version_info[1], sys.version_info[2]))
    sys.exit(1)

# 解析命令行参数
parser = argparse.ArgumentParser(description="启动Steam爬虫Web服务器")
parser.add_argument("--browser", choices=["chrome", "edge"], default="chrome", help="选择浏览器类型 (chrome 或 edge)")
args = parser.parse_args()

# 设置环境变量，让应用知道使用哪种浏览器
os.environ["STEAM_CRAWLER_BROWSER"] = args.browser
print(f"使用 {args.browser.upper()} 浏览器")

# 创建必要的目录
for directory in ["cookies", "output", "logs"]:
    Path(directory).mkdir(exist_ok=True)
    print(f"确保目录存在: {directory}")

# 获取项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)

# 将src目录添加到模块搜索路径
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

# 设置明确的退出处理
def setup_exit_handler():
    import atexit
    
    def exit_handler():
        print("\n正在清理资源并退出...")
        # 移除浏览器启动标记
        browser_flag_file = os.path.join(project_root, '.browser_launched')
        if os.path.exists(browser_flag_file):
            try:
                os.remove(browser_flag_file)
                print(f"已删除浏览器标记文件: {browser_flag_file}")
            except Exception as e:
                print(f"删除浏览器标记文件时出错: {e}")
        
        print("清理完成，程序已退出")
    
    atexit.register(exit_handler)

# 注册退出处理函数
setup_exit_handler()

try:
    # 导入app模块中的main函数
    from crawler_web.app import main
    
    # 确保输出和cookies目录存在
    os.makedirs(os.path.join(project_root, "output"), exist_ok=True)
    os.makedirs(os.path.join(project_root, "cookies"), exist_ok=True)
    
    # 延迟打开浏览器，等待服务器启动
    def open_browser():
        try:
            # 等待服务器启动
            time.sleep(2)
            
            # 创建一个标志文件，表示浏览器已经打开
            browser_flag_file = os.path.join(project_root, ".browser_opened")
            
            # 如果标志文件不存在，打开浏览器
            if not os.path.exists(browser_flag_file):
                with open(browser_flag_file, "w") as f:
                    f.write("1")
                
                print("正在打开浏览器...")
                webbrowser.open("http://localhost:5000/steam")
            
            # 注册退出时的清理函数
            def cleanup():
                try:
                    if os.path.exists(browser_flag_file):
                        os.remove(browser_flag_file)
                except:
                    pass
        
            import atexit
            atexit.register(cleanup)
        except Exception as e:
            print(f"打开浏览器时出错: {e}")
            print("请手动访问: http://localhost:5000")
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # 启动服务
    main()
    
except ImportError as e:
    print("错误: 无法导入模块 - {}".format(e))
    print("\n尝试以下解决方案:")
    print("1. 确保已激活虚拟环境: source venv/bin/activate (Linux/Mac) 或 venv\\Scripts\\activate (Windows)")
    print("2. 尝试直接运行app.py: cd src/crawler_web && python app.py")
    print("3. 检查是否已安装所有依赖: pip install -r requirements.txt")
    print("4. 详细安装说明请参考README.md文件")
    sys.exit(1)
except Exception as e:
    print("启动服务器时出错: {}".format(e))
    print("请检查是否已安装所有依赖和系统要求")
    sys.exit(1)