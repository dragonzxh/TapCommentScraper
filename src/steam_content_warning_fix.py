#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Steam 内容警告处理模块 - 专门处理Steam评论页面的暴力色情内容警告
可以直接应用到现有的 steam_crawler.py 中
"""

import logging
import time
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# 设置日志
logger = logging.getLogger("SteamCrawler")

def is_content_warning_page(driver):
    """检查当前是否在暴力色情内容警告页面
    
    Args:
        driver: WebDriver实例
        
    Returns:
        bool: 是否在内容警告页面
    """
    try:
        page_source = driver.page_source.lower()
        
        # 检查特定的Steam内容警告页面文本，更精确地匹配
        steam_specific_warnings = [
            "this game contains content you have asked not to see",
            "该游戏包含您不希望看到的内容",
            "内容警告",
            "content warning"
        ]
        
        for specific_warning in steam_specific_warnings:
            if specific_warning in page_source:
                logger.info(f"检测到特定的Steam内容警告页面: '{specific_warning}'")
                return True
        
        # 检查是否有View Community Hub按钮，这是内容警告页面的标志之一
        try:
            # 使用JavaScript检测特定按钮
            js_script = """
                var communityHubButton = false;
                // 检查文本内容
                var elements = document.querySelectorAll('a, button');
                for (var i = 0; i < elements.length; i++) {
                    var text = elements[i].textContent.trim().toLowerCase();
                    if (text.includes('view community hub') || 
                        text.includes('浏览社区中心') || 
                        text.includes('浏览社区内容') || 
                        text.includes('community hub')) {
                        return true;
                    }
                }
                return false;
            """
            has_community_hub_button = driver.execute_script(js_script)
            if has_community_hub_button:
                logger.info("通过按钮文本检测到内容警告页面")
                return True
        except Exception as e:
            logger.warning(f"检查View Community Hub按钮失败: {e}")
        
        # 检查常见的内容警告关键词
        content_warning_indicators = [
            "mature content", 
            "adult content",
            "violent content", 
            "sexual content",
            "violent or sexual content",
            "成人内容", 
            "暴力内容", 
            "色情内容",
            "确认年龄",
            "partially nudity",
            "some nudity",
            "sexual content",
            "血腥",
            "暴力",
            "性内容",
            "nudity"
        ]
        
        # 内容警告页面的特征是存在这些关键词和确认按钮
        for indicator in content_warning_indicators:
            if indicator in page_source:
                # 确认页面上有继续按钮或"View Community Hub"按钮
                continue_buttons = driver.find_elements(By.CSS_SELECTOR, 
                    "a.btn_green_white_innerfade, button.btn_green_steamui, " + 
                    ".btnv6_green_white_innerfade, .agecheck_continue_button, " + 
                    "a[href*='communitypage'], a[href*='community'], " + 
                    ".btn_blue_steamui")
                
                if continue_buttons and any(btn.is_displayed() for btn in continue_buttons):
                    logger.info(f"检测到内容警告页面特征: '{indicator}'")
                    return True
                
                # 检查是否有任何可能的确认按钮
                js_button_check = """
                    var possibleButtons = document.querySelectorAll('a, button');
                    for (var i = 0; i < possibleButtons.length; i++) {
                        var btn = possibleButtons[i];
                        var text = btn.textContent.trim().toLowerCase();
                        if ((text.includes('view') || text.includes('continue') || 
                             text.includes('proceed') || text.includes('确认') || 
                             text.includes('继续') || text.includes('浏览') ||
                             text.includes('社区中心')) && 
                            btn.offsetParent !== null) {
                            return true;
                        }
                    }
                    return false;
                """
                has_buttons = driver.execute_script(js_button_check)
                if has_buttons:
                    logger.info(f"通过按钮检测到内容警告页面特征: '{indicator}'")
                    return True
        
        # 检查URL参数是否包含内容警告相关参数
        current_url = driver.current_url.lower()
        if 'mature_content=1' in current_url or 'agecheck=1' in current_url:
            logger.info("URL参数显示这可能是内容警告页面")
            # 额外检查页面内容确认
            if '确认' in page_source or 'confirm' in page_source or 'view' in page_source:
                return True
        
        # 检查是否是简化版移动内容警告页面
        if ('want to update what type of content you see on steam' in page_source or
            '想要更新您在Steam上看到的内容类型' in page_source):
            logger.info("检测到移动版内容警告页面")
            return True
        
        return False
    except Exception as e:
        logger.error(f"检查内容警告页面时出错: {e}")
        return False

def handle_content_warning_page(driver):
    """处理暴力色情内容警告页面
    
    Args:
        driver: WebDriver实例
        
    Returns:
        bool: 是否成功处理
    """
    try:
        logger.info("尝试处理内容警告页面...")
        
        # 直接针对"浏览社区中心"按钮的点击策略
        try:
            # 首先尝试直接查找"浏览社区中心"按钮并点击
            js_target_button = """
                var buttonTexts = ['浏览社区中心', 'View Community Hub'];
                var buttons = document.querySelectorAll('a');
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    var text = btn.textContent.trim();
                    if (buttonTexts.some(t => text.includes(t)) && btn.offsetParent !== null) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            """
            direct_clicked = driver.execute_script(js_target_button)
            if direct_clicked:
                logger.info("成功直接点击'浏览社区中心'按钮")
                time.sleep(3)  # 等待页面加载
                return True
        except Exception as e:
            logger.warning(f"直接点击'浏览社区中心'按钮失败: {e}")
        
        # 更精确的选择器，包含Steam警告页面特有的按钮标识
        specific_selectors = [
            # View Community Hub按钮(浏览社区中心)的选择器
            "a[href*='communitypage']", 
            "a[href*='community']", 
            "a:contains('View Community Hub')", 
            "a:contains('浏览社区中心')",
            "a.view_community_hub", 
            "a.community_hub_btn"
        ]
        
        # 先尝试更精确的选择器
        button_clicked = False
        for selector in specific_selectors:
            try:
                # 使用JavaScript查找元素，解决某些选择器在Selenium中不支持的问题
                js_script = f"""
                    var btns = [];
                    if ('{selector}'.includes(':contains')) {{
                        // 处理:contains选择器
                        var text = '{selector}'.split("'")[1];
                        var elements = document.querySelectorAll('a');
                        for (var i = 0; i < elements.length; i++) {{
                            if (elements[i].textContent.includes(text)) {{
                                btns.push(elements[i]);
                            }}
                        }}
                    }} else {{
                        // 常规选择器
                        btns = document.querySelectorAll('{selector}');
                    }}
                    if (btns.length > 0) {{
                        for (var i = 0; i < btns.length; i++) {{
                            if (btns[i].offsetParent !== null && btns[i].style.display !== 'none') {{
                                btns[i].click();
                                return true;
                            }}
                        }}
                    }}
                    return false;
                """
                button_clicked = driver.execute_script(js_script)
                if button_clicked:
                    logger.info(f"成功通过精确选择器 '{selector}' 点击警告确认按钮")
                    time.sleep(3)  # 等待页面加载
                    break
            except Exception as e:
                logger.warning(f"尝试选择器 '{selector}' 失败: {e}")
        
        # 如果精确选择器未找到，尝试通过页面文本内容查找按钮
        if not button_clicked:
            try:
                # 查找包含特定文本的按钮
                text_keywords = ['View Community Hub', '浏览社区中心', 'Continue', '继续', 'View Page', '查看页面']
                js_find_by_text = """
                    var keywords = arguments[0];
                    var elements = document.querySelectorAll('a, button');
                    for (var i = 0; i < elements.length; i++) {
                        var elem = elements[i];
                        var text = elem.textContent.trim();
                        for (var j = 0; j < keywords.length; j++) {
                            if (text.includes(keywords[j]) && elem.offsetParent !== null) {
                                elem.click();
                                return true;
                            }
                        }
                    }
                    return false;
                """
                button_clicked = driver.execute_script(js_find_by_text, text_keywords)
                if button_clicked:
                    logger.info(f"成功通过文本内容匹配点击警告确认按钮")
                    time.sleep(3)  # 等待页面加载
            except Exception as e:
                logger.warning(f"通过文本内容匹配按钮失败: {e}")
        
        # 如果上述方法都失败，尝试常规的按钮选择器
        if not button_clicked:
            # 尝试点击"查看页面"或"继续"按钮
            continue_buttons = driver.find_elements(By.CSS_SELECTOR, 
                "a.btn_green_white_innerfade, button.btn_green_steamui, .btnv6_green_white_innerfade, .agecheck_continue_button, .btn_blue_steamui")
            
            for button in continue_buttons:
                if button.is_displayed():
                    try:
                        button_text = button.text.strip()
                        logger.info(f"点击内容警告确认按钮: '{button_text}'")
                        driver_js = driver.execute_script
                        driver_js("arguments[0].scrollIntoView(true);", button)
                        time.sleep(1)
                        driver_js("arguments[0].click();", button)
                        button_clicked = True
                        time.sleep(3)  # 等待页面加载
                        break
                    except Exception as e:
                        logger.warning(f"点击按钮 '{button_text}' 时出错: {e}")
        
        # 最后手段：尝试使用更通用的JavaScript方法点击任何可见的按钮
        if not button_clicked:
            logger.info("尝试使用通用JavaScript方法点击内容警告确认按钮...")
            js_script = """
                // 查找所有可点击元素
                var clickables = document.querySelectorAll('a, button, input[type="submit"]');
                // 按照显示顺序排序(通常警告确认按钮会比较突出)
                var visibleButtons = Array.from(clickables).filter(function(el) {
                    return el.offsetParent !== null && 
                           (el.tagName === 'A' || el.tagName === 'BUTTON' || 
                            (el.tagName === 'INPUT' && el.type === 'submit'));
                });
                
                // 按照可能性排序 - 绿色/蓝色按钮优先
                visibleButtons.sort(function(a, b) {
                    var aClass = a.className.toLowerCase();
                    var bClass = b.className.toLowerCase();
                    var aText = a.textContent.toLowerCase();
                    var bText = b.textContent.toLowerCase();
                    
                    // 优先选择含有关键词的按钮
                    var keywords = ['view', 'community', 'hub', 'continue', 'proceed', 'confirm', '浏览', '社区', '中心', '继续', '确认'];
                    var aHasKeyword = keywords.some(k => aText.includes(k));
                    var bHasKeyword = keywords.some(k => bText.includes(k));
                    
                    if (aHasKeyword && !bHasKeyword) return -1;
                    if (!aHasKeyword && bHasKeyword) return 1;
                    
                    // 其次选择绿色/蓝色按钮
                    var aIsColorBtn = aClass.includes('green') || aClass.includes('blue');
                    var bIsColorBtn = bClass.includes('green') || bClass.includes('blue');
                    
                    if (aIsColorBtn && !bIsColorBtn) return -1;
                    if (!aIsColorBtn && bIsColorBtn) return 1;
                    
                    return 0;
                });
                
                // 点击最可能的按钮
                if (visibleButtons.length > 0) {
                    visibleButtons[0].click();
                    return true;
                }
                return false;
            """
            button_clicked = driver.execute_script(js_script)
            
            if button_clicked:
                logger.info("成功使用通用JavaScript方法点击确认按钮")
                time.sleep(3)  # 等待页面加载
            else:
                logger.warning("未能找到可点击的确认按钮")
                
                # 最后尝试：输出页面中所有的链接和按钮文本进行分析
                try:
                    logger.info("分析页面上所有可点击元素...")
                    js_analyze = """
                        var result = [];
                        var elements = document.querySelectorAll('a, button');
                        for (var i = 0; i < elements.length; i++) {
                            var e = elements[i];
                            if (e.offsetParent !== null) {
                                result.push({
                                    tag: e.tagName,
                                    text: e.textContent.trim(),
                                    href: e.href || '',
                                    className: e.className || '',
                                    display: window.getComputedStyle(e).display,
                                    visible: e.offsetWidth > 0 && e.offsetHeight > 0
                                });
                            }
                        }
                        return JSON.stringify(result);
                    """
                    elements_info = driver.execute_script(js_analyze)
                    logger.info(f"页面可点击元素分析: {elements_info}")
                except Exception as e:
                    logger.error(f"分析页面元素失败: {e}")
        
        # 最终检查是否已移出内容警告页面
        if not is_content_warning_page(driver):
            logger.info("成功处理内容警告页面")
            return True
        else:
            # 最后尝试：保存页面截图和HTML以便分析
            try:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"content_warning_page_{timestamp}.png"
                html_path = f"content_warning_page_{timestamp}.html"
                driver.save_screenshot(screenshot_path)
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                logger.warning(f"保存了内容警告页面截图到 {screenshot_path} 和HTML到 {html_path} 以便分析")
            except Exception as e:
                logger.error(f"保存页面信息失败: {e}")
                
            logger.warning("处理内容警告页面失败，仍然在警告页面上")
            return False
            
    except Exception as e:
        logger.error(f"处理内容警告页面时出错: {e}")
        return False

# 如何修改 steam_crawler.py 中的 process_reviews_page 方法:
"""
在 process_reviews_page 方法中的 handle_age_check() 后面添加以下代码:

