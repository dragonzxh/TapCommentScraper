# Steam评论爬虫工具使用说明

## 系统要求

- Python 3.8 或更高版本
- Microsoft Edge 浏览器
- 操作系统：Windows 10/11 或 macOS

## 安装步骤

### Windows

1. 确保已安装 Python 3.8+ 和 Microsoft Edge 浏览器
2. 双击 `setup.bat` 文件，或在命令提示符中运行：
   ```
   setup.bat
   ```
3. 安装脚本会自动创建虚拟环境并安装所需依赖

### macOS

1. 确保已安装 Python 3.8+ 和 Microsoft Edge 浏览器
2. 打开终端，进入项目目录，运行：
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
3. 安装脚本会自动创建虚拟环境并安装所需依赖

## 启动爬虫

### Windows

1. 双击 `start_steam_crawler_edge.bat` 文件
2. 或在 PowerShell 中右键点击 `start_steam_crawler_edge_ps1.ps1` 选择"使用 PowerShell 运行"

### macOS

1. 双击 `start_steam_crawler_edge.command` 文件
2. 或在终端中运行：
   ```bash
   chmod +x start_steam_crawler_edge.command
   ./start_steam_crawler_edge.command
   ```

## 使用Web界面

1. 启动后，浏览器会自动打开 http://localhost:5000/steam
2. 在Web界面中：
   - 输入Steam游戏URL或AppID
   - 设置保存路径和格式
   - 选择是否使用无头模式
   - 点击"开始爬取"按钮

## 查看评论数据

1. 爬取完成后，数据将保存在 `output` 目录下
2. 可以在Web界面上查看爬取结果
3. 支持导出为CSV格式

## 常见问题解决

### 安装问题

1. **找不到Microsoft Edge浏览器**
   - 确保已安装最新版本的Microsoft Edge浏览器
   - 可以从[Microsoft官网](https://www.microsoft.com/edge)下载安装

2. **找不到模块**
   - 确保已激活虚拟环境
   - 重新运行安装脚本：`setup.bat` 或 `setup.sh`

3. **Python版本问题**
   - 确保安装了Python 3.8或更高版本
   - 可以从[Python官网](https://www.python.org/downloads/)下载安装

### 运行问题

1. **Edge浏览器找不到**
   - 确保已安装Microsoft Edge浏览器
   - 如果安装在非标准位置，请修改 `src/steam_config.py` 中的浏览器路径

2. **网页元素无法找到**
   - 可能是网站结构已更改，尝试更新爬虫代码中的选择器
   - 尝试关闭无头模式，以便查看浏览器操作

3. **爬虫运行缓慢**
   - 减少要爬取的评论数量
   - 检查网络连接
   - 确保计算机资源充足

## 高级使用

1. **修改输出格式**
   - 爬虫默认将数据保存为CSV格式
   - 可以在Web界面中选择不同的导出格式

2. **自定义输出目录**
   - 修改 `output` 文件夹的路径（默认在项目根目录下）
   - 在Web界面中可以设置自定义保存路径

## 注意事项

- 爬虫工具仅用于研究和学习目的
- 请遵守Steam网站的使用条款和robots.txt规则
- 过于频繁的请求可能导致IP被封，请合理控制爬取频率
- 请勿使用爬取的数据进行商业用途 