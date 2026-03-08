# 第2章结果写作稿（12变量正式版）

## 2.2 因子分析结果与解释

本文在2016-2017至2024-2025赛季英超球队数据基础上，选取12个风格指标进行因子分析。通过标准化处理后，依据特征值大于1的准则提取出3个公共因子。模型的累计解释能力约为70.94%，说明该因子结构能够较好地压缩原始变量信息，并保留主要风格差异。

从因子载荷结果看（见`data/derived/team_factor_loadings_12vars_2016_2025.csv`），三个因子的含义可解释为：

1. 因子1（综合竞争质量因子）
该因子在`goals_per_match`（0.996）、`shots_on_target_per_match`（0.917）和`goals_per_sot`（0.725）上呈现较高正载荷，同时在`goals_against_per_match`（-0.669）和`shots_on_target_against_per_match`（-0.674）上呈现较高负载荷。说明因子1高分球队通常进攻产出更高、防守承压更低，体现“攻防综合质量更优”的特征。

2. 因子2（进攻效率与执行风格因子）
该因子对`goals_per_sot`（-0.670）和`shots_on_target_per_match`（0.371）有较明显载荷，反映球队在进攻转化效率与进攻执行方式上的差异。该因子可理解为“机会转化与进攻执行偏好”的补充维度。

3. 因子3（防守风险与阵容波动因子）
该因子在`goals_against_per_match`（0.674）、`shots_on_target_against_per_match`（0.517）与`players_used`（0.553）上负荷较高，在`clean_sheet_pct`（-0.598）上呈负载荷，表明其刻画的是“防守失球风险+阵容使用波动”的联合特征。

整体上，因子1负责区分强弱格局，因子2和因子3进一步刻画球队在风格执行与防守风险上的结构差异。碎石图见`data/derived/scree_plot_12vars.png`，载荷热力图见`data/derived/factor_loadings_heatmap_12vars.png`。

## 2.3 基于因子得分的球队聚类识别

在3个因子得分基础上，采用K-means方法进行4类聚类，得到180个球队-赛季样本的分组结果（见`data/derived/team_clusters_assigned_12vars.csv`）。四类样本规模分别为40、40、54、46，分布较为均衡。

各聚类中心（见`data/derived/team_cluster_statistics_12vars.csv`）可归纳为：

1. Cluster 1（高竞争质量型，n=40）
因子1显著为正（1.372），且因子2也为正（0.446），说明该类球队具备较高攻防质量与较稳定执行能力，通常对应争冠或欧战区球队赛季样本。

2. Cluster 0（执行型防守稳态，n=40）
因子2显著为正（0.908），因子1为负（-0.745），因子3为负（-0.672）。该类球队在某些执行层面具备特征优势，但综合质量不及第一类，更接近“体系执行明确但上限受限”的球队群体。

3. Cluster 2（高风险波动型，n=54）
因子3显著为正（1.081），而因子1与因子2均略低于0，表现为防守风险暴露和阵容波动更明显，整体稳定性偏弱，常见于中下游或阶段性波动较大的样本。

4. Cluster 3（低效率保守型，n=46）
因子2显著为负（-0.997），因子1和因子3也低于0，反映其在进攻执行和综合质量上均不占优，偏向低效保守或长期弱势风格。

二维散点可视化见`data/derived/cluster_scatter_f1_f2_12vars.png`与`data/derived/cluster_scatter_f1_f3_12vars.png`，聚类中心热图见`data/derived/cluster_centers_heatmap_12vars.png`，规模分布图见`data/derived/cluster_distribution_12vars.png`。

## 2.4 风格结构的时间演变

进一步地，本文基于赛季序列考察球队聚类身份的动态迁移（见`data/derived/top_teams_cluster_evolution_12vars.png`）。结果显示：

1. 强队样本更容易长期停留在高竞争质量型（Cluster 1）或在Cluster 1与Cluster 0之间波动，体现为稳定的体系执行与较高的攻防产出。
2. 中游球队更常在Cluster 0、Cluster 2与Cluster 3之间切换，说明其风格受教练更替、阵容变动和赛季目标调整影响更大。
3. 高风险波动型（Cluster 2）在多个赛季中占比较高（54个样本），提示英超中下游群体普遍存在防守稳定性不足和阵容管理波动问题。

综合来看，12变量正式版分析不仅能识别“谁更强”，也能说明“强弱差异来自何种攻防机制”，并通过聚类迁移轨迹呈现球队风格在时间维度上的动态演化。这为后续章节讨论风格与成绩之间的关系提供了可量化基础。

## 图表与表格对应建议

1. 图2-1：`data/derived/scree_plot_12vars.png`
2. 图2-2：`data/derived/factor_loadings_heatmap_12vars.png`
3. 图2-3：`data/derived/cluster_scatter_f1_f2_12vars.png`
4. 图2-4：`data/derived/cluster_scatter_f1_f3_12vars.png`
5. 图2-5：`data/derived/cluster_centers_heatmap_12vars.png`
6. 图2-6：`data/derived/cluster_distribution_12vars.png`
7. 图2-7：`data/derived/top_teams_cluster_evolution_12vars.png`
8. 表2-2：`data/derived/team_factor_loadings_12vars_2016_2025.csv`
9. 表2-3：`data/derived/team_cluster_statistics_12vars.csv`
