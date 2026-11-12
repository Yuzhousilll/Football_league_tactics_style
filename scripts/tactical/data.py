"""Read archived/normalized CSVs or FBref data-stat HTML with provenance."""
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import time
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup, Comment
import requests

from .config import LEAGUES, resolve, season


def fingerprint(path, kind, **extra):
    p = Path(path)
    return {'kind': kind, 'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), **extra}


def numeric(series):
    return pd.to_numeric(series.astype(str).str.replace(',', '', regex=False).str.rstrip('%'), errors='coerce')


def validate_frame(df, c, player=False):
    keys = ['league', 'Season', 'Squad'] + (['Player'] if player else [])
    missing = set(keys) - set(df.columns)
    if missing:
        raise ValueError(f'数据缺少主键列 {sorted(missing)}')
    if df[keys].isna().any().any():
        raise ValueError('数据主键包含空值')
    df = df.copy()
    df['Season'] = df['Season'].map(season)
    df = df[(df.league == c['league']) & df.Season.isin(c['seasons'])].copy()
    for col, category in [('Squad', 'teams'), ('Player', 'players')] if player else [('Squad', 'teams')]:
        df[col] = df[col].astype(str).str.strip().replace(c['aliases'].get(category, {}))
        if df[col].eq('').any():
            raise ValueError(f'{col} 包含空名称')
    if df.duplicated(keys).any():
        raise ValueError(f'数据主键重复：{df.loc[df.duplicated(keys, keep=False), keys].head().to_dict("records")}')
    for col in df.columns.difference(keys):
        if col not in {'data_scope', 'Position', 'PlayerID'}:
            original = df[col]
            df[col] = numeric(original)
            if (original.notna() & df[col].isna()).any():
                raise ValueError(f'{col} 包含无法解析的数值')
    num = df.select_dtypes(include='number')
    if np.isinf(num.to_numpy()).any():
        raise ValueError('数据包含无穷值')
    for col in ['MP', 'Minutes', 'goals_per_match', 'goals_against_per_match', 'Goals', 'Assists']:
        if col in df and (df[col].dropna() < 0).any():
            raise ValueError(f'{col} 不允许负数')
    if 'MP' in df and (df.MP.dropna() <= 0).any():
        raise ValueError('比赛场次必须为正')
    for col in ('clean_sheet_pct', 'goals_per_sot', 'cross_share_of_shots_and_crosses'):
        if col in df and not df[col].dropna().between(0, 1).all():
            raise ValueError(f'{col} 必须为 0 至 1 的比例')
    return df.sort_values(keys).reset_index(drop=True)


def validate_coverage(teams, players, c):
    missing = set(c['seasons']) - set(teams.Season)
    if missing:
        raise ValueError(f'球队数据缺少完整赛季：{sorted(missing)}')
    for s,count in c['source'].get('expected_teams_per_season',{}).items():
        if s in c['seasons'] and teams[teams.Season==s].Squad.nunique()!=count:
            raise ValueError(f'{s} 球队数量与配置的完整性要求 {count} 不符')
    for key, frame, col in [('teams', teams, 'Squad'), ('players', players, 'Player')]:
        absent = set(c[key]) - (set(frame[col]) if col in frame else set())
        if absent:
            raise ValueError(f'找不到指定{key}：{sorted(absent)}。请检查名称、别名或数据覆盖范围')


def archive(c):
    root = resolve(c, c['source'].get('root', '..'))
    metrics_path, results_path, player_path = [root / x for x in ['style_metrics_all.csv', 'all_stats.csv', 'all_top_stats.csv']]
    t = pd.read_csv(metrics_path).rename(columns={'cross_share_of_touches': 'cross_share_of_shots_and_crosses'})
    r = pd.read_csv(results_path).rename(columns={'season': 'Season', 'Pts': 'points'})
    t['Season'], r['Season'] = t.Season.map(season), r.Season.map(season)
    if r.duplicated(['Season', 'Squad']).any():
        raise ValueError('历史积分表主键重复')
    r['MP'] = r[['W','D','L']].sum(axis=1, min_count=3)
    t = t.merge(r[['Season','Squad','points','MP','GF','Poss']], on=['Season','Squad'], validate='one_to_one', how='left')
    t.insert(0, 'league', 'premier-league')
    p = pd.read_csv(player_path).dropna(subset=['player','squad','value'])
    if p.duplicated(['season','player','squad','metric']).any():
        raise ValueError('球员排行榜存在重复条目')
    p = p.pivot(index=['season','player','squad'], columns='metric', values='value').reset_index()
    p = p.rename(columns={'season':'Season','player':'Player','squad':'Squad','最佳射手':'Goals','助攻王':'Assists',
                          '每90min进球榜':'Goals_per90','每90min助攻榜':'Assists_per90'})
    p.insert(0, 'league', 'premier-league')
    p['data_scope'] = 'leaderboard_only'
    return t, p, [fingerprint(x,'repository_archive') for x in [metrics_path, results_path, player_path]], [
        '历史球员数据仅覆盖排行榜入选条目；未上榜表示缺测，不表示该项为零。',
        '历史 cross_share_of_touches 实际分母为射门数与传中数之和；已更名，不解释为触球占比。']


def parse_tables(html):
    """Use stable data-stat names rather than positional/multi-row headers."""
    soup = BeautifulSoup(html, 'lxml')
    if soup.select('td.line-content'):
        soup = BeautifulSoup('\n'.join(x.get_text() for x in soup.select('td.line-content')), 'lxml')
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if '<table' in comment:
            comment.replace_with(BeautifulSoup(str(comment), 'lxml'))
    result = {}
    for table in soup.find_all('table'):
        rows=[]
        for tr in table.select('tbody tr'):
            if 'thead' in tr.get('class', []):
                continue
            row={cell.get('data-stat'):cell.get_text(' ',strip=True) for cell in tr.find_all(['th','td']) if cell.get('data-stat')}
            if row:
                rows.append(row)
        if rows:
            result[table.get('id','')] = pd.DataFrame(rows)
    return result


def select_table(tables, prefix):
    matches=[v for k,v in tables.items() if k.startswith(prefix)]
    if len(matches)!=1:
        raise ValueError(f'需要唯一的 {prefix} 表，实际找到 {len(matches)}；请检查页面或数据供应方字段变更')
    return matches[0]


def team_metrics(tables):
    results = select_table(tables, 'results').copy()
    # A combined home/away table also starts with results; select only overall upstream.
    base = results.rename(columns={'team':'Squad','squad':'Squad','games':'MP','points':'points','goals_for':'GF','goals_against':'GA'})
    cols=[x for x in ['Squad','MP','points','GF','GA'] if x in base]
    base=base[cols]
    if not {'Squad','MP','GF','GA'} <= set(base):
        raise ValueError('积分表缺少球队/比赛/进球/失球字段')
    maps={
        'stats_squads_standard_for': {'assists':'Ast','goals':'Gls','pens_made':'PK','players_used':'players_used'},
        'stats_squads_shooting_for': {'shots':'Sh','shots_on_target':'SoT'},
        'stats_squads_misc_for': {'crosses':'Crs','interceptions':'Int','tackles_won':'TklW','pens_won':'PKwon','fouls':'Fls','fouled':'Fld','offsides':'Off'},
        'stats_squads_keeper_for': {'clean_sheets':'CS','shots_on_target_against':'SoTA'},
    }
    for table_id,mapping in maps.items():
        table=tables.get(table_id)
        if table is None:
            continue
        table=table.rename(columns={'team':'Squad','squad':'Squad',**mapping})
        keep=['Squad']+[v for v in mapping.values() if v in table]
        base=base.merge(table[keep],on='Squad',how='left',validate='one_to_one')
    for col in base.columns.difference(['Squad']):
        base[col]=numeric(base[col])
    def ratio(a,b):
        left=base[a] if a in base else pd.Series(np.nan,index=base.index)
        right=base[b] if b in base else pd.Series(np.nan,index=base.index)
        return left/right.replace(0,np.nan)
    for name,a,b in [('shots_per_match','Sh','MP'),('shots_on_target_per_match','SoT','MP'),
                     ('goals_per_match','GF','MP'),('goals_against_per_match','GA','MP'),
                     ('goals_per_sot','Gls','SoT'),('assists_per_match','Ast','MP'),
                     ('cross_volume_per_match','Crs','MP'),('penalties_won_per_match','PKwon','MP'),
                     ('offsides_to_shots_ratio','Off','Sh'),('clean_sheet_pct','CS','MP'),
                     ('tackles_won_per_match','TklW','MP'),('interceptions_per_match','Int','MP'),
                     ('shots_on_target_against_per_match','SoTA','MP'),('fouls_drawn_per_match','Fld','MP')]:
        base[name]=ratio(a,b)
    base['cross_share_of_shots_and_crosses']=np.nan
    if {'Crs','Sh'}<=set(base):
        base['cross_share_of_shots_and_crosses']=base.Crs/(base.Crs+base.Sh).replace(0,np.nan)
    return base


def html_source(c, out):
    source=c['source']; mode=source['mode']; league=LEAGUES[c['league']]
    teams=[]; players=[]; provenance=[]
    for index,s in enumerate(c['seasons']):
        if mode=='online':
            if index:
                time.sleep(5)
            url=f'https://fbref.com/en/comps/{league["fbref_id"]}/{s}/{s}-{league["slug"]}-Stats'
            response=requests.get(url,timeout=40,headers={'User-Agent':'football-tactical-report/1.0 (research; local report)'})
            if response.status_code in (403,429):
                raise ValueError(f'数据源返回 {response.status_code}；停止请求，请改用获准保存的 HTML 或 CSV。{url}')
            response.raise_for_status()
            path=out/'raw'/f'{c["league"]}-{s}.html'; path.parent.mkdir(exist_ok=True)
            path.write_text(response.text,encoding='utf-8')
            provenance.append(fingerprint(path,'online',url=url,retrieved_at=datetime.now(timezone.utc).isoformat()))
        else:
            path=resolve(c,source['team_html'][s]); provenance.append(fingerprint(path,'saved_html'))
        tables=parse_tables(path.read_text(encoding='utf-8'))
        tables={k:v for k,v in tables.items() if not (k.startswith('results') and not k.endswith('_overall'))}
        frame=team_metrics(tables); frame['Season']=s; frame['league']=c['league']; teams.append(frame)
        pp=source.get('player_html',{}).get(s)
        if pp:
            player_path=resolve(c,pp); provenance.append(fingerprint(player_path,'saved_player_html'))
            ptables=parse_tables(player_path.read_text(encoding='utf-8'))
            p=select_table(ptables,'stats_standard').rename(columns={'player':'Player','team':'Squad','squad':'Squad',
               'minutes':'Minutes','goals':'Goals','assists':'Assists','position':'Position'})
            keep=[col for col in ['Player','Squad','Minutes','Goals','Assists','Position'] if col in p]
            p=p[keep].copy(); p['league']=c['league']; p['Season']=s; p['data_scope']='full_standard_table'; players.append(p)
    p=pd.concat(players,ignore_index=True) if players else pd.DataFrame(columns=['league','Season','Squad','Player'])
    return pd.concat(teams,ignore_index=True),p,provenance,[]


def load_data(c,out):
    mode=c['source']['mode']
    if mode=='archive':
        t,p,provenance,notes=archive(c)
    elif mode=='csv':
        tp=resolve(c,c['source']['teams_csv']); t=pd.read_csv(tp); provenance=[fingerprint(tp,'normalized_csv')]; notes=[]
        if c['source'].get('players_csv'):
            pp=resolve(c,c['source']['players_csv']); p=pd.read_csv(pp); provenance.append(fingerprint(pp,'normalized_player_csv'))
        else:
            p=pd.DataFrame(columns=['league','Season','Squad','Player'])
    else:
        t,p,provenance,notes=html_source(c,out)
    t,p=validate_frame(t,c),validate_frame(p,c,True)
    validate_coverage(t,p,c)
    if not p.empty and 'Minutes' in p:
        minutes=p.Minutes.replace(0,np.nan)
        for total in ['Goals','Assists']:
            if total in p:
                p[f'{total}_per90']=p[total]*90/minutes
    return t,p,provenance,notes
