#!/usr/bin/env python3
"""Regenerate README.md with per-category counts from the Markdown tree."""
import collections
import os
import re
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))

STATE_DIRS = [
    ("constitucion", "Constitución Española (1978)"),
    ("leyes-organicas", "Leyes Orgánicas (incl. Estatutos de Autonomía, Código Penal)"),
    ("leyes", "Leyes"),
    ("reales-decretos-legislativos", "Reales Decretos Legislativos (textos refundidos)"),
    ("reales-decretos-leyes", "Reales Decretos-leyes"),
    ("reales-decretos", "Reales Decretos (incl. Código Civil, Código de Comercio)"),
    ("decretos", "Decretos (pre-1978 / misc.)"),
    ("decretos-leyes", "Decretos-leyes (pre-1978)"),
    ("ordenes", "Órdenes ministeriales"),
    ("resoluciones", "Resoluciones"),
    ("circulares", "Circulares (Banco de España, CNMV...)"),
    ("instrucciones", "Instrucciones"),
    ("acuerdos", "Acuerdos"),
    ("acuerdos-internacionales", "Acuerdos internacionales (tratados)"),
    ("reglamentos", "Reglamentos"),
]

COMMUNITY_NAMES = {
    "andalucia": "Andalucía", "aragon": "Aragón", "asturias": "Principado de Asturias",
    "illes-balears": "Illes Balears", "canarias": "Canarias", "cantabria": "Cantabria",
    "castilla-la-mancha": "Castilla-La Mancha", "castilla-y-leon": "Castilla y León",
    "cataluna": "Cataluña", "comunitat-valenciana": "Comunitat Valenciana",
    "extremadura": "Extremadura", "galicia": "Galicia", "la-rioja": "La Rioja",
    "madrid": "Comunidad de Madrid", "murcia": "Región de Murcia",
    "navarra": "Comunidad Foral de Navarra", "pais-vasco": "País Vasco",
    "ceuta": "Ceuta", "melilla": "Melilla",
}


def count_md(path):
    n = 0
    for _, _, files in os.walk(path):
        n += sum(1 for f in files if f.endswith(".md"))
    return n


