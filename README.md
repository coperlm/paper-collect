# 📚 Security & Cryptography Paper Collector

**自动收集密码学与网络安全顶级会议论文的工具**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 支持的会议

### IACR 密码学三大会议
- **CRYPTO** - International Cryptology Conference
- **ASIACRYPT** - International Conference on the Theory and Application of Cryptology and Information Security
- **EUROCRYPT** - International Conference on the Theory and Applications of Cryptographic Techniques

### Big 4 安全会议
- **USENIX Security** - USENIX Security Symposium
- **IEEE S&P** - IEEE Symposium on Security and Privacy  
- **NDSS** - Network and Distributed System Security Symposium
- **CCS** - ACM Conference on Computer and Communications Security (待上线)

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 📊 **多源数据收集** | IACR使用官方JSON API，安全会议通过HTML解析 |
| 📝 **完整元数据** | 包含论文标题、作者、摘要、DOI、会议链接等 |
| 💾 **数据库存储** | SQLite数据库持久化存储，方便查询管理 |
| 🌐 **可视化查看** | 本地网页界面，支持搜索、筛选、浏览 |
| 🔧 **简洁高效** | 自动化数据收集，数据准确可靠 |

## 🚀 快速开始

### 1️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

所需依赖：
- `requests` - HTTP请求
- `beautifulsoup4` - HTML解析
- `lxml` - 解析器后端

### 2️⃣ 收集论文数据

```bash
# 收集所有支持会议的2025年论文
python update_iacr_data.py
```

首次运行会提示是否删除旧数据，输入 `yes` 确认。收集过程大约需要1-2分钟。

**收集结果**（2025年数据）：
- ✅ CRYPTO 2025: ~156 篇
- ✅ EUROCRYPT 2025: ~126 篇  
- ✅ USENIX Security 2025: ~460 篇
- ✅ NDSS 2025: ~215 篇
- ✅ IEEE S&P 2025: ~43 篇
- ⏳ CCS 2025: 待上线（accepted papers页面尚未发布）

**总计约 1000+ 篇论文**

### 3️⃣ 查询论文

使用 `query_db.py` 进行灵活查询：

```bash
# 查看统计信息
python query_db.py stats

# 搜索包含特定关键词的论文
python query_db.py search "backdoor" --limit 10

# 按会议和年份列出论文
python query_db.py list --conference NDSS --year 2025 --limit 20

# 查看某篇论文的详细信息
python query_db.py detail 2835

# 导出数据到CSV
python query_db.py export --conference CRYPTO --year 2025 --output crypto_2025.csv
```

### 4️⃣ 可视化查看

```bash
# 启动本地网页查看器
python start_viewer.py
```

浏览器会自动打开 http://localhost:8000，你可以：
- 🔍 搜索论文标题和作者
- 📊 按会议、年份筛选
- 📄 阅读论文摘要
- 🔗 点击链接访问原文

---

## 📖 详细使用

### 查询命令

`query_db.py` 提供以下子命令：

#### 1. stats - 查看统计信息
```bash
python query_db.py stats
```

#### 2. list - 列出论文
```bash
# 列出所有论文（默认10条）
python query_db.py list

# 按会议筛选
python query_db.py list --conference CRYPTO

# 按年份筛选
python query_db.py list --year 2025

# 组合筛选并限制数量
python query_db.py list --conference NDSS --year 2025 --limit 50
```

#### 3. search - 搜索论文
```bash
# 搜索标题包含关键词的论文
python query_db.py search "backdoor"

# 搜索作者
python query_db.py search "Zhang" --limit 20
```

#### 4. detail - 查看论文详情
```bash
# 查看指定ID的论文完整信息
python query_db.py detail 2835
```

#### 5. export - 导出数据
```bash
# 导出所有数据到CSV
python query_db.py export

# 按会议导出
python query_db.py export --conference CRYPTO --output crypto.csv

# 按年份导出
python query_db.py export --year 2025 --output papers_2025.csv
```

## 📁 数据访问

### 方式一：网页查看器 🌐（推荐）

```bash
python start_viewer.py
```

可视化界面，支持搜索、筛选、浏览。自动打开浏览器访问 http://localhost:8000

### 方式二：命令行查询 💻

```bash
# 查看统计
python query_db.py stats

# 搜索论文
python query_db.py search "backdoor" --limit 10

# 导出CSV
python query_db.py export --conference CRYPTO --output crypto.csv
```

### 方式三：直接访问数据库 💾

```python
import sqlite3

conn = sqlite3.connect('data/papers.db')
cursor = conn.cursor()

# 查询CRYPTO 2025所有论文
cursor.execute("""
    SELECT title, authors, abstract 
    FROM papers 
    WHERE conference='CRYPTO' AND year=2025
""")

for title, authors, abstract in cursor.fetchall():
    print(f"{title}\n{authors}\n")
```

## 🏗️ 项目结构

```
paper-collect/
├── crawlers/
│   ├── base_crawler.py          # 爬虫基类
│   ├── iacr_crawler.py          # IACR会议爬虫（JSON API）
│   └── security_crawler.py      # 安全会议爬虫（HTML解析）
├── utils/
│   ├── database.py              # 数据库管理
│   └── logger.py                # 日志工具
├── data/
│   └── papers.db                # SQLite数据库（~1000篇论文）
├── update_iacr_data.py          # 数据收集脚本
├── query_db.py                  # 查询工具
├── start_viewer.py              # 网页查看器
├── viewer.html                  # 可视化界面
├── requirements.txt             # 依赖列表
├── README.md                    # 本文档
└── LICENSE                      # MIT许可证
```

## 🔧 进阶使用

### 定制化数据收集

编辑 `update_iacr_data.py` 修改要收集的会议和年份：

```python
# IACR会议
iacr_conferences = {
    'CRYPTO': [2025, 2024],      # 可添加多个年份
    'ASIACRYPT': [2025],         # 取消注释以收集
    'EUROCRYPT': [2025, 2024]
}

# 四大安全会议
security_conferences = {
    'USENIX Security': [2025],
    'NDSS': [2025],
    'IEEE S&P': [2025],
    # 'CCS': [2025]  # CCS 2025尚未发布
}
```

### 扩展新会议

在 `crawlers/security_crawler.py` 中添加新会议：

1. 在 `CONFERENCE_URLS` 中添加URL模板
2. 实现对应的解析方法 `_parse_xxx()`
3. 在 `update_iacr_data.py` 中配置该会议

## ⚠️ 注意事项

- 🕐 数据收集约需1-2分钟完成
- 🌐 请遵守各会议网站的使用条款
- 💾 建议定期备份 `data/papers.db`
- 🔄 会议网页结构变化可能导致解析失败，及时更新爬虫

## 🐛 故障排查

| 问题 | 解决方案 |
|------|----------|
| 网络连接失败 | 检查网络连接，爬虫会自动重试3次 |
| 解析失败 | 某些会议页面可能未更新，查看日志确认 |
| 数据库错误 | 删除 `data/papers.db` 重新收集 |
| 查看日志 | 程序输出包含详细的日志信息 |

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个Star！**

Made with ❤️ for security & cryptography researchers

</div>
