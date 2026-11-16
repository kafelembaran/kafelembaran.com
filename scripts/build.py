"""Build the Kafe Lembaran static site from data/books.json.

Usage:
  python3 scripts/build.py            # build for kafelembaran.com (pretty URLs: /slug/)
  python3 scripts/build.py --preview  # build for a private preview (links end in index.html)

Output goes to dist/. Nothing here needs secrets, a database or a login.
"""
import html, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "books.json"
DIST = ROOT / "dist"
PREVIEW = "--preview" in sys.argv

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REQUIRED = ["slug", "title", "author", "category", "summary", "why_read", "for_who", "links"]
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lora:wght@600;700&display=swap">'


def e(s):
    return html.escape(str(s), quote=True)


def validate(data):
    """Stop the build with a clear message if the data has a mistake."""
    errors, seen = [], set()
    for i, b in enumerate(data["books"]):
        who = b.get("slug") or f"book #{i + 1}"
        for f in REQUIRED:
            if not b.get(f):
                errors.append(f"{who}: missing '{f}'")
        slug = b.get("slug", "")
        if slug and not SLUG_RE.match(slug):
            errors.append(f"{who}: slug must be lowercase letters, numbers and hyphens")
        if slug in seen:
            errors.append(f"{who}: slug used twice")
        seen.add(slug)
        if slug in {"assets", "tentang", "index"}:
            errors.append(f"{who}: slug '{slug}' is reserved")
        if len(b.get("summary", [])) != 3:
            errors.append(f"{who}: summary must have exactly 3 lines")
        links = b.get("links", {})
        if not links.get("shopee") and not links.get("publisher") and not links.get("bookcafe"):
            errors.append(f"{who}: needs at least one buy link")
        for k, v in links.items():
            if v and not v.startswith("https://"):
                errors.append(f"{who}: {k} link must start with https://")
    if sum(1 for b in data["books"] if b.get("featured")) > 1:
        errors.append("only one book can be 'featured'")
    if errors:
        sys.exit("Build stopped, fix these first:\n  - " + "\n  - ".join(errors))


def href(path):
    """Link to a page; previews need the explicit index.html."""
    if PREVIEW:
        return (path + "index.html") if path.endswith("/") or path == "" else path
    return path or "./"


def cover(b, cls="cover"):
    if b.get("cover_image"):
        return f'<div class="{cls} img"><img src="{e(b["cover_image"])}" alt="Kulit buku {e(b["title"])}"></div>'
    return (f'<div class="{cls}" style="background:{e(b.get("cover_color", "#1f6f6a"))}" aria-hidden="true">'
            f'<b>{e(b["title"])}</b><small>{e(b["author"])}</small></div>')


def head(title, desc, canonical, noindex, css):
    robots = '<meta name="robots" content="noindex">' if noindex else ""
    return f"""<!DOCTYPE html>
<html lang="ms">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
{robots}
{FONTS}
<link rel="stylesheet" href="{css}">
<link rel="icon" href="{css.replace('style.css', 'logo.svg')}">
</head>
<body>"""


