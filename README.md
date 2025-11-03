# 📚 Paper Collector

**自动收集密码学与安全顶会论文的一站式工具**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 支持的会议

### 三大密码学会议
- **CRYPTO** - 美密会
- **ASIACRYPT** - 亚密会  
- **EUROCRYPT** - 欧密会

### Big 4 安全会议
- **USENIX Security**
- **IEEE S&P** - IEEE Symposium on Security and Privacy
- **CCS** - ACM Conference on Computer and Communications Security
- **NDSS** - Network and Distributed System Security Symposium

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 📊 **元数据收集** | 从DBLP自动获取论文标题、作者、年份、DOI |
| 📝 **摘要获取** | 通过Semantic Scholar API补充论文摘要 |
| 📥 **PDF下载** | 批量下载论文PDF，支持断点续传 |
| 💾 **多格式存储** | SQLite数据库 + JSON文件 |
| 🌐 **可视化查看** | 本地网页界面，搜索、筛选、浏览 |
| 🔧 **模块化设计** | 独立模块，易于调试和扩展 |

## 🚀 快速开始

### 1️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 2️⃣ 收集论文

```bash
# 测试：收集CRYPTO 2024的论文
python main.py collect --conferences crypto --years 2024
```

### 3️⃣ 可视化查看

```bash
# 导出JSON数据
python main.py export

# 启动本地查看器
python start_viewer.py
```

浏览器会自动打开，你可以：
- 🔍 搜索论文标题和作者
- 📊 查看统计信息
- 📄 阅读论文摘要
- 🔗 点击链接访问PDF

### ⚡ 一键完成

```bash
# 收集 + 获取摘要 + 下载PDF + 导出
python main.py all --with-abstract
```

---

## 📖 完整文档

查看 **[MANUAL.md](MANUAL.md)** 获取详细使用说明和高级功能。

## 🎯 主要命令

```bash
# 收集论文元数据
python main.py collect [--conferences CONF] [--years YEAR]

# 获取论文摘要
python main.py enrich [--limit N]
python enrich_smart.py 50  # 推荐：智能过滤

# 下载PDF
python main.py download [--conference CONF] [--limit N]

# 导出JSON
python main.py export

# 启动查看器
python start_viewer.py

# 查看统计
python main.py stats

# 一键完成
python main.py all [--with-abstract]
```

## 📁 数据访问

### 方式一：网页查看器 🌐（推荐）

```bash
python start_viewer.py
```

可视化界面，支持搜索、筛选、导出。

### 方式二：JSON文件 📄

```python
import json
with open('data/json/papers_readable.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    papers = data['conferences']['CRYPTO']
```

### 方式三：数据库查询 💾

```bash
python query_db.py list --conference "CRYPTO"
python query_db.py search "quantum"
python query_db.py export output.csv
```

## 🏗️ 项目结构

```
paper-collect/
├── config/              # 配置文件
├── crawlers/            # 爬虫模块（DBLP, Semantic Scholar）
├── utils/               # 工具模块（数据库、下载器、JSON导出）
├── data/
│   ├── papers.db        # SQLite数据库
│   ├── json/            # JSON导出
│   └── pdfs/            # PDF文件
├── main.py              # 主程序
├── start_viewer.py      # 本地服务器
├── viewer.html          # 可视化界面
└── MANUAL.md            # 完整使用手册
```

## � 配置

编辑 `config/conferences.yaml` 添加会议：

```yaml
conferences:
  your_conf:
    - name: "YourConf"
      dblp_key: "conf/yourconf"
      years: [2024]
```

编辑 `config/settings.yaml` 调整参数：

```yaml
settings:
  crawler:
    timeout: 30
    retry_times: 3
```

## ⚠️ 注意事项

- ⏱️ Semantic Scholar API有速率限制（每次请求间隔2秒）
- 🔒 部分PDF需要机构访问权限
- 🌐 请遵守网站使用条款
- 💾 建议定期备份 `data/papers.db`

## 🐛 故障排查

| 问题 | 解决方案 |
|------|----------|
| 下载失败 | `python main.py retry` |
| CORS错误 | 使用 `python start_viewer.py` |
| 摘要获取慢 | 使用 `enrich_smart.py` 并限制数量 |
| 查看日志 | `logs/crawler.log` |

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个Star！**

Made with ❤️ for researchers

</div>