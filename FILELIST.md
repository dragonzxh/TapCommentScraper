# 项目文件列表

## 核心爬虫文件 (src/)
- `steam_simple_crawler_edge.py` - Steam评论爬虫主程序（Edge浏览器版）
- `steam_config.py` - Steam爬虫配置文件
- `steam_driver.py` - Steam浏览器驱动管理
- `steam_cookies.py` - Steam Cookie管理
- `steam_cookies_helper.py` - Steam Cookie辅助工具
- `steam_cookies_launcher.py` - Steam Cookie启动器
- `steam_content_warning_fix.py` - Steam内容警告处理
- `age_verification.py` - 年龄验证处理
- `crawler_base.py` - 爬虫基础类
- `crawler_web_start.py` - 爬虫Web服务启动器

## 其他爬虫相关文件 (src/)
- `bili_crawler.py` - B站评论爬虫
- `tap_crawler.py` - TapTap评论爬虫
- `run_crawlers.py` - 多平台爬虫运行器

## 工具和辅助文件 (src/)
- `check_deps.py` - 依赖检查工具
- `check_saved_files.py` - 文件检查工具
- `diagnose_edge_crawler.py` - Edge爬虫诊断工具
- `windows_encoding_fix.py` - Windows编码修复工具

## 启动脚本
- `start_steam_crawler_edge.bat` - Windows启动脚本
- `start_steam_crawler_edge.command` - macOS启动脚本
- `start_steam_crawler_edge_ps1.ps1` - PowerShell启动脚本

## 设置脚本
- `setup.bat` - Windows环境设置脚本
- `setup.sh` - macOS/Linux环境设置脚本

## 文档
- `README.md` - 项目说明文档
- `CHANGELOG.md` - 更新日志
- `USAGE.md` - 使用说明
- `UPDATE_LOG.md` - 更新记录
- `LICENSE` - 许可证文件

## 目录
- `src/` - Python源代码目录
- `logs/` - 日志文件目录
- `output/` - 输出文件目录
- `cookies/` - Cookie文件目录
- `venv/` - Python虚拟环境目录
- `crawler_web/` - Web界面相关文件
- `.git/` - Git版本控制目录

## 其他文件
- `requirements.txt` - Python依赖列表
- `git_commit.sh` - Git提交脚本
- `diagnose_edge_crawler_fix.bat` - Edge爬虫诊断修复脚本 