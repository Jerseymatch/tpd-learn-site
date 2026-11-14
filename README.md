# learn.truepokerdealer.com: The Dealer's Handbook

Marc Shumsker's SEO content site for True Poker Dealer. It's static and pre-rendered, and Cloudflare Pages deploys it from the repo root with no build step.

## How it works

- `src/pages/**.html` is the source for every page: a JSON meta block followed by body HTML with shortcodes. See the docstring at the top of `src/build.py`.
- `src/data/videos.json` holds metadata for every YouTube video the site embeds (title, upload date, duration). It feeds the VideoObject schema.
- `python3 src/build.py` regenerates `index.html`, `deal/`, `about/` and so on at the repo root, plus `sitemap.xml`. **Commit both the source and the generated output.**
- `assets/site.css` and `assets/site.js` contain all the styling and the click-to-load YouTube embeds.

## Content standard (non-negotiable)

1. **Every claim comes from Marc**: his class transcripts, lesson transcripts, YouTube videos, or the correction log in `Training Videos/correction_analysis/`. No generic filler.
2. **Pages are written in Marc's first-person voice and bylined to him**, so he reviews every page before it counts as final (`"review": "pending"` in the meta until he approves).
3. **No student names on public pages.** Class moments are described anonymously.
4. **Class video clips are used only with Marc's approval.** Public YouTube videos can be embedded freely.
5. **No thin pages.** A topic isn't published until it's better than anything else ranking for it.

## URL structure

- `/deal/` covers procedures: how to deal, step by step.
- `/career/` covers becoming a dealer (planned).
- `/rules/` covers rulings, "what happens if…" (planned).
- `/about/marc-shumsker/` is the author page.

Old draft URLs under `/guide/` 301 to `/deal/` via `_redirects`.
