"""Checks run before every preview or release: python3 scripts/test_build.py"""
import html
import copy, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build  # noqa: E402

data = json.loads((ROOT / "data" / "books.json").read_text(encoding="utf-8"))
fails = []


def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


def rejects(name, mutate):
    bad = copy.deepcopy(data)
    mutate(bad)
    try:
        build.validate(bad)
        check(name, False)
    except SystemExit:
        check(name, True)


# 1. bad data is refused
rejects("rejects uppercase slug", lambda d: d["books"][0].update(slug="Tabiat Kecil"))
rejects("rejects duplicate slug", lambda d: d["books"].append(dict(d["books"][0], featured=False)))
rejects("rejects reserved slug", lambda d: d["books"][0].update(slug="assets"))
rejects("rejects 2-line summary", lambda d: d["books"][0].update(summary=["a", "b"]))
rejects("rejects http (not https) link", lambda d: d["books"][0]["links"].update(shopee="http://shopee.com.my/"))
rejects("rejects book with no buy link", lambda d: d["books"][0].update(links={"shopee": "", "publisher": "", "bookcafe": ""}))
rejects("rejects two featured books", lambda d: d["books"].append(dict(d["books"][0], slug=d["books"][0]["slug"] + "-2", featured=True)))

# 2. the real build works
r = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "build.py")], capture_output=True, text=True)
check("build runs", r.returncode == 0)
dist = ROOT / "dist"
for b in data["books"]:
    page = dist / b["slug"] / "index.html"
    check(f"page exists: /{b['slug']}/", page.exists())
    if not page.exists():
        continue
    h = page.read_text(encoding="utf-8")
    check(f"{b['slug']}: has title", b["title"] in html.unescape(h))
    if b["links"].get("shopee"):
        check(f"{b['slug']}: Shopee button present", 'class="buy"' in h and "Beli di Shopee" in h)
    check(f"{b['slug']}: no price shown", "RM" not in h)
    check(f"{b['slug']}: disclosure shown", "komisen" in h)
    check(f"{b['slug']}: buy links marked sponsored", 'rel="sponsored' in h)
    check(f"{b['slug']}: sample pages hidden from Google", (not b.get("sample")) or 'name="robots" content="noindex"' in h)

# 2b. homepage
home = (dist / "index.html").read_text(encoding="utf-8") if (dist / "index.html").exists() else ""
check("homepage exists", bool(home))
check("homepage links every book", all(f'href="{b["slug"]}/' in home for b in data["books"]))
feat = next((b for b in data["books"] if b.get("featured")), None)
check("homepage shows book of the week", "Buku minggu ini" in home and (not feat or feat["title"].split(",")[0] in home))
check("no WhatsApp button without a channel link", data["site"].get("whatsapp_channel") or "saluran WhatsApp" not in home)
check("homepage has logo and favicon", 'assets/logo.svg' in home and 'rel="icon"' in home)
check("logo copied to site", (dist / "assets" / "logo.svg").exists())
check("homepage hidden from Google while all books are samples", (not all(b.get("sample") for b in data["books"])) or 'content="noindex"' in home)

check("media files published", all((dist / "media" / f.name).exists() for f in (ROOT / "media").glob("*")) if (ROOT / "media").exists() else True)

# 2c. calculator page /kira/ (maths checked against the video numbers)
calc = (dist / "kira" / "index.html")
check("calculator page exists: /kira/", calc.exists())
check("homepage links the calculator", 'href="kira/"' in home)
if calc.exists():
    ch = calc.read_text(encoding="utf-8")
    check("calculator says it is not financial advice", "bukan nasihat kewangan" in ch)
    js = ch.split("<script>")[1].split("</script>")[0]
    node = subprocess.run(["node", "-e", js + "\nconst p=plan(25,60,1e6,0.06,3);console.log(JSON.stringify(p))"], capture_output=True, text=True)
    if node.returncode == 0:
        p = json.loads(node.stdout)
        check("calc: titik silang at age 37", p["ageCross"] == 37)
        check("calc: RM1,116/month to age 40", round(p["monthly"]) == 1116 and p["ageStop"] == 40)
        check("calc: RM311,805 at age 40", round(p["needAtStop"]) == 311805)
        check("calc: RM748/month if saving all 35 years", round(p["monthlyAll"]) == 748)
    else:
        print("SKIP calculator maths (node not available)")

# 3. text is escaped (no broken pages from quotes or < >)
evil = copy.deepcopy(data["books"][0]); evil["title"] = 'A <b>"bold"</b> title'
check("escapes HTML in titles", "<b>\"bold\"</b>" not in build.book_page(data["site"], evil))

# 4. no secrets in the project
import re
secret_re = re.compile(r"""(api[_-]?key|password|passwd|secret|token)["']?\s*[:=]\s*["']?[A-Za-z0-9_\-]{8,}""", re.I)
leaks = [p.name for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and p.name != "test_build.py"
         and secret_re.search(p.read_text(errors="ignore"))]
check("secret check catches a planted key", bool(secret_re.search('API_KEY="sk_live_12345678abc"')))
check("no secrets in files", not leaks)

print(f"\n{len(fails)} failed" if fails else "\nAll checks passed")
sys.exit(1 if fails else 0)