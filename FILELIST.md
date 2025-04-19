# 项目文件清单

## 核心文件（必需）

这些文件是项目正常运行的必要文件，不能删除：

### 爬虫核心

- `crawler_base.py` - 爬虫基础类，提供通用的爬虫功能
- `steam_crawler.py` - Steam游戏评论爬虫
- `tap_crawler.py` - TapTap游戏评论爬取
- `bili_crawler.py` - Bilibili评论爬虫

### Web界面

- `crawler_web/` - Web界面目录
  - `app.py` - Flask应用主文件
  - `crawler_manager.py` - 爬虫管理器
  - `utils.py` - 工具函数
  - `templates/` - HTML模板目录
    - `index.html` - 主页模板
  - `static/` - 静态资源目录
    - `css/` - CSS样式文件
    - `js/` - JavaScript文件
- `crawler_web_start.py` - Web服务启动脚本

### 配置文件

- `requirements_full.txt` - 完整的依赖列表
- `setup.sh` - Linux/macOS安装脚本
- `setup.bat` - Windows安装脚本
- `README_new.md` - 新版本的说明文档

## 工具脚本（推荐保留）

这些文件提供实用的工具功能，推荐保留但不是必需的：

- `run_crawlers.py` - 批量运行爬虫
- `cleanup.py` - 清理临时文件和缓存
- `test_steam.py` - Steam爬虫测试脚本
- `test_crawler.py` - 通用爬虫测试脚本

## 自动创建的目录

以下目录会在程序运行时自动创建，无需手动创建：

- `output/` - 爬取结果输出目录
- `cookies/` - Cookie存储目录
- `logs/` - 日志文件目录

## 可以安全删除的文件

以下文件是旧版本、临时文件或不再需要的文件，可以安全删除：

- `TapTapCrawler.spec` - PyInstaller规格文件
- `game_errorlist.txt` - 错误游戏列表（临时文件）
- `~$84463_comments.xlsx` - Excel临时文件
- `.gitignore` - Git忽略文件（除非使用git管理项目）
- `__pycache__/` - Python缓存目录
- `Tapcomment.py` - 旧版爬虫文件（已被tap_crawler.py替代）
- `Bilicomment.py` - 旧版爬虫文件（已被bili_crawler.py替代）
- `requirements.txt` - 旧版依赖文件（已被requirements_full.txt替代）
- `requirements_web.txt` - 旧版Web依赖文件（已被requirements_full.txt替代）

## 数据文件

这些是爬取得到的数据文件，根据需要决定是否保留：

- `output/` 目录下的所有CSV、TXT和Excel文件
- `730_comments.csv` - CS:GO评论数据文件
- `84463_comments.xlsx` - 游戏评论Excel文件

## 部署相关文件

这些文件用于项目部署和打包，如果不需要可以删除：

- `setup.py` - Python包安装脚本
- `crawler_web.egg-info/` - Python包元数据
- `webserver.py` - 独立的Web服务器脚本 