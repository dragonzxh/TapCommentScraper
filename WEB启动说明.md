# 评论爬虫Web应用启动说明

## 方法一：使用启动脚本（推荐）

我们提供了几种便捷的启动脚本，您可以根据自己的喜好选择使用：

### macOS 用户

1. **双击启动（最简单）**：
   - 在项目根目录找到 `启动评论爬虫.command` 文件
   - 双击此文件即可启动Web应用
   - 首次运行可能需要在系统对话框中确认允许运行

2. **使用通用启动脚本**：
   - 打开终端
   - 进入项目目录：`cd /Users/hippolyte/TapCommentScraper`
   - 执行脚本：`./web_launcher.sh`

3. **使用菜单选择**：
   - 打开终端
   - 进入项目目录：`cd /Users/hippolyte/TapCommentScraper`
   - 执行脚本：`./run_on_mac.sh`
   - 在菜单中选择选项 `5` 启动Web界面

### Windows 用户

1. **双击启动（最简单）**：
   - 在项目根目录找到 `启动评论爬虫.bat` 文件
   - 双击此文件即可启动Web应用

2. **使用通用启动脚本**：
   - 打开命令提示符(CMD)
   - 进入项目目录：`cd C:\您的项目路径\TapCommentScraper`
   - 执行脚本：`web_launcher_windows.bat`

3. **使用菜单选择**：
   - 打开命令提示符(CMD)
   - 进入项目目录：`cd C:\您的项目路径\TapCommentScraper`
   - 执行脚本：`run_on_windows.bat`
   - 在菜单中选择选项 `5` 启动Web界面

## 方法二：手动启动

如果启动脚本出现问题，您可以尝试手动启动：

### macOS 用户

1. 打开终端
2. 进入项目目录：`cd /Users/hippolyte/TapCommentScraper`
3. 激活虚拟环境：`source venv/bin/activate`
4. 启动服务器：`python crawler_web_start.py`

### Windows 用户

1. 打开命令提示符(CMD)
2. 进入项目目录：`cd C:\您的项目路径\TapCommentScraper`
3. 激活虚拟环境：`venv\Scripts\activate.bat`
4. 启动服务器：`python crawler_web_start.py`

## 访问Web应用

无论使用哪种方式启动，Web应用启动成功后，您可以在浏览器中访问：

```
http://localhost:5000
```

## 常见问题排查

1. **无法找到文件** - 确保您在正确的目录下执行命令
   - macOS: `cd /Users/hippolyte/TapCommentScraper`
   - Windows: `cd C:\您的项目路径\TapCommentScraper`

2. **虚拟环境不存在** - 需要先运行安装脚本
   - macOS: `./setup.sh`
   - Windows: `setup.bat`

3. **端口冲突** - 如果5000端口被占用，您可以修改 `crawler_web/app.py` 文件中的端口号
   ```python
   app.run(debug=True, host='0.0.0.0', port=5000)  # 将5000改为其他端口
   ```

4. **Windows中文显示问题** - 如果命令行中显示乱码，请确保使用了UTF-8编码
   - 在CMD中执行：`chcp 65001`
   - 或使用PowerShell代替CMD 