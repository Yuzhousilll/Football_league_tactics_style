# 第2章 英超球队风格识别与演变分析（12变量正式版）

## 2.1 研究设计与变量体系

本章目标在于构建一个可解释、可量化且可用于跨赛季比较的球队风格识别框架。基于`style_metrics_all.csv`中2016-2017至2024-2025赛季（共9个赛季）英超球队样本，形成180个“球队-赛季”观测。为平衡信息完整性与变量冗余，本文在前期全维度筛选基础上，最终保留12个风格变量进入正式模型：

1. `shots_on_target_per_match`
2. `goals_per_match`
3. `goals_per_sot`
4. `cross_share_of_touches`
5. `penalties_won_per_match`
6. `offsides_to_shots_ratio`
7. `goals_against_per_match`
8. `clean_sheet_pct`
9. `tackles_won_per_match`
10. `interceptions_per_match`
11. `shots_on_target_against_per_match`
12. `players_used`

上述指标覆盖进攻产出、进攻效率、进攻路径、防守承压、防守结果与阵容使用等关键维度。方法上，先对变量进行标准化，再通过因子分析提取潜在风格维度，随后以因子得分作为输入执行K-means聚类，以识别球队风格类型。最后通过赛季序列分析考察风格结构的动态演化。

## 2.2 因子分析结果

### 2.2.1 因子提取与解释度

基于12变量的标准化数据，按特征值大于1（Kaiser准则）自动提取3个公共因子。结果显示，三因子累计解释度约为70.94%，说明该结构能够在较少维度下保留多数原始信息。相较于直接使用高维指标进行聚类，因子压缩能够减弱多重共线性影响，并提升后续分类解释的一致性。

对应结果文件如下：
- 因子载荷：`data/derived/team_factor_loadings_12vars_2016_2025.csv`
- 因子得分：`data/derived/team_factor_scores_12vars_2016_2025.csv`
- 碎石图：`data/derived/scree_plot_12vars.png`
- 载荷热力图：`data/derived/factor_loadings_heatmap_12vars.png`

### 2.2.2 因子载荷结构与风格含义

根据载荷矩阵，三个因子的含义可概括如下。

1. Factor1：综合竞争质量因子
该因子在`goals_per_match`（0.996）、`shots_on_target_per_match`（0.917）和`goals_per_sot`（0.725）上呈高正载荷，同时在`goals_against_per_match`（-0.669）与`shots_on_target_against_per_match`（-0.674）上呈显著负载荷。其统计含义是：当球队在进攻端更具持续产出能力且防守端失球风险更低时，Factor1得分更高。因此，Factor1可视作表征“攻防综合质量”的主轴。

2. Factor2：机会转化与执行倾向因子
Factor2对`goals_per_sot`与部分进攻执行变量呈较高负载或中等载荷，反映同等进攻活动下的终结效率差异与执行路径差异。该因子更偏向“质量”而非“数量”，用于区分在机会管理、射门转化与组织偏好上存在系统差异的球队。

3. Factor3：防守风险与阵容波动因子
Factor3在`goals_against_per_match`（0.674）、`shots_on_target_against_per_match`（0.517）和`players_used`（0.553）上为正，在`clean_sheet_pct`（-0.598）上为负，说明其能够刻画“防守失稳与阵容变动”共同出现的风险结构。当球队防守端承压偏高、零封率偏低且阵容轮换幅度较大时，Factor3通常上升。

综合而言，Factor1提供“强弱主轴”，Factor2与Factor3提供“执行差异”和“风险差异”两个侧向补充维度。三者共同形成球队风格的多维表示，便于后续聚类识别与时序比较。

### 2.2.3 结果解释的边界

需要强调，因子命名属于“统计载荷基础上的实证解释”，而非先验定义。即，因子含义来自变量在样本中的共同变化模式，因此其解释应理解为“倾向性结构”而非单一因果机制。此外，个别变量共同度较低（如`tackles_won_per_match`、`interceptions_per_match`）提示其在当前因子结构中的解释贡献相对有限，这为后续稳健性检验（如旋转方案比较、样本分段检验）提供了进一步空间。

## 2.3 基于因子得分的球队风格聚类

### 2.3.1 聚类设定与总体分布

在3个因子得分基础上，采用K-means进行4类聚类。最终180个样本的分类规模为40、40、54、46，未出现极端不平衡情况，说明4类划分在样本层面具有可用性。

对应文件如下：
- 聚类结果：`data/derived/team_clusters_assigned_12vars.csv`
- 聚类中心：`data/derived/team_cluster_statistics_12vars.csv`
- 聚类摘要：`data/derived/team_clustering_summary_12vars.txt`
- 可视化：
  - `data/derived/cluster_scatter_f1_f2_12vars.png`
  - `data/derived/cluster_scatter_f1_f3_12vars.png`
  - `data/derived/cluster_centers_heatmap_12vars.png`
  - `data/derived/cluster_distribution_12vars.png`

### 2.3.2 四类风格画像

根据聚类中心值，四类风格可解释如下。

1. Cluster 2（高竞争质量型，n=40）
中心特征为Factor1显著为正（1.372），Factor2中度为正（0.446），Factor3接近0略负。该类样本通常对应进攻产出稳定、防守控制较好、整体竞争质量较高的球队赛季，实务上可理解为"高位竞争群体"。

2. Cluster 1（执行偏强但综合质量受限型，n=40）
因子2明显为正（0.908），但Factor1显著为负（-0.745），Factor3亦为负（-0.672）。其特征表现为某些执行层面有明确风格，但综合攻防质量仍受约束，体现为"战术可识别、成绩弹性有限"的群体。

