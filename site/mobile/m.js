/* LifeWay mobile — hamburger toggle for the authored /mobile/* pages. */
(function () {
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn, { once: true });
  }
  ready(function () {
    var burger = document.querySelector('.m-burger');
    var nav = document.querySelector('.m-nav');
    if (!burger || !nav) return;
    function setOpen(open) {
      document.body.classList.toggle('m-nav-open', open);
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
    burger.addEventListener('click', function () {
      setOpen(!document.body.classList.contains('m-nav-open'));
    });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') setOpen(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setOpen(false);
    });
  });
})();
