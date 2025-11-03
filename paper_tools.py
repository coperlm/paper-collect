"""
论文工具集 - 导出、下载、管理一体化工具
"""
import os
import sqlite3
import json
import requests
import time
import argparse
from pathlib import Path
from typing import List, Dict
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== PDF链接生成器 ====================

class PDFLinkGenerator:
    """生成论文PDF下载链接"""
    
    @staticmethod
    def get_iacr_pdf_link(url: str) -> str:
        """从IACR URL提取PDF链接"""
        if not url or 'eprint.iacr.org' not in url:
            return None
        try:
            parts = url.rstrip('/').split('/')
            if len(parts) >= 2:
                year, paper_id = parts[-2], parts[-1]
                return f"https://eprint.iacr.org/{year}/{paper_id}.pdf"
        except:
            pass
        return None
    
    @staticmethod
    def get_usenix_pdf_link(url: str, title: str) -> str:
        """构建USENIX PDF链接"""
        if not url or 'usenix.org' not in url:
            return None
        try:
            slug = title.lower()
            slug = ''.join(c if c.isalnum() or c == ' ' else '' for c in slug)
            slug = '-'.join(slug.split())[:50]
            return f"https://www.usenix.org/system/files/usenixsecurity25/usenixsecurity25-{slug}.pdf"
        except:
            pass
        return None
    
    @staticmethod
    def get_ndss_pdf_link(url: str) -> str:
        """NDSS使用详情页链接"""
        if url and 'ndss-symposium.org' in url:
            return url
        return None
    
    @staticmethod
    def get_ieee_sp_pdf_link(url: str) -> str:
        """IEEE S&P使用会议主页"""
        if url and 'ieee-security.org' in url:
            return url
        return None
    
    @staticmethod
    def generate_pdf_link(paper: Dict) -> str:
        """为论文生成PDF链接"""
        url = paper.get('url', '')
        conference = paper.get('conference', '')
        title = paper.get('title', '')
        
        if 'CRYPTO' in conference or 'EUROCRYPT' in conference or 'ASIACRYPT' in conference:
            return PDFLinkGenerator.get_iacr_pdf_link(url)
        elif 'USENIX' in conference:
            return PDFLinkGenerator.get_usenix_pdf_link(url, title)
        elif 'NDSS' in conference:
            return PDFLinkGenerator.get_ndss_pdf_link(url)
        elif 'S&P' in conference or 'S & P' in conference:
            return PDFLinkGenerator.get_ieee_sp_pdf_link(url)
        
        return None


# ==================== PDF下载器 ====================

