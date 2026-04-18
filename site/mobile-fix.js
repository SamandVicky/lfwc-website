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

  var resizeTimer = null;
  function onResize() {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(function () {
      applyDeviceClasses();
      resetNavStart();
    }, 120);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      applyDeviceClasses();
      resetNavStart();
    }, { once: true });
  } else {
    applyDeviceClasses();
    resetNavStart();
  }

  window.addEventListener('resize', onResize);
  window.addEventListener('orientationchange', function () {
    applyDeviceClasses();
    resetNavStart();
  });
  window.addEventListener('load', resetNavStart);
})();
