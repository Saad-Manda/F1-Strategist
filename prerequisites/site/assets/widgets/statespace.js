/* Widget: how many states a design has, and what one more feature does to that (lab p35-01). */
(function () {
  "use strict";
  var FACTORS = [
    ["lap", 55, "laps in the race"],
    ["compound", 5, "SOFT / MEDIUM / HARD / INTER / WET"],
    ["tyre_age", 55, "laps on the current tyre, capped at the race length"],
    ["used_mask", 8, "three dry compounds, each used or not"],
    ["sc_active", 2, "safety car out, or not"],
    ["weather", 3, "DRY / DAMP / WET"]
  ];
  var EXTRAS = [
    ["fuel load, to the nearest 0.1 kg (0 to 110 kg)", 1101],
    ["gap to the car ahead, to the nearest 0.1 s (0 to 60 s)", 601],
    ["track temperature, to the nearest degree (15 to 55 °C)", 41]
  ];
  var ACTIONS = 6, BYTES = 8;

  function group(n) { return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ","); }
  function size(bytes) {
    if (bytes < 1e6) return (bytes / 1e3).toFixed(0) + " kB";
    if (bytes < 1e9) return (bytes / 1e6).toFixed(1) + " MB";
    if (bytes < 1e12) return (bytes / 1e9).toFixed(1) + " GB";
    return group(bytes / 1e12) + " TB";
  }

  window.LAB_WIDGETS = window.LAB_WIDGETS || {};
  window.LAB_WIDGETS.statespace = function (node) {
    var html = '<table class="w-table"><tbody>';
    FACTORS.forEach(function (f, i) {
      html += '<tr><td><code>' + f[0] + '</code></td><td><input class="w-num" type="number" min="1" step="1" value="' + f[1] +
              '" data-i="' + i + '" aria-label="' + f[0] + ' values"></td><td class="w-note">' + f[2] + "</td></tr>";
    });
    EXTRAS.forEach(function (e, i) {
      html += '<tr><td colspan="2"><label><input class="w-extra" type="checkbox" data-i="' + i + '"> add: ' + e[0] +
              '</label></td><td class="w-note">× ' + group(e[1]) + "</td></tr>";
    });
    html += '</tbody></table><p class="w-read"></p><button class="lab-check w-reset" type="button">Reset to the real design</button>';
    node.innerHTML = html;
    var nums = Array.prototype.slice.call(node.querySelectorAll(".w-num"));
    var extras = Array.prototype.slice.call(node.querySelectorAll(".w-extra"));
    var read = node.querySelector(".w-read");

    function draw() {
      var states = 1;
      nums.forEach(function (n) { states *= Math.max(1, parseInt(n.value, 10) || 1); });
      extras.forEach(function (e, i) { if (e.checked) states *= EXTRAS[i][1]; });
      var entries = states * ACTIONS, bytes = entries * BYTES;
      var verdict = bytes < 2e9 ? "Fits in a laptop's memory: exact solving is possible."
                  : bytes < 64e9 ? "More than a laptop holds: exact solving needs a large server."
                  : "Far beyond any single machine: exact solving is out of reach.";
      read.innerHTML = "<strong>" + group(states) + "</strong> states × " + ACTIONS + " actions = " + group(entries) +
        " table entries, " + size(bytes) + " at 8 bytes each. " + verdict;
    }
    nums.concat(extras).forEach(function (el) { el.addEventListener("input", draw); el.addEventListener("change", draw); });
    node.querySelector(".w-reset").addEventListener("click", function () {
      nums.forEach(function (n, i) { n.value = FACTORS[i][1]; });
      extras.forEach(function (e) { e.checked = false; });
      draw();
    });
    draw();
  };
})();
