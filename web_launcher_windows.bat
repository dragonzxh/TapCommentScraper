@echo off
chcp 65001 >nul
:: 评论爬虫Web应用通用启动器 (Windows)
:: 此脚本可以从命令行中运行，用于启动Web应用

echo =================================================
echo       评论爬虫Web应用 - 通用启动器 (Windows)
echo =================================================
echo 正在启动服务...
echo.

:: 获取脚本所在目录
set SCRIPT_DIR=%~dp0
echo ✓ 脚本所在目录: %SCRIPT_DIR%

:: 切换到项目目录
cd /d "%SCRIPT_DIR%"
echo ✓ 当前工作目录: %cd%

:: 检查虚拟环境是否存在
if exist "venv\Scripts\activate.bat" (
    :: 激活虚拟环境
    call venv\Scripts\activate.bat
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
    python crawler_web_start.py
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