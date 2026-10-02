#!/usr/bin/env python3
"""Make the desktop page tree self-contained: download every asset it pulls
from Duda's CDNs (CSS, JS, runtime chunks, fonts, images) into site/ and
rewrite all references to local paths. The Duda site was deleted, so its CDN
files are disappearing (WIDGET_CSS, the hero video, ...).

Layout:
  static.cdn-website.com/mnlt/production/6300/X -> /X   (where Duda served it;
      the runtime derives its chunk/public paths from the page origin)
  static.cdn-website.com/libs/X                 -> /libs/X
  <other duda host>/X                            -> /cdn/<host>/X

Lost WIDGET_CSS files are restored from recovered copies in
recovered_widget_css/ (Wayback Machine). Re-runnable: already-downloaded
files are reused. The mobile tree is left alone.
"""
import concurrent.futures as cf
import hashlib
import html
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")
RECOVERED = os.path.join(ROOT, "recovered_widget_css")
STATIC_MNLT = "https://static.cdn-website.com/mnlt/production/6300"

PAGES = ["", "about", "events", "faq", "get-connected", "get-in-touch",
         "giving", "media", "ministries", "newsletter", "plan-your-visit",
         "services", "tuesday-services"]

DUDA_HOST = r"(?:lirp|irp|static|vid|irt-cdn|dd-cdn|dp-cdn|irp-cdn)\.(?:cdn-website|multiscreensite)\.com"
URL_RE = re.compile(r"(?:https?:)?(?://|\\/\\/)" + DUDA_HOST + r"(?:/|\\/)[^\s\"'()<>]*")
CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)([^'\")]+)\1\s*\)|@import\s+(['\"])([^'\"]+)\3")

failures = {}
cache = {}

# Duda URLs that were already dead before the migration (403/404), mapped to a
# surviving equivalent or dropped. Applied to pages and downloaded CSS.
DEAD_REFS = [
    # template default background, overridden everywhere it matters
    (r"url\(https://irt-cdn\.multiscreensite\.com/[^)]*/site_background_education-2087x1173\.jpg\)", "none"),
    # rules for template sections/buttons no page uses
    (r"url\(https://(?:dp-cdn|irp-cdn)\.multiscreensite\.com/[^)]*\)", "none"),
    # unsized originals are gone; the sized renditions survive
    (r"(lirp\.cdn-website\.com/a78c0b5c/dms3rep/multi/opt/3-02fe8396)\.jpg", r"\1-2880w.jpg"),
    (r"(lirp\.cdn-website\.com/a78c0b5c/dms3rep/multi/opt/Agape\+Bible\+Fellowship\+Church\+%281%29)\.png",
     r"\1-2880w.png"),
    # legacy SVG icon-font sources; woff/ttf are listed first and localized
    (r',url\(https://static\.cdn-website\.com/fonts/dm-(?:social-)?font\.svg[^)]*\) format\("svg"\)', ""),
]


def clean(raw):
    """Trim a regex match down to the URL proper and decode it for fetching."""
    for stop in ("&quot;", "&#39;", "&gt;", "&lt;"):
        raw = raw.split(stop)[0]
    raw = raw.rstrip(",;")
    url = html.unescape(raw).replace("\\/", "/")
    if url.startswith("//"):
        url = "https:" + url
    return raw, url


def local_path(url):
    """Map a Duda URL to the site-root path it will be served from."""
    p = urllib.parse.urlsplit(url)
    path = urllib.parse.unquote(p.path)
    if p.netloc == "static.cdn-website.com" and path.startswith("/mnlt/production/6300/"):
        local = path[len("/mnlt/production/6300"):]
    elif p.netloc == "static.cdn-website.com" and path.startswith("/libs/"):
        local = path
    else:
        local = "/cdn/" + p.netloc.split(".")[0] + path
    if p.query and (local.endswith("/css2") or "." not in os.path.basename(local)):
        local += "-" + hashlib.md5(p.query.encode()).hexdigest()[:10] + ".css"
    # keep served paths free of characters that need URL-encoding
    return re.sub(r"[^A-Za-z0-9._/-]", "_", local)


UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140 Safari/537.36")
# lirp is Duda's resizing image CDN: it negotiates the format, and browsers
# were sent WebP (often 30x smaller than the stored PNG original)
NEGOTIATED_IMG = re.compile(r"^https://lirp\.cdn-website\.com/.*\.(?:png|jpe?g)$", re.I)


def fetch(url, dest, accept="*/*"):
    """curl url to dest; returns the response content type. (curl rather than
    urllib: lirp answers some URLs with a 301 that urllib loops on.)"""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    r = subprocess.run(["curl", "-sfL", "--compressed", "-m", "120", "-A", UA,
                        "-H", "Accept: " + accept, "-o", dest, "-w", "%{content_type}", url],
                       capture_output=True, text=True)
    if r.returncode:
        if os.path.exists(dest):
            os.remove(dest)
        raise RuntimeError(f"curl exit {r.returncode}")
    return r.stdout


def download(url):
    """Download url to its local path (once). Returns local path or None."""
    if url in cache:
        return cache[url]
    local = local_path(url)
    webp = NEGOTIATED_IMG.match(url.split("?")[0])
    if webp:
        local = os.path.splitext(local)[0] + ".webp"
    dest = os.path.join(SITE, local.lstrip("/"))
    if not os.path.exists(dest):
        widget = re.search(r"/WIDGET_CSS/([0-9a-f]+)\.css", url)
        try:
            if widget:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy(os.path.join(RECOVERED, widget.group(1) + ".css"), dest)
            elif webp:
                ctype = fetch(url, dest, "image/avif,image/webp,image/*,*/*;q=0.8")
                if ctype != "image/webp":
                    os.remove(dest)
                    raise RuntimeError("expected webp, got " + ctype)
            else:
                fetch(url, dest)
        except Exception as e:
            failures[url] = str(e)
            cache[url] = None
            return None
    cache[url] = local
    return local


def fix_dead_refs(text):
    for pat, repl in DEAD_REFS:
        text = re.sub(pat, repl, text)
    return text


def localize_css(local, base_url):
    """Pull in a stylesheet's url()/@import dependencies and point them local."""
    dest = os.path.join(SITE, local.lstrip("/"))
    css = fix_dead_refs(open(dest, encoding="utf-8", errors="replace").read())

    def resolve(ref):
        if ref.startswith(("data:", "#")):
            return None
        if ref.startswith("/") and not ref.startswith("//"):
            # root-relative = the old Duda site origin, i.e. the runtime tree
            return STATIC_MNLT + ref
        return urllib.parse.urljoin(base_url, ref)

    deps = {}
    for m in CSS_URL_RE.finditer(css):
        ref = m.group(2) or m.group(4)
        absu = resolve(ref.strip())
        if absu and re.match(r"https://" + DUDA_HOST + "/", absu):
            deps[ref] = absu
    with cf.ThreadPoolExecutor(16) as ex:
        results = dict(zip(deps, ex.map(download, deps.values())))
    # relative and root-relative refs stay valid because the tree is mirrored
    # as-is; only absolute CDN URLs need rewriting
    for ref, loc in results.items():
        if loc and ref.startswith(("http", "//")):
            css = css.replace(ref, loc)
    for ref, absu in deps.items():
        loc = results[ref]
        if loc and loc.endswith(".css") and absu not in seen_css:
            seen_css.add(absu)
            localize_css(loc, absu)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(css)


seen_css = set()

EXTRA_ASSETS = [
    "https://static.cdn-website.com/libs/bower-skrollr/skrollr.min.js",
    "https://static.cdn-website.com/libs/requirejs/2.3.7/require.js",
]

RUNTIME_PROPS = {
    "runtimecollector.url": "''",
    "ecommerce.ecwid.script": "''",
    "rt.pushnotifs.sslframe.encoded": "''",
    "common.resources.cdn.host": "''",
    "common.resources.folder": "''",
    "import.images.storage.imageCDN": "'/'",
}


def patch_runtime_js(local):
    """Rewrite hard-coded Duda hosts inside a downloaded script."""
    dest = os.path.join(SITE, local.lstrip("/"))
    js = open(dest, encoding="utf-8", errors="replace").read()
    new = js.replace("https://static.cdn-website.com/_dm/", "/_dm/")
    new = new.replace("https://dd-cdn.multiscreensite.com/jscache/facebook_all_en_US.js",
                      "https://connect.facebook.net/en_US/sdk.js")
    if new != js:
        with open(dest, "w", encoding="utf-8") as f:
            f.write(new)


def runtime_chunks(local):
    """Download every webpack chunk the runtime can lazy-load."""
    js = open(os.path.join(SITE, local.lstrip("/")), encoding="utf-8", errors="replace").read()
    base = re.search(r'\.p="(/editor/apps/modules/runtime/)"', js)
    if not base:
        return
    # a.u=R=>(({id:"name",...}[R]||R)+"."+{id:"hash",...}[R]+".js")
    u = re.search(r'\.u=\w+=>\(\(\{([^}]*)\}\[\w+\]\|\|\w+\)\+"\."\+\{([^}]*)\}\[\w+\]\+"\.js"\)', js)
    if not u:
        return
    names = dict(re.findall(r'(\d+):"([^"]+)"', u.group(1)))
    hashes = re.findall(r'(\d+):"([0-9a-f]{20})"', u.group(2))
    urls = [f"{STATIC_MNLT}{base.group(1)}{names.get(cid, cid)}.{h}.js" for cid, h in hashes]
    with cf.ThreadPoolExecutor(16) as ex:
        locs = list(ex.map(download, urls))
    for loc in filter(None, locs):
        patch_runtime_js(loc)
    print(f"  runtime chunks: {sum(1 for l in locs if l)}/{len(urls)}")


def main():
    # loaded by the runtime via rtCommonProps["common.resources.cdn.host"]
    for url in EXTRA_ASSETS:
        download(url)
    for page in PAGES:
        path = os.path.join(SITE, page, "index.html")
        doc = fix_dead_refs(open(path, encoding="utf-8").read())

        # Duda RUM / ecommerce / push hooks and CDN hosts in the runtime config
        for key, val in RUNTIME_PROPS.items():
            doc = re.sub(r'(rtCommonProps\["%s"\]\s*=\s*)[^;]+;' % re.escape(key),
                         lambda m: m.group(1) + val + ";", doc)
        doc = re.sub(r'<link rel="preconnect" href="https://(?:l?irp|static)\.cdn-website\.com/?"\s*/?>\n?', "", doc)
        # Duda's Snowplow page-view tracker; keep a no-op so runtime calls are safe
        doc = re.sub(r'(<script type="text/javascript" id="d_track_sp">).*?(</script>)',
                     r"\1\nwindow.dmsnowplow = window.dmsnowplow || function () {};\n\2",
                     doc, flags=re.S)
        # InSite popup rules + their scripts were served by the deleted Duda
        # site server (never by the CDN), so they have 404'd since the move
        doc = re.sub(r"var _dm_insite = \[.*?\];", "var _dm_insite = [];", doc)
        doc = re.sub(r'<script[^>]*src="/_dm/s/rt/smart/[^"]*"[^>]*>\s*</script>\n?', "", doc)

        refs = {}
        for m in URL_RE.finditer(doc):
            raw, url = clean(m.group(0))
            if urllib.parse.urlsplit(url).path.strip("/"):
                refs[raw] = url
        with cf.ThreadPoolExecutor(16) as ex:
            locs = dict(zip(refs, ex.map(download, refs.values())))
        for raw in sorted(locs, key=len, reverse=True):
            loc = locs[raw]
            if not loc:
                continue
            if loc.endswith(".css") and refs[raw] not in seen_css:
                seen_css.add(refs[raw])
                localize_css(loc, refs[raw])
            if loc.endswith(".js") and refs[raw].startswith(STATIC_MNLT):
                patch_runtime_js(loc)
            doc = doc.replace(raw, loc.replace("/", "\\/") if "\\/" in raw else loc)

        with open(path, "w", encoding="utf-8") as f:
            f.write(doc)
        left = len(URL_RE.findall(doc))
        print(f"{page or 'home'}: {len(refs)} refs localized, {left} Duda refs remain")

    scripts = os.path.join(SITE, "_dm/s/rt/dist/scripts")
    for name in sorted(os.listdir(scripts)) if os.path.isdir(scripts) else []:
        runtime_chunks("/_dm/s/rt/dist/scripts/" + name)

    if failures:
        print("\nFAILED downloads:")
        for u, e in sorted(failures.items()):
            print(f"  {e}  {u}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
