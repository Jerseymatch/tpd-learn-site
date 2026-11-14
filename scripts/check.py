#!/usr/bin/env python3
"""Pre-publish checks for the generated site. Run after src/build.py.

    python3 scripts/check.py [--names path/to/student_names.txt]

Checks: internal links resolve, JSON-LD parses, no leftover [[shortcodes]],
every page has a title/description/canonical, affiliate links are marked
sponsored, and (optionally) no student names appear in any page.
Exits non-zero on any failure.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
fails = []

names = []
if "--names" in sys.argv:
    with open(sys.argv[sys.argv.index("--names") + 1]) as f:
        names = [n.strip() for n in f if len(n.strip()) >= 3]

pages = [p for p in glob.glob("**/*.html", recursive=True) if not p.startswith(("src/", "node_modules/"))]
for f in pages:
    h = open(f, encoding="utf-8").read()
    if "[[" in h:
        fails.append(f"{f}: leftover shortcode")
    for ld in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try:
            json.loads(ld)
        except Exception as ex:
            fails.append(f"{f}: bad JSON-LD ({ex})")
    if f != "404.html":
        for tag in ("<title>", 'name="description"', 'rel="canonical"'):
            if tag not in h:
                fails.append(f"{f}: missing {tag}")
    for href in re.findall(r'href="(/[^"#?]*)', h):
        if href.startswith("/assets"):
            if not os.path.exists(href.lstrip("/")):
                fails.append(f"{f}: missing asset {href}")
            continue
        p = href.strip("/")
        if not os.path.exists(os.path.join(p, "index.html") if p else "index.html"):
            fails.append(f"{f}: broken link {href}")
    for a in re.findall(r"<a [^>]*amzn\.to[^>]*>", h):
        if "sponsored" not in a:
            fails.append(f"{f}: affiliate link without rel=sponsored")
    text = re.sub(r"<[^>]+>", " ", h)
    for n in names:
        if re.search(r"\b" + re.escape(n) + r"\b", text):
            fails.append(f"{f}: contains student name '{n}'")

print(f"Checked {len(pages)} pages.")
if fails:
    print("FAIL:\n  " + "\n  ".join(fails))
    sys.exit(1)
print("All checks passed.")
