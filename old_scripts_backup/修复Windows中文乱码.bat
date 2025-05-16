@echo off
chcp 65001 >nul
echo Windows中文编码修复工具
echo =================================
echo 此工具将修复评论爬虫在Windows环境下可能出现的中文乱码问题。
echo.

:: 检查是否以管理员身份运行
net session >nul 2>&1
if %errorlevel% == 0 (
    echo 正在以管理员身份运行...
) else (
    echo 需要管理员权限才能修复系统编码问题。
    echo 请右键点击此文件，选择"以管理员身份运行"。
    echo.
    pause
    exit /b
)

:: 运行Python修复脚本
echo 正在修复编码问题...
python windows_encoding_fix.py

echo.
echo 修复完成！现在您可以正常运行爬虫而不会出现中文乱码。
echo.
pause 