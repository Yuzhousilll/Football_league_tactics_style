
## Style trend dimensions (computed)

中文说明：
用于研究英超联赛风格变化的可计算指标维度。以下指标均可由已有字段计算得到。

Source coverage:
- data/*/general_stats.csv
- data/*/stats_squads_misc_for.csv
- data/*/stats_squads_keeper_for.csv
- data/*/results*_overall.csv

| Dimension (维度) | Metric (指标) | Formula (公式) | Notes / columns used (备注/使用字段) |
| --- | --- | --- | --- |
| Tempo / Rhythm (节奏) | shots_per_match | Sh / MP | Sh from general_stats, MP from results_overall |
| Tempo / Rhythm (节奏) | shots_on_target_per_match | SoT / MP | SoT, MP |
| Tempo / Rhythm (节奏) | fouls_per_match | Fls / MP | Fls from misc_for, MP from results_overall |
| Tempo / Rhythm (节奏) | offsides_per_match | Off / MP | Off from misc_for, MP from results_overall |
| Tempo / Rhythm (节奏) | cards_per_match | (CrdY + CrdR) / MP | CrdY, CrdR from misc_for, MP from results_overall |
| Attack Output (进攻产出) | goals_per_match | GF / MP | GF from results_overall |
| Attack Output (进攻产出) | assists_per_match | Ast / MP | Ast from general_stats |
| Attack Efficiency (进攻效率) | goals_per_shot | Gls / Sh | Gls, Sh from general_stats |
| Attack Efficiency (进攻效率) | goals_per_sot | Gls / SoT | Gls, SoT from general_stats |
| Attack Style (进攻方式) | cross_volume_per_match | Crs / MP | Crs from misc_for, MP from results_overall |
| Attack Style (进攻方式) | cross_share_of_touches | Crs / (Sh + Crs) | Proxy: crossing tendency relative to shooting |
| Set Pieces (定位球) | penalty_goal_share | PK / GF | PK from general_stats, GF from results_overall |
| Set Pieces (定位球) | penalties_won_per_match | PKwon / MP | PKwon from misc_for |
| Build Up vs Direct (推进方式) | offsides_to_shots_ratio | Off / Sh | Proxy for direct runs and verticality |
| Defense Output (防守表现) | goals_against_per_match | GA / MP | GA from results_overall |
| Defense Output (防守表现) | clean_sheet_pct | CS / MP | CS from keeper_for, MP from results_overall |
| Defense Style (防守方式) | tackles_won_per_match | TklW / MP | TklW from misc_for |
| Defense Style (防守方式) | interceptions_per_match | Int / MP | Int from misc_for |
| Defense Style (防守方式) | defensive_actions_per_match | (TklW + Int) / MP | Proxy for defensive activity |
| Keeper Impact (门将影响) | save_pct | Save% | Save% from keeper_for |
| Keeper Impact (门将影响) | shots_on_target_against_per_match | SoTA / MP | SoTA from keeper_for |
| Discipline (纪律) | red_cards_per_match | CrdR / MP | CrdR from misc_for |
| Discipline (纪律) | fouls_drawn_per_match | Fld / MP | Fld from misc_for |
| Squad Profile (球队结构) | avg_age | Age | Age from general_stats |
| Squad Profile (球队结构) | players_used | # Pl | # Pl from misc_for |
