# graduation_thesis
毕业论文相关数据与代码。主要包含英超赛季统计数据的抓取、整理与汇总。

## 目录结构
- [scrape_fbref_pl.py](scrape_fbref_pl.py): 抓取 FBref 表格并保存为 CSV；支持读取本地 HTML
- [process_fbref_pl_data.py](process_fbref_pl_data.py): 生成榜单与球队汇总表
- [data](data): 按赛季保存的原始表格 CSV
- [all_stats.csv](all_stats.csv): 汇总的赛季球队统计表
- [all_top_stats.csv](all_top_stats.csv): 汇总的榜单统计表
- [html源文件](html源文件): 浏览器保存的 FBref 源码页面

## 数据来源
数据来自 FBref 的 Premier League 赛季统计页面（https://fbref.com/en/comps/9/）。
仓库内保留了部分赛季的网页源码快照，便于离线解析与复现。

## 使用示例
抓取指定赛季：

```bash
python scrape_fbref_pl.py --season 2019-2020
```

使用本地 HTML 解析：

```bash
python scrape_fbref_pl.py --html "html源文件/view-source_https___fbref.com_en_comps_9_2019-2020_2019-2020-Premier-League-Stats.html"
```

生成清洗后的汇总表：

```bash
python process_fbref_pl_data.py --input-dir data/fbref_pl_2019_2020
```
