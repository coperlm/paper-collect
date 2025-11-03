"""
更新会议数据脚本
收集IACR会议和四大安全会议的论文数据
"""
import sqlite3
import logging
from utils.database import DatabaseManager
from crawlers.iacr_crawler import IACRCrawler
from crawlers.security_crawler import SecurityCrawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    # 初始化
    db = DatabaseManager('data/papers.db')
    iacr_crawler = IACRCrawler({})
    security_crawler = SecurityCrawler({})
    
    # 定义要收集的会议和年份（只收集2025年）
    # IACR会议
    iacr_conferences = {
        'CRYPTO': [2025],
        # 'ASIACRYPT': [2025],  # 暂未发布
        'EUROCRYPT': [2025]
    }
    
    # 四大安全会议
    security_conferences = {
        'USENIX Security': [2025],
        'NDSS': [2025],
        'IEEE S&P': [2025],
        # 'CCS': [2025]  # CCS 2025 accepted papers页面尚未发布
    }
    
    # 步骤1: 清除旧数据
    logger.info("=" * 60)
    logger.info("步骤1: 清除旧数据")
    logger.info("=" * 60)
    
    conn = sqlite3.connect('data/papers.db')
    cursor = conn.cursor()
    
    # 统计当前数据
    all_conferences = list(iacr_conferences.keys()) + list(security_conferences.keys())
    placeholders = ','.join(['?' for _ in all_conferences])
    cursor.execute(f"SELECT conference, COUNT(*) FROM papers WHERE conference IN ({placeholders}) GROUP BY conference", 
                   all_conferences)
    old_data = cursor.fetchall()
    
    total_old = sum(count for _, count in old_data)
    
    if old_data:
        logger.info("当前数据库中的论文统计:")
        for conf, count in old_data:
            logger.info(f"  {conf}: {count} 篇")
        logger.info(f"  总计: {total_old} 篇")
        
        response = input(f"\n是否删除这些论文并重新收集? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("用户取消操作")
            return
        
        cursor.execute(f"DELETE FROM papers WHERE conference IN ({placeholders})", all_conferences)
        conn.commit()
        logger.info(f"已删除 {total_old} 篇旧论文")
    else:
        logger.info("数据库为空，开始收集数据")
    
    conn.close()
    
    # 步骤2: 收集IACR数据
    logger.info("\n" + "=" * 60)
    logger.info("步骤2: 收集IACR会议数据")
    logger.info("=" * 60 + "\n")
    
    total_papers = 0
    
    for conf, years in iacr_conferences.items():
        for year in years:
            logger.info(f"\n收集 {conf} {year}...")
            try:
                papers = iacr_crawler.crawl(conf, year)
                
                if papers:
                    logger.info(f"  找到 {len(papers)} 篇论文")
                    
                    # 保存到数据库
                    for paper in papers:
                        try:
                            db.insert_paper(paper)
                        except Exception as e:
                            logger.warning(f"  保存论文失败: {paper.get('title', 'N/A')[:50]}... - {e}")
                    
                    total_papers += len(papers)
                    logger.info(f"  ✓ {conf} {year} 完成")
                else:
                    logger.warning(f"  ✗ {conf} {year} 未找到论文")
            
            except Exception as e:
                logger.error(f"  ✗ {conf} {year} 失败: {e}")
    
    # 步骤3: 收集四大安全会议数据
    logger.info("\n" + "=" * 60)
    logger.info("步骤3: 收集四大安全会议数据")
    logger.info("=" * 60 + "\n")
    
    for conf, years in security_conferences.items():
        for year in years:
            logger.info(f"\n收集 {conf} {year}...")
            try:
                papers = security_crawler.crawl(conf, year)
                
                if papers:
                    logger.info(f"  找到 {len(papers)} 篇论文")
                    
                    # 保存到数据库
                    for paper in papers:
                        try:
                            db.insert_paper(paper)
                        except Exception as e:
                            logger.warning(f"  保存论文失败: {paper.get('title', 'N/A')[:50]}... - {e}")
                    
                    total_papers += len(papers)
                    logger.info(f"  ✓ {conf} {year} 完成")
                else:
                    logger.warning(f"  ✗ {conf} {year} 未找到论文")
            
            except Exception as e:
                logger.error(f"  ✗ {conf} {year} 失败: {e}")
    
    # 步骤4: 汇总统计
    logger.info("\n" + "=" * 60)
    logger.info("步骤4: 数据统计")
    logger.info("=" * 60)
    
    conn = sqlite3.connect('data/papers.db')
    cursor = conn.cursor()
    
    logger.info(f"\n总共收集: {total_papers} 篇论文\n")
    
    logger.info("IACR会议:")
    for conf in iacr_conferences.keys():
        cursor.execute("SELECT year, COUNT(*) FROM papers WHERE conference=? GROUP BY year ORDER BY year DESC", (conf,))
        results = cursor.fetchall()
        
        if results:
            for year, count in results:
                logger.info(f"  {conf} {year}: {count} 篇")
        else:
            logger.info(f"  {conf}: 0 篇")
    
    logger.info("\n四大安全会议:")
    for conf in security_conferences.keys():
        cursor.execute("SELECT year, COUNT(*) FROM papers WHERE conference=? GROUP BY year ORDER BY year DESC", (conf,))
        results = cursor.fetchall()
        
        if results:
            for year, count in results:
                logger.info(f"  {conf} {year}: {count} 篇")
        else:
            logger.info(f"  {conf}: 0 篇")
    
    conn.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("数据更新完成！")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
