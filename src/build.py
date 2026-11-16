#!/usr/bin/env python3
"""Static site builder for learn.truepokerdealer.com.

Source pages live in src/pages/**.html. Each starts with a JSON meta block:

    <!--meta
    {"title": "...", "description": "...", "updated": "2026-11-13", ...}
    -->
    <p>Body HTML with shortcodes...</p>

Output is written to the repo root (Cloudflare Pages serves the repo root with
no build step), e.g. src/pages/deal/how-to-shuffle-cards.html ->
deal/how-to-shuffle-cards/index.html.

Shortcodes:
    [[video ID]]          primary video: real lazy-loaded embed + VideoObject schema
    [[lite ID]]           secondary video: click-to-load facade + VideoObject schema
    [[moment ID M:SS | caption]]  click-to-load facade that starts at that moment of a long video
                          (livestream teaching moments; caption optional)
    [[shorts ID ID ...]]  row of vertical YouTube Shorts facades
    [[cta KEY]]           call to action block (course | school | free | call)
    [[toc]]               table of contents built from the page's <h2 id=...> headings

Run:  python3 src/build.py
No third-party dependencies.
"""
import hashlib
import html
import json
import os
import re
import shutil
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
PAGES = os.path.join(SRC, "pages")
SITE = "https://learn.truepokerdealer.com"
MAIN = "https://truepokerdealer.com"
YT_CHANNEL = "https://www.youtube.com/@truepokerdealer"

# Every generated top-level path. The builder deletes and recreates these, and
# nothing else, so hand-maintained files at the root are never touched.
GENERATED_DIRS = ["deal", "about", "career", "rules", "tools", "stories", "gear"]

SECTIONS = {
    "deal": {"name": "How to Deal", "path": "/deal/"},
    "career": {"name": "Becoming a Dealer", "path": "/career/"},
    "rules": {"name": "Rulings", "path": "/rules/"},
    "gear": {"name": "Gear", "path": "/gear/"},
    "about": {"name": "About", "path": "/about/marc-shumsker/"},
}

AUTHOR = {
    "@type": "Person",
    "name": "Marc Shumsker",
    "url": SITE + "/about/marc-shumsker/",
    "image": SITE + "/assets/marc.jpg",
    "jobTitle": "Poker dealer, poker room shift manager and dealer trainer",
    "sameAs": [YT_CHANNEL, "https://instagram.com/truepokerdealer", MAIN],
}

ORG = {
    "@type": "Organization",
    "@id": MAIN + "/#org",
    "name": "True Poker Dealer",
    "url": MAIN,
    "sameAs": [YT_CHANNEL, "https://instagram.com/truepokerdealer", "https://tiktok.com/truepokerdealer"],
}

with open(os.path.join(SRC, "data", "videos.json")) as f:
    VIDEOS = json.load(f)
with open(os.path.join(SRC, "data", "gear.json")) as f:
    GEAR = json.load(f)


def utm(url, campaign, content="cta"):
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}utm_source=learn&utm_medium=referral&utm_campaign={campaign}&utm_content={content}"


CTAS = {
    "free": {
        "kicker": "Start free",
        "title": "Watch the first six lessons of the course, free",
        "body": "The same lessons my paying students start with: the shuffle, the pitch, cutting and handling chips. No credit card.",
        "button": "Watch the free lessons",
        "url": MAIN + "/freelessons",
    },
    "course": {
        "kicker": "The Complete Course",
        "title": "Every procedure, in order, at your own pace",
        "body": "50+ lessons covering everything a poker room expects you to know on day one. It's the course I built so I could stop re-training new hires in the back of the house. $79/month, cancel any time.",
        "button": "See the Complete Course",
        "url": MAIN + "/complete-course",
    },
    "call": {
        "kicker": "Free pathway call",
        "title": "Not sure where to start? Talk it through with me",
        "body": "Book a free 30-minute Poker Dealer Pathway Call and I'll give you a clear, personal roadmap toward getting hired.",
        "button": "Book a free call",
        "url": MAIN + "/book-pathwaycall",
    },
    "school": {
        "kicker": "Remote Dealer School",
        "title": "Want me to watch you deal and correct you live?",
        "body": "Small Zoom classes where I watch your hands and fix your mechanics in real time, until you're ready to pass an audition.",
        "button": "See Remote Dealer School",
        "url": MAIN + "/remote-dealer-school",
    },
}

