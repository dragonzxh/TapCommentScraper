@echo off
echo ===============================================
echo 游戏评论爬虫启动脚本 (Windows)
echo ===============================================
echo.

REM 检查Python是否已安装
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python。请先安装Python 3.8以上版本。
    pause
    exit /b 1
)

REM 检查虚拟环境是否存在
if not exist venv (
    echo 未找到虚拟环境，请先运行setup.bat安装
    pause
    exit /b 1
)

REM 激活虚拟环境
call venv\Scripts\activate

echo 请选择要运行的爬虫:
echo 1. Steam游戏评论爬虫
echo 2. TapTap游戏评论爬虫
echo 3. Bilibili视频评论爬虫
echo 4. 所有爬虫
echo 5. 启动Web界面
echo 6. 退出

choice /c 123456 /n /m "请输入选项 [1-6]: "

if errorlevel 6 goto :exit
if errorlevel 5 goto :web
if errorlevel 4 goto :all
if errorlevel 3 goto :bilibili
if errorlevel 2 goto :taptap
if errorlevel 1 goto :steam

:steam
echo.
echo 正在启动Steam爬虫...
python run_crawlers.py --steam
goto :end

:taptap
echo.
echo 正在启动TapTap爬虫...
python run_crawlers.py --taptap
goto :end

:bilibili
echo.
echo 正在启动Bilibili爬虫...
python run_crawlers.py --bilibili
goto :end

:all
echo.
echo 正在启动所有爬虫...
python run_crawlers.py --all
goto :end

:web
echo.
echo 正在启动Web界面...
echo 请在浏览器中访问: http://localhost:5000
python crawler_web_start.py
goto :end

:exit
echo.
echo 退出程序
goto :eof

:end
echo.
echo 任务已完成，按任意键退出...
pause > nul 