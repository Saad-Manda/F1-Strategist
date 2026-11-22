/* Widget: PPO's clipped objective against the probability ratio, with A and epsilon as knobs (lab p9-04). */
(function () {
  "use strict";
  var W = 600, H = 260, PAD = 40, RMAX = 2.5;

  function clip(r, e) { return Math.min(Math.max(r, 1 - e), 1 + e); }
  function objective(r, a, e) { return Math.min(r * a, clip(r, e) * a); }
  function bound(r, a, e) { return (a > 0 && r >= 1 + e) || (a < 0 && r <= 1 - e); }
  function slope(r, a, e) { return bound(r, a, e) ? 0 : a; }

  window.LAB_WIDGETS = window.LAB_WIDGETS || {};
  window.LAB_WIDGETS.clip = function (node) {
    node.innerHTML =
      '<div class="w-row"><label>advantage A: <output class="w-val" data-o="a"></output> ' +
      '<input class="w-slider" data-i="a" type="range" min="-2" max="2" step="0.1" value="1" aria-label="advantage"></label></div>' +
      '<div class="w-row"><label>clip ε: <output class="w-val" data-o="e"></output> ' +
      '<input class="w-slider" data-i="e" type="range" min="0.05" max="0.4" step="0.01" value="0.2" aria-label="clip range"></label></div>' +
      '<div class="w-row"><label>ratio r: <output class="w-val" data-o="r"></output> ' +
      '<input class="w-slider" data-i="r" type="range" min="0" max="2.5" step="0.01" value="1" aria-label="probability ratio"></label></div>' +
      '<div class="w-plot"></div><p class="w-read"></p>';
    var ia = node.querySelector('[data-i="a"]'), ie = node.querySelector('[data-i="e"]'), ir = node.querySelector('[data-i="r"]');
    var plot = node.querySelector(".w-plot"), read = node.querySelector(".w-read");

    function draw() {
      var a = parseFloat(ia.value), e = parseFloat(ie.value), r = parseFloat(ir.value);
      node.querySelector('[data-o="a"]').textContent = a.toFixed(1);
      node.querySelector('[data-o="e"]').textContent = e.toFixed(2);
      node.querySelector('[data-o="r"]').textContent = r.toFixed(2);
      var ymax = Math.max(1, Math.abs(a) * RMAX), ymin = -ymax;
      function sx(x) { return PAD + (x / RMAX) * (W - PAD - 10); }
      function sy(y) { return H - PAD - ((y - ymin) / (ymax - ymin)) * (H - PAD - 16); }
      function path(fn) {
        var d = "";
        for (var i = 0; i <= 250; i++) { var x = (RMAX * i) / 250; d += (i ? "L" : "M") + sx(x).toFixed(1) + "," + sy(fn(x)).toFixed(1); }
        return d;
      }
      var s = '<svg class="w-chart" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="clipped objective against the ratio">';
      // shade where the gradient is zero
      if (a > 0) s += '<rect class="w-bar" style="opacity:0.18" x="' + sx(1 + e) + '" y="16" width="' + (sx(RMAX) - sx(1 + e)) + '" height="' + (H - PAD - 16) + '"><title>gradient is zero here</title></rect>';
      if (a < 0) s += '<rect class="w-bar" style="opacity:0.18" x="' + sx(0) + '" y="16" width="' + (sx(1 - e) - sx(0)) + '" height="' + (H - PAD - 16) + '"><title>gradient is zero here</title></rect>';
      s += '<line class="w-true" style="stroke-dasharray:none" x1="' + PAD + '" y1="' + sy(0) + '" x2="' + (W - 10) + '" y2="' + sy(0) + '"/>';
      [0, 0.5, 1, 1.5, 2, 2.5].forEach(function (x) {
        s += '<text class="w-axis" x="' + sx(x) + '" y="' + (H - PAD + 14) + '" text-anchor="middle">' + x.toFixed(1) + "</text>";
      });
      [ymin, 0, ymax].forEach(function (y) { s += '<text class="w-axis" x="' + (PAD - 4) + '" y="' + (sy(y) + 4) + '" text-anchor="end">' + y.toFixed(1) + "</text>"; });
      s += '<text class="w-axis" x="' + (W / 2) + '" y="' + (H - 6) + '" text-anchor="middle">probability ratio r = π_new(a) / π_old(a)</text>';
      s += '<path class="w-true" style="fill:none" d="' + path(function (x) { return x * a; }) + '"><title>unclipped r·A</title></path>';
      s += '<path class="w-line" d="' + path(function (x) { return objective(x, a, e); }) + '"><title>min(r·A, clip(r)·A)</title></path>';
      s += '<circle class="w-dot" style="opacity:1" cx="' + sx(r) + '" cy="' + sy(objective(r, a, e)) + '" r="5"></circle>';
      s += "</svg>";
      plot.innerHTML = s;
      var b = bound(r, a, e);
      read.textContent = "At r = " + r.toFixed(2) + ": r·A = " + (r * a).toFixed(2) + ", clip(r)·A = " + (clip(r, e) * a).toFixed(2) +
        ", objective = " + objective(r, a, e).toFixed(2) + ". Its slope in r is " + slope(r, a, e).toFixed(2) +
        (b ? ": the clip binds, so the update leaves this sample alone." : a === 0 ? "." : ": the unclipped term is the smaller one, so the update still pushes.") +
        " Dashed: r·A without the clip. Shaded: where the slope is zero.";
    }
    [ia, ie, ir].forEach(function (el) { el.addEventListener("input", draw); });
    draw();
  };
})();
