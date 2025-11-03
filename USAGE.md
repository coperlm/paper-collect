# 使用指南

## 项目结构

```
paper-collect/
├── config/                 # 配置文件目录
│   ├── conferences.yaml    # 会议配置
│   └── settings.yaml       # 全局设置
├── crawlers/              # 爬虫模块
│   ├── __init__.py
│   ├── base_crawler.py    # 基础爬虫类
│   └── dblp_crawler.py    # DBLP爬虫
├── utils/                 # 工具模块
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库管理
│   ├── downloader.py      # PDF下载器
│   └── logger.py          # 日志配置
├── data/                  # 数据目录（自动创建）
│   ├── papers.db          # SQLite数据库
│   └── pdfs/              # PDF文件存储
├── logs/                  # 日志目录（自动创建）
├── main.py                # 主程序
├── requirements.txt       # 依赖包
└── README.md
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 查看帮助

```bash
python main.py --help
```

### 2. 收集论文元数据

收集所有配置的会议论文：
```bash
python main.py collect
```

收集特定会议：
```bash
python main.py collect --conferences crypto asiacrypt eurocrypt
```

收集特定年份：
```bash
python main.py collect --years 2023 2024
```

收集特定会议和年份：
```bash
python main.py collect --conferences crypto --years 2023 2024
```

### 3. 下载PDF文件

下载所有待下载的PDF：
```bash
python main.py download
```

下载特定会议的PDF：
```bash
python main.py download --conference "CRYPTO"
```

下载特定会议和年份的PDF：
```bash
python main.py download --conference "CRYPTO" --year 2024
```

限制下载数量：
```bash
python main.py download --limit 10
```

### 4. 重试失败的下载

```bash
python main.py retry
```

### 5. 查看统计信息

```bash
python main.py stats
```

### 6. 执行完整流程

一次性收集元数据并下载PDF：
```bash
python main.py all
```

指定会议和年份：
```bash
python main.py all --conferences crypto --years 2024
```

## 配置说明

### conferences.yaml

配置要收集的会议信息：
- `name`: 会议简称
- `full_name`: 会议全名
- `dblp_key`: DBLP的会议key
- `years`: 要收集的年份列表
- `url_template`: 会议官网URL模板（预留）

### settings.yaml

全局配置：
- `database.path`: 数据库文件路径
- `pdf_storage.base_path`: PDF存储目录
- `crawler.timeout`: 请求超时时间
- `crawler.retry_times`: 重试次数
- `crawler.retry_delay`: 重试延迟
- `logging.level`: 日志级别（DEBUG, INFO, WARNING, ERROR）

## 数据库结构

### papers表

存储论文元数据：
- `id`: 主键
- `title`: 标题
- `authors`: 作者（分号分隔）
- `abstract`: 摘要
- `year`: 年份
- `conference`: 会议名称
- `url`: DBLP URL
- `pdf_url`: PDF下载链接
- `pdf_path`: 本地PDF路径
- `doi`: DOI
- `dblp_key`: DBLP唯一标识
- `download_status`: 下载状态（pending, downloading, completed, failed）
- `created_at`: 创建时间
- `updated_at`: 更新时间

### download_log表

记录下载历史：
- `id`: 主键
- `paper_id`: 论文ID
- `attempt_time`: 尝试时间
- `status`: 状态
- `error_message`: 错误信息

## 常见问题

### 1. 某些论文没有PDF链接

DBLP主要提供元数据，PDF链接需要从各会议官网获取。当前版本从DBLP的`ee`字段获取PDF链接，部分论文可能没有。

### 2. 下载失败

可能的原因：
- 网络连接问题
- PDF链接失效
- 需要访问权限

使用 `python main.py retry` 重试失败的下载。

### 3. 修改配置后如何应用

直接修改配置文件后再次运行命令即可，程序会读取最新配置。

### 4. 如何查看详细日志

在 `config/settings.yaml` 中将日志级别改为 `DEBUG`：
```yaml
logging:
  level: "DEBUG"
```

## 模块化设计

项目采用模块化设计，便于调试和扩展：

1. **utils/database.py**: 独立的数据库操作模块
2. **utils/downloader.py**: 独立的PDF下载模块
3. **crawlers/base_crawler.py**: 可复用的基础爬虫类
4. **crawlers/dblp_crawler.py**: DBLP专用爬虫
5. **main.py**: 主程序，整合各模块

如需添加新的会议专用爬虫，只需继承 `BaseCrawler` 类并实现 `crawl` 方法。

## 扩展开发

### 添加新的会议爬虫

1. 在 `crawlers/` 目录创建新文件，如 `iacr_crawler.py`
2. 继承 `BaseCrawler` 类
3. 实现 `crawl` 方法，返回论文列表
4. 在 `main.py` 中集成

示例：
```python
from crawlers.base_crawler import BaseCrawler

class IACRCrawler(BaseCrawler):
    def crawl(self, conference, year):
        # 实现爬取逻辑
        return papers
```

## 注意事项

1. 请遵守网站的robots.txt和使用条款
2. 避免过于频繁的请求
3. 某些PDF可能需要机构访问权限
4. 定期备份数据库文件
