import os
import re

site_dir = os.path.join(os.path.dirname(__file__), "site")

# Inject a script at the top of <body> that overrides nav click behavior
# and removes any JS that tries to do AJAX/SPA navigation
NAV_FIX = """
<script>
// Force all internal nav links to do normal browser navigation
document.addEventListener('DOMContentLoaded', function() {
    // Intercept all clicks on nav links
    document.querySelectorAll('a[href]').forEach(function(a) {
        var href = a.getAttribute('href');
        if (href && href.startsWith('/') && !href.startsWith('//')) {
            a.addEventListener('click', function(e) {
                e.stopImmediatePropagation();
                window.location.href = href;
            }, true);
        }
    });
});
// Also override pushState navigation used by the platform
window.addEventListener('load', function() {
    document.querySelectorAll('a[href]').forEach(function(a) {
        var href = a.getAttribute('href');
        if (href && href.startsWith('/') && !href.startsWith('//')) {
            a.onclick = function(e) {
                e.preventDefault();
                e.stopImmediatePropagation();
                window.location.href = href;
                return false;
            };
        }
    });
});
</script>
"""

for root, dirs, files in os.walk(site_dir):
    for fname in files:
        if fname.endswith(".html"):
            fpath = os.path.join(root, fname)
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Inject nav fix just before </body>
            if NAV_FIX.strip() not in content:
                patched = content.replace("</body>", NAV_FIX + "\n</body>", 1)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(patched)
                print(f"Patched: {fpath}")

print("Done.")
