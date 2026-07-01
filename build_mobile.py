#!/usr/bin/env python3
"""Extract clean, ordered content from the frozen Duda-ONE desktop mirror so we
can author dedicated mobile pages (no dm* desktop DOM). Emits one JSON blob of
content blocks per page to scratchpad for inspection / to drive the generator."""
import re, json, os, sys
from html.parser import HTMLParser

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")
PAGES = ["", "about", "ministries", "services", "giving", "plan-your-visit",
         "media", "faq", "events", "get-connected", "get-in-touch",
         "newsletter", "tuesday-services"]

HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
NAV_TEXT = {"home", "about", "ministries", "services", "giving", "more",
            "plan your visit", "contact", "faq", "menu"}


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def clean_body(html):
    m = re.search(r"<body\b.*?>(.*)</body>", html, re.S)
    body = m.group(1) if m else html
    # drop non-content chrome
    body = re.sub(r"<script\b.*?</script>", "", body, flags=re.S | re.I)
    body = re.sub(r"<style\b.*?</style>", "", body, flags=re.S | re.I)
    body = re.sub(r"<svg\b.*?</svg>", "", body, flags=re.S | re.I)
    body = re.sub(r"<noscript\b.*?</noscript>", "", body, flags=re.S | re.I)
    body = re.sub(r"<nav\b.*?</nav>", "", body, flags=re.S | re.I)
    # drop the fixed header container (Duda header) if present
    body = re.sub(r'<div[^>]*id="hcontainer".*?</header>', "", body, flags=re.S | re.I)
    return body


# one combined scanner: headings, paragraphs, images, buttons, in document order
TOKEN = re.compile(
    r'(?P<h><h(?P<hl>[1-6])\b[^>]*>(?P<htext>.*?)</h(?P=hl)>)'
    r'|(?P<img><img\b[^>]*>)'
    r'|(?P<btn><a\b[^>]*class="[^"]*(?:dmButtonLink|flexButton|dm-button)[^"]*"[^>]*>(?P<btext>.*?)</a>)'
    r'|(?P<p><p\b[^>]*>(?P<ptext>.*?)</p>)',
    re.S | re.I)


def extract(page):
    path = os.path.join(SITE, page, "index.html") if page else os.path.join(SITE, "index.html")
    html = open(path, encoding="utf-8").read()
    body = clean_body(html)
    blocks = []
    for m in TOKEN.finditer(body):
        if m.group("h"):
            t = strip_tags(m.group("htext"))
            if t and t.lower() not in NAV_TEXT:
                blocks.append({"type": "h", "level": int(m.group("hl")), "text": t})
        elif m.group("img"):
            src = re.search(r'\bsrc="([^"]+)"', m.group("img"))
            alt = re.search(r'\balt="([^"]*)"', m.group("img"))
            src = src.group(1) if src else ""
            if src.startswith("http") and "cdn-website" in src and "logo" not in src.lower():
                blocks.append({"type": "img", "src": src, "alt": alt.group(1) if alt else ""})
        elif m.group("btn"):
            href = re.search(r'\bhref="([^"]*)"', m.group("btn"))
            t = strip_tags(m.group("btext"))
            if t:
                blocks.append({"type": "button", "text": t, "href": href.group(1) if href else "#"})
        elif m.group("p"):
            t = strip_tags(m.group("ptext"))
            if t and t.lower() not in NAV_TEXT:
                blocks.append({"type": "p", "text": t})
    return dedupe(blocks)


