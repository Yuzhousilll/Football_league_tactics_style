import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from tactical.config import load_config, STYLE, ACTION, season
from tactical.data import validate_frame, validate_coverage, archive, parse_tables, team_metrics, html_source
from tactical.analysis import style_model, points_model
from football_report import run


class Reports(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.base=Path(self.temp.name)
        self.c=load_config(ROOT/'configs/premier-league.json')

    def config(self,**changes):
        c=json.loads((ROOT/'configs/premier-league.json').read_text());c.update(changes)
        if 'teams' in changes or 'players' in changes:
            c.pop('event',None)
        c['source']={'mode':'archive','root':str(ROOT)} if 'source' not in changes else changes['source']
        p=self.base/'config.json';p.write_text(json.dumps(c)); return p

    def test_invalid_season_and_reversed_range(self):
        for s in ['2022-2025','2023','2023-23']:
            with self.assertRaises(ValueError): season(s)
        with self.assertRaises(ValueError): load_config(self.config(season_start='2024-2025',season_end='2022-2023'))

    def test_other_league_cannot_relabel_archive(self):
        with self.assertRaisesRegex(ValueError,'只属于英超'): load_config(self.config(league='la-liga'))

    def test_alias_is_applied_to_request_and_data(self):
        c=load_config(self.config(teams=['Manchester United']))
        self.assertEqual(c['teams'],['Manchester Utd'])

    def test_normalized_duplicate_and_nonfinite_rejected(self):
        base=pd.DataFrame({'league':['premier-league']*2,'Season':['2022_2023','2022-2023'],'Squad':['A','A'],'points':[1,2]})
        with self.assertRaisesRegex(ValueError,'重复'): validate_frame(base,self.c)
        base['points']=base.points.astype(float)
        base.loc[1,'Squad']='B';base.loc[0,'points']=np.inf
        with self.assertRaisesRegex(ValueError,'无穷'): validate_frame(base,self.c)

    def test_missing_season_or_unknown_player_rejected(self):
        t,p,_,_=archive(self.c);t=validate_frame(t,self.c);p=validate_frame(p,self.c,True)
        with self.assertRaisesRegex(ValueError,'缺少完整赛季'): validate_coverage(t[t.Season!='2022-2023'],p,self.c)
        c={**self.c,'players':['Nonexistent Player']}
        with self.assertRaisesRegex(ValueError,'找不到'): validate_coverage(t,p,c)

    def test_archive_real_points_and_leaderboard_missingness(self):
        t,p,_,_=archive(self.c)
        self.assertEqual(len(t),180)
        city=t[(t.Squad=='Manchester City')&(t.Season=='2022-2023')].iloc[0]
        self.assertEqual(city.points,89);self.assertEqual(city.MP,38)
        h=p[(p.Player=='Erling Haaland')&(p.Season=='2022-2023')].iloc[0]
        self.assertEqual(h.Goals,36); self.assertEqual(h.data_scope,'leaderboard_only')
        self.assertTrue(p.Goals.isna().any())

    def test_comment_and_view_source_html(self):
        html='<!--<table id="stats_standard"><tbody><tr><th data-stat="player">A</th><td data-stat="goals">7</td></tr></tbody></table>-->'
        self.assertEqual(parse_tables(html)['stats_standard'].iloc[0]['goals'],'7')
        wrapped='<td class="line-content">'+html.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')+'</td>'
        self.assertEqual(parse_tables(wrapped)['stats_standard'].iloc[0]['player'],'A')

    def test_actual_match_denominator_and_zero(self):
        tables={'results2023_overall':pd.DataFrame({'team':['A','B'],'games':['34','0'],'goals_for':['68','0'],'goals_against':['34','0'],'points':['75','0']})}
        t=team_metrics(tables)
        self.assertEqual(t.iloc[0].goals_per_match,2)
        self.assertTrue(pd.isna(t.iloc[1].goals_per_match))

    def test_blocked_site_stops_without_retry(self):
        c={**self.c,'source':{'mode':'online'}}
        for status in [403,429]:
            with patch('tactical.data.requests.get',return_value=Mock(status_code=status)) as get:
                with self.assertRaisesRegex(ValueError,str(status)): html_source(c,self.base)
                self.assertEqual(get.call_count,1)

    def test_low_sample_missing_constant_models_skip(self):
        t,_,_,_=archive(self.c)
        m,_=style_model(t.head(20),self.c,self.base);self.assertEqual(m['status'],'unavailable')
        t.loc[:,'goals_per_match']=0
        m,_=style_model(t,self.c,self.base);self.assertEqual(m['status'],'unavailable')
        self.assertEqual(points_model(t.drop(columns='points'),self.c,self.base)['status'],'unavailable')

    def test_portable_real_baseline_and_existing_output_preserved(self):
        output=self.base/'report';result=run(self.config(),output)
        self.assertEqual(result['team_rows'],180);self.assertEqual(result['player_case_rows'],3)
        analysis=json.loads((output/'analysis.json').read_text())
        self.assertEqual(analysis['style']['factors'],3)
        self.assertAlmostEqual(analysis['action']['explained_total'],.7526,places=3)
        p=pd.read_csv(output/'player_cases.csv');self.assertEqual(p.Goals.tolist(),[36,27,22])
        peers=pd.read_csv(output/'player_peer_comparison.csv')
        goals=peers[peers.metric=='Goals'].sort_values('Season')
        self.assertEqual(goals.peer_mean.round(1).tolist(),[17.7,18.3,18.5])
        self.assertTrue((peers.peer_top_n<=10).all())
        scores=pd.read_csv(output/'action_scores.csv')
        for _,rows in scores.groupby('Season'): self.assertEqual(rows.index_rank.min(),1)
        before=(output/'report.html').read_bytes()
        with self.assertRaisesRegex(ValueError,'已存在'):run(self.config(),output)
        self.assertEqual(before,(output/'report.html').read_bytes())

    def test_failed_run_leaves_no_report(self):
        with self.assertRaises(ValueError):run(self.config(players=['unknown']),self.base/'bad')
        self.assertFalse((self.base/'bad').exists());self.assertFalse(list(self.base.glob('.football-report-*')))

    def test_other_league_synthetic_pipeline(self):
        rng=np.random.default_rng(31);rows=[]
        for s in ['2022-2023','2023-2024','2024-2025']:
            for i in range(20):
                row={'league':'la-liga','Season':s,'Squad':f'Test team {i}'}
                row.update({x:float(rng.uniform(.1,.9)) for x in set(STYLE+ACTION)})
                rows.append(row)
        path=self.base/'synthetic-teams.csv';pd.DataFrame(rows).to_csv(path,index=False)
        c=self.config(league='la-liga',season_start='2022-2023',season_end='2024-2025',teams=['Test team 1'],players=[],source={'mode':'csv','teams_csv':'synthetic-teams.csv'})
        output=self.base/'synthetic-report';result=run(c,output)
        self.assertEqual(result['team_rows'],60)
        html=(output/'report.html').read_text()
        self.assertIn('西甲',html);self.assertNotIn('Erling Haaland',html)
        self.assertEqual(set(pd.read_csv(output/'teams.csv').league),{'la-liga'})

    def test_event_comparison_real_data_and_missing_preperiod(self):
        from tactical.analysis import event_comparison
        t,_,_,_=archive(self.c)
        event=event_comparison(t,self.c,self.base)
        self.assertEqual(event['status'],'ok')
        values=pd.read_csv(self.base/'event_comparison.csv').change_pct.round(1).tolist()
        self.assertEqual(values,[-6.1,-4.6,-7.3,-10.6])
        short=t[t.Season>='2022-2023']
        self.assertEqual(event_comparison(short,self.c,self.base)['status'],'unavailable')

    def test_case_selection_does_not_change_league_model(self):
        from tactical.analysis import action_model
        t,_,_,_=archive(self.c)
        meta,a=action_model(t,self.c,self.base)
        c={**self.c,'teams':['Arsenal'],'players':['Bukayo Saka']}
        meta2,b=action_model(t,c,self.base)
        np.testing.assert_array_equal(a.action_index,b.action_index)


if __name__=='__main__':unittest.main()
