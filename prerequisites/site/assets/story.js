/* Story components for the course pages: cold opens, reveals, case closing.
   Classic script, no dependencies, works from file://. Load after nav.js.

   Markup contract
     <section class="cold-open" data-call="p1-01">           the moment and the question
       <p class="co-label">, <p class="co-moment">, <p class="co-ask">
       <div class="lab-q" data-type="choice" data-answer="b">  radio options, label.lab-opt
       <p class="co-status">                                   filled in here
     <section class="reveal closed" data-for="p1-01">          further down the page
       <div class="co-pair"> ... <b data-slot="mine"> ... </div>  "you called" is filled in here
       <div class="co-body"> the explanation </div>
     <button data-close-case="1">                              closes the phase's case
   A call is locked the moment it is made (that is the point of a cold open) and stored in
   f1prereq.v1 as calls[id] = { pick, right, at }. Opening a reveal before calling is allowed;
   it just records no call. Cases closed are stored as cases[phaseId] = at. */
(function () {
  "use strict";

  var KEY = "f1prereq.v1";

  function load() {
    var s;
    try { s = JSON.parse(localStorage.getItem(KEY)); } catch (e) { s = null; }
    s = s || {};
    s.calls = s.calls || {};
    s.cases = s.cases || {};
    return s;
  }
  function update(fn) {
    var s = load();
    fn(s);
    try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) { /* storage unavailable */ }
    return s;
  }
  function each(sel, fn) { Array.prototype.forEach.call(document.querySelectorAll(sel), fn); }
  function refreshNav() { if (window.F1NAV) window.F1NAV.refresh(); }

  function optionText(q, value) {
    var inp = q.querySelector('input[value="' + value + '"]');
    var lab = inp && inp.closest("label");
    return lab ? lab.textContent.trim() : value;
  }

  function paintReveal(id) {
    var call = load().calls[id];
    each('.reveal[data-for="' + id + '"]', function (rv) {
      var slot = rv.querySelector('[data-slot="mine"]');
      var co = document.querySelector('.cold-open[data-call="' + id + '"] .lab-q');
      if (slot) {
        if (call && co) {
          slot.textContent = optionText(co, call.pick) + (call.right ? "  ✓" : "");
          slot.className = call.right ? "t-green" : "t-yellow";
        } else {
          slot.textContent = "no call made";
          slot.className = "";
        }
      }
      if (call) rv.classList.remove("closed");
    });
  }

  function lock(co, q, call) {
    co.classList.add("locked");
    Array.prototype.forEach.call(q.querySelectorAll("input"), function (inp) {
      inp.disabled = true;
      inp.checked = inp.value === call.pick;
      var lab = inp.closest(".lab-opt");
      if (lab) lab.classList.toggle("mine", inp.value === call.pick);
    });
    var st = co.querySelector(".co-status");
    var rv = document.querySelector('.reveal[data-for="' + co.getAttribute("data-call") + '"]');
    if (st) {
      st.innerHTML = "Call locked in. " + (rv ? '<a href="#reveal-' + co.getAttribute("data-call") +
        '">Read on</a>: this page works it out, and the reveal shows whether it holds.' : "");
    }
  }

  each(".cold-open[data-call]", function (co) {
    var id = co.getAttribute("data-call"), q = co.querySelector(".lab-q");
    if (!q) return;
    var saved = load().calls[id];
    if (saved) { lock(co, q, saved); return; }
    var st = co.querySelector(".co-status");
    if (st) st.textContent = "Make the call before reading on. It locks once made.";
    Array.prototype.forEach.call(q.querySelectorAll("input"), function (inp) {
      inp.addEventListener("change", function () {
        if (load().calls[id]) return;
        var call = { pick: inp.value, right: inp.value === q.getAttribute("data-answer"), at: Date.now() };
        update(function (s) { s.calls[id] = call; });
        lock(co, q, call);
        paintReveal(id);
        refreshNav();
      });
    });
  });

  each(".reveal[data-for]", function (rv) {
    var id = rv.getAttribute("data-for");
    if (!rv.id) rv.id = "reveal-" + id;
    if (!rv.querySelector(".co-open")) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "co-open";
      btn.textContent = "Show the reveal";
      btn.addEventListener("click", function () { rv.classList.remove("closed"); });
      rv.appendChild(btn);
    }
    paintReveal(id);
  });

  each("[data-close-case]", function (btn) {
    var ph = btn.getAttribute("data-close-case");
    function paint() {
      var at = load().cases[ph];
      btn.disabled = !!at;
      btn.textContent = at ? "Case closed ✓" : btn.getAttribute("data-label") || "Close the case";
    }
    btn.addEventListener("click", function () {
      update(function (s) { s.cases[ph] = Date.now(); });
      paint();
      refreshNav();
    });
    paint();
  });
})();
