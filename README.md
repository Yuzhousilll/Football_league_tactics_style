# graduation_thesis
毕业论文相关数据与代码。主要包含英超赛季统计数据的抓取、整理与汇总。

## 目录结构
- [expository](expository): 数据抓取与清洗脚本、汇总产物
- [expository/data](expository/data): 按赛季保存的原始表格 CSV
- [expository/all_stats.csv](expository/all_stats.csv): 汇总的赛季球队统计表
- [expository/all_top_stats.csv](expository/all_top_stats.csv): 汇总的榜单统计表
- [view-source_https___fbref.com_en_comps_9_2015-2016_2015-2016-Premier-League-Stats.html](view-source_https___fbref.com_en_comps_9_2015-2016_2015-2016-Premier-League-Stats.html) 等: 浏览器保存的 FBref 源码页面

## 数据来源
数据来自 FBref 的 Premier League 赛季统计页面（https://fbref.com/en/comps/9/）。
仓库内保留了部分赛季的网页源码快照，便于离线解析与复现。

## 脚本说明
- [expository/scrape_fbref_pl.py](expository/scrape_fbref_pl.py): 抓取 FBref 表格并保存为 CSV；支持读取本地 HTML。
- [expository/process_fbref_pl_data.py](expository/process_fbref_pl_data.py): 生成榜单与球队汇总表（top_leaders.csv、general_stats.csv）。

## 使用示例
抓取指定赛季：

```bash
python expository/scrape_fbref_pl.py --season 2019-2020
```

使用本地 HTML 解析：

```bash
python expository/scrape_fbref_pl.py --html "view-source_https___fbref.com_en_comps_9_2019-2020_2019-2020-Premier-League-Stats.html"
```

生成清洗后的汇总表：

```bash
python expository/process_fbref_pl_data.py --input-dir expository/data/fbref_pl_2019_2020
```
