"""
PDF下载器 - 负责下载论文PDF文件
"""
import os
import logging
import time
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)


class PDFDownloader:
    """PDF下载器"""
    
    def __init__(self, config: Dict[str, Any], base_path: str = "data/pdfs"):
        """
        初始化PDF下载器
        
        Args:
            config: 配置字典
            base_path: PDF存储基础路径
        """
        self.config = config
        self.base_path = base_path
        self.timeout = config.get('timeout', 30)
        self.retry_times = config.get('retry_times', 3)
        self.retry_delay = config.get('retry_delay', 2)
        self.session = self._create_session()
        
        # 确保基础目录存在
        os.makedirs(base_path, exist_ok=True)
    
    def _create_session(self) -> requests.Session:
        """创建HTTP会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.config.get('user_agent',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        })
        return session
    
    def download(self, url: str, conference: str, year: int, 
                 filename: str, force: bool = False) -> Optional[str]:
        """
        下载PDF文件
        
        Args:
            url: PDF的URL
            conference: 会议名称
            year: 年份
            filename: 文件名（不含扩展名）
            force: 是否强制重新下载
            
        Returns:
            保存的文件路径，失败返回None
        """
        # 创建目录结构: base_path/conference/year/
        save_dir = os.path.join(self.base_path, conference, str(year))
        os.makedirs(save_dir, exist_ok=True)
        
        # 清理文件名
        safe_filename = self._sanitize_filename(filename)
        if not safe_filename.endswith('.pdf'):
            safe_filename += '.pdf'
        
        save_path = os.path.join(save_dir, safe_filename)
        
        # 如果文件已存在且不强制下载
        if os.path.exists(save_path) and not force:
            logger.info(f"文件已存在: {save_path}")
            return save_path
        
        # 尝试下载
        for attempt in range(self.retry_times):
            try:
                logger.info(f"下载PDF (尝试 {attempt + 1}/{self.retry_times}): {url}")
                
                response = self.session.get(url, timeout=self.timeout, stream=True)
                response.raise_for_status()
                
                # 获取文件大小
                total_size = int(response.headers.get('content-length', 0))
                
                # 下载文件
                with open(save_path, 'wb') as f:
                    if total_size == 0:
                        f.write(response.content)
                    else:
                        # 使用进度条
                        with tqdm(total=total_size, unit='iB', unit_scale=True, 
                                 desc=safe_filename[:30], leave=False) as pbar:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    pbar.update(len(chunk))
                
                # 验证文件
                if os.path.getsize(save_path) > 0:
                    logger.info(f"下载成功: {save_path}")
                    return save_path
                else:
                    logger.warning(f"下载的文件为空: {save_path}")
                    os.remove(save_path)
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"下载失败 ({attempt + 1}/{self.retry_times}): {e}")
                
                if os.path.exists(save_path):
                    os.remove(save_path)
                
                if attempt < self.retry_times - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
            
            except Exception as e:
                logger.error(f"下载异常: {e}")
                if os.path.exists(save_path):
                    os.remove(save_path)
                break
        
        logger.error(f"下载最终失败: {url}")
        return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            安全的文件名
        """
        # Windows不允许的字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 限制文件名长度
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename.strip()
    
    def batch_download(self, papers: list, db_manager) -> Dict[str, int]:
        """
        批量下载论文
        
        Args:
            papers: 论文列表
            db_manager: 数据库管理器
            
        Returns:
            下载统计信息
        """
        stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        logger.info(f"开始批量下载，共 {len(papers)} 篇论文")
        
        for paper in tqdm(papers, desc="下载PDF"):
            paper_id = paper['id']
            pdf_url = paper.get('pdf_url')
            
            if not pdf_url:
                logger.debug(f"跳过无PDF链接的论文: {paper['title'][:50]}")
                stats['skipped'] += 1
                continue
            
            # 更新状态为下载中
            db_manager.update_download_status(paper_id, 'downloading')
            
            # 下载
            pdf_path = self.download(
                url=pdf_url,
                conference=paper['conference'],
                year=paper['year'],
                filename=paper['title']
            )
            
            if pdf_path:
                db_manager.update_download_status(paper_id, 'completed', pdf_path=pdf_path)
                stats['success'] += 1
            else:
                db_manager.update_download_status(
                    paper_id, 'failed', 
                    error_msg="下载失败"
                )
                stats['failed'] += 1
        
        logger.info(f"批量下载完成: 成功 {stats['success']}, 失败 {stats['failed']}, 跳过 {stats['skipped']}")
        return stats
    
    def close(self):
        """关闭会话"""
        self.session.close()
