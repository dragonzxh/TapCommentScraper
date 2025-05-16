@echo off
title Steam评论爬虫启动工具
echo ======================================================
echo           Steam评论爬虫启动工具 - Windows版
echo ======================================================
echo.

REM 设置UTF-8编码
chcp 65001 >nul
echo 已设置UTF-8编码

REM 设置工作目录为脚本所在目录
cd /d "%~dp0"
echo 已切换到程序目录: %CD%

REM 检查Python是否存在
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python。请安装Python 3.8或更高版本。
    echo 您可以从以下地址下载安装: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查Python版本
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
echo 已检测到Python版本: %PYTHON_VERSION%

REM 创建必要的目录
if not exist "cookies" mkdir cookies
if not exist "output" mkdir output
if not exist "logs" mkdir logs
echo 已确保必要目录存在

REM 判断是否有虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo 检测到虚拟环境，正在激活...
    call venv\Scripts\activate.bat
) else (
    echo 未检测到虚拟环境，尝试创建...
    python -m venv venv
    if %ERRORLEVEL% EQU 0 (
        echo 虚拟环境创建成功，正在激活...
        call venv\Scripts\activate.bat
    ) else (
        echo 警告: 创建虚拟环境失败，将使用系统Python继续
    )
)

REM 安装依赖（如果需要）
if exist "requirements.txt" (
    echo 检查并安装依赖...
    pip install -r requirements.txt >logs\pip_install.log 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo 警告: 安装依赖时出现错误，请查看 logs\pip_install.log
    ) else (
        echo 依赖检查完成
    )
)

echo.
echo ======================================================
echo 启动爬虫Web服务...
echo ======================================================
echo.

REM 启动爬虫服务
python crawler_web_start.py

REM 如果程序异常退出，保持窗口打开
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 程序异常退出，错误代码: %ERRORLEVEL%
    echo 请检查上方错误信息
    pause
)

REM 如果在虚拟环境中，退出虚拟环境
if defined VIRTUAL_ENV (
    deactivate
) 