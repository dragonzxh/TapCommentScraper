@echo off
rem 使用默认系统编码，避免UTF-8编码问题
echo Edge爬虫诊断工具
echo ==============================
echo.

rem 获取当前目录
set "DIR=%~dp0"
cd /d "%DIR%"

rem 创建日志目录
if not exist "logs" mkdir logs

echo 正在启动诊断工具...
echo 这将帮助诊断和修复Windows环境下Edge爬虫的常见问题
echo.

rem 检查Python安装
echo 检查Python安装...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

rem 检查虚拟环境
if exist "venv" (
    echo 检测到虚拟环境，激活中...
    call venv\Scripts\activate.bat
) else (
    echo 未检测到虚拟环境，使用系统Python
)

rem 运行诊断工具
echo 正在运行诊断工具...
python diagnose_edge_crawler.py

echo.
echo 诊断完成，请根据诊断结果修复问题
pause 