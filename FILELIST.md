# 项目文件清单

## 核心文件（必需）

这些文件是项目正常运行的必要文件，不能删除：

### 爬虫核心

- `crawler_base.py` - 爬虫基础类，提供通用的爬虫功能
- `steam_crawler.py` - Steam游戏评论爬虫
- `tap_crawler.py` - TapTap游戏评论爬取
- `bili_crawler.py` - Bilibili评论爬虫
- `steam_cookies_helper.py` - Steam Cookie获取工具
- `steam_cookies_launcher.py` - Steam爬虫统一启动器

### 启动文件

- `启动Steam评论获取工具.bat` - Windows启动文件
- `启动Steam评论获取工具.command` - macOS启动文件
- `windows_quick_fix.bat` - Windows修复工具

### Web界面

- `crawler_web/` - Web界面目录
  - `app.py` - Flask应用主文件
  - `templates/` - HTML模板目录
    - `index.html` - 主页模板
    - `comments.html` - 评论列表页模板
    - `comment_details.html` - 评论详情页模板
  - `static/` - 静态资源目录
- `crawler_web_start.py` - Web服务启动脚本

### 配置文件

- `requirements.txt` - 项目依赖列表
- `setup.sh` - Linux/macOS安装脚本
- `setup.bat` - Windows安装脚本
- `USAGE.md` - 详细使用说明文档

## 工具脚本（推荐保留）

这些文件提供实用的工具功能，推荐保留但不是必需的：

- `run_crawlers.py` - 批量运行爬虫
- `cleanup.py` - 清理临时文件和缓存
- `windows_encoding_fix.py` - 修复Windows中文编码问题

## 自动创建的目录

以下目录会在程序运行时自动创建，无需手动创建：

- `output/` - 爬取结果输出目录
- `cookies/` - Cookie存储目录
- `logs/` - 日志文件目录
- `venv/` - Python虚拟环境目录

## 可以安全删除的文件

以下文件是旧版本、临时文件或不再需要的文件，可以安全删除：

- `.gitignore` - Git忽略文件（除非使用git管理项目）
- `__pycache__/` - Python缓存目录
- `.DS_Store` - macOS系统文件

## 文档文件

- `README.md` - 项目说明文档
- `USAGE.md` - 使用说明文档
- `UPDATE_LOG.md` - 更新日志
- `Windows中文乱码修复指南.md` - Windows编码问题修复指南
- `WEB启动说明.md` - Web服务启动说明
- `COMMIT_GUIDE.md` - 代码提交指南
- `LICENSE` - 许可证文件 