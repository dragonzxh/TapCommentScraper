from steam_crawler import SteamCrawler

def test_steam():
    """测试Steam评论爬虫"""
    try:
        # 创建爬虫实例（非无头模式便于观察）
        crawler = SteamCrawler(use_headless=False)
        
        try:
            # 如果Cookie验证失败才要求输入用户名密码
            if not crawler.is_logged_in:
                print("Cookie验证失败，需要重新登录")
                username = input("请输入Steam用户名: ")
                password = input("请输入Steam密码: ")
                
                if not crawler.login(username, password):
                    print("登录失败，程序退出")
                    return
            
            # 测试评论提取
            test_url = "https://steamcommunity.com/app/1295660/reviews/?browsefilter=toprated&snr=1_5_100010_&filterLanguage=schinese"
            crawler.extract_comments(test_url)
            
        except Exception as e:
            print(f"爬取过程中出错: {e}")
        finally:
            # 确保关闭浏览器
            crawler.close()
            
    except Exception as e:
        print(f"程序运行时出错: {e}")

if __name__ == "__main__":
    test_steam() 