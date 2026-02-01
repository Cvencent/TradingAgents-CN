"""
东方财富股吧热门帖子爬虫
用于社媒分析师获取A股论坛讨论数据
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import re
from datetime import datetime
from typing import List, Dict, Optional

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("dataflows.guba_crawler")


class GubaHotCrawler:
    """东方财富股吧热门帖子爬虫"""

    def __init__(self, stock_code: str):
        self.stock_code = stock_code
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        self.results = []

    def crawl_hot_list(self, max_posts: int = 20) -> List[Dict]:
        """
        爬取热门帖子列表前N条

        Args:
            max_posts: 最大获取帖子数量

        Returns:
            List[Dict]: 帖子列表，每个帖子包含标题、作者、阅读数、评论数、更新时间、正文等
        """
        logger.info(f"🕷️ [股吧爬虫] 开始爬取股票 {self.stock_code} 的热门帖子...")

        url = f'https://guba.eastmoney.com/list,{self.stock_code},99.html'

        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.encoding = 'utf-8'

            if resp.status_code != 200:
                logger.warning(f"⚠️ [股吧爬虫] 页面返回状态码: {resp.status_code}")
                return []

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 查找所有帖子链接（热门列表使用caifuhao.eastmoney.com域名）
            hot_links = soup.find_all('a', href=re.compile(r'//caifuhao\.eastmoney\.com/news/\d+'))

            count = 0
            for link in hot_links[:max_posts]:
                try:
                    title = link.text.strip()
                    href = link.get('href', '')

                    if not title or not href:
                        continue

                    # 获取data-postid作为ID
                    post_id = link.get('data-postid', '')

                    # 提取阅读数和评论数（从父级tr元素）
                    parent_tr = link.find_parent('tr')
                    read_num = ''
                    comment_num = ''
                    author = ''
                    update_time = ''

                    if parent_tr:
                        # 查找所有td
                        tds = parent_tr.find_all('td')
                        if len(tds) >= 5:
                            read_num = tds[0].text.strip()
                            comment_num = tds[1].text.strip()
                            author_elem = tds[3].find('a')
                            if author_elem:
                                author = author_elem.text.strip()
                            update_time = tds[4].text.strip()

                    # 构建完整链接
                    full_link = href if href.startswith('http') else f'https:{href}'

                    if title:
                        self.results.append({
                            'stock_code': self.stock_code,
                            'post_id': post_id,
                            'title': title,
                            'link': full_link,
                            'read_count': read_num,
                            'comment_count': comment_num,
                            'author': author,
                            'update_time': update_time,
                            'content': '',  # 稍后填充
                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        count += 1

                except Exception as e:
                    logger.debug(f"⚠️ [股吧爬虫] 解析帖子链接失败: {e}")
                    continue

            logger.info(f"✅ [股吧爬虫] 获取 {count} 条热门帖子列表")

        except Exception as e:
            logger.error(f"❌ [股吧爬虫] 获取列表失败: {e}")
            return []

        # 去重
        seen_ids = set()
        unique_results = []
        for item in self.results:
            if item['post_id'] and item['post_id'] not in seen_ids:
                seen_ids.add(item['post_id'])
                unique_results.append(item)

        self.results = unique_results[:max_posts]

        # 获取每条帖子的正文内容
        logger.info(f"🕷️ [股吧爬虫] 开始获取 {len(self.results)} 条帖子的正文内容...")
        for i, item in enumerate(self.results, 1):
            try:
                content = self.fetch_post_content(item['link'])
                item['content'] = content

                # 延时，避免请求过快
                if i < len(self.results):
                    delay = random.uniform(0.5, 1.5)
                    time.sleep(delay)

            except Exception as e:
                logger.debug(f"⚠️ [股吧爬虫] 获取正文失败: {e}")
                item['content'] = '(获取正文失败)'
                continue

        logger.info(f"✅ [股吧爬虫] 爬取完成！共获取 {len(self.results)} 条热门帖子（含正文）")
        return self.results

    def clean_content(self, text: str) -> str:
        """
        清理正文内容，删除免责声明等无关信息

        Args:
            text: 原始正文内容

        Returns:
            str: 清理后的内容
        """
        if not text:
            return text

        # 定义免责声明的关键标识（按优先级排序）
        disclaimer_patterns = [
            r'追加内容.*',  # 删除"追加内容"及之后的内容
            r'举报郑重声明.*',  # 删除"举报郑重声明"及之后的内容
            r'郑重声明：.*',  # 删除"郑重声明"及之后的内容
            r'免责声明.*',  # 删除"免责声明"及之后的内容
            r'用户在社区发表的所有信息.*',  # 删除用户声明及之后的内容
            r'请勿相信代客理财.*',  # 删除风险提示及之后的内容
            r'请勿添加发言用户的手机号码.*',  # 删除防骗提示及之后的内容
        ]

        # 逐个模式进行清理
        for pattern in disclaimer_patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

        # 清理多余空行和首尾空白
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = text.strip()

        return text

    def fetch_post_content(self, url: str) -> str:
        """
        获取帖子详情页的正文内容

        Args:
            url: 帖子详情页URL

        Returns:
            str: 帖子正文内容
        """
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.encoding = 'utf-8'

            if resp.status_code != 200:
                return '(页面访问失败)'

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 尝试多种选择器获取正文
            text = None

            # 方法1: 查找data-postid属性的div
            content_div = soup.find('div', {'data-postid': True})
            if content_div:
                text = content_div.get_text(separator='\n', strip=True)
                if len(text) > 10:
                    return self.clean_content(text)

            # 方法2: 查找article或main标签
            for tag in ['article', 'main', '[class*="content"]', '[class*="post"]']:
                try:
                    elem = soup.select_one(tag)
                    if elem:
                        text = elem.get_text(separator='\n', strip=True)
                        if len(text) > 50:
                            return self.clean_content(text)
                except Exception:
                    continue

            # 方法3: 查找最长的文本段落
            paragraphs = soup.find_all('p')
            if paragraphs:
                longest = max(paragraphs, key=lambda p: len(p.get_text(strip=True)))
                text = longest.get_text(separator='\n', strip=True)
                if len(text) > 20:
                    return self.clean_content(text)

            # 方法4: 返回页面中所有文本
            body = soup.find('body')
            if body:
                # 移除脚本和样式
                for script in body(['script', 'style']):
                    script.decompose()
                text = body.get_text(separator='\n', strip=True)
                # 清理多余空行
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                full_text = '\n'.join(lines[:50])  # 限制长度
                return self.clean_content(full_text)

            return '(未能提取正文)'

        except Exception as e:
            logger.debug(f"⚠️ [股吧爬虫] 获取正文出错: {e}")
            return f'(获取正文出错)'

    def generate_markdown_report(self) -> str:
        """
        生成Markdown格式报告

        Returns:
            str: Markdown格式的股吧讨论报告
        """
        if not self.results:
            return "## 东方财富股吧讨论\n\n暂无数据"

        md_lines = []

        # 标题
        md_lines.append(f"## 东方财富股吧热门讨论 - {self.stock_code}")
        md_lines.append(f"\n> 数据来源：东方财富股吧热门讨论")
        md_lines.append(f"> 爬取时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md_lines.append(f"> 帖子数量：{len(self.results)} 条\n")

        # 帖子汇总表格
        md_lines.append("### 帖子汇总\n")
        md_lines.append("| 序号 | 标题 | 作者 | 阅读 | 评论 | 更新时间 |")
        md_lines.append("|------|------|------|------|------|----------|")

        for i, item in enumerate(self.results, 1):
            title = item['title'][:35] + '...' if len(item['title']) > 35 else item['title']
            author = item['author'][:10] if item['author'] else '-'
            read_num = item['read_count'] or '-'
            comment_num = item['comment_count'] or '-'
            update_time = item['update_time'] or '-'

            md_lines.append(f"| {i} | {title} | {author} | {read_num} | {comment_num} | {update_time} |")

        md_lines.append("")

        # 详细内容
        md_lines.append("### 详细内容\n")

        for i, item in enumerate(self.results, 1):
            md_lines.append(f"#### {i}. {item['title']}\n")
            md_lines.append(f"- **作者**：{item['author'] or '未知'}")
            md_lines.append(f"- **阅读数**：{item['read_count'] or '未知'}")
            md_lines.append(f"- **评论数**：{item['comment_count'] or '未知'}")
            md_lines.append(f"- **更新时间**：{item['update_time'] or '未知'}")
            md_lines.append(f"- **链接**：[查看原帖]({item['link']})\n")

            md_lines.append("**正文内容**：\n")
            content = item['content'] or '(无正文)'
            md_lines.append(f"> {content[:500]}{'...' if len(content) > 500 else ''}\n")
            md_lines.append("---\n")

        return '\n'.join(md_lines)

    def generate_sentiment_summary(self) -> Dict:
        """
        生成情绪分析汇总数据

        Returns:
            Dict: 情绪分析数据字典
        """
        if not self.results:
            return {
                'sentiment_score': 0,
                'discussion_count': 0,
                'hot_topics': [],
                'confidence': 0,
                'summary': '暂无数据'
            }

        # 简单的情绪分析（基于关键词）
        positive_keywords = ['涨', '牛', '看好', '买入', '加仓', '突破', '利好', '强势', '反弹']
        negative_keywords = ['跌', '熊', '看空', '卖出', '减仓', '跌破', '利空', '弱势', '下跌']

        positive_count = 0
        negative_count = 0
        neutral_count = 0
        hot_topics = []

        for post in self.results:
            title = post.get('title', '')
            content = post.get('content', '')
            full_text = f"{title} {content}"

            # 提取热门话题（前5个标题）
            if title and len(hot_topics) < 5:
                hot_topics.append(title)

            # 简单情绪判断
            pos_score = sum(1 for kw in positive_keywords if kw in full_text)
            neg_score = sum(1 for kw in negative_keywords if kw in full_text)

            if pos_score > neg_score:
                positive_count += 1
            elif neg_score > pos_score:
                negative_count += 1
            else:
                neutral_count += 1

        total = len(self.results)
        sentiment_score = (positive_count - negative_count) / total if total > 0 else 0
        confidence = min(total / 10, 1.0)

        # 生成汇总文本
        if sentiment_score > 0.2:
            summary = f"股吧讨论整体偏乐观，{positive_count}/{total} 条帖子表达积极情绪"
        elif sentiment_score < -0.2:
            summary = f"股吧讨论整体偏悲观，{negative_count}/{total} 条帖子表达消极情绪"
        else:
            summary = f"股吧讨论情绪中性，积极{positive_count}条、消极{negative_count}条、中性{neutral_count}条"

        return {
            'sentiment_score': sentiment_score,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'discussion_count': total,
            'hot_topics': hot_topics,
            'confidence': confidence,
            'summary': summary
        }


def get_guba_posts(stock_code: str, max_posts: int = 20) -> List[Dict]:
    """
    获取东方财富股吧帖子（对外接口）

    Args:
        stock_code: 股票代码
        max_posts: 最大获取帖子数量

    Returns:
        List[Dict]: 帖子列表
    """
    try:
        crawler = GubaHotCrawler(stock_code)
        return crawler.crawl_hot_list(max_posts=max_posts)
    except Exception as e:
        logger.error(f"❌ [股吧爬虫] 获取帖子失败: {e}")
        return []


def get_guba_sentiment_report(stock_code: str, max_posts: int = 20) -> str:
    """
    获取东方财富股吧情绪分析报告（对外接口）

    Args:
        stock_code: 股票代码
        max_posts: 最大获取帖子数量

    Returns:
        str: Markdown格式的情绪分析报告
    """
    try:
        crawler = GubaHotCrawler(stock_code)
        posts = crawler.crawl_hot_list(max_posts=max_posts)

        if not posts:
            return f"## 东方财富股吧讨论 - {stock_code}\n\n暂无数据"

        return crawler.generate_markdown_report()
    except Exception as e:
        logger.error(f"❌ [股吧爬虫] 生成报告失败: {e}")
        return f"## 东方财富股吧讨论 - {stock_code}\n\n获取数据失败: {str(e)}"
