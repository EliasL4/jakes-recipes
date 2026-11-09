#!/usr/bin/env python3
"""Regenerate Jake's Recipes from the JSON files in data/recipes/.

Usage (from the repo root or anywhere):
    python3 scripts/build.py

Reads:   data/recipes/*.json
Writes:  recipes/<id>.html, data/index.json, index.html

Standard library only. No dependencies, no build step needed on the host.
"""
import json
import sys
from datetime import date
from fractions import Fraction
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "recipes"
PAGES_DIR = ROOT / "recipes"
SITE_NAME = "Jake's Recipes"
SITE_DESC = ("Jake's personal recipe collection: tried and saved recipes, "
             "searchable by name and tag, each credited to its original source.")

REQUIRED = ["id", "title", "summary", "tags", "ingredient_groups", "steps", "source_url"]


def e(value):
    return escape(str(value), quote=True)


def fmt_qty(q):
    """0.5 -> 1/2, 1.5 -> 1 1/2, 8 -> 8."""
    if q is None:
        return ""
    frac = Fraction(q).limit_denominator(16)
    whole, rem = divmod(frac.numerator, frac.denominator)
    if rem == 0:
        return str(whole)
    part = f"{rem}/{frac.denominator}"
    return f"{whole} {part}" if whole else part


def source_site(r):
    if r.get("source_site"):
        return r["source_site"]
    name = r.get("source_name", "the original recipe")
    return name.split(" (")[0]


