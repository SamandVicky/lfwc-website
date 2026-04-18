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

  var resizeTimer = null;
  function onResize() {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(applyDeviceClasses, 120);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyDeviceClasses, { once: true });
  } else {
    applyDeviceClasses();
  }

  window.addEventListener('resize', onResize);
  window.addEventListener('orientationchange', applyDeviceClasses);
})();
