# 英超多赛季数据采集与战术分析

基于毕业论文最终版的方法框架，将足球联赛数据采集、质量检查、战术因子分析、动作主成分分析和球队/球员案例组成可重复运行的 Codex skill。默认英超案例，联赛、完整赛季范围、球队和球员由同一个配置文件指定。

## 快速运行

Python 3.10及以上。在独立环境中安装依赖：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/football_report.py \
  --config configs/premier-league.json \
  --output reports/premier-league-2016-2025
```

无需联网即可使用仓库归档的英超2016–2017至2024–2025数据。默认9赛季、180个球队赛季观测，以曼联和曼城为球队案例，哈兰德为球员案例。模型在整个联赛样本中拟合，案例条件不缩小参照群体。每次使用新的输出目录，不覆盖已有报告。

| 产物 | 内容 |
| --- | --- |
| `report.html` | 六章报告，图表内嵌，可独立打开和打印 |
| `report.md` 与 `figures/` | 可编辑报告，SVG和PNG图表 |
| `teams.csv`、`players.csv`、`player_cases.csv` | 实际使用的数据及案例 |
| `factor_loadings.csv`、`factor_scores.csv` | 因子载荷、共同度与得分 |
| `cluster_centers.csv`、`cluster_shares.csv` | 聚类中心和赛季占比 |
| `action_loadings.csv`、`action_scores.csv` | 动作PCA及综合指数 |
| `analysis.json` | 检验、缺失处理、模型可用状态及原因 |
| `config.resolved.json`、`manifest.json` | 参数、来源、版本和校验摘要 |

模型不可用时不生成相应模型文件，报告保留章节并说明原因。自动流程默认HTML与Markdown；用户要求Word/PDF时，skill从本次报告另行制作并检查排版。

## 更换研究对象

复制 `configs/premier-league.json`，修改 `league`、`season_start`、`season_end`、`teams`、`players`。输入相对路径以配置文件所在目录为准，脚本可以从任意目录调用。

支持英超、西甲、德甲、意甲、法甲。**归档仅属于英超**，其他联赛或未覆盖赛季需要真实数据。`configs/custom-league.json` 展示西甲配置，需先提供其中指定CSV；不附带西甲实测数据。

来源可选归档CSV、规范CSV、保存的FBref HTML、在线球队页。站点可能拒绝访问或变更字段；403/429会停止，改用有权提供的HTML/CSV。球员需单独的球员标准表或规范CSV；现有归档只覆盖排行榜条目，未上榜不等于零。详细字段见 [数据约定](references/data-contract.md)。时间范围为完整赛季，不从整季数据推算任意日期区间。

## 作为 Codex skill 使用

入口为 [SKILL.md](SKILL.md)，显示名“英超多赛季数据采集与战术分析”，调用名 `$football-tactical-report`。例如：“使用 $football-tactical-report，分析英超2022–2023至2024–2025的阿森纳、曼城，球员选择萨卡、哈兰德。”

```bash
.venv/bin/python tools/package_skill.py --output dist
```

将打包目录中的 `football-tactical-report` 安装到Codex的skills目录后即可复用。包内只含运行脚本、参数、参考说明和三份归档CSV，不含论文原件、个人文件、虚拟环境或生成报告。

## 与最终版论文的关系

报告按六章：引言、研究方法、联赛战术风格识别及演变、球队成绩竞争力评估、球员角色分析、结论与展望。已核对最终版Word的章节、12项风格指标、8项动作指标；PDF状态见 [版本记录](references/thesis-profile.json)。

新范围必须重新计算。移植时明确修正原“传中占比”的分母命名、FA/PCA解释方差混用及因子方向差异，详见 [论文对齐说明](references/thesis-alignment.md)。程序不会修改原论文。

```bash
.venv/bin/python scripts/import_thesis.py \
  --docx /path/to/final.docx --pdf /path/to/final.pdf \
  --output .work/thesis-review
```

全文提取仅用于本地核对，不自动认定版本一致，不上传全文。核对后更新profile中的方法与版本摘要。

## 验证

```bash
.venv/bin/python -m unittest discover -s tests -v
```

复用入口是 `scripts/football_report.py` 和 `scripts/tactical/`；`configs/` 是参数，`references/` 是方法。原研究脚本及章节成果保留为论文历史材料，不作为新配置流程入口。验证使用真实英超归档与明确标记的合成测试夹具，不将其他联赛测试数据作为实测结论。报告边界见 [报告规范](references/report-standard.md)。
