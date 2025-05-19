#!/bin/bash
# 自动同步本地与GitHub远程分支（以本地为准）
# 用法：bash git_commit.sh "提交说明"

# 确保脚本在错误时退出
set -e

echo "开始提交代码到GitHub..."

# 1. 拉取远程最新（保留本地变更）
git fetch origin

echo "对比本地与远程分支..."
git status

echo "添加所有变更..."
git add .

# 2. 提交（带自定义说明）
if [ -z "$1" ]; then
  msg="sync: 本地结构与代码为准自动同步"
else
  msg="$1"
fi
git commit -m "$msg" || echo "无变更可提交"

# 3. 强制推送本地到远程（以本地为准）
echo "强制推送到远程..."
git push origin HEAD:main --force

echo "完成！代码已成功提交到GitHub。" 