class PDFDownloader:
    """PDF批量下载器"""
    
    def __init__(self, db_path='data/papers.db', output_dir='data/pdfs'):
        self.db_path = db_path
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    def sanitize_filename(self, filename: str) -> str:
        """清理文件名"""
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        return filename[:200]
    
    def download_pdf(self, paper: Dict, timeout: int = 30) -> bool:
        """下载单个PDF"""
        if not paper['pdf_url']:
            return False
        
        conference = paper['conference'].replace(' ', '_').replace('/', '_')
        year = paper['year']
        title = self.sanitize_filename(paper['title'])
        
        conf_dir = Path(self.output_dir) / f"{conference}_{year}"
        conf_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{paper['id']}_{title}.pdf"
        filepath = conf_dir / filename
        
        if filepath.exists():
            return True
        
        try:
            response = self.session.get(paper['pdf_url'], timeout=timeout, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"✓ 下载成功: {paper['title'][:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"✗ 下载失败 [{paper['id']}]: {str(e)[:100]}")
            return False
    
    def get_papers_to_download(self, conference: str = None, year: int = None, 
                                limit: int = None) -> List[Dict]:
        """获取需要下载的论文列表"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT id, title, conference, year, pdf_url
            FROM papers
            WHERE pdf_url IS NOT NULL AND pdf_url != ''
        """
        params = []
        
        if conference:
            query += " AND conference = ?"
            params.append(conference)
        
        if year:
            query += " AND year = ?"
            params.append(year)
        
        query += " ORDER BY conference, year DESC, title"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        papers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return papers
    
    def download_batch(self, conference: str = None, year: int = None, 
                       limit: int = None, max_workers: int = 5, delay: float = 0.5):
        """批量下载PDF"""
        papers = self.get_papers_to_download(conference, year, limit)
        
        if not papers:
            logger.warning("没有找到需要下载的论文")
            return
        
        logger.info(f"找到 {len(papers)} 篇论文需要下载")
        
        stats = {'total': len(papers), 'success': 0, 'failed': 0}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            for paper in papers:
                time.sleep(delay)
                future = executor.submit(self.download_pdf, paper)
                futures[future] = paper
            
            for future in as_completed(futures):
                try:
                    success = future.result()
                    if success:
                        stats['success'] += 1
                    else:
                        stats['failed'] += 1
                except Exception:
                    stats['failed'] += 1
        
        logger.info("\n" + "="*60)
        logger.info(f"下载统计: 总计 {stats['total']}, 成功 {stats['success']}, "
                   f"失败 {stats['failed']}, 成功率 {stats['success']/stats['total']*100:.1f}%")
        logger.info("="*60)


# ==================== 下载管理器 ====================

class DownloadManager:
    """管理PDF下载状态"""
    
    def __init__(self, db_path='data/papers.db', pdf_dir='data/pdfs'):
        self.db_path = db_path
        self.pdf_dir = pdf_dir
    
    def update_download_status(self):
        """扫描PDF目录，更新下载状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, conference, year
            FROM papers
            WHERE pdf_url IS NOT NULL AND pdf_url != ''
        """)
        
        papers = cursor.fetchall()
        updated = 0
        
        for paper_id, title, conference, year in papers:
            conf_dir = f"{conference.replace(' ', '_').replace('/', '_')}_{year}"
            pdf_path = Path(self.pdf_dir) / conf_dir
            
            downloaded = False
            if pdf_path.exists():
                for file in pdf_path.glob(f"{paper_id}_*.pdf"):
                    if file.is_file() and file.stat().st_size > 1024:
                        downloaded = True
                        break
            
            status = 'downloaded' if downloaded else 'pending'
            cursor.execute("UPDATE papers SET download_status = ? WHERE id = ?", 
                          (status, paper_id))
            updated += 1
        
        conn.commit()
        conn.close()
        
        print(f"✓ 已更新 {updated} 条论文的下载状态")
    
    def show_stats(self):
        """显示下载统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN pdf_url IS NOT NULL AND pdf_url != '' THEN 1 ELSE 0 END) as has_link,
                SUM(CASE WHEN download_status = 'downloaded' THEN 1 ELSE 0 END) as downloaded
            FROM papers
        """)
        total, has_link, downloaded = cursor.fetchone()
        
        cursor.execute("""
            SELECT 
                conference,
                COUNT(*) as total,
                SUM(CASE WHEN download_status = 'downloaded' THEN 1 ELSE 0 END) as downloaded,
                SUM(CASE WHEN pdf_url IS NOT NULL AND pdf_url != '' THEN 1 ELSE 0 END) as has_link
            FROM papers
            GROUP BY conference
            ORDER BY conference
        """)
        by_conference = cursor.fetchall()
        conn.close()
        
        print("\n" + "="*60)
        print("PDF 下载统计")
        print("="*60)
        print(f"\n总体统计:")
        print(f"  总论文数: {total}")
        print(f"  有下载链接: {has_link} ({has_link/total*100:.1f}%)")
        if has_link > 0:
            print(f"  已下载: {downloaded} ({downloaded/has_link*100:.1f}%)")
        print(f"\n按会议统计:")
        print(f"{'会议':<20} {'总数':>6} {'有链接':>8} {'已下载':>8} {'进度':>8}")
        print("-"*60)
        
        for conf, total, downloaded, has_link in by_conference:
            progress = f"{downloaded}/{has_link}" if has_link > 0 else "0/0"
            pct = f"({downloaded/has_link*100:.0f}%)" if has_link > 0 else "(0%)"
            print(f"{conf:<20} {total:>6} {has_link:>8} {downloaded:>8} {progress:>8} {pct}")
        
        print("="*60 + "\n")


# ==================== JSON导出器 ====================