e = html.escape


def iso_duration(seconds):
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "PT" + (f"{h}H" if h else "") + (f"{m}M" if m else "") + f"{s}S"


def fmt_dur(seconds):
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


CHANNEL = json.load(open(os.path.join(SRC, "data", "channel.json"), encoding="utf-8"))


def views_short(n):
    # 1439044 -> "1.4M", 667819 -> "667K", 4991348 -> "4.9M+" style is applied by callers
    if n >= 1_000_000:
        return f"{int(n / 100_000) / 10:g}M"
    if n >= 1_000:
        return f"{int(n / 1_000)}K"
    return str(n)


def views_long(n):
    m = n / 1_000_000
    nxt = int(m) + 1
    if nxt - m <= 0.02 * nxt:
        return f"almost {nxt} million"
    return f"over {int(m * 10) / 10:g} million"


def stat(key):
    n = CHANNEL["views"]
    return {
        "views_long": views_long(n),
        "views_short": views_short(n) + "+",
        "since": str(CHANNEL["since"]),
        "years": str(date.today().year - CHANNEL["since"]),
        "subs": CHANNEL["subscribers"],
    }[key]


def video_schema(vid):
    v = VIDEOS[vid]
    return {
        "@type": "VideoObject",
        "name": v["title"],
        "description": v.get("desc") or v["title"],
        "thumbnailUrl": [f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"],
        "uploadDate": v["date"],
        "duration": iso_duration(v["dur"]),
        "embedUrl": f"https://www.youtube.com/embed/{vid}",
        "contentUrl": f"https://www.youtube.com/watch?v={vid}",
        **({"interactionStatistic": {"@type": "InteractionCounter", "interactionType": {"@type": "WatchAction"},
                                     "userInteractionCount": v["views"]}} if v.get("views") else {}),
    }


def render_video(vid, primary, used):
    if vid not in VIDEOS:
        sys.exit(f"Unknown video id {vid} - add it to src/data/videos.json")
    used.append(vid)
    v = VIDEOS[vid]
    title = e(v["title"])
    vw = f' <span class="views">{views_short(v["views"])} views on YouTube</span>' if v.get("views", 0) >= 10000 else ""
    cap = f'<figcaption>{title} <span class="dur">{fmt_dur(v["dur"])}</span>{vw}</figcaption>'
    if primary:
        frame = (
            f'<div class="vframe"><iframe src="https://www.youtube-nocookie.com/embed/{vid}?rel=0" '
            f'title="{title}" loading="lazy" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture; fullscreen" '
            f'allowfullscreen></iframe></div>'
        )
    else:
        frame = (
            f'<a class="vframe lite" href="https://www.youtube.com/watch?v={vid}" data-yt="{vid}" aria-label="Play: {title}">'
            f'<img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360">'
            f'<span class="play" aria-hidden="true"></span></a>'
        )
    return f'<figure class="video">{frame}{cap}</figure>'


def to_sec(ts):
    sec = 0
    for part in ts.split(":"):
        sec = sec * 60 + int(part)
    return sec


def render_moment(vid, ts, caption, used):
    if vid not in VIDEOS:
        sys.exit(f"Unknown video id {vid} - add it to src/data/videos.json")
    used.append(vid)
    v = VIDEOS[vid]
    title = e(v["title"])
    start = to_sec(ts)
    cap = e(caption.strip()) if caption and caption.strip() else f"From my video: {title}"
    frame = (
        f'<a class="vframe lite" href="https://www.youtube.com/watch?v={vid}&amp;t={start}s" data-yt="{vid}" data-start="{start}" '
        f'aria-label="Play from {ts}: {title}">'
        f'<img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360">'
        f'<span class="play" aria-hidden="true"></span></a>'
    )
    return f'<figure class="video moment">{frame}<figcaption>{cap} <span class="dur">starts at {ts}</span></figcaption></figure>'


def render_shorts(ids, used):
    items = []
    for vid in ids:
        if vid not in VIDEOS:
            sys.exit(f"Unknown video id {vid}")
        used.append(vid)
        v = VIDEOS[vid]
        t = e(v["title"])
        items.append(
            f'<figure class="short"><a class="sframe lite" href="https://www.youtube.com/shorts/{vid}" data-yt="{vid}" aria-label="Play: {t}">'
            f'<img src="https://i.ytimg.com/vi/{vid}/oardefault.jpg" onerror="this.src=\'https://i.ytimg.com/vi/{vid}/hqdefault.jpg\'" alt="" loading="lazy">'
            f'<span class="play" aria-hidden="true"></span></a><figcaption>{t}</figcaption></figure>'
        )
    return '<div class="shorts">' + "".join(items) + "</div>"


def render_cta(key, campaign):
    c = CTAS[key]
    return (
        f'<aside class="cta cta-{key}"><p class="kicker">{e(c["kicker"])}</p>'
        f'<h2 class="cta-title">{e(c["title"])}</h2><p>{e(c["body"])}</p>'
        f'<a class="btn" href="{e(utm(c["url"], campaign, key))}">{e(c["button"])}</a></aside>'
    )


def render_gear(spec, campaign):
    if "|" in spec:
        keys, heading = spec.split("|", 1)
    else:
        keys, heading = spec, "What I recommend for practicing this"
    items = []
    for k in keys.split():
        if k not in GEAR:
            sys.exit(f"Unknown gear key {k} - add it to src/data/gear.json")
        g = GEAR[k]
        items.append(
            f'<li><div class="gear-txt"><span class="gear-label">{e(g["label"])}</span>'
            f'<span class="gear-name">{e(g["name"])}</span><span class="gear-note">{e(g["note"])}</span></div>'
            f'<a class="gear-btn" href="{e(g["url"])}" rel="sponsored nofollow noopener" target="_blank">See it on Amazon</a></li>'
        )
    return (
        f'<aside class="gear"><p class="gear-kicker">What I use</p><p class="gear-h">{e(heading.strip())}</p>'
        f'<ul class="gear-list">{"".join(items)}</ul>'
        f'<p class="gear-disc">These are the same items I recommend to students in my course. I earn a small commission if you buy through these links, at no extra cost to you. '
        f'<a href="/gear/">See everything you need to practice at home</a>.</p></aside>'
    )


def slugify(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def add_heading_ids(body):
    def repl(m):
        attrs, inner = m.group(1), m.group(2)
        if "id=" in attrs:
            return m.group(0)
        return f'<h2 id="{slugify(inner)}"{attrs}>{inner}</h2>'

    return re.sub(r"<h2([^>]*)>(.*?)</h2>", repl, body, flags=re.S)


def build_toc(body):
    heads = [(i, t) for i, a, t in re.findall(r'<h2 id="([^"]+)"([^>]*)>(.*?)</h2>', body, flags=re.S) if "cta-title" not in a]
    if len(heads) < 3:
        return ""
    lis = "".join(f'<li><a href="#{i}">{re.sub(r"<[^>]+>", "", t)}</a></li>' for i, t in heads)
    return f'<nav class="toc" aria-label="On this page"><p class="toc-title">On this page</p><ol>{lis}</ol></nav>'


SCHOOL = json.load(open(os.path.join(SRC, "data", "school.json"), encoding="utf-8"))

# Rail line per section: what the reader is doing on that page, tied to the school.
RAIL_HOOK = {
    "deal": "Want to deal this with me watching?",
    "rules": "Want to practice these rulings on real hands?",
    "career": "Want help getting through your audition?",
    "gear": "Got the gear? Now get the feedback.",
}


def school_when(campaign, content):
    nc = (SCHOOL.get("next_class") or "").strip()
    link = e(utm(MAIN + "/remote-dealer-school", campaign, content + "-date"))
    iso = (SCHOOL.get("next_class_iso") or "").strip()
    if nc and iso:
        # site.js swaps this for the plain link once the date has passed, so it can't go stale.
        return (f'<p class="when" data-until="{e(iso)}" data-fallback="See when the next class starts &rarr;" data-href="{link}">'
                f'Next class starts <strong>{e(nc)}</strong>. <a href="{link}">Details</a></p>')
    if nc:
        return f'<p class="when">Next class starts <strong>{e(nc)}</strong>. <a href="{link}">Details</a></p>'
    return f'<p class="when"><a href="{link}">See when the next class starts &rarr;</a></p>'


RAIL_VIDEO = {"id": "Ljnk9aLZf2Y", "caption": "Two of my students on going from class to dealing WSOP Circuit events"}
RAIL_PROOF = {"text": "A student got hired as a poker dealer one hour after class.", "url": "https://www.youtube.com/watch?v=w8RLdmVwZQo"}


def render_rail(section, campaign, hook=None, course_line=None):
    hook = hook or RAIL_HOOK.get(section, "Want me to watch you deal and correct you live?")
    school = e(utm(MAIN + "/remote-dealer-school", campaign, "rail-school"))
    call = e(utm(MAIN + "/book-pathwaycall", campaign, "rail-call"))
    course = e(utm(MAIN + "/complete-course", campaign, "rail-course"))
    vid = RAIL_VIDEO["id"]
    course_line = course_line or "This guide is one lesson. The Complete Course has all 50+, in order, at your own pace."
    return (
        '<aside class="rail" aria-label="Learn with Marc"><div class="rail-in">'
        '<div class="rail-card rail-school">'
        '<div class="rail-who"><img src="/assets/marc.jpg" alt="Marc Shumsker" width="44" height="44" loading="lazy">'
        f'<p><strong>Marc Shumsker</strong><span>{views_short(CHANNEL["views"])}+ YouTube views since {CHANNEL["since"]}</span><span>10,000+ dealers trained</span></p></div>'
        f'<p class="rail-title">{e(hook)}</p>'
        '<p class="rail-what">That&rsquo;s what <strong>Remote Dealer School</strong> is: my live class on Zoom.</p>'
        '<ul class="rail-list">'
        '<li>8 weeks, in a small group, live with me</li>'
        '<li>You deal on camera and I correct you in real time</li>'
        '<li>Every class is recorded, so you can rewatch your corrections</li>'
        '<li>The last week covers getting hired</li>'
        '</ul>'
        f'<a class="vframe rail-vid" href="https://www.youtube.com/watch?v={vid}" data-yt="{vid}" data-modal aria-label="Play: {e(RAIL_VIDEO["caption"])}">'
        f'<img src="https://i.ytimg.com/vi/{vid}/mqdefault.jpg" alt="" loading="lazy" width="320" height="180"><span class="play" aria-hidden="true"></span></a>'
        f'<p class="rail-vcap"><strong>Watch:</strong> {e(RAIL_VIDEO["caption"])}</p>'
        f'{school_when(campaign, "rail")}'
        f'<a class="btn btn-block" href="{school}">See if it&rsquo;s right for me</a>'
        f'<p class="rail-call">Not sure yet? <a href="{call}">Book a free call with me</a></p>'
        f'<p class="rail-proof"><a href="{e(RAIL_PROOF["url"])}">{e(RAIL_PROOF["text"])}</a></p>'
        '</div>'
        '<div class="rail-card rail-course"><p class="kicker">Learning on your own?</p>'
        f'<p>{e(course_line)} $79/month.</p>'
        f'<a class="rail-link" href="{course}">See the Complete Course &rarr;</a></div>'
        '</div></aside>'
    )


def render_inline_school(section, campaign, hook=None):
    hook = hook or RAIL_HOOK.get(section, "Want me to watch you deal and correct you live?")
    school = e(utm(MAIN + "/remote-dealer-school", campaign, "inline-school"))
    return (
        '<aside class="inline-school" aria-label="Remote Dealer School">'
        '<img src="/assets/marc.jpg" alt="Marc Shumsker" width="48" height="48" loading="lazy">'
        f'<div><p><strong>{e(hook)}</strong> In Remote Dealer School you deal on camera and I correct you live.</p>'
        f'<a href="{school}">See if it&rsquo;s right for you &rarr;</a></div></aside>'
    )


def add_drill_lines(body, campaign):
    link = e(utm(MAIN + "/remote-dealer-school", campaign, "classroom"))
    line = f'<p class="drill"><a href="{link}">We drill exactly this in Remote Dealer School &rarr;</a></p>'
    return re.sub(r'(<div class="classroom">.*?)(</div>)', lambda m: m.group(1) + line + m.group(2), body, flags=re.S)


MANUAL_BOX = (
    '<aside class="manual-box"><img src="/assets/manual-cover.jpg" alt="" width="120" height="158" loading="lazy">'
    '<div><p class="kicker">Free download</p><p class="mb-title">Read a real poker room&rsquo;s dealer procedures manual</p>'
    '<p>The manual a working room handed its dealers: house rules, dealer procedures, the rake and fills. 39 pages, free.</p>'
    '<a class="btn" href="/procedures-manual/">Get the free manual</a></div></aside>'
)


def insert_manual_box(body):
    m = re.search(r'<h2 id="[^"]*"[^>]*>\s*Common questions', body)
    if m:
        return body[:m.start()] + MANUAL_BOX + body[m.start():]
    return body + MANUAL_BOX


def insert_early_school(body, section, campaign, hook=None):
    # Before the 2nd H2 of the body (after the first real section); shown only on narrow screens.
    heads = [m.start() for m in re.finditer(r'<h2 id=', body)]
    if len(heads) < 3:
        return body
    i = heads[1]
    return body[:i] + render_inline_school(section, campaign, hook) + body[i:]


def process_body(body, campaign):
    used = []
    body = re.sub(r"\[\[video ([\w-]{11})\]\]", lambda m: render_video(m.group(1), True, used), body)
    body = re.sub(r"\[\[lite ([\w-]{11})\]\]", lambda m: render_video(m.group(1), False, used), body)
    body = re.sub(r"\[\[moment ([\w-]{11}) (\d+(?::\d\d){1,2})(?:\s*\|([^\]]*))?\]\]",
                  lambda m: render_moment(m.group(1), m.group(2), m.group(3), used), body)
    body = re.sub(r"\[\[shorts ([\w\- ]+)\]\]", lambda m: render_shorts(m.group(1).split(), used), body)
    body = re.sub(r"\[\[cta (\w+)\]\]", lambda m: render_cta(m.group(1), campaign), body)
    body = re.sub(r"\[\[gear ([^\]]+)\]\]", lambda m: render_gear(m.group(1), campaign), body)
    body = body.replace("[[storefront]]", e(GEAR["_storefront"]))
    body = re.sub(r"\[\[stat (\w+)\]\]", lambda m: stat(m.group(1)), body)
    body = add_heading_ids(body)
    body = body.replace("[[toc]]", build_toc(body))
    return body, used


def read_page(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*", raw, flags=re.S)
    if not m:
        sys.exit(f"{path}: missing <!--meta {{...}} --> block")
    meta = json.loads(m.group(1))
    return meta, raw[m.end():]


def url_for(relpath):
    rel = relpath[:-5]  # strip .html
    if rel == "index":
        return "/"
    if rel.endswith("/index"):
        return "/" + rel[: -len("index")]
    return "/" + rel + "/"


def out_path(url):
    return os.path.join(ROOT, url.strip("/"), "index.html") if url != "/" else os.path.join(ROOT, "index.html")


def header(current_section):
    links = []
    for key in ("deal", "career", "rules", "gear", "about"):
        if key not in PUBLISHED_SECTIONS:
            continue
        s = SECTIONS[key]
        cur = ' aria-current="page"' if key == current_section else ""
        links.append(f'<a href="{s["path"]}"{cur}>{s["name"]}</a>')
    free = utm(CTAS["free"]["url"], "nav", "free")
    return (
        '<header class="site"><div class="wrap">'
        '<a class="brand" href="/"><span class="brand-mark" aria-hidden="true">&#9824;</span>'
        '<span class="brand-text">True Poker Dealer<small>Learn to deal poker</small></span></a>'
        f'<nav class="primary">{"".join(links)}<a class="btn btn-sm" href="{e(free)}">Free lessons</a></nav>'
        "</div></header>"
    )


def footer():
    yr = date.today().year
    return (
        '<footer class="site"><div class="wrap">'
        '<div class="foot-cols">'
        '<div><p class="foot-brand">True Poker Dealer</p><p>Learn to deal poker the way real poker rooms run, taught by '
        '<a href="/about/marc-shumsker/">Marc Shumsker</a>, a dealer, floor supervisor and shift manager who has hired and trained thousands of dealers.</p></div>'
        f'<div><p class="foot-h">Train with Marc</p><a href="/procedures-manual/">Free procedures manual</a><a href="{e(utm(MAIN + "/freelessons", "footer", "free"))}">Free lessons</a>'
        f'<a href="{e(utm(MAIN + "/complete-course", "footer", "course"))}">The Complete Course</a>'
        f'<a href="{e(utm(MAIN + "/remote-dealer-school", "footer", "school"))}">Remote Dealer School</a></div>'
        f'<div><p class="foot-h">Follow</p><a href="{YT_CHANNEL}">YouTube</a><a href="https://instagram.com/truepokerdealer">Instagram</a>'
        '<a href="https://tiktok.com/truepokerdealer">TikTok</a></div>'
        "</div>"
        '<p class="fine">As an Amazon Associate, True Poker Dealer earns from qualifying purchases. '
        f'<a href="{MAIN}/privacy-policy">Privacy</a> &middot; <a href="{MAIN}/terms-and-conditions">Terms</a> &middot; &copy; {yr} True Poker Dealer</p>'
        "</div></footer>"
    )


def page_shell(meta, url, body_html, schema_graph, section):
    title = meta["title"]
    desc = meta["description"]
    canonical = SITE + url
    og_img = meta.get("og_image") or (
        f"https://i.ytimg.com/vi/{meta['hero_video']}/maxresdefault.jpg" if meta.get("hero_video") else None
    )
    robots = '<meta name="robots" content="noindex">' if meta.get("noindex") else ""
    og = (
        f'<meta property="og:type" content="{"article" if meta.get("type") == "article" else "website"}">'
        f'<meta property="og:title" content="{e(meta.get("og_title", title))}">'
        f'<meta property="og:description" content="{e(desc)}">'
        f'<meta property="og:url" content="{canonical}">'
        '<meta property="og:site_name" content="True Poker Dealer">'
        + (f'<meta property="og:image" content="{og_img}">' if og_img else "")
        + '<meta name="twitter:card" content="summary_large_image">'
    )
    ld = json.dumps({"@context": "https://schema.org", "@graph": schema_graph}, ensure_ascii=False, indent=1)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
{robots}{og}
<link rel="preconnect" href="https://i.ytimg.com">
<link rel="stylesheet" href="/assets/site.css?v={ASSET_VERSION}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<script type="application/ld+json">
{ld}
</script>
</head>
<body class="t-{meta.get('type', 'page')}">
<a class="skip" href="#main">Skip to content</a>
{header(section)}
<main id="main">
{body_html}
</main>
{footer()}
<script src="/assets/site.js?v={ASSET_VERSION}" defer></script>
<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "5f325265caf240aabf0da79f32a64185"}}'></script>
</body>
</html>
"""


def breadcrumbs(meta, url, section):
    crumbs = [("Home", "/")]
    if section and section in SECTIONS and url != SECTIONS[section]["path"]:
        crumbs.append((SECTIONS[section]["name"], SECTIONS[section]["path"]))
    crumbs.append((meta.get("crumb", meta.get("h1", meta["title"])), url))
    html_ = '<nav class="crumbs" aria-label="Breadcrumb"><ol>' + "".join(
        f'<li><a href="{u}">{e(n)}</a></li>' if i < len(crumbs) - 1 else f'<li aria-current="page">{e(n)}</li>'
        for i, (n, u) in enumerate(crumbs)
    ) + "</ol></nav>"
    schema = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(crumbs)
        ],
    }
    return html_, schema


def nice_date(d):
    y, m, dd = map(int, d.split("-"))
    return date(y, m, dd).strftime("%B %-d, %Y")


def author_box():
    return (
        '<aside class="author-box"><img src="/assets/marc.jpg" alt="Marc Shumsker" width="96" height="96" loading="lazy" onerror="this.remove()">'
        '<div><p class="ab-name">Written by Marc Shumsker</p>'
        "<p>I started dealing in 2007 and have worked as a dealer, floor supervisor and shift manager in Washington, Florida and Texas. "
        "As a shift manager I ran over 1,000 live dealer auditions and did the hiring. I started True Poker Dealer on YouTube in 2012, "
        f"where my lessons now have {views_long(CHANNEL['views'])} views, and I still "
        'pick up dealing shifts in Texas. <a href="/about/marc-shumsker/">More about me</a></p></div></aside>'
    )


def build_page(relpath, meta, raw_body, all_pages):
    url = url_for(relpath)
    section = meta.get("section") or (url.strip("/").split("/")[0] if url != "/" else None)
    campaign = url.strip("/").replace("/", "-") or "home"
    body, used = process_body(raw_body, campaign)
    ptype = meta.get("type", "page")
    graph = [ORG]
    crumbs_html, crumbs_schema = ("", None) if url == "/" else breadcrumbs(meta, url, section)
    if crumbs_schema:
        graph.append(crumbs_schema)

    if ptype == "article":
        mins = max(1, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 230))
        updated = meta["updated"]
        byline = (
            f'<p class="byline">By <a href="/about/marc-shumsker/">Marc Shumsker</a> &middot; '
            f'Updated <time datetime="{updated}">{nice_date(updated)}</time> &middot; {mins} min read</p>'
        )
        head = (
            f'<header class="article-head">{crumbs_html}<h1>{meta.get("h1", meta["title"])}</h1>'
            f'<p class="dek">{meta["dek"]}</p>{byline}</header>'
        )
        related = ""
        if meta.get("related"):
            items = []
            for r in meta["related"]:
                p = all_pages.get(r)
                if p:
                    items.append(f'<li><a href="{r}">{e(p.get("h1", p["title"]))}</a></li>')
            if items:
                related = f'<nav class="related"><p class="rel-title">Keep going</p><ul>{"".join(items)}</ul></nav>'
        section = url.strip("/").split("/")[0]
        body = add_drill_lines(body, campaign)
        if url != "/procedures-manual/":
            body = insert_manual_box(body)
        body = insert_early_school(body, section, campaign, meta.get("rail_hook"))
        body_html = (
            f'<div class="with-rail"><article class="article">{head}<div class="prose">{body}</div>{author_box()}{related}</article>'
            f'{render_rail(section, campaign, meta.get("rail_hook"), meta.get("rail_course"))}</div>'
        )
        art = {
            "@type": "Article",
            "headline": meta.get("h1", meta["title"]),
            "description": meta["description"],
            "author": AUTHOR,
            "publisher": {"@id": ORG["@id"]},
            "datePublished": meta.get("published", updated),
            "dateModified": updated,
            "mainEntityOfPage": SITE + url,
        }
        if meta.get("hero_video"):
            art["image"] = f"https://i.ytimg.com/vi/{meta['hero_video']}/maxresdefault.jpg"
        if used:
            art["video"] = [video_schema(v) for v in dict.fromkeys(used)]
        graph.append(art)
    else:
        if crumbs_html:
            body = crumbs_html + body
        body_html = f'<div class="page page-{ptype}">{body}</div>'
        if ptype == "profile":
            graph.append({"@type": "ProfilePage", "mainEntity": AUTHOR, "url": SITE + url})
        else:
            graph.append({"@type": "WebPage", "name": meta["title"], "url": SITE + url, "description": meta["description"]})
        if used:
            graph.extend(video_schema(v) for v in dict.fromkeys(used))
        if url == "/":
            graph.append({"@type": "WebSite", "name": "True Poker Dealer: Learn to Deal Poker", "url": SITE + "/"})

    out = out_path(url)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page_shell(meta, url, body_html, graph, section))
    return url


def main():
    global PUBLISHED_SECTIONS, ASSET_VERSION
    pages = {}
    for dirpath, _, files in os.walk(PAGES):
        for fn in sorted(files):
            if fn.endswith(".html"):
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, PAGES).replace(os.sep, "/")
                meta, body = read_page(full)
                if meta.get("draft"):
                    continue
                pages[rel] = (meta, body)
    PUBLISHED_SECTIONS = {url_for(r).strip("/").split("/")[0] for r in pages if url_for(r) != "/"}
    ASSET_VERSION = hashlib.md5(
        (open(os.path.join(ROOT, "assets", "site.css"), "rb").read() + open(os.path.join(ROOT, "assets", "site.js"), "rb").read())
    ).hexdigest()[:8]
    by_url = {url_for(r): m for r, (m, _) in pages.items()}

    # Hub pages can list their section's articles with [[list SECTION]].
    def list_section(sec):
        items = sorted(
            ((u, m) for u, m in by_url.items() if u.startswith(f"/{sec}/") and u != f"/{sec}/" and m.get("type") == "article"),
            key=lambda x: x[1].get("order", 999),
        )
        return '<ul class="cards">' + "".join(
            f'<li><a class="card" href="{u}"><span class="card-kicker">{e(m.get("kicker", ""))}</span>'
            f'<span class="card-title">{e(m.get("h1", m["title"]))}</span><span class="card-dek">{e(m.get("card", m["description"]))}</span></a></li>'
            for u, m in items
        ) + "</ul>"

    for d in GENERATED_DIRS:
        p = os.path.join(ROOT, d)
        if os.path.isdir(p):
            shutil.rmtree(p)

    built = []
    for rel, (meta, body) in pages.items():
        body = re.sub(r"\[\[list (\w+)\]\]", lambda m: list_section(m.group(1)), body)
        built.append((build_page(rel, meta, body, by_url), meta))

    # Real 404 page. Without it, Cloudflare Pages serves the homepage for unknown
    # URLs with a 200 status, which Google treats as soft 404s.
    nf_meta = {"title": "Page not found | True Poker Dealer", "description": "This page doesn't exist.", "noindex": True, "type": "page"}
    nf_body = (
        '<div class="page"><h1>That page isn\'t here</h1><p class="lede">It may have moved. '
        'Try the <a href="/deal/">How to Deal</a> guides or head back to the <a href="/">homepage</a>.</p></div>'
    )
    with open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8") as f:
        f.write(page_shell(nf_meta, "/404", nf_body, [ORG], None))

    urls = sorted(built, key=lambda x: (x[0] != "/", x[0]))
    with open(os.path.join(ROOT, "sitemap.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u, m in urls:
            if m.get("noindex"):
                continue
            lm = f"<lastmod>{m['updated']}</lastmod>" if m.get("updated") else ""
            f.write(f"  <url><loc>{SITE}{u}</loc>{lm}</url>\n")
        f.write("</urlset>\n")
    print(f"Built {len(built)} pages:")
    for u, _ in urls:
        print("  ", u)


if __name__ == "__main__":
    main()
