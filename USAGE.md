# 游戏评论爬虫工具使用说明

## 系统要求

- Python 3.8 或更高版本
- Chrome 浏览器
- 操作系统：Windows、macOS 或 Linux

## 安装步骤

### Windows

1. 确保已安装 Python 3.8+ 和 Chrome 浏览器
2. 双击 `setup.bat` 文件，或在命令提示符中运行：
   ```
   setup.bat
   ```
3. 安装脚本会自动创建虚拟环境并安装所需依赖

### macOS/Linux

1. 确保已安装 Python 3.8+ 和 Chrome 浏览器
2. 打开终端，进入项目目录，运行：
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
3. 安装脚本会自动创建虚拟环境并安装所需依赖

## 启动爬虫Web界面

### Windows

1. 打开命令提示符，进入项目目录
2. 激活虚拟环境：
   ```
   venv\Scripts\activate
   ```
3. 启动Web服务：
   ```
   python crawler_web_start.py
   ```
4. 在浏览器中访问：http://localhost:5000

### macOS/Linux

1. 打开终端，进入项目目录
2. 激活虚拟环境：
   ```bash
   source venv/bin/activate
   ```
3. 启动Web服务：
   ```bash
   python crawler_web_start.py
   ```
4. 在浏览器中访问：http://localhost:5000

## 使用爬虫

1. 在Web界面中，选择要使用的爬虫类型（Steam、TapTap或Bilibili）
2. 输入要爬取的URL
3. 点击"开始爬取"按钮
4. 爬取完成后，可在"查看已爬取的评论"页面查看结果

## 查看评论数据

1. 在Web界面上点击"查看已爬取的评论"按钮
2. 在评论列表页面，点击"查看详情"以查看特定文件的评论
3. 在评论详情页面，可以浏览评论内容并使用分页功能

## 常见问题解决

### 安装问题

1. **Pillow安装失败**
   - Windows：尝试 `pip install pillow --only-binary :all:`
   - macOS：安装系统依赖 `brew install libjpeg libtiff little-cms2 webp openjpeg`，然后 `pip install pillow`
   - Linux：安装系统依赖 `sudo apt-get install libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libopenjp2-7-dev`，然后 `pip install pillow`

2. **找不到模块 'tqdm'**
   - 确保已激活虚拟环境
   - 手动安装：`pip install tqdm`

3. **找不到模块 'crawler_web.app'**
   - 尝试直接运行：`cd crawler_web && python app.py`
   - 或修改导入方式：编辑 `crawler_web_start.py` 修改导入语句为 `from app import main`

### 运行问题

1. **Chrome浏览器找不到**
   - 确保已安装Chrome浏览器
   - 如果安装在非标准位置，请修改 `crawler_base.py` 中的浏览器路径

2. **网页元素无法找到**
   - 可能是网站结构已更改，尝试更新爬虫代码中的选择器
   - 尝试关闭无头模式，以便查看浏览器操作

3. **爬虫运行缓慢**
   - 减少要爬取的评论数量
   - 检查网络连接
   - 确保计算机资源充足

## 高级使用

1. **修改输出格式**
   - 爬虫默认将数据保存为CSV格式，如需其他格式，请修改 `crawler_base.py` 中的 `ExcelWriter` 类

2. **添加新爬虫**
   - 继承 `BaseCrawler` 类创建新的爬虫类
   - 实现 `get_comment_selectors` 和 `extract_comments` 方法
   - 更新Web界面以支持新爬虫

3. **自定义输出目录**
   - 修改 `output` 文件夹的路径（默认在项目根目录下）

## 注意事项

- 爬虫工具仅用于研究和学习目的
- 请遵守网站的使用条款和robots.txt规则
- 过于频繁的请求可能导致IP被封，请合理控制爬取频率
- 请勿使用爬取的数据进行商业用途 