(function () {
  // Mobile menu
  var btn = document.querySelector('.menu-btn');
  var menu = document.getElementById('menu');
  if (btn && menu) {
    btn.addEventListener('click', function () {
      var open = menu.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    });
  }
  // Dropdowns (click / keyboard)
  document.querySelectorAll('.sub-btn').forEach(function (b) {
    b.addEventListener('click', function () {
      var li = b.parentElement;
      var open = !li.classList.contains('open');
      document.querySelectorAll('.has-sub.open').forEach(function (o) {
        o.classList.remove('open'); o.querySelector('.sub-btn').setAttribute('aria-expanded', 'false');
      });
      if (open) { li.classList.add('open'); b.setAttribute('aria-expanded', 'true'); }
    });
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.has-sub')) {
      document.querySelectorAll('.has-sub.open').forEach(function (o) {
        o.classList.remove('open'); o.querySelector('.sub-btn').setAttribute('aria-expanded', 'false');
      });
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.has-sub.open').forEach(function (o) { o.classList.remove('open'); });
    }
  });
  // Spam-safe email links
  document.querySelectorAll('.email-link').forEach(function (a) {
    var addr = a.getAttribute('data-u') + '@' + a.getAttribute('data-d');
    var subj = a.getAttribute('data-subject'), body = a.getAttribute('data-body');
    a.setAttribute('href', 'mailto:' + addr + (subj ? '?subject=' + encodeURIComponent(subj) + (body ? '&body=' + body : '') : ''));
    if (a.closest('.email-big')) a.textContent = addr;
  });
  // Filters (experience type, write-up language)
  document.querySelectorAll('.filter').forEach(function (group) {
    var list = group.parentElement.querySelector('[data-filterable]');
    if (!list) return;
    group.querySelectorAll('[data-filter]').forEach(function (b) {
      b.addEventListener('click', function () {
        var f = b.getAttribute('data-filter');
        group.querySelectorAll('[data-filter]').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        list.querySelectorAll('[data-kind]').forEach(function (item) {
          item.hidden = !(f === 'all' || item.getAttribute('data-kind') === f);
        });
      });
    });
  });
  // Read counts: starting number (from Facebook) + live reads on the public site.
  (function () {
    var els = document.querySelectorAll('.reads[data-key]');
    if (!els.length) return;
    var live = location.hostname === 'alrabbysiemens.github.io';
    function compact(n) {
      if (n < 100) return '';
      if (n < 1000) return String(n);
      return (Math.round(n / 100) / 10).toFixed(1).replace(/\.0$/, '') + 'k';
    }
    els.forEach(function (el) {
      if (!live) return;
      var key = el.getAttribute('data-key'), base = +el.getAttribute('data-base') || 0;
      var url = 'https://abacus.jasoncameron.dev/' + (el.hasAttribute('data-count') ? 'hit' : 'get') + '/alrabbysiemens/' + key;
      fetch(url).then(function (r) { return r.ok ? r.json() : { value: 0 }; }).then(function (d) {
        var c = compact(base + (d && d.value || 0));
        var up = el.closest('.crumb') ? ' READS' : ' reads';
        el.textContent = c ? ' · ' + c + up : '';
      }).catch(function () {});
    });
  })();

  // "Leave a note" window: opens when a visitor is about to leave (desktop), after a while (phones), or from a button.
  (function () {
    var modal = document.getElementById('note-modal'), form = document.getElementById('note-form');
    if (!modal || !form) return;
    function get(k) { try { return sessionStorage.getItem(k) || localStorage.getItem(k); } catch (e) { return null; } }
    function set(k, store) { try { (store || sessionStorage).setItem(k, '1'); } catch (e) {} }
    var last = null;
    function open(force) {
      if (!force && (get('note-shown') || get('note-sent'))) return;
      set('note-shown'); last = document.activeElement;
      modal.hidden = false; document.body.classList.add('note-lock');
      setTimeout(function () { form.message.focus(); }, 30);
    }
    function close() { modal.hidden = true; document.body.classList.remove('note-lock'); if (last && last.focus) last.focus(); }
    modal.querySelectorAll('[data-close]').forEach(function (b) { b.addEventListener('click', close); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !modal.hidden) close(); });
    document.querySelectorAll('.note-open').forEach(function (b) { b.addEventListener('click', function () { open(true); }); });
    // desktop: pointer heads for the tab bar / close button
    document.addEventListener('mouseout', function (e) {
      if (!e.relatedTarget && e.clientY <= 0 && window.innerWidth > 760) open(false);
    });
    // phones/tablets: no "leaving" signal, so offer it once after 45 seconds
    if (window.matchMedia && window.matchMedia('(hover: none)').matches) setTimeout(function () { open(false); }, 45000);
    var now = new Date(), months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    var stamp = now.getDate() + ' ' + months[now.getMonth()] + ' ' + now.getFullYear();
    var dEl = form.querySelector('.note-date'); if (dEl) dEl.textContent = '· ' + stamp;
    var msg = form.message, count = form.querySelector('.note-count');
    msg.addEventListener('input', function () { count.textContent = msg.value.length + ' / 300'; });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var st = form.querySelector('.note-status');
      if (form._honey.value) return;
      if (!msg.value.trim() || !form.name.value.trim()) { st.textContent = 'Please add a message and your name.'; return; }
      var live = location.hostname === 'alrabbysiemens.github.io';
      if (!live) { st.textContent = 'Preview only: notes start arriving once the site is live.'; return; }
      var to = (window.NOTE_TO || []).join('@');
      st.textContent = 'Pinning…';
      fetch('https://formsubmit.co/ajax/' + to, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({ name: form.name.value.trim(), location: form.location.value.trim(), message: msg.value.trim(), date: stamp,
          page: location.pathname, _subject: 'New note for "Your Presence" from ' + form.name.value.trim(), _template: 'table' })
      }).then(function (r) { return r.json(); }).then(function () {
        set('note-sent', localStorage);
        form.innerHTML = '<p class="mono small note-kick">THANK YOU</p><h2>Your note is on its way 📌</h2><p class="note-sub">Once I read it, it will be pinned on the Your Presence board.</p><div class="note-actions"><button type="button" class="btn" data-close>Close</button></div>';
        form.querySelector('[data-close]').addEventListener('click', close);
      }).catch(function () { st.textContent = 'Sorry, that did not go through. Please try again in a moment.'; });
    });
  })();

  // Videos page: real YouTube titles, playlist thumbnails, and a pop-up player.
  (function () {
    if (!document.querySelector('.vids')) return;
    function oembed(url) { return fetch('https://noembed.com/embed?url=' + encodeURIComponent(url)).then(function (r) { return r.json(); }); }
    document.querySelectorAll('[data-yt]').forEach(function (el) {
      oembed('https://www.youtube.com/watch?v=' + el.getAttribute('data-yt')).then(function (d) { if (d && d.title) el.textContent = d.title; }).catch(function () {});
    });
    document.querySelectorAll('[data-yt-list]').forEach(function (el) {
      oembed('https://www.youtube.com/playlist?list=' + el.getAttribute('data-yt-list')).then(function (d) {
        if (d && d.thumbnail_url) { var i = new Image(); i.onload = function () { el.style.backgroundImage = 'url(' + d.thumbnail_url + ')'; el.classList.add('has-img'); }; i.src = d.thumbnail_url; }
      }).catch(function () {});
    });
    // show real thumbnails only when they actually load; otherwise keep the drawn cover
    document.querySelectorAll('.v-th').forEach(function (el) {
      var m = (el.getAttribute('style') || '').match(/url\(['"]?([^'")]+)/);
      if (!m) return;
      var img = new Image();
      img.onload = function () { if (img.naturalWidth > 120) el.classList.add('has-img'); };
      img.src = m[1];
    });
    var modal = document.getElementById('v-modal'), frame = document.getElementById('v-frame'), out = document.getElementById('v-out');
    function close() { modal.hidden = true; frame.innerHTML = ''; document.body.classList.remove('note-lock'); }
    document.querySelectorAll('[data-play]').forEach(function (b) {
      b.addEventListener('click', function () {
        var src, link;
        if (b.getAttribute('data-play') === 'yt') {
          var id = b.getAttribute('data-id');
          src = 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1'; link = 'https://www.youtube.com/watch?v=' + id;
        } else {
          link = b.getAttribute('data-url');
          src = 'https://www.facebook.com/plugins/video.php?show_text=false&autoplay=true&href=' + encodeURIComponent(link);
        }
        frame.innerHTML = '<iframe src="' + src + '" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe>';
        out.href = link; modal.hidden = false; document.body.classList.add('note-lock');
      });
    });
    modal.querySelectorAll('[data-vclose]').forEach(function (x) { x.addEventListener('click', close); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !modal.hidden) close(); });
  })();
})();

