#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Windows编码修复工具

此脚本用于解决Windows环境下运行爬虫时可能出现的中文乱码问题。
它会修改相关Python文件中的编码设置，确保在Windows环境中正确处理中文字符。
"""

import os
import sys
import re
import glob
import fileinput
import locale
import ctypes

def get_system_encoding():
    """获取系统编码"""
    return locale.getpreferredencoding()

def is_admin():
    """检查是否有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def fix_file_encoding(file_path):
    """修复文件中的编码设置"""
    print(f"正在修复文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换CSV文件的编码设置
    if 'newline=\'\'' in content and 'encoding=\'utf-8\'' in content:
        content = content.replace('encoding=\'utf-8\'', 'encoding=\'utf-8-sig\'')
    
    # 替换文件打开时的编码设置
    content = re.sub(r'open\(([^,]+), \'w\', encoding=\'utf-8\'\)', 
                     r'open(\1, \'w\', encoding=\'utf-8-sig\')', 
                     content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ 文件修复完成: {file_path}")

def add_system_encoding_init():
    """在爬虫初始化文件中添加系统编码设置"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    init_file = os.path.join(base_path, 'crawler_web', '__init__.py')
    
    if os.path.exists(init_file):
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'sys.stdout.reconfigure' not in content:
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(content + """
# Windows中文环境编码修复
import sys
import locale

# 设置控制台输出编码
try:
    if sys.platform.startswith('win'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    # Python 3.6及以下版本不支持reconfigure方法
    pass
""")
            print(f"✓ 已添加系统编码设置到: {init_file}")

def fix_crawler_base():
    """修复crawler_base.py中的编码问题"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    base_file = os.path.join(base_path, 'crawler_base.py')
    
    if os.path.exists(base_file):
        fix_file_encoding(base_file)

def fix_crawler_files():
    """修复所有爬虫文件的编码问题"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    crawler_files = [
        os.path.join(base_path, 'steam_crawler.py'),
        os.path.join(base_path, 'tap_crawler.py'),
        os.path.join(base_path, 'bili_crawler.py'),
        os.path.join(base_path, 'run_crawlers.py')
    ]
    
    for file in crawler_files:
        if os.path.exists(file):
            fix_file_encoding(file)

def create_batch_file():
    """创建一个批处理文件，在管理员模式下运行Python脚本"""
    batch_content = """@echo off
chcp 65001 >nul
echo Windows中文编码修复工具
echo =================================
echo 此工具将修复评论爬虫在Windows环境下可能出现的中文乱码问题。
echo.

:: 检查是否以管理员身份运行
net session >nul 2>&1
if %errorlevel% == 0 (
    echo 正在以管理员身份运行...
) else (
    echo 需要管理员权限才能修复系统编码问题。
    echo 请右键点击此文件，选择"以管理员身份运行"。
    echo.
    pause
    exit /b
)

:: 运行Python修复脚本
echo 正在修复编码问题...
python windows_encoding_fix.py

echo.
echo 修复完成！现在您可以正常运行爬虫而不会出现中文乱码。
echo.
pause
"""
    
    with open('修复Windows中文乱码.bat', 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    print(f"✓ 已创建批处理文件: 修复Windows中文乱码.bat")

def add_chcp_to_bat_files():
    """向所有.bat文件添加中文编码支持"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    bat_files = glob.glob(os.path.join(base_path, '*.bat'))
    
    for bat_file in bat_files:
        with open(bat_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'chcp 65001' not in content and '@echo off' in content:
            content = content.replace('@echo off', '@echo off\nchcp 65001 >nul')
            
            with open(bat_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✓ 已添加中文编码支持到: {bat_file}")

def add_readme():
    """添加README文件解释乱码问题的解决方法"""
    readme_content = """# Windows中文乱码修复指南

## 问题描述

在Windows系统中运行评论爬虫时，可能会遇到中文显示乱码的问题。这主要是由于Windows默认使用的编码（通常是GBK或GB2312）与Python默认的UTF-8编码不匹配导致的。

## 解决方法

### 方法一：使用自动修复工具（推荐）

1. 双击运行 `修复Windows中文乱码.bat` 文件
2. 当提示需要管理员权限时，请右键点击此文件并选择"以管理员身份运行"
3. 等待修复完成
4. 重新运行爬虫程序

### 方法二：手动修复

如果自动修复工具不起作用，您可以尝试以下手动修复方法：

1. 在命令提示符(CMD)中运行爬虫前，执行以下命令：
   ```
   chcp 65001
   ```

2. 修改Python脚本中的文件编码：
   - 将 `encoding='utf-8'` 改为 `encoding='utf-8-sig'`，特别是在写入CSV文件时
   - 在脚本开头添加以下代码：
     ```python
     import sys
     sys.stdout.reconfigure(encoding='utf-8')
     ```

3. 使用专门的中文环境启动脚本：
   - 双击运行 `启动评论爬虫_中文环境.bat`

## 原理说明

- `chcp 65001` 命令将Windows命令提示符的代码页设置为UTF-8
- `utf-8-sig` 编码在文件开头添加BOM(字节顺序标记)，使Windows能够正确识别UTF-8编码的文件
- `sys.stdout.reconfigure` 重新配置Python的标准输出流，确保中文字符能够正确显示

## 注意事项

- 此修复仅适用于Windows系统，macOS和Linux系统一般不需要此修复
- 如果您使用的是Python 3.6或更早版本，某些修复方法可能不适用
- 建议永久设置Windows的默认编码为UTF-8，可在区域设置中完成
"""
    
    with open('Windows中文乱码修复指南.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✓ 已创建说明文档: Windows中文乱码修复指南.md")

def create_chinese_env_bat():
    """创建专门的中文环境启动脚本"""
    bat_content = """@echo off
chcp 65001 >nul
:: 评论爬虫Web应用快速启动器 (Windows中文环境专用)
:: 此文件解决中文显示乱码问题

echo =================================================
echo       评论爬虫Web应用 - 快速启动器 (中文环境)
echo =================================================
echo 正在启动服务...
echo.

:: 设置环境变量强制使用UTF-8
set PYTHONIOENCODING=utf-8

:: 项目目录路径
set PROJECT_PATH=%~dp0

:: 显示当前路径
echo ✓ 当前工作目录: %PROJECT_PATH%

:: 切换到项目目录
cd /d "%PROJECT_PATH%"

:: 检查虚拟环境是否存在
if exist "venv\\Scripts\\activate.bat" (
    :: 激活虚拟环境
    call venv\\Scripts\\activate.bat
    echo ✓ 已激活Python虚拟环境
) else (
    echo 错误: 虚拟环境不存在!
    echo 请先运行 setup.bat 脚本安装依赖
    echo.
    echo 按任意键退出...
    pause >nul
    exit /b 1
)

:: 检查启动脚本是否存在
if exist "crawler_web_start.py" (
    :: 启动Web应用
    echo ✓ 正在启动Web服务器...
    echo ✓ 服务启动后，请在浏览器中访问: http://localhost:5000
    echo.
    :: 使用-u参数强制Python的stdin/stdout/stderr以unbuffered模式运行，有助于解决编码问题
    python -u crawler_web_start.py
) else (
    echo 错误: 找不到启动脚本 crawler_web_start.py!
    echo 请确保项目文件完整
    echo.
    echo 按任意键退出...
    pause >nul
    exit /b 1
)

:: 脚本结束
echo.
echo Web服务器已关闭
echo 按任意键退出...
pause >nul
"""
    
    with open('启动评论爬虫_中文环境.bat', 'w', encoding='utf-8') as f:
        f.write(bat_content)
    
    print(f"✓ 已创建中文环境启动脚本: 启动评论爬虫_中文环境.bat")

def main():
    """主函数"""
    print("Windows中文编码修复工具")
    print("===================================")
    print("此工具将修复Windows环境下可能出现的中文乱码问题。")
    print("")
    
    # 系统检查
    if not sys.platform.startswith('win'):
        print("此工具仅适用于Windows系统。")
        if sys.platform.startswith('darwin'):
            print("您使用的是macOS系统，一般不会出现中文乱码问题。")
        elif sys.platform.startswith('linux'):
            print("您使用的是Linux系统，一般不会出现中文乱码问题。")
        return
    
    # 显示当前系统编码
    print(f"当前系统编码: {get_system_encoding()}")
    print(f"Python标准输出编码: {sys.stdout.encoding}")
    print("")
    
    # 创建批处理文件供用户以管理员身份运行
    create_batch_file()
    
    # 如果不是管理员权限，提示用户
    if not is_admin():
        print("注意: 某些修复需要管理员权限。")
        print("请右键点击'修复Windows中文乱码.bat'文件，选择'以管理员身份运行'。")
        print("")
    
    # 修复编码问题
    fix_crawler_base()
    fix_crawler_files()
    add_system_encoding_init()
    add_chcp_to_bat_files()
    
    # 创建中文环境专用启动脚本
    create_chinese_env_bat()
    
    # 创建说明文档
    add_readme()
    
    print("")
    print("===================================")
    print("修复完成！现在您可以正常运行爬虫而不会出现中文乱码。")
    print("如果仍然遇到问题，请参阅 'Windows中文乱码修复指南.md' 文档。")

if __name__ == "__main__":
    main() 