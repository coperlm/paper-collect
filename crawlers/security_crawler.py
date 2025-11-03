"""
四大安全会议爬虫 - USENIX Security, NDSS, IEEE S&P, CCS
从官方网站HTML页面提取论文信息
"""
import logging
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from crawlers.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class SecurityCrawler(BaseCrawler):
    """四大安全会议爬虫"""
    
    # 会议URL模板
    CONFERENCE_URLS = {
        'USENIX Security': 'https://www.usenix.org/conference/usenixsecurity{year}/technical-sessions',
        'NDSS': 'https://www.ndss-symposium.org/ndss{year}/accepted-papers/',
        'IEEE S&P': 'https://www.ieee-security.org/TC/SP{year}/program-papers.html',
        'CCS': 'https://www.sigsac.org/ccs/CCS{year}/accepted-papers.html'
    }
    
    # 特殊年份的URL映射（某些年份URL格式不同）
    SPECIAL_URLS = {
        ('USENIX Security', 2025): 'https://www.usenix.org/conference/usenixsecurity25/technical-sessions',
        # CCS 2025的accepted papers页面尚未发布（截至2025年11月）
    }
    
    def __init__(self, config: Dict[str, Any]):
        """初始化爬虫"""
        super().__init__(config)
    
    def crawl(self, conference: str, year: int) -> List[Dict[str, Any]]:
        """
        爬取指定会议的论文
        
        Args:
            conference: 会议名称 (USENIX Security, NDSS, IEEE S&P, CCS)
            year: 年份
            
        Returns:
            论文列表
        """
        if conference not in self.CONFERENCE_URLS:
            logger.error(f"不支持的会议: {conference}")
            return []
        
        # 首先检查是否有特殊URL
        url_key = (conference, year)
        if url_key in self.SPECIAL_URLS:
            url = self.SPECIAL_URLS[url_key]
        else:
            url_template = self.CONFERENCE_URLS[conference]
            # 对于不同年份的会议，URL格式可能不同
            if year < 2025:
                # 2025之前的会议可能使用简短的年份格式
                url = url_template.format(year=str(year)[-2:])
            else:
                url = url_template.format(year=year)
        
        logger.info(f"爬取 {conference} {year} 从 {url}")
        
        try:
            html_content = self._fetch_url(url)
            if not html_content:
                logger.warning(f"无法获取 {conference} {year} 的页面内容")
                return []
            
            # 根据不同会议使用不同的解析方法
            if conference == 'USENIX Security':
                papers = self._parse_usenix_security(html_content, year)
            elif conference == 'NDSS':
                papers = self._parse_ndss(html_content, year)
            elif conference == 'IEEE S&P':
                papers = self._parse_ieee_sp(html_content, year)
            elif conference == 'CCS':
                papers = self._parse_ccs(html_content, year)
            else:
                papers = []
            
            logger.info(f"从 {conference} {year} 获取 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            logger.error(f"爬取 {conference} {year} 时出错: {e}")
            return []
    
    def _parse_usenix_security(self, html: str, year: int) -> List[Dict[str, Any]]:
        """解析USENIX Security页面"""
        soup = BeautifulSoup(html, 'html.parser')
        papers = []
        
        # USENIX的论文通常在<h2>标签中，链接在<a>标签中
        for heading in soup.find_all('h2'):
            link = heading.find('a')
            if not link:
                continue
            
            title = link.get_text(strip=True)
            paper_url = link.get('href', '')
            if paper_url and not paper_url.startswith('http'):
                paper_url = 'https://www.usenix.org' + paper_url
            
            # 查找作者信息（通常在标题下方）
            next_elem = heading.find_next_sibling()
            authors = ''
            if next_elem:
                authors_text = next_elem.get_text(strip=True)
                # 清理作者信息，移除"Short Presentation"等标记
                authors = re.sub(r'Short Presentation.*$', '', authors_text, flags=re.IGNORECASE)
                authors = re.sub(r'Distinguished Paper.*$', '', authors, flags=re.IGNORECASE)
                authors = authors.strip()
            
            paper = {
                'title': title,
                'authors': authors,
                'conference': 'USENIX Security',
                'year': year,
                'url': paper_url,
                'abstract': '',  # USENIX页面通常不包含摘要
                'doi': '',
                'pdf_url': paper_url  # 论文URL通常就是PDF链接
            }
            papers.append(paper)
        
        return papers
    
    def _parse_ndss(self, html: str, year: int) -> List[Dict[str, Any]]:
        """解析NDSS页面"""
        soup = BeautifulSoup(html, 'html.parser')
        papers = []
        
        # NDSS的论文在<h3>标签中
        for heading in soup.find_all('h3'):
            title_text = heading.get_text(strip=True)
            
            # 查找论文链接
            paper_link = heading.find_next('a', string='More Details')
            paper_url = ''
            if paper_link:
                paper_url = paper_link.get('href', '')
                if paper_url and not paper_url.startswith('http'):
                    paper_url = 'https://www.ndss-symposium.org' + paper_url
            
            # 查找作者信息（通常在标题下方的段落中）
            next_p = heading.find_next('p')
            authors = ''
            if next_p:
                authors = next_p.get_text(strip=True)
            
            paper = {
                'title': title_text,
                'authors': authors,
                'conference': 'NDSS',
                'year': year,
                'url': paper_url,
                'abstract': '',
                'doi': '',
                'pdf_url': ''
            }
            papers.append(paper)
        
        return papers
    
    def _parse_ieee_sp(self, html: str, year: int) -> List[Dict[str, Any]]:
        """解析IEEE S&P页面"""
        soup = BeautifulSoup(html, 'html.parser')
        papers = []
        
        # IEEE S&P的论文标题在<b>标签中（不是<strong>）
        # 标题和作者信息都在同一个div中
        bold_tags = soup.find_all('b')
        
        for b in bold_tags:
            title = b.get_text(strip=True)
            
            # 跳过太短的文本（可能是标题或导航）
            if len(title) < 10:
                continue
            
            # 获取作者信息（在同一个父元素中）
            parent = b.parent
            parent_text = parent.get_text(strip=True)
            # 从父元素文本中移除标题，剩下的就是作者
            authors = parent_text.replace(title, '', 1).strip()
            
            paper = {
                'title': title,
                'authors': authors,
                'conference': 'IEEE S&P',
                'year': year,
                'url': f'https://www.ieee-security.org/TC/SP{year}/',
                'abstract': '',
                'doi': '',
                'pdf_url': ''
            }
            papers.append(paper)
        
        return papers
    
    def _parse_ccs(self, html: str, year: int) -> List[Dict[str, Any]]:
        """解析CCS页面"""
        soup = BeautifulSoup(html, 'html.parser')
        papers = []
        
        # CCS的论文格式类似NDSS
        for item in soup.find_all(['div', 'li'], class_=re.compile(r'paper|publication', re.I)):
            title_elem = item.find(['h1', 'h2', 'h3', 'h4'])
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            
            # 查找作者
            authors = ''
            author_elem = item.find(class_=re.compile(r'author', re.I))
            if not author_elem:
                # 尝试在下一个段落中找作者
                next_p = title_elem.find_next(['p', 'span'])
                if next_p:
                    authors = next_p.get_text(strip=True)
            else:
                authors = author_elem.get_text(strip=True)
            
            # 查找链接
            link = item.find('a')
            paper_url = ''
            if link:
                paper_url = link.get('href', '')
                if paper_url and not paper_url.startswith('http'):
                    paper_url = 'https://www.sigsac.org' + paper_url
            
            paper = {
                'title': title,
                'authors': authors,
                'conference': 'CCS',
                'year': year,
                'url': paper_url,
                'abstract': '',
                'doi': '',
                'pdf_url': ''
            }
            papers.append(paper)
        
        return papers
