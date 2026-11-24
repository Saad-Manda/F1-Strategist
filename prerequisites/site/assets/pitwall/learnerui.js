/* Pit Wall, Learner mode (Phase 4): two table learners train on the toy race side by side, one
   with fine bins and one with the plan's coarse 5-lap bins. Needs engine.js, oracle.js,
   learner.js and ui.js. ui.js mounts it for <div data-widget="pitwall" data-mode="learner">.

   Options (data attributes on the node)
     data-seed    the learners' random seed (default 1); "New learners" draws another
     data-start   races to train before the panel first draws (default 0)
     data-tune    "1" shows the settings: learning rate and how long exploration lasts
   Personal best: pitwall.best.learner = { gap, bins, races, seed, at }, the smallest gap to the
   optimum either learner's greedy policy has reached. Points count a gap of 1 s or less. */
(function (root) {
  "use strict";
  var PW = root.PitWall;
  if (!PW || !PW.learner || !PW.oracle) return;
  var L = PW.learner, A = PW.A, DRY = PW.DRY;
  var BUDGET = 20000, CHUNK = 250, EVERY = 500, YMAX = 35;
  var KINDS = [
    { id: "fine", name: "fine bins", sub: "one bin per lap", color: "var(--wet)" },
    { id: "coarse", name: "coarse bins", sub: "5-lap bins, as in the plan", color: "var(--t-yellow)" }
  ];
  var ctx = null;

  function context() {
    if (!ctx) {
      var m = new PW.RaceModel(), sol = PW.oracle.solve(m);
      ctx = { model: m, sol: sol, optimum: sol.value({ lap: 1, compound: A, age: 1, sc: 0, usedBoth: false, weather: DRY }) };
    }
    return ctx;
  }
  function comma(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ","); }

  /* "box for B on lap 8" from a list of actions, one per lap. */
  function stops(actions) {
    var out = [];
    actions.forEach(function (a, i) { if (a !== PW.STAY_OUT) out.push((a === PW.PIT_B ? "B" : "A") + " on lap " + (i + 1)); });
    return out.length ? "boxes for " + out.join(", then ") : "never stops";
  }

  function mountLearner(node) {
    var U = PW.ui, fx = U.fx;
    var seed = parseInt(node.getAttribute("data-seed") || "1", 10);
    var tune = node.getAttribute("data-tune") === "1";
    var alpha = 0.1, decayRaces = 6000;
    var learners, curves, busy = false, target = 0, msg = "", tbl = { open: false };

    node.classList.add("pw-panel", "pitwall", "pw-learner");

    function reset() {
      learners = {}; curves = {};
      KINDS.forEach(function (k) {
        learners[k.id] = new L.Learner({ bins: k.id, seed: seed, alpha: alpha, decaySteps: decayRaces * 20 });
        curves[k.id] = [];
      });
      target = 0;
      msg = "Two learners, the same race, the same random numbers. The only difference is how finely each one's table slices laps and tyre age.";
    }

    function checkpoint() {
      var c = context(), bestGap = Infinity, bestKind = null;
      KINDS.forEach(function (k) {
        var l = learners[k.id], sc = l.score(c.model, c.sol);
        l.last = sc;
        curves[k.id].push([l.races, sc.gap]);
        if (sc.gap < bestGap) { bestGap = sc.gap; bestKind = k.id; }
      });
      var prev = U.load().pitwall.best.learner;
      if (!prev || bestGap < prev.gap - 1e-9) {
        U.save(function (s) {
          s.pitwall.best.learner = { gap: bestGap, bins: bestKind, races: learners[bestKind].races, seed: seed, at: Date.now() };
        });
        if (root.F1NAV) root.F1NAV.refresh();
      }
    }

    function trainTo(t, sync) {
      target = Math.min(BUDGET, t);
      if (busy) return;
      busy = true;
      function step() {
        var l0 = learners.fine;
        if (l0.races >= target) {
          busy = false;
          var c = context();
          msg = "After " + comma(l0.races) + " races: fine bins " + stops(learners.fine.quietPlan(c.model)) +
            "; coarse bins " + stops(learners.coarse.quietPlan(c.model)) + ". The oracle " +
            stops(L.quietPlan(c.model, c.sol.asPolicy())) + ". (On a race with no safety car.)";
          if (!sync) draw();
          return;
        }
        var n = Math.min(CHUNK, target - l0.races);
        KINDS.forEach(function (k) { learners[k.id].train(context().model, n); });
        if (l0.races % EVERY === 0 || l0.races === target) checkpoint();
        if (sync) step();
        else { draw(); setTimeout(step, 0); }
      }
      step();
    }

    function chart() {
      var W = 640, H = 190, L0 = 34, R = 10, T = 10, B = 26, xmax = BUDGET;
      function X(r) { return L0 + (W - L0 - R) * r / xmax; }
      function Y(g) { return T + (H - T - B) * (1 - Math.min(g, YMAX) / YMAX); }
      var h = '<svg class="pw-chart" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Gap to the optimum against races trained">';
      [0, 10, 20, 30].forEach(function (g) {
        h += '<line x1="' + L0 + '" x2="' + (W - R) + '" y1="' + Y(g) + '" y2="' + Y(g) + '" class="grid"/>' +
          '<text x="' + (L0 - 6) + '" y="' + (Y(g) + 4) + '" text-anchor="end">' + g + "</text>";
      });
      h += '<line x1="' + L0 + '" x2="' + (W - R) + '" y1="' + Y(1) + '" y2="' + Y(1) + '" class="goal"/>' +
        '<text x="' + (W - R) + '" y="' + (Y(1) - 4) + '" text-anchor="end" class="goal">1 s</text>';
      [0, 5000, 10000, 15000, 20000].forEach(function (r) {
        h += '<text x="' + X(r) + '" y="' + (H - 8) + '" text-anchor="middle">' + (r ? r / 1000 + "k" : "0") + "</text>";
      });
      h += '<text x="' + L0 + '" y="' + (T + 2) + '" class="axis">gap to the optimum, s</text>';
      KINDS.forEach(function (k) {
        var pts = curves[k.id].map(function (p) { return X(p[0]).toFixed(1) + "," + Y(p[1]).toFixed(1); });
        if (pts.length) h += '<polyline points="' + pts.join(" ") + '" style="stroke:' + k.color + '"/>';
      });
      return h + "</svg>";
    }

    /* One row per situation on the first stint (still on the starting A, no stop yet), one cell per
       lap: the learner's call there. Thick borders mark where the coarse table's cells change. */
    function policyRows(label, pick, edgesFor, visitsFor) {
      var c = context(), h = '<div class="pw-prow"><div class="pw-plabel">' + label + "</div>";
      [0, 1].forEach(function (sc) {
        h += '<div class="pw-pcells" style="--laps:' + c.model.horizon + '">';
        var prevKey = null;
        for (var lap = 1; lap <= c.model.horizon; lap++) {
          var a = pick(lap, sc), cls = "pc " + (a === PW.PIT_B ? "b" : a === PW.PIT_A ? "a" : "s");
          var k = edgesFor ? edgesFor(lap, sc) : null;
          if (edgesFor && prevKey !== null && k !== prevKey) cls += " edge";
          if (visitsFor && !visitsFor(lap, sc)) cls += " unseen";
          prevKey = k;
          h += '<i class="' + cls + '" title="lap ' + lap + (sc ? ", safety car" : "") + ": " + PW.ACTION_NAMES[a] + '"></i>';
        }
        h += '<span class="pw-psc">' + (sc ? "safety car" : "green") + "</span></div>";
      });
      return h + "</div>";
    }

    function grids() {
      var c = context(), H = c.model.horizon;
      function legal(lap) { return c.model.legalActions(lap, A, DRY, false); }
      var h = '<div class="pw-kicker" style="margin:14px 0 6px">The call on each lap if you are still on your first set of ' +
        U.tyre(A) + "</div>";
      h += policyRows("oracle", function (lap, sc) { return c.sol.best({ lap: lap, compound: A, age: lap, sc: sc, usedBoth: false, weather: DRY }); });
      KINDS.forEach(function (k) {
        var l = learners[k.id];
        h += policyRows(k.name,
          function (lap, sc) { return l.act(l.key(lap, A, lap, sc, false), legal(lap), true); },
          k.id === "coarse" ? function (lap, sc) { return l.key(lap, A, lap, sc, false); } : null,
          function (lap, sc) { return l.visits[l.key(lap, A, lap, sc, false)] > 0; });
      });
      h += '<div class="lapstrip-legend"><span><i class="pc s"></i>stay out</span><span><i class="pc b"></i>box for B</span>' +
        '<span><i class="pc a"></i>box for A</span><span><i class="pc s unseen"></i>never visited</span>' +
        "<span>a thick line: the table's cell changes</span><span>laps 1 to " + H + "</span></div>";
      return h;
    }

    function draw() {
      var c = context(), best = U.load().pitwall.best.learner;
      var h = '<div class="pw-kicker"><b>Learner</b> · Phase 4 · seed ' + seed + " · dry race, safety car on · optimum " + fx(c.optimum) + " s</div>";
      h += '<div class="pw-result">';
      KINDS.forEach(function (k) {
        var l = learners[k.id], s = l.last;
        h += '<div><span><i class="pw-swatch" style="background:' + k.color + '"></i>' + k.name + " · " + k.sub + "</span><b>" +
          (s ? "+" + fx(s.gap) + " s" : "—") + "</b><small>" + comma(l.races) + " races · ε " + fx(l.epsilon) +
          (s ? " · expects " + fx(s.expected) : "") + "</small></div>";
      });
      h += "</div>" + chart();
      if (curves.fine.length) {
        h += U.table(tbl, "Gap to the optimum in seconds at each checkpoint (1 s is the goal)",
          ["Races trained"].concat(KINDS.map(function (k) { return k.name + " (" + k.sub + ")"; })),
          curves.fine.map(function (p, i) { return [comma(p[0])].concat(KINDS.map(function (k) { return "+" + fx(curves[k.id][i][1]); })); }));
      }
      h += '<div class="pw-actions">' +
        '<button class="pw-btn go" data-pw="more"' + (busy || learners.fine.races >= BUDGET ? " disabled" : "") + ">Train 1,000 more races</button>" +
        '<button class="pw-btn" data-pw="all"' + (busy || learners.fine.races >= BUDGET ? " disabled" : "") + ">Train to " + comma(BUDGET) + "</button>" +
        '<button class="pw-btn" data-pw="fresh"' + (busy ? " disabled" : "") + ">New learners</button></div>";
      h += '<p class="pw-msg" aria-live="polite">' + (busy ? "Training: race " + comma(learners.fine.races) + " of " + comma(target) + "…" : msg) + "</p>";
      h += grids();
      if (tune) {
        h += '<details class="pw-details"><summary>Settings (both learners; changing one starts them again)</summary><div class="pw-kicker" style="margin-top:8px">' +
          '<label>Learning rate α <select data-pw="alpha">' + [0.05, 0.1, 0.2].map(function (v) {
            return "<option" + (v === alpha ? " selected" : "") + ">" + v + "</option>";
          }).join("") + "</select></label>" +
          '<label>Exploration ε falls from 1 to 0.05 over <select data-pw="decay">' + [2000, 6000, 15000].map(function (v) {
            return '<option value="' + v + '"' + (v === decayRaces ? " selected" : "") + ">" + comma(v) + " races</option>";
          }).join("") + "</select></label></div></details>";
      }
      h += '<p class="pw-msg">' + (best ? "Best learner so far: <b>+" + fx(best.gap) + " s</b> from the optimum (" + best.bins + " bins, " +
        comma(best.races) + " races, seed " + best.seed + ")." : "No learner trained yet.") +
        " A learner within 1 s of the optimum scores 5 championship points.</p>";
      node.innerHTML = h;
      U.keepTable(node, tbl);

      function on(sel, ev, fn) { var e = node.querySelector('[data-pw="' + sel + '"]'); if (e) e.addEventListener(ev, fn); }
      on("more", "click", function () { trainTo(learners.fine.races + 1000); });
      on("all", "click", function () { trainTo(BUDGET); });
      on("fresh", "click", function () { seed = 2 + Math.floor(Math.random() * 9998); reset(); draw(); });
      on("alpha", "change", function (e) { alpha = parseFloat(e.target.value); reset(); draw(); });
      on("decay", "change", function (e) { decayRaces = parseInt(e.target.value, 10); reset(); draw(); });
    }

    reset();
    var start = parseInt(node.getAttribute("data-start") || "0", 10);
    if (start > 0) trainTo(start, true);
    draw();
  }

  PW.mountLearner = mountLearner;
})(this);
