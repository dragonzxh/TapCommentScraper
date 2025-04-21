# Git提交指南

按照以下步骤将更改提交到GitHub仓库。

## 1. 添加新文件

```bash
# 添加启动脚本
git add start_web.sh
git add web_launcher.sh
git add web_launcher_windows.bat
git add "启动评论爬虫.command"
git add "启动评论爬虫.bat"

# 添加文档
git add "WEB启动说明.md"
git add UPDATE_LOG.md
git add USAGE.md
git add COMMIT_GUIDE.md

# 添加其它新增文件
git add crawler_web/__init__.py
git add run_on_mac.sh
git add run_on_windows.bat
```

## 2. 添加修改的文件

```bash
# 添加所有修改的文件
git add -u
```

## 3. 检查状态

```bash
git status
```

确保所有需要提交的文件都已经被添加，而不需要提交的文件（如output目录内容）没有被添加。

## 4. 提交更改

```bash
git commit -m "增强Web应用启动脚本，支持跨平台一键启动"
```

## 5. 推送到远程仓库

```bash
git push origin main
```

## 注意事项

1. 确保不要提交敏感信息或大型数据文件
2. 如果没有写权限，可以先创建分支，然后提交Pull Request
3. 如果出现冲突，需要先拉取最新代码并解决冲突

```bash
git pull origin main
# 解决冲突后再提交
```

## 提交后的工作

1. 验证GitHub上的更改是否正确显示
2. 检查CI/CD流程是否正常运行（如果有）
3. 更新相关的文档或Wiki页面 