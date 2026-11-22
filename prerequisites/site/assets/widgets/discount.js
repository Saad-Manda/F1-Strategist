/* Widget: how a discount factor weights the steps of a 20-step episode (lab p1-02). */
(function () {
  "use strict";
  var STEPS = 20, W = 560, H = 170, PAD = 24;

  window.LAB_WIDGETS = window.LAB_WIDGETS || {};
  window.LAB_WIDGETS.discount = function (node) {
    node.innerHTML =
      '<div class="w-row"><label>γ = <output class="w-val"></output> ' +
      '<input class="w-slider" type="range" min="0" max="1" step="0.01" value="0.5" aria-label="discount factor"></label></div>' +
      '<svg class="w-chart" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="weight on each step"></svg>' +
      '<p class="w-read"></p>';
    var slider = node.querySelector(".w-slider"), out = node.querySelector(".w-val");
    var svg = node.querySelector(".w-chart"), read = node.querySelector(".w-read");

    function draw() {
      var g = parseFloat(slider.value), weights = [], total = 0, last5 = 0, i;
      for (i = 0; i < STEPS; i++) { weights.push(Math.pow(g, i)); total += weights[i]; }
      for (i = STEPS - 5; i < STEPS; i++) last5 += weights[i];
      var bw = (W - 2 * PAD) / STEPS, bars = "";
      for (i = 0; i < STEPS; i++) {
        var h = weights[i] * (H - 2 * PAD);
        bars += '<rect class="' + (i >= STEPS - 5 ? "w-bar late" : "w-bar") + '" x="' + (PAD + i * bw + 2).toFixed(1) +
                '" y="' + (H - PAD - h).toFixed(1) + '" width="' + (bw - 4).toFixed(1) + '" height="' + Math.max(h, 0.5).toFixed(1) + '"></rect>';
      }
      svg.innerHTML = bars +
        '<text class="w-axis" x="' + PAD + '" y="' + (H - 6) + '">step 1</text>' +
        '<text class="w-axis" text-anchor="end" x="' + (W - PAD) + '" y="' + (H - 6) + '">step 20</text>';
      out.textContent = g.toFixed(2);
      read.textContent = "Return of an episode paying −1 on every step: " + (-total).toFixed(2) +
        ". The last five steps (highlighted) carry " + (100 * last5 / total).toFixed(1) + "% of the total weight.";
    }
    slider.addEventListener("input", draw);
    draw();
  };
})();
