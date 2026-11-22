/* Widget: page 08's two constant-pace cars, with and without the blocking line (lab p6-05). */
(function () {
  "use strict";
  var TICKS = 30, SLOW = 5.0, FAST = 4.5, PIT = 20, FOLLOW = 1.0;
  var W = 320, H = 180, PAD = 36;

  /* Same rule as page 08's BlockingPaddockRace: order by total time (a tie counts SLOW as ahead),
     and a car less than FOLLOW behind cannot be faster than the car ahead this tick. */
  function race(pitTick, blocking, fastStart) {
    var s = 0, f = fastStart, gaps = [f - s];
    for (var t = 0; t < TICKS; t++) {
      var ps = SLOW, pf = FAST + (t === pitTick ? PIT : 0);
      if (blocking) {
        if (f >= s && f - s < FOLLOW) pf = Math.max(pf, ps);
        else if (s > f && s - f < FOLLOW) ps = Math.max(ps, pf);
      }
      s += ps; f += pf; gaps.push(f - s);
    }
    return gaps;
  }

  window.LAB_WIDGETS = window.LAB_WIDGETS || {};
  window.LAB_WIDGETS.blocking = function (node) {
    node.innerHTML =
      '<div class="w-row"><label>FAST pits on tick: <output class="w-val" data-o="p"></output> ' +
      '<input class="w-slider" data-i="p" type="range" min="0" max="29" step="1" value="5" aria-label="pit tick"></label></div>' +
      '<div class="w-row"><label>FAST starts behind by (s): <output class="w-val" data-o="h"></output> ' +
      '<input class="w-slider" data-i="h" type="range" min="-3" max="3" step="0.1" value="0" aria-label="FAST start offset"></label></div>' +
      '<div class="w-row"><label><input type="checkbox" data-i="b" checked> blocking line on</label></div>' +
      '<div class="w-plot"></div><p class="w-read"></p>';
    var p = node.querySelector('[data-i="p"]'), h = node.querySelector('[data-i="h"]'), b = node.querySelector('[data-i="b"]');
    var plot = node.querySelector(".w-plot"), read = node.querySelector(".w-read");

    function draw() {
      var pv = parseInt(p.value, 10), hv = parseFloat(h.value), bv = b.checked;
      node.querySelector('[data-o="p"]').textContent = pv;
      node.querySelector('[data-o="h"]').textContent = hv.toFixed(1);
      var on = race(pv, bv, hv), off = race(pv, !bv, hv);
      var lo = Math.min(-5, Math.min.apply(null, on.concat(off))), hi = Math.max(25, Math.max.apply(null, on.concat(off)));
      function X(t) { return PAD + (t / TICKS) * (W - PAD - 8); }
      function Y(g) { return 14 + ((hi - g) / (hi - lo)) * (H - PAD - 14); }
      function line(gs, cls, dash) {
        return '<path class="' + cls + '"' + (dash ? ' style="stroke-dasharray:4 4;opacity:.6"' : "") + ' d="' +
          gs.map(function (g, t) { return (t ? "L" : "M") + X(t).toFixed(1) + "," + Y(g).toFixed(1); }).join("") + '"/>';
      }
      var svg = '<svg class="w-chart" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="gap between the cars over time">';
      svg += '<line class="w-true" x1="' + PAD + '" x2="' + (W - 8) + '" y1="' + Y(0) + '" y2="' + Y(0) + '"/>';
      svg += '<text class="w-axis" x="' + (PAD - 4) + '" y="' + (Y(0) + 4) + '" text-anchor="end">0</text>';
      svg += '<text class="w-axis" x="' + (PAD - 4) + '" y="' + (Y(hi) + 8) + '" text-anchor="end">' + hi.toFixed(0) + "</text>";
      svg += '<text class="w-axis" x="' + (W / 2) + '" y="' + (H - 6) + '" text-anchor="middle">tick (FAST − SLOW in seconds: above 0 means FAST is behind)</text>';
      svg += line(off, "w-line", true) + line(on, "w-line", false) + "</svg>";
      plot.innerHTML = svg;
      read.textContent = "Final gap (FAST − SLOW): " + on[TICKS].toFixed(1) + " s with the blocking line " + (bv ? "on" : "off") +
        "; " + off[TICKS].toFixed(1) + " s with it " + (bv ? "off" : "on") + " (dashed).";
    }
    [p, h, b].forEach(function (el) { el.addEventListener("input", draw); });
    draw();
  };
})();
