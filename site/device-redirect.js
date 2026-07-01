/* lfwc device routing — sends phones to the /mobile/* page tree and
   everything else to the normal tree. Loaded on every page (both trees);
   the direction is decided by the current path. Loop-safe: the phone
   test uses the physical screen short-edge + UA (stable per device),
   never window width, so resizing/rotating can't bounce a visitor. */
(function () {
  var ua = navigator.userAgent || '';
  var uaPhone = /Android.*Mobile|iPhone|iPod|Windows Phone|IEMobile|BlackBerry|Opera Mini/i.test(ua);
  var shortEdge = Math.min(screen.width || 9999, screen.height || 9999);
  var isPhone = uaPhone || shortEdge < 768;

  var path = location.pathname || '/';
  var inMobile = /^\/mobile(\/|$)/.test(path);
  var rest = location.search + location.hash;

  if (isPhone && !inMobile) {
    location.replace('/mobile' + (path === '/' ? '/' : path) + rest);
  } else if (!isPhone && inMobile) {
    location.replace((path.replace(/^\/mobile/, '') || '/') + rest);
  }
})();
