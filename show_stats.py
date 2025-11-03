import json

with open('data/json/summary.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('📊 数据统计摘要')
print('=' * 50)
print(f'总论文数: {data["total"]}')
print(f'有摘要: {data["with_abstract"]}')
print(f'已下载: {data["by_download_status"].get("completed", 0)}')
print(f'\n按会议统计:')
for conf, count in data['by_conference'].items():
    print(f'  {conf}: {count} 篇')
print('=' * 50)
print('\n✅ JSON文件已生成在 data/json/ 目录')
print('💡 打开 viewer.html 查看可视化界面')
