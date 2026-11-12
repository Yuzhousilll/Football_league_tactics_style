# 参数与数据口径

配置示例见 `configs/premier-league.json` 和 `configs/custom-league.json`。支持的联赛键为 `premier-league`、`la-liga`、`bundesliga`、`serie-a`、`ligue-1`。`season_start` 和 `season_end` 均为包含端点的完整赛季，例如 `2022-2023`。球队和球员用列表表示；空列表表示不生成对应案例。名称以数据源规范名为准，也可在 `aliases.teams` / `aliases.players` 中显式映射。

## 数据来源

- `archive`：`root` 指向包含三个归档 CSV 的目录。球队使用 `style_metrics_all.csv`，真实积分与比赛场次来自 `all_stats.csv`，球员来自 `all_top_stats.csv`。只有英超2016–2017至2024–2025的球队指标完整；2015–2016不在模型归档覆盖范围。
- `csv`：提供 `teams_csv`，有球员案例时另提供 `players_csv`。字段见下文。可在 `source.expected_teams_per_season` 中声明各赛季应有球队数，程序将据此检查覆盖。
- `html`：`team_html` 是赛季到球队页面文件的映射；`player_html` 是赛季到球员标准统计页面的映射。支持普通 HTML、浏览器 view-source 页面和注释包裹的表格。每季球队页需有总体积分表；可选 shooting、standard、misc、keeper 球队表提供模型指标。球员不能从球队页凭空生成。
- `online`：按联赛ID和赛季下载 FBref 球队页，每次间隔5秒，保存原始页面及时间。403/429立即失败，不进行自动重试或反爬绕过。此模式仍需以 `player_html` 提供球员表；也可统一使用规范CSV。页面或指标变更时程序会失败或注明模型不可用；在线可访问性不能保证。

所有输入相对路径以配置文件所在目录为准；建议将配置与数据保存在同一研究工作区。归档或规范CSV不会被原地修改。

## 球队CSV

每行是一个球队赛季，主键列：`league,Season,Squad`。

12个风格指标：

| 字段 | 口径 |
| --- | --- |
| shots_on_target_per_match | 场均射正 |
| goals_per_match | 场均进球 |
| goals_per_sot | 非乌龙球进球数除以射正数，保留来源对进球的定义 |
| cross_share_of_shots_and_crosses | 传中数除以传中数与射门数之和 |
| penalties_won_per_match | 场均赢得点球数 |
| offsides_to_shots_ratio | 越位数除以射门数 |
| goals_against_per_match | 场均失球 |
| clean_sheet_pct | 零封场次占比赛场次，取值0至1 |
| tackles_won_per_match | 场均抢断成功 |
| interceptions_per_match | 场均拦截 |
| shots_on_target_against_per_match | 场均被射正 |
| players_used | 当赛季实际使用球员总数，非场均 |

动作PCA共8项：`shots_per_match,shots_on_target_per_match,assists_per_match,cross_volume_per_match,penalties_won_per_match,tackles_won_per_match,interceptions_per_match,fouls_drawn_per_match`。其中另外四项分别为场均射门、助攻、传中、被侵犯次数。

可选：`points` 为实际积分，`MP` 为实际比赛场次，`GF` 为球队总进球。缺少积分时跳过积分扩展；缺少球队总进球时不生成球员进球占比。不同联赛不能混合建模，配置联赛外的行会被筛除，缺少指定赛季时失败。

## 球员CSV

主键：`league,Season,Squad,Player`。可选字段：`Goals,Assists,Minutes,Goals_per90,Assists_per90,Position,PlayerID,data_scope`。有 `Minutes` 时重新计算每90分钟值；无分钟时保留源站明确提供的每90分钟值，不能倒推分钟。分钟为零时每90分钟值为空。`data_scope` 应说明全表还是排行榜。

转会球员保留各队分行，删除上游多队合计行；球队名称必须与球队表一致，否则不能计算该队贡献占比。同名球员须在输入中明确区分，不能猜测合并。统计列以数字存储；缺失为空值，不能填造零。

## 模型参数

`clusters` 默认4；`max_factors` 默认6；`missing_threshold` 默认0.2；`random_state` 默认42。样本少于30或每指标5倍时跳过对应模型。指标缺失率超阈值或为常量时不强行拟合；其余缺失按模型样本中位数填补并留记录。`points_extension` 默认false，显式开启时才运行按赛季留出验证的积分回顾模型。

`event` 为可选案例事件，包含 `team,player,season,label`。球员和球队必须在本次案例列表中；该赛季及之后为事件后，之前为事件前。前后至少各一个实际赛季才比较，不把描述差异解释成球员因果影响。更换案例时同时更新或删除event。默认哈兰德加盟赛季来自用户最终版论文。