def dedupe(blocks):
    out, seen = [], set()
    for b in blocks:
        key = (b["type"], b.get("text", ""), b.get("src", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(b)
    return out


# ============================================================
#  Page generation — author dedicated, standalone mobile pages.
# ============================================================
import html as _html

PHONE = "860-205-8432"
EMAIL = "connect@lifewayfwc.com"
LOGO = "https://lirp.cdn-website.com/a78c0b5c/dms3rep/multi/opt/logo01-1920w.png"
FACEBOOK = "https://www.facebook.com/lifewayfamily.worshipcenter"
YOUTUBE = "https://www.youtube.com/@ApostleMehranPayandeh"

NAV = [("Home", "/mobile/"), ("About", "/mobile/about"), ("Ministries", "/mobile/ministries"),
       ("Services", "/mobile/services"), ("Giving", "/mobile/giving"),
       ("Plan Your Visit", "/mobile/plan-your-visit"),
       ("Contact", "/mobile/get-in-touch"), ("FAQ", "/mobile/faq")]

# curated hero copy per page (title/eyebrow/subtitle); content flows below
META = {
    "home": ("Eternal Truth", "LifeWay Family Worship Center",
             "A vibrant church community in Greater Hartford, CT — rooted in faith, growing together in God's love."),
    "about": ("About Our Church", "Who We Are",
              "Meet the heart, leadership, and beliefs behind LifeWay Family Worship Center."),
    "ministries": ("Ministries", "Get Connected",
                   "We make it easy to get and stay connected as you journey through life."),
    "services": ("Services", "Come & Fellowship With Us",
                 "Gather with us in person or online for prayer, worship, and the Word."),
    "giving": ("Giving", "Give With a Grateful Heart",
               "Your generosity fuels the mission and blesses our community and beyond."),
    "plan-your-visit": ("Plan Your Visit", "We Can't Wait to Meet You",
                        "Everything you need to know before your first visit."),
    "media": ("Media & Messages", "Watch & Listen",
              "Hear God's Word delivered by Pastor through the Holy Spirit."),
    "faq": ("FAQ", "Questions & Answers",
            "Answers to the questions we're asked most about worship and church life."),
    "events": ("Events", "What's Happening",
               "Stay in the loop on upcoming gatherings and special services."),
    "get-connected": ("Get Connected", "Join the Family",
                      "Take your next step and get plugged in with our church family."),
    "get-in-touch": ("Get in Touch", "We'd Love to Hear From You",
                     "Reach out with a question, a prayer request, or just to say hello."),
    "newsletter": ("Newsletter", "Stay Connected",
                   "Get updates, encouragement, and news from LifeWay in your inbox."),
    "tuesday-services": ("Tuesday Services", "Midweek Worship",
                         "Join us Tuesday evenings to be refreshed in the middle of your week."),
}

JUNK = {"contact info", "phone:", "email:", "phone", "email",
        "all rights reserved | lifeway family worship center",
        PHONE, " " + PHONE, EMAIL}


def clean_text(t):
    t = _html.unescape(t or "")
    t = t.replace("﻿", "").replace(" ", " ")
    return re.sub(r"\s+", " ", t).strip()


def is_junk(t):
    low = t.lower().strip()
    if "carlisle first methodist" in low:  # stray demo-video title from the template
        return True
    return (not low or low in JUNK or PHONE in t or EMAIL in low
            or low.rstrip(":") in {"phone", "email", "contact info"}
            or set(low) <= set(" .,-|"))


def fix_href(h):
    if not h:
        return "#"
    if h.startswith(("http", "tel:", "mailto:")):
        return h
    if h.startswith("#") or h in ("/#Contact",):
        return "/mobile/get-in-touch"
    if h.startswith("/#"):
        return "/mobile/get-in-touch"
    if h.startswith("/"):
        return "/mobile" + ("" if h == "/" else h) + ("/" if h == "/" else "")
    return h


def group_items(blocks):
    items, cur, hero_btns, eyebrow = [], None, [], None

    def new(title=None, level=3, img=None):
        nonlocal cur, eyebrow
        cur = {"eyebrow": eyebrow, "title": title, "level": level, "paras": [], "img": img, "buttons": []}
        items.append(cur); eyebrow = None
        return cur

    for b in blocks:
        if b["type"] == "h":
            t = clean_text(b["text"])
            if is_junk(t):
                continue
            if b["level"] >= 5 and (cur is None or cur["title"]):
                eyebrow = t; continue
            new(title=t, level=b["level"])
        elif b["type"] == "p":
            t = clean_text(b["text"])
            if is_junk(t):
                continue
            if cur is None:
                new()
            cur["paras"].append(t)
        elif b["type"] == "img":
            if cur is None or cur["img"] or cur["paras"] or cur["title"]:
                new(img=b)
            else:
                cur["img"] = b
        elif b["type"] == "button":
            t = clean_text(b["text"])
            href = fix_href(b["href"])
            if cur is None:
                hero_btns.append((t, href))
            else:
                cur["buttons"].append((t, href))
    # drop empty items
    items = [it for it in items if it["title"] or it["paras"] or it["img"] or it["buttons"]]
    return items, hero_btns


def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_card(it):
    parts = ['<div class="m-card">']
    if it["img"]:
        parts.append(f'<img class="m-card__img" src="{it["img"]["src"]}" alt="{esc(it["img"].get("alt",""))}" loading="lazy">')
    if it["eyebrow"]:
        parts.append(f'<p class="m-eyebrow" style="text-align:left">{esc(it["eyebrow"])}</p>')
    if it["title"]:
        parts.append(f'<h3>{esc(it["title"])}</h3>')
    for p in it["paras"]:
        parts.append(f'<p>{esc(p)}</p>')
    if it["buttons"]:
        parts.append('<div class="m-btn-row" style="justify-content:flex-start">')
        for t, href in it["buttons"]:
            parts.append(f'<a class="m-btn" href="{href}">{esc(t)}</a>')
        parts.append('</div>')
    parts.append('</div>')
    return "".join(parts)


def render_nav(current):
    out = ['<nav class="m-nav" aria-label="Mobile navigation">']
    for label, href in NAV:
        cls = ' class="is-current"' if href.rstrip("/") == current.rstrip("/") else ""
        out.append(f'<a href="{href}"{cls}>{label}</a>')
    out.append('</nav>')
    return "\n".join(out)


FB_SVG = '<svg viewBox="0 0 24 24"><path d="M13 22v-8h3l.5-3.5H13V8.3c0-1 .3-1.7 1.8-1.7H16.6V3.4C16.3 3.4 15.2 3.3 14 3.3c-2.6 0-4.3 1.6-4.3 4.5v2.7H6.7V14h3V22h3.3z"/></svg>'
YT_SVG = '<svg viewBox="0 0 24 24"><path d="M23 8.2a3 3 0 0 0-2.1-2.1C19 5.6 12 5.6 12 5.6s-7 0-8.9.5A3 3 0 0 0 1 8.2 31 31 0 0 0 .6 12 31 31 0 0 0 1 15.8a3 3 0 0 0 2.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .4-3.8 31 31 0 0 0-.4-3.8zM9.8 15.3V8.7l5.7 3.3-5.7 3.3z"/></svg>'
MAIL_SVG = '<svg viewBox="0 0 24 24"><path d="M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm0 4-8 5-8-5V6l8 5 8-5v2z"/></svg>'
PHONE_SVG = '<svg viewBox="0 0 24 24"><path d="M6.6 10.8a15 15 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.2 11 11 0 0 0 3.5.6 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1 11 11 0 0 0 .6 3.5 1 1 0 0 1-.2 1l-2.3 2.3z"/></svg>'


def render_footer():
    return f'''<footer class="m-footer">
  <img class="m-footer__logo" src="{LOGO}" alt="LifeWay Family Worship Center">
  <div class="m-social">
    <a href="{FACEBOOK}" aria-label="Facebook">{FB_SVG}</a>
    <a href="{YOUTUBE}" aria-label="YouTube">{YT_SVG}</a>
    <a href="mailto:{EMAIL}" aria-label="Email">{MAIL_SVG}</a>
    <a href="tel:+1{PHONE.replace('-','')}" aria-label="Call">{PHONE_SVG}</a>
  </div>
  <div class="m-footer__row"><h4>Phone</h4><a href="tel:+1{PHONE.replace('-','')}">{PHONE}</a></div>
  <div class="m-footer__row"><h4>Email</h4><a href="mailto:{EMAIL}">{EMAIL}</a></div>
  <p class="m-footer__legal">© {{year}} LifeWay Family Worship Center. All Rights Reserved.</p>
</footer>'''


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def polish_items(items, hero_title, hero_eyebrow):
    # 1) drop leading title-only cards that just echo the hero
    dup = {_norm(hero_title), _norm(hero_eyebrow)}
    while items:
        it = items[0]
        bare = it["title"] and not it["paras"] and not it["img"] and not it["buttons"]
        if bare and _norm(it["title"]) in dup:
            items.pop(0)
        else:
            break
    # 2) fold a title-only card into the next card (becomes its heading/kicker)
    out = []
    i = 0
    while i < len(items):
        it = items[i]
        bare = it["title"] and not it["paras"] and not it["img"] and not it["buttons"]
        if bare and i + 1 < len(items):
            nxt = items[i + 1]
            if not nxt["title"]:
                nxt["title"] = it["title"]
            elif not nxt["eyebrow"]:
                nxt["eyebrow"] = it["title"]
            i += 1
            continue
        # 3) drop orphan label cards (no title/img/button, only tiny scraps)
        if (not it["title"] and not it["img"] and not it["buttons"]
                and sum(len(p) for p in it["paras"]) < 60):
            i += 1
            continue
        out.append(it)
        i += 1
    return out


def contact_card():
    return ('<div class="m-card"><h3>Reach Out to Us</h3>'
            '<p>We\'d love to connect. Call or email us and a member of our team '
            'will get back to you.</p>'
            '<div class="m-btn-row" style="justify-content:flex-start">'
            f'<a class="m-btn" href="tel:+1{PHONE.replace("-","")}">Call {PHONE}</a>'
            f'<a class="m-btn m-btn--ghost" style="color:var(--blue);border-color:var(--blue)" href="mailto:{EMAIL}">Email Us</a>'
            '</div></div>')


CDN = "https://lirp.cdn-website.com/a78c0b5c/dms3rep/multi/opt/"


def curated_home():
    """The home page is a dense mosaic of tiny Duda overlays that the generic
    extractor fragments; author it explicitly for a clean, intentional flow."""
    def item(title=None, eyebrow=None, paras=None, img=None, alt="", buttons=None):
        return {"eyebrow": eyebrow, "title": title, "level": 3,
                "paras": paras or [], "img": {"src": CDN + img, "alt": alt} if img else None,
                "buttons": buttons or []}
    items = [
        item(title="Discover a Vibrant Church Community", eyebrow="Join Us Every Week",
             img="IMG_6947-d3b7298b-1920w.jpeg", alt="Pastor preaching",
             paras=["Join a community rooted in faith and purpose, where we grow together in "
                    "God's love, support one another, and fulfill His calling for our lives. "
                    "Together, we strengthen our bonds, share in the joy of fellowship, and "
                    "empower each other to live out our faith with passion and conviction."]),
        item(title="Watch Our Latest Message", eyebrow="Discover a Message",
             paras=["“But when he, the Spirit of truth, comes, he will guide you into all "
                    "the truth. He will not speak on his own; he will speak only what he hears, "
                    "and he will tell you what is yet to come.”",
                    "— John 16:13 (NIV)"],
             buttons=[("Watch Services", "/mobile/services")]),
        item(title="Eternal Sonship Academy", eyebrow="Download Our Mobile App",
             img="eternal-sonship-academy-1920w.png", alt="Eternal Sonship Academy app",
             paras=["We offer courses, workshops, and resources based on biblical truth to "
                    "deepen spiritual understanding, strengthen faith, and build leadership skills."],
             buttons=[("Apple Store", "https://apps.apple.com/us/app/eternal-sonship-academy/id6746934635"),
                      ("Google Play", "https://play.google.com/store/search?q=Eternal%20Sonship%20Academy&c=apps")]),
        item(title="Lifeway 365",
             paras=["Lifeway 365 is a structured daily scripture-reading framework designed to "
                    "guide you toward deeper spiritual understanding and enlightenment throughout "
                    "the year."]),
        item(title="Guiding Faithful Leaders", eyebrow="Mentorship",
             paras=["Our mentorship program builds personalized relationships that emphasize "
                    "guidance, accountability, and spiritual development tailored for leaders at "
                    "various stages of their journey."],
             buttons=[("Find Out More", "/mobile/get-in-touch")]),
        item(title="Transformative Training for Spiritual Growth",
             eyebrow="Deepen Your Understanding of the Bible",
             paras=["Our training programs are designed to fortify your understanding of the Bible "
                    "and enhance your spiritual insight through engaging courses and immersive study.",
                    "Offering a comprehensive approach to spiritual growth, our training division is "
                    "dedicated to guiding you on the path to fulfilling your God-given potential."],
             buttons=[("Check Our FAQs", "/mobile/faq")]),
        item(title="Watch Teachings & Services", img="2-fff9ef86-1920w.png", alt="Teachings",
             paras=["Hear God's Word delivered by Pastor through the Holy Spirit."],
             buttons=[("Watch Now", "/mobile/services")]),
        item(title="Looking For A Bible Study?", img="1-f9329f42-1920w.png", alt="Bible study",
             paras=["This is the most important question that will impact your eternity."],
             buttons=[("Plan Your Visit", "/mobile/plan-your-visit")]),
        item(title="Submit a Prayer Request", img="3-de34e1c2-1920w.png", alt="Prayer",
             paras=["Need prayer? Please submit your prayer request to our pastor."],
             buttons=[("Request Prayer", "/mobile/get-in-touch")]),
    ]
    return items, [("Get Started", "/mobile/get-in-touch")]


def render_page(page, blocks):
    key = page or "home"
    title, eyebrow, subtitle = META[key]
    current = "/mobile/" if key == "home" else f"/mobile/{key}"
    if key == "home":
        items, hero_btns = curated_home()
    else:
        items, hero_btns = group_items(blocks)
        items = polish_items(items, title, eyebrow)

    hero_cta = ""
    if hero_btns:
        hero_cta = '<div class="m-btn-row">' + "".join(
            f'<a class="m-btn{" m-btn--ghost" if i else ""}" href="{h}">{esc(t)}</a>'
            for i, (t, h) in enumerate(hero_btns[:2])) + '</div>'

    # sparse pages (mostly JS form widgets that can't be mirrored) get a
    # useful fallback so they never render an empty grey band.
    if len(items) < 2:
        items.append({"eyebrow": None, "title": None, "level": 3, "paras": [], "img": None, "buttons": []})
        cards_html = "\n".join(render_card(it) for it in items if it["title"] or it["paras"] or it["img"] or it["buttons"])
        cards_html += contact_card()
    else:
        cards_html = "\n".join(render_card(it) for it in items)
    cards = cards_html
    doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<script src="/device-redirect.js?v=20260701m2"></script>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)} — LifeWay Family Worship Center</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Mulish:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/mobile/m.css?v=20260701m2">
