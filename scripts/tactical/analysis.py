import warnings
import numpy as np
import pandas as pd
from scipy.stats import chi2
from sklearn.cluster import KMeans
from sklearn.decomposition import FactorAnalysis, PCA
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, r2_score, silhouette_score
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning

from .config import STYLE, ACTION


def prepare(df, variables, c):
    absent=[x for x in variables if x not in df]
    if absent:
        return None, {'status':'unavailable','reason':f'缺少模型指标：{", ".join(absent)}'}
    values=df[variables].copy()
    missing=values.isna().mean()
    excess=missing[missing>c['model']['missing_threshold']]
    if not excess.empty:
        return None, {'status':'unavailable','reason':f'指标缺失比例超限：{excess.round(3).to_dict()}'}
    keep=values.isna().mean(axis=1)<=c['model']['missing_threshold']
    work=df.loc[keep].copy()
    if len(work)<max(30,5*len(variables)):
        return None, {'status':'unavailable','reason':f'有效样本 {len(work)}，少于最低要求 {max(30,5*len(variables))}'}
    if (work[variables].nunique()<2).any():
        return None, {'status':'unavailable','reason':'存在常量或全空模型指标'}
    fill=work[variables].median()
    imputed=work[variables].fillna(fill)
    x=StandardScaler().fit_transform(imputed)
    return (work, x), {'status':'ok','n':len(work),'variables':variables,
       'imputed_cells':int(work[variables].isna().sum().sum()),'dropped_rows':int((~keep).sum()),
       'medians':fill.to_dict()}


