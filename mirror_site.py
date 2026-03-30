import urllib.request
import urllib.parse
import os
import re
import time
from html.parser import HTMLParser

BASE_URL = "https://www.lifewayfamilyworshipcenter.com"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "site")

visited = set()
to_visit = ["/"]

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])

def normalize(url):
    if url.startswith("//"):
        url = "https:" + url
    if url.startswith("/"):
        url = BASE_URL + url
    if not url.startswith(BASE_URL):
        return None
    url = url.split("#")[0].split("?")[0]
    return url.rstrip("/") or BASE_URL

def url_to_path(url):
    path = url.replace(BASE_URL, "").strip("/")
    if not path:
        return os.path.join(OUTPUT_DIR, "index.html")
    return os.path.join(OUTPUT_DIR, path, "index.html")

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None

os.makedirs(OUTPUT_DIR, exist_ok=True)

pages = [
    "/", "/about", "/ministries", "/services", "/giving", "/faq",
    "/contact", "/sermons", "/events", "/media"
]

queue = list(pages)
visited = set()

while queue:
    path = queue.pop(0)
    url = BASE_URL + path if not path.startswith("http") else path
    url = url.rstrip("/") or BASE_URL

    if url in visited:
        continue
    visited.add(url)

    print(f"Fetching: {url}")
    html = fetch(url)
    if not html:
        continue

    # Parse links
    parser = LinkParser()
    parser.feed(html)
    for link in parser.links:
        norm = normalize(link)
        if norm and norm not in visited:
            rel = norm.replace(BASE_URL, "") or "/"
            if rel not in queue:
                queue.append(rel)

    # Save file
    out_path = url_to_path(url)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Saved -> {out_path}")
    time.sleep(0.3)

print(f"\nDone! {len(visited)} pages saved to: {OUTPUT_DIR}")
