# Playbook: learn.truepokerdealer.com ("The Dealer's Handbook")

You are writing and maintaining Marc Shumsker's SEO content site for True Poker Dealer. Read this whole file before doing anything. The content plan, with every page and its status, is in `docs/content-plan.md`. Update both files when something changes.

## What this site is for
- The most authoritative resource anywhere on how to deal poker, built only from what Marc actually teaches.
- It exists to earn money: the **Complete Course** ($79/mo), **Remote Dealer School** (live Zoom classes), **Amazon affiliate** gear, and the free **pathway call** that leads into both. SEO does the work of bringing people in.
- Marc has delegated SEO and site-structure decisions to Claude. He wants opinions and suggestions, not just execution.

## Who Marc is (facts you can rely on)
He has worked in casinos since 2007: blackjack and table games first, then poker. He worked in Washington State, then worked the floor full time in South Florida at a Seminole property, and helped open the 29-table poker room at Calder Casino, where he became shift manager and ran 1,000+ live dealer auditions. He founded True Poker Dealer around 2011–2012. His YouTube shuffle lesson has 1.4M+ views and the channel has about 33K subscribers. He finished the Complete Course in 2020, and today he teaches Remote Dealer School and still picks up dealing shifts in Texas. He hired Victor as a chip runner, and Victor is now COO of Texas Card House; Marc OK'd naming him.

## Non-negotiable content rules
1. **Every claim comes from Marc's material**: lesson transcripts, class transcripts, his YouTube videos, or the correction log. If you can't find a source for a claim, cut it. No generic poker-dealer filler, and no invented stories, numbers or quotes.
2. **First-person Marc voice, bylined to him.** Plain, direct, practical, the way he talks in class. Every page starts with `"review": "pending"` in its meta until Marc reads it. Add it to the review list at the bottom of `docs/content-plan.md`.
3. **No student names on public pages. Ever.** Describe class moments anonymously ("a student", "nearly every student").
4. **Class video clips (LaCie / Vimeo) are used only with Marc's explicit approval.** Public YouTube videos can be embedded anywhere freely.
5. **No thin pages.** A page is published only when it's better than anything else ranking for that topic. Hubs show "coming next" cards (non-links) for planned pages, never stub pages.
6. **Affiliate products:** only items Marc actually recommends, from `src/data/gear.json` (the source is the "Materials Needed" lesson in the Complete Course on Ivorey). Use them where genuinely helpful. Never invent a recommendation. Links get `rel="sponsored nofollow"` and the inline disclosure, which the shortcode adds automatically.
7. **truepokerdealer.com is off-limits.** It's GoHighLevel/Ivorey, where students log in to paid courses. Don't change it unless Marc has explicitly approved a specific plan.

## Where the source material is
- **Private repo `Jerseymatch/tpd-knowledge`.** It holds class transcripts by cohort (`transcripts/<Month Year>/<MM_DD_YY>.srt`), edited lesson transcripts (`transcripts/Remote School Edited Lessons/`, `transcripts/TPD Course/`), `correction_analysis/detail_log.csv` (every correction moment, with timestamp, topic and a verbatim evidence quote; the `generalized=true` rows are recurring issues Marc calls common), `clip_index.csv` (clipped correction moments by category), and `manifest.csv`. **It contains student names. Never copy raw text from it into this public repo.**
- If tpd-knowledge isn't attached, it's also on Marc's Mac under `My Drive/Training Videos` (via the device bridge).
- **Best sources per topic:** the Remote School edited lessons (1 Shuffle, 2 Pitch, 3 Chips, 4 Bank, 5 Buy-ins/Cheque change/Color-ups, 6 Intro to poker, 7 Flop/turn/river, 8 Dealing a hand of 1-2 NL, 9 Cards speak & one player per hand, 10 Cash games, 11 Bets/calls/making change, 12 Showdown, 13 Rake/promo/tips, 14 Technical rules of betting, 15 Misdeals). Use the class transcripts and correction log for "what I correct in class" and real teaching moments.
- **Video metadata** (title, upload date, duration) is in `src/data/videos.json`. To add a video, fetch its real upload date and duration from YouTube first. Never guess dates.

## How to build a page (the pipeline)
1. **Pick the next page** from `docs/content-plan.md`.
2. **Gather sources.** Read the main lesson transcript in full, then search the correction log and class transcripts for the topic. Write a short source brief (claims → where they came from) in your scratch space.
3. **Draft** `src/pages/<section>/<slug>.html` following the template below.
4. **Independent fact check.** Spawn a separate agent that hasn't seen your draft process. Give it the draft and the source files, and have it list every claim that isn't supported by the sources, or that contradicts them. Fix or cut each one. This is required. The pages carry Marc's name.
5. **Build and check:** `python3 src/build.py && python3 scripts/check.py` (link, schema, shortcode and leftover-marker checks). Screenshot the page at 390px and 1280px wide and look at it.
6. **Publish:** commit to `main` and push (Cloudflare deploys in about 3 minutes). Confirm the page is live, update `docs/content-plan.md` (status + review list), and update hub "coming next" cards.

## Page template (see existing guides in `src/pages/deal/`)
- Meta JSON: `title` (≤ ~65 chars + " | True Poker Dealer"), `h1`, `crumb`, `description` (~150 chars), `dek`, `kicker`, `card`, `type: "article"`, `order`, `updated`, `published`, `hero_video`, `review`, `related`.
- Body: a 1–2 paragraph intro on why it matters → `[[video ID]]` (primary) → `[[toc]]` → H2 sections with steps → `<div class="classroom">` "What I correct in class" callouts from the correction log → `[[shorts ...]]`/`[[lite ...]]` where they help → practice section → `[[gear ... | heading]]` if relevant → `[[cta free]]` → "Common questions" H3 Q&As (real search phrasing, short direct answers) → `[[cta course]]` (or `school` / `call` on career and audition pages).
- Link between guides generously (procedure ↔ procedure, guide ↔ /gear/).

## Shortcodes and build
See the docstring at the top of `src/build.py`: `[[video]]`, `[[lite]]`, `[[shorts]]`, `[[cta free|course|school|call]]`, `[[gear keys | heading]]`, `[[toc]]`, `[[list section]]`, `[[storefront]]`. The output is generated into the repo root, and both source and output get committed.

## Infrastructure
- GitHub `Jerseymatch/tpd-learn-site` (public). The Claude GitHub App has access. Cloudflare Pages auto-deploys `main`. A real `404.html` exists. `_redirects` sends the old `/guide/*` URLs to `/deal/`.
- Google Search Console: Domain property `truepokerdealer.com` under truepokerdealer@gmail.com. The sitemap is submitted. Re-submit after big batches.
- Long-term plan: move the content onto truepokerdealer.com subfolders, with the student portal on its own subdomain. This needs Marc's approval and a careful plan, because student logins are involved.
