/* Search and phase filter for the merged glossary. Classic script: works from file://. */
(function () {
  "use strict";

  var search = document.getElementById("g-search");
  var chips = Array.prototype.slice.call(document.querySelectorAll(".g-chip"));
  var entries = Array.prototype.slice.call(document.querySelectorAll(".g-entry"));
  var scopes = Array.prototype.slice.call(document.querySelectorAll(".g-scope"));
  var count = document.getElementById("g-count");
  if (!search) return;

  var phase = "";

  function apply() {
    var q = search.value.trim().toLowerCase(), shown = 0;
    entries.forEach(function (e) {
      var inPhase = !phase || (" " + e.getAttribute("data-phases") + " ").indexOf(" " + phase + " ") >= 0;
      var match = !q || e.textContent.toLowerCase().indexOf(q) >= 0;
      e.hidden = !(inPhase && match);
      if (!e.hidden) shown++;
    });
    chips.forEach(function (c) { c.classList.toggle("on", c.getAttribute("data-phase") === phase); });
    scopes.forEach(function (s) { s.classList.toggle("on", !!phase && s.getAttribute("data-phase") === phase); });
    count.textContent = shown + " of " + entries.length + " terms";
  }

  function fromHash() {
    var m = /^#phase-(.+)$/.exec(location.hash);
    if (m) { phase = m[1]; apply(); }
  }

  search.addEventListener("input", apply);
  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      phase = c.getAttribute("data-phase");
      if (history.replaceState) history.replaceState(null, "", phase ? "#phase-" + phase : location.pathname);
      apply();
    });
  });
  window.addEventListener("hashchange", fromHash);

  apply();
  fromHash();
})();
