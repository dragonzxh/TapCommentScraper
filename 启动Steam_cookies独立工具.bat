@echo off
chcp 65001 > nul
title Steam Cookies获取工具

echo ===============================================
echo Steam Cookies获取工具启动中...
echo ===============================================

:: 检查Python是否安装
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请安装Python 3.8或更高版本
    echo 您可以从 https://www.python.org/downloads/ 下载安装
    pause
    exit /b 1
)

:: 设置项目路径
set PROJECT_PATH=%~dp0

:: 切换到项目目录
cd /d "%PROJECT_PATH%"

:: 检查并创建虚拟环境
if not exist venv (
    echo 初次运行，创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
)

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 检查并安装依赖
pip show selenium >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装必要的依赖...
    pip install selenium webdriver-manager
)

:: 检查并创建必要的目录
if not exist cookies mkdir cookies
if not exist output mkdir output
if not exist logs mkdir logs

:: 直接启动Steam Cookies Helper
echo 正在启动Steam Cookies Helper工具...
python steam_cookies_helper.py

:: 如果发生错误，保持窗口打开
if %errorlevel% neq 0 (
    echo.
    echo [错误] 程序执行异常，请查看上方错误信息
    pause
    exit /b 1
)

:: 退出虚拟环境
call venv\Scripts\deactivate.bat

echo 程序已完成执行，可以关闭窗口
pause
exit /b 0 