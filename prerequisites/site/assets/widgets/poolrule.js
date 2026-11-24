/* Widget: the Phase 8 plan's CheckpointPool.sample(), run in the browser (Phase 8 case brief, page 03).
   cut = max(1, int(0.8 n)); with probability 0.7 pick from checkpoints[cut:], else from
   checkpoints[:cut]. np.random.choice on an empty list raises ValueError, so this counts a crash.
   The plan's training loop holds one checkpoint for episodes 0 to 999 and samples one opponent
   per episode (two cars). "With the guard": a pool with no recent slice samples from what it has. */
(function () {
  "use strict";
  var W = 560, H = 150, PAD = 26, BIAS = 0.7, SIZES = [1, 2, 3, 5, 6, 8, 10, 20, 50];

  function rng(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function comma(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ","); }

  /* One call of sample() on a pool of n entries: the index picked, or -1 for ValueError. */
  function sample(n, r, guard) {
    var cut = Math.max(1, Math.floor(0.8 * n));
    var recent = n - cut, older = cut;
    if (r() < BIAS) {
      if (!recent) return guard ? Math.floor(r() * n) : -1;
      return cut + Math.floor(r() * recent);
    }
    return Math.floor(r() * older);
  }

  window.LAB_WIDGETS = window.LAB_WIDGETS || {};
  window.LAB_WIDGETS.poolrule = function (node) {
    var n = parseInt(node.getAttribute("data-n") || "1", 10), guard = false, runs = 0, result = null;
    node.innerHTML =
      '<div class="w-row"><label>Checkpoints in the pool <select class="w-n">' + SIZES.map(function (s) {
        return '<option value="' + s + '"' + (s === n ? " selected" : "") + ">" + s + "</option>";
      }).join("") + '</select></label> <label class="pw-toggle"><input type="checkbox" class="w-guard"> with the one-line guard</label></div>' +
      '<div class="w-row"><button type="button" class="pw-btn go w-sample">Sample 1,000 opponents</button> ' +
      '<button type="button" class="pw-btn w-train">Start the plan\'s training 1,000 times</button></div>' +
      '<svg class="w-chart" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="how often each checkpoint is picked"></svg>' +
      '<p class="w-read" aria-live="polite"></p>';
    var svg = node.querySelector(".w-chart"), read = node.querySelector(".w-read");

    function slices() {
      var cut = Math.max(1, Math.floor(0.8 * n));
      return "With " + n + " checkpoint" + (n > 1 ? "s" : "") + ", <code>cut = max(1, int(0.8 × " + n + ")) = " + cut + "</code>: the newest-20% slice <code>checkpoints[" + cut + ":]</code> holds " +
        (n - cut) + " entr" + (n - cut === 1 ? "y" : "ies") + ", the older slice holds " + cut + ".";
    }

    function draw() {
      var bars = "", cells = result && result.kind === "sample" ? result.counts.length + 1 : 0;
      if (cells) {
        var max = Math.max.apply(null, result.counts.concat([result.crash, 1])), bw = (W - 2 * PAD) / cells;
        function bar(i, v, label, cls) {
          var h = (H - 2 * PAD) * v / max, x = PAD + i * bw;
          return '<rect class="' + cls + '" x="' + (x + 2).toFixed(1) + '" y="' + (H - PAD - h).toFixed(1) + '" width="' + Math.max(1, bw - 4).toFixed(1) + '" height="' + h.toFixed(1) + '"></rect>' +
            (cells <= 12 ? '<text class="w-axis" text-anchor="middle" x="' + (x + bw / 2).toFixed(1) + '" y="' + (H - 8) + '">' + label + "</text>" : "");
        }
        result.counts.forEach(function (c, i) { bars += bar(i, c, "#" + i, "w-bar"); });
        bars += bar(result.counts.length, result.crash, "crash", "w-bar bad");
        bars += '<text class="w-axis" x="' + PAD + '" y="14">picks per checkpoint, oldest first, out of 1,000</text>';
      }
      svg.innerHTML = bars;
      svg.style.display = cells ? "" : "none";
      if (!result) { read.innerHTML = slices() + " Press a button."; return; }
      if (result.kind === "sample") {
        read.innerHTML = slices() + " Of 1,000 calls, <b>" + comma(result.crash) + "</b> raised <code>ValueError</code>" +
          (n === 1 && !guard ? ": every time the 70% branch was taken, it chose from an empty list. The exact rate is 0.7." : result.crash ? "." : ", and every entry could be picked.") +
          (n > 1 ? " Each of the newest " + (n - Math.max(1, Math.floor(0.8 * n))) + " is picked " + (100 * BIAS / (n - Math.max(1, Math.floor(0.8 * n)))).toFixed(1) + "% of the time, each older one " + (100 * (1 - BIAS) / Math.max(1, Math.floor(0.8 * n))).toFixed(2) + "%." : "");
      } else {
        read.innerHTML = "The pool holds one checkpoint, the untrained seed, until episode 1,000 adds the second, and each episode samples one opponent. " +
          (guard ? "With the guard, all 1,000 runs reach episode 1,000." :
            "Of 1,000 runs, <b>" + comma(result.died0) + "</b> died at episode 0, " + comma(result.died5) + " within the first five episodes, and the longest got to episode " + result.longest +
            ". None reached episode 1,000: that would take 1,000 escapes in a row at 0.3 each, 0.3<sup>1000</sup>.");
      }
    }

    node.querySelector(".w-n").addEventListener("change", function (e) { n = parseInt(e.target.value, 10); result = null; draw(); });
    node.querySelector(".w-guard").addEventListener("change", function (e) { guard = e.target.checked; result = null; draw(); });
    node.querySelector(".w-sample").addEventListener("click", function () {
      var r = rng(8000 + runs++), counts = new Array(n).fill(0), crash = 0;
      for (var k = 0; k < 1000; k++) { var i = sample(n, r, guard); if (i < 0) crash++; else counts[i]++; }
      result = { kind: "sample", counts: counts, crash: crash }; draw();
    });
    node.querySelector(".w-train").addEventListener("click", function () {
      var r = rng(9000 + runs++), died0 = 0, died5 = 0, longest = 0;
      for (var k = 0; k < 1000; k++) {
        var ep = 0;
        while (ep < 1000 && sample(1, r, guard) >= 0) ep++;
        if (ep < 1000) { if (ep === 0) died0++; if (ep < 5) died5++; longest = Math.max(longest, ep); }
      }
      result = { kind: "train", died0: died0, died5: died5, longest: longest }; draw();
    });
    draw();
  };
})();
