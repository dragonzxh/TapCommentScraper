#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
爬虫Web服务器启动脚本 - 简化版本
只需要运行此脚本即可启动服务
"""

import sys
import os
from pathlib import Path
import webbrowser
import time

# 检查Python版本
if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 6):
    print("错误: 需要Python 3.6或更高版本")
    print("当前Python版本: {}.{}.{}".format(sys.version_info[0], sys.version_info[1], sys.version_info[2]))
    sys.exit(1)

# 创建必要的目录
for directory in ["cookies", "output", "logs"]:
    Path(directory).mkdir(exist_ok=True)
    print(f"确保目录存在: {directory}")

# 将当前目录添加到模块搜索路径
sys.path.insert(0, os.path.abspath('.'))

# 将crawler_web目录添加到模块搜索路径
crawler_web_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crawler_web')
sys.path.insert(0, crawler_web_path)

# 设置明确的退出处理
def setup_exit_handler():
    import atexit
    
    def exit_handler():
        print("\n正在清理资源并退出...")
        # 移除浏览器启动标记
        browser_flag_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.browser_launched')
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
    # 直接导入app模块中的main函数
    from crawler_web.app import main
    
    print("\n服务器准备就绪，正在启动...")
    print("请稍候，浏览器将自动打开...")
    
    # 延迟一秒，准备启动
    time.sleep(1)
    
    # 在另一个线程启动网页
    def open_browser():
        # 创建一个标记文件，防止浏览器被多次打开
        browser_flag_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.browser_launched')
        
        # 检查标记文件是否存在，如果存在则不再打开浏览器
        if os.path.exists(browser_flag_file):
            return
        
        time.sleep(3)  # 等待服务器启动
        
        try:
            # 创建标记文件
            with open(browser_flag_file, 'w') as f:
                f.write(str(time.time()))
            
            # 打开浏览器
            webbrowser.open('http://localhost:5000')
            print("已自动打开浏览器，如未显示请手动访问: http://localhost:5000")
            
            # 设置标记文件在程序退出时自动删除
            def cleanup():
                if os.path.exists(browser_flag_file):
                    try:
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
    print("2. 尝试直接运行app.py: cd crawler_web && python app.py")
    print("3. 检查是否已安装所有依赖: pip install -r requirements.txt")
    print("4. 详细安装说明请参考README.md文件")
    sys.exit(1)
except Exception as e:
    print("启动服务器时出错: {}".format(e))
    print("请检查是否已安装所有依赖和系统要求")
    sys.exit(1)