/* gallery lightbox */
(function(){
  var lb=document.querySelector('.g-lb'); if(!lb) return;
  var ph=[].slice.call(document.querySelectorAll('.g-ph')), i=0, img=lb.querySelector('img'), cap=lb.querySelector('figcaption');
  function show(n){ i=(n+ph.length)%ph.length; img.src=ph[i].dataset.lb; cap.textContent=ph[i].dataset.cap; lb.hidden=false; }
  ph.forEach(function(b,n){ b.addEventListener('click',function(){ show(n); }); });
  lb.querySelector('.g-lb-x').onclick=function(){ lb.hidden=true; };
  lb.querySelector('.g-lb-p').onclick=function(){ show(i-1); };
  lb.querySelector('.g-lb-n').onclick=function(){ show(i+1); };
  lb.addEventListener('click',function(e){ if(e.target===lb) lb.hidden=true; });
  document.addEventListener('keydown',function(e){ if(lb.hidden) return; if(e.key==='Escape') lb.hidden=true; if(e.key==='ArrowLeft') show(i-1); if(e.key==='ArrowRight') show(i+1); });
})();

/* sticker laptop: drop stickers when visible, tap to show note on touch */
(function(){
  var sec=document.querySelector('.affil'); if(!sec) return;
  if('IntersectionObserver' in window){ var io=new IntersectionObserver(function(e){ if(e[0].isIntersecting){ sec.classList.add('go'); io.disconnect(); } },{threshold:.2}); io.observe(sec); } else sec.classList.add('go');
  var st=sec.querySelectorAll('.stk');
  function nudge(b){ var t=b.querySelector('.stk-tip'); if(!t) return; b.style.setProperty('--tx','0px'); var r=t.getBoundingClientRect(), W=document.documentElement.clientWidth, d=0; if(r.left<8) d=8-r.left; else if(r.right>W-8) d=W-8-r.right; b.style.setProperty('--tx',d+'px'); }
  st.forEach(function(b){ b.addEventListener('mouseenter',function(){nudge(b);}); b.addEventListener('focus',function(){nudge(b);}); });
  st.forEach(function(b){ b.addEventListener('click',function(){ var was=b.classList.contains('on'); st.forEach(function(x){x.classList.remove('on');}); if(!was){ b.classList.add('on'); nudge(b); } }); });
})();
