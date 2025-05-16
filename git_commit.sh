#!/bin/bash

# 确保脚本在错误时退出
set -e

echo "开始提交代码到GitHub..."

# 添加所有修改的文件
git add .

# 使用COMMIT_MESSAGE.md中的内容作为提交信息
echo "使用COMMIT_MESSAGE.md作为提交信息..."
git commit -F COMMIT_MESSAGE.md

# 推送到远程仓库
echo "推送到远程仓库..."
git push origin main

echo "完成！代码已成功提交到GitHub。" 