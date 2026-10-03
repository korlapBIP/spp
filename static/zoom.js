/* Zoom otomatis foto siswa: arahkan kursor ke foto (class "zoom-foto") untuk melihat versi besar.
   Di layar sentuh: ketuk foto untuk membuka/menutup. Tidak terpengaruh overflow tabel. */
(function () {
  var SIZE = 260;      // ukuran sisi terpanjang foto yang diperbesar (px)
  var GAP = 12;
  var pop = null, img = null, active = null;

  function build() {
    pop = document.createElement('div');
    pop.style.cssText = 'position:fixed;z-index:9999;pointer-events:none;background:#fff;padding:5px;' +
      'border-radius:14px;box-shadow:0 8px 28px rgba(0,0,0,.35);opacity:0;transform:scale(.6);' +
      'transform-origin:center;transition:opacity .15s ease,transform .18s ease;display:none';
    img = document.createElement('img');
    img.style.cssText = 'display:block;max-width:' + SIZE + 'px;max-height:' + SIZE + 'px;border-radius:10px;object-fit:contain';
    pop.appendChild(img);
    document.body.appendChild(pop);
  }

  function place(el) {
    var r = el.getBoundingClientRect();
    var w = pop.offsetWidth, h = pop.offsetHeight;
    var vw = window.innerWidth, vh = window.innerHeight;
    var x = r.right + GAP;
    if (x + w > vw - 8) x = r.left - GAP - w;           // tidak muat di kanan -> taruh di kiri
    if (x < 8) x = Math.max(8, Math.min(vw - w - 8, r.left + r.width / 2 - w / 2));
    var y = r.top + r.height / 2 - h / 2;
    y = Math.max(8, Math.min(vh - h - 8, y));
    pop.style.left = x + 'px';
    pop.style.top = y + 'px';
  }

  function show(el) {
    if (!pop) build();
    active = el;
    img.onload = function () { if (active === el) place(el); };
    img.src = el.currentSrc || el.src;
    pop.style.display = 'block';
    place(el);
    requestAnimationFrame(function () { pop.style.opacity = '1'; pop.style.transform = 'scale(1)'; });
  }

  function hide() {
    if (!pop || !active) return;
    active = null;
    pop.style.opacity = '0';
    pop.style.transform = 'scale(.6)';
    setTimeout(function () { if (!active) pop.style.display = 'none'; }, 180);
  }

  function target(e) {
    return e.target && e.target.closest ? e.target.closest('.zoom-foto') : null;
  }

  document.addEventListener('mouseover', function (e) {
    var t = target(e);
    if (t && t !== active) show(t);
  });
  document.addEventListener('mouseout', function (e) {
    var t = target(e);
    if (t && (!e.relatedTarget || !t.contains(e.relatedTarget))) hide();
  });
  // layar sentuh: ketuk untuk toggle
  document.addEventListener('click', function (e) {
    if (!window.matchMedia('(hover: none)').matches) return;
    var t = target(e);
    if (t) { active === t ? hide() : show(t); } else { hide(); }
  });
  window.addEventListener('scroll', hide, true);
})();
