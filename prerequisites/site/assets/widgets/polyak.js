/* Widget: how fast a soft-updated target network follows a jump in the online network (lab p5-03). */
(function () {
  "use strict";
  var W = 560, H = 190, PAD = 26, TRAIN_FREQ = 4, LAPS = 52;

  window.LAB_WIDGETS = window.LAB_WIDGETS || {};
  window.LAB_WIDGETS.polyak = function (node) {
    node.innerHTML =
      '<div class="w-row"><label>τ = <output class="w-val"></output> ' +
      '<input class="w-slider" type="range" min="0.001" max="0.1" step="0.001" value="0.005" aria-label="soft update rate tau"></label></div>' +
      '<svg class="w-chart" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="share of the gap still open after each update"></svg>' +
      '<p class="w-read"></p>';
    var slider = node.querySelector(".w-slider"), out = node.querySelector(".w-val");
    var svg = node.querySelector(".w-chart"), read = node.querySelector(".w-read");

    function draw() {
      var tau = parseFloat(slider.value), exact = Math.log(0.5) / Math.log(1 - tau);
      var half = Math.ceil(exact - 1e-9), span = Math.max(20, 4 * half), path = "", hard, n;
      function x(i) { return PAD + (W - 2 * PAD) * i / span; }
      function y(v) { return PAD + (H - 2 * PAD) * (1 - v); }
      for (n = 0; n <= span; n += Math.max(1, Math.floor(span / 300))) {
        path += (n ? "L" : "M") + x(n).toFixed(1) + " " + y(Math.pow(1 - tau, n)).toFixed(1);
      }
      hard = "M" + x(0) + " " + y(1) + "L" + x(half) + " " + y(1) + "L" + x(half) + " " + y(0) + "L" + x(span) + " " + y(0);
      svg.innerHTML =
        '<line class="w-true" x1="' + PAD + '" x2="' + (W - PAD) + '" y1="' + y(0.5) + '" y2="' + y(0.5) + '"></line>' +
        '<path class="w-true" fill="none" d="' + hard + '"></path>' +
        '<path class="w-line" d="' + path + '"></path>' +
        '<text class="w-axis" x="' + PAD + '" y="' + (H - 6) + '">update 0</text>' +
        '<text class="w-axis" text-anchor="end" x="' + (W - PAD) + '" y="' + (H - 6) + '">update ' + span + "</text>" +
        '<text class="w-axis" x="' + (PAD + 4) + '" y="' + (y(0.5) - 5) + '">half the gap</text>' +
        '<text class="w-axis" text-anchor="end" x="' + (x(half) - 4) + '" y="' + (y(1) + 14) + '">hard copy at update ' + half + "</text>";
      out.textContent = tau.toFixed(3);
      read.textContent = "Solid line: the share of the gap still open after each soft update, (1 − τ)ⁿ. Dashed: a hard copy made at the same moment, for comparison. " +
        "At τ = " + tau.toFixed(3) + " the formula gives ln 0.5 / ln(1 − τ) = " + exact.toFixed(1) + ", so half the gap is closed after update " + half +
        ". With one update every " + TRAIN_FREQ + " laps that is " + (half * TRAIN_FREQ) + " laps, or " + (half * TRAIN_FREQ / LAPS).toFixed(1) + " races of " + LAPS + " laps.";
    }
    slider.addEventListener("input", draw);
    draw();
  };
})();
