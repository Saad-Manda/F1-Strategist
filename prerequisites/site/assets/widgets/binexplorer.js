/* Widget: which tyre ages share a bin, for a bin count you choose (lab p4-06). */
(function () {
  "use strict";
  var MAX_AGE = 50, FIRST = 18, LAST = 39, WIN_LO = 25, WIN_HI = 32, OPTIMAL = 27;

  // whole-number arithmetic, so that bin edges are exact
  function bin(age, n) { return Math.min(Math.floor(age * n / MAX_AGE), n - 1); }

  window.LAB_WIDGETS = window.LAB_WIDGETS || {};
  window.LAB_WIDGETS.binexplorer = function (node) {
    node.innerHTML =
      '<div class="w-row"><label>tyre-age bins: <output class="w-val"></output> ' +
      '<input class="w-slider" type="range" min="5" max="50" step="1" value="10" aria-label="number of tyre-age bins"></label></div>' +
      '<div class="w-cells" role="img" aria-label="tyre ages coloured by bin"></div>' +
      '<p class="w-read"></p>';
    var slider = node.querySelector(".w-slider"), out = node.querySelector(".w-val");
    var cells = node.querySelector(".w-cells"), read = node.querySelector(".w-read");

    function draw() {
      var n = parseInt(slider.value, 10), html = "", groups = [], age, b;
      for (age = FIRST; age <= LAST; age++) {
        b = bin(age, n);
        var cls = "w-cell" + (b % 2 ? " odd" : "") + (age >= WIN_LO && age <= WIN_HI ? " win" : "") + (age === OPTIMAL ? " best" : "");
        html += '<span class="' + cls + '" title="age ' + age + ": bin " + b + '">' + age + "</span>";
        if (age >= WIN_LO && age <= WIN_HI) {
          if (!groups.length || groups[groups.length - 1].b !== b) groups.push({ b: b, from: age, to: age });
          else groups[groups.length - 1].to = age;
        }
      }
      cells.innerHTML = html;
      out.textContent = n;
      var parts = groups.map(function (g) { return (g.from === g.to ? "" + g.from : g.from + "–" + g.to) + " (bin " + g.b + ")"; });
      read.textContent = "Each bin covers " + (MAX_AGE / n).toFixed(2) + " laps of tyre age. The 8 laps of the pit window (outlined, ages 25–32) fall into " +
        groups.length + " bin" + (groups.length === 1 ? "" : "s") + ": " + parts.join(", ") + ".";
    }
    slider.addEventListener("input", draw);
    draw();
  };
})();
