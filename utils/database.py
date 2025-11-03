"""
数据库模块 - 用于管理论文元数据
"""
import sqlite3
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"创建数据库目录: {db_dir}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 创建论文表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                abstract TEXT,
                year INTEGER,
                conference TEXT NOT NULL,
                url TEXT,
                pdf_url TEXT,
                pdf_path TEXT,
                doi TEXT,
                dblp_key TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                download_status TEXT DEFAULT 'pending',
                notes TEXT
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conference_year 
            ON papers(conference, year)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_download_status 
            ON papers(download_status)
        """)
        
        # 创建下载日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS download_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER,
                attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                error_message TEXT,
                FOREIGN KEY (paper_id) REFERENCES papers(id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"数据库初始化完成: {self.db_path}")
    
    def insert_paper(self, paper_data: Dict[str, Any]) -> Optional[int]:
        """
        插入论文记录
        
        Args:
            paper_data: 论文数据字典
            
        Returns:
            插入的记录ID，如果已存在则返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO papers (
                    title, authors, abstract, year, conference, 
                    url, pdf_url, doi, dblp_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                paper_data.get('title'),
                paper_data.get('authors'),
                paper_data.get('abstract'),
                paper_data.get('year'),
                paper_data.get('conference'),
                paper_data.get('url'),
                paper_data.get('pdf_url'),
                paper_data.get('doi'),
                paper_data.get('dblp_key')
            ))
            conn.commit()
            paper_id = cursor.lastrowid
            logger.info(f"插入论文: {paper_data.get('title')[:50]}...")
            return paper_id
        except sqlite3.IntegrityError:
            logger.debug(f"论文已存在: {paper_data.get('dblp_key')}")
            return None
        except Exception as e:
            logger.error(f"插入论文失败: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def update_paper(self, paper_id: int, update_data: Dict[str, Any]) -> bool:
        """
        更新论文记录
        
        Args:
            paper_id: 论文ID
            update_data: 要更新的数据字典
            
        Returns:
            是否更新成功
        """
        if not update_data:
            return False
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 构建SET子句
            set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            values = list(update_data.values()) + [paper_id]
            
            cursor.execute(f"""
                UPDATE papers SET {set_clause} WHERE id = ?
            """, values)
            
            conn.commit()
            logger.debug(f"更新论文ID {paper_id}")
            return True
        except Exception as e:
            logger.error(f"更新论文失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_paper_by_id(self, paper_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取论文"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_papers_by_conference(self, conference: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        根据会议名称获取论文列表
        
        Args:
            conference: 会议名称
            year: 年份（可选）
            
        Returns:
            论文列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if year:
            cursor.execute(
                "SELECT * FROM papers WHERE conference = ? AND year = ? ORDER BY title",
                (conference, year)
            )
        else:
            cursor.execute(
                "SELECT * FROM papers WHERE conference = ? ORDER BY year DESC, title",
                (conference,)
            )
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_pending_downloads(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取待下载的论文
        
        Args:
            limit: 返回数量限制
            
        Returns:
            待下载论文列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM papers WHERE download_status = 'pending' AND pdf_url IS NOT NULL"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def update_download_status(self, paper_id: int, status: str, pdf_path: Optional[str] = None, error_msg: Optional[str] = None):
        """
        更新下载状态
        
        Args:
            paper_id: 论文ID
            status: 状态 (pending, downloading, completed, failed)
            pdf_path: PDF文件路径
            error_msg: 错误信息
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 更新论文表
            if pdf_path:
                cursor.execute("""
                    UPDATE papers 
                    SET download_status = ?, pdf_path = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, pdf_path, paper_id))
            else:
                cursor.execute("""
                    UPDATE papers 
                    SET download_status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, paper_id))
            
            # 插入下载日志
            cursor.execute("""
                INSERT INTO download_log (paper_id, status, error_message)
                VALUES (?, ?, ?)
            """, (paper_id, status, error_msg))
            
            conn.commit()
        except Exception as e:
            logger.error(f"更新下载状态失败: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 总论文数
        cursor.execute("SELECT COUNT(*) as total FROM papers")
        total = cursor.fetchone()['total']
        
        # 按会议统计
        cursor.execute("""
            SELECT conference, COUNT(*) as count 
            FROM papers 
            GROUP BY conference
        """)
        by_conference = {row['conference']: row['count'] for row in cursor.fetchall()}
        
        # 下载状态统计
        cursor.execute("""
            SELECT download_status, COUNT(*) as count 
            FROM papers 
            GROUP BY download_status
        """)
        by_status = {row['download_status']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'total': total,
            'by_conference': by_conference,
            'by_status': by_status
        }
