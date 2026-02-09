#!/usr/bin/env python3
"""Scrape FBref Premier League tables into CSVs."""

import argparse
import os
import re
from typing import Dict, List, Tuple

import html as html_lib
import io

import pandas as pd
import requests
from bs4 import BeautifulSoup, Comment

try:
    import cloudscraper
except ImportError:  # pragma: no cover - optional dependency
    cloudscraper = None

URL_TEMPLATE = "https://fbref.com/en/comps/9/{season}/{season}-Premier-League-Stats"
DEFAULT_SEASON = "2016-2017"
DEFAULT_OUTPUT_DIR = os.path.join("data", "fbref_pl_2016_2017")


def _sanitize_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_") or "table"


def _extract_tables(html: str) -> List[Tuple[str, str]]:
    """Return list of (table_id_or_caption, table_html)."""
    soup = BeautifulSoup(html, "lxml")
    tables: List[Tuple[str, str]] = []

    def add_table(tag) -> None:
        table_id = tag.get("id") or ""
        caption = tag.find("caption")
        caption_text = caption.get_text(" ", strip=True) if caption else ""
        name = table_id or caption_text or "table"
        tables.append((name, str(tag)))

    for table in soup.find_all("table"):
        add_table(table)

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if "<table" not in comment:
            continue
        comment_soup = BeautifulSoup(comment, "lxml")
        for table in comment_soup.find_all("table"):
            add_table(table)

    return tables


def _table_to_dataframe(table_html: str) -> pd.DataFrame:
    dfs = pd.read_html(io.StringIO(table_html))
    if not dfs:
        raise ValueError("No table parsed")
    return dfs[0]


def _fetch_html(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    cookies = {}
    cf_clearance = os.getenv("CF_CLEARANCE", "").strip()
    if cf_clearance:
        cookies["cf_clearance"] = cf_clearance
    cf_bm = os.getenv("CF_BM", "").strip()
    if cf_bm:
        cookies["__cf_bm"] = cf_bm

    if cloudscraper is not None:
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(url, headers=headers, cookies=cookies, timeout=30)
    else:
        resp = requests.get(url, headers=headers, cookies=cookies, timeout=30)

    resp.raise_for_status()
    return resp.text


def _maybe_unwrap_view_source(html: str) -> str:
    """Convert browser view-source HTML to the original page HTML when needed."""
    if "line-content" not in html or "html-doctype" not in html:
        return html

    soup = BeautifulSoup(html, "lxml")
    lines = [cell.get_text() for cell in soup.select("td.line-content")]
    if not lines:
        return html

    reconstructed = "\n".join(html_lib.unescape(line) for line in lines)
    return reconstructed if "<html" in reconstructed else html


def _load_html_from_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    return _maybe_unwrap_view_source(raw)


def _resolve_url(season: str | None, url: str | None) -> str:
    if url:
        return url
    season_value = season or DEFAULT_SEASON
    return URL_TEMPLATE.format(season=season_value)


def _resolve_output_dir(output_dir: str | None, season: str | None) -> str:
    if output_dir:
        return output_dir
    season_value = season or DEFAULT_SEASON
    safe_season = season_value.replace("-", "_")
    return os.path.join("data", f"fbref_pl_{safe_season}")


def scrape(
    html_path: str | None = None,
    season: str | None = None,
    url: str | None = None,
    output_dir: str | None = None,
) -> Dict[str, str]:
    html = _load_html_from_file(html_path) if html_path else _fetch_html(_resolve_url(season, url))

    resolved_output_dir = _resolve_output_dir(output_dir, season)
    os.makedirs(resolved_output_dir, exist_ok=True)

    saved: Dict[str, str] = {}
    for name, table_html in _extract_tables(html):
        safe = _sanitize_name(name)
        out_path = os.path.join(resolved_output_dir, f"{safe}.csv")
        df = _table_to_dataframe(table_html)
        df.to_csv(out_path, index=False)
        saved[name] = out_path

    index_path = os.path.join(resolved_output_dir, "_index.txt")
    with open(index_path, "w", encoding="utf-8") as f:
        for name, path in sorted(saved.items()):
            f.write(f"{name}\t{path}\n")

    return saved


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape FBref tables into CSVs")
    parser.add_argument(
        "--html",
        dest="html_path",
        help="Path to a saved HTML file to parse instead of fetching from web",
    )
    parser.add_argument(
        "--season",
        default=DEFAULT_SEASON,
        help="Season identifier like 2016-2017 or 2017-2018",
    )
    parser.add_argument(
        "--url",
        help="Override FBref URL. If set, --season is ignored for fetching",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for CSVs (defaults to data/fbref_pl_<season>)",
    )
    args = parser.parse_args()

    saved = scrape(
        html_path=args.html_path,
        season=args.season,
        url=args.url,
        output_dir=args.output_dir,
    )
    resolved_output_dir = _resolve_output_dir(args.output_dir, args.season)
    print(f"Saved {len(saved)} tables to {resolved_output_dir}")


if __name__ == "__main__":
    main()
