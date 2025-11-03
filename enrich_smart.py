"""
智能摘要获取脚本 - 过滤真正的论文
"""
import sqlite3
import sys
from crawlers.semantic_scholar_crawler import SemanticScholarCrawler
from utils.database import DatabaseManager
from utils.logger import setup_logger
import logging

# 设置日志
logger = setup_logger(level="INFO", console=True)

def get_real_papers(db_path='data/papers.db', limit=10):
    """获取真正的论文（过滤会议文集）"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 过滤条件：
    # 1. 不包含 Proceedings, Conference, Symposium, Workshop 等关键词
    # 2. 有DOI
    # 3. DOI不是ISBN格式(978-)
    # 4. 没有摘要
    query = """
    SELECT * FROM papers 
    WHERE (abstract IS NULL OR abstract = '')
      AND doi IS NOT NULL
      AND doi NOT LIKE '%.978-%'
      AND title NOT LIKE '%Proceedings%'
      AND title NOT LIKE '%Conference%'
      AND title NOT LIKE '%Symposium%'
      AND title NOT LIKE '%Workshop%'
      AND title NOT LIKE '%Front Matter%'
    LIMIT ?
    """
    
    cursor.execute(query, (limit,))
    papers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return papers

def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    logger.info(f"获取前{limit}篇真实论文并添加摘要")
    
    # 获取论文
    papers = get_real_papers(limit=limit)
    
    if not papers:
        logger.info("没有找到符合条件的论文")
        return
    
    logger.info(f"找到 {len(papers)} 篇论文")
    
    # 初始化爬虫和数据库
    crawler = SemanticScholarCrawler({})
    db = DatabaseManager('data/papers.db')
    
    # 批量获取摘要
    stats = crawler.batch_enrich_papers(papers, db)
    
    logger.info(f"完成！成功: {stats['success']}, 失败: {stats['failed']}, 跳过: {stats['skipped']}")

if __name__ == '__main__':
    main()
