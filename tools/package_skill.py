#!/usr/bin/env python3
"""Package only the portable runtime and archived research CSVs."""
import argparse
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
FILES=['SKILL.md','requirements.txt','agents/openai.yaml','configs/premier-league.json','configs/custom-league.json',
       'scripts/football_report.py','scripts/import_thesis.py','style_metrics_all.csv','all_stats.csv','all_top_stats.csv']


def package(output):
    output=Path(output).resolve(); target=output/'football-tactical-report'
    if target.exists() or (output/'football-tactical-report.zip').exists():
        raise ValueError('打包目标已存在，请选择新目录')
    paths=FILES+[str(p.relative_to(ROOT)) for p in (ROOT/'references').glob('*') if p.is_file()]
    paths += [str(p.relative_to(ROOT)) for p in (ROOT/'scripts'/'tactical').glob('*.py')]
    for relative in paths:
        dest=target/relative; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/relative,dest)
    zip_path=shutil.make_archive(str(output/'football-tactical-report'),'zip',output,'football-tactical-report')
    return target,zip_path


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output',required=True); args=parser.parse_args()
    target,zipped=package(args.output); print(f'{target}\n{zipped}')
