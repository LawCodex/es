#!/usr/bin/env python3
"""Convert BOE consolidated-legislation XML (downloaded by fetch.py) to Markdown.

Usage: python scripts/convert.py [--raw DIR] [--out DIR] [--ids ID ...]

Writes one Markdown file per norm into the repository tree and a
scripts/manifest.json (identifier -> path) used to remove stale files on re-runs.
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import date

from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
DEFAULT_RAW = os.path.abspath(os.path.join(REPO, "..", "_raw", "es"))
TODAY = date.today()

# rango -> (directory, type)
RANGOS = {
    "Constitución": ("constitucion", "constitution"),
    "Ley Orgánica": ("leyes-organicas", "organic_law"),
    "Ley": ("leyes", "act"),
    "Ley Foral": ("leyes-forales", "act"),
    "Real Decreto Legislativo": ("reales-decretos-legislativos", "legislative_decree"),
    "Decreto Legislativo": ("decretos-legislativos", "legislative_decree"),
    "Decreto Foral Legislativo": ("decretos-forales-legislativos", "legislative_decree"),
    "Real Decreto-ley": ("reales-decretos-leyes", "decree_law"),
    "Decreto-ley": ("decretos-leyes", "decree_law"),
    "Decreto-ley Foral": ("decretos-leyes-forales", "decree_law"),
    "Real Decreto": ("reales-decretos", "decree"),
    "Decreto": ("decretos", "decree"),
    "Orden": ("ordenes", "order"),
    "Resolución": ("resoluciones", "resolution"),
    "Circular": ("circulares", "circular"),
    "Instrucción": ("instrucciones", "instruction"),
    "Acuerdo": ("acuerdos", "agreement"),
    "Acuerdo Internacional": ("acuerdos-internacionales", "treaty"),
    "Reglamento": ("reglamentos", "regulation"),
}

COMMUNITIES = [
    ("andaluc", "andalucia"),
    ("arag", "aragon"),
    ("asturias", "asturias"),
    ("balears", "illes-balears"),
    ("baleares", "illes-balears"),
    ("canarias", "canarias"),
    ("cantabria", "cantabria"),
    ("castilla-la mancha", "castilla-la-mancha"),
    ("castilla y le", "castilla-y-leon"),
    ("catalu", "cataluna"),
    ("valencia", "comunitat-valenciana"),
    ("extremadura", "extremadura"),
    ("galicia", "galicia"),
    ("rioja", "la-rioja"),
    ("madrid", "madrid"),
    ("murcia", "murcia"),
    ("navarra", "navarra"),
    ("vasco", "pais-vasco"),
    ("ceuta", "ceuta"),
    ("melilla", "melilla"),
]

# heading p-class prefixes, in hierarchical order
HEAD_RANKS = ["parte", "libro", "titulo", "capitulo", "seccion", "subseccion"]
CODE_RE = re.compile(
    r"^(C[óo]digo\b"
    r"|[^,]+, de \d+ de \w+(?: de \d{4})?, (?:del|de) C[óo]digo\b"
    r"|.{0,120}\bpor (?:el|la) que se (?:aprueba|publica|promulga)n? (?:el )?(?:texto (?:refundido|articulado) del? )?C[óo]digo\b)(?! de [Cc]onducta| de [Bb]uen)",
    re.I)


def slugify(s, maxlen=100):
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > maxlen:
        s = s[:maxlen].rsplit("-", 1)[0]
    return s


def community_slug(dep):
    d = (dep or "").lower()
    for key, slug in COMMUNITIES:
        if key in d:
            return slug
    return slugify(dep or "desconocida")


def fmt_date(s):
    if s and re.fullmatch(r"\d{8}", s):
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return None


def yaml_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def norm_ws(s):
    return re.sub(r"\s+", " ", s or "").strip()


def md_escape_line(s):
    # avoid accidental Markdown block constructs at line start
    if re.match(r"^(#{1,6}\s|>|[-+*]\s|\d+\.\s|={3,}|-{3,}|\|)", s):
        if re.match(r"^\d+\.\s", s):
            return re.sub(r"^(\d+)\.", r"\1\\.", s, count=1)
        return "\\" + s
    return s


# ---------------------------------------------------------------- inline

def inline(el, base_url):
    """Render inline content of an element to Markdown text."""
    out = []
    if el.text:
        out.append(el.text)
    for ch in el:
        tag = ch.tag if isinstance(ch.tag, str) else ""
        inner = inline(ch, base_url) if tag else ""
        if tag in ("strong", "b"):
            t = inner.strip()
            out.append(f"**{t}**" if t else "")
        elif tag in ("em", "i"):
            t = inner.strip()
            out.append(f"*{t}*" if t else "")
        elif tag == "sup":
            out.append(f"<sup>{inner}</sup>" if inner.strip() else "")
        elif tag == "sub":
            out.append(f"<sub>{inner}</sub>" if inner.strip() else "")
        elif tag == "br":
            out.append("<br>")
        elif tag == "img":
            src = ch.get("src") or ""
            if src and not src.startswith("http"):
                src = "https://www.boe.es" + (src if src.startswith("/") else "/" + src)
            alt = norm_ws(ch.get("alt") or "imagen")
            out.append(f"![{alt}]({src})")
        elif tag == "a":
            href = ch.get("href") or ""
            t = inner
            mref = re.match(r"\s*Ref\.\s*([A-Z]{3,4}-[A-Za-z]-\d{4}-\d+)(#\S*)?\s*$", t)
            if (ch.get("class") or "") == "refPost" and mref:
                out.append(f"[Ref. {mref.group(1)}](https://www.boe.es/buscar/doc.php?id={mref.group(1)})")
                if ch.tail:
                    out.append(ch.tail)
                continue
            if href and href.startswith("http") and t.strip():
                out.append(f"[{t.strip()}]({href})")
            else:
                out.append(t)
        else:  # span, ins, del, u, etc.
            out.append(inner)
        if ch.tail:
            out.append(ch.tail)
    return "".join(out)


def text_of(el, base_url):
    return norm_ws(inline(el, base_url).replace("\n", " "))


# ---------------------------------------------------------------- tables

def table_to_md(tbl, base_url):
    rows = tbl.xpath(".//tr")
    simple = bool(rows)
    for c in tbl.xpath(".//td|.//th"):
        if (c.get("rowspan") not in (None, "1")) or (c.get("colspan") not in (None, "1")):
            simple = False
            break
        if c.xpath(".//table|.//ul|.//ol"):
            simple = False
            break
    grid = []
    if simple:
        for r in rows:
            cells = []
            for c in r.xpath("./td|./th"):
                parts = [text_of(p, base_url) for p in c.xpath("./p")] or [text_of(c, base_url)]
                t = "<br>".join(x for x in parts if x) if c.xpath("./p") else text_of(c, base_url)
                cells.append(t.replace("|", "\\|"))
            grid.append(cells)
        width = max((len(r) for r in grid), default=0)
        if width == 0 or any(len(r) != width for r in grid):
            simple = False
    if not simple:
        import copy
        t2 = copy.deepcopy(tbl)
        t2.tail = None
        for cg in t2.xpath(".//colgroup|.//col"):
            cg.getparent().remove(cg)
        for e in t2.iter():
            if not isinstance(e.tag, str):
                continue
            for a in list(e.attrib):
                if a in ("rowspan", "colspan") and e.get(a) != "1":
                    continue
                if e.tag == "img" and a in ("src", "alt"):
                    continue
                if e.tag == "a" and a == "href":
                    continue
                del e.attrib[a]
            if e.tag == "img":
                src = e.get("src") or ""
                if src and not src.startswith("http"):
                    e.set("src", "https://www.boe.es" + (src if src.startswith("/") else "/" + src))
        html = etree.tostring(t2, encoding="unicode", method="html", with_tail=False)
        html = re.sub(r"\s*\n\s*", "\n", html).strip()
        return html
    lines = ["| " + " | ".join(grid[0]) + " |", "|" + "---|" * width]
    for r in grid[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------- body

class Ctx:
    def __init__(self, base_url, levels):
        self.base_url = base_url
        self.levels = levels  # rank prefix -> heading level
        self.article_level = 2 + len([r for r in levels if r != "anexo"])
        self.out = []

    def heading(self, level, text):
        text = text.strip()
        if not text:
            return
        if level <= 6:
            self.out.append("#" * level + " " + text)
        else:
            self.out.append(f"**{text}**")

    def para(self, text, quote=False):
        text = text.strip()
        if not text:
            return
        text = md_escape_line(text)
        if quote:
            text = "\n".join("> " + ln for ln in text.split("\n"))
        self.out.append(text)


def head_rank(cls):
    cls = (cls or "").lower()
    if cls == "anexo" or cls.startswith("anexo_"):
        return "anexo"
    for r in reversed(HEAD_RANKS):  # subseccion before seccion
        if cls == r or cls.startswith(r + "_"):
            return r
    return None


def render_children(ctx, parent, quote=False):
    pending = None  # (rank, [texts]) for *_num + *_tit merging
    children = list(parent)

    def flush():
        nonlocal pending
        if pending:
            rank, texts = pending
            ctx.heading(ctx.levels.get(rank, ctx.article_level), " — ".join(t for t in texts if t))
            pending = None

    for ch in children:
        tag = ch.tag if isinstance(ch.tag, str) else ""
        if not tag:
            continue
        cls = ch.get("class") or ""
        cad = ch.get("caduca") or ""
        if re.fullmatch(r"\d{8}", cad) and cad <= TODAY.strftime("%Y%m%d"):
            continue  # element expired (shown on boe.es only until that date)
        if tag == "p":
            t = text_of(ch, ctx.base_url)
            rank = head_rank(cls) if not quote else None
            if rank:
                if pending and pending[0] == rank and cls.endswith("_tit"):
                    pending[1].append(t)
                    flush()
                    continue
                flush()
                if cls.endswith("_num"):
                    pending = (rank, [t])
                else:
                    ctx.heading(ctx.levels.get(rank, ctx.article_level), t)
                continue
            flush()
            if cls == "articulo" and not quote:
                ctx.heading(ctx.article_level, t)
            elif cls in ("centro_negrita",) and t and not quote:
                ctx.para(f"**{t}**")
            else:
                ctx.para(t, quote)
        elif tag == "blockquote":
            flush()
            # "noDesdeYYYYMMDD": note/previous wording shown only until that date (as on boe.es)
            mnd = re.search(r"noDesde(\d{8})", cls)
            if mnd and mnd.group(1) <= TODAY.strftime("%Y%m%d"):
                continue
            render_children(ctx, ch, quote=True)
        elif tag == "table":
            flush()
            md = table_to_md(ch, ctx.base_url)
            if quote:
                md = "\n".join("> " + ln for ln in md.split("\n"))
            ctx.out.append(md)
        elif tag in ("ul", "ol"):
            flush()
            for i, li in enumerate(ch.xpath("./li"), 1):
                t = text_of(li, ctx.base_url)
                if t:
                    item = (f"{i}. " if tag == "ol" else "- ") + t
                    ctx.out.append(("> " if quote else "") + item)
        elif tag == "img":
            flush()
            ctx.para(text_of_img(ch), quote)
        elif tag in ("div", "section"):
            flush()
            render_children(ctx, ch, quote)
        elif tag in ("pre",):
            flush()
            ctx.out.append("```\n" + "".join(ch.itertext()).strip("\n") + "\n```")
        else:
            flush()
            t = text_of(ch, ctx.base_url)
            if t:
                ctx.para(t, quote)
    flush()


def text_of_img(img):
    src = img.get("src") or ""
    if src and not src.startswith("http"):
        src = "https://www.boe.es" + (src if src.startswith("/") else "/" + src)
    return f"![{norm_ws(img.get('alt') or 'imagen')}]({src})"


def pick_version(bloque):
    vs = bloque.findall("version")
    return vs[-1] if vs else None


def convert(xml_path, retrieved, cat=None):
    tree = etree.parse(xml_path, etree.XMLParser(huge_tree=True, recover=True))
    data = tree.find("data")
    md = data.find("metadatos")
    cat = cat or {}

    def m(tag):
        v = cat.get(tag)
        if isinstance(v, dict):
            v = v.get("texto")
        if v:
            return norm_ws(str(v))
        e = md.find(tag) if md is not None else None
        return norm_ws(e.text) if e is not None and e.text else ""

    ident = m("identificador")
    titulo = m("titulo")
    rango = m("rango")
    ambito = m("ambito")
    dep = m("departamento")
    texto = data.find("texto")
    bloques = texto.findall("bloque") if texto is not None else []

    xml_id = os.path.basename(xml_path)[:-4]
    today = TODAY.strftime("%Y%m%d")
    chosen = []
    pubs = []
    for b in bloques:
        cad = b.get("fecha_caducidad")
        if cad and re.fullmatch(r"\d{8}", cad) and cad <= today:
            continue
        v = pick_version(b)
        if v is None:
            continue
        chosen.append((b, v))
        for vv in b.findall("version"):
            p = vv.get("fecha_publicacion")
            if p and vv.get("id_norma") and vv.get("id_norma") != xml_id:
                pubs.append(p)

    # heading ranks present
    present = set()
    for b, v in chosen:
        for p in v.iter("p"):
            if p.getparent().tag == "blockquote":
                continue
            r = head_rank(p.get("class"))
            if r and r != "anexo":
                present.add(r)
    ranks = [r for r in HEAD_RANKS if r in present]
    levels = {r: 2 + i for i, r in enumerate(ranks)}
    levels["anexo"] = 2
    base_url = f"https://www.boe.es/buscar/act.php?id={ident}"
    ctx = Ctx(base_url, levels)
    for b, v in chosen:
        render_children(ctx, v)

    body = "\n\n".join(x for x in ctx.out if x.strip())
    body = re.sub(r"[ \t]+\n", "\n", body)

    status = "in_force"
    if m("vigencia_agotada") == "S" or m("estatus_derogacion") == "S":
        status = "repealed"
    elif m("estatus_anulacion") == "S":
        status = "repealed"
    for b in bloques:
        if b.get("tipo") == "nota_inicial":
            t = norm_ws(" ".join(b.itertext()))
            if re.match(r"(Norma|Disposición) (derogada|anulada)", t):
                status = "repealed"

    typ = RANGOS.get(rango, (None, "regulation"))[1]
    if CODE_RE.match(titulo) and rango != "Constitución":
        typ = "code"

    last = max(pubs) if pubs else None
    fm = [
        "---",
        f"title: {yaml_str(titulo.rstrip('.') if titulo.endswith('.') and not titulo.endswith('..') else titulo)}",
        f"identifier: {yaml_str(ident)}",
    ]
    eli = m("url_eli")
    if eli:
        fm.append(f"eli: {yaml_str(eli)}")
    fm += [
        f"type: {typ}",
        f"rank: {yaml_str(rango)}",
        "jurisdiction: es" + ("" if ambito == "Estatal" else f"-{community_slug(dep)}"),
        "language: es",
    ]
    if dep:
        fm.append(f"department: {yaml_str(dep)}")
    for key, tag in (("date", "fecha_disposicion"), ("published", "fecha_publicacion"),
                     ("in_force_from", "fecha_vigencia")):
        d = fmt_date(m(tag))
        if d:
            fm.append(f"{key}: {d}")
    if last and fmt_date(last):
        fm.append(f"last_amended: {fmt_date(last)}")
    upd = m("fecha_actualizacion")
    if upd and fmt_date(upd[:8]):
        fm.append(f"consolidated: {fmt_date(upd[:8])}")
    diario = m("diario")
    num = m("diario_numero")
    if diario:
        fm.append(f"gazette: {yaml_str(diario + (' núm. ' + num if num else ''))}")
    fm += [
        f"status: {status}",
        f"source: {yaml_str(m('url_html_consolidada') or base_url)}",
        f"retrieved: {retrieved}",
        "---",
    ]
    h1 = titulo.rstrip(".") if titulo.endswith(".") else titulo
    doc = "\n".join(fm) + "\n\n# " + h1 + "\n\n" + body.strip() + "\n"
    return ident, titulo, rango, ambito, dep, doc, bool(chosen)


def target_path(ident, titulo, rango, ambito, dep, fecha):
    year = (fecha or "")[:4] or "sin-fecha"
    d, _ = RANGOS.get(rango, (slugify(rango) or "otros", None))
    stem = slugify(ident, 40)
    name = slugify(stem + "-" + slugify(titulo, 200), 100)
    if rango == "Constitución" and ambito == "Estatal":
        return os.path.join("constitucion", name + ".md")
    if ambito == "Estatal":
        return os.path.join(d, year, name + ".md")
    return os.path.join("autonomicas", community_slug(dep), d, year, name + ".md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=DEFAULT_RAW)
    ap.add_argument("--out", default=REPO)
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--retrieved", default=TODAY.isoformat())
    args = ap.parse_args()
    xml_dir = os.path.join(args.raw, "xml")
    manifest_path = os.path.join(args.out, "scripts", "manifest.json")
    manifest = {}
    if os.path.exists(manifest_path):
        manifest = json.load(open(manifest_path, encoding="utf-8"))
    catalogue = {}
    cat_path = os.path.join(args.raw, "catalogue.json")
    if os.path.exists(cat_path):
        catalogue = {i["identificador"]: i for i in json.load(open(cat_path, encoding="utf-8"))}
    files = sorted(os.listdir(xml_dir))
    if args.ids:
        files = [i + ".xml" for i in args.ids]
    n = 0
    empty = []
    for fn in files:
        if not fn.endswith(".xml"):
            continue
        p = os.path.join(xml_dir, fn)
        try:
            ident, titulo, rango, ambito, dep, doc, has_text = convert(p, args.retrieved, catalogue.get(fn[:-4]))
        except Exception as e:  # noqa
            print(f"ERROR {fn}: {e}", file=sys.stderr)
            continue
        if not has_text:
            empty.append(ident)
        fecha = re.search(r"^date: (\d{4})", doc, re.M)
        rel = target_path(ident, titulo, rango, ambito, dep, fecha.group(1) if fecha else None)
        old = manifest.get(ident)
        if old and old != rel and os.path.exists(os.path.join(args.out, old)):
            os.remove(os.path.join(args.out, old))
        full = os.path.join(args.out, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(doc)
        manifest[ident] = rel
        n += 1
        if n % 500 == 0:
            print(f"{n} converted", file=sys.stderr)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(manifest.items())), f, ensure_ascii=False, indent=0)
    print(f"converted {n}; without text: {len(empty)} {empty[:20]}", file=sys.stderr)


if __name__ == "__main__":
    main()
