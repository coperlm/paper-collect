# 📚 Security & Cryptography Paper Collector

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

自动收集密码学与网络安全顶级会议论文的工具，支持数据导出、PDF批量下载和管理。

## 🎯 支持的会议

### IACR 密码学会议
- **CRYPTO** - International Cryptology Conference
- **EUROCRYPT** - International Conference on the Theory and Applications of Cryptographic Techniques
- **ASIACRYPT** - International Conference on Cryptology and Information Security

### 四大安全会议
- **USENIX Security** - USENIX Security Symposium
- **IEEE S&P** - IEEE Symposium on Security and Privacy
- **NDSS** - Network and Distributed System Security Symposium
- **CCS** - ACM Conference on Computer and Communications Security

## ✨ 核心功能

- 🔄 **自动采集** - 从官方网站自动收集论文元数据
- 💾 **数据存储** - SQLite数据库持久化存储
- 📥 **批量下载** - 并发下载论文PDF，支持断点续传
- 📊 **多格式导出** - 支持JSON、CSV、TXT等格式
- 🌐 **可视化界面** - 网页界面浏览和搜索论文
- 📈 **状态追踪** - 自动追踪下载状态和统计

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 1. 收集论文数据

```bash
python update_iacr_data.py
```

**当前收集量**（2025年数据）：
- CRYPTO: 156篇
- EUROCRYPT: 126篇
- USENIX Security: 460篇
- NDSS: 215篇
- IEEE S&P: 43篇
- **总计：1000+篇**

### 2. 查询论文

```bash
# 查看统计
python query_db.py stats

# 搜索论文
python query_db.py search "zero-knowledge" --limit 10

# 按会议列出
python query_db.py list --conference CRYPTO --year 2025

# 查看详情
python query_db.py detail 123

# 导出CSV
python query_db.py export --conference NDSS --output ndss.csv
```

### 3. 导出数据

```bash
# 导出所有论文为JSON
python paper_tools.py export-json --mode all

# 按会议分别导出
python paper_tools.py export-json --mode by-conference

# 导出PDF下载链接列表
python paper_tools.py export-links
```

生成的文件：
- `data/papers_all.json` - 所有论文（1.3 MB）
- `data/json/CRYPTO_2025.json` - 按会议分类
- `data/download_links.txt` - PDF下载链接（970个）

### 4. 批量下载PDF

```bash
# 下载所有PDF（推荐先小批量测试）
python paper_tools.py download --limit 10

# 下载指定会议
python paper_tools.py download --conference CRYPTO

# 下载指定年份
python paper_tools.py download --year 2025

# 自定义并发数和延迟
python paper_tools.py download --workers 10 --delay 0.3
```

### 5. 管理下载状态

```bash
# 更新下载状态（扫描已下载的PDF）
python paper_tools.py status-update

# 查看下载统计
python paper_tools.py status-show
```

### 6. 网页界面浏览

```bash
python start_viewer.py
```

浏览器自动打开 http://localhost:8000，支持搜索、筛选和浏览论文。

## ⚠️ 注意事项

- 🕐 首次数据收集约需1-2分钟
- 🌐 请遵守各会议网站的使用条款，建议设置合理的请求延迟
- 💾 建议定期备份 `data/papers.db` 数据库
- 🔄 会议网页结构变化可能导致解析失败，及时更新爬虫
- 📥 PDF下载成功率约97%（30篇论文缺少下载链接）

## 🐛 故障排查

| 问题 | 解决方案 |
|------|----------|
| 网络连接失败 | 检查网络，爬虫会自动重试3次 |
| 解析失败 | 某些会议页面可能未更新，查看日志 |
| 数据库错误 | 删除 `data/papers.db` 重新收集 |
| 下载速度慢 | 调整 `--workers` 参数或使用aria2c |
| PDF下载失败 | 使用 `status-update` 查看失败原因 |

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发计划

- [ ] 支持更多会议（CCS 2025等）
- [ ] 添加论文引用分析
- [ ] 支持全文搜索
- [ ] 添加论文推荐功能
- [ ] Docker容器化部署

## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个Star！**

Made with ❤️ for security & cryptography researchers

</div>