def head(title, description, css_href, extra=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta name="robots" content="index,follow">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#b5532a">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%8D%B2%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="{css_href}">
{extra}</head>
"""


def header(home_href):
    return f"""<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{home_href}"><span class="brand-mark" aria-hidden="true">🍲</span> {e(SITE_NAME)}</a>
  </div>
</header>
"""


def footer():
    return """<footer class="site-footer">
  <div class="wrap">
    <p>Jake's personal recipe collection. Every recipe is credited and linked to its original source; summaries and steps are written in our own words, and photos stay on the original sites.</p>
  </div>
</footer>
"""


def json_ld(r):
    ings = []
    for g in r["ingredient_groups"]:
        for it in g["items"]:
            ings.append(it.get("original_text") or f"{fmt_qty(it.get('quantity'))} {it.get('unit') or ''} {it['name']}".strip())
    steps = [{"@type": "HowToStep", "text": s} for p in r["steps"] for s in p["items"]]
    data = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": r["title"],
        "description": r["summary"],
        "keywords": ", ".join(r["tags"]),
        "recipeYield": r.get("yield") or r.get("servings"),
        "recipeIngredient": ings,
        "recipeInstructions": steps,
        "isBasedOn": r["source_url"],
    }
    if r.get("date_added"):
        data["datePublished"] = r["date_added"]
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"


def ingredient_li(it):
    qty = fmt_qty(it.get("quantity"))
    unit = it.get("unit") or ""
    amount = " ".join(x for x in [qty, unit] if x)
    notes = f' <span class="ing-note">({e(it["notes"])})</span>' if it.get("notes") else ""
    amt = f'<span class="ing-amt">{e(amount)}</span> ' if amount else ""
    return (f'<li data-name="{e(it["name"])}" data-quantity="{e(it.get("quantity") if it.get("quantity") is not None else "")}" '
            f'data-unit="{e(unit)}">{amt}<span class="ing-name">{e(it["name"])}</span>{notes}</li>')


def recipe_page(r):
    site = source_site(r)
    title = f"{r['title']} | {SITE_NAME}"
    times = r.get("times") or {}
    facts = [
        ("Yield", r.get("yield")),
        ("Servings", r.get("servings")),
        ("Prep", times.get("prep")),
        ("Cook", times.get("cook")),
        ("Total", times.get("total")),
    ]
    facts_html = "\n".join(
        f'<div class="fact"><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in facts if v)
    tags_html = " ".join(f'<a class="tag" href="../index.html?tag={e(t)}">{e(t)}</a>' for t in r["tags"])

    groups = []
    for g in r["ingredient_groups"]:
        items = "\n".join(ingredient_li(it) for it in g["items"])
        groups.append(f'<div class="ing-group"><h3>{e(g["group"])}</h3>\n<ul class="ingredients">\n{items}\n</ul></div>')

    steps = []
    for p in r["steps"]:
        lis = "\n".join(f"<li>{e(s)}</li>" for s in p["items"])
        steps.append(f'<div class="step-group"><h3>{e(p["phase"])}</h3>\n<ol class="steps">\n{lis}\n</ol></div>')

    flags = r.get("flags") or []
    order = {"high": 0, "medium": 1, "low": 2}
    flags = sorted(flags, key=lambda f: order.get(f.get("severity"), 3))
    flags_html = ""
    if flags:
        lis = "\n".join(
            f'<li class="flag flag-{e(f.get("severity", "low"))}">{e(f["text"])}</li>' for f in flags)
        flags_html = f"""<section class="card headsup" aria-labelledby="headsup-h">
  <h2 id="headsup-h"><span aria-hidden="true">⚠️</span> Heads up</h2>
  <ul class="flags">
{lis}
  </ul>
</section>
"""
    notes = r.get("notes") or []
    notes_html = ""
    if notes:
        lis = "\n".join(f"<li>{e(n)}</li>" for n in notes)
        notes_html = f'<section class="card" aria-labelledby="notes-h"><h2 id="notes-h">Notes</h2>\n<ul class="notes">\n{lis}\n</ul></section>\n'

    photos_url = (r.get("images") or {}).get("source_photos_url") or r["source_url"]
    added = f'<p class="added">Added {e(r["date_added"])}</p>' if r.get("date_added") else ""
    author = f" by {e(r['source_author'])}" if r.get("source_author") else ""

    return head(title, r["summary"], "../assets/style.css", json_ld(r)) + f"""<body class="recipe-page">
{header("../index.html")}<main class="wrap">
<nav class="crumbs"><a href="../index.html">← All recipes</a></nav>
<article class="recipe">
  <header class="recipe-head">
    <h1>{e(r['title'])}</h1>
    <p class="summary">{e(r['summary'])}</p>
    <div class="tags">{tags_html}</div>
    <a class="credit" href="{e(r['source_url'])}" target="_blank" rel="noopener">
      <span class="credit-label">Recipe from</span>
      <span class="credit-name">{e(site)}</span>
      <span class="credit-go" aria-hidden="true">↗</span>
    </a>
  </header>

  <figure class="photo-placeholder">
    <div class="photo-art" aria-hidden="true">
      <svg viewBox="0 0 120 80" width="120" height="80"><path d="M14 38h92a46 30 0 0 1-92 0z" fill="#f3c77b" stroke="#b5532a" stroke-width="3"/><path d="M30 38c4-10 12-14 20-8 6-8 16-8 22 0 8-6 16-2 20 8" fill="none" stroke="#e39a3b" stroke-width="4" stroke-linecap="round"/><path d="M46 20c-4-6 4-8 0-14M60 20c-4-6 4-8 0-14M74 20c-4-6 4-8 0-14" fill="none" stroke="#c9a88a" stroke-width="2.5" stroke-linecap="round"/></svg>
    </div>
    <figcaption>No photo here yet. <a href="{e(photos_url)}" target="_blank" rel="noopener">See photos at the original recipe ↗</a></figcaption>
  </figure>

  <section class="card" aria-label="Quick facts">
    <h2>Quick facts</h2>
    <dl class="facts">
{facts_html}
    </dl>
  </section>

{flags_html}
  <div class="cols">
    <section class="card" aria-labelledby="ing-h">
      <h2 id="ing-h">Ingredients</h2>
{''.join(groups)}
    </section>
    <section class="card" aria-labelledby="steps-h">
      <h2 id="steps-h">Steps</h2>
{''.join(steps)}
    </section>
  </div>

{notes_html}
  <section class="card source-card">
    <h2>Credit</h2>
    <p>This recipe comes from <a href="{e(r['source_url'])}" target="_blank" rel="noopener"><strong>{e(site)}</strong></a>{author}. Ingredients and amounts match the original recipe card; the summary and steps are in our own words. Visit the original for the full post and photos.</p>
    <a class="btn" href="{e(r['source_url'])}" target="_blank" rel="noopener">Recipe from {e(site)} ↗</a>
    {added}
  </section>
</article>
</main>
{footer()}</body>
</html>
"""


def index_entry(r):
    times = r.get("times") or {}
    return {
        "id": r["id"],
        "title": r["title"],
        "summary": r["summary"],
        "tags": r["tags"],
        "total_time": times.get("total"),
        "source_site": source_site(r),
        "source_url": r["source_url"],
        "date_added": r.get("date_added"),
        "url": f"recipes/{r['id']}.html",
        "data": f"data/recipes/{r['id']}.json",
    }


def index_page(entries):
    tags = sorted({t for x in entries for t in x["tags"]})
    chips = ['<button type="button" class="chip is-active" data-tag="all" aria-pressed="true">All</button>']
    for t in tags:
        n = sum(1 for x in entries if t in x["tags"])
        chips.append(f'<button type="button" class="chip" data-tag="{e(t)}" aria-pressed="false">{e(t)} <span class="count">{n}</span></button>')
    cards = []
    for x in entries:
        hay = " ".join([x["title"], x["summary"], " ".join(x["tags"]), x["source_site"]]).lower()
        tag_spans = "".join(f'<span class="tag">{e(t)}</span>' for t in x["tags"])
        time = f'<span class="time">⏱ {e(x["total_time"])}</span>' if x.get("total_time") else ""
        cards.append(f"""<li class="recipe-card" data-tags="{e(' '.join(x['tags']))}" data-search="{e(hay)}">
  <a href="{e(x['url'])}">
    <h3>{e(x['title'])}</h3>
    <p>{e(x['summary'])}</p>
    <div class="card-meta">{time}<span class="from">from {e(x['source_site'])}</span></div>
    <div class="tags">{tag_spans}</div>
  </a>
</li>""")
    count = len(entries)
    return head(SITE_NAME, SITE_DESC, "assets/style.css") + f"""<body class="home">
{header("index.html")}<main class="wrap">
<section class="hero">
  <h1>{e(SITE_NAME)}</h1>
  <p>A personal recipe book. Search by name or ingredient idea, or tap a tag to filter.</p>
</section>
<section class="browse" aria-label="Browse recipes">
  <label class="search">
    <span class="visually-hidden">Search recipes</span>
    <input id="q" type="search" placeholder="Search recipes: mac, pantry, pasta…" autocomplete="off">
  </label>
  <div class="chips" role="group" aria-label="Filter by tag">
    {''.join(chips)}
  </div>
  <p class="result-count" id="count" aria-live="polite">{count} recipe{'s' if count != 1 else ''}</p>
  <ul class="recipe-list" id="list">
{chr(10).join(cards)}
  </ul>
  <p class="empty" id="empty" hidden>No recipes match. Try another word or tag.</p>
</section>
</main>
{footer()}<script src="assets/app.js" defer></script>
</body>
</html>
"""


def main():
    files = sorted(DATA_DIR.glob("*.json"))
    if not files:
        sys.exit("No recipes found in data/recipes/")
    recipes, seen = [], set()
    for f in files:
        r = json.loads(f.read_text(encoding="utf-8"))
        missing = [k for k in REQUIRED if k not in r]
        if missing:
            sys.exit(f"{f.name}: missing fields {missing}")
        if r["id"] != f.stem:
            sys.exit(f"{f.name}: id '{r['id']}' must match the file name")
        if r["id"] in seen:
            sys.exit(f"duplicate id {r['id']}")
        seen.add(r["id"])
        recipes.append(r)

    recipes.sort(key=lambda r: (r.get("date_added") or "", r["title"]), reverse=True)
    PAGES_DIR.mkdir(exist_ok=True)
    keep = set()
    for r in recipes:
        out = PAGES_DIR / f"{r['id']}.html"
        out.write_text(recipe_page(r), encoding="utf-8")
        keep.add(out.name)
    for old in PAGES_DIR.glob("*.html"):
        if old.name not in keep:
            old.unlink()
            print(f"removed stale {old.relative_to(ROOT)}")

    entries = [index_entry(r) for r in recipes]
    updated = max((r.get("date_added") or "" for r in recipes), default="") or date.today().isoformat()
    (ROOT / "data" / "index.json").write_text(
        json.dumps({"updated": updated, "count": len(entries), "recipes": entries}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (ROOT / "index.html").write_text(index_page(entries), encoding="utf-8")
    print(f"Built {len(recipes)} recipe page(s), data/index.json and index.html")


if __name__ == "__main__":
    main()
