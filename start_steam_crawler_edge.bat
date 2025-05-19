@echo off
:: 设置UTF-8编码
chcp 65001 > nul
echo Steam评论爬虫 - Edge浏览器版本
echo ==============================
echo.

:: 获取当前目录
set "DIR=%~dp0"
cd /d "%DIR%"

:: 创建日志目录
if not exist "logs" mkdir logs

:: 创建调试日志文件
set "DEBUG_LOG=%DIR%logs\edge_crawler_debug_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
set "DEBUG_LOG=%DEBUG_LOG: =0%"

:: 开始记录调试信息
echo [%date% %time%] 开始执行批处理文件 > "%DEBUG_LOG%"
echo [%date% %time%] 当前目录: %DIR% >> "%DEBUG_LOG%"

:: 检查Python安装
echo 检查Python安装...
echo [%date% %time%] 检查Python安装... >> "%DEBUG_LOG%"
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.8或更高版本
    echo [%date% %time%] [错误] 未找到Python >> "%DEBUG_LOG%"
    pause
    exit /b 1
)

:: 输出Python版本信息
echo [%date% %time%] Python版本信息: >> "%DEBUG_LOG%"
python --version >> "%DEBUG_LOG%" 2>&1

:: 检查虚拟环境
echo 检查虚拟环境...
echo [%date% %time%] 检查虚拟环境... >> "%DEBUG_LOG%"
if not exist "venv" (
    echo 创建虚拟环境...
    echo [%date% %time%] 创建虚拟环境... >> "%DEBUG_LOG%"
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [错误] 创建虚拟环境失败
        echo [%date% %time%] [错误] 创建虚拟环境失败，错误码: %errorlevel% >> "%DEBUG_LOG%"
        pause
        exit /b 1
    )
    
    call venv\Scripts\activate.bat
    
    echo 安装依赖项...
    echo [%date% %time%] 安装依赖项... >> "%DEBUG_LOG%"
    pip install --upgrade pip >> "%DEBUG_LOG%" 2>&1
    pip install flask selenium beautifulsoup4 requests webdriver-manager >> "%DEBUG_LOG%" 2>&1
    if %errorlevel% neq 0 (
        echo [错误] 安装依赖项失败
        echo [%date% %time%] [错误] 安装依赖项失败，错误码: %errorlevel% >> "%DEBUG_LOG%"
        pause
        exit /b 1
    )
) else (
    echo 检测到已有虚拟环境，激活中...
    echo [%date% %time%] 激活已有虚拟环境... >> "%DEBUG_LOG%"
    call venv\Scripts\activate.bat
)

:: 确保输出目录存在
echo 检查输出目录...
echo [%date% %time%] 检查输出目录... >> "%DEBUG_LOG%"
if not exist "output" mkdir output
if not exist "cookies" mkdir cookies

:: 检查Edge浏览器安装
echo 检查Microsoft Edge浏览器...
echo [%date% %time%] 检查Microsoft Edge浏览器... >> "%DEBUG_LOG%"
reg query "HKEY_CURRENT_USER\Software\Microsoft\Edge" >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 未检测到Microsoft Edge浏览器
    echo [%date% %time%] [警告] 未检测到Microsoft Edge浏览器 >> "%DEBUG_LOG%"
    set /p choice="是否继续? [y/n]: "
    echo [%date% %time%] 用户选择: %choice% >> "%DEBUG_LOG%"
    if /i "%choice%" neq "y" (
        echo 退出程序
        echo [%date% %time%] 用户选择退出程序 >> "%DEBUG_LOG%"
        pause
        exit /b 1
    )
) else (
    echo Microsoft Edge浏览器已安装
    echo [%date% %time%] Microsoft Edge浏览器已安装 >> "%DEBUG_LOG%"
    
    :: 获取Edge版本信息
    for /f "tokens=2 delims==" %%I in ('wmic datafile where name^="C:\\Program Files ^(x86^)\\Microsoft\\Edge\\Application\\msedge.exe" get Version /value 2^>nul') do set "EDGE_VERSION=%%I"
    if not defined EDGE_VERSION (
        for /f "tokens=2 delims==" %%I in ('wmic datafile where name^="C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe" get Version /value 2^>nul') do set "EDGE_VERSION=%%I"
    )
    
    if defined EDGE_VERSION (
        echo Edge版本: %EDGE_VERSION%
        echo [%date% %time%] Edge版本: %EDGE_VERSION% >> "%DEBUG_LOG%"
    ) else (
        echo 无法获取Edge版本信息
        echo [%date% %time%] 无法获取Edge版本信息 >> "%DEBUG_LOG%"
    )
)

