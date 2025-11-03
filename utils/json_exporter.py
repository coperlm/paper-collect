"""
JSON导出和管理工具 - 将数据库内容导出为易读的JSON文件
"""
import json
import os
from typing import Optional, List, Dict, Any
from utils.database import DatabaseManager
import logging

logger = logging.getLogger(__name__)


class JSONExporter:
    """JSON导出器"""
    
    def __init__(self, db_path: str = "data/papers.db", json_dir: str = "data/json"):
        """
        初始化JSON导出器
        
        Args:
            db_path: 数据库路径
            json_dir: JSON文件存储目录
        """
        self.db = DatabaseManager(db_path)
        self.json_dir = json_dir
        os.makedirs(json_dir, exist_ok=True)
    
    def export_all(self, output_file: Optional[str] = None) -> str:
        """
        导出所有论文到单个JSON文件
        
        Args:
            output_file: 输出文件路径，None则使用默认路径
            
        Returns:
            输出文件路径
        """
        if output_file is None:
            output_file = os.path.join(self.json_dir, "all_papers.json")
        
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM papers ORDER BY conference, year DESC, title")
        papers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已导出 {len(papers)} 篇论文到 {output_file}")
        return output_file
    
    def export_by_conference(self) -> Dict[str, str]:
        """
        按会议分别导出到不同的JSON文件
        
        Returns:
            会议名称到文件路径的映射
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        # 获取所有会议
        cursor.execute("SELECT DISTINCT conference FROM papers ORDER BY conference")
        conferences = [row['conference'] for row in cursor.fetchall()]
        
        output_files = {}
        
        for conf in conferences:
            cursor.execute(
                "SELECT * FROM papers WHERE conference = ? ORDER BY year DESC, title",
                (conf,)
            )
            papers = [dict(row) for row in cursor.fetchall()]
            
            # 清理文件名
            safe_name = conf.replace('/', '_').replace(' ', '_')
            output_file = os.path.join(self.json_dir, f"{safe_name}.json")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(papers, f, ensure_ascii=False, indent=2)
            
            output_files[conf] = output_file
            logger.info(f"{conf}: 导出 {len(papers)} 篇论文到 {output_file}")
        
        conn.close()
        return output_files
    
    def export_by_conference_and_year(self) -> Dict[str, str]:
        """
        按会议和年份分别导出到不同的JSON文件
        
        Returns:
            标识到文件路径的映射
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        # 获取所有会议-年份组合
        cursor.execute("""
            SELECT DISTINCT conference, year 
            FROM papers 
            ORDER BY conference, year DESC
        """)
        combinations = cursor.fetchall()
        
        output_files = {}
        
        for row in combinations:
            conf = row['conference']
            year = row['year']
            
            cursor.execute(
                "SELECT * FROM papers WHERE conference = ? AND year = ? ORDER BY title",
                (conf, year)
            )
            papers = [dict(row) for row in cursor.fetchall()]
            
            # 创建会议目录
            safe_conf_name = conf.replace('/', '_').replace(' ', '_')
            conf_dir = os.path.join(self.json_dir, safe_conf_name)
            os.makedirs(conf_dir, exist_ok=True)
            
            # 保存文件
            output_file = os.path.join(conf_dir, f"{year}.json")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(papers, f, ensure_ascii=False, indent=2)
            
            key = f"{conf}_{year}"
            output_files[key] = output_file
            logger.info(f"{conf} {year}: 导出 {len(papers)} 篇论文到 {output_file}")
        
        conn.close()
        return output_files
    
    def export_summary(self, output_file: Optional[str] = None) -> str:
        """
        导出摘要统计信息
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            输出文件路径
        """
        if output_file is None:
            output_file = os.path.join(self.json_dir, "summary.json")
        
        stats = self.db.get_statistics()
        
        # 添加更多统计信息
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        # 按会议和年份统计
        cursor.execute("""
            SELECT conference, year, COUNT(*) as count 
            FROM papers 
            GROUP BY conference, year
            ORDER BY conference, year DESC
        """)
        by_conf_year = {}
        for row in cursor.fetchall():
            conf = row['conference']
            if conf not in by_conf_year:
                by_conf_year[conf] = {}
            by_conf_year[conf][str(row['year'])] = row['count']
        
        # 有摘要的统计
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM papers 
            WHERE abstract IS NOT NULL AND abstract != ''
        """)
        with_abstract = cursor.fetchone()['count']
        
        conn.close()
        
        summary = {
            'total': stats['total'],
            'with_abstract': with_abstract,
            'by_conference': stats['by_conference'],
            'by_conference_and_year': by_conf_year,
            'by_download_status': stats['by_status']
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"统计信息已导出到 {output_file}")
        return output_file
    
    def export_readable_format(self, output_file: Optional[str] = None) -> str:
        """
        导出为更易读的格式（简化字段）
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            输出文件路径
        """
        if output_file is None:
            output_file = os.path.join(self.json_dir, "papers_readable.json")
        
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, authors, abstract, year, conference, 
                   doi, pdf_url, pdf_path, download_status
            FROM papers 
            ORDER BY conference, year DESC, title
        """)
        
        papers = []
        for row in cursor.fetchall():
            paper = {
                'id': row['id'],
                'title': row['title'],
                'authors': row['authors'].split('; ') if row['authors'] else [],
                'abstract': row['abstract'],
                'year': row['year'],
                'conference': row['conference'],
                'doi': row['doi'],
                'pdf_url': row['pdf_url'],
                'pdf_path': row['pdf_path'],
                'downloaded': row['download_status'] == 'completed'
            }
            papers.append(paper)
        
        conn.close()
        
        # 按会议分组
        by_conference = {}
        for paper in papers:
            conf = paper['conference']
            if conf not in by_conference:
                by_conference[conf] = []
            by_conference[conf].append(paper)
        
        output = {
            'total': len(papers),
            'conferences': by_conference
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"易读格式已导出到 {output_file}")
        return output_file
    
    def auto_export(self):
        """自动导出所有格式"""
        logger.info("开始自动导出...")
        
        # 导出摘要
        self.export_summary()
        
        # 导出所有论文
        self.export_all()
        
        # 按会议导出
        self.export_by_conference()
        
        # 导出易读格式
        self.export_readable_format()
        
        logger.info("自动导出完成！")
        logger.info(f"所有文件保存在: {self.json_dir}")


def main():
    """命令行接口"""
    import argparse
    from utils.logger import setup_logger
    
    setup_logger(level="INFO", console=True)
    
    parser = argparse.ArgumentParser(description='JSON导出工具')
    parser.add_argument('--db', default='data/papers.db', help='数据库路径')
    parser.add_argument('--output-dir', default='data/json', help='输出目录')
    parser.add_argument('--mode', choices=['all', 'conference', 'year', 'summary', 'readable', 'auto'],
                       default='auto', help='导出模式')
    
    args = parser.parse_args()
    
    exporter = JSONExporter(args.db, args.output_dir)
    
    if args.mode == 'all':
        exporter.export_all()
    elif args.mode == 'conference':
        exporter.export_by_conference()
    elif args.mode == 'year':
        exporter.export_by_conference_and_year()
    elif args.mode == 'summary':
        exporter.export_summary()
    elif args.mode == 'readable':
        exporter.export_readable_format()
    elif args.mode == 'auto':
        exporter.auto_export()


if __name__ == '__main__':
    main()
