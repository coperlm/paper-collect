# JSON数据格式说明

## 📂 生成的JSON文件

运行 `python main.py export` 后，会在 `data/json/` 目录生成以下文件：

### 1. summary.json - 统计摘要

```json
{
  "total": 809,                    // 总论文数
  "with_abstract": 2,              // 有摘要的论文数
  "by_conference": {               // 按会议统计
    "CRYPTO": 809
  },
  "by_conference_and_year": {      // 按会议和年份统计
    "CRYPTO": {
      "2025": 26,
      "2024": 783
    }
  },
  "by_download_status": {          // 按下载状态统计
    "completed": 5,
    "pending": 804
  }
}
```

### 2. all_papers.json - 所有论文（完整数据）

包含数据库中所有字段的完整论文列表：

```json
[
  {
    "id": 1,
    "title": "论文标题",
    "authors": "作者1; 作者2",
    "abstract": "论文摘要...",
    "year": 2024,
    "conference": "CRYPTO",
    "url": "https://dblp.org/...",
    "pdf_url": "https://...",
    "pdf_path": "data/pdfs/...",
    "doi": "10.1007/...",
    "dblp_key": "conf/crypto/...",
    "created_at": "2025-11-03 07:00:46",
    "updated_at": "2025-11-03 07:09:44",
    "download_status": "completed",
    "notes": "Citations: 10; Date: 2024-08-15"
  }
]
```

### 3. papers_readable.json - 易读格式

简化字段，按会议分组，便于浏览：

```json
{
  "total": 809,
  "conferences": {
    "CRYPTO": [
      {
        "id": 1,
        "title": "论文标题",
        "authors": ["作者1", "作者2"],    // 数组格式
        "abstract": "摘要...",
        "year": 2024,
        "conference": "CRYPTO",
        "doi": "10.1007/...",
        "pdf_url": "https://...",
        "pdf_path": "data/pdfs/...",
        "downloaded": true              // 布尔值
      }
    ]
  }
}
```

### 4. {会议名称}.json - 按会议分组

每个会议单独的JSON文件，例如 `CRYPTO.json`：

```json
[
  {
    "id": 1,
    "title": "...",
    ...
  }
]
```

## 🔍 如何使用JSON文件

### 方法一：使用网页查看器（推荐）

1. 确保已导出JSON：`python main.py export`
2. 双击打开 `viewer.html` 文件
3. 在浏览器中查看、搜索、筛选论文

**功能：**
- ✅ 搜索标题和作者
- ✅ 按会议、年份、状态筛选
- ✅ 查看摘要
- ✅ 快速访问DOI和PDF链接
- ✅ 导出筛选结果为CSV

### 方法二：使用Python读取

```python
import json

# 读取易读格式
with open('data/json/papers_readable.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 获取所有CRYPTO论文
crypto_papers = data['conferences']['CRYPTO']

# 查找特定论文
for paper in crypto_papers:
    if 'quantum' in paper['title'].lower():
        print(paper['title'])
        print(paper['abstract'])
```

### 方法三：使用JavaScript

```javascript
// 在网页中加载
fetch('data/json/papers_readable.json')
    .then(response => response.json())
    .then(data => {
        console.log(`总共 ${data.total} 篇论文`);
        
        // 遍历CRYPTO会议论文
        data.conferences.CRYPTO.forEach(paper => {
            console.log(paper.title);
        });
    });
```

### 方法四：使用命令行工具

```bash
# 使用jq查询（需要安装jq）
cat data/json/papers_readable.json | jq '.conferences.CRYPTO[] | select(.year == 2024)'

# 统计有摘要的论文
cat data/json/papers_readable.json | jq '[.conferences.CRYPTO[] | select(.abstract != null)] | length'
```

## 📊 常见查询示例

### Python示例

```python
import json

with open('data/json/papers_readable.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

papers = []
for conf_papers in data['conferences'].values():
    papers.extend(conf_papers)

# 1. 找出所有2024年的论文
papers_2024 = [p for p in papers if p['year'] == 2024]
print(f"2024年共 {len(papers_2024)} 篇论文")

# 2. 找出有摘要的论文
with_abstract = [p for p in papers if p['abstract']]
print(f"有摘要的论文: {len(with_abstract)}")

# 3. 按作者搜索
author_name = "Zhang"
author_papers = [p for p in papers 
                 if any(author_name in a for a in p['authors'])]
print(f"作者 {author_name} 的论文: {len(author_papers)}")

# 4. 关键词搜索
keyword = "cryptography"
keyword_papers = [p for p in papers 
                  if keyword.lower() in p['title'].lower()]
print(f"包含 '{keyword}' 的论文: {len(keyword_papers)}")

# 5. 导出为Markdown
with open('papers.md', 'w', encoding='utf-8') as f:
    for paper in papers[:10]:
        f.write(f"## {paper['title']}\n\n")
        f.write(f"**作者:** {', '.join(paper['authors'])}\n\n")
        f.write(f"**会议:** {paper['conference']} {paper['year']}\n\n")
        if paper['abstract']:
            f.write(f"**摘要:** {paper['abstract']}\n\n")
        f.write(f"---\n\n")
```

## 🔄 自动导出

在完整流程中自动导出：

```bash
python main.py all --with-abstract
```

这会自动：
1. 收集论文元数据
2. 获取摘要
3. 下载PDF
4. **导出JSON文件**

## 💡 最佳实践

1. **定期导出**：每次更新数据后运行 `python main.py export`
2. **版本控制**：可以git忽略JSON文件，或保留用于备份
3. **数据分析**：JSON格式便于用Python/R进行数据分析
4. **分享数据**：JSON文件可以轻松分享给他人
5. **网页展示**：使用viewer.html快速浏览和搜索

## 🛠️ 自定义导出

如果需要自定义JSON格式，可以修改 `utils/json_exporter.py`：

```python
from utils.json_exporter import JSONExporter

exporter = JSONExporter()

# 导出特定会议
exporter.export_by_conference()

# 导出按年份分组
exporter.export_by_conference_and_year()

# 自定义导出
# 修改 json_exporter.py 添加新方法
```

## 📦 JSON文件大小

- `all_papers.json`: 通常 1-10 MB（取决于论文数量）
- `papers_readable.json`: 略小于all_papers.json
- 各会议JSON: 几百KB到几MB
- `summary.json`: 几KB

**注意：** 如果论文数量很大（>10000篇），建议使用数据库查询而不是加载整个JSON文件。
