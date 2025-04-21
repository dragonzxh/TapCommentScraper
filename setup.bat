@echo off
echo ===============================================
echo 游戏评论爬虫与分析工具 - 安装脚本 (Windows)
echo ===============================================
echo.

REM 检查Python
echo 正在检查Python环境...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python。请先安装Python 3.8以上版本。
    exit /b 1
)

REM 检查Python版本
for /f "tokens=*" %%a in ('python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))"') do set PY_VERSION=%%a
echo Python版本: %PY_VERSION%

REM 创建虚拟环境
echo.
echo 创建Python虚拟环境...
if exist venv (
    echo 虚拟环境已存在，跳过创建步骤。
) else (
    python -m venv venv
    echo 已创建虚拟环境: venv
)

REM 激活虚拟环境
echo.
echo 正在激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo.
echo 正在安装依赖...
echo 注意: 使用更轻量级的依赖配置，使用内置csv模块替代pandas
python -m pip install --upgrade pip
pip install -r requirements.txt

REM 创建必要的目录
echo.
echo 创建工作目录...
if not exist output mkdir output
if not exist cookies mkdir cookies
if not exist logs mkdir logs

REM 检查Chrome浏览器
echo.
echo 检查Chrome浏览器...
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo 已检测到Chrome浏览器。
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    echo 已检测到Chrome浏览器。
) else (
    echo 警告: 未检测到Chrome浏览器。爬虫功能需要Chrome浏览器才能正常运行。
    echo 请安装Chrome浏览器: https://www.google.com/chrome/
)

REM 安装完成
echo.
echo ===============================================
echo 安装完成!
echo ===============================================
echo.
echo 使用以下命令启动Web界面:
echo ^> venv\Scripts\activate
echo ^> python crawler_web_start.py
echo.
echo 或运行爬虫:
echo ^> python steam_crawler.py
echo.
echo 访问Web界面: http://localhost:5000
echo ===============================================

REM 暂停以便用户查看信息
pause 