/* lfwc mobile pages — hamburger menu. Runs only on /mobile/* pages.
   Builds a fixed top-right button + full-screen overlay menu from the
   site nav links. Self-contained (does not use the old mobile-fix.js). */
(function () {
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn, { once: true });
  }

  function collectLinks() {
    var out = [], seen = {};
    document.querySelectorAll('.main-navigation.unifiednav .unifiednav__item').forEach(function (a) {
      var href = (a.getAttribute('href') || '').trim();
      var text = (a.textContent || '').replace(/\s+/g, ' ').trim();
      if (!text || !href || href === '#' || href === '/mobile#' || href === '/mobile/#') return;
      var key = href + '|' + text;
      if (seen[key]) return;
      seen[key] = 1;
      out.push({ href: href, text: text });
    });
    if (!out.length) {
      out = [['/mobile/', 'Home'], ['/mobile/about', 'About'], ['/mobile/ministries', 'Ministries'],
        ['/mobile/services', 'Services'], ['/mobile/giving', 'Giving'],
        ['/mobile/plan-your-visit', 'Plan Your Visit'], ['/mobile/#Contact', 'Contact'],
        ['/mobile/faq', 'FAQ']].map(function (x) { return { href: x[0], text: x[1] }; });
    }
    return out;
  }

  function build() {
    var menu = document.querySelector('.lfwc-mnav');
    if (menu) { sync(menu); return; }

    var header = document.getElementById('hcontainer') || document.querySelector('.dmHeader') || document.body;

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'lfwc-mnav-btn';
    btn.setAttribute('aria-label', 'Menu');
    btn.setAttribute('aria-expanded', 'false');
    btn.innerHTML = '<span></span><span></span><span></span>';
    (header === document.body ? document.body : header).appendChild(btn);

    menu = document.createElement('nav');
    menu.className = 'lfwc-mnav';
    menu.setAttribute('aria-label', 'Mobile navigation');
    sync(menu);
    document.body.appendChild(menu);

    function setOpen(open) {
      btn.classList.toggle('open', open);
      menu.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.style.overflow = open ? 'hidden' : '';
    }
    btn.addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation();
      setOpen(!menu.classList.contains('open'));
    });
    menu.addEventListener('click', function (e) { if (e.target && e.target.tagName === 'A') setOpen(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' || e.keyCode === 27) setOpen(false); });
  }

  function sync(menu) {
    var links = collectLinks();
    if (menu.querySelectorAll('a').length >= links.length) return;
    menu.innerHTML = '';
    links.forEach(function (l) {
      var a = document.createElement('a');
      a.href = l.href;
      a.textContent = l.text;
      menu.appendChild(a);
    });
  }

  ready(build);
  window.addEventListener('load', build);
  var t = setInterval(build, 700);
  setTimeout(function () { clearInterval(t); }, 5000);
})();
