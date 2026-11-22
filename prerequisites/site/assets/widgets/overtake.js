/* Widget: the wake-loss line and the pass-chance curve, with the steepness as a knob (lab p6-04). */
(function () {
  "use strict";
  var W = 300, H = 170, PAD = 34;

  function wake(gap) { return gap >= 1.5 ? 0 : 0.5 * (1.5 - gap) / 1.5; }
  function chance(adv, k, follow, cap) {
    if (adv <= 0) return 0;
    var p = 1 / (1 + Math.exp(k * (-adv + 0.5))) + Math.min(0.1 * follow, 0.2);
    return cap ? Math.min(p, 0.95) : Math.min(p, 1);
  }

  function chart(title, xLabel, xMax, yMax, yTicks) {
    var s = '<svg class="w-chart" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + title + '">';
    s += '<text class="w-axis" x="' + PAD + '" y="12">' + title + "</text>";
    s += '<line class="w-true" x1="' + PAD + '" y1="' + (H - PAD) + '" x2="' + (W - 8) + '" y2="' + (H - PAD) + '"/>';
    s += '<line class="w-true" x1="' + PAD + '" y1="20" x2="' + PAD + '" y2="' + (H - PAD) + '"/>';
    for (var x = 0; x <= xMax + 1e-9; x += 0.5) {
      s += '<text class="w-axis" x="' + sx(x, xMax) + '" y="' + (H - PAD + 14) + '" text-anchor="middle">' + x.toFixed(1) + "</text>";
    }
    yTicks.forEach(function (y) { s += '<text class="w-axis" x="' + (PAD - 4) + '" y="' + (sy(y, yMax) + 4) + '" text-anchor="end">' + y + "</text>"; });
    s += '<text class="w-axis" x="' + (W / 2) + '" y="' + (H - 4) + '" text-anchor="middle">' + xLabel + "</text>";
    return s;
  }
  function sx(x, xMax) { return PAD + (x / xMax) * (W - PAD - 8); }
  function sy(y, yMax) { return H - PAD - (y / yMax) * (H - PAD - 20); }
  function path(fn, xMax, yMax) {
    var d = "";
    for (var i = 0; i <= 200; i++) { var x = (xMax * i) / 200; d += (i ? "L" : "M") + sx(x, xMax).toFixed(1) + "," + sy(fn(x), yMax).toFixed(1); }
    return d;
  }

  window.LAB_WIDGETS = window.LAB_WIDGETS || {};
  window.LAB_WIDGETS.overtake = function (node) {
    node.innerHTML =
      '<div class="w-row"><label>steepness k: <output class="w-val" data-o="k"></output> ' +
      '<input class="w-slider" data-i="k" type="range" min="1" max="8" step="0.01" value="5" aria-label="sigmoid steepness"></label></div>' +
      '<div class="w-row"><label>laps following: <output class="w-val" data-o="f"></output> ' +
      '<input class="w-slider" data-i="f" type="range" min="0" max="4" step="1" value="0" aria-label="laps following"></label></div>' +
      '<div class="w-row"><label><input type="checkbox" data-i="cap" checked> cap at 0.95</label></div>' +
      '<div class="w-plots"></div><p class="w-read"></p>';
    var k = node.querySelector('[data-i="k"]'), f = node.querySelector('[data-i="f"]'), cap = node.querySelector('[data-i="cap"]');
    var plots = node.querySelector(".w-plots"), read = node.querySelector(".w-read");

    function draw() {
      var kv = parseFloat(k.value), fv = parseInt(f.value, 10), cv = cap.checked;
      node.querySelector('[data-o="k"]').textContent = kv.toFixed(2);
      node.querySelector('[data-o="f"]').textContent = fv;
      var a = chart("wake loss (s) against gap", "gap to the car ahead, s", 2, 0.5, [0, 0.25, 0.5]);
      a += '<path class="w-line" d="' + path(wake, 2, 0.5) + '"/></svg>';
      var b = chart("pass chance against pace advantage", "seconds faster this lap", 2, 1, [0, 0.5, 1]);
      b += '<path class="w-line" d="' + path(function (x) { return chance(x, kv, fv, cv); }, 2, 1) + '"/>';
      [[0.5, 0.5], [1.0, 0.8], [1.5, 0.95]].forEach(function (p) {
        b += '<circle class="w-dot" style="opacity:1" cx="' + sx(p[0], 2) + '" cy="' + sy(p[1], 1) + '" r="4"><title>docstring: ' + p[1] * 100 + "% at " + p[0] + " s</title></circle>";
      });
      b += "</svg>";
      plots.innerHTML = a + b;
      read.textContent = "Pass chance at 0.5 / 1.0 / 1.5 s faster: " +
        [0.5, 1.0, 1.5].map(function (x) { return (100 * chance(x, kv, fv, cv)).toFixed(1) + "%"; }).join(" / ") +
        ". The grey dots are the plan's docstring claims: 50%, 80%, 95%.";
    }
    [k, f, cap].forEach(function (el) { el.addEventListener("input", draw); });
    draw();
  };
})();
