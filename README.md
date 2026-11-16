# Kafe Lembaran

Laman web [kafelembaran.com](https://kafelembaran.com): cadangan buku untuk orang sibuk.

## How it works

- All books live in `data/books.json`. Add a book there; every page is generated from it.
- `scripts/build.py` turns the data file into the site in `dist/`.
- `scripts/test_build.py` checks the data and the built pages (bad slugs, missing links, prices, secrets).
- Every push to `main` runs the checks, builds the site and publishes it with GitHub Pages
  (`.github/workflows/deploy.yml`). If a check fails, nothing is published.

## Rules

- No database, no login, no personal data collected.
- No API keys or passwords in this repository, ever. If one is ever needed, it goes in GitHub Secrets.
- Sample books (`"sample": true`) are hidden from Google and must be replaced before launch.

## Local commands

```
python3 scripts/test_build.py      # run all checks
python3 scripts/build.py           # build for kafelembaran.com
python3 scripts/build.py --preview # build for a private preview
```
