"""
IACR会议爬虫 - 从IACR官网的currentProgram.php获取准确的论文列表
支持 CRYPTO, ASIACRYPT, EUROCRYPT
"""
import logging
import re
import json
import time
from typing import List, Dict, Any, Optional
from crawlers.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class IACRCrawler(BaseCrawler):
    """IACR会议爬虫 - 使用currentProgram.php JSON API"""
    
    # 会议JSON API URL模板
    CONFERENCE_URLS = {
        'CRYPTO': 'https://crypto.iacr.org/{year}/currentProgram.php',
        'ASIACRYPT': 'https://asiacrypt.iacr.org/{year}/currentProgram.php',
        'EUROCRYPT': 'https://eurocrypt.iacr.org/{year}/currentProgram.php'
    }
    
    # IACR eprint URL
    EPRINT_BASE = 'https://eprint.iacr.org'
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
    
    def crawl(self, conference: str, year: int) -> List[Dict[str, Any]]:
        """
        从IACR官网currentProgram.php获取论文
        
        Args:
            conference: 会议名称 (CRYPTO, ASIACRYPT, EUROCRYPT)
            year: 年份
            
        Returns:
            论文列表
        """
        if conference not in self.CONFERENCE_URLS:
            logger.error(f"不支持的会议: {conference}")
            return []
        
        # 添加时间戳参数避免缓存
        url = f"{self.CONFERENCE_URLS[conference].format(year=year)}?v={int(time.time() * 1000)}"
        logger.info(f"爬取 {conference} {year} 从 currentProgram.php API")
        
        response = self.fetch(url)
        if not response:
            logger.warning(f"无法访问 {url}")
            return []
        
        # 解析JSON响应
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return []
        
        papers = self._parse_program_data(data, conference, year)
        logger.info(f"从 {conference} {year} 获取 {len(papers)} 篇论文")
        
        return papers
    
    def _parse_program_data(self, data: Dict, conference: str, year: int) -> List[Dict[str, Any]]:
        """
        解析currentProgram.php返回的JSON数据
        
        JSON结构:
        {
          "days": [
            {
              "timeslots": [
                {
                  "sessions": [
                    {
                      "talks": [
                        {
                          "title": "论文标题",
                          "authors": ["作者1", "作者2"],
                          "abstract": "摘要",
                          "paperId": "123",
                          "paperUrl": "DOI URL",
                          "eprint": "eprint URL",
                          "slidesUrl": "...",
                          ...
                        }
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        }
        """
        papers = []
        
        # 遍历所有天的日程
        for day in data.get('days', []):
            for timeslot in day.get('timeslots', []):
                for session in timeslot.get('sessions', []):
                    # 跳过非技术会议（如午餐、休息等）
                    session_title = session.get('session_title', '')
                    if any(skip in session_title.lower() for skip in 
                           ['lunch', 'break', 'dinner', 'reception', 'registration', 'opening', 'closing']):
                        continue
                    
                    # 提取论文
                    for talk in session.get('talks', []):
                        paper = self._extract_paper_from_talk(talk, conference, year)
                        if paper:
                            papers.append(paper)
        
        return papers
    
    def _extract_paper_from_talk(self, talk: Dict, conference: str, year: int) -> Optional[Dict[str, Any]]:
        """从talk数据中提取论文信息"""
        # 检查是否是论文talk（有paperId）
        if not talk.get('paperId'):
            return None
        
        # 提取作者
        authors = talk.get('authors', [])
        if isinstance(authors, list):
            authors_str = '; '.join(authors)
        else:
            authors_str = str(authors)
        
        paper = {
            'conference': conference,
            'year': year,
            'title': talk.get('title', '').strip(),
            'authors': authors_str,
            'abstract': talk.get('abstract', '').strip(),
            'paper_id': talk.get('paperId'),
        }
        
        # 提取URL
        if talk.get('paperUrl'):
            paper['url'] = talk['paperUrl']
            # 从DOI URL提取DOI
            if 'doi.org' in paper['url']:
                paper['doi'] = paper['url'].split('doi.org/')[-1]
        
        # eprint URL
        if talk.get('eprint'):
            paper['eprint_url'] = talk['eprint']
        
        # PDF URL - 通常在DOI URL或eprint
        if paper.get('url') and 'doi.org' in paper['url']:
            # DOI URL通常可以获取PDF
            paper['pdf_url'] = paper['url']
        elif paper.get('eprint_url'):
            # eprint URL也可以下载PDF
            paper['pdf_url'] = paper['eprint_url'] + '.pdf'
        
        # 其他链接
        if talk.get('slidesUrl'):
            paper['slides_url'] = talk['slidesUrl']
        if talk.get('videoUrl'):
            paper['video_url'] = talk['videoUrl']
        
        # 关键词
        if talk.get('keywords'):
            paper['keywords'] = talk['keywords']
        
        # 仿属
        if talk.get('affiliations'):
            paper['affiliations'] = '; '.join(talk['affiliations']) if isinstance(talk['affiliations'], list) else talk['affiliations']
        
        return paper if paper['title'] else None


def test_iacr_crawler():
    """测试IACR爬虫"""
    import json
    
    crawler = IACRCrawler({})
    
    # 测试CRYPTO 2024
    papers = crawler.crawl('CRYPTO', 2024)
    
    print(f"找到 {len(papers)} 篇论文")
    
    if papers:
        print("\n前3篇论文:")
        for paper in papers[:3]:
            print(f"\n标题: {paper['title']}")
            print(f"作者: {paper.get('authors', 'N/A')}")
            print(f"PDF: {paper.get('pdf_url', 'N/A')}")
        
        # 保存到JSON
        with open('test_iacr_papers.json', 'w', encoding='utf-8') as f:
            json.dump(papers[:10], f, ensure_ascii=False, indent=2)
        print("\n已保存前10篇到 test_iacr_papers.json")


if __name__ == '__main__':
    test_iacr_crawler()
