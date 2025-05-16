@echo off
title Steam评论爬虫工具 - 一键启动

echo =========================================
echo      Steam评论爬虫工具 - 一键启动
echo =========================================
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 检查Python是否已安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未检测到Python，请先安装Python 3.8或更高版本
    echo 您可以从 https://www.python.org/downloads/ 下载并安装
    echo.
    echo 按任意键退出...
    pause >nul
    exit /b 1
)

:: 检查虚拟环境是否存在，如果不存在则创建
if not exist venv (
    echo === 首次运行安装 ===
    echo 创建虚拟环境...
    python -m venv venv
    
    if not exist venv (
        echo 错误: 虚拟环境创建失败
        echo 按任意键退出...
        pause >nul
        exit /b 1
    )
    
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
    
    echo 安装依赖包...
    pip install --upgrade pip
    pip install flask selenium beautifulsoup4 requests webdriver-manager
) else (
    echo 检测到已存在的虚拟环境，正在激活...
    call venv\Scripts\activate.bat
)

:: 确保output和cookies目录存在
if not exist output mkdir output
if not exist cookies mkdir cookies

:: 检查Chrome浏览器是否安装
where chrome >nul 2>&1
if %errorlevel% neq 0 (
    echo 警告: 未检测到Chrome浏览器，爬虫可能无法正常工作
    echo 请安装Chrome浏览器后再运行此脚本
    echo.
    set /p choice=是否继续? [y/n]: 
    if /i not "%choice%"=="y" (
        echo 已取消操作，按任意键退出...
        pause >nul
        exit /b 1
    )
)

:: 设置环境变量，告诉程序不要检查登录状态
set SKIP_LOGIN_CHECK=1

:: 启动Flask服务器
echo 启动网页服务器...
start /B python -m crawler_web.app

:: 等待服务器启动
echo 等待服务器启动...
timeout /t 3 /nobreak >nul

:: 打开浏览器访问Steam独立页面
echo 正在打开网页...
start http://localhost:5000/steam

echo.
echo Steam评论爬虫工具已启动！
echo 请在浏览器中操作。完成后关闭此窗口即可停止服务器。
echo.

echo 按任意键停止服务器...
pause >nul

echo 正在停止服务器...
taskkill /F /IM python.exe >nul 2>&1
echo 服务器已停止。

timeout /t 3 >nul 