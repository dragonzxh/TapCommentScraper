#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
统一爬虫运行入口 - 用于启动不同的爬虫
"""

import os
import sys
import argparse
import logging

# 确保logs目录存在
os.makedirs("logs", exist_ok=True)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", "crawler.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CrawlerLauncher")

def run_steam_crawler(args, existing_driver=None):
    """运行Steam爬虫
    
    Args:
        args: 命令行参数
        existing_driver: 已创建的WebDriver实例，如果提供则直接使用
    """
    try:
        from steam_crawler import SteamCrawler, JsonDataWriter
        
        logger.info("启动Steam爬虫...")
        
        # 初始化数据写入器
        data_writer = JsonDataWriter()
        
        # 初始化爬虫
        crawler = SteamCrawler(
            use_headless=args.headless, 
            data_writer=data_writer,
            existing_driver=existing_driver
        )
        
        # 运行爬虫
        crawler.run(args.url)
        
        logger.info("Steam爬虫任务完成")
        return True
    except Exception as e:
        logger.error(f"运行Steam爬虫出错: {e}")
        return False

def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description='统一爬虫运行入口')
    subparsers = parser.add_subparsers(dest='crawler', help='选择要运行的爬虫')
    
    # Steam爬虫参数
    steam_parser = subparsers.add_parser('steam', help='Steam评论爬虫')
    steam_parser.add_argument('--url', type=str, help='要爬取的游戏URL')
    steam_parser.add_argument('--headless', action='store_true', help='使用无头模式')
    steam_parser.add_argument('--max-reviews', type=int, default=None, help='最大爬取评论数')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 如果没有指定爬虫类型，显示帮助
    if not args.crawler:
        parser.print_help()
        return
    
    # 根据爬虫类型运行相应的爬虫
    if args.crawler == 'steam':
        # 先进行年龄验证处理
        driver = None
        if args.url:
            try:
                from age_verification import handle_age_verification_for_game
                logger.info("正在启动爬虫...")
                logger.info("正在准备steam爬虫...")
                logger.info("服务器状态：初始化爬虫环境")
                
                logger.info("正在导入Steam爬虫模块...")
                logger.info("服务器状态：加载Steam爬虫依赖")
                
                # 从URL提取游戏ID
                import re
                game_id = None
                app_id_match = re.search(r'/app/(\d+)', args.url)
                if app_id_match:
                    game_id = app_id_match.group(1)
                else:
                    # 尝试直接作为ID处理
                    if args.url.isdigit():
                        game_id = args.url
                
                if game_id:
                    logger.info(f"提取的游戏ID: {game_id}")
                
                    # 1. 处理年龄验证
                    logger.info("1. 检查登录状态和处理年龄验证...")
                    logger.info("服务器状态：准备验证流程")
                    
                    logger.info("2. 设置浏览器实例...")
                    logger.info("3. 加载已保存的cookies...")
                    logger.info("3.1 验证cookies是否正确加载...")
                    logger.info(f"4. 处理游戏 {game_id} 的年龄验证...")
                    
                    # 进行年龄验证
                    verification_success, driver = handle_age_verification_for_game(
                        game_id, 
                        use_headless=args.headless
                    )
                    
                    if verification_success:
                        logger.info("✅ 年龄验证处理成功")
                        logger.info("5. 保存最新cookies...")
                        logger.info("6. 继续使用当前浏览器实例进行爬取...")
                        
                        # 运行爬虫，传递已创建的driver
                        logger.info("正在初始化爬虫...")
                        logger.info("服务器状态：准备爬虫实例")
                        logger.info("使用已创建的浏览器实例...")
                        
                        run_steam_crawler(args, existing_driver=driver)
                    else:
                        logger.error("年龄验证处理失败，无法继续爬取")
                        logger.info("服务器状态：爬虫启动失败，请检查年龄验证")
                else:
                    logger.error(f"无法从URL中提取游戏ID: {args.url}")
                    logger.info("服务器状态：爬虫启动失败，无效的游戏URL")
            except Exception as e:
                logger.error(f"爬虫运行出错: {e}")
                logger.info("服务器状态：爬虫启动失败，请检查系统环境")
            finally:
                # 确保关闭driver
                if driver:
                    try:
                        driver.quit()
                        logger.info("浏览器实例已关闭")
                    except:
                        pass
                logger.info("爬虫任务结束")
        else:
            # 没有提供URL，直接运行爬虫
            run_steam_crawler(args)
    else:
        logger.error(f"未知的爬虫类型: {args.crawler}")

if __name__ == "__main__":
    main() 