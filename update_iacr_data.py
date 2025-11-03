"""
更新IACR会议数据脚本
清除旧的错误数据，重新使用currentProgram.php API收集准确数据
"""
import sqlite3
import logging
from utils.database import DatabaseManager
from crawlers.iacr_crawler import IACRCrawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    # 初始化
    db = DatabaseManager('data/papers.db')
    crawler = IACRCrawler({})
    
    # 定义要收集的会议和年份（只收集2025年）
    conferences = {
        'CRYPTO': [2025],
        # 'ASIACRYPT': [2025],  # 暂未发布
        'EUROCRYPT': [2025]
    }
    
    # 步骤1: 清除旧数据
    logger.info("=" * 60)
    logger.info("步骤1: 清除旧的IACR数据")
    logger.info("=" * 60)
    
    conn = sqlite3.connect('data/papers.db')
    cursor = conn.cursor()
    
    # 检查当前数据
    cursor.execute("SELECT COUNT(*) FROM papers WHERE conference IN ('CRYPTO', 'ASIACRYPT', 'EUROCRYPT')")
    old_count = cursor.fetchone()[0]
    logger.info(f"当前数据库中有 {old_count} 篇IACR论文")
    
    if old_count > 0:
        response = input(f"\n是否删除这 {old_count} 篇论文并重新收集? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("用户取消操作")
            return
        
        cursor.execute("DELETE FROM papers WHERE conference IN ('CRYPTO', 'ASIACRYPT', 'EUROCRYPT')")
        conn.commit()
        logger.info(f"已删除 {old_count} 篇旧论文")
    
    conn.close()
    
    # 步骤2: 重新收集数据
    logger.info("\n" + "=" * 60)
    logger.info("步骤2: 从currentProgram.php API重新收集数据")
    logger.info("=" * 60 + "\n")
    
    total_papers = 0
    
    for conf, years in conferences.items():
        for year in years:
            logger.info(f"\n收集 {conf} {year}...")
            try:
                papers = crawler.crawl(conf, year)
                
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
    
    # 步骤3: 汇总统计
    logger.info("\n" + "=" * 60)
    logger.info("步骤3: 数据统计")
    logger.info("=" * 60)
    
    conn = sqlite3.connect('data/papers.db')
    cursor = conn.cursor()
    
    logger.info(f"\n总共收集: {total_papers} 篇论文\n")
    
    for conf in ['CRYPTO', 'ASIACRYPT', 'EUROCRYPT']:
        cursor.execute("SELECT year, COUNT(*) FROM papers WHERE conference=? GROUP BY year ORDER BY year DESC", (conf,))
        results = cursor.fetchall()
        
        if results:
            logger.info(f"{conf}:")
            for year, count in results:
                logger.info(f"  {year}: {count} 篇")
        else:
            logger.info(f"{conf}: 0 篇")
    
    conn.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("数据更新完成！")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
