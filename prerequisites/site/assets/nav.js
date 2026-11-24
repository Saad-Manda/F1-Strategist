/* Course navigation for the prerequisites site.
   Renders the global tree sidebar, breadcrumb bar, on-this-page outline and
   continuous prev/next from window.COURSE (assets/course.js), and keeps
   visited/resume state in localStorage. Classic script: works from file://. */
(function () {
  "use strict";

  var COURSE = window.COURSE;
  if (!COURSE) return;

  var KEY = "f1prereq.v1";
  var GROUPS = { concepts: "Concepts", capstone: "Capstone", project: "This project" };

  var pageId = document.body.getAttribute("data-page") || "";
  var root = pageId.indexOf("/") > 0 ? "../" : "";

  var flat = [];
  COURSE.phases.forEach(function (ph) {
    ph.pages.forEach(function (p) {
      flat.push({ ph: ph, p: p, id: ph.id + "/" + p.n, href: root + ph.slug + "/" + p.file });
    });
  });
  var idx = -1;
  flat.forEach(function (f, i) { if (f.id === pageId) idx = i; });
  var cur = idx >= 0 ? flat[idx] : null;

  /* ---------- state ---------- */

  function load() {
    var s;
    try { s = JSON.parse(localStorage.getItem(KEY)); } catch (e) { s = null; }
    s = s || {};
    s.pages = s.pages || {};
    s.labs = s.labs || {};
    return s;
  }
  function update(fn) {
    var s = load();
    fn(s);
    try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) { /* storage unavailable */ }
    return s;
  }

  var state = load();
  var resumeY = null;
  if (cur && location.hash === "#resume" && state.last && state.last.page === pageId) {
    resumeY = state.last.y || 0;
  }
  if (cur) {
    state = update(function (s) {
      s.pages[pageId] = s.pages[pageId] || {};
      s.pages[pageId].opened = true;
      s.last = { page: pageId, y: resumeY || 0, at: Date.now() };
    });
  }

  function pageState(id) {
    var ps = state.pages[id];
    return ps ? (ps.finished ? "finished" : "opened") : "";
  }
  function labDone(id) {
    var lp = window.LAB_PROGRESS || {};
    return !!((lp[id] && lp[id].passed) || state.labs[id]);
  }

  /* Championship points (light: nothing is locked). The table lives in the redesign plan, section 10.
     page read 1 · cold-open call 1 · in-page lab 3 · code lab 5 · capstone 10 · case closed 10 ·
     Pit Wall personal best within 1 s of the oracle 5 per mode. */
  var PITWALL_MODES = { "1": ["race"], "3.5": ["oracle"], "4": ["learner"], "5": ["replay"], "6": ["rival"], "8": ["duel"], "9": ["training"] };
  function labPoints(p) {
    if (p.group === "capstone") return 10;
    return p.lab.format === "notebook" || p.lab.format === "pytest" ? 5 : 3;
  }
  function points(phId) {
    var got = 0, max = 0, calls = state.calls || {}, cases = state.cases || {};
    var pw = (state.pitwall && state.pitwall.best) || {};
    COURSE.phases.forEach(function (ph) {
      if (phId && ph.id !== phId) return;
      ph.pages.forEach(function (p) {
        var id = ph.id + "/" + p.n;
        max += 1; if (pageState(id) === "finished") got += 1;
        if (p.call) { max += 1; if (calls[p.call]) got += 1; }
        if (p.lab) { var lp = labPoints(p); max += lp; if (labDone(p.lab.id)) got += lp; }
      });
      if (ph["case"]) { max += 10; if (cases[ph.id]) got += 10; }
      (PITWALL_MODES[ph.id] || []).forEach(function (m) {
        max += 5; if (pw[m] && pw[m].gap <= 1.0) got += 5;
      });
    });
    return { got: got, max: max };
  }

  /* ---------- helpers ---------- */

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  function byId(id) {
    for (var i = 0; i < flat.length; i++) if (flat[i].id === id) return flat[i];
    return null;
  }

  /* ---------- sidebar tree ---------- */

  var openPhases = {};
  if (cur) openPhases[cur.ph.id] = true;

  function renderSidebar() {
    var nav = document.getElementById("sidebar");
    if (!nav) return;
    var scrollTop = nav.scrollTop;
    var wasOpen = !!(nav.querySelector(".tree") && nav.querySelector(".tree").classList.contains("open"));

    var total = flat.length, done = 0, labsTotal = 0, labsDone = 0;
    flat.forEach(function (f) {
      if (pageState(f.id) === "finished") done++;
      if (f.p.lab) { labsTotal++; if (labDone(f.p.lab.id)) labsDone++; }
    });

    var h = "";
    h += '<a class="brand" href="' + root + 'index.html">' +
         '<span class="kicker">F1 Strategy Agent</span>' +
         '<span class="title">Prerequisites</span></a>';
    h += '<button class="menu-toggle" type="button">☰ Course</button>';
    h += '<div class="progress-track"><div class="progress-fill" style="width:' +
         (total ? Math.round(100 * done / total) : 0) + '%"></div></div>';
    var pts = points();
    h += '<div class="progress-label">pages ' + done + " / " + total +
         (labsTotal ? " · labs " + labsDone + " / " + labsTotal : "") +
         ' · <b class="pts">' + pts.got + "</b> pts</div>";
    h += '<div class="tree' + (wasOpen ? " open" : "") + '">';

    COURSE.phases.forEach(function (ph) {
      var n = ph.pages.length, fin = 0;
      ph.pages.forEach(function (p) { if (pageState(ph.id + "/" + p.n) === "finished") fin++; });
      var isCur = cur && cur.ph.id === ph.id;
      var isOpen = !!openPhases[ph.id];
      h += '<div class="ph' + (isOpen ? " open" : "") + (isCur ? " current" : "") + '" data-phase="' + esc(ph.id) + '">';
      h += '<button class="ph-row" type="button" aria-expanded="' + isOpen + '">' +
           '<span class="chev">▶</span><span class="n">' + esc(ph.id) + "</span>" +
           '<span class="name">' + esc(ph.short) + "</span>" +
           '<span class="count' + (fin === n ? " done" : "") + '">' + (fin === n ? "✓" : fin + "/" + n) + "</span></button>";
      h += '<ul class="nav-list">';
      var lastGroup = null;
      ph.pages.forEach(function (p) {
        var id = ph.id + "/" + p.n;
        if (p.group !== lastGroup && GROUPS[p.group]) h += '<li class="grp">' + GROUPS[p.group] + "</li>";
        lastGroup = p.group;
        var href = root + ph.slug + "/" + p.file;
        var active = id === pageId;
        h += '<li><a href="' + href + '"' + (active ? ' class="active" aria-current="page"' : "") +
             (p.blurb ? ' title="' + esc(p.blurb) + '"' : "") + ">" +
             '<span class="n">' + esc(p.n) + '</span><span class="t">' + esc(p.title) + "</span>" +
             '<span class="st ' + pageState(id) + '"></span></a></li>';
        if (p.lab) {
          h += '<li><a class="lab-row" href="' + href + '#lab"><span class="t">Lab: ' + esc(p.lab.title) +
               '</span><span class="st ' + (labDone(p.lab.id) ? "finished" : "") + '"></span></a></li>';
        }
      });
      h += "</ul></div>";
    });

    h += '<a class="gloss-link' + (pageId === "pitwall" ? " active" : "") + '" href="' + root + 'pitwall.html">The Pit Wall</a>';
    h += '<a class="gloss-link' + (pageId === "glossary" ? " active" : "") + '" href="' + root + 'glossary.html">Glossary</a>';
    h += "</div>";
    nav.innerHTML = h;

    nav.querySelector(".menu-toggle").addEventListener("click", function () {
      nav.querySelector(".tree").classList.toggle("open");
    });
    Array.prototype.forEach.call(nav.querySelectorAll(".ph-row"), function (btn) {
      btn.addEventListener("click", function () {
        var ph = btn.parentNode, id = ph.getAttribute("data-phase");
        openPhases[id] = !openPhases[id];
        ph.classList.toggle("open", openPhases[id]);
        btn.setAttribute("aria-expanded", String(!!openPhases[id]));
      });
    });
    nav.scrollTop = scrollTop;
  }

  /* ---------- breadcrumb bar ---------- */

  function renderCrumbs(main) {
    var sep = '<span class="sep">›</span>';
    var h = '<a href="' + root + 'index.html">Prerequisites</a>';
    if (cur) {
      var over = root + cur.ph.slug + "/" + cur.ph.pages[0].file;
      h += sep + '<a href="' + over + '">Phase ' + esc(cur.ph.id) + " · " + esc(cur.ph.short) + "</a>";
      h += sep + '<span class="here">' + esc(cur.p.n) + " " + esc(cur.p.title) + "</span>";
      h += '<span class="pos">' + (idx + 1) + " of " + flat.length + "</span>";
    } else if (pageId === "glossary") {
      h += sep + '<span class="here">Glossary</span>';
    } else if (pageId === "pitwall") {
      h += sep + '<span class="here">The Pit Wall</span>';
    } else {
      h += sep + '<span class="here">Course map</span>';
    }
    main.insertBefore(el("div", "crumbs", h), main.firstChild);
  }

  /* ---------- on-this-page outline ---------- */

  function slug(text, used) {
    var s = text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "section";
    var base = s, i = 2;
    while (used[s]) s = base + "-" + i++;
    used[s] = true;
    return s;
  }

  function renderOutline(doc, inner) {
    var heads = Array.prototype.slice.call(doc.querySelectorAll("h2")).filter(function (hd) {
      return !hd.closest(".lab");  // the lab block gets its own single "Lab" entry below
    });
    var used = {};
    heads.forEach(function (hd) { if (hd.id) used[hd.id] = true; });
    heads.forEach(function (hd) { if (!hd.id) hd.id = slug(hd.textContent, used); });
    if (heads.length < 3) return;

    var items = heads.map(function (hd) {
      return '<li><a href="#' + hd.id + '">' + esc(hd.textContent) + "</a></li>";
    }).join("");
    var lab = doc.querySelector(".lab[id]");
    if (lab) items += '<li><a href="#' + lab.id + '">Lab</a></li>';

    inner.appendChild(el("aside", "outline", '<div class="outline-title">On this page</div><ul>' + items + "</ul>"));
    var inline = el("details", "outline-inline", "<summary>On this page</summary><ul>" + items + "</ul>");
    var anchor = doc.querySelector(".dek") || doc.querySelector("h1");
    if (anchor && anchor.nextSibling) doc.insertBefore(inline, anchor.nextSibling);

    var targets = heads.slice();
    if (lab) targets.push(lab);
    var links = Array.prototype.slice.call(document.querySelectorAll(".outline a, .outline-inline a"));
    var ticking = false;
    function spy() {
      ticking = false;
      var active = targets[0].id;
      for (var i = 0; i < targets.length; i++) {
        if (targets[i].getBoundingClientRect().top <= 110) active = targets[i].id;
      }
      links.forEach(function (a) { a.classList.toggle("active", a.getAttribute("href") === "#" + active); });
    }
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(spy); }
    }, { passive: true });
    spy();
  }

  /* ---------- continuous prev / next ---------- */

  function navLink(cls, dir, label, href) {
    return '<a class="' + cls + '" href="' + href + '"><span class="dir">' + dir +
           '</span><span class="label">' + label + "</span></a>";
  }

  function renderPagenav() {
    var box = document.getElementById("pagenav");
    if (!box || !cur) return;
    var prev = flat[idx - 1], next = flat[idx + 1], h = "";
    if (!prev) {
      h += navLink("prev", "Back", "← Course map", root + "index.html");
    } else if (prev.ph.id !== cur.ph.id) {
      h += navLink("prev", "Previous phase", "← Phase " + esc(prev.ph.id) + " · " + esc(prev.p.n) + " " + esc(prev.p.title), prev.href);
    } else {
      h += navLink("prev", "Previous", "← " + esc(prev.p.n) + " — " + esc(prev.p.title), prev.href);
    }
    if (!next) {
      h += navLink("next", "End of course", "Course map →", root + "index.html");
    } else if (next.ph.id !== cur.ph.id) {
      h += navLink("next", "Next phase", "Phase " + esc(next.ph.id) + " — " + esc(next.ph.short) + " →", next.href);
    } else {
      h += navLink("next", "Next", esc(next.p.n) + " — " + esc(next.p.title) + " →", next.href);
    }
    box.innerHTML = h;
  }

  /* ---------- visited / finished / resume ---------- */

  function trackReading() {
    if (!cur) return;
    var box = document.getElementById("pagenav");
    if (box && "IntersectionObserver" in window) {
      var timer = null;
      var io = new IntersectionObserver(function (entries) {
        if (entries[0].isIntersecting) {
          // a short dwell, so a page that fits on one screen is not finished the instant it opens
          timer = setTimeout(function () {
            state = update(function (s) {
              s.pages[pageId] = s.pages[pageId] || { opened: true };
              s.pages[pageId].finished = true;
            });
            renderSidebar();
            io.disconnect();
          }, 2500);
        } else if (timer) {
          clearTimeout(timer);
          timer = null;
        }
      });
      io.observe(box);
    }
    var pending = null;
    window.addEventListener("scroll", function () {
      if (pending) return;
      pending = setTimeout(function () {
        pending = null;
        update(function (s) { s.last = { page: pageId, y: Math.round(window.scrollY), at: Date.now() }; });
      }, 400);
    }, { passive: true });
    if (resumeY) window.scrollTo(0, resumeY);
  }

  /* ---------- hub: continue button, per-phase counts, reset ---------- */

  function renderHub() {
    var slot = document.getElementById("resume");
    if (slot) {
      var last = state.last && byId(state.last.page);
      var target = last || flat[0];
      slot.innerHTML =
        '<a class="resume-card" href="' + target.href + (last ? "#resume" : "") + '">' +
        '<span class="dir">' + (last ? "Continue where you left off" : "Start here") + "</span>" +
        '<span class="label">Phase ' + esc(target.ph.id) + " · " + esc(target.p.n) + " " + esc(target.p.title) + " →</span></a>";
    }
    Array.prototype.forEach.call(document.querySelectorAll("[data-phase-count]"), function (node) {
      var ph = null;
      COURSE.phases.forEach(function (p) { if (p.id === node.getAttribute("data-phase-count")) ph = p; });
      if (!ph) return;
      var fin = 0, labs = 0, labsFin = 0;
      ph.pages.forEach(function (p) {
        if (pageState(ph.id + "/" + p.n) === "finished") fin++;
        if (p.lab) { labs++; if (labDone(p.lab.id)) labsFin++; }
      });
      node.textContent = "read " + fin + " / " + ph.pages.length + (labs ? " · labs " + labsFin + " / " + labs : "");
    });
    Array.prototype.forEach.call(document.querySelectorAll("[data-page-link]"), function (a) {
      var st = pageState(a.getAttribute("data-page-link"));
      if (st) a.insertAdjacentHTML("afterend", ' <span class="st ' + st + '" style="display:inline-block;margin-left:6px"></span>');
    });
    Array.prototype.forEach.call(document.querySelectorAll("[data-round-pts]"), function (node) {
      var pid = node.getAttribute("data-round-pts"), pt = points(pid);
      node.innerHTML = "<b>" + pt.got + "</b> / " + pt.max + " pts";
      var bar = node.parentNode.querySelector(".r-bar i");
      if (bar) bar.style.width = (pt.max ? Math.round(100 * pt.got / pt.max) : 0) + "%";
    });
    var standing = document.getElementById("standings");
    if (standing) {
      var all = points(), roundsDone = 0;
      COURSE.phases.forEach(function (ph) { if ((state.cases || {})[ph.id]) roundsDone++; });
      standing.innerHTML = "<span><b>" + all.got + "</b> / " + all.max + " points</span>" +
        "<span>cases closed " + roundsDone + " / " + COURSE.phases.length + "</span>";
    }
    var reset = document.getElementById("reset-progress");
    if (reset) {
      var armed = false;
      reset.addEventListener("click", function () {
        if (!armed) { armed = true; reset.textContent = "Click again to erase reading progress"; return; }
        try { localStorage.removeItem(KEY); } catch (e) { /* ignore */ }
        location.reload();
      });
    }
  }

  /* ---------- assemble ---------- */

  // lets in-page labs redraw the sidebar ticks the moment a lab is completed
  window.F1NAV = { refresh: function () { state = load(); renderSidebar(); }, points: function (ph) { state = load(); return points(ph); } };

  renderSidebar();
  var main = document.querySelector("main");
  var doc = main && main.querySelector(".doc");
  if (main && doc) {
    var inner = el("div", "main-inner");
    main.insertBefore(inner, doc);
    inner.appendChild(doc);
    renderCrumbs(main);
    renderOutline(doc, inner);
  }
  renderPagenav();
  renderHub();
  trackReading();

  // centre the current page inside the sidebar's own scroll area (never scrolls the window)
  var sidebar = document.getElementById("sidebar");
  var activeLink = sidebar && sidebar.querySelector("a.active");
  if (activeLink && sidebar.scrollHeight > sidebar.clientHeight) {
    var r = activeLink.getBoundingClientRect(), sr = sidebar.getBoundingClientRect();
    sidebar.scrollTop += r.top - sr.top - sidebar.clientHeight / 2;
  }
})();
