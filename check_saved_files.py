#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Steam评论文件检查工具 - 用于检查并管理已保存的评论文件
"""

import os
import sys
import json
import glob
import time
import shutil
import argparse
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# 默认输出目录
DEFAULT_OUTPUT_DIR = "output"

def find_all_review_files(base_dir=DEFAULT_OUTPUT_DIR):
    """查找所有评论文件
    
    Args:
        base_dir: 基础目录
        
    Returns:
        list: 文件路径列表
    """
    try:
        # 确保目录存在
        if not os.path.exists(base_dir):
            print(f"错误: 目录 {base_dir} 不存在")
            return []
        
        # 查找所有JSON文件
        pattern = os.path.join(base_dir, "**", "*.json")
        files = glob.glob(pattern, recursive=True)
        
        print(f"在 {base_dir} 中找到 {len(files)} 个评论文件")
        return files
    except Exception as e:
        print(f"查找文件时出错: {e}")
        return []

def read_review_file(file_path):
    """读取评论文件内容
    
    Args:
        file_path: 文件路径
        
    Returns:
        dict: 评论数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return None

def copy_files_to_dir(files, target_dir):
    """将文件复制到目标目录
    
    Args:
        files: 文件路径列表
        target_dir: 目标目录
        
    Returns:
        int: 成功复制的文件数量
    """
    try:
        # 确保目标目录存在
        os.makedirs(target_dir, exist_ok=True)
        
        copied_count = 0
        for file_path in files:
            if os.path.exists(file_path):
                # 获取相对路径（保持app_ID的目录结构）
                filename = os.path.basename(file_path)
                app_dir = os.path.basename(os.path.dirname(file_path))
                
                # 创建目标目录
                app_target_dir = os.path.join(target_dir, app_dir)
                os.makedirs(app_target_dir, exist_ok=True)
                
                # 目标文件路径
                target_path = os.path.join(app_target_dir, filename)
                
                # 复制文件
                shutil.copy2(file_path, target_path)
                copied_count += 1
                print(f"已复制: {file_path} -> {target_path}")
        
        print(f"成功复制 {copied_count} 个文件到 {target_dir}")
        return copied_count
    except Exception as e:
        print(f"复制文件失败: {e}")
        return 0

