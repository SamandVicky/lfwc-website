(function () {
  function getDevice() {
    var width = window.innerWidth || document.documentElement.clientWidth || 1200;
    if (width <= 767) return 'mobile';
    if (width <= 1024) return 'tablet';
    return 'desktop';
  }

  function applyDeviceClasses() {
    var body = document.getElementById('dmRoot') || document.body;
    if (!body) return;

    var device = getDevice();
    window._currentDevice = device;

    body.classList.remove('dmDesktopBody', 'dmTabletBody', 'dmMobileBody');
    if (device === 'mobile') {
      body.classList.add('dmMobileBody');
    } else if (device === 'tablet') {
      body.classList.add('dmTabletBody');
    } else {
      body.classList.add('dmDesktopBody');
    }

    body.classList.add('lfwc-responsive-fix');
    document.documentElement.setAttribute('data-lfwc-device', device);
  }

  function resetNavStart() {
    var navContainer = document.querySelector('.main-navigation.unifiednav .unifiednav__container');
    if (!navContainer) return;
    navContainer.scrollLeft = 0;
    window.requestAnimationFrame(function () {
      navContainer.scrollLeft = 0;
    });
    window.setTimeout(function () {
      navContainer.scrollLeft = 0;
    }, 120);
  }

  function normalizeSelectedNavItem() {
    var body = document.getElementById('dmRoot');
    if (!body) return;
    if (body.getAttribute('data-page-alias') !== 'home') return;

    var items = document.querySelectorAll('.main-navigation.unifiednav .unifiednav__item');
    if (!items.length) return;

    var homeItem = null;
    items.forEach(function (item) {
      var href = (item.getAttribute('href') || '').trim();
      if (href === '/') {
        homeItem = item;
      }
    });

    if (!homeItem) return;

    items.forEach(function (item) {
      item.classList.remove('dmNavItemSelected');
      item.removeAttribute('aria-current');
    });
    homeItem.classList.add('dmNavItemSelected');
    homeItem.setAttribute('aria-current', 'page');
  }

  function tagFaqSections() {
    var links = document.querySelectorAll('a[href]');
    if (!links.length) return;

    links.forEach(function (link) {
      var txt = (link.textContent || '').trim().toLowerCase();
      if (txt !== 'check our faqs') return;

      var row = link.closest('.dmRespRow');
      if (row) row.classList.add('lfwc-faq-focus');

      var col = link.closest('.dmRespCol');
      if (col) col.classList.add('lfwc-faq-main-col');
    });
  }

  // Build the mobile hamburger button + full-screen menu. The CSS for
  // .lfwc-hamburger-btn / .lfwc-mobile-menu already exists in
  // mobile-fix.css; this creates the elements (Duda's own mobile nav
  // runtime isn't in the mirror) and wires the toggle. Idempotent.
  function collectNavLinks() {
    var links = [];
    var seen = {};
    document.querySelectorAll('.main-navigation.unifiednav .unifiednav__item').forEach(function (a) {
      var href = (a.getAttribute('href') || '').trim();
      var text = (a.textContent || '').replace(/\s+/g, ' ').trim();
      if (!text || !href || href === '#') return; // skip dropdown parent (e.g. "MORE")
      var key = href + '|' + text;
      if (seen[key]) return;
      seen[key] = 1;
      links.push({ href: href, text: text });
    });
    if (!links.length) {
      links = [['/', 'Home'], ['/about', 'About'], ['/ministries', 'Ministries'],
        ['/services', 'Services'], ['/giving', 'Giving'], ['/plan-your-visit', 'Plan Your Visit'],
        ['/#Contact', 'Contact'], ['/faq', 'FAQ']].map(function (x) { return { href: x[0], text: x[1] }; });
    }
    return links;
  }

  // Keep the drawer's links in sync with the nav. The Duda dropdown
  // children ("Plan Your Visit"/"Contact"/"FAQ") can appear in the DOM
  // after the first build, so refresh whenever the count grows.
  function syncMenuLinks(menu) {
    var links = collectNavLinks();
    if (menu.querySelectorAll('a').length >= links.length) return;
    menu.innerHTML = '';
    links.forEach(function (l) {
      var a = document.createElement('a');
      a.href = l.href;
      a.textContent = l.text;
      menu.appendChild(a);
    });
  }

  function buildHamburger() {
    var menu = document.querySelector('.lfwc-mobile-menu');
    if (menu) { syncMenuLinks(menu); return; }

    var headerRow = document.querySelector('.u_1418466502') ||
      document.getElementById('hcontainer') ||
      document.querySelector('.dmHeader');
    if (!headerRow) return;

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'lfwc-hamburger-btn';
    btn.setAttribute('aria-label', 'Menu');
    btn.setAttribute('aria-expanded', 'false');
    btn.innerHTML = '<span></span><span></span><span></span>';
    headerRow.appendChild(btn);

    menu = document.createElement('nav');
    menu.className = 'lfwc-mobile-menu';
    menu.setAttribute('aria-label', 'Mobile navigation');
    syncMenuLinks(menu);
    document.body.appendChild(menu);

    function setOpen(open) {
      btn.classList.toggle('open', open);
      menu.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.style.overflow = open ? 'hidden' : '';
    }
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      setOpen(!menu.classList.contains('open'));
    });
    menu.addEventListener('click', function (e) {
      if (e.target && e.target.tagName === 'A') setOpen(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' || e.keyCode === 27) setOpen(false);
    });
  }

  var resizeTimer = null;
  function onResize() {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(function () {
      applyDeviceClasses();
      normalizeSelectedNavItem();
      tagFaqSections();
      resetNavStart();
    }, 120);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      applyDeviceClasses();
      buildHamburger();
      normalizeSelectedNavItem();
      tagFaqSections();
      resetNavStart();
    }, { once: true });
  } else {
    applyDeviceClasses();
    buildHamburger();
    normalizeSelectedNavItem();
    tagFaqSections();
    resetNavStart();
  }

  window.addEventListener('resize', onResize);
  window.addEventListener('orientationchange', function () {
    applyDeviceClasses();
    normalizeSelectedNavItem();
    tagFaqSections();
    resetNavStart();
  });
  window.addEventListener('load', function () {
    buildHamburger();
    normalizeSelectedNavItem();
    tagFaqSections();
    resetNavStart();
  });

  var observeTimer = window.setInterval(function () {
    buildHamburger();
    normalizeSelectedNavItem();
    tagFaqSections();
    resetNavStart();
  }, 700);
  window.setTimeout(function () {
    window.clearInterval(observeTimer);
  }, 5000);
})();
