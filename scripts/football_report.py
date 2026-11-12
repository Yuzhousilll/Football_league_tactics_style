#!/usr/bin/env python3
"""Run the reusable football report from any working directory."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'football-report-matplotlib'))
from tactical.config import load_config, public_config
from tactical.data import load_data
from tactical.analysis import style_model, action_model, points_model, player_cases, event_comparison
from tactical.report import build_report

ROOT=Path(__file__).resolve().parents[1]


def write_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def run(config, output):
    c=load_config(config)
    target=Path(output).expanduser().resolve()
    if target.exists():
        raise ValueError(f'输出目录已存在，请使用新目录以保留历史报告：{target}')
    target.parent.mkdir(parents=True,exist_ok=True)
    working=Path(tempfile.mkdtemp(prefix='.football-report-',dir=target.parent))
    try:
        teams,players,provenance,notes=load_data(c,working)
        for record in provenance:
            source_path=Path(record['path'])
            if source_path.is_relative_to(working):
                record['path']=str(target/source_path.relative_to(working))
        teams.to_csv(working/'teams.csv',index=False,encoding='utf-8-sig')
        players.to_csv(working/'players.csv',index=False,encoding='utf-8-sig')
        summary={}
        summary['style'],styles=style_model(teams,c,working)
        summary['action'],actions=action_model(teams,c,working)
        summary['players'],cases=player_cases(players,teams,c,working)
        summary['event']=event_comparison(teams,c,working)
        summary['points']=points_model(teams,c,working) if c['model'].get('points_extension',False) else {'status':'not_requested','reason':'论文正式分析不包含随机森林；需要时可开启扩展'}
        thesis_path=ROOT/'references'/'thesis-profile.json'
        thesis=json.loads(thesis_path.read_text(encoding='utf-8')) if thesis_path.exists() else {}
        build_report(c,teams,styles,actions,cases,summary,provenance,notes,thesis,working)
        write_json(working/'analysis.json',summary)
        write_json(working/'config.resolved.json',public_config(c))
        manifest={'project':'英超多赛季数据采集与战术分析','created_at':datetime.now(timezone.utc).isoformat(),
          'source_repository':'https://github.com/Yuzhousilll/graduation_thesis',
          'versions':{p:importlib.metadata.version(p) for p in ['pandas','numpy','scipy','scikit-learn','matplotlib']},
          'inputs':provenance,'thesis':thesis,'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in working.iterdir() if p.is_file()},
          'figures':{str(p.relative_to(working)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (working/'figures').iterdir()}}
        write_json(working/'manifest.json',manifest)
        working.rename(target)
    except BaseException:
        shutil.rmtree(working)
        raise
    return {'output':str(target),'team_rows':len(teams),'player_case_rows':len(cases),'models':{k:v['status'] for k,v in summary.items()}}


def main():
    parser=argparse.ArgumentParser(description='英超多赛季数据采集与战术分析（支持切换联赛）')
    parser.add_argument('--config',required=True,help='JSON 参数文件；相对数据路径相对于该配置文件')
    parser.add_argument('--output',required=True,help='新的报告输出目录，不覆盖已有报告')
    args=parser.parse_args()
    try:
        print(json.dumps(run(args.config,args.output),ensure_ascii=False,indent=2))
    except (ValueError,KeyError,OSError) as exc:
        print(f'报告未生成：{exc}',file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