</head>
<body data-page="{key}">
<header class="m-header">
  <a class="m-header__logo" href="/mobile/" aria-label="Home"><img src="{LOGO}" alt="LifeWay Family Worship Center"></a>
  <button class="m-burger" type="button" aria-label="Menu" aria-expanded="false"><span></span><span></span><span></span></button>
</header>
{render_nav(current)}
<main>
  <section class="m-hero">
    <div class="m-hero__inner">
      <p class="m-hero__eyebrow">{esc(eyebrow)}</p>
      <h1>{esc(title)}</h1>
      <p>{esc(subtitle)}</p>
      {hero_cta}
    </div>
  </section>
  <section class="m-section">
    <div class="m-wrap">
      <div class="m-cards">
        {cards}
      </div>
    </div>
  </section>
</main>
{render_footer().replace("{year}", "2026")}
<script src="/mobile/m.js?v=20260701m2"></script>
</body>
</html>'''
    return doc


def build_all():
    for pg in PAGES:
        blocks = extract(pg)
        doc = render_page(pg, blocks)
        d = os.path.join(SITE, "mobile", pg) if pg else os.path.join(SITE, "mobile")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"  wrote /mobile/{pg or ''}  ({len(blocks)} blocks)")


if __name__ == "__main__":
    if "build" in sys.argv:
        build_all()
    else:
        out = {}
        for pg in PAGES:
            blocks = extract(pg)
            out[pg or "home"] = blocks
            print(f"{pg or 'home':18} {len(blocks):3} blocks")
        dst = os.environ.get("OUT", "/tmp/lfwc_content.json")
        json.dump(out, open(dst, "w"), indent=1)
        print("wrote", dst)
