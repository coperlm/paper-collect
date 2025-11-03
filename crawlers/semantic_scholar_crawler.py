"""
Semantic Scholar爬虫 - 获取论文摘要和额外信息
Semantic Scholar提供免费的学术论文API，包含摘要信息
"""
import logging
import time
from typing import Optional, Dict, Any, List
from crawlers.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class SemanticScholarCrawler(BaseCrawler):
    """Semantic Scholar API爬虫"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Semantic Scholar爬虫
        
        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.api_base = "https://api.semanticscholar.org/graph/v1"
        self.rate_limit_delay = 2  # API限速延迟（秒），增加延迟避免429错误
    
    def get_paper_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        根据DOI获取论文信息
        
        Args:
            doi: 论文的DOI
            
        Returns:
            论文信息字典，包含摘要
        """
        if not doi:
            return None
        
        # 清理DOI
        doi = doi.strip()
        
        url = f"{self.api_base}/paper/DOI:{doi}"
        params = {
            'fields': 'title,abstract,authors,year,citationCount,publicationDate,externalIds'
        }
        
        logger.debug(f"查询Semantic Scholar: DOI={doi}")
        
        response = self.fetch(url, params=params)
        if not response:
            logger.debug(f"未找到论文: DOI={doi}")
            return None
        
        try:
            data = response.json()
            
            # 提取摘要和其他信息
            result = {
                'abstract': data.get('abstract'),
                'citation_count': data.get('citationCount'),
                'publication_date': data.get('publicationDate')
            }
            
            # 限速
            time.sleep(self.rate_limit_delay)
            
            return result
        except Exception as e:
            logger.error(f"解析Semantic Scholar响应失败: {e}")
            return None
    
    def search_paper_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """
        根据标题搜索论文
        
        Args:
            title: 论文标题
            
        Returns:
            论文信息字典
        """
        if not title:
            return None
        
        url = f"{self.api_base}/paper/search"
        params = {
            'query': title,
            'limit': 1,
            'fields': 'title,abstract,authors,year,citationCount,publicationDate,externalIds'
        }
        
        logger.debug(f"搜索Semantic Scholar: {title[:50]}...")
        
        response = self.fetch(url, params=params)
        if not response:
            return None
        
        try:
            data = response.json()
            papers = data.get('data', [])
            
            if not papers:
                logger.debug(f"未找到论文: {title[:50]}...")
                return None
            
            paper = papers[0]
            result = {
                'abstract': paper.get('abstract'),
                'citation_count': paper.get('citationCount'),
                'publication_date': paper.get('publicationDate'),
                'doi': paper.get('externalIds', {}).get('DOI')
            }
            
            # 限速
            time.sleep(self.rate_limit_delay)
            
            return result
        except Exception as e:
            logger.error(f"解析Semantic Scholar搜索结果失败: {e}")
            return None
    
    def crawl(self, paper_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        获取论文的详细信息（主要是摘要）
        
        Args:
            paper_info: 包含title和/或doi的论文信息
            
        Returns:
            包含摘要等信息的字典
        """
        # 优先使用DOI查询
        doi = paper_info.get('doi')
        if doi:
            result = self.get_paper_by_doi(doi)
            if result and result.get('abstract'):
                return result
        
        # 如果DOI查询失败，使用标题搜索
        title = paper_info.get('title')
        if title:
            result = self.search_paper_by_title(title)
            if result and result.get('abstract'):
                return result
        
        return None
    
    def batch_enrich_papers(self, papers: List[Dict[str, Any]], 
                           db_manager) -> Dict[str, int]:
        """
        批量为论文添加摘要信息
        
        Args:
            papers: 论文列表
            db_manager: 数据库管理器
            
        Returns:
            处理统计信息
        """
        stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        logger.info(f"开始获取摘要，共 {len(papers)} 篇论文")
        
        for idx, paper in enumerate(papers, 1):
            paper_id = paper['id']
            
            # 如果已有摘要，跳过
            if paper.get('abstract'):
                logger.debug(f"论文已有摘要，跳过: {paper['title'][:50]}...")
                stats['skipped'] += 1
                continue
            
            logger.info(f"[{idx}/{len(papers)}] 获取摘要: {paper['title'][:60]}...")
            
            # 获取详细信息
            enriched_info = self.crawl(paper)
            
            if enriched_info and enriched_info.get('abstract'):
                # 更新数据库
                update_data = {
                    'abstract': enriched_info['abstract']
                }
                
                # 如果获取到新的DOI，也更新
                if enriched_info.get('doi') and not paper.get('doi'):
                    update_data['doi'] = enriched_info['doi']
                
                # 添加备注信息（引用数和发表日期）
                notes = []
                if enriched_info.get('citation_count'):
                    notes.append(f"Citations: {enriched_info['citation_count']}")
                if enriched_info.get('publication_date'):
                    notes.append(f"Date: {enriched_info['publication_date']}")
                if notes:
                    update_data['notes'] = '; '.join(notes)
                
                success = db_manager.update_paper(paper_id, update_data)
                
                if success:
                    stats['success'] += 1
                    logger.info(f"✓ 成功获取摘要")
                else:
                    stats['failed'] += 1
                    logger.warning(f"✗ 更新数据库失败")
            else:
                stats['failed'] += 1
                logger.warning(f"✗ 未找到摘要")
        
        logger.info(f"摘要获取完成: 成功 {stats['success']}, 失败 {stats['failed']}, 跳过 {stats['skipped']}")
        return stats