:: 检查webdriver-manager安装
echo 检查webdriver-manager...
echo [%date% %time%] 检查webdriver-manager... >> "%DEBUG_LOG%"
pip show webdriver-manager >nul 2>&1
if %errorlevel% neq 0 (
    echo 安装webdriver-manager...
    echo [%date% %time%] 安装webdriver-manager... >> "%DEBUG_LOG%"
    pip install webdriver-manager >> "%DEBUG_LOG%" 2>&1
    if %errorlevel% neq 0 (
        echo [错误] 安装webdriver-manager失败
        echo [%date% %time%] [错误] 安装webdriver-manager失败，错误码: %errorlevel% >> "%DEBUG_LOG%"
        pause
        exit /b 1
    )
) else (
    echo webdriver-manager已安装
    echo [%date% %time%] webdriver-manager已安装 >> "%DEBUG_LOG%"
    
    :: 获取webdriver-manager版本
    for /f "tokens=2" %%a in ('pip show webdriver-manager ^| findstr Version') do set WDM_VERSION=%%a
    echo webdriver-manager版本: %WDM_VERSION%
    echo [%date% %time%] webdriver-manager版本: %WDM_VERSION% >> "%DEBUG_LOG%"
    
    :: 尝试更新webdriver-manager
    echo 更新webdriver-manager...
    echo [%date% %time%] 更新webdriver-manager... >> "%DEBUG_LOG%"
    pip install --upgrade webdriver-manager >> "%DEBUG_LOG%" 2>&1
)

:: 设置环境变量跳过登录检查
set SKIP_LOGIN_CHECK=1
echo [%date% %time%] 设置环境变量SKIP_LOGIN_CHECK=1 >> "%DEBUG_LOG%"

:: 启动爬虫服务
echo 启动爬虫服务...
echo [%date% %time%] 启动爬虫服务... >> "%DEBUG_LOG%"
echo 请在浏览器中操作，程序运行日志将显示在此窗口
echo 按Ctrl+C可停止服务

:: 生成时间戳（格式：YYYYMMDD_HHMMSS）
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set d=%%a%%b%%c
for /f "tokens=1-3 delims=:., " %%a in ('echo %time%') do set t=%%a%%b%%c
set TIMESTAMP=%d%_%t%
set TIMESTAMP=%TIMESTAMP: =0%

:: 启动Flask服务器并传递Edge浏览器参数
echo [%date% %time%] 执行命令: python src/crawler_web_start.py --browser edge --timestamp %TIMESTAMP% >> "%DEBUG_LOG%"
start /b python src/crawler_web_start.py --browser edge --timestamp %TIMESTAMP% >> "%DEBUG_LOG%" 2>&1

:: 等待服务器启动
echo 等待服务器启动...
echo [%date% %time%] 等待服务器启动... >> "%DEBUG_LOG%"
timeout /t 3 > nul

:: 打开网页
echo 打开浏览器...
echo [%date% %time%] 打开浏览器... >> "%DEBUG_LOG%"
start http://localhost:5000/steam

echo 服务已启动，请在浏览器中操作
echo 要停止服务，请按任意键...
echo [%date% %time%] 等待用户停止服务... >> "%DEBUG_LOG%"
pause > nul

:: 关闭Python进程
echo 正在关闭服务...
echo [%date% %time%] 正在关闭服务... >> "%DEBUG_LOG%"
taskkill /f /im python.exe
echo [%date% %time%] 批处理文件执行完毕 >> "%DEBUG_LOG%"
echo 服务已关闭
pause 