def book_page(site, b):
    l = b["links"]
    title = f'{b["title"]} oleh {b["author"]} | {site["name"]}'
    desc = " ".join(b["summary"])[:155]
    out = [head(title, desc, f'{site["domain"]}/{b["slug"]}/', b.get("sample"), "../assets/style.css")]
    if b.get("sample"):
        out.append('<div class="sample">CONTOH: buku dan pautan ini untuk ujian sahaja</div>')
    out.append(f'<div class="wrap"><nav class="top"><a class="brandrow brand" href="{href("../")}"><img src="../assets/logo.svg" alt="">{e(site["name"])}</a>'
               f'<a class="back" href="{href("../")}">&larr; Semua buku</a></nav>')
    out.append(cover(b))
    out.append(f'<h1>{e(b["title"])}</h1><p class="author">{e(b["author"])}</p><span class="cat">{e(b["category"])}</span>')
    if l.get("shopee"):
        out.append(f'<a class="buy" href="{e(l["shopee"])}" rel="sponsored noopener" target="_blank">Beli di Shopee<small>Semak harga di Shopee</small></a>')
    alts = []
    if l.get("publisher"):
        alts.append(f'<a href="{e(l["publisher"])}" rel="sponsored noopener" target="_blank">Laman penerbit</a>')
    if l.get("bookcafe"):
        alts.append(f'<a href="{e(l["bookcafe"])}" rel="sponsored noopener" target="_blank">Bookcafe</a>')
    if alts:
        out.append('<div class="alt">' + "".join(alts) + "</div>")
    else:
        out.append('<div style="height:16px"></div>')
    out.append('<section class="card"><h2>Ringkasan</h2><ul>' + "".join(f"<li>{e(s)}</li>" for s in b["summary"]) + "</ul></section>")
    out.append(f'<section class="card"><h2>Kenapa baca buku ni</h2><p>{e(b["why_read"])}</p></section>')
    out.append(f'<section class="card"><h2>Sesuai untuk siapa</h2><p>{e(b["for_who"])}</p></section>')
    out.append(f'<p class="disclose">{e(site["disclosure"])}</p>')
    out.append(f'<footer>{e(site["name"])} &middot; {e(site["tagline"])}</footer></div></body></html>')
    return "\n".join(out)


def home(site, books):
    """Homepage: book of the week, grid of all books, optional WhatsApp button."""
    featured = next((b for b in books if b.get("featured")), books[0] if books else None)
    noindex = all(b.get("sample") for b in books)
    desc = f'{site["tagline"]} Cadangan buku untuk orang sibuk, dengan pautan beli di Shopee.'
    out = [head(f'{site["name"]}: cadangan buku untuk orang sibuk', desc, site["domain"] + "/", noindex, "assets/style.css")]
    if any(b.get("sample") for b in books):
        out.append('<div class="sample">CONTOH: buku dan pautan ini untuk ujian sahaja</div>')
    out.append(f'<div class="wrap"><nav class="top"><a class="brandrow brand" href="{href("")}"><img src="assets/logo.svg" alt="">{e(site["name"])}</a></nav>')
    out.append(f'<header class="hero"><h1>Cadangan buku untuk orang sibuk</h1><p>{e(site["tagline"])} Satu buku, satu minit.</p></header>')
    if featured:
        f = featured
        out.append('<h2 class="label">Buku minggu ini</h2>')
        out.append(f'<a class="feat" href="{href(f["slug"] + "/")}">{cover(f)}<span><h3>{e(f["title"])}</h3>'
                   f'<p class="by">{e(f["author"])}</p><p class="why">{e(f["why_read"])}</p><span class="go">Lihat buku &rarr;</span></span></a>')
    out.append(f'<h2 class="label">Semua buku ({len(books)})</h2><div class="grid">')
    for b in books:
        out.append(f'<a href="{href(b["slug"] + "/")}">{cover(b)}<strong>{e(b["title"])}</strong>'
                   f'<small class="meta">{e(b["author"])} &middot; {e(b["category"])}</small></a>')
    out.append("</div>")
    if site.get("whatsapp_channel"):
        out.append(f'<a class="wa" href="{e(site["whatsapp_channel"])}" rel="noopener" target="_blank">Sertai saluran WhatsApp: 1 buku seminggu</a>')
    out.append(f'<p class="disclose">{e(site["disclosure"])}</p>')
    out.append(f'<footer>{e(site["name"])} &middot; {e(site["tagline"])}</footer></div></body></html>')
    return "\n".join(out)


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    validate(data)
    site, books = data["site"], sorted(data["books"], key=lambda b: b.get("added", ""), reverse=True)
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets").mkdir(parents=True)
    shutil.copy(ROOT / "assets" / "style.css", DIST / "assets" / "style.css")
    for b in books:
        (DIST / b["slug"]).mkdir()
        (DIST / b["slug"] / "index.html").write_text(book_page(site, b), encoding="utf-8")
    shutil.copy(ROOT / "assets" / "logo.svg", DIST / "assets" / "logo.svg")
    (DIST / "index.html").write_text(home(site, books), encoding="utf-8")
    print(f"Built {len(books)} book pages into dist/" + (" (preview mode)" if PREVIEW else ""))


if __name__ == "__main__":
    main()
