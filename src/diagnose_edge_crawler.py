#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Edge爬虫诊断工具
用于诊断和修复Windows环境下Edge爬虫的常见问题
"""

import os
import sys
import platform
import subprocess
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# 设置日志
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 创建一个日志文件名，包含日期和时间
log_file = log_dir / f"edge_diagnosis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("EdgeDiagnostic")

def print_header(title):
    """打印格式化的标题"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50 + "\n")

def check_system_info():
    """检查系统信息"""
    print_header("系统信息")
    
    system_info = {
        "操作系统": platform.system(),
        "操作系统版本": platform.version(),
        "操作系统发行版": platform.release(),
        "处理器架构": platform.machine(),
        "Python版本": platform.python_version(),
        "Python解释器": sys.executable,
        "当前目录": os.getcwd(),
        "用户主目录": str(Path.home())
    }
    
    for key, value in system_info.items():
        logger.info(f"{key}: {value}")
        print(f"{key}: {value}")
    
    return system_info

def check_edge_browser():
    """检查Edge浏览器安装情况"""
    print_header("Edge浏览器检查")
    
    edge_info = {
        "已安装": False,
        "版本": "未知",
        "安装路径": "未知"
    }
    
    # 检查Edge浏览器是否安装
    if platform.system() == "Windows":
        # 检查常见的Edge安装路径
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        
        for path in edge_paths:
            if os.path.exists(path):
                edge_info["已安装"] = True
                edge_info["安装路径"] = path
                
                # 尝试获取版本信息
                try:
                    result = subprocess.run(
                        [path, "--version"], 
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    if result.stdout:
                        edge_info["版本"] = result.stdout.strip()
                    else:
                        # 尝试另一种方式获取版本
                        import winreg
                        try:
                            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Edge\BLBeacon") as key:
                                edge_info["版本"] = winreg.QueryValueEx(key, "version")[0]
                        except:
                            pass
                except:
                    pass
                
                break
    else:
        logger.warning("非Windows系统，Edge浏览器检查可能不准确")
        
        # 在非Windows系统上尝试检测Edge
        try:
            result = subprocess.run(
                ["msedge", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0:
                edge_info["已安装"] = True
                edge_info["版本"] = result.stdout.strip()
        except:
            pass
    
    if edge_info["已安装"]:
        logger.info(f"Microsoft Edge已安装: 版本 {edge_info['版本']}")
        logger.info(f"安装路径: {edge_info['安装路径']}")
        print(f"✅ Microsoft Edge已安装: 版本 {edge_info['版本']}")
        print(f"   安装路径: {edge_info['安装路径']}")
    else:
        logger.warning("未检测到Microsoft Edge浏览器")
        print("❌ 未检测到Microsoft Edge浏览器")
        print("   请安装Microsoft Edge浏览器后再使用Edge爬虫")
    
    return edge_info

def check_python_packages():
    """检查必要的Python包"""
    print_header("Python包检查")
    
    required_packages = [
        "flask", 
        "selenium", 
        "beautifulsoup4", 
        "requests", 
        "webdriver-manager"
    ]
    
    packages_info = {}
    missing_packages = []
    
    for package in required_packages:
        try:
            # 尝试导入包
            module = __import__(package.replace("-", "_"))
            version = getattr(module, "__version__", "未知")
            packages_info[package] = {
                "已安装": True,
                "版本": version
            }
            logger.info(f"✅ {package}: 已安装 (版本 {version})")
            print(f"✅ {package}: 已安装 (版本 {version})")
        except ImportError:
            packages_info[package] = {
                "已安装": False,
                "版本": "未安装"
            }
            missing_packages.append(package)
            logger.warning(f"❌ {package}: 未安装")
            print(f"❌ {package}: 未安装")
    
    # 特别检查webdriver_manager
    try:
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        packages_info["webdriver_manager_edge"] = {
            "已安装": True,
            "版本": "可用"
        }
        logger.info("✅ EdgeChromiumDriverManager可用")
        print("✅ EdgeChromiumDriverManager可用")
    except ImportError:
        packages_info["webdriver_manager_edge"] = {
            "已安装": False,
            "版本": "不可用"
        }
        logger.warning("❌ EdgeChromiumDriverManager不可用")
        print("❌ EdgeChromiumDriverManager不可用")
    
    if missing_packages:
        print("\n需要安装以下包:")
        install_cmd = f"{sys.executable} -m pip install " + " ".join(missing_packages)
        print(f"  {install_cmd}")
        
        choice = input("\n是否立即安装这些包? (y/n): ")
        if choice.lower() == 'y':
            try:
                logger.info(f"开始安装缺失的包: {', '.join(missing_packages)}")
                subprocess.run(install_cmd, shell=True, check=True)
                logger.info("包安装完成")
                print("✅ 包安装完成")
            except subprocess.CalledProcessError:
                logger.error("安装包时出错")
                print("❌ 安装包时出错")
    
    return packages_info

def check_webdriver():
    """检查WebDriver"""
    print_header("WebDriver检查")
    
    webdriver_info = {
        "webdriver_manager": False,
        "edge_driver": False,
        "edge_driver_path": "未知"
    }
    
    # 检查webdriver_manager
    try:
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        webdriver_info["webdriver_manager"] = True
        
        # 尝试获取Edge驱动路径
        try:
            driver_path = EdgeChromiumDriverManager().install()
            webdriver_info["edge_driver"] = True
            webdriver_info["edge_driver_path"] = driver_path
            
            logger.info(f"✅ Edge驱动已安装: {driver_path}")
            print(f"✅ Edge驱动已安装: {driver_path}")
        except Exception as e:
            logger.error(f"安装Edge驱动时出错: {e}")
            print(f"❌ 安装Edge驱动时出错: {e}")
    except ImportError:
        logger.warning("未安装webdriver_manager")
        print("❌ 未安装webdriver_manager")
    
    return webdriver_info

def check_project_structure():
    """检查项目结构"""
    print_header("项目结构检查")
    
    required_files = [
        "steam_simple_crawler_edge.py",
        "crawler_web_start.py",
        "crawler_web/app.py"
    ]
    
    required_dirs = [
        "crawler_web",
        "output",
        "cookies",
        "logs"
    ]
    
    structure_info = {
        "files": {},
        "directories": {}
    }
    
    # 检查必要的文件
    for file_path in required_files:
        file = Path(file_path)
        exists = file.exists()
        structure_info["files"][file_path] = exists
        
        if exists:
            logger.info(f"✅ 文件存在: {file_path}")
            print(f"✅ 文件存在: {file_path}")
        else:
            logger.warning(f"❌ 文件不存在: {file_path}")
            print(f"❌ 文件不存在: {file_path}")
    
    # 检查必要的目录
    for dir_path in required_dirs:
        directory = Path(dir_path)
        exists = directory.exists()
        structure_info["directories"][dir_path] = exists
        
        if exists:
            logger.info(f"✅ 目录存在: {dir_path}")
            print(f"✅ 目录存在: {dir_path}")
        else:
            logger.warning(f"❌ 目录不存在: {dir_path}")
            print(f"❌ 目录不存在: {dir_path}")
            
            # 创建缺失的目录
            choice = input(f"是否创建目录 {dir_path}? (y/n): ")
            if choice.lower() == 'y':
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    logger.info(f"已创建目录: {dir_path}")
                    print(f"✅ 已创建目录: {dir_path}")
                except Exception as e:
                    logger.error(f"创建目录时出错: {e}")
                    print(f"❌ 创建目录时出错: {e}")
    
    return structure_info

def test_selenium_edge():
    """测试Selenium和Edge浏览器"""
    print_header("Selenium和Edge浏览器测试")
    
    test_result = {
        "selenium_import": False,
        "edge_import": False,
        "webdriver_manager_import": False,
        "edge_launch": False,
        "navigation": False,
        "screenshot": False
    }
    
    # 测试Selenium导入
    try:
        import selenium
        test_result["selenium_import"] = True
        logger.info(f"✅ Selenium导入成功 (版本 {selenium.__version__})")
        print(f"✅ Selenium导入成功 (版本 {selenium.__version__})")
    except ImportError as e:
        logger.error(f"❌ Selenium导入失败: {e}")
        print(f"❌ Selenium导入失败: {e}")
        return test_result
    
    # 测试Edge WebDriver导入
    try:
        from selenium import webdriver
        from selenium.webdriver.edge.service import Service
        from selenium.webdriver.edge.options import Options
        test_result["edge_import"] = True
        logger.info("✅ Edge WebDriver导入成功")
        print("✅ Edge WebDriver导入成功")
    except ImportError as e:
        logger.error(f"❌ Edge WebDriver导入失败: {e}")
        print(f"❌ Edge WebDriver导入失败: {e}")
        return test_result
    
    # 测试WebDriver Manager导入
    try:
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        test_result["webdriver_manager_import"] = True
        logger.info("✅ EdgeChromiumDriverManager导入成功")
        print("✅ EdgeChromiumDriverManager导入成功")
    except ImportError as e:
        logger.warning(f"❌ EdgeChromiumDriverManager导入失败: {e}")
        print(f"❌ EdgeChromiumDriverManager导入失败: {e}")
        # 继续测试，因为可能有系统安装的Edge驱动
    
    # 测试启动Edge浏览器
    driver = None
    try:
        print("正在尝试启动Edge浏览器...")
        options = Options()
        options.add_argument('--headless=new')
        
        if test_result["webdriver_manager_import"]:
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            service = Service(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=options)
        else:
            driver = webdriver.Edge(options=options)
        
        test_result["edge_launch"] = True
        logger.info("✅ Edge浏览器启动成功")
        print("✅ Edge浏览器启动成功")
        
        # 测试导航
        print("正在测试网页导航...")
        driver.get("https://www.microsoft.com")
        test_result["navigation"] = True
        logger.info("✅ 网页导航成功")
        print("✅ 网页导航成功")
        
        # 测试截图
        screenshots_dir = Path("logs/screenshots")
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = screenshots_dir / f"test_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        driver.save_screenshot(str(screenshot_path))
        test_result["screenshot"] = True
        logger.info(f"✅ 截图成功保存至: {screenshot_path}")
        print(f"✅ 截图成功保存至: {screenshot_path}")
        
    except Exception as e:
        logger.error(f"❌ Edge浏览器测试失败: {e}")
        print(f"❌ Edge浏览器测试失败: {e}")
    finally:
        if driver:
            driver.quit()
            logger.info("浏览器已关闭")
    
    return test_result

def check_permissions():
    """检查文件和目录权限"""
    print_header("权限检查")
    
    permission_info = {}
    
    # 检查目录权限
    dirs_to_check = ["output", "cookies", "logs"]
    for dir_name in dirs_to_check:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 测试写入权限
        test_file = dir_path / "permission_test.txt"
        can_write = False
        
        try:
            with open(test_file, 'w') as f:
                f.write("Permission test")
            can_write = True
            test_file.unlink()  # 删除测试文件
        except Exception as e:
            logger.error(f"无法写入目录 {dir_name}: {e}")
        
        permission_info[dir_name] = can_write
        
        if can_write:
            logger.info(f"✅ 目录 {dir_name} 具有写入权限")
            print(f"✅ 目录 {dir_name} 具有写入权限")
        else:
            logger.warning(f"❌ 目录 {dir_name} 没有写入权限")
            print(f"❌ 目录 {dir_name} 没有写入权限")
    
    return permission_info

def run_diagnostics():
    """运行所有诊断测试"""
    start_time = time.time()
    
    print_header("Edge爬虫诊断工具")
    print("此工具将帮助诊断和修复Windows环境下Edge爬虫的常见问题")
    print(f"诊断日志将保存至: {log_file}\n")
    
    # 收集所有诊断结果
    results = {}
    
    # 运行诊断测试
    results["system_info"] = check_system_info()
    results["edge_browser"] = check_edge_browser()
    results["python_packages"] = check_python_packages()
    results["project_structure"] = check_project_structure()
    results["webdriver"] = check_webdriver()
    results["permissions"] = check_permissions()
    
    # 询问是否进行Selenium测试
    print("\n是否进行Selenium和Edge浏览器测试? 这将启动浏览器进行测试。")
    choice = input("运行测试? (y/n): ")
    if choice.lower() == 'y':
        results["selenium_test"] = test_selenium_edge()
    
    # 保存诊断结果
    results_file = log_dir / f"edge_diagnosis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"诊断结果已保存至: {results_file}")
        print(f"\n诊断结果已保存至: {results_file}")
    except Exception as e:
        logger.error(f"保存诊断结果时出错: {e}")
    
    # 诊断总结
    print_header("诊断总结")
    
    # 检查是否有问题
    has_problems = False
    
    # Edge浏览器检查
    if not results["edge_browser"]["已安装"]:
        has_problems = True
        print("❌ 未检测到Microsoft Edge浏览器")
        print("   解决方案: 安装Microsoft Edge浏览器")
    
    # Python包检查
    missing_packages = [pkg for pkg, info in results["python_packages"].items() 
                       if isinstance(info, dict) and not info.get("已安装", True)]
    if missing_packages:
        has_problems = True
        print(f"❌ 缺少必要的Python包: {', '.join(missing_packages)}")
        print(f"   解决方案: pip install {' '.join(missing_packages)}")
    
    # 项目结构检查
    missing_files = [file for file, exists in results["project_structure"]["files"].items() if not exists]
    if missing_files:
        has_problems = True
        print(f"❌ 缺少必要的文件: {', '.join(missing_files)}")
        print("   解决方案: 重新下载或恢复这些文件")
    
    # WebDriver检查
    if not results["webdriver"].get("edge_driver", False):
        has_problems = True
        print("❌ Edge驱动未安装或安装失败")
        print("   解决方案: 安装webdriver-manager或手动下载Edge驱动")
    
    # 权限检查
    permission_issues = [dir_name for dir_name, has_perm in results["permissions"].items() if not has_perm]
    if permission_issues:
        has_problems = True
        print(f"❌ 目录权限问题: {', '.join(permission_issues)}")
        print("   解决方案: 检查这些目录的写入权限")
    
    if not has_problems:
        print("✅ 未检测到明显问题，Edge爬虫应该可以正常工作")
    
    # 显示诊断用时
    elapsed_time = time.time() - start_time
    print(f"\n诊断完成，用时: {elapsed_time:.2f}秒")
    print(f"详细日志已保存至: {log_file}")

if __name__ == "__main__":
    run_diagnostics() 