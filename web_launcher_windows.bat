@echo off
chcp 65001 >nul
:: 评论爬虫Web应用通用启动器 (Windows)
:: 此脚本可以从命令行中运行，用于启动Web应用

echo =================================================
echo       评论爬虫Web应用 - 通用启动器 (Windows)
echo =================================================
echo 正在初始化...
echo.

:: 获取脚本所在目录
set SCRIPT_DIR=%~dp0
echo ✓ 脚本所在目录: %SCRIPT_DIR%

:: 检测系统语言环境
for /f "tokens=3 delims= " %%i in ('reg query "HKCU\Control Panel\International" /v "LocaleName" ^| find "LocaleName"') do set LANG=%%i
echo ✓ 当前系统语言: %LANG%

:: 如果是中文环境，设置PYTHONIOENCODING环境变量
if "%LANG:~0,2%"=="zh" (
    echo ✓ 检测到中文环境，应用特殊编码设置
    set PYTHONIOENCODING=utf-8
)

:: 切换到项目目录
cd /d "%SCRIPT_DIR%"
echo ✓ 当前工作目录: %cd%

:: 检查Python是否安装
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python。请先安装Python 3.8以上版本。
    echo.
    echo 您可以从以下网址下载Python: https://www.python.org/downloads/
    echo 安装时请勾选"Add Python to PATH"选项
    echo.
    echo 按任意键退出...
    pause >nul
    exit /b 1
)

:: 检查Python版本
for /f "tokens=*" %%a in ('python -c "import sys; print(sys.version_info[0]*10+sys.version_info[1])"') do set PY_VER=%%a
if %PY_VER% LSS 38 (
    echo 错误: Python版本过低，需要Python 3.8或更高版本。
    echo.
    echo 按任意键退出...
    pause >nul
    exit /b 1
)
echo ✓ Python版本检查通过

:: 检查虚拟环境是否存在
if exist "venv\Scripts\activate.bat" (
    :: 激活虚拟环境
    call venv\Scripts\activate.bat
    echo ✓ 已激活Python虚拟环境
) else (
    echo 未找到虚拟环境，正在为您自动安装...
    echo 首次运行需要一些时间，请耐心等待...
    echo.
    
    :: 执行setup
    if exist "setup.bat" (
        call setup.bat
        if %ERRORLEVEL% NEQ 0 (
            echo.
            echo 初始化失败！请尝试手动运行setup.bat，或查看上面的错误信息。
            echo.
            echo 按任意键退出...
            pause >nul
            exit /b 1
        )
    ) else (
        :: 创建虚拟环境
        echo 正在创建虚拟环境...
        python -m venv venv
        if %ERRORLEVEL% NEQ 0 (
            echo 创建虚拟环境失败！
            echo.
            echo 按任意键退出...
            pause >nul
            exit /b 1
        )
        
        :: 激活虚拟环境
        call venv\Scripts\activate.bat
        
        :: 安装依赖
        echo 正在安装必要依赖...
        python -m pip install --upgrade pip
        
        if exist "requirements.txt" (
            pip install -r requirements.txt
            if %ERRORLEVEL% NEQ 0 (
                echo 部分依赖安装失败，但将继续尝试启动...
            )
        ) else (
            echo requirements.txt文件不存在，安装基本依赖...
            pip install flask selenium beautifulsoup4 webdriver-manager
        )
        
        :: 创建必要目录
        if not exist "output" mkdir output
        if not exist "cookies" mkdir cookies
        if not exist "logs" mkdir logs
    )
    
    echo ✓ 初始化完成！
    echo.
)

:: 检查是否存在乱码修复文件
if exist "Windows中文乱码修复指南.md" (
    echo 提示: 如果运行过程中出现中文乱码，请参考"Windows中文乱码修复指南.md"
    echo       或运行"启动评论爬虫_中文环境.bat"
    echo.
)

:: 检查启动脚本是否存在
if exist "crawler_web_start.py" (
    :: 启动Web应用
    echo ✓ 正在启动Web服务器...
    echo ✓ 服务启动后，请在浏览器中访问: http://localhost:5000
    echo.
    
    :: 在中文环境下使用-u参数启动Python
    if "%LANG:~0,2%"=="zh" (
        python -u crawler_web_start.py
    ) else (
        python crawler_web_start.py
    )
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