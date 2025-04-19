from src.crawlers.taptap import TapTapCrawler

def test_content():
    """测试评论内容提取"""
    game_id = "84463"  # 更新为正确的游戏ID
    
    with TapTapCrawler(headless=False) as crawler:  # 使用有头模式以便观察
        crawler.test_content_extraction(game_id)

if __name__ == "__main__":
    test_content() 