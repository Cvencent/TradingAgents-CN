"""
东方财富股吧热门帖子爬虫 - Markdown输出版
爬取热门列表前20条，获取正文内容，输出Markdown格式
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import re
from datetime import datetime
import sys

class GubaHotCrawler:
    """东方财富股吧热门帖子爬虫 - Markdown输出版"""
    
    def __init__(self, stock_code):
        self.stock_code = stock_code
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        self.results = []
    
    def crawl_hot_list(self, max_posts=20):
        """
        爬取热门帖子列表前N条
        URL格式: https://guba.eastmoney.com/list,{stock_code},99.html
        """
        print(f"开始爬取股票 {self.stock_code} 的热门帖子...")
        print(f"目标URL: https://guba.eastmoney.com/list,{self.stock_code},99.html\n")
        
        url = f'https://guba.eastmoney.com/list,{self.stock_code},99.html'
        
        try:
            print(f"正在获取热门列表...")
            
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.encoding = 'utf-8'
            
            if resp.status_code != 200:
                print(f"页面返回状态码: {resp.status_code}")
                return []
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 查找所有帖子链接（热门列表使用caifuhao.eastmoney.com域名）
            hot_links = soup.find_all('a', href=re.compile(r'//caifuhao\.eastmoney\.com/news/\d+'))
            
            count = 0
            for link in hot_links[:max_posts]:  # 只取前N条
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
                            '股票代码': self.stock_code,
                            '帖子ID': post_id,
                            '标题': title,
                            '链接': full_link,
                            '阅读数': read_num,
                            '评论数': comment_num,
                            '作者': author,
                            '最后更新': update_time,
                            '正文': '',  # 稍后填充
                            '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        count += 1
                        
                except Exception as e:
                    continue
            
            print(f"[OK] 获取 {count} 条热门帖子列表\n")
            
        except Exception as e:
            print(f"[ERROR] 获取列表失败: {e}")
            return []
        
        # 去重
        seen_ids = set()
        unique_results = []
        for item in self.results:
            if item['帖子ID'] and item['帖子ID'] not in seen_ids:
                seen_ids.add(item['帖子ID'])
                unique_results.append(item)
        
        self.results = unique_results[:max_posts]  # 确保最多max_posts条
        
        # 获取每条帖子的正文内容
        print(f"开始获取 {len(self.results)} 条帖子的正文内容...")
        for i, item in enumerate(self.results, 1):
            try:
                print(f"  [{i}/{len(self.results)}] 获取正文: {item['标题'][:30]}...")
                content = self.fetch_post_content(item['链接'])
                item['正文'] = content
                
                # 延时，避免请求过快
                if i < len(self.results):
                    delay = random.uniform(1, 2)
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"    [ERROR] 获取正文失败: {e}")
                item['正文'] = '(获取正文失败)'
                continue
        
        print(f"\n[OK] 爬取完成！共获取 {len(self.results)} 条热门帖子（含正文）\n")
        return self.results
    
    def clean_content(self, text):
        """
        清理正文内容，删除免责声明等无关信息
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
    
    def fetch_post_content(self, url):
        """
        获取帖子详情页的正文内容（已清理免责声明）
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
                elem = soup.select_one(tag)
                if elem:
                    text = elem.get_text(separator='\n', strip=True)
                    if len(text) > 50:
                        return self.clean_content(text)
            
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
            return f'(获取正文出错: {str(e)})'
    
    def generate_markdown(self):
        """
        生成Markdown格式输出
        """
        if not self.results:
            return "# 错误\n\n没有获取到任何数据"
        
        md_lines = []
        
        # 标题
        md_lines.append(f"# 股票 {self.stock_code} 热门帖子舆情数据")
        md_lines.append(f"\n> 数据来源：东方财富股吧热门讨论")
        md_lines.append(f"> 爬取时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md_lines.append(f"> 帖子数量：{len(self.results)} 条\n")
        
        # 帖子汇总表格
        md_lines.append("## 帖子汇总\n")
        md_lines.append("| 序号 | 标题 | 作者 | 阅读 | 评论 | 更新时间 |")
        md_lines.append("|------|------|------|------|------|----------|")
        
        for i, item in enumerate(self.results, 1):
            title = item['标题'][:35] + '...' if len(item['标题']) > 35 else item['标题']
            author = item['作者'][:10]
            read_num = item['阅读数']
            comment_num = item['评论数']
            update_time = item['最后更新']
            
            md_lines.append(f"| {i} | {title} | {author} | {read_num} | {comment_num} | {update_time} |")
        
        md_lines.append("")
        
        # 详细内容
        md_lines.append("## 详细内容\n")
        
        for i, item in enumerate(self.results, 1):
            md_lines.append(f"### {i}. {item['标题']}\n")
            md_lines.append(f"- **作者**：{item['作者']}")
            md_lines.append(f"- **阅读数**：{item['阅读数']}")
            md_lines.append(f"- **评论数**：{item['评论数']}")
            md_lines.append(f"- **更新时间**：{item['最后更新']}")
            md_lines.append(f"- **链接**：[查看原帖]({item['链接']})\n")
            
            md_lines.append("**正文内容**：\n")
            md_lines.append(f"```\n{item['正文']}\n```\n")
            md_lines.append("---\n")
        
        return '\n'.join(md_lines)
    
    def save_markdown(self, filename=None):
        """
        保存Markdown到文件
        """
        if not filename:
            filename = f'guba_hot_{self.stock_code}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        
        md_content = self.generate_markdown()
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"[OK] Markdown文件已保存: {filename}")
            return filename
        except Exception as e:
            print(f"[ERROR] 保存文件失败: {e}")
            return None
    
    def show_summary(self):
        """显示结果摘要"""
        if not self.results:
            print("没有数据")
            return
            
        print(f"\n{'='*70}")
        print(f"共获取 {len(self.results)} 条热门帖子")
        print(f"{'='*70}\n")
        
        for i, item in enumerate(self.results, 1):
            print(f"{i}. {item['标题'][:50]}")
            print(f"   阅读:{item['阅读数']} 评论:{item['评论数']} 作者:{item['作者']}")
            # 显示正文前100字预览
            preview = item['正文'][:100].replace('\n', ' ')
            print(f"   正文预览: {preview}...")
            print()


def main():
    """主函数"""
    stock_code = '600519'  # 默认茅台
    
    if len(sys.argv) > 1:
        stock_code = sys.argv[1]
    
    print(f"\n{'='*70}")
    print(f"东方财富股吧热门帖子爬虫 - Markdown版")
    print(f"{'='*70}\n")
    
    crawler = GubaHotCrawler(stock_code)
    crawler.crawl_hot_list(max_posts=20)
    crawler.show_summary()
    
    # 保存为Markdown
    md_file = crawler.save_markdown()
    
    # 同时输出Markdown内容到控制台（前2000字符）
    print(f"\n{'='*70}")
    print("Markdown内容预览（前2000字符）：")
    print(f"{'='*70}\n")
    md_content = crawler.generate_markdown()
    print(md_content[:2000])
    print("\n... [内容已截断，完整内容请查看文件] ...\n")
    
    print(f"{'='*70}")
    print("完成!")
    if md_file:
        print(f"Markdown文件: {md_file}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
