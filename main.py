"""
论文收集主程序
"""
import os
import sys
import argparse
import logging
from typing import List, Dict, Any

from utils.config import ConfigManager
from utils.logger import setup_logger
from utils.database import DatabaseManager
from utils.downloader import PDFDownloader
from crawlers.dblp_crawler import DBLPCrawler
from crawlers.semantic_scholar_crawler import SemanticScholarCrawler

logger = logging.getLogger(__name__)


class PaperCollector:
    """论文收集器主类"""
    
    def __init__(self, config_dir: str = "config"):
        """
        初始化论文收集器
        
        Args:
            config_dir: 配置文件目录
        """
        # 加载配置
        self.config = ConfigManager(config_dir)
        
        # 设置日志
        log_config = self.config.settings.get('settings', {}).get('logging', {})
        global logger
        logger = setup_logger(
            log_file=log_config.get('file'),
            level=log_config.get('level', 'INFO'),
            console=log_config.get('console', True)
        )
        
        # 初始化数据库
        db_path = self.config.get_setting('settings', 'database', 'path', default='data/papers.db')
        self.db = DatabaseManager(db_path)
        
        # 初始化爬虫配置
        crawler_config = self.config.get_setting('settings', 'crawler', default={})
        dblp_config = self.config.get_setting('settings', 'dblp', default={})
        crawler_config.update(dblp_config)
        
        # 初始化DBLP爬虫
        self.dblp_crawler = DBLPCrawler(crawler_config)
        
        # 初始化PDF下载器
        pdf_base_path = self.config.get_setting('settings', 'pdf_storage', 'base_path', 
                                                 default='data/pdfs')
        self.downloader = PDFDownloader(crawler_config, pdf_base_path)
        
        # 初始化Semantic Scholar爬虫（用于获取摘要）
        self.semantic_crawler = SemanticScholarCrawler(crawler_config)
        
        logger.info("论文收集器初始化完成")
    
    def collect_metadata(self, conference_keys: List[str] = None, years: List[int] = None):
        """
        收集论文元数据
        
        Args:
            conference_keys: 会议key列表，None表示所有会议
            years: 年份列表，None表示配置中的所有年份
        """
        all_conferences = self.config.get_all_conferences()
        
        if conference_keys is None:
            conference_keys = list(all_conferences.keys())
        
        logger.info(f"开始收集元数据，会议: {conference_keys}")
        
        total_papers = 0
        
        for conf_key in conference_keys:
            conf_list = all_conferences.get(conf_key, [])
            
            if not conf_list:
                logger.warning(f"未找到会议配置: {conf_key}")
                continue
            
            for conf_info in conf_list:
                conf_name = conf_info.get('name')
                dblp_key = conf_info.get('dblp_key')
                conf_years = years if years else conf_info.get('years', [])
                
                logger.info(f"收集 {conf_name} 的论文")
                
                for year in conf_years:
                    logger.info(f"  年份: {year}")
                    
                    # 从DBLP获取论文
                    papers = self.dblp_crawler.crawl(dblp_key, year)
                    
                    # 存入数据库
                    inserted = 0
                    for paper in papers:
                        paper['conference'] = conf_name
                        paper_id = self.db.insert_paper(paper)
                        if paper_id:
                            inserted += 1
                    
                    logger.info(f"  插入 {inserted}/{len(papers)} 篇论文")
                    total_papers += inserted
        
        logger.info(f"元数据收集完成，共收集 {total_papers} 篇论文")
        self._print_statistics()
    
    def download_pdfs(self, conference: str = None, year: int = None, limit: int = None):
        """
        下载PDF文件
        
        Args:
            conference: 会议名称，None表示所有会议
            year: 年份，None表示所有年份
            limit: 下载数量限制
        """
        logger.info("开始下载PDF文件")
        
        if conference or year:
            # 获取特定会议的论文
            papers = self.db.get_papers_by_conference(conference, year)
            # 过滤出待下载的
            papers = [p for p in papers if p['download_status'] == 'pending' and p['pdf_url']]
        else:
            # 获取所有待下载的论文
            papers = self.db.get_pending_downloads(limit)
        
        if not papers:
            logger.info("没有需要下载的论文")
            return
        
        logger.info(f"找到 {len(papers)} 篇待下载论文")
        
        # 批量下载
        stats = self.downloader.batch_download(papers, self.db)
        
        logger.info(f"PDF下载完成: 成功 {stats['success']}, 失败 {stats['failed']}, 跳过 {stats['skipped']}")
    
    def retry_failed_downloads(self):
        """重试失败的下载"""
        logger.info("重试失败的下载")
        
        # 获取失败的下载
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM papers 
            WHERE download_status = 'failed' AND pdf_url IS NOT NULL
        """)
        papers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not papers:
            logger.info("没有失败的下载")
            return
        
        logger.info(f"找到 {len(papers)} 篇下载失败的论文")
        
        # 重置状态并重试
        for paper in papers:
            self.db.update_download_status(paper['id'], 'pending')
        
        stats = self.downloader.batch_download(papers, self.db)
        logger.info(f"重试完成: 成功 {stats['success']}, 失败 {stats['failed']}")
    
    def enrich_abstracts(self, conference: str = None, year: int = None, limit: int = None):
        """
        为论文添加摘要信息
        
        Args:
            conference: 会议名称，None表示所有会议
            year: 年份，None表示所有年份
            limit: 处理数量限制
        """
        logger.info("开始获取论文摘要")
        
        # 获取没有摘要的论文
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM papers WHERE abstract IS NULL OR abstract = ''"
        params = []
        
        if conference:
            query += " AND conference = ?"
            params.append(conference)
        if year:
            query += " AND year = ?"
            params.append(year)
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        papers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not papers:
            logger.info("所有论文都已有摘要")
            return
        
        logger.info(f"找到 {len(papers)} 篇缺少摘要的论文")
        
        # 批量获取摘要
        stats = self.semantic_crawler.batch_enrich_papers(papers, self.db)
        
        logger.info(f"摘要获取完成: 成功 {stats['success']}, 失败 {stats['failed']}, 跳过 {stats['skipped']}")
    
    def _print_statistics(self):
        """打印统计信息"""
        stats = self.db.get_statistics()
        
        logger.info("=" * 60)
        logger.info(f"数据库统计信息:")
        logger.info(f"  总论文数: {stats['total']}")
        logger.info(f"  按会议统计:")
        for conf, count in stats['by_conference'].items():
            logger.info(f"    {conf}: {count}")
        logger.info(f"  下载状态:")
        for status, count in stats['by_status'].items():
            logger.info(f"    {status}: {count}")
        logger.info("=" * 60)
    
    def show_statistics(self):
        """显示统计信息"""
        self._print_statistics()
    
    def close(self):
        """清理资源"""
        self.dblp_crawler.close()
        self.downloader.close()
        self.semantic_crawler.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='学术论文收集工具')
    parser.add_argument('--config', default='config', help='配置文件目录')
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # collect命令 - 收集元数据
    collect_parser = subparsers.add_parser('collect', help='收集论文元数据')
    collect_parser.add_argument('--conferences', nargs='+', 
                               help='会议key列表，如: crypto asiacrypt')
    collect_parser.add_argument('--years', type=int, nargs='+',
                               help='年份列表，如: 2023 2024')
    
    # download命令 - 下载PDF
    download_parser = subparsers.add_parser('download', help='下载PDF文件')
    download_parser.add_argument('--conference', help='会议名称')
    download_parser.add_argument('--year', type=int, help='年份')
    download_parser.add_argument('--limit', type=int, help='下载数量限制')
    
    # retry命令 - 重试失败的下载
    subparsers.add_parser('retry', help='重试失败的下载')
    
    # enrich命令 - 获取摘要
    enrich_parser = subparsers.add_parser('enrich', help='为论文添加摘要信息')
    enrich_parser.add_argument('--conference', help='会议名称')
    enrich_parser.add_argument('--year', type=int, help='年份')
    enrich_parser.add_argument('--limit', type=int, help='处理数量限制')
    
    # stats命令 - 显示统计信息
    subparsers.add_parser('stats', help='显示统计信息')
    
    # all命令 - 执行完整流程
    all_parser = subparsers.add_parser('all', help='执行完整流程（收集+下载）')
    all_parser.add_argument('--conferences', nargs='+',
                           help='会议key列表')
    all_parser.add_argument('--years', type=int, nargs='+',
                           help='年份列表')
    all_parser.add_argument('--with-abstract', action='store_true',
                           help='同时获取摘要')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 创建收集器
    collector = PaperCollector(args.config)
    
    try:
        if args.command == 'collect':
            collector.collect_metadata(args.conferences, args.years)
        
        elif args.command == 'download':
            collector.download_pdfs(args.conference, args.year, args.limit)
        
        elif args.command == 'retry':
            collector.retry_failed_downloads()
        
        elif args.command == 'enrich':
            collector.enrich_abstracts(args.conference, args.year, args.limit)
        
        elif args.command == 'stats':
            collector.show_statistics()
        
        elif args.command == 'all':
            logger.info("执行完整流程：收集元数据 -> 获取摘要 -> 下载PDF")
            collector.collect_metadata(args.conferences, args.years)
            
            if args.with_abstract:
                logger.info("获取摘要信息...")
                collector.enrich_abstracts()
            
            collector.download_pdfs()
        
    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"发生错误: {e}", exc_info=True)
    finally:
        collector.close()
        logger.info("程序结束")


if __name__ == '__main__':
    main()
