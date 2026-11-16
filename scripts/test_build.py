"""Checks run before every preview or release: python3 scripts/test_build.py"""
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
rejects("rejects duplicate slug", lambda d: d["books"][1].update(slug=d["books"][0]["slug"]))
rejects("rejects reserved slug", lambda d: d["books"][0].update(slug="assets"))
rejects("rejects 2-line summary", lambda d: d["books"][0].update(summary=["a", "b"]))
rejects("rejects http (not https) link", lambda d: d["books"][0]["links"].update(shopee="http://shopee.com.my/"))
rejects("rejects book with no buy link", lambda d: d["books"][0].update(links={"shopee": "", "publisher": "", "bookcafe": ""}))
rejects("rejects two featured books", lambda d: [b.update(featured=True) for b in d["books"]])

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
    check(f"{b['slug']}: has title", b["title"] in h.replace("&#x27;", "'"))
    if b["links"].get("shopee"):
        check(f"{b['slug']}: Shopee button present", 'class="buy"' in h and "Beli di Shopee" in h)
    check(f"{b['slug']}: no price shown", "RM" not in h)
    check(f"{b['slug']}: disclosure shown", "komisen" in h)
    check(f"{b['slug']}: buy links marked sponsored", 'rel="sponsored' in h)
    check(f"{b['slug']}: sample pages hidden from Google", (not b.get("sample")) or 'name="robots" content="noindex"' in h)

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