def main():
    retrieved = None
    repealed = 0
    codes = []
    for root, _, files in os.walk(REPO):
        if "/.git" in root or root.endswith("/scripts"):
            continue
        for f in files:
            if not f.endswith(".md") or root == REPO:
                continue
            with open(os.path.join(root, f), encoding="utf-8") as fh:
                head = fh.read(2500)
            m = re.search(r"^retrieved: (\S+)", head, re.M)
            if re.search(r"^status: repealed$", head, re.M):
                repealed += 1
            if m and not retrieved:
                retrieved = m.group(1)
            if re.search(r"^type: code$", head, re.M) and "/autonomicas/" not in root:
                t = re.search(r'^title: "(.*)"$', head, re.M).group(1)
                codes.append((t, os.path.relpath(os.path.join(root, f), REPO)))
    retrieved = retrieved or date.today().isoformat()

    state_rows = []
    total_state = 0
    for d, label in STATE_DIRS:
        p = os.path.join(REPO, d)
        if os.path.isdir(p):
            n = count_md(p)
            total_state += n
            state_rows.append(f"| `{d}/` | {label} | {n:,} |")

    auto_rows = []
    total_auto = 0
    auto_root = os.path.join(REPO, "autonomicas")
    rank_totals = collections.Counter()
    if os.path.isdir(auto_root):
        for c in sorted(os.listdir(auto_root)):
            cp = os.path.join(auto_root, c)
            if not os.path.isdir(cp):
                continue
            parts = []
            n_c = 0
            for r in sorted(os.listdir(cp)):
                rp = os.path.join(cp, r)
                if os.path.isdir(rp):
                    n = count_md(rp)
                    n_c += n
                    rank_totals[r] += n
                    parts.append(f"{r} {n}")
            total_auto += n_c
            auto_rows.append(f"| `autonomicas/{c}/` | {COMMUNITY_NAMES.get(c, c)} | {n_c:,} | {', '.join(parts)} |")

    codes.sort()
    code_lines = "\n".join(f"- [{t}]({p})" for t, p in codes)

    readme = f"""# LawCodex — España (Spain)

Spanish legislation as plain Markdown, one file per norm, generated from the official
consolidated texts (*Legislación consolidada*) of the **Boletín Oficial del Estado (BOE)**.

Part of [LawCodex](https://github.com/LawCodex): the legislation of every country as Markdown in git.

- Jurisdiction: Spain (`es`), language: Spanish (castellano)
- Source: BOE open-data API — <https://www.boe.es/datosabiertos/api/legislacion-consolidada>
- Retrieved: {retrieved}
- Total: **{total_state + total_auto:,}** norms ({total_state:,} state-level, {total_auto:,} autonomous-community)

## Coverage

Everything the BOE consolidated-legislation database marks as **in force** (`vigencia_agotada = N`),
in its latest consolidated version (all amendments applied, as published by the BOE).
A small number of these ({repealed:,}) carry a BOE note saying the norm has just been repealed or
annulled (the catalogue flag lags behind); they are kept with `status: repealed`.

### State legislation (ámbito estatal)

| Directory | Category | Files |
|---|---|---:|
{chr(10).join(state_rows)}
| | **Total state** | **{total_state:,}** |

### Autonomous-community legislation (ámbito autonómico)

The BOE also consolidates the *laws* of the autonomous communities (leyes, leyes forales,
decretos legislativos, decretos-leyes, plus a few resoluciones), i.e. the regional legislation
that is republished in the BOE. Identifiers of texts consolidated from a regional gazette use that
gazette's prefix (e.g. `DOGC-f-…`, `BOJA-b-…`).

| Directory | Community | Files | By rank |
|---|---|---:|---|
{chr(10).join(auto_rows)}
| | **Total autonomous** | **{total_auto:,}** | |

### Codes

Spain has no single "codes" collection in the consolidated database: the classic codes are
ordinary norms of various ranks (e.g. the *Código Civil* is a Real Decreto of 1889, the
*Código Penal* is Ley Orgánica 10/1995). They are stored under their rank and tagged
`type: code` in the front matter:

{code_lines}

## Not covered

- **Repealed / expired norms** (`vigencia_agotada = S` in the BOE catalogue, ~2,400 norms):
  skipped. Run `scripts/fetch.py --all` to include them (they get `status: repealed`).
- **Historical versions**: only the current consolidated wording of each provision is kept; the BOE
  XML contains every past version (`<version>` elements) but these are not reproduced. Provisions
  whose validity has lapsed (`fecha_caducidad`) are omitted, as on boe.es.
- **Non-consolidated texts**: the BOE consolidates a selection of norms (all state laws and
  most important regulations, but not every Real Decreto, Orden or Resolución ever published
  in the BOE). Non-consolidated dispositions (BOE *Sección I* daily texts) are not included.
- **Autonomous-community regulations** (decretos, órdenes of the regional governments) and
  laws only published in regional gazettes are not in the BOE consolidated database.
- **Co-official languages** (català, galego, euskara): the BOE consolidated texts are in Spanish only.
- **Images and complex tables**: images (formulas, forms, maps) are linked to `boe.es`, not copied;
  tables with merged cells are kept as HTML.
- **BOE "Códigos electrónicos"** (thematic compilations of the Biblioteca Jurídica Digital, distributed
  under CC BY-NC-ND): not reproduced; their component norms are included individually from the
  consolidated-legislation database.

## Structure

```
constitucion/                       Constitución Española
leyes-organicas/<year>/             Leyes Orgánicas
leyes/<year>/                       Leyes
reales-decretos-legislativos/<year>/
reales-decretos-leyes/<year>/
reales-decretos/<year>/
ordenes/<year>/  resoluciones/<year>/  circulares/<year>/  instrucciones/<year>/ ...
acuerdos-internacionales/<year>/
autonomicas/<community>/<rank>/<year>/
```

`<year>` is the year of the disposition (`fecha_disposicion`). File names are
`<boe-identifier>-<slug-of-title>.md` (lowercase ASCII, ≤ 100 chars), e.g.
`leyes-organicas/1995/boe-a-1995-25444-ley-organica-10-1995-de-23-de-noviembre-del-codigo-penal.md`.

Each file has YAML front matter:

```yaml
title: "Ley Orgánica 10/1995, de 23 de noviembre, del Código Penal"
identifier: "BOE-A-1995-25444"      # BOE identifier
eli: "https://www.boe.es/eli/es/lo/1995/11/23/10"
type: code                          # constitution | organic_law | act | legislative_decree | decree_law | decree | order | resolution | circular | instruction | agreement | treaty | regulation | code
rank: "Ley Orgánica"                # BOE rango
jurisdiction: es                    # es-<community> for autonomous legislation
language: es
department: "Jefatura del Estado"
date: 1995-11-23                    # fecha_disposicion
published: 1995-11-24               # BOE publication
in_force_from: 1996-05-24
last_amended: 2025-...              # publication date of the latest amending norm applied
consolidated: 2026-...              # last update of the consolidated text by the BOE
gazette: "Boletín Oficial del Estado núm. 281"
status: in_force
source: "https://www.boe.es/buscar/act.php?id=BOE-A-1995-25444"
retrieved: {retrieved}
```

The body maps the BOE structure to headings: Libro / Título / Capítulo / Sección / Subsección
become `##`…`######` (only the levels actually used by a norm are allocated), articles and
dispositions (*disposiciones adicionales, transitorias, derogatorias, finales*) are the deepest
heading level; when a norm uses so many levels that articles would go past `######`, article
labels are rendered in **bold**. Anexos are `##` headings. The BOE's editorial notes on
amendments ("Se modifica por…", with a link to the amending norm) are kept as `>` blockquotes.

## Licence

The texts come from the Agencia Estatal Boletín Oficial del Estado. Legislative and regulatory
texts are excluded from copyright under Spanish law (art. 13 of the *Ley de Propiedad Intelectual*,
Real Decreto Legislativo 1/1996). The BOE's documents and open data may be reused for commercial
and non-commercial purposes under the BOE
[conditions of reuse](https://www.boe.es/informacion/aviso_legal/index.php#reutilizacion)
(licence approved by BOE Resolution of 27 June 2024, under Ley 37/2007 on the reuse of public-sector
information): cite the source (Agencia Estatal Boletín Oficial del Estado, <https://www.boe.es>),
do not alter the content or its meaning, and state the date of the last update (`consolidated` /
`retrieved` in each file's front matter).
This repository is **not** an official publication; only the BOE texts have legal value.

## Regenerating

```sh
pip install -r scripts/requirements.txt
python scripts/fetch.py      # catalogue + XML texts -> ../_raw/es (cached, incremental)
python scripts/convert.py    # XML -> Markdown in this repo (scripts/manifest.json tracks paths)
python scripts/readme.py     # refresh the counts in this README
```

`fetch.py` options: `--all` (include repealed norms), `--workers N` (≤ 4), `--raw DIR`.
"""
    with open(os.path.join(REPO, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(readme)


if __name__ == "__main__":
    main()
