import os

site_dir = os.path.join(os.path.dirname(__file__), "site")

for root, dirs, files in os.walk(site_dir):
    for fname in files:
        if fname.endswith(".html"):
            fpath = os.path.join(root, fname)
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            patched = content.replace(
                "https://www.lifewayfamilyworshipcenter.com",
                "http://localhost:8080"
            )
            if patched != content:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(patched)
                print(f"Patched: {fpath}")

print("Done.")
