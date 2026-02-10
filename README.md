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

## CSV 字段说明

### all_stats.csv
| 字段(符号) | 中文 | 指标描述 |
| --- | --- | --- |
| season | 赛季 | 赛季标识，例如 2019-2020 |
| Squad | 球队 | 球队名称 |
| W | 胜 | 胜场数 |
| D | 平 | 平局数 |
| L | 负 | 负场数 |
| GF | 进球 | 进球总数 |
| GA_x | 失球 | 失球总数（积分榜口径） |
| GD | 净胜球 | 进球减失球 |
| Pts | 积分 | 联赛积分 |
| Pts/MP | 场均积分 | 每场平均积分 |
| Attendance | 上座人数 | 场均上座人数 |
| Std_#Pl | 使用球员数 | 标准统计中登场球员数 |
| Age | 平均年龄 | 球队平均年龄 |
| Poss | 控球率 | 平均控球率（%） |
| Gls | 进球 | 标准统计口径进球数 |
| Ast | 助攻 | 助攻数 |
| G+A | 进球+助攻 | 进球与助攻合计 |
| G-PK | 非点球进球 | 不含点球的进球数 |
| PK | 点球进球 | 点球进球数 |
| PKatt | 点球尝试 | 点球主罚次数 |
| CrdY | 黄牌 | 黄牌数 |
| CrdR | 红牌 | 红牌数 |
| GK_#Pl | 使用门将数 | 守门员统计中的登场门将数 |
| GA_y | 失球 | 守门员统计口径失球数 |
| SoTA | 被射正 | 对手射正次数 |
| Saves | 扑救 | 扑救次数 |
| Save% | 扑救率 | 扑救成功率（%） |
| CS | 零封 | 零封场次 |
| CS% | 零封率 | 零封比例（%） |
| Sh | 射门 | 射门总次数 |
| SoT | 射正 | 射正次数 |
| SoT% | 射正率 | 射正占比（%） |
| G/Sh | 进球/射门 | 每次射门的进球率 |
| G/SoT | 进球/射正 | 每次射正的进球率 |
| Fls | 犯规 | 犯规次数 |
| Fld | 被犯规 | 被犯规次数 |
| Off | 越位 | 越位次数 |
| Crs | 传中 | 传中次数 |
| Int | 拦截 | 拦截次数 |
| TklW | 抢断成功 | 成功抢断次数 |
| PKwon | 造点球 | 赢得点球次数 |
| PKcon | 送点球 | 送出点球次数 |
| OG | 乌龙球 | 乌龙球次数 |

### all_top_stats.csv
| 字段(符号) | 中文 | 指标描述 |
| --- | --- | --- |
| season | 赛季 | 赛季标识，例如 2019-2020 |
| metric | 榜单指标 | 榜单名称，如“最佳射手” |
| rank | 排名 | 榜单排名 |
| player | 球员 | 球员姓名 |
| squad | 球队 | 所属球队 |
| value | 数值 | 榜单对应的统计值 |

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
