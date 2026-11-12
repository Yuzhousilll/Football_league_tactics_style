from copy import deepcopy
import json
from pathlib import Path
import re

PROJECT_NAME = '英超多赛季数据采集与战术分析'
LEAGUES = {
    'premier-league': {'name': '英超', 'fbref_id': 9, 'slug': 'Premier-League'},
    'la-liga': {'name': '西甲', 'fbref_id': 12, 'slug': 'La-Liga'},
    'bundesliga': {'name': '德甲', 'fbref_id': 20, 'slug': 'Bundesliga'},
    'serie-a': {'name': '意甲', 'fbref_id': 11, 'slug': 'Serie-A'},
    'ligue-1': {'name': '法甲', 'fbref_id': 13, 'slug': 'Ligue-1'},
}
STYLE = ['shots_on_target_per_match', 'goals_per_match', 'goals_per_sot',
         'cross_share_of_shots_and_crosses', 'penalties_won_per_match',
         'offsides_to_shots_ratio', 'goals_against_per_match', 'clean_sheet_pct',
         'tackles_won_per_match', 'interceptions_per_match',
         'shots_on_target_against_per_match', 'players_used']
ACTION = ['shots_per_match', 'shots_on_target_per_match', 'assists_per_match',
          'cross_volume_per_match', 'penalties_won_per_match',
          'tackles_won_per_match', 'interceptions_per_match', 'fouls_drawn_per_match']


def season(value):
    value = str(value).replace('_', '-')
    if not re.fullmatch(r'\d{4}-\d{4}', value) or int(value[5:]) != int(value[:4]) + 1:
        raise ValueError(f'赛季必须为相邻年份，例如 2023-2024；收到 {value}')
    return value


def load_config(path):
    path = Path(path).resolve()
    c = json.loads(path.read_text(encoding='utf-8'))
    if c.get('league') not in LEAGUES:
        raise ValueError(f'league 请选择 {list(LEAGUES)}')
    c['season_start'], c['season_end'] = season(c['season_start']), season(c['season_end'])
    start, end = int(c['season_start'][:4]), int(c['season_end'][:4])
    if start > end:
        raise ValueError('起始赛季晚于结束赛季')
    c['seasons'] = [f'{y}-{y+1}' for y in range(start, end+1)]
    for k in ('teams', 'players'):
        c.setdefault(k, [])
        if not isinstance(c[k], list) or any(not isinstance(x, str) or not x.strip() for x in c[k]):
            raise ValueError(f'{k} 必须是非空名称的列表；空列表表示不指定案例')
        if len(set(c[k])) != len(c[k]):
            raise ValueError(f'{k} 中名称重复')
    c.setdefault('aliases', {'teams': {}, 'players': {}})
    for category in ('teams','players'):
        c[category]=[c['aliases'].get(category,{}).get(x.strip(),x.strip()) for x in c[category]]
        if len(set(c[category]))!=len(c[category]):
            raise ValueError(f'{category} 别名归一后出现重复名称')
    if c.get('event'):
        event=c['event']
        event['season']=season(event['season'])
        event['team']=c['aliases'].get('teams',{}).get(event['team'],event['team'])
        event['player']=c['aliases'].get('players',{}).get(event['player'],event['player'])
        if event['team'] not in c['teams'] or event['player'] not in c['players']:
            raise ValueError('event 的球队和球员必须出现在本次案例列表；更换案例时同时更新或删除event')
    c.setdefault('model', {})
    m = c['model']
    for k,v in {'clusters': 4, 'max_factors': 6, 'missing_threshold': .2, 'random_state': 42}.items():
        m.setdefault(k,v)
    if not isinstance(m['clusters'], int) or m['clusters'] < 2:
        raise ValueError('clusters 必须为至少 2 的整数')
    if not isinstance(m['max_factors'], int) or m['max_factors'] < 1:
        raise ValueError('max_factors 必须为正整数')
    if not 0 <= m['missing_threshold'] <= .5:
        raise ValueError('missing_threshold 必须在 0 至 0.5 之间')
    c.setdefault('source', {'mode': 'archive', 'root': '..'})
    s = c['source']
    if s.get('mode') not in {'archive', 'csv', 'html', 'online'}:
        raise ValueError('source.mode 必须为 archive/csv/html/online')
    if s['mode'] == 'archive' and c['league'] != 'premier-league':
        raise ValueError('仓库历史数据只属于英超；其他联赛请使用 csv/html/online 数据源')
    c['_config_dir'] = str(path.parent)
    c['_config_path'] = str(path)
    return c


def resolve(c, value):
    p = Path(value).expanduser()
    return p.resolve() if p.is_absolute() else (Path(c['_config_dir']) / p).resolve()


def public_config(c):
    result = deepcopy(c)
    for key in list(result):
        if key.startswith('_'):
            del result[key]
    return result
