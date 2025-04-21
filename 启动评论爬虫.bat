@echo off
chcp 65001 >nul
:: 评论爬虫Web应用快速启动器 (Windows)
:: 此文件可以放在桌面上，用户只需双击即可启动应用

echo =================================================
echo       评论爬虫Web应用 - 快速启动器 (Windows)
echo =================================================
echo 正在启动服务...
echo.

:: 项目目录路径 - 请根据实际安装位置修改
set PROJECT_PATH=%~dp0

:: 显示当前路径
echo ✓ 当前工作目录: %PROJECT_PATH%

:: 切换到项目目录
cd /d "%PROJECT_PATH%"

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