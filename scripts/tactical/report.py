from html import escape
from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .config import PROJECT_NAME, LEAGUES

LABELS={'Season':'赛季','Squad':'球队','Player':'球员','Goals':'进球','Assists':'助攻','Minutes':'分钟',
        'Goals_per90':'每90分钟进球','Assists_per90':'每90分钟助攻','team_goal_share':'球队进球占比',
        'action_index':'动作综合指数','index_rank':'指数排名','points':'实际积分',
        'MP':'比赛场次','goals_per_match':'场均进球','goals_against_per_match':'场均失球',
        'Cluster':'聚类','data_scope':'数据覆盖'}
LABELS.update({'metric':'指标','player_value':'球员数值','peer_top_n':'榜单前N','peer_mean':'榜单前N均值','pool_n':'可用比较记录',
               'pre_mean':'事件前均值','post_mean':'事件后均值','change_pct':'变化百分比','pre_n':'事件前赛季数','post_n':'事件后赛季数'})


def fmt(value):
    if pd.isna(value):
        return '—'
    if isinstance(value,(float,np.floating)):
        return f'{value:.3f}'
    return str(value)


def table(frame,columns=None,limit=50):
    if columns is not None:
        frame=frame[[x for x in columns if x in frame]]
    total=len(frame)
    frame=frame.head(limit)
    if frame.empty:
        return '<p>本节无可用观测。</p>','本节无可用观测。'
    headers=[LABELS.get(x,x) for x in frame.columns]
    html='<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+escape(x)+'</th>' for x in headers)+'</tr></thead><tbody>'
    md='| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'
    for row in frame.itertuples(index=False,name=None):
        html+='<tr>'+''.join('<td>'+escape(fmt(x))+'</td>' for x in row)+'</tr>'
        md+='| '+' | '.join(fmt(x).replace('|','\\|').replace('\n',' ') for x in row)+' |\n'
    html+='</tbody></table></div>'
    if total>limit:
        note=f'本表展示前{limit}行，共{total}行；完整数据见随附CSV。'
        html+='<p>'+note+'</p>';md+='\n'+note+'\n'
    return html,md


def charts(teams,style,action,players,c,out):
    figures=[]
    target=out/'figures'; target.mkdir()
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'path'})
    def save(fig,name,caption):
        fig.tight_layout(); fig.savefig(target/f'{name}.svg',bbox_inches='tight'); fig.savefig(target/f'{name}.png',dpi=160,bbox_inches='tight'); plt.close(fig)
        figures.append((name,caption))
    trends=teams.groupby('Season')[[x for x in ['goals_per_match','goals_against_per_match'] if x in teams]].mean()
    if len(trends.columns):
        fig,ax=plt.subplots(figsize=(9,3.7)); trends.plot(ax=ax,marker='o'); ax.set_ylabel('Per match'); ax.set_xlabel('Season'); ax.tick_params(axis='x',rotation=30)
        save(fig,'league_trends','图3-1 联赛进球与失球场均值；球队等权平均。')
    if style is not None:
        factors=[x for x in style if re.fullmatch(r'F\d+',x)]
        fig,ax=plt.subplots(figsize=(9,3.7)); style.groupby('Season')[factors].mean().plot(ax=ax,marker='o'); ax.set_ylabel('Mean factor score'); ax.tick_params(axis='x',rotation=30)
        save(fig,'factor_trends','图3-2 联赛因子均值趋势；各赛季共用同一标准化和因子模型。')
        if 'Cluster' in style:
            fig,ax=plt.subplots(figsize=(9,3.7)); pd.crosstab(style.Season,style.Cluster,normalize='index').plot.bar(stacked=True,ax=ax,colormap='Set2'); ax.set_ylabel('Share'); ax.tick_params(axis='x',rotation=30)
            save(fig,'cluster_shares','图3-3 各赛季风格聚类占比；类别编号仅在本次拟合内可比。')
    if action is not None and c['teams']:
        fig,ax=plt.subplots(figsize=(9,3.7))
        for team in c['teams']:
            rows=action[action.Squad==team].sort_values('Season'); ax.plot(rows.Season,rows.action_index,marker='o',label=team)
        ax.axhline(0,color='#aaa',lw=.7); ax.set_ylabel('Action index'); ax.tick_params(axis='x',rotation=30); ax.legend()
        save(fig,'team_action','图4-1 指定球队动作综合指数轨迹；分值不等于联赛积分。')
    if not players.empty and 'Goals' in players and players.Goals.notna().any():
        fig,ax=plt.subplots(figsize=(9,3.7))
        for (player,squad),rows in players.groupby(['Player','Squad']):
            rows=rows.sort_values('Season'); ax.plot(rows.Season,rows.Goals,marker='o',label=f'{player} · {squad}')
        ax.set_ylabel('League goals'); ax.tick_params(axis='x',rotation=30); ax.legend(fontsize=8)
        save(fig,'player_goals','图5-1 指定球员联赛进球；缺失年份不代表零进球。')
    return figures