# 检查是否是暴力色情内容警告页面
if is_content_warning_page(self.driver):
    logger.info("检测到暴力色情内容警告页面，尝试处理...")
    if handle_content_warning_page(self.driver):
        logger.info("成功处理内容警告页面")
    else:
        logger.warning("处理内容警告页面失败，可能需要手动登录再尝试")

另外，在确认是否成功加载评论页面的检查中添加对内容警告页面的检查:

# 检查是否仍在内容警告页面
if is_content_warning_page(self.driver):
    logger.error("仍然处于内容警告页面，无法访问评论")
    logger.info("建议手动登录Steam并确认内容警告后再尝试")
    return 0
"""

# 为什么需要先访问 Steam 主页然后再访问评论页面的说明
"""
为什么需要先访问 Steam 主页再访问评论页面:

1. Cookie 域限制:
   - Steam 的 Cookie 系统是基于域的。当加载 Cookie 时，需要先访问相应的域名
     (如 store.steampowered.com 和 steamcommunity.com) 才能正确设置 Cookie。
   - 这是浏览器的安全机制，不同域的 Cookie 无法直接互相访问。

2. 登录状态验证:
   - Steam 的登录系统比较复杂，有时需要在不同的子域之间同步登录状态。
   - 通过先访问主域，可以确保登录状态在整个 Steam 网站范围内都是有效的。

3. 内容警告处理:
   - 对于含有敏感内容的游戏，Steam 会在未登录状态下显示内容警告页面。
   - 登录后 Steam 会记住您已经确认过这些警告，但这个确认状态需要先在主域名上设置好。

优化方案 - 直接访问评论页面:

如果您确实需要直接访问评论页面，可以按以下流程处理:

1. 先检查是否已登录，如果未登录则:
   a. 先访问 Steam 主页 (https://store.steampowered.com/)
   b. 加载 Cookie
   c. 刷新登录状态

2. 然后直接访问评论页面
3. 处理可能出现的内容警告页面
4. 继续爬取评论

这样就能在尽可能直接访问评论页面的同时，确保登录状态正确传递。
"""
