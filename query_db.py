"""
数据库查询工具 - 方便查看和导出论文数据
"""
import sqlite3
import argparse
import csv
import os
from typing import List, Dict, Any


class DatabaseViewer:
    """数据库查看器"""
    
    def __init__(self, db_path: str = "data/papers.db"):
        """初始化数据库查看器"""
        self.db_path = db_path
        if not os.path.exists(db_path):
            print(f"错误: 数据库文件不存在: {db_path}")
            exit(1)
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def list_papers(self, conference: str = None, year: int = None, limit: int = 10):
        """列出论文"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT id, title, authors, year, conference, download_status FROM papers"
        params = []
        
        where_clauses = []
        if conference:
            where_clauses.append("conference = ?")
            params.append(conference)
        if year:
            where_clauses.append("year = ?")
            params.append(year)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += f" ORDER BY year DESC, title LIMIT {limit}"
        
        cursor.execute(query, params)
        papers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not papers:
            print("没有找到论文")
            return
        
        print(f"\n找到 {len(papers)} 篇论文:")
        print("-" * 100)
        for paper in papers:
            print(f"ID: {paper['id']}")
            print(f"标题: {paper['title'][:80]}...")
            print(f"作者: {paper['authors'][:80]}...")
            print(f"会议: {paper['conference']} {paper['year']}")
            print(f"状态: {paper['download_status']}")
            print("-" * 100)
    
    def show_statistics(self):
        """显示统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 总数
        cursor.execute("SELECT COUNT(*) as total FROM papers")
        total = cursor.fetchone()['total']
        
        # 按会议统计
        cursor.execute("""
            SELECT conference, year, COUNT(*) as count 
            FROM papers 
            GROUP BY conference, year
            ORDER BY conference, year DESC
        """)
        by_conf_year = cursor.fetchall()
        
        # 按状态统计
        cursor.execute("""
            SELECT download_status, COUNT(*) as count 
            FROM papers 
            GROUP BY download_status
        """)
        by_status = cursor.fetchall()
        
        # 有PDF链接的数量
        cursor.execute("SELECT COUNT(*) as count FROM papers WHERE pdf_url IS NOT NULL")
        with_pdf_url = cursor.fetchone()['count']
        
        # 已下载的数量
        cursor.execute("SELECT COUNT(*) as count FROM papers WHERE download_status = 'completed'")
        downloaded = cursor.fetchone()['count']
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("数据库统计信息")
        print("=" * 60)
        print(f"总论文数: {total}")
        print(f"有PDF链接: {with_pdf_url}")
        print(f"已下载: {downloaded}")
        print()
        
        print("按会议和年份:")
        for row in by_conf_year:
            print(f"  {row['conference']} {row['year']}: {row['count']}")
        print()
        
        print("下载状态:")
        for row in by_status:
            print(f"  {row['download_status']}: {row['count']}")
        print("=" * 60)
    
    def search(self, keyword: str, limit: int = 10):
        """搜索论文"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT id, title, authors, year, conference, download_status 
            FROM papers 
            WHERE title LIKE ? OR authors LIKE ?
            LIMIT ?
        """
        
        cursor.execute(query, (f"%{keyword}%", f"%{keyword}%", limit))
        papers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not papers:
            print(f"没有找到包含 '{keyword}' 的论文")
            return
        
        print(f"\n找到 {len(papers)} 篇包含 '{keyword}' 的论文:")
        print("-" * 100)
        for paper in papers:
            print(f"ID: {paper['id']}")
            print(f"标题: {paper['title']}")
            print(f"作者: {paper['authors'][:80]}...")
            print(f"会议: {paper['conference']} {paper['year']}")
            print("-" * 100)
    
    def export_to_csv(self, output_file: str, conference: str = None, year: int = None):
        """导出到CSV"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM papers"
        params = []
        
        where_clauses = []
        if conference:
            where_clauses.append("conference = ?")
            params.append(conference)
        if year:
            where_clauses.append("year = ?")
            params.append(year)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        cursor.execute(query, params)
        papers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not papers:
            print("没有找到论文")
            return
        
        # 写入CSV
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=papers[0].keys())
            writer.writeheader()
            writer.writerows(papers)
        
        print(f"已导出 {len(papers)} 篇论文到 {output_file}")
    
    def show_paper_detail(self, paper_id: int):
        """显示论文详情"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
        paper = cursor.fetchone()
        conn.close()
        
        if not paper:
            print(f"未找到ID为 {paper_id} 的论文")
            return
        
        paper = dict(paper)
        print("\n" + "=" * 60)
        print(f"论文详情 (ID: {paper['id']})")
        print("=" * 60)
        for key, value in paper.items():
            if value and key not in ['id']:
                print(f"{key}: {value}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='论文数据库查询工具')
    parser.add_argument('--db', default='data/papers.db', help='数据库路径')
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # list命令
    list_parser = subparsers.add_parser('list', help='列出论文')
    list_parser.add_argument('--conference', help='会议名称')
    list_parser.add_argument('--year', type=int, help='年份')
    list_parser.add_argument('--limit', type=int, default=10, help='显示数量')
    
    # stats命令
    subparsers.add_parser('stats', help='显示统计信息')
    
    # search命令
    search_parser = subparsers.add_parser('search', help='搜索论文')
    search_parser.add_argument('keyword', help='搜索关键词')
    search_parser.add_argument('--limit', type=int, default=10, help='显示数量')
    
    # export命令
    export_parser = subparsers.add_parser('export', help='导出到CSV')
    export_parser.add_argument('output', help='输出文件路径')
    export_parser.add_argument('--conference', help='会议名称')
    export_parser.add_argument('--year', type=int, help='年份')
    
    # detail命令
    detail_parser = subparsers.add_parser('detail', help='显示论文详情')
    detail_parser.add_argument('id', type=int, help='论文ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    viewer = DatabaseViewer(args.db)
    
    if args.command == 'list':
        viewer.list_papers(args.conference, args.year, args.limit)
    elif args.command == 'stats':
        viewer.show_statistics()
    elif args.command == 'search':
        viewer.search(args.keyword, args.limit)
    elif args.command == 'export':
        viewer.export_to_csv(args.output, args.conference, args.year)
    elif args.command == 'detail':
        viewer.show_paper_detail(args.id)


if __name__ == '__main__':
    main()
