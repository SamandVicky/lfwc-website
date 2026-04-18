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
      normalizeSelectedNavItem();
      tagFaqSections();
      resetNavStart();
    }, { once: true });
  } else {
    applyDeviceClasses();
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
    normalizeSelectedNavItem();
    tagFaqSections();
    resetNavStart();
  });

  var observeTimer = window.setInterval(function () {
    normalizeSelectedNavItem();
    tagFaqSections();
    resetNavStart();
  }, 700);
  window.setTimeout(function () {
    window.clearInterval(observeTimer);
  }, 5000);
})();
