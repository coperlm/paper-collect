# 🚀 快速开始指南

## 5分钟快速上手

### 步骤1：安装依赖

```bash
pip install -r requirements.txt
```

### 步骤2：收集论文（测试）

先测试收集CRYPTO 2024的论文：

```bash
python main.py collect --conferences crypto --years 2024
```

看到类似输出：
```
✅ 收集 CRYPTO 2024: 插入 783 篇论文
```

### 步骤3：获取摘要（可选）

为论文添加摘要信息（使用智能脚本，只处理真正的论文）：

```bash
python enrich_smart.py 10
```

这会为前10篇论文获取摘要。

### 步骤4：导出为JSON

```bash
python main.py export
```

生成的文件在 `data/json/` 目录。

### 步骤5：可视化查看 🎉

双击打开 `viewer.html` 文件！

你现在可以：
- 🔍 搜索论文
- 📊 查看统计
- 📝 阅读摘要
- 🔗 访问PDF链接

---

## 完整工作流程

### 场景1：收集所有会议近5年论文

```bash
# 方法1：使用快速启动脚本（Windows）
.\start.ps1
# 然后选择选项1

# 方法2：命令行
python main.py collect --years 2020 2021 2022 2023 2024
python enrich_smart.py 100      # 获取100篇论文的摘要
python main.py download --limit 50  # 下载50篇PDF
python main.py export           # 导出JSON
# 打开 viewer.html 查看
```

### 场景2：只收集特定会议

```bash
# 三大密码学会议
python main.py collect --conferences crypto asiacrypt eurocrypt --years 2024

# Big4安全会议
python main.py collect --conferences usenix_security sp ccs ndss --years 2024

# 导出查看
python main.py export
```

### 场景3：完整流程（一键完成）

```bash
python main.py all --with-abstract
```

这会自动：
1. ✅ 收集元数据
2. ✅ 获取摘要
3. ✅ 下载PDF
4. ✅ 导出JSON

---

## 数据查看方式对比

| 方式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **viewer.html** | ✅ 可视化<br>✅ 搜索快<br>✅ 无需编程 | ❌ 需要浏览器 | 日常查看、搜索 |
| **JSON文件** | ✅ 明文可读<br>✅ 易于分享<br>✅ 编程方便 | ❌ 大文件加载慢 | 数据分析、分享 |
| **数据库** | ✅ 查询高效<br>✅ 支持复杂查询 | ❌ 需要SQL知识 | 高级查询、大数据 |

**推荐：** 
- 📱 日常使用 → viewer.html
- 💻 编程分析 → JSON文件
- 🔬 复杂查询 → 数据库

---

## 常见问题

### Q1: 论文数量很多，JSON文件太大怎么办？

**A:** 使用按会议导出：
```bash
python utils/json_exporter.py --mode conference
```

每个会议生成单独的JSON文件。

### Q2: 如何只看有摘要的论文？

**A:** 在viewer.html中：
1. 状态下拉框选择 "有摘要"
2. 点击筛选按钮

或者用Python：
```python
import json
with open('data/json/papers_readable.json') as f:
    data = json.load(f)
papers = [p for conf in data['conferences'].values() 
          for p in conf if p['abstract']]
```

### Q3: 摘要获取很慢？

**A:** 
1. 使用 `enrich_smart.py` 而不是 `main.py enrich`
2. 限制数量：`python enrich_smart.py 50`
3. Semantic Scholar有API限速，每次请求间隔2秒

### Q4: 如何备份数据？

**A:** 备份这些文件：
```bash
data/papers.db        # 数据库
data/json/            # JSON文件（可选）
data/pdfs/            # PDF文件
```

---

## 进阶使用

### 自定义会议

编辑 `config/conferences.yaml`：

```yaml
conferences:
  my_conference:
    - name: "MyConf"
      dblp_key: "conf/myconf"
      years: [2024]
```

### 定时自动更新

Windows任务计划或Linux cron：

```bash
# Linux crontab
0 2 * * 1 cd /path/to/paper-collect && python main.py all
```

### 批量导出PDF列表

```python
import json
with open('data/json/papers_readable.json') as f:
    data = json.load(f)

with open('pdf_urls.txt', 'w') as f:
    for conf_papers in data['conferences'].values():
        for p in conf_papers:
            if p['pdf_url']:
                f.write(f"{p['pdf_url']}\n")
```

---

## 下一步

- 📖 查看 [USAGE.md](USAGE.md) 了解所有命令
- 📄 查看 [JSON_GUIDE.md](JSON_GUIDE.md) 了解JSON格式
- 🔧 根据需要修改 `config/` 中的配置

**享受使用！** 🎉
