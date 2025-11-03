"""
DBLP爬虫 - 从DBLP获取论文元数据
"""
import logging
import urllib.parse
from typing import List, Dict, Any, Optional
from crawlers.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class DBLPCrawler(BaseCrawler):
    """DBLP API爬虫"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化DBLP爬虫
        
        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.api_url = config.get('api_url', 'https://dblp.org/search/publ/api')
        self.max_results = config.get('max_results', 1000)
    
    def crawl(self, conference_key: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        爬取指定会议的论文
        
        Args:
            conference_key: DBLP会议key，如 "conf/crypto"
            year: 年份，如果指定则只爬取该年份
            
        Returns:
            论文列表
        """
        papers = []
        
        if year:
            papers.extend(self._fetch_papers_by_year(conference_key, year))
        else:
            # 如果没有指定年份，爬取所有年份
            logger.info(f"爬取 {conference_key} 所有年份的论文")
            # 这里可以根据需要调整年份范围
            for y in range(2020, 2025):
                papers.extend(self._fetch_papers_by_year(conference_key, y))
        
        return papers
    
    def _fetch_papers_by_year(self, conference_key: str, year: int) -> List[Dict[str, Any]]:
        """
        获取指定会议和年份的论文
        
        Args:
            conference_key: 会议key
            year: 年份
            
        Returns:
            论文列表
        """
        # 构建查询
        query = f"{conference_key} {year}"
        params = {
            'q': query,
            'format': 'json',
            'h': self.max_results
        }
        
        url = f"{self.api_url}?{urllib.parse.urlencode(params)}"
        logger.info(f"DBLP查询: {conference_key} {year}")
        
        response = self.fetch(url)
        if not response:
            logger.warning(f"DBLP API请求失败: {conference_key} {year}")
            return []
        
        try:
            data = response.json()
            return self._parse_dblp_response(data, year)
        except Exception as e:
            logger.error(f"解析DBLP响应失败: {e}")
            return []
    
    def _parse_dblp_response(self, data: Dict[str, Any], year: int) -> List[Dict[str, Any]]:
        """
        解析DBLP API响应
        
        Args:
            data: JSON响应数据
            year: 年份
            
        Returns:
            论文列表
        """
        papers = []
        
        result = data.get('result', {})
        hits = result.get('hits', {})
        hit_list = hits.get('hit', [])
        
        logger.info(f"找到 {len(hit_list)} 篇论文")
        
        for hit in hit_list:
            info = hit.get('info', {})
            
            # 提取作者
            authors_data = info.get('authors', {}).get('author', [])
            if isinstance(authors_data, dict):
                authors_data = [authors_data]
            authors = '; '.join([a.get('text', '') if isinstance(a, dict) else str(a) 
                                for a in authors_data])
            
            # 提取URL
            url = info.get('url', '')
            ee = info.get('ee', '')
            if isinstance(ee, list):
                ee = ee[0] if ee else ''
            
            paper = {
                'title': info.get('title', ''),
                'authors': authors,
                'year': info.get('year', year),
                'url': url,
                'pdf_url': ee if ee.endswith('.pdf') else None,
                'doi': info.get('doi', ''),
                'dblp_key': info.get('key', ''),
                'venue': info.get('venue', '')
            }
            
            papers.append(paper)
        
        return papers
    
    def search_paper(self, title: str) -> Optional[Dict[str, Any]]:
        """
        根据标题搜索论文
        
        Args:
            title: 论文标题
            
        Returns:
            论文信息字典
        """
        params = {
            'q': title,
            'format': 'json',
            'h': 1
        }
        
        url = f"{self.api_url}?{urllib.parse.urlencode(params)}"
        response = self.fetch(url)
        
        if not response:
            return None
        
        try:
            data = response.json()
            papers = self._parse_dblp_response(data, None)
            return papers[0] if papers else None
        except Exception as e:
            logger.error(f"搜索论文失败: {e}")
            return None
