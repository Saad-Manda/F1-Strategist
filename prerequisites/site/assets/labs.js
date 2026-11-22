/* In-page labs for the prerequisites site: answer checking, saved answers, lab status.
   Classic script, no dependencies, works from file://. Loaded after nav.js.

   Markup contract (inside <section class="lab" data-lab-id="..." data-lab-format="...">):
     .lab-part                 a group of questions with one Check button (added here)
     .lab-q[data-type]         one question; data-answer holds the expected value
        num     <input>             data-tol = allowed absolute error (default 0.01)
        choice  radio inputs        data-answer = the correct input's value
        multi   checkbox inputs     data-answer = comma-separated correct values
        select  <select>            data-answer = the correct option's value
     .lab-q[data-explain]      shown once the answer is right
     .lab-solution             <details> kept hidden until the first attempt
     .lab-status               status line, filled in here
   Code labs (data-lab-format notebook | pytest) get their status line from
   window.LAB_PROGRESS, which `python -m labs status` regenerates. If a code lab contains
   .lab-q warm-up questions, those are checked here too, without affecting its status. */
(function () {
  "use strict";

  var KEY = "f1prereq.v1";

  function load() {
    var s;
    try { s = JSON.parse(localStorage.getItem(KEY)); } catch (e) { s = null; }
    s = s || {};
    s.labs = s.labs || {};
    s.answers = s.answers || {};
    return s;
  }
  function update(fn) {
    var s = load();
    fn(s);
    try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) { /* storage unavailable */ }
  }

  function inputs(q) { return Array.prototype.slice.call(q.querySelectorAll("input, select")); }

  function readAnswer(q) {
    var type = q.getAttribute("data-type"), els = inputs(q);
    if (type === "num") return els[0].value.trim();
    if (type === "select") return els[0].value;
    if (type === "choice") {
      var picked = els.filter(function (e) { return e.checked; })[0];
      return picked ? picked.value : "";
    }
    return els.filter(function (e) { return e.checked; }).map(function (e) { return e.value; }).sort().join(",");
  }

  function writeAnswer(q, value) {
    var type = q.getAttribute("data-type"), els = inputs(q);
    if (type === "num" || type === "select") { els[0].value = value; return; }
    var chosen = value ? value.split(",") : [];
    els.forEach(function (e) { e.checked = chosen.indexOf(e.value) >= 0; });
  }

  function isCorrect(q, value) {
    var type = q.getAttribute("data-type"), want = q.getAttribute("data-answer");
    if (value === "") return null;
    if (type === "num") {
      var got = parseFloat(value.replace(",", ".").replace("−", "-").replace("%", ""));
      if (isNaN(got)) return false;
      return Math.abs(got - parseFloat(want)) <= parseFloat(q.getAttribute("data-tol") || "0.01");
    }
    if (type === "multi") return value === want.split(",").sort().join(",");
    return value === want;
  }

  function mark(q, result) {
    var fb = q.querySelector(".lab-fb");
    if (!fb) { fb = document.createElement("span"); fb.className = "lab-fb"; q.appendChild(fb); }
    q.classList.toggle("right", result === true);
    q.classList.toggle("wrong", result === false);
    if (result === true) fb.textContent = "✓ " + (q.getAttribute("data-explain") || "Correct.");
    else if (result === false) fb.textContent = "✗ " + (q.getAttribute("data-nudge") || "Not yet. Try again.");
    else fb.textContent = "";
  }

  // warmup = true: the questions sit inside a code lab. They are checked and saved, but the
  // lab's status line and completion belong to the code checks.
  function setupInPageLab(lab, warmup) {
    var id = lab.getAttribute("data-lab-id");
    var qs = Array.prototype.slice.call(lab.querySelectorAll(".lab-q"));
    var status = warmup ? null : lab.querySelector(".lab-status");
    var solutions = Array.prototype.slice.call(lab.querySelectorAll(".lab-solution"));
    var saved = load().answers[id] || {};
    var attempted = Object.keys(saved).length > 0;

    function refresh(checkOnly) {
      var right = 0;
      checkOnly.forEach(function (q) { mark(q, isCorrect(q, readAnswer(q))); });
      qs.forEach(function (q) { if (q.classList.contains("right")) right++; });
      var done = right === qs.length;
      solutions.forEach(function (d) { d.hidden = !attempted; });
      if (status) {
        status.textContent = done ? "Lab complete: " + right + " of " + qs.length + " correct."
                                  : right + " of " + qs.length + " correct so far.";
        status.classList.toggle("done", done);
      }
      if (!warmup && done !== !!load().labs[id]) {
        update(function (s) { if (done) s.labs[id] = true; else delete s.labs[id]; });
        if (window.F1NAV) window.F1NAV.refresh();
      }
    }

    qs.forEach(function (q, i) { if (saved[i] != null) writeAnswer(q, saved[i]); });

    Array.prototype.forEach.call(lab.querySelectorAll(".lab-part"), function (part) {
      var mine = Array.prototype.slice.call(part.querySelectorAll(".lab-q"));
      if (!mine.length) return;
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "lab-check";
      btn.textContent = "Check";
      part.appendChild(btn);
      btn.addEventListener("click", function () {
        attempted = true;
        update(function (s) {
          s.answers[id] = s.answers[id] || {};
          mine.forEach(function (q) { s.answers[id][qs.indexOf(q)] = readAnswer(q); });
        });
        refresh(mine);
      });
    });

    // restore marks for answers saved on an earlier visit
    refresh(qs.filter(function (q, i) { return saved[i] != null && saved[i] !== ""; }));
  }

  function setupCodeLab(lab) {
    var id = lab.getAttribute("data-lab-id"), status = lab.querySelector(".lab-status");
    if (!status) return;
    var entry = (window.LAB_PROGRESS || {})[id];
    if (entry && entry.passed) {
      status.textContent = "Passed.";
      status.classList.add("done");
    } else {
      status.textContent = (entry ? "Status: " + entry.detail + ". " : "Not checked yet. ") +
        "Run python -m labs status and reload this page to update.";
    }
  }

  Array.prototype.forEach.call(document.querySelectorAll(".lab[data-lab-id]"), function (lab) {
    var format = lab.getAttribute("data-lab-format");
    if (format === "notebook" || format === "pytest") {
      setupCodeLab(lab);
      if (lab.querySelector(".lab-q")) setupInPageLab(lab, true);
    } else setupInPageLab(lab, false);
  });

  Array.prototype.forEach.call(document.querySelectorAll("[data-widget]"), function (node) {
    var mount = (window.LAB_WIDGETS || {})[node.getAttribute("data-widget")];
    if (mount) mount(node);
  });
})();