def create_gui():
    """创建图形界面"""
    window = tk.Tk()
    window.title("Steam评论文件检查工具")
    window.geometry("800x600")
    
    # 设置样式
    style = ttk.Style()
    style.configure("TButton", padding=6, relief="flat", background="#ccc")
    style.configure("TLabel", padding=6)
    style.configure("TFrame", padding=10)
    
    # 主框架
    main_frame = ttk.Frame(window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # 源目录框架
    source_frame = ttk.Frame(main_frame)
    source_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(source_frame, text="评论文件目录:").pack(side=tk.LEFT)
    source_entry = ttk.Entry(source_frame, width=50)
    source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    source_entry.insert(0, os.path.abspath(DEFAULT_OUTPUT_DIR))
    
    def browse_source():
        directory = filedialog.askdirectory(
            initialdir=source_entry.get(),
            title="选择评论文件目录"
        )
        if directory:
            source_entry.delete(0, tk.END)
            source_entry.insert(0, directory)
            refresh_file_list()
    
    ttk.Button(source_frame, text="浏览...", command=browse_source).pack(side=tk.RIGHT)
    
    # 文件列表框架
    list_frame = ttk.Frame(main_frame)
    list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # 创建带滚动条的列表
    list_scroll = ttk.Scrollbar(list_frame)
    list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    columns = ("游戏ID", "评论ID", "用户名", "推荐", "评论日期", "文件路径")
    file_tree = ttk.Treeview(list_frame, columns=columns, show="headings", yscrollcommand=list_scroll.set)
    
    # 设置列宽和标题
    file_tree.heading("游戏ID", text="游戏ID")
    file_tree.heading("评论ID", text="评论ID")
    file_tree.heading("用户名", text="用户名")
    file_tree.heading("推荐", text="推荐")
    file_tree.heading("评论日期", text="评论日期")
    file_tree.heading("文件路径", text="文件路径")
    
    file_tree.column("游戏ID", width=80)
    file_tree.column("评论ID", width=100)
    file_tree.column("用户名", width=120)
    file_tree.column("推荐", width=60)
    file_tree.column("评论日期", width=120)
    file_tree.column("文件路径", width=250)
    
    file_tree.pack(fill=tk.BOTH, expand=True)
    list_scroll.config(command=file_tree.yview)
    
    # 信息框架
    info_frame = ttk.Frame(main_frame)
    info_frame.pack(fill=tk.X, pady=5)
    
    file_count_var = tk.StringVar(value="找到 0 个评论文件")
    ttk.Label(info_frame, textvariable=file_count_var).pack(side=tk.LEFT)
    
    # 按钮框架
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=10)
    
    def refresh_file_list():
        # 清除当前列表
        for item in file_tree.get_children():
            file_tree.delete(item)
        
        # 找到所有文件
        source_dir = source_entry.get()
        files = find_all_review_files(source_dir)
        
        # 更新文件计数
        file_count_var.set(f"找到 {len(files)} 个评论文件")
        
        # 添加到列表
        for file_path in files:
            review_data = read_review_file(file_path)
            if review_data:
                item_values = (
                    review_data.get('app_id', '未知'),
                    review_data.get('review_id', '未知'),
                    review_data.get('user_name', '未知'),
                    "是" if review_data.get('recommended', False) else "否",
                    review_data.get('posted_date', '未知'),
                    file_path
                )
                file_tree.insert('', tk.END, values=item_values)
    
    def open_file():
        selected_items = file_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择一个文件")
            return
        
        # 获取选中文件的路径
        item = selected_items[0]
        file_path = file_tree.item(item, "values")[-1]
        
        # 在系统默认程序中打开文件
        try:
            import platform
            if platform.system() == 'Darwin':  # macOS
                os.system(f'open "{file_path}"')
            elif platform.system() == 'Windows':  # Windows
                os.system(f'start "" "{file_path}"')
            else:  # Linux
                os.system(f'xdg-open "{file_path}"')
            print(f"已打开文件: {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"打开文件失败: {e}")
    
    def copy_to_new_dir():
        selected_items = file_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择要复制的文件")
            return
        
        # 获取目标目录
        target_dir = filedialog.askdirectory(
            title="选择目标目录",
            mustexist=False
        )
        if not target_dir:
            return
        
        # 复制选中的文件
        files_to_copy = []
        for item in selected_items:
            file_path = file_tree.item(item, "values")[-1]
            files_to_copy.append(file_path)
        
        if not files_to_copy:
            messagebox.showinfo("提示", "没有选择任何文件")
            return
        
        # 执行复制
        copied = copy_files_to_dir(files_to_copy, target_dir)
        messagebox.showinfo("完成", f"成功复制 {copied} 个文件到 {target_dir}")
    
    def open_source_dir():
        source_dir = source_entry.get()
        if not os.path.exists(source_dir):
            messagebox.showinfo("提示", f"目录 {source_dir} 不存在")
            return
        
        # 打开源目录
        try:
            import platform
            if platform.system() == 'Darwin':  # macOS
                os.system(f'open "{source_dir}"')
            elif platform.system() == 'Windows':  # Windows
                os.system(f'explorer "{source_dir}"')
            else:  # Linux
                os.system(f'xdg-open "{source_dir}"')
            print(f"已打开目录: {source_dir}")
        except Exception as e:
            messagebox.showerror("错误", f"打开目录失败: {e}")
    
    ttk.Button(button_frame, text="刷新文件列表", command=refresh_file_list).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="打开选中文件", command=open_file).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="打开源目录", command=open_source_dir).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="另存为...", command=copy_to_new_dir).pack(side=tk.RIGHT, padx=5)
    
    # 初始加载文件列表
    refresh_file_list()
    
    window.mainloop()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Steam评论文件检查工具")
    parser.add_argument('--dir', type=str, default=DEFAULT_OUTPUT_DIR, help='评论文件目录')
    parser.add_argument('--gui', action='store_true', help='启动图形界面')
    args = parser.parse_args()
    
    if args.gui:
        create_gui()
    else:
        # 命令行模式
        files = find_all_review_files(args.dir)
        
        if not files:
            print("未找到任何评论文件")
            return
        
        # 显示文件信息
        print("\n文件列表:")
        for i, file_path in enumerate(files, 1):
            review_data = read_review_file(file_path)
            if review_data:
                app_id = review_data.get('app_id', '未知')
                game_title = review_data.get('game_title', '未知')
                user_name = review_data.get('user_name', '未知')
                recommended = "推荐" if review_data.get('recommended', False) else "不推荐"
                
                print(f"{i}. {game_title} (ID: {app_id}) - {user_name} {recommended}")
                print(f"   文件: {file_path}")
        
        # 询问是否复制文件
        print("\n是否要将文件复制到其他目录? (y/n)")
        answer = input().strip().lower()
        if answer == 'y':
            print("输入目标目录路径:")
            target_dir = input().strip()
            copy_files_to_dir(files, target_dir)

if __name__ == "__main__":
    main() 