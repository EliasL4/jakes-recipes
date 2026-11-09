# Jake's Recipes

Jake's personal recipe collection: a plain static website (HTML, CSS and a little vanilla JavaScript). There is no framework and no build step on the host, so it deploys as-is to Cloudflare Pages or any static host.

## What's in here

```
index.html                 Home page: searchable, tag-filterable recipe index (generated)
recipes/<id>.html          One page per recipe (generated)
data/recipes/<id>.json     Source of truth: structured data for each recipe
data/index.json            Summary list of all recipes (generated)
assets/style.css           Site styles
assets/app.js              Search and tag filtering on the home page
scripts/build.py           Regenerates the generated files from data/recipes/*.json
```

Only edit the files in `data/recipes/` (plus `assets/` and `scripts/build.py` for design changes). Everything marked *generated* is rebuilt by the script.

## Add a recipe

1. Copy an existing file in `data/recipes/` to `data/recipes/<new-id>.json`. Use a short lowercase id with dashes, for example `banana-bread`. The `id` field inside the file must match the file name.
2. Fill in the fields (see the format below). Copy ingredient amounts exactly from the original recipe, but write the summary and steps in your own words.
3. Run the build (Python 3, standard library only):

   ```sh
   python3 scripts/build.py
   ```

4. Preview locally:

   ```sh
   python3 -m http.server 8000
   # open http://localhost:8000
   ```

5. Commit and push. Cloudflare Pages republishes the site automatically:

   ```sh
   git add -A
   git commit -m "Add banana bread"
   git push
   ```

## Recipe format

```json
{
  "id": "banana-bread",
  "title": "Banana Bread",
  "source_url": "https://example.com/banana-bread/",
  "source_name": "Example Kitchen (Author Name)",
  "source_site": "Example Kitchen",
  "source_author": "Author Name",
  "summary": "One or two sentences, in our own words.",
  "tags": ["baking", "breakfast"],
  "servings": "1 loaf, about 10 slices",
  "yield": "1 loaf",
  "times": { "prep": "15 minutes", "cook": "60 minutes", "total": "75 minutes" },
  "ingredient_groups": [
    {
      "group": "Batter",
      "items": [
        {
          "original_text": "2 cups all-purpose flour",
          "name": "all-purpose flour",
          "quantity": 2,
          "unit": "cup",
          "notes": null
        }
      ]
    }
  ],
  "steps": [
    { "phase": "Mix", "items": ["Step one in our own words.", "Step two."] }
  ],
  "notes": ["Optional tips."],
  "flags": [
    { "severity": "high", "text": "Anything a cook should double-check, shown as a Heads up note." }
  ],
  "images": { "embedded": [], "note": "", "source_photos_url": "https://example.com/banana-bread/" },
  "date_added": "2026-11-09"
}
```

Required fields: `id`, `title`, `summary`, `tags`, `ingredient_groups`, `steps`, `source_url`. Everything else is optional and is skipped on the page when empty or `null`.

### Ingredients (inventory-friendly)

Each ingredient keeps a normalized `name` (lowercase, singular where sensible), a numeric `quantity` (decimals, e.g. `0.5` for 1/2; `null` if none), a `unit` (`cup`, `tbsp`, `tsp`, `oz`, `lb`, `g`, `ml`, ...; `null` if none) and free-text `notes`. `original_text` keeps the line exactly as the source wrote it. Pages display quantities as fractions (0.5 becomes 1/2). The same data is exposed as `data-name`, `data-quantity` and `data-unit` attributes on each ingredient line, and in `data/recipes/*.json`, for a future pantry/inventory app.

### Flags

`flags` show up on the recipe page under **Heads up**, ordered by severity (`high`, `medium`, `low`). Use them for things like a source that labels a recipe dairy-free while it contains milk powder.

## Copyright and credit

Every recipe page links prominently to its original source. Ingredient lists and amounts are factual and are reproduced exactly; summaries and steps are written in our own words, and blog narrative is not copied. Photos from source sites are not used. Each page has a placeholder that links to the original recipe's photos. Only add photos you took yourself or have the rights to use.

## Deploying on Cloudflare Pages

Connect this GitHub repo in Cloudflare Pages with:

| Setting | Value |
| --- | --- |
| Framework preset | None |
| Build command | *(leave blank)* |
| Build output directory | `/` |
| Production branch | `main` |

Run `python3 scripts/build.py` locally before pushing; the host just serves the committed files.
