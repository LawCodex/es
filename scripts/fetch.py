#!/usr/bin/env python3
"""Download the BOE "Legislación consolidada" catalogue and full texts (XML).

Usage: python scripts/fetch.py [--raw DIR] [--all] [--workers N]

- Lists every consolidated norm via the BOE open-data API
  (https://www.boe.es/datosabiertos/api/legislacion-consolidada), paginated.
- Downloads the consolidated text (XML, /id/<ID>/texto) of each norm to RAW/xml/<ID>.xml
  (metadata come from the catalogue, RAW/catalogue.json).
  Already downloaded files are re-fetched only when the catalogue's
  `fecha_actualizacion` is newer than the cached copy.
- By default only norms that are in force (vigencia_agotada == "N") are fetched;
  pass --all to fetch repealed / expired norms as well.
"""
import argparse
import concurrent.futures as cf
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

API = "https://www.boe.es/datosabiertos/api/legislacion-consolidada"
UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
DEFAULT_RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_raw", "es")

session = requests.Session()
session.headers["User-Agent"] = UA


def get(url, accept, params=None, timeout=300):
    delay = 5
    for attempt in range(8):
        try:
            r = session.get(url, headers={"Accept": accept}, params=params, timeout=timeout)
            if r.status_code == 200:
                return r
            if r.status_code == 404:
                return None
            print(f"HTTP {r.status_code} for {url}", file=sys.stderr)
        except requests.RequestException as e:
            print(f"error {e} for {url}", file=sys.stderr)
        time.sleep(delay)
        delay = min(delay * 2, 300)
    raise RuntimeError(f"giving up on {url}")


def fetch_catalogue(raw, page=2000):
    items = []
    offset = 0
    while True:
        r = get(API, "application/json", params={"offset": offset, "limit": page})
        data = r.json().get("data") or []
        items.extend(data)
        print(f"catalogue: {len(items)}", file=sys.stderr)
        if len(data) < page:
            break
        offset += page
        time.sleep(1)
    seen = {}
    for it in items:
        seen[it["identificador"]] = it
    items = list(seen.values())
    with open(os.path.join(raw, "catalogue.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False)
    return items


def upd_ts(item):
    s = item.get("fecha_actualizacion") or ""
    try:
        return datetime.strptime(s, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return 0


def fetch_one(raw, item):
    ident = item["identificador"]
    path = os.path.join(raw, "xml", ident + ".xml")
    if os.path.exists(path) and os.path.getsize(path) > 0 and os.path.getmtime(path) >= upd_ts(item):
        return ident, "cached"
    r = get(f"{API}/id/{ident}/texto", "application/xml")
    if r is None:
        return ident, "missing"
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(r.content)
    os.replace(tmp, path)
    time.sleep(0.2)
    return ident, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=DEFAULT_RAW)
    ap.add_argument("--all", action="store_true", help="also fetch repealed/expired norms")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--skip-catalogue", action="store_true", help="reuse RAW/catalogue.json")
    args = ap.parse_args()
    raw = os.path.abspath(args.raw)
    os.makedirs(os.path.join(raw, "xml"), exist_ok=True)
    cat_path = os.path.join(raw, "catalogue.json")
    if args.skip_catalogue and os.path.exists(cat_path):
        items = json.load(open(cat_path, encoding="utf-8"))
    else:
        items = fetch_catalogue(raw)
    if not args.all:
        items = [i for i in items if i.get("vigencia_agotada") != "S"]
    print(f"{len(items)} norms to fetch", file=sys.stderr)
    stats = {}
    workers = min(args.workers, 4)
    with cf.ThreadPoolExecutor(workers) as ex:
        futs = [ex.submit(fetch_one, raw, it) for it in items]
        for n, fut in enumerate(cf.as_completed(futs), 1):
            ident, st = fut.result()
            stats[st] = stats.get(st, 0) + 1
            if st == "missing":
                print(f"missing: {ident}", file=sys.stderr)
            if n % 250 == 0:
                print(f"{n}/{len(items)} {stats}", file=sys.stderr)
    print(f"done {stats}", file=sys.stderr)


if __name__ == "__main__":
    main()
