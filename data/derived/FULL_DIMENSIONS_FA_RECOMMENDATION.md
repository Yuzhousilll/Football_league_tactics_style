# 基于原始全部维度的因子分析变量建议

## 分析前提
- 数据源：`style_metrics_all.csv`
- 赛季范围：2016-2017 到 2024-2025
- 样本量：180（9赛季 × 20队）
- 原始数值维度：25

## 全维度筛选结果
- 缺失/方差过滤后维度：25
- 自动推荐维度：20
- 自动提取因子数：6（特征值 > 1）
- KMO（推荐维度集合）：**0.7125**（达到可用水平）

## 自动推荐变量（20个）
1. shots_per_match
2. shots_on_target_per_match
3. offsides_per_match
4. cards_per_match
5. goals_per_match
6. assists_per_match
7. goals_per_shot
8. goals_per_sot
9. cross_volume_per_match
10. cross_share_of_touches
11. penalty_goal_share
12. penalties_won_per_match
13. offsides_to_shots_ratio
14. goals_against_per_match
15. clean_sheet_pct
16. tackles_won_per_match
17. interceptions_per_match
18. defensive_actions_per_match
19. shots_on_target_against_per_match
20. players_used

## 不推荐变量（共同度偏低）
- save_pct
- fouls_per_match
- avg_age
- red_cards_per_match
- fouls_drawn_per_match

## 建议用于论文主模型的“精简版变量”（12个）
为避免高相关冗余（例如 goals_per_match 与 assists_per_match、shots_per_match 与 shots_on_target_per_match），建议使用下列12个变量作为主模型输入：

1. shots_on_target_per_match
2. goals_per_match
3. goals_per_sot
4. cross_share_of_touches
5. penalties_won_per_match
6. offsides_to_shots_ratio
7. goals_against_per_match
8. clean_sheet_pct
9. tackles_won_per_match
10. interceptions_per_match
11. shots_on_target_against_per_match
12. players_used

## 相关输出文件
- `data/derived/full_dimensions_variable_screening.csv`
- `data/derived/full_dimensions_factor_loadings.csv`
- `data/derived/full_dimensions_factor_scores.csv`
- `data/derived/full_dimensions_fa_summary.txt`
- `scripts/select_fa_variables_from_full.py`
