# 毕业论文：英超联赛战术演变与竞争力分析 (2016-2025)

本项目为毕业论文《英超联赛战术演变与竞争力分析》的数据抓取、预处理、实证模型（因子分析/主成分分析）以及各章节分析报告的全部代码与成果仓库。通过对涵盖近十年英超赛季的精细化赛事数据进行挖掘，量化探讨了现代足球体系下的球队战术风格演变规律及关键球员角色变化带来的微观战术创新。

## 📁 核心目录结构

本仓库涵盖了从初始数据获取到最终章节初稿报告的全流程文件：

### 1. 文档与报告 (Documents)
- **`研究方案与写作提纲.md`**: 论文的研究基础、流程方案与章节目录提纲。
- **`metrics_list.md`**: 筛选确立的战术风格评价指标与底层变量体系。

### 2. 分析主章节 (Chapters)
- **`chapter3_competitiveness/`**: 第三章（联赛战术风格识别及演变、成绩竞争力评估）的输出目录。包含：
  - `CHAPTER3_COMPETITIVENESS_REPORT.md` (分析总结与实证草稿)
  - 球队竞争力衍生数据集（`competitiveness_dataset.csv`）及因子的 PCA 模型提取结果（`competitiveness_pca_loadings.csv` 等）。
- **`chapter4_player_role/`** 与 **`haaland_analysis/`**: 第四章（球员角色分析）的输出目录。包含：
  - 哈兰德微观战术案例分析实证数据与报告 (`HAALAND_ANALYSIS_REPORT.md`)。
  - 内收型边后卫特征演化与曼城攻防效率横纵对比宽表。

### 3. 代码脚本体系 (Scripts)
核心代码全部汇总存放于 `scripts/`（及少数早期代码在根目录），主要协同三大模块运转：
- **数据获取与特征清洗**：
  - `scrape_fbref_pl.py`: 核心网页抓取爬虫程序（支持在线及离线解析 HTML 源文件）。
  - `process_fbref_pl_data.py` & `compute_style_metrics.py`: 基于原始网页表结构，提取并计算诸如高位压迫、传控指数等深层的战术风格复合指标。
- **降维建模与统计分析**：
  - `evaluate_factor_model.py`, `evaluate_fa_model.py`, `evaluate_6vars_model.py` 等：进行因子分析与主成分分析，将多重共线性的原始数据提炼为少数核心战术因子及综合成绩竞争力指数。
- **数据可视化体系建立**：
  - `analyze_style_evolution_*.py`: 基于聚类技术构建并绘制不同风格类型的时序演变轨迹图。
  - `draw_haaland_tactical_diagram.py`, `draw_inverted_fullback_tactical_diagram.py`: 结合微观战术理论，绘制符合高学术规范标准的跑位及阵型分析图（统清爽配色，避免图内英文/注释堆叠）。

### 4. 数据中心 (Data)
- **`html源文件/`**: 浏览器保存的近10年历代 FBref 英超联赛源码页面快照，保障底层脱网环境可读且复现。
- **`data/`**: 原始数据 CSV 及清洗衍生的细分次级数据集。
- **`all_stats.csv`** 与 **`style_metrics_all.csv`**: 全览宽表文件，汇聚历年全部参赛球队的核心统计指标及二次计算产出的战术风格映射数据。

## 💡 已完成的核心工作

1. **底层数据流转贯通**：从2015赛季至2025赛季的近十年长跨度多维数据全部顺利归档，完成了脱敏、缺失填补，并清洗了基础宽表中的高噪音特征。
2. **战术抽象降维及演变实证**：运用多维统计降维技术消除共线性，提炼出能代表控球与压迫的核心“战术风格因子”，将繁杂表现切片收敛为各阶段风格聚类结构版图。
3. **宏观竞争力分析体系构建**：从成绩维度出发，采用净胜球、期望进球（xG）和场均积分构建了基于主成分的竞争力综合评价模型，结合豪门案例追踪战术变迁期表现起伏。
4. **微观球员角色转型推演**：重点落脚于特定中锋（如哈兰德）的进攻数据贡献和边后卫的内收打法，并用定量的方式佐证了微观战术变化对体系效率的主导作用。
5. **配套图表规范定版**：完成实证分析所必需的趋势分布图、类图和战术图设计，严格遵照毕业论文制图排版格式统一了画风要求。

## 🚀 快速测试使用说明

*(运行前请确保环境中包结构完整，如 Pandas, Numpy, Scikit-Learn, Factor-Analyzer, Matplotlib, Seaborn 等)*

**1. 离线抓取与解析历史数据（以 2019-2020 赛季为例）：**
```bash
python scrape_fbref_pl.py --html "html源文件/view-source_https___fbref.com_en_comps_9_2019-2020_2019-2020-Premier-League-Stats.html"
```

**2. 派生生成各队伍深层战术特征表：**
```bash
python scripts/compute_style_metrics.py
```

**3. 执行降维并评估聚类打法迁移：**
```bash
python scripts/evaluate_factor_model.py
```

**4. 渲染战术分析图及演变散点图：**
```bash
python scripts/draw_haaland_tactical_diagram.py
python scripts/analyze_style_evolution_12vars.py
```
