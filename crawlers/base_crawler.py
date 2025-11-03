"""
基础爬虫类 - 提供通用的爬虫功能
"""
import requests
import logging
import time
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """基础爬虫抽象类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化爬虫
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.session = self._create_session()
        self.timeout = config.get('timeout', 30)
        self.retry_times = config.get('retry_times', 3)
        self.retry_delay = config.get('retry_delay', 2)
    
    def _create_session(self) -> requests.Session:
        """创建HTTP会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.config.get('user_agent', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        })
        return session
    
    def fetch(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """
        发送HTTP请求，支持重试
        
        Args:
            url: 目标URL
            method: HTTP方法
            **kwargs: 其他请求参数
            
        Returns:
            响应对象，失败返回None
        """
        for attempt in range(self.retry_times):
            try:
                logger.debug(f"请求 {url} (尝试 {attempt + 1}/{self.retry_times})")
                
                if method.upper() == 'GET':
                    response = self.session.get(url, timeout=self.timeout, **kwargs)
                else:
                    response = self.session.post(url, timeout=self.timeout, **kwargs)
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"请求失败 ({attempt + 1}/{self.retry_times}): {e}")
                
                if attempt < self.retry_times - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"请求最终失败: {url}")
                    return None
    
    def parse_html(self, html: str) -> Optional[BeautifulSoup]:
        """
        解析HTML
        
        Args:
            html: HTML字符串
            
        Returns:
            BeautifulSoup对象
        """
        try:
            return BeautifulSoup(html, 'lxml')
        except Exception as e:
            logger.error(f"解析HTML失败: {e}")
            return None
    
    def _fetch_url(self, url: str) -> Optional[str]:
        """
        获取URL内容并返回文本
        
        Args:
            url: 目标URL
            
        Returns:
            HTML文本，失败返回None
        """
        response = self.fetch(url)
        if response:
            return response.text
        return None
    
    @abstractmethod
    def crawl(self, *args, **kwargs) -> Any:
        """
        爬取方法，由子类实现
        
        Returns:
            爬取结果
        """
        pass
    
    def close(self):
        """关闭会话"""
        self.session.close()
