/* Widget: one table cell estimating a noisy value, at a learning rate you choose (lab p4-01). */
(function () {
  "use strict";
  var N = 200, TRUE = -10, NOISE = 4, W = 560, H = 190, PAD = 26, LO = -16, HI = 1;

  // a fixed stream of samples, the same on every visit, so answers can be checked
  var samples = (function () {
    var out = [], seed = 12345;
    for (var i = 0; i < N; i++) {
      seed = (seed * 1103515245 + 12345) % 2147483648;
      out.push(TRUE + NOISE * (2 * seed / 2147483648 - 1));
    }
    return out;
  })();

  function x(i) { return PAD + (W - 2 * PAD) * i / (N - 1); }
  function y(v) { return PAD + (H - 2 * PAD) * (HI - Math.max(LO, Math.min(HI, v))) / (HI - LO); }

  window.LAB_WIDGETS = window.LAB_WIDGETS || {};
  window.LAB_WIDGETS.alphanudge = function (node) {
    node.innerHTML =
      '<div class="w-row"><label>α = <output class="w-val"></output> ' +
      '<input class="w-slider" type="range" min="0.01" max="1" step="0.01" value="0.1" aria-label="learning rate"></label></div>' +
      '<svg class="w-chart" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="estimate after each sample"></svg>' +
      '<p class="w-read"></p>';
    var slider = node.querySelector(".w-slider"), out = node.querySelector(".w-val");
    var svg = node.querySelector(".w-chart"), read = node.querySelector(".w-read");

    function draw() {
      var alpha = parseFloat(slider.value), e = 0, path = "", dots = "", lo = Infinity, hi = -Infinity, arrived = null, i;
      for (i = 0; i < N; i++) {
        e += alpha * (samples[i] - e);
        path += (i ? "L" : "M") + x(i).toFixed(1) + " " + y(e).toFixed(1);
        dots += '<circle class="w-dot" cx="' + x(i).toFixed(1) + '" cy="' + y(samples[i]).toFixed(1) + '" r="1.6"></circle>';
        if (arrived === null && Math.abs(e - TRUE) <= 1) arrived = i + 1;
        if (i >= N - 100) { lo = Math.min(lo, e); hi = Math.max(hi, e); }
      }
      svg.innerHTML = dots +
        '<line class="w-true" x1="' + PAD + '" x2="' + (W - PAD) + '" y1="' + y(TRUE) + '" y2="' + y(TRUE) + '"></line>' +
        '<path class="w-line" d="' + path + '"></path>' +
        '<text class="w-axis" x="' + PAD + '" y="' + (H - 6) + '">sample 1</text>' +
        '<text class="w-axis" text-anchor="end" x="' + (W - PAD) + '" y="' + (H - 6) + '">sample 200</text>' +
        '<text class="w-axis" x="' + (W - PAD - 4) + '" text-anchor="end" y="' + (y(TRUE) - 5) + '">true value −10</text>';
      out.textContent = alpha.toFixed(2);
      read.textContent = "Estimate after 200 samples: " + e.toFixed(2) + ". " +
        (arrived === null ? "It never came within 1 of the true value." : "It first came within 1 of the true value at sample " + arrived + ".") +
        " Over the last 100 samples it ranged from " + lo.toFixed(2) + " to " + hi.toFixed(2) + ", a spread of " + (hi - lo).toFixed(2) + ".";
    }
    slider.addEventListener("input", draw);
    draw();
  };
})();
