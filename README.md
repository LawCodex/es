# LawCodex — España (Spain)

Spanish legislation as plain Markdown, one file per norm, generated from the official
consolidated texts (*Legislación consolidada*) of the **Boletín Oficial del Estado (BOE)**.

Part of [LawCodex](https://github.com/LawCodex): the legislation of every country as Markdown in git.

- Jurisdiction: Spain (`es`), language: Spanish (castellano)
- Source: BOE open-data API — <https://www.boe.es/datosabiertos/api/legislacion-consolidada>
- Retrieved: 2026-10-11
- Total: **8,064** norms (5,398 state-level, 2,666 autonomous-community)

## Coverage

Everything the BOE consolidated-legislation database marks as **in force** (`vigencia_agotada = N`),
in its latest consolidated version (all amendments applied, as published by the BOE).

### State legislation (ámbito estatal)

| Directory | Category | Files |
|---|---|---:|
| `constitucion/` | Constitución Española (1978) | 1 |
| `leyes-organicas/` | Leyes Orgánicas (incl. Estatutos de Autonomía, Código Penal) | 136 |
| `leyes/` | Leyes | 560 |
| `reales-decretos-legislativos/` | Reales Decretos Legislativos (textos refundidos) | 30 |
| `reales-decretos-leyes/` | Reales Decretos-leyes | 242 |
| `reales-decretos/` | Reales Decretos (incl. Código Civil, Código de Comercio) | 2,150 |
| `decretos/` | Decretos (pre-1978 / misc.) | 11 |
| `ordenes/` | Órdenes ministeriales | 1,398 |
| `resoluciones/` | Resoluciones | 519 |
| `circulares/` | Circulares (Banco de España, CNMV...) | 99 |
| `instrucciones/` | Instrucciones | 83 |
| `acuerdos/` | Acuerdos | 21 |
| `acuerdos-internacionales/` | Acuerdos internacionales (tratados) | 147 |
| `reglamentos/` | Reglamentos | 1 |
| | **Total state** | **5,398** |

### Autonomous-community legislation (ámbito autonómico)

The BOE also consolidates the *laws* of the autonomous communities (leyes, leyes forales,
decretos legislativos, decretos-leyes, plus a few resoluciones), i.e. the regional legislation
that is republished in the BOE. Identifiers of texts consolidated from a regional gazette use that
gazette's prefix (e.g. `DOGC-f-…`, `BOJA-b-…`).

| Directory | Community | Files | By rank |
|---|---|---:|---|
| `autonomicas/andalucia/` | Andalucía | 158 | decretos-legislativos 4, decretos-leyes 13, leyes 141 |
| `autonomicas/aragon/` | Aragón | 184 | decretos-legislativos 6, decretos-leyes 2, leyes 176 |
| `autonomicas/asturias/` | Principado de Asturias | 88 | decretos-legislativos 5, leyes 83 |
| `autonomicas/canarias/` | Canarias | 147 | decretos-legislativos 3, decretos-leyes 10, leyes 134 |
| `autonomicas/cantabria/` | Cantabria | 119 | decretos-legislativos 1, leyes 118 |
| `autonomicas/castilla-la-mancha/` | Castilla-La Mancha | 130 | decretos-legislativos 2, leyes 128 |
| `autonomicas/castilla-y-leon/` | Castilla y León | 147 | decretos-leyes 3, leyes 144 |
| `autonomicas/cataluna/` | Cataluña | 284 | decretos-legislativos 15, decretos-leyes 55, leyes 213, resoluciones 1 |
| `autonomicas/comunitat-valenciana/` | Comunitat Valenciana | 191 | decretos-legislativos 4, decretos-leyes 12, leyes 175 |
| `autonomicas/extremadura/` | Extremadura | 149 | decretos-legislativos 1, decretos-leyes 22, leyes 126 |
| `autonomicas/galicia/` | Galicia | 161 | decretos-legislativos 4, leyes 157 |
| `autonomicas/illes-balears/` | Illes Balears | 198 | decretos-legislativos 5, decretos-leyes 22, leyes 171 |
| `autonomicas/la-rioja/` | La Rioja | 108 | leyes 108 |
| `autonomicas/madrid/` | Comunidad de Madrid | 133 | decretos-legislativos 2, leyes 131 |
| `autonomicas/murcia/` | Región de Murcia | 115 | decretos-legislativos 2, decretos-leyes 3, leyes 110 |
| `autonomicas/navarra/` | Comunidad Foral de Navarra | 183 | decretos-forales-legislativos 8, decretos-leyes-forales 14, leyes-forales 160, resoluciones 1 |
| `autonomicas/pais-vasco/` | País Vasco | 171 | decretos-legislativos 12, leyes 158, resoluciones 1 |
| | **Total autonomous** | **2,666** | |

### Codes

Spain has no single "codes" collection in the consolidated database: the classic codes are
ordinary norms of various ranks (e.g. the *Código Civil* is a Real Decreto of 1889, the
*Código Penal* is Ley Orgánica 10/1995). They are stored under their rank and tagged
`type: code` in the front matter:

- [Ley Orgánica 10/1995, de 23 de noviembre, del Código Penal](leyes-organicas/1995/boe-a-1995-25444-ley-organica-10-1995-de-23-de-noviembre-del-codigo-penal.md)
- [Ley Orgánica 14/2015, de 14 de octubre, del Código Penal Militar](leyes-organicas/2015/boe-a-2015-11070-ley-organica-14-2015-de-14-de-octubre-del-codigo-penal-militar.md)
- [Real Decreto 314/2006, de 17 de marzo, por el que se aprueba el Código Técnico de la Edificación](reales-decretos/2006/boe-a-2006-5515-real-decreto-314-2006-de-17-de-marzo-por-el-que-se-aprueba-el-codigo-tecnico-de-la.md)
- [Real Decreto de 24 de julio de 1889 por el que se publica el Código Civil](reales-decretos/1889/boe-a-1889-4763-real-decreto-de-24-de-julio-de-1889-por-el-que-se-publica-el-codigo-civil.md)

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
retrieved: 2026-10-11
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