def diagnostics(x):
    n,p=x.shape; corr=np.corrcoef(x,rowvar=False)
    if np.linalg.matrix_rank(corr)<p:
        return {'kmo':None,'bartlett_p':None,'note':'相关矩阵奇异，KMO 与 Bartlett 检验未报告'}
    inv=np.linalg.inv(corr)
    partial=-inv/np.sqrt(np.outer(np.diag(inv),np.diag(inv)))
    np.fill_diagonal(partial,0)
    squared=corr**2; np.fill_diagonal(squared,0)
    kmo=float(squared.sum()/(squared.sum()+(partial**2).sum()))
    sign,logdet=np.linalg.slogdet(corr)
    stat=-(n-1-(2*p+5)/6)*logdet
    return {'kmo':kmo,'bartlett_chi2':float(stat),'bartlett_df':p*(p-1)//2,
            'bartlett_p':float(chi2.sf(stat,p*(p-1)//2)) if sign>0 else None}


def orient(components, scores):
    signs=np.sign(components[np.arange(len(components)),np.argmax(abs(components),axis=1)])
    signs[signs==0]=1
    return components*signs[:,None],scores*signs


def style_model(df,c,out):
    ready,meta=prepare(df,STYLE,c)
    if ready is None:
        return meta,None
    work,x=ready
    meta['diagnostics']=diagnostics(x)
    eigen=np.linalg.eigvalsh(np.corrcoef(x,rowvar=False))[::-1]
    nf=max(1,min(int((eigen>1).sum()),c['model']['max_factors'],len(STYLE)-1))
    fa=FactorAnalysis(n_components=nf,random_state=c['model']['random_state'],max_iter=2000)
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter('always',ConvergenceWarning)
        scores=fa.fit_transform(x)
    if any(issubclass(w.category,ConvergenceWarning) for w in seen):
        return {'status':'unavailable','reason':'因子分析未收敛；未输出模型结论'},None
    components,scores=orient(fa.components_,scores)
    factors=[f'F{i+1}' for i in range(nf)]
    loading=pd.DataFrame(components.T,index=STYLE,columns=factors)
    loading['communality']=(components**2).sum(axis=0)
    loading.rename_axis('variable').to_csv(out/'factor_loadings.csv',encoding='utf-8-sig')
    result=work[['league','Season','Squad']].reset_index(drop=True)
    result[factors]=scores
    k=c['model']['clusters']
    if len(np.unique(scores,axis=0))<=k:
        meta['clustering']={'status':'unavailable','reason':'不同因子得分数量不足以支持指定聚类数'}
    else:
        km=KMeans(n_clusters=k,n_init=20,random_state=c['model']['random_state'])
        labels=km.fit_predict(scores)
        # Stable labels ordered lexicographically by fitted factor centroids.
        order=sorted(range(k),key=lambda j:tuple(km.cluster_centers_[j]))
        names={old:new+1 for new,old in enumerate(order)}
        result['Cluster']=[names[x] for x in labels]
        meta['clustering']={'status':'ok','k':k,'silhouette':float(silhouette_score(scores,labels)),
                            'sizes':result.Cluster.value_counts().sort_index().to_dict()}
        pd.DataFrame(km.cluster_centers_[order],columns=factors,index=range(1,k+1)).rename_axis('Cluster').to_csv(out/'cluster_centers.csv')
        shares=pd.crosstab(result.Season,result.Cluster,normalize='index')
        shares.to_csv(out/'cluster_shares.csv')
    result.to_csv(out/'factor_scores.csv',index=False,encoding='utf-8-sig')
    result.groupby('Season')[factors].mean().to_csv(out/'factor_trends.csv')
    meta.update({'factors':nf,'correlation_eigenvalues':eigen.tolist(),
                 'common_variance_share':float((components**2).sum()/len(STYLE)),
                 'top_loadings':{f:loading[f].reindex(loading[f].abs().sort_values(ascending=False).index).head(3).to_dict() for f in factors}})
    return meta,result


def action_model(df,c,out):
    ready,meta=prepare(df,ACTION,c)
    if ready is None:
        return meta,None
    work,x=ready
    full=PCA().fit(x)
    k=max(1,int((full.explained_variance_>1).sum()))
    scores=full.transform(x)[:,:k]
    components,scores=orient(full.components_[:k],scores)
    cols=[f'PC{i+1}' for i in range(k)]
    weights=full.explained_variance_ratio_[:k]; weights=weights/weights.sum()
    result=work[['league','Season','Squad']].reset_index(drop=True)
    result[cols]=scores
    result['action_index']=scores@weights
    result['index_rank']=result.groupby('Season').action_index.rank(ascending=False,method='min')
    for field in ['points','MP','GF','goals_per_match','goals_against_per_match']:
        if field in work:
            result[field]=work[field].to_numpy()
    result.to_csv(out/'action_scores.csv',index=False,encoding='utf-8-sig')
    loadings=pd.DataFrame(components.T*np.sqrt(full.explained_variance_[:k]),index=ACTION,columns=cols)
    loadings.rename_axis('variable').to_csv(out/'action_loadings.csv',encoding='utf-8-sig')
    meta.update({'components':k,'explained_variance_ratio':full.explained_variance_ratio_[:k].tolist(),
                 'explained_total':float(full.explained_variance_ratio_[:k].sum()),'weights':weights.tolist(),
                 'diagnostics':diagnostics(x),'sign_rule':'每个主成分绝对载荷最大的变量取正向'})
    return meta,result


def points_model(df,c,out):
    variables=['shots_per_match','shots_on_target_per_match','goals_per_match',
               'cross_volume_per_match','interceptions_per_match','tackles_won_per_match']
    if 'points' not in df or df.points.isna().any():
        return {'status':'unavailable','reason':'缺少完整真实积分；不使用进球等代理值伪装积分'}
    if not set(variables)<=set(df):
        return {'status':'unavailable','reason':'缺少积分回归所需指标'}
    seasons=sorted(df.Season.unique())
    if len(seasons)<3:
        return {'status':'unavailable','reason':'少于三个赛季，无法按时间留出验证'}
    train=df[df.Season<seasons[-1]]; test=df[df.Season==seasons[-1]]
    if len(train)<40 or len(test)<10 or (train[variables].isna().mean()>c['model']['missing_threshold']).any() or (test[variables].isna().mean()>c['model']['missing_threshold']).any():
        return {'status':'unavailable','reason':'训练/留出赛季样本或数据完整性不足'}
    if (train[variables].nunique()<2).any():
        return {'status':'unavailable','reason':'积分回归训练指标存在常量'}
    median=train[variables].median(); x=train[variables].fillna(median); xt=test[variables].fillna(median)
    model=RandomForestRegressor(n_estimators=200,max_depth=5,min_samples_leaf=3,random_state=c['model']['random_state'],n_jobs=1)
    model.fit(x,train.points); pred=model.predict(xt)
    baseline=DummyRegressor().fit(x,train.points).predict(xt)
    perm=permutation_importance(model,xt,test.points,n_repeats=10,random_state=c['model']['random_state'],scoring='neg_mean_absolute_error')
    pd.DataFrame({'variable':variables,'mae_increase':perm.importances_mean,'std':perm.importances_std}).to_csv(out/'points_importance.csv',index=False)
    test[['league','Season','Squad','points']].assign(predicted_points=pred).to_csv(out/'points_holdout.csv',index=False)
    return {'status':'ok','train_n':len(train),'test_n':len(test),'holdout_season':seasons[-1],
       'mae':float(mean_absolute_error(test.points,pred)), 'baseline_mae':float(mean_absolute_error(test.points,baseline)),
       'r2':float(r2_score(test.points,pred)), 'purpose':'用赛季结束时指标回顾性解释同赛季积分；不是赛前预测或球员因果效应'}


def player_cases(players,teams,c,out):
    if not c['players']:
        return {'status':'not_requested'},players.iloc[:0].copy()
    p=players[players.Player.isin(c['players'])].copy()
    p=p.merge(teams[[x for x in ['league','Season','Squad','GF'] if x in teams]],on=['league','Season','Squad'],how='left',validate='many_to_one')
    if {'Goals','GF'}<=set(p):
        p['team_goal_share']=p.Goals/p.GF.replace(0,np.nan)
        if (p.team_goal_share.dropna()>1).any():
            raise ValueError('球员进球超过所属球队进球，请检查转会合计行与联赛口径')
    p.to_csv(out/'player_cases.csv',index=False,encoding='utf-8-sig')
    comparisons=[]
    for player in c['players']:
        for s in sorted(p.loc[p.Player==player,'Season'].unique()):
            for metric in ['Goals','Goals_per90','每90min射门数']:
                if metric not in players:
                    continue
                # Compare each metric's top ten independently, as in the final thesis.
                pool=players[(players.Season==s)&(players.Player!=player)].dropna(subset=[metric])
                if pool.Player.duplicated().any():
                    # Transfer totals cannot be reconstructed reliably from leaderboard fragments.
                    continue
                top=pool.nlargest(10,metric)
                value=p.loc[(p.Player==player)&(p.Season==s),metric].dropna()
                if len(top) and len(value)==1:
                    comparisons.append({'Player':player,'Season':s,'metric':metric,'player_value':float(value.iloc[0]),
                        'peer_top_n':len(top),'peer_mean':float(top[metric].mean()),'pool_n':len(pool)})
    if comparisons:
        pd.DataFrame(comparisons).to_csv(out/'player_peer_comparison.csv',index=False,encoding='utf-8-sig')
    coverage={name:{'seasons':sorted(p.loc[p.Player==name,'Season'].unique()),
                     'missing_seasons':sorted(set(c['seasons'])-set(p.loc[p.Player==name,'Season']))} for name in c['players']}
    return {'status':'ok','rows':len(p),'coverage':coverage,'peer_comparison_rows':len(comparisons),
            'scope':sorted(p.data_scope.unique()) if 'data_scope' in p else ['supplied_csv']},p


def event_comparison(teams,c,out):
    event=c.get('event')
    if not event:
        return {'status':'not_requested'}
    frame=teams[teams.Squad==event['team']]
    pre=frame[frame.Season<event['season']];post=frame[frame.Season>=event['season']]
    if pre.empty or post.empty:
        return {'status':'unavailable','reason':'指定事件前后至少各需一个有数据的赛季；当前范围不满足'}
    metrics=['shots_per_match','shots_on_target_per_match','goals_per_match','cross_volume_per_match']
    rows=[]
    for metric in metrics:
        if metric not in frame or pre[metric].dropna().empty or post[metric].dropna().empty:
            continue
        before,after=pre[metric].mean(),post[metric].mean()
        rows.append({'metric':metric,'pre_mean':before,'post_mean':after,'change_pct':(after/before-1)*100 if before else np.nan,
                     'pre_n':int(pre[metric].notna().sum()),'post_n':int(post[metric].notna().sum())})
    if not rows:
        return {'status':'unavailable','reason':'事件前后缺少可比进攻指标'}
    pd.DataFrame(rows).to_csv(out/'event_comparison.csv',index=False,encoding='utf-8-sig')
    return {'status':'ok','team':event['team'],'player':event['player'],'season':event['season'],'label':event.get('label','事件'),
        'pre_seasons':sorted(pre.Season.unique()),'post_seasons':sorted(post.Season.unique()),
        'interpretation':'仅为事件前后的描述差异，不控制教练、队友、伤病或对手变化，不等同于球员因果效应'}