def build_report(c,teams,style,action,players,summary,provenance,notes,thesis,out):
    figs=charts(teams,style,action,players,c,out)
    html_parts=[]; md_parts=[]
    def heading(text,level=2):
        html_parts.append(f'<h{level}>{escape(text)}</h{level}>'); md_parts.append('#'*level+' '+text+'\n')
    def para(text):
        html_parts.append('<p>'+escape(text)+'</p>'); md_parts.append(text+'\n')
    def add_table(df,columns=None,limit=50):
        h,m=table(df,columns,limit); html_parts.append(h); md_parts.append(m+'\n')
    def figure(name):
        for key,caption in figs:
            if key!=name:
                continue
            svg=(out/'figures'/f'{key}.svg').read_text()
            svg=svg[svg.index('<svg'):]
            html_parts.append('<figure>'+svg+'<figcaption>'+escape(caption)+'</figcaption></figure>')
            md_parts.append(f'![{caption}](figures/{key}.svg)\n\n{caption}\n')
    heading(PROJECT_NAME,1)
    scope=f'{LEAGUES[c["league"]]["name"]}｜{c["season_start"]} 至 {c["season_end"]}｜{len(teams)} 个球队赛季观测'
    para(scope)
    heading('摘要')
    available=[name for name,key in [('战术因子模型','style'),('动作主成分模型','action')] if summary[key]['status']=='ok']
    para(f'本报告以{LEAGUES[c["league"]]["name"]}的赛季统计为基础，完成数据覆盖检查、联赛风格识别及指定球队和球员的描述分析。当前可用模型：'+('、'.join(available) if available else '样本或指标不足，保留描述统计')+'。所有数值均由本次选定样本重新计算。')
    heading('1 引言')
    para('研究围绕联赛格局、球队场上表现与球员贡献三个层面展开。重点观察指标结构与赛季变化，并通过具体案例建立宏观模型与个体表现的联系。')
    para('指定球队：'+('、'.join(c['teams']) or '无')+'。指定球员：'+('、'.join(c['players']) or '无')+'。球队与球员选择仅用于案例展示，模型始终在所选联赛和时间范围内的全部可用球队上拟合。')
    heading('2 研究方法')
    para('报告结构以论文最终版的引言、研究方法、联赛战术风格、球队成绩竞争力、球员角色、结论与展望六部分为基础。对赛季统计按实际比赛场次或出场分钟转换，比例变量保持原比例口径。')
    para('风格模型使用12项指标，标准化后拟合因子分析，并依据相关矩阵特征值大于1选择因子数；随后对共同因子得分进行K-means聚类。动作模型使用8项场均行为指标进行PCA，以保留主成分的解释方差比归一化加权形成动作综合指数。')
    para('跨赛季共用标准化器与载荷。每个因子或主成分以绝对载荷最大项为正向固定符号；本次聚类按中心排序编号。更换样本后因子含义及聚类标签须重新解释，不能套用原论文的固定名称。')
    para('模型指标缺失比例超过配置阈值时跳过相应模型；样本数至少为30且不少于指标数的5倍。其余少量缺失使用本次模型样本的中位数填补并记录数量；这些阈值是本工具的运行约束，不是统计充分性的证明。')
    heading('2.1 数据质量与覆盖',3)
    counts=teams.groupby('Season').size().rename('球队数').reset_index(); add_table(counts)
    missing=teams.isna().sum(); missing=missing[missing>0]
    if len(missing):
        para('存在缺失的字段及单元格数：'+str(missing.to_dict()))
    for note in notes:
        para(note)
    heading('3 联赛战术风格识别及演变')
    sm=summary['style']
    if sm['status']=='ok':
        para(f'有效观测 {sm["n"]} 个，提取 {sm["factors"]} 个因子；载荷平方和占标准化总方差的比例为 {sm["common_variance_share"]:.2%}。这一口径与相关矩阵前若干特征值之和不同，不混称为同一解释率。填补 {sm["imputed_cells"]} 个缺失单元格，排除 {sm["dropped_rows"]} 行。')
        d=sm['diagnostics']; para('因子模型适配性：'+(f'KMO={d["kmo"]:.3f}，Bartlett p={d["bartlett_p"]:.3g}。' if d.get('kmo') is not None else d['note']))
        for f,loadings in sm['top_loadings'].items():
            para(f+' 的主要载荷：'+'；'.join(f'{x}：{v:+.3f}' for x,v in loadings.items())+'。命名应结合完整载荷表与比赛证据。')
        if sm['clustering']['status']=='ok':
            para(f'聚类数 {sm["clustering"]["k"]}，轮廓系数 {sm["clustering"]["silhouette"]:.3f}；类别规模为 {sm["clustering"]["sizes"]}。低轮廓系数提示类别边界可能重叠。')
        else:
            para(sm['clustering']['reason'])
        figure('factor_trends'); figure('cluster_shares')
    else:
        para('本节模型未生成：'+sm['reason'])
    figure('league_trends')
    if 'goals_per_match' in teams:
        means=teams.groupby('Season').goals_per_match.mean().dropna()
        if len(means)>1:
            para(f'联赛球队等权场均进球从 {means.index[0]} 的 {means.iloc[0]:.3f} 变化到 {means.index[-1]} 的 {means.iloc[-1]:.3f}。该变化描述进球产出，不单独证明压迫强度或空间控制变化。')
    heading('4 球队成绩竞争力评估')
    am=summary['action']
    if am['status']=='ok':
        para(f'动作主成分模型纳入 {am["n"]} 个观测，保留 {am["components"]} 个主成分，累计解释方差为 {am["explained_total"]:.2%}。该指数是场上动作结构的综合代理，分值或指数排名不等于联赛实力的确定排序。')
        d=am['diagnostics']; para('动作模型适配性：'+(f'KMO={d["kmo"]:.3f}，Bartlett p={d["bartlett_p"]:.3g}。' if d.get('kmo') is not None else d['note']))
        figure('team_action')
        for team in c['teams']:
            heading('4.1 '+team,3)
            rows=action[action.Squad==team].sort_values('Season')
            add_table(rows,['Season','action_index','index_rank','points'],limit=100)
            absent=sorted(set(c['seasons'])-set(rows.Season))
            if absent:
                para('缺少该球队的赛季观测：'+'、'.join(absent)+'。升降级、名称变化或数据缺漏需要结合赛季背景核实。')
            if len(rows)>1:
                para(f'本次样本中，该球队动作指数的首末观测分别为 {rows.action_index.iloc[0]:.3f} 与 {rows.action_index.iloc[-1]:.3f}；解释其变化需同时考察各主成分、实际积分及比赛背景。')
    else:
        para('本节模型未生成：'+am['reason'])
    heading('5 球员角色分析')
    if not c['players']:
        para('本次未指定球员，不生成球员案例。')
    else:
        figure('player_goals')
        for player in c['players']:
            heading('5.1 '+player,3)
            rows=players[players.Player==player].sort_values(['Season','Squad'])
            add_table(rows,['Season','Squad','Goals','Assists','Goals_per90','team_goal_share'],limit=100)
            coverage=summary['players']['coverage'][player]
            if coverage['missing_seasons']:
                para('缺少该球员观测的赛季：'+'、'.join(coverage['missing_seasons'])+'。不推断这些赛季的出场或贡献为零。')
        para('球员进球占比按同联赛、同赛季、同球队匹配计算。球员跨队赛季保留分队记录，不将多队合计行当作某支球队的数据。只有提供实际分钟时才计算每90分钟指标。')
        peer_path=out/'player_peer_comparison.csv'
        if peer_path.exists():
            heading('5.2 同项指标横向对比',3)
            add_table(pd.read_csv(peer_path),['Player','Season','metric','player_value','peer_top_n','peer_mean'])
            para('各指标分别排除研究球员后，取本次其余可用球员记录的前10名；不足10名时使用实际人数。榜单均值不是全联赛平均，也不是同位置匹配后的对照组。转会分队记录导致同名重复的赛季不做该项比较。')
        if summary.get('event',{}).get('status')=='ok':
            heading('5.3 球队事件前后对比',3)
            ev=summary['event'];para(f'{ev["player"]}：{ev["season"]} {ev["label"]}；观察球队 {ev["team"]}。事件前 {len(ev["pre_seasons"])} 季，事件后 {len(ev["post_seasons"])} 季。')
            add_table(pd.read_csv(out/'event_comparison.csv'))
            para(ev['interpretation'])
        elif summary.get('event',{}).get('status')=='unavailable':
            para('事件前后对比未生成：'+summary['event']['reason'])
        para('赛季汇总数据可以反映产出和结构差异；关于内收、牵制防线、制造空间及加盟影响的判断，需要比赛录像、事件或追踪数据支持。当前报告不将描述差异表述为球员造成的因果效应。')
    heading('6 结论与展望')
    para(f'本次研究覆盖 {len(c["seasons"])} 个赛季、{teams.Squad.nunique()} 支不同球队。联赛模型与球队、球员案例采用同一范围和数据口径，分析结果可以回溯到附录中的数据文件。')
    para('更换联赛或赛季后需要重新拟合与检验。聚类标签、载荷方向与模型分数只在本次样本内解释。数据完整性、联赛间统计定义差异、升降级造成的样本变动及小样本不确定性均会影响结论。')
    heading('参考来源与论文依据')
    para(thesis.get('statement','论文依据尚未配置；请先导入最终版 Word 和 PDF。'))
    for record in thesis.get('sources',[]):
        para(f'{record["format"]} 校验摘要：{record["sha256"]}；状态：{record["status"]}。')
    para('统计方法实现参考：scikit-learn 的 FactorAnalysis、PCA 与 KMeans 官方文档。FA 的共同方差与 PCA 的解释方差分别报告。')
    html_parts.append('<p><a href="https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.FactorAnalysis.html">FactorAnalysis 文档</a> · <a href="https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html">PCA 文档</a></p>')
    md_parts.append('[FactorAnalysis 文档](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.FactorAnalysis.html) · [PCA 文档](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html)\n')
    heading('附录 可复现文件与模型状态')
    para('输入与输出的校验摘要、运行时间、依赖版本见 manifest.json；完整参数见 config.resolved.json；质量与建模状态见 analysis.json。输入原始数据不被改写。')
    add_table(pd.DataFrame([{'模块':k,'状态':v['status'],'说明':v.get('reason','已完成')} for k,v in summary.items()]))
    if summary['points']['status']=='ok':
        pm=summary['points']; para(f'扩展积分模型：留出 {pm["holdout_season"]}，MAE={pm["mae"]:.3f}，均值基线MAE={pm["baseline_mae"]:.3f}，R²={pm["r2"]:.3f}。{pm["purpose"]}。')
    para('数据来源及校验摘要：')
    add_table(pd.DataFrame([{'来源':x.get('url',Path(x['path']).name),'类型':x['kind'],'SHA256':x['sha256']} for x in provenance]))
    css='''body{font-family:"PingFang SC","Microsoft YaHei",sans-serif;color:#202931;background:#eef1f4;margin:0;line-height:1.8}main{max-width:1000px;margin:32px auto;background:white;padding:48px 56px}h1{font-size:28px;line-height:1.4}h2{font-size:22px;margin-top:40px;border-bottom:1px solid #d8dee5;padding-bottom:8px}h3{font-size:17px;margin-top:28px}p{overflow-wrap:anywhere}table{border-collapse:collapse;width:100%;font-size:13px;margin:16px 0}td,th{border:1px solid #d8dee5;padding:9px 12px;text-align:right}th{background:#edf2f6}td:first-child,th:first-child{text-align:left}tbody tr:nth-child(even){background:#f8fafb}.table-wrap{overflow-x:auto}figure{margin:26px 0;break-inside:avoid}figure svg{max-width:100%;height:auto}figcaption{font-size:13px;color:#52606b;text-align:center}a{color:#225b8c}@media(max-width:700px){main{margin:0;padding:24px 18px}h1{font-size:23px}}@media print{@page{size:A4;margin:20mm 15mm}body{background:white;font-size:10pt}main{padding:0;margin:0;max-width:none}h2,h3{break-after:avoid}tr{break-inside:avoid}figure{break-inside:avoid}thead{display:table-header-group}}'''
    html='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+PROJECT_NAME+'</title><style>'+css+'</style></head><body><main>'+''.join(html_parts)+'</main></body></html>'
    (out/'report.html').write_text(html,encoding='utf-8')
    (out/'report.md').write_text('\n'.join(md_parts),encoding='utf-8')