class JSONExporter:
    """导出数据为JSON格式"""
    
    def __init__(self, db_path='data/papers.db'):
        self.db_path = db_path
    
    def export_all(self, output_file='data/papers_all.json'):
        """导出所有论文到单个JSON"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM papers ORDER BY conference, year DESC, title")
        papers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        data = {
            'metadata': {
                'total': len(papers),
                'exported_at': datetime.now().isoformat(),
                'conferences': list(set(p['conference'] for p in papers))
            },
            'papers': papers
        }
        
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 已导出 {len(papers)} 篇论文到 {output_file}")
    
    def export_by_conference(self, output_dir='data/json'):
        """按会议分别导出"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT conference, year FROM papers ORDER BY conference, year")
        conferences = cursor.fetchall()
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for conference, year in conferences:
            cursor.execute("""
                SELECT * FROM papers 
                WHERE conference = ? AND year = ?
                ORDER BY title
            """, (conference, year))
            
            papers = [dict(row) for row in cursor.fetchall()]
            
            filename = f"{conference.replace(' ', '_').replace('/', '_')}_{year}.json"
            filepath = Path(output_dir) / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(papers, f, ensure_ascii=False, indent=2)
            
            print(f"✓ {conference} {year}: {len(papers)} 篇 -> {filepath}")
        
        conn.close()
    
    def export_download_links(self, output_file='data/download_links.txt'):
        """导出PDF下载链接列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT conference, year, title, pdf_url
            FROM papers
            WHERE pdf_url IS NOT NULL AND pdf_url != ''
            ORDER BY conference, year DESC, title
        """)
        
        papers = cursor.fetchall()
        conn.close()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# 论文PDF下载链接列表\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 总计: {len(papers)} 篇论文\n\n")
            
            current_conf = None
            for conference, year, title, pdf_url in papers:
                conf_key = f"{conference} {year}"
                if conf_key != current_conf:
                    f.write(f"\n## {conf_key}\n\n")
                    current_conf = conf_key
                
                f.write(f"{pdf_url}  # {title[:80]}\n")
        
        print(f"✓ 已导出 {len(papers)} 个下载链接到 {output_file}")


# ==================== 主程序 ====================

def main():
    parser = argparse.ArgumentParser(
        description='论文工具集 - 导出、下载、管理',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 下载PDF
  python paper_tools.py download --limit 10
  python paper_tools.py download --conference CRYPTO
  
  # 导出数据
  python paper_tools.py export-json --mode all
  python paper_tools.py export-json --mode by-conference
  python paper_tools.py export-links
  
  # 管理下载
  python paper_tools.py status-update
  python paper_tools.py status-show
        """)
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 下载命令
    download_parser = subparsers.add_parser('download', help='批量下载PDF')
    download_parser.add_argument('--conference', '-c', help='会议名称')
    download_parser.add_argument('--year', '-y', type=int, help='年份')
    download_parser.add_argument('--limit', '-l', type=int, help='限制数量')
    download_parser.add_argument('--workers', '-w', type=int, default=5, help='并发数')
    download_parser.add_argument('--delay', '-d', type=float, default=0.5, help='延迟(秒)')
    download_parser.add_argument('--output-dir', '-o', default='data/pdfs', help='输出目录')
    
    # 导出JSON
    export_json_parser = subparsers.add_parser('export-json', help='导出JSON')
    export_json_parser.add_argument('--mode', choices=['all', 'by-conference'], 
                                     default='all', help='导出模式')
    export_json_parser.add_argument('--output', help='输出文件路径')
    
    # 导出下载链接
    subparsers.add_parser('export-links', help='导出PDF下载链接列表')
    
    # 状态管理
    subparsers.add_parser('status-update', help='更新下载状态')
    subparsers.add_parser('status-show', help='显示下载统计')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行命令
    if args.command == 'download':
        downloader = PDFDownloader(output_dir=args.output_dir)
        downloader.download_batch(
            conference=args.conference,
            year=args.year,
            limit=args.limit,
            max_workers=args.workers,
            delay=args.delay
        )
    
    elif args.command == 'export-json':
        exporter = JSONExporter()
        if args.mode == 'all':
            output = args.output or 'data/papers_all.json'
            exporter.export_all(output)
        else:
            exporter.export_by_conference()
    
    elif args.command == 'export-links':
        exporter = JSONExporter()
        exporter.export_download_links()
    
    elif args.command == 'status-update':
        manager = DownloadManager()
        manager.update_download_status()
        manager.show_stats()
    
    elif args.command == 'status-show':
        manager = DownloadManager()
        manager.show_stats()


if __name__ == '__main__':
    main()
