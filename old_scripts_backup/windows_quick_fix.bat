@echo off
chcp 65001 >nul
echo Windows启动修复工具
echo =================================
echo 此工具将尝试解决"could not reach host"问题
echo.

:: 设置环境变量强制使用UTF-8
set PYTHONIOENCODING=utf-8

:: 切换到项目目录
cd /d "%~dp0"
echo 当前工作目录: %cd%

:: 检查虚拟环境是否存在
if exist "venv\Scripts\activate.bat" (
    :: 激活虚拟环境
    call venv\Scripts\activate.bat
    echo 已激活虚拟环境
) else (
    echo 错误: 虚拟环境不存在!
    echo 请先运行 setup.bat 脚本安装依赖
    pause
    exit /b 1
)

:: 添加环境变量
set FLASK_APP=crawler_web/app.py
set FLASK_ENV=development
set FLASK_DEBUG=1

echo 正在启动服务器...
echo 服务启动后，请在浏览器中访问: http://localhost:5000
echo.

:: 使用flask命令直接启动
python -m flask run --host=localhost --port=5000

echo.
echo 服务器已关闭
pause 