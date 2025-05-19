# 游戏评论爬虫与分析工具

一个功能强大的多平台游戏评论爬取、分析和可视化工具，支持Steam、TapTap和Bilibili等主流游戏平台。

## 主要功能

- **多平台爬虫**：
  - Steam游戏评论爬取
  - TapTap游戏评论爬取
  - Bilibili游戏视频评论爬取
- **Web界面**：提供用户友好的网页操作界面
- **数据导出**：支持CSV格式
- **实时进度**：显示爬取进度和实时日志
- **无头模式**：支持后台运行，提高性能
- **轻量级设计**：使用Python内置csv模块，无需额外的大型数据分析依赖

## 系统要求

- **操作系统**：Windows 10/11, macOS, Linux
- **Python版本**：Python 3.8+
- **浏览器**：Chrome (用于Selenium)
- **内存**：至少2GB RAM（推荐4GB）
- **存储**：至少100MB可用空间（取决于爬取数据量）

## 安装指南

### 步骤1：安装必要软件

1. 安装 [Python 3.8+](https://www.python.org/downloads/)
2. 安装 [Chrome浏览器](https://www.google.com/chrome/)
3. 确保安装了pip（Python包管理器）

### 步骤2：克隆项目

```bash
git clone https://github.com/dragonzxh/TapCommentScraper.git
cd TapCommentScraper
```

### 步骤3：安装依赖

在Linux/macOS上：
```bash
./setup.sh
```

在Windows上：
```bash
setup.bat
```

或者手动安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行使用

1. **Steam评论爬取**:
   ```bash
   python steam_crawler.py
   ```

2. **TapTap评论爬取**:
   ```bash
   python tap_crawler.py
   ```

3. **批量爬取**:
   ```bash
   python run_crawlers.py
   ```

### Web界面使用

1. **启动Web服务**:
   ```bash
   python crawler_web_start.py
   ```

2. **访问界面**:
   在浏览器中访问 http://localhost:5000

3. **设置参数**:
   - 选择爬虫类型（Steam/TapTap/Bilibili）
   - 输入游戏URL或ID
   - 设置保存路径和格式
   - 选择是否使用无头模式

4. **开始爬取**:
   点击"开始爬取"按钮，实时查看进度和日志

## 项目结构

```
TapCommentScraper/
├── crawler_base.py        # 爬虫基础类
├── steam_crawler.py       # Steam评论爬虫
├── tap_crawler.py         # TapTap评论爬虫
├── bili_crawler.py        # Bilibili评论爬虫
├── run_crawlers.py        # 批量爬取工具
├── crawler_web/           # Web界面模块
│   ├── app.py             # Flask应用
│   ├── crawler_manager.py # 爬虫管理器
│   ├── utils.py           # 工具函数
│   ├── static/            # 静态资源
│   └── templates/         # HTML模板
├── crawler_web_start.py   # Web服务启动脚本
├── output/                # 输出目录
├── cookies/               # Cookie存储目录
└── requirements.txt       # 依赖列表
```

## 常见问题

### Q: 爬虫运行速度慢怎么办？
A: 尝试以下方法：
   - 使用无头模式运行
   - 减少同时爬取的游戏数量
   - 优化网络连接
   - 增加系统内存

### Q: 提示"ChromeDriver未找到"怎么解决？
A: 系统会自动下载适配的ChromeDriver。如果失败，请手动下载ChromeDriver并放入PATH环境变量指定的目录。

### Q: 如何处理"请求被拒绝"错误？
A: 可能是因为请求频率过高被平台限制。尝试：
   - 减少爬取频率
   - 使用Cookie登录状态
   - 等待一段时间后再尝试

### Q: 数据保存在哪里？
A: 默认保存在项目根目录的`output`文件夹，可以在Web界面或参数中修改保存路径。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来帮助改进项目！

# Steam评论爬虫工具

一个基于Microsoft Edge浏览器的Steam游戏评论爬取工具，支持评论数据导出和分析。

## 主要功能

- **Steam评论爬取**：
  - 支持Steam游戏评论爬取
  - 自动处理Steam登录和Cookie管理
  - 自动处理年龄验证页面
  - 支持评论分页爬取
  - 支持评论回复爬取
- **Web界面**：提供用户友好的网页操作界面
- **数据导出**：支持CSV格式导出
- **实时进度**：显示爬取进度和实时日志
- **无头模式**：支持后台运行，提高性能

## 系统要求

- **操作系统**：Windows 10/11, macOS
- **Python版本**：Python 3.8+
- **浏览器**：Microsoft Edge
- **内存**：至少2GB RAM（推荐4GB）
- **存储**：至少100MB可用空间（取决于爬取数据量）

## 安装指南

### 步骤1：安装必要软件

1. 安装 [Python 3.8+](https://www.python.org/downloads/)
2. 安装 [Microsoft Edge浏览器](https://www.microsoft.com/edge)
3. 确保安装了pip（Python包管理器）

### 步骤2：克隆项目

```bash
git clone https://github.com/dragonzxh/TapCommentScraper.git
cd TapCommentScraper
```

### 步骤3：安装依赖

在macOS上：
```bash
./setup.sh
```

在Windows上：
```bash
setup.bat
```

或者手动安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

### 启动爬虫

#### Windows用户
1. 双击 `start_steam_crawler_edge.bat`
2. 或在PowerShell中运行 `start_steam_crawler_edge_ps1.ps1`

#### macOS用户
1. 双击 `start_steam_crawler_edge.command`
2. 或在终端中运行：
```bash
chmod +x start_steam_crawler_edge.command
./start_steam_crawler_edge.command
```

### Web界面使用

1. 启动后，浏览器会自动打开 http://localhost:5000/steam
2. 在界面中：
   - 输入Steam游戏URL或AppID
   - 设置保存路径和格式
   - 选择是否使用无头模式
   - 点击"开始爬取"按钮

## 项目结构

```
TapCommentScraper/
├── src/                    # Python源代码目录
│   ├── steam_simple_crawler_edge.py  # 主程序
│   ├── steam_config.py     # 配置文件
│   ├── steam_driver.py     # 浏览器驱动管理
│   ├── steam_cookies.py    # Cookie管理
│   └── ... (其他Python文件)
├── start_steam_crawler_edge.bat      # Windows启动脚本
├── start_steam_crawler_edge.command  # macOS启动脚本
├── start_steam_crawler_edge_ps1.ps1  # PowerShell启动脚本
├── setup.bat              # Windows设置脚本
├── setup.sh              # macOS设置脚本
├── requirements.txt      # 依赖文件
└── README.md            # 项目说明
```

## 常见问题

### Q: 爬虫运行速度慢怎么办？
A: 尝试以下方法：
   - 使用无头模式运行
   - 减少同时爬取的游戏数量
   - 优化网络连接
   - 增加系统内存

### Q: 提示"EdgeDriver未找到"怎么解决？
A: 系统会自动下载适配的EdgeDriver。如果失败，请确保已安装最新版本的Microsoft Edge浏览器。

### Q: 如何处理"请求被拒绝"错误？
A: 可能是因为请求频率过高被平台限制。尝试：
   - 减少爬取频率
   - 使用Cookie登录状态
   - 等待一段时间后再尝试

### Q: 数据保存在哪里？
A: 默认保存在项目根目录的`output`文件夹，可以在Web界面或参数中修改保存路径。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来帮助改进项目！
