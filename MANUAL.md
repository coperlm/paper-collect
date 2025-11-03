# Paper Collector - 完整使用手册

> 本手册提供所有功能的详细说明，适合深度使用和二次开发

---

## 📑 目录

- [安装与配置](#安装与配置)
- [核心功能](#核心功能)
- [数据访问](#数据访问)
- [高级功能](#高级功能)
- [配置详解](#配置详解)
- [API参考](#api参考)
- [常见问题](#常见问题)
- [开发指南](#开发指南)

---

## 安装与配置

### 系统要求

- Python 3.7+
- Windows/Linux/macOS
- 网络连接（访问DBLP和Semantic Scholar）

### 安装步骤

```bash
# 1. 克隆或下载项目
git clone https://github.com/coperlm/paper-collect.git
cd paper-collect

# 2. 安装依赖
pip install -r requirements.txt

# 3. 验证安装
python main.py --help
```

### 依赖说明

- `requests` - HTTP请求
- `beautifulsoup4` + `lxml` - HTML解析
- `pyyaml` - 配置文件解析
- `tqdm` - 进度条显示
- `selenium` - （可选）用于复杂网页爬取

---

## 核心功能

### 1. 收集论文元数据

从DBLP获取论文的基本信息。

#### 基本用法

```bash
# 收集所有配置的会议
python main.py collect

# 收集特定会议
python main.py collect --conferences crypto

# 收集特定年份
python main.py collect --years 2024

# 组合条件
python main.py collect --conferences crypto asiacrypt --years 2023 2024
```

#### 工作原理

1. 读取 `config/conferences.yaml` 中的会议配置
2. 通过DBLP API查询论文
3. 解析返回的JSON数据
4. 存储到SQLite数据库

#### 数据字段

- `title` - 论文标题
- `authors` - 作者列表（分号分隔）
- `year` - 发表年份
- `conference` - 会议名称
- `url` - DBLP链接
- `doi` - DOI标识
- `dblp_key` - DBLP唯一键

### 2. 获取论文摘要

通过Semantic Scholar API补充摘要信息。

#### 基本用法

```bash
# 为所有论文获取摘要
python main.py enrich

# 限制数量
python main.py enrich --limit 10

# 特定会议
python main.py enrich --conference "CRYPTO" --year 2024
```

#### 智能获取（推荐）

```bash
# 使用智能脚本，自动过滤会议文集
python enrich_smart.py 50
```

**智能过滤规则：**
- 排除包含 "Proceedings", "Conference" 的标题
- 排除ISBN格式的DOI
- 只处理真正的单篇论文

#### 工作原理

1. 从数据库读取缺少摘要的论文
2. 优先使用DOI查询Semantic Scholar
3. DOI失败则使用标题搜索
4. 更新数据库中的abstract字段
5. 附加引用数和发表日期到notes字段

#### 速率限制

- Semantic Scholar限制：每秒1次请求
- 本工具设置：每次间隔2秒
- 建议分批处理，避免一次处理太多

### 3. 下载PDF文件

批量下载论文PDF文件。

#### 基本用法

```bash
# 下载所有待下载的PDF
python main.py download

# 限制下载数量
python main.py download --limit 10

# 下载特定会议
python main.py download --conference "CRYPTO"

# 下载特定年份
python main.py download --conference "CRYPTO" --year 2024
```

#### 重试失败的下载

```bash
python main.py retry
```

#### 存储结构

```
data/pdfs/
├── CRYPTO/
│   ├── 2024/
│   │   ├── paper1.pdf
│   │   └── paper2.pdf
│   └── 2023/
├── ASIACRYPT/
└── ...
```

#### 下载状态

- `pending` - 待下载
- `downloading` - 下载中
- `completed` - 已完成
- `failed` - 失败

### 4. 导出JSON数据

将数据库内容导出为JSON格式。

#### 基本用法

```bash
# 自动导出所有格式
python main.py export

# 指定导出模式
python main.py export --mode all         # 单个完整文件
python main.py export --mode conference  # 按会议分文件
python main.py export --mode year        # 按会议和年份分文件
python main.py export --mode summary     # 统计摘要
python main.py export --mode readable    # 易读格式
```

#### 生成的文件

1. **summary.json** - 统计信息
   ```json
   {
     "total": 809,
     "with_abstract": 2,
     "by_conference": {...},
     "by_download_status": {...}
   }
   ```

2. **papers_readable.json** - 易读格式
   ```json
   {
     "total": 809,
     "conferences": {
       "CRYPTO": [
         {
           "id": 1,
           "title": "...",
           "authors": ["Author1", "Author2"],
           "abstract": "...",
           "downloaded": true
         }
       ]
     }
   }
   ```

3. **all_papers.json** - 完整数据（所有字段）

4. **{会议名}.json** - 各会议单独文件

### 5. 可视化查看

使用本地网页界面查看和搜索论文。

#### 启动查看器

```bash
python start_viewer.py
```

浏览器自动打开 http://localhost:8000/viewer.html

#### 功能特性

- ✅ 实时搜索（标题、作者）
- ✅ 多条件筛选（会议、年份、状态）
- ✅ 显示论文摘要
- ✅ 点击访问DOI和PDF链接
- ✅ 导出筛选结果为CSV
- ✅ 响应式设计

#### 解决CORS问题

直接打开HTML文件会遇到CORS错误，必须使用本地服务器：
```bash
python start_viewer.py  # 自动启动服务器
```

---

## 数据访问

### 方式一：网页查看器（推荐）

**优点：**
- 可视化界面
- 实时搜索和筛选
- 无需编程知识
- 导出CSV

**使用：**
```bash
python start_viewer.py
```

### 方式二：JSON文件

**优点：**
- 明文可读
- 易于分享
- 适合编程处理

**Python示例：**
```python
import json

with open('data/json/papers_readable.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 获取所有CRYPTO论文
crypto_papers = data['conferences']['CRYPTO']

# 搜索关键词
keyword_papers = [p for p in crypto_papers 
                  if 'quantum' in p['title'].lower()]

# 统计有摘要的论文
with_abstract = [p for p in crypto_papers if p['abstract']]
print(f"有摘要: {len(with_abstract)}/{len(crypto_papers)}")

# 按作者筛选
author_papers = [p for p in crypto_papers 
                 if any('Zhang' in a for a in p['authors'])]
```

**JavaScript示例：**
```javascript
fetch('data/json/papers_readable.json')
  .then(response => response.json())
  .then(data => {
    const papers = data.conferences.CRYPTO;
    
    // 查找2024年的论文
    const papers2024 = papers.filter(p => p.year === 2024);
    
    // 显示
    papers2024.forEach(p => {
      console.log(p.title);
    });
  });
```

### 方式三：数据库查询

**优点：**
- 查询高效
- 支持复杂查询
- 适合大规模数据

**命令行工具：**
```bash
# 列出论文
python query_db.py list --conference "CRYPTO" --year 2024 --limit 20

# 搜索
python query_db.py search "quantum cryptography"

# 显示详情
python query_db.py detail 305

# 导出CSV
python query_db.py export crypto_2024.csv --conference "CRYPTO" --year 2024

# 查看统计
python query_db.py stats
```

**SQL查询：**
```python
import sqlite3

conn = sqlite3.connect('data/papers.db')
cursor = conn.cursor()

# 查询示例
cursor.execute("""
    SELECT title, authors, year 
    FROM papers 
    WHERE conference = 'CRYPTO' 
      AND year >= 2020
      AND abstract IS NOT NULL
    ORDER BY year DESC
""")

for row in cursor.fetchall():
    print(row)

conn.close()
```

**复杂查询示例：**
```sql
-- 统计各年份论文数
SELECT year, COUNT(*) as count
FROM papers
GROUP BY year
ORDER BY year DESC;

-- 查找特定作者的所有论文
SELECT title, conference, year
FROM papers
WHERE authors LIKE '%Zhang%'
ORDER BY year DESC;

-- 统计有摘要的比例
SELECT 
    conference,
    COUNT(*) as total,
    SUM(CASE WHEN abstract IS NOT NULL THEN 1 ELSE 0 END) as with_abstract,
    ROUND(100.0 * SUM(CASE WHEN abstract IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as percentage
FROM papers
GROUP BY conference;

-- 查找下载失败的论文
SELECT id, title, pdf_url
FROM papers
WHERE download_status = 'failed'
  AND pdf_url IS NOT NULL;
```

---

## 高级功能

### 一键完成

执行完整流程：收集 → 摘要 → 下载 → 导出

```bash
python main.py all

# 包含摘要获取
python main.py all --with-abstract

# 指定会议和年份
python main.py all --conferences crypto --years 2024 --with-abstract
```

### 查看统计信息

```bash
python main.py stats
```

输出示例：
```
============================================================
数据库统计信息:
  总论文数: 809
  按会议统计:
    CRYPTO: 809
  下载状态:
    pending: 804
    completed: 5
============================================================
```

### 批量导出

```python
# 使用Python脚本批量操作
from utils.json_exporter import JSONExporter

exporter = JSONExporter()

# 按会议导出
exporter.export_by_conference()

# 按年份导出
exporter.export_by_conference_and_year()

# 自定义导出
import sqlite3
conn = sqlite3.connect('data/papers.db')
cursor = conn.cursor()

# 自定义查询
cursor.execute("SELECT * FROM papers WHERE year = 2024")
papers_2024 = [dict(row) for row in cursor.fetchall()]

import json
with open('custom_export.json', 'w', encoding='utf-8') as f:
    json.dump(papers_2024, f, ensure_ascii=False, indent=2)
```

### Windows快速启动脚本

```powershell
.\start.ps1
```

交互式菜单：
```
1. 收集所有会议的论文元数据
2. 收集三大密码学会议 (2020-2024)
3. 收集Big4安全会议 (2020-2024)
4. 收集2024年的所有论文
5. 下载所有待下载的PDF
6. 查看统计信息
7. 执行完整流程（收集+下载）
8. 重试失败的下载
9. 自定义命令
0. 退出
```

---

## 配置详解

### conferences.yaml

定义要收集的会议。

```yaml
conferences:
  crypto:  # 配置键
    - name: "CRYPTO"            # 会议名称（显示用）
      full_name: "International Cryptology Conference"  # 全称
      dblp_key: "conf/crypto"   # DBLP中的键
      years: [2020, 2021, 2022, 2023, 2024]  # 要收集的年份
      url_template: "https://..."  # 会议官网（预留）
  
  # 添加新会议
  my_conference:
    - name: "MyConf"
      dblp_key: "conf/myconf"
      years: [2024]
```

**DBLP Key查找：**
1. 访问 https://dblp.org/
2. 搜索会议名称
3. 查看URL中的路径，如 `conf/crypto` 就是DBLP key

### settings.yaml

全局配置参数。

```yaml
settings:
  # 数据库配置
  database:
    path: "data/papers.db"
  
  # PDF存储配置
  pdf_storage:
    base_path: "data/pdfs"
    organize_by: "conference"  # conference, year, or both
  
  # JSON存储配置
  json_storage:
    path: "data/json"
    auto_export: true
  
  # 爬虫配置
  crawler:
    user_agent: "Mozilla/5.0 ..."
    timeout: 30          # 请求超时（秒）
    retry_times: 3       # 重试次数
    retry_delay: 2       # 重试延迟（秒）
    concurrent_downloads: 3  # 并发下载数
  
  # 日志配置
  logging:
    level: "INFO"        # DEBUG, INFO, WARNING, ERROR
    file: "logs/crawler.log"
    console: true
  
  # DBLP API配置
  dblp:
    api_url: "https://dblp.org/search/publ/api"
    format: "json"
    max_results: 1000
```

---

## API参考

### 数据库API

```python
from utils.database import DatabaseManager

db = DatabaseManager('data/papers.db')

# 插入论文
paper_id = db.insert_paper({
    'title': '...',
    'authors': '...',
    'year': 2024,
    'conference': 'CRYPTO',
    'doi': '...'
})

# 更新论文
db.update_paper(paper_id, {'abstract': '...'})

# 查询论文
papers = db.get_papers_by_conference('CRYPTO', 2024)

# 获取待下载列表
pending = db.get_pending_downloads(limit=10)

# 更新下载状态
db.update_download_status(paper_id, 'completed', pdf_path='...')

# 统计信息
stats = db.get_statistics()
```

### 爬虫API

```python
from crawlers.dblp_crawler import DBLPCrawler
from crawlers.semantic_scholar_crawler import SemanticScholarCrawler

# DBLP爬虫
dblp = DBLPCrawler(config)
papers = dblp.crawl('conf/crypto', 2024)

# Semantic Scholar爬虫
ss = SemanticScholarCrawler(config)
info = ss.get_paper_by_doi('10.1007/...')
result = ss.search_paper_by_title('Paper Title')
```

### 下载器API

```python
from utils.downloader import PDFDownloader

downloader = PDFDownloader(config, 'data/pdfs')

# 下载单个PDF
pdf_path = downloader.download(
    url='https://...',
    conference='CRYPTO',
    year=2024,
    filename='paper_title'
)

# 批量下载
stats = downloader.batch_download(papers, db_manager)
```

### JSON导出API

```python
from utils.json_exporter import JSONExporter

exporter = JSONExporter('data/papers.db', 'data/json')

# 导出所有论文
exporter.export_all('output.json')

# 按会议导出
files = exporter.export_by_conference()

# 按会议和年份导出
files = exporter.export_by_conference_and_year()

# 导出统计
exporter.export_summary()

# 易读格式
exporter.export_readable_format()

# 自动导出所有
exporter.auto_export()
```

---

## 常见问题

### Q1: 论文数量很多，如何优化？

**A: 分批处理**
```bash
# 按年份分批收集
for year in 2020 2021 2022 2023 2024; do
    python main.py collect --years $year
    python main.py export
done

# 限制每次处理数量
python main.py enrich --limit 100
python main.py download --limit 50
```

### Q2: Semantic Scholar API速率限制？

**A: 策略**
- 使用 `enrich_smart.py` 智能过滤
- 设置较小的limit
- 分多次运行
- 代码已内置2秒延迟

### Q3: PDF下载失败？

**A: 排查**
1. 检查 `pdf_url` 字段是否存在
2. 某些PDF需要机构访问权限
3. 使用 `python main.py retry` 重试
4. 查看日志 `logs/crawler.log`

### Q4: 如何查看下载进度？

**A:**
```bash
# 查看统计
python main.py stats

# 查看数据库
python query_db.py stats

# 查看JSON统计
cat data/json/summary.json
```

### Q5: 如何备份数据？

**A: 备份文件**
```bash
# 数据库
cp data/papers.db backup/papers_$(date +%Y%m%d).db

# JSON文件
tar -czf backup_json.tar.gz data/json/

# PDF文件
tar -czf backup_pdfs.tar.gz data/pdfs/
```

### Q6: 如何添加新会议？

**A: 编辑配置**
1. 在DBLP查找会议key
2. 编辑 `config/conferences.yaml`
3. 运行 `python main.py collect --conferences new_conf`

### Q7: JSON文件太大？

**A: 使用分文件导出**
```bash
# 按会议分文件
python main.py export --mode conference

# 按年份分文件
python main.py export --mode year

# 或直接用数据库查询
python query_db.py list --conference "CRYPTO"
```

### Q8: 如何导出特定字段？

**A: 自定义查询**
```python
import json
import sqlite3

conn = sqlite3.connect('data/papers.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT title, authors, year, doi, abstract
    FROM papers
    WHERE conference = 'CRYPTO'
""")

papers = []
for row in cursor.fetchall():
    papers.append({
        'title': row[0],
        'authors': row[1],
        'year': row[2],
        'doi': row[3],
        'abstract': row[4]
    })

with open('custom.json', 'w', encoding='utf-8') as f:
    json.dump(papers, f, ensure_ascii=False, indent=2)
```

### Q9: viewer.html显示空白？

**A: CORS问题**
不要直接双击打开HTML，使用：
```bash
python start_viewer.py
```

### Q10: 如何定时自动更新？

**A: 使用计划任务**

**Windows (任务计划程序):**
```powershell
# 创建每周一凌晨2点运行的任务
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\path\to\paper-collect\main.py all"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 2am
Register-ScheduledTask -TaskName "PaperCollector" -Action $action -Trigger $trigger
```

**Linux (crontab):**
```bash
# 每周一凌晨2点运行
0 2 * * 1 cd /path/to/paper-collect && python3 main.py all
```

---

## 开发指南

### 添加新的爬虫

创建 `crawlers/new_crawler.py`:

```python
from crawlers.base_crawler import BaseCrawler

class NewCrawler(BaseCrawler):
    def __init__(self, config):
        super().__init__(config)
        # 初始化
    
    def crawl(self, conference, year):
        # 实现爬取逻辑
        papers = []
        
        # 爬取代码
        url = f"https://example.com/{conference}/{year}"
        response = self.fetch(url)
        
        if response:
            soup = self.parse_html(response.text)
            # 解析HTML
            
        return papers
```

### 扩展数据库字段

修改 `utils/database.py` 中的表结构：

```python
cursor.execute("""
    CREATE TABLE IF NOT EXISTS papers (
        ...
        new_field TEXT,  # 添加新字段
        ...
    )
""")
```

### 自定义导出格式

修改 `utils/json_exporter.py`：

```python
class JSONExporter:
    def export_custom_format(self):
        # 自定义导出逻辑
        pass
```

### 测试

```bash
# 测试数据库
python -c "from utils.database import DatabaseManager; db = DatabaseManager('test.db')"

# 测试爬虫
python -c "from crawlers.dblp_crawler import DBLPCrawler; c = DBLPCrawler({}); print(c.crawl('conf/crypto', 2024)[:1])"
```

### 调试

设置日志级别为DEBUG：

`config/settings.yaml`:
```yaml
logging:
  level: "DEBUG"
```

查看详细日志：
```bash
tail -f logs/crawler.log
```

---

## 性能优化

### 并发下载

修改 `config/settings.yaml`:
```yaml
crawler:
  concurrent_downloads: 5  # 增加并发数
```

### 数据库索引

已自动创建的索引：
- `idx_conference_year` - 按会议和年份查询
- `idx_download_status` - 按下载状态查询

添加新索引：
```python
cursor.execute("""
    CREATE INDEX idx_doi ON papers(doi)
""")
```

### 缓存策略

```python
# 使用functools.lru_cache缓存结果
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_operation(param):
    # 耗时操作
    return result
```

---

## 数据分析示例

### 统计分析

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/papers.db')

# 读取数据
df = pd.read_sql_query("SELECT * FROM papers", conn)

# 统计各会议论文数
print(df['conference'].value_counts())

# 统计各年份论文数
print(df['year'].value_counts().sort_index())

# 有摘要的比例
abstract_ratio = df['abstract'].notna().sum() / len(df)
print(f"有摘要比例: {abstract_ratio:.2%}")

# 按会议统计平均年份
print(df.groupby('conference')['year'].mean())

conn.close()
```

### 可视化

```python
import matplotlib.pyplot as plt
import seaborn as sns

# 论文数量趋势
df.groupby('year').size().plot(kind='line', marker='o')
plt.title('论文数量趋势')
plt.xlabel('年份')
plt.ylabel('论文数')
plt.savefig('trend.png')

# 各会议分布
df['conference'].value_counts().plot(kind='bar')
plt.title('各会议论文数量')
plt.tight_layout()
plt.savefig('distribution.png')
```

---

## 贡献指南

欢迎贡献代码！

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 代码风格

- 使用Python 3.7+特性
- 遵循PEP 8规范
- 添加docstring注释
- 模块化设计

---

## 许可证

MIT License - 详见LICENSE文件

---

## 致谢

- [DBLP](https://dblp.org/) - 提供论文元数据
- [Semantic Scholar](https://www.semanticscholar.org/) - 提供论文摘要
- 所有贡献者

---

<div align="center">

**📧 联系方式**

如有问题或建议，欢迎提交Issue

Made with ❤️ by coperlm

</div>
