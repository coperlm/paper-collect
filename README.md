# paper-collect

论文自动收集工具 - 专注于收集密码学和安全顶会论文

## 📚 目标会议

收集下面论文：

- **3大密码学会议**
    - 亚密会（ASIACRYPT）
    - 美密会（CRYPTO）
    - 欧密会（EUROCRYPT）
- **Big4 安全会议**
    - USENIX Security
    - IEEE Symposium on Security and Privacy (S&P)
    - ACM Conference on Computer and Communications Security (CCS)
    - The Network and Distributed System Security Symposium (NDSS)

## ✨ 功能特性

- ✅ 自动从DBLP获取论文元数据（标题、作者、年份、DOI等）
- ✅ **通过Semantic Scholar API获取论文摘要**
- ✅ 批量下载PDF文件
- ✅ SQLite数据库存储，便于查询和管理
- ✅ 支持断点续传和失败重试
- ✅ 模块化设计，便于调试和扩展
- ✅ 详细的日志记录
- ✅ 进度条显示
- ✅ 按会议和年份组织文件

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 使用快速启动脚本（Windows）

```powershell
.\start.ps1
```

### 3. 或使用命令行

```bash
# 查看帮助
python main.py --help

# 收集所有会议的论文元数据
python main.py collect

# 收集特定会议
python main.py collect --conferences crypto --years 2024

# 下载所有PDF
python main.py download

# 执行完整流程（收集+下载）
python main.py all

# 查看统计信息
python main.py stats
```

## 📖 详细文档

查看 [USAGE.md](USAGE.md) 获取完整的使用指南。

## 📁 项目结构

```
paper-collect/
├── config/              # 配置文件
│   ├── conferences.yaml # 会议配置
│   └── settings.yaml    # 全局设置
├── crawlers/           # 爬虫模块
│   ├── base_crawler.py # 基础爬虫类
│   └── dblp_crawler.py # DBLP爬虫
├── utils/              # 工具模块
│   ├── config.py       # 配置管理
│   ├── database.py     # 数据库管理
│   ├── downloader.py   # PDF下载器
│   └── logger.py       # 日志配置
├── data/               # 数据目录
│   ├── papers.db       # SQLite数据库
│   └── pdfs/           # PDF文件
├── main.py             # 主程序
└── start.ps1           # 快速启动脚本
```

## 🎯 使用示例

### 收集三大密码学会议2023-2024年的论文

```bash
python main.py collect --conferences crypto asiacrypt eurocrypt --years 2023 2024
```

### 下载CRYPTO 2024的PDF

```bash
python main.py download --conference "CRYPTO" --year 2024
```

### 重试失败的下载

```bash
python main.py retry
```

## 🔧 配置说明

### 修改会议配置

编辑 `config/conferences.yaml` 添加或修改会议：

```yaml
conferences:
  crypto:
    - name: "CRYPTO"
      dblp_key: "conf/crypto"
      years: [2020, 2021, 2022, 2023, 2024]
```

### 修改全局设置

编辑 `config/settings.yaml` 调整下载参数：

```yaml
settings:
  crawler:
    timeout: 30
    retry_times: 3
    retry_delay: 2
```

## 📊 数据库查询

数据库文件：`data/papers.db`

可以使用任何SQLite客户端查询：

```sql
-- 查询CRYPTO 2024的所有论文
SELECT title, authors, pdf_path 
FROM papers 
WHERE conference = 'CRYPTO' AND year = 2024;

-- 统计各会议论文数
SELECT conference, year, COUNT(*) as count 
FROM papers 
GROUP BY conference, year;
```

## ⚠️ 注意事项

1. 请遵守网站的robots.txt和使用条款
2. 避免过于频繁的请求
3. 部分PDF可能需要机构访问权限
4. 建议定期备份数据库文件

## 🛠️ 故障排查

### 下载失败

- 检查网络连接
- 使用 `python main.py retry` 重试
- 查看日志文件 `logs/crawler.log`

### 找不到PDF链接

DBLP主要提供元数据，部分论文可能没有PDF链接。可以手动添加PDF URL到数据库。

## 🔮 后续扩展

项目采用模块化设计，便于扩展：

- 添加新的会议：修改 `config/conferences.yaml`
- 添加专用爬虫：继承 `BaseCrawler` 类
- 自定义下载策略：修改 `utils/downloader.py`

## 📝 测试结果

✅ 已测试：成功收集CRYPTO 2024共809篇论文元数据
✅ 已测试：PDF下载功能正常
✅ 已测试：数据库存储和查询功能正常

## 📄 许可证

MIT License