3. Cluster 3（风险暴露与波动型，n=54）
Factor3显著为正（1.081），Factor1与Factor2略负。该类样本在防守风险、承压水平与阵容稳定性方面更具波动，常对应中下游球队或转型期球队的赛季表现，是样本中数量最多的一类。

4. Cluster 4（低效率保守型，n=46）
Factor2显著为负（-0.997），Factor1与Factor3均为负值。该类球队在进攻执行效率和综合质量上均不占优，更接近低效率与保守策略并存的风格区间。

### 2.3.3 聚类结果的研究意义

上述分群结果显示，英超球队风格并非单维度线性排序，而是“质量主轴 + 执行差异 + 风险差异”共同作用形成的结构。该结论对于后续章节有两点价值：

1. 可将风格类型作为解释变量，考察其与成绩指标（积分、排名、净胜球）之间的耦合关系。
2. 可在赛季维度上追踪同一球队的类型迁移，识别“风格升级”“风格失稳”与“策略调整”的轨迹。

## 2.4 风格演变分析（整合版）

本节在前述聚类和因子结果基础上，从“因子均值趋势”“聚类占比结构”和“头部球队轨迹”三个层面分析2016-2024的风格演进。

### 2.4.1 联赛层面因子趋势

基于`style_evolution_trends_12vars.csv`，联赛平均因子随时间变化呈现如下特征：

1. Factor3上升最明显（年斜率 +0.1264，2016-2024累计 +0.4240）。
这表明样本整体在“防守风险-阵容波动”维度上有增强趋势，反映联赛中部和下部样本在防守稳定性与人员连续性方面面临更大压力。

2. Factor2总体下降（年斜率 -0.0204，累计 -0.3425）。
说明机会转化与执行倾向因子在联赛平均水平上出现回落，可能与联赛竞争强度提升、防守对抗升级以及战术同质化有关。

3. Factor1小幅上升（年斜率 +0.0388，累计 +0.1226）。
体现整体竞争质量并未下降，且存在有限改善，但其增幅显著小于Factor3，提示“质量提升”与“风险抬升”并行。

对应图表：`data/derived/style_evolution_league_trends_12vars.png`。

### 2.4.2 聚类结构占比演化

依据`style_evolution_cluster_shares_12vars.csv`，聚类占比在2016-2024的变化呈现结构性迁移：

1. Cluster 3占比上升最多（+20.00%）。
即"风险暴露与波动型"样本在后期赛季比重增加，说明联赛中存在更强的风格分化与不稳定性累积。

2. Cluster 1占比下降最多（-10.00%）。
执行偏强但综合质量受限的中间状态样本减少，可能意味着球队在竞争压力下向“高质量型”或“高风险型”两端分化。

3. 其余类别呈阶段性波动。
不同赛季中，部分聚类占比出现短期抬升后回落，说明风格演化并非单调过程，而受到教练更替、转会策略、赛程密度和伤病冲击等因素共同影响。

对应图表：`data/derived/style_evolution_cluster_shares_12vars.png`。

### 2.4.3 头部球队的风格轨迹

对传统六强样本进行因子轨迹可视化（`data/derived/style_evolution_top6_12vars.png`）后可见：

1. 头部球队总体更靠近高竞争质量区间，但在不同赛季仍存在因子波动，表明即便强队也会受到战术调整与人员更替影响。
2. 个别赛季中，强队在Factor3方向短暂抬升，反映高压赛程或阵容不稳定会对防守风险维度造成可观扰动。
3. 强队长期维持高位表现的核心并非单一进攻强度，而是攻防质量、效率与风险控制的协同。

### 2.4.4 综合判断与研究启示

将三类证据合并后可以得到一个更稳健的结论：

1. 英超球队风格演变表现为“整体质量温和提升”与“风险维度显著抬升”并行。
2. 联赛结构出现由中间形态向两端分化的迹象，高竞争质量与高风险波动两类在不同阶段交替扩张。
3. 风格迁移具有显著动态性，球队并非固定属于某一类，而是随管理策略与赛季环境在类别间转移。

这意味着后续章节若讨论“风格与成绩”的关系，不应仅采用静态横截面，而应采用“风格状态 + 演变方向”的联合解释框架。

## 2.5 本章小结

本章构建并验证了一个由12变量驱动的球队风格识别体系。通过因子分析提取3个潜在风格维度，在保留70.94%信息的前提下显著压缩变量空间；通过4类聚类实现球队风格分型；通过赛季演化分析揭示了联赛风格结构的动态迁移。整体结果表明，英超球队风格是多维、动态且可度量的，这为下一章开展“风格与竞争绩效关系”分析提供了方法基础与实证输入。

## 图表与表格索引（最终版）

1. 图2-1：`data/derived/scree_plot_12vars.png`
2. 图2-2：`data/derived/factor_loadings_heatmap_12vars.png`
3. 图2-3：`data/derived/cluster_scatter_f1_f2_12vars.png`
4. 图2-4：`data/derived/cluster_scatter_f1_f3_12vars.png`
5. 图2-5：`data/derived/cluster_centers_heatmap_12vars.png`
6. 图2-6：`data/derived/cluster_distribution_12vars.png`
7. 图2-7：`data/derived/top_teams_cluster_evolution_12vars.png`
8. 图2-8：`data/derived/style_evolution_top6_12vars.png`
9. 图2-9：`data/derived/style_evolution_league_trends_12vars.png`
10. 图2-10：`data/derived/style_evolution_cluster_shares_12vars.png`
11. 表2-1：12变量体系（可由正文整理）
12. 表2-2：`data/derived/team_factor_loadings_12vars_2016_2025.csv`
13. 表2-3：`data/derived/team_cluster_statistics_12vars.csv`
14. 表2-4：`data/derived/style_evolution_trends_12vars.csv`
15. 表2-5：`data/derived/style_evolution_cluster_shares_12vars.csv`
