/* Pit Wall, Training room (Phase 9): learning runs recorded by labs/tools/pitwall_training_export.py,
   replayed. Nothing trains in the browser: every curve is a run the labs made, scored exactly at a
   checkpoint every 100 races. Needs engine.js, training_data.js and ui.js; ui.js mounts it for
   <div data-widget="pitwall" data-mode="training">.

   Options (data attributes on the node)
     data-learner   the learner selected first: reinforce, ac, ppo4, noclip4, ppo10, noclip10, sb3 (default sb3)
     data-reward    centred, raw, or vecnorm (MaskablePPO only: the raw reward through SB3's
                    VecNormalize, rewards only) (default raw)
     data-seed      0, 1 or 2 (default 0)
     data-fixed     "1" hides the reward switch (the case brief shows only the plan's raw reward)
     data-show      runs drawn on mount, as "learner|reward|seed" separated by commas
   With prefers-reduced-motion set, a run is drawn whole instead of checkpoint by checkpoint.
   Personal best: pitwall.best.training = { gap, learner, reward, seed, at }, the final exact gap of
   a run you trained here. Points count a gap of 1 s or less. */
(function (root) {
  "use strict";
  var PW = root.PitWall;
  if (!PW || !PW.trainingData || !PW.ui) return;
  var D = PW.trainingData, U = PW.ui, fx = U.fx;
  var NAMES = {
    reinforce: "REINFORCE", ac: "actor-critic", ppo4: "mini PPO, 4 epochs", noclip4: "mini PPO, 4 epochs, no clip",
    ppo10: "mini PPO, 10 epochs", noclip10: "mini PPO, 10 epochs, no clip", sb3: "MaskablePPO (the library)"
  };
  var ABOUT = {
    reinforce: "Page 01: after each race, every lap's logits move by α · G<sub>t</sub> · ∇log π. A table policy, no critic.",
    ac: "Page 02: the same push, with G<sub>t</sub> − V(s) and a table critic that moves 10% of the way to each return.",
    ppo4: "Pages 03–04: GAE advantages with the table critic, batches of 10 races, advantages standardised per batch, 4 clipped passes over each batch.",
    noclip4: "The mini PPO with the clip removed, 4 passes per batch.",
    ppo10: "The mini PPO with 10 passes per batch, the plan's n_epochs.",
    noclip10: "10 passes per batch and no clip.",
    sb3: "sb3-contrib's MaskablePPO, the class the plan uses: a 32 × 32 network for the policy and one for the critic, trained by Adam, with the capstone report's settings (n_steps 400, batch 100, 10 epochs, γ = 1, ent_coef 0.01)."
  };
  var REWARDS = [["raw", "raw: −lap time"], ["centred", "centred: −(lap time − 10)"], ["vecnorm", "raw, through VecNormalize"]];
  var COLOURS = ["var(--accent)", "var(--t-purple)", "var(--t-green)", "var(--t-yellow)", "var(--tyre-b)", "var(--tyre-a)"];
  var MAXRUNS = 6, N = D.races / D.every;
  var MODEL = new PW.RaceModel({ scHazard: 0.0 }), DICE = new Array(2 * MODEL.horizon).fill(0.5);
  var UNTRAINED = 38.48;

  function key(l, r, s) { return l + "|" + r + "|" + s; }
  function label(k) { var p = k.split("|"); return NAMES[p[0]] + " · " + (p[1] === "vecnorm" ? "raw + VecNormalize" : p[1]) + " · seed " + p[2]; }
  function planRun(p) { return PW.simulate(MODEL, function (lap) { return +p[lap - 1]; }, DICE); }

  function mountTraining(node) {
    var learner = node.getAttribute("data-learner") || "sb3", reward = node.getAttribute("data-reward") || "raw";
    var seed = parseInt(node.getAttribute("data-seed") || "0", 10), fixed = node.getAttribute("data-fixed") === "1";
    var shown = [], cur = null, at = N, timer = null, msg = "", tbl = { open: false };
    (node.getAttribute("data-show") || "").split(",").forEach(function (k) {
      k = k.trim();
      if (k && D.runs[k]) shown.push({ key: k, upto: N });
    });
    if (shown.length) { cur = shown[shown.length - 1].key; }

    function colour(i) { return COLOURS[i % COLOURS.length]; }

    function chart() {
      var W = 600, Ht = 210, padL = 34, padB = 22, top = 8, ymax = 50;
      function x(i) { return padL + (W - padL - 10) * i / N; }
      function y(g) { return top + (Ht - top - padB) * (1 - Math.min(ymax, Math.max(0, g)) / ymax); }
      var h = '<svg class="pw-chart pw-train-chart" viewBox="0 0 ' + W + " " + Ht + '" role="img" aria-label="exact gap to the optimum after every 100 races">';
      [0, 10, 20, 30, 40, 50].forEach(function (g) {
        h += '<line class="grid" x1="' + padL + '" x2="' + (W - 10) + '" y1="' + y(g) + '" y2="' + y(g) + '"></line><text x="2" y="' + (y(g) + 4) + '">' + g + "</text>";
      });
      [0, 5, 10, 15, 20].forEach(function (i) {
        h += '<text text-anchor="' + (i === 0 ? "start" : i === N ? "end" : "middle") + '" x="' + x(i) + '" y="' + (Ht - 5) + '">' + (i * D.every).toLocaleString("en-GB") + "</text>";
      });
      h += '<line class="goal" x1="' + padL + '" x2="' + (W - 10) + '" y1="' + y(1) + '" y2="' + y(1) + '"></line>' +
        '<text class="goal" x="' + (W - 120) + '" y="' + (y(1) - 5) + '">within 1 s</text>' +
        '<line class="grid untrained" x1="' + padL + '" x2="' + (W - 10) + '" y1="' + y(UNTRAINED) + '" y2="' + y(UNTRAINED) + '"></line>' +
        '<text x="' + (padL + 4) + '" y="' + (y(UNTRAINED) - 5) + '">38.48: never chooses to stop</text>';
      shown.forEach(function (s, i) {
        var g = D.runs[s.key].gap.slice(0, s.upto + 1);
        h += '<polyline points="' + g.map(function (v, j) { return x(j) + "," + y(v); }).join(" ") + '" style="stroke:' + colour(i) + '"' +
          (s.key === cur ? "" : ' class="faint"') + "></polyline>";
      });
      if (cur) {
        var r = D.runs[cur], j = Math.min(at, upto(cur));
        h += '<circle cx="' + x(j) + '" cy="' + y(r.gap[j]) + '" r="4" style="fill:' + colour(indexOf(cur)) + '"></circle>';
      }
      return h + '<text text-anchor="end" x="' + (W - 10) + '" y="' + (top + 12) + '">gap to the optimum (s), by races trained</text></svg>';
    }
    function indexOf(k) { for (var i = 0; i < shown.length; i++) if (shown[i].key === k) return i; return -1; }
    function upto(k) { var i = indexOf(k); return i < 0 ? N : shown[i].upto; }

    function legend() {
      if (!shown.length) return "";
      return '<div class="pw-train-legend">' + shown.map(function (s, i) {
        var r = D.runs[s.key], done = s.upto === N;
        return '<button type="button" class="pw-chip' + (s.key === cur ? " on" : "") + '" data-pw-run="' + s.key + '"><i style="background:' + colour(i) + '"></i>' + label(s.key) +
          " <b>" + (done ? fx(r.gap[N]) + " s" : "…") + "</b></button>";
      }).join("") + "</div>";
    }

    function chartTable() {
      if (!shown.length) return "";
      var rows = [];
      for (var j = 0; j <= N; j++) {
        rows.push([(j * D.every).toLocaleString("en-GB")].concat(shown.map(function (s) {
          return j <= s.upto ? "+" + fx(D.runs[s.key].gap[j]) : "";
        })));
      }
      return U.table(tbl, "Gap to the optimum in seconds after each 100 races (within 1 s is the goal; 38.48 never stops)",
        ["Races trained"].concat(shown.map(function (s) { return label(s.key); })), rows);
    }

    function detail() {
      if (!cur) return '<p class="pw-msg">Pick a learner and a reward, then press <b>Train</b>. Each run is one the labs recorded; you watch it happen.</p>';
      var p = cur.split("|"), r = D.runs[cur], j = Math.min(at, upto(cur)), run = planRun(r.plan[j]);
      var ret = -(run.time - D.offsets[p[1]] * MODEL.horizon), v = r.v[j];
      var stops = run.log.filter(function (e) { return e.action !== PW.STAY_OUT; }).map(function (e) { return "lap " + e.state.lap + " onto " + PW.COMPOUND_NAMES[e.action === PW.PIT_B ? PW.B : PW.A]; });
      var h = '<div class="pw-kicker" style="margin-top:8px"><label>After <input type="range" min="0" max="' + upto(cur) + '" value="' + j + '" data-pw="at"> <b>' +
        (j * D.every).toLocaleString("en-GB") + " races</b></label><span>" + label(cur) + "</span></div>";
      h += '<div class="pw-result">' +
        "<div><span>gap to the optimum</span><b class=\"" + (r.gap[j] <= 1 ? "t-green" : "t-yellow") + "\">+" + fx(r.gap[j]) + " s</b><small>its greedy plan, scored exactly</small></div>" +
        "<div><span>how random its calls still are</span><b>" + fx(r.ent[j]) + "</b><small>mean entropy along the plan, nats</small></div>" +
        "<div><span>the critic's value of lap 1</span><b class=\"t-purple\">" + (v === null ? "none" : fx(v, 1)) + "</b><small>" +
        (v === null ? "REINFORCE has no critic" : p[1] === "vecnorm" ? "in VecNormalize's scaled units (rewards ÷ about 61)" : "what its plan returns: " + fx(ret, 1)) + "</small></div></div>";
      h += U.strip(run.log, MODEL.horizon, 0, "its plan · " + (stops.length ? stops.join(", ") : "no stop") + " · " + fx(run.time) + " s") + U.LEGEND;
      return h;
    }

    function draw() {
      var best = U.load().pitwall.best.training;
      var h = '<div class="pw-head"><div class="pw-kicker"><b>Training room</b><span>Phase 9</span><span>recorded runs, replayed: nothing trains in your browser</span>' +
        "<span>quiet toy race · optimum " + fx(D.optimum) + " s</span></div>";
      h += '<div class="pw-kicker"><label>Learner <select data-pw="learner">' + Object.keys(NAMES).map(function (k) {
        return '<option value="' + k + '"' + (k === learner ? " selected" : "") + ">" + NAMES[k] + "</option>";
      }).join("") + "</select></label>" +
        (fixed ? "<label>Reward <b>raw: −lap time</b></label>" : '<label>Reward <select data-pw="reward">' + REWARDS.filter(function (r) { return r[0] !== "vecnorm" || learner === "sb3"; }).map(function (r) {
          return '<option value="' + r[0] + '"' + (reward === r[0] ? " selected" : "") + ">" + r[1] + "</option>";
        }).join("") + "</select></label>") +
        '<label>Seed <select data-pw="seed">' + [0, 1, 2].map(function (s) { return '<option value="' + s + '"' + (s === seed ? " selected" : "") + ">" + s + "</option>"; }).join("") +
        "</select></label></div></div>";
      h += '<p class="pw-msg">' + ABOUT[learner] + "</p>";
      h += '<div class="pw-actions"><button class="pw-btn go" type="button" data-pw="train"' + (timer ? " disabled" : "") + ">Train " + D.races.toLocaleString("en-GB") + " races</button>" +
        '<button class="pw-btn" type="button" data-pw="clear"' + (shown.length && !timer ? "" : " disabled") + ">Clear the chart</button></div>";
      h += chart() + legend() + chartTable() + detail();
      h += '<p class="pw-msg" aria-live="polite">' + msg + "</p>";
      h += '<p class="pw-msg">' + (best ? "Best run trained here: <b>+" + fx(best.gap) + " s</b> (" + NAMES[best.learner] + ", " + best.reward + " reward)." : "No run trained here yet.") +
        " A run that ends within 1 s of the optimum scores 5 championship points.</p>";
      node.innerHTML = h;
      U.keepTable(node, tbl);

      function on(sel, ev, fn) { var e = node.querySelector('[data-pw="' + sel + '"]'); if (e) e.addEventListener(ev, fn); }
      on("learner", "change", function (e) { learner = e.target.value; if (learner !== "sb3" && reward === "vecnorm") reward = "raw"; draw(); });
      on("reward", "change", function (e) { reward = e.target.value; draw(); });
      on("seed", "change", function (e) { seed = parseInt(e.target.value, 10); draw(); });
      on("clear", "click", function () { shown = []; cur = null; msg = ""; draw(); });
      on("at", "input", function (e) { at = parseInt(e.target.value, 10); draw(); var r = node.querySelector('[data-pw="at"]'); if (r) r.focus(); });
      on("train", "click", train);
      Array.prototype.forEach.call(node.querySelectorAll("[data-pw-run]"), function (b) {
        b.addEventListener("click", function () { cur = b.getAttribute("data-pw-run"); at = upto(cur); draw(); });
      });
    }

    function finish(k) {
      var p = k.split("|"), g = D.runs[k].gap[N], prev = U.load().pitwall.best.training;
      if (!prev || g < prev.gap - 1e-9) {
        U.save(function (st) { st.pitwall.best.training = { gap: g, learner: p[0], reward: p[1], seed: +p[2], at: Date.now() }; });
      }
      msg = label(k) + ": " + (g <= 1 ? "within a second of the optimum." : Math.abs(g - UNTRAINED) < 0.005 ? "it ends on the plan it started with." : "+" + fx(g) + " s from the optimum after " + D.races.toLocaleString("en-GB") + " races.");
      if (root.F1NAV) root.F1NAV.refresh();
    }

    function train() {
      var k = key(learner, reward, seed), i = indexOf(k);
      if (i >= 0) shown.splice(i, 1);
      if (shown.length >= MAXRUNS) shown.shift();
      var s = { key: k, upto: 0 };
      shown.push(s); cur = k; at = 0; msg = "";
      if (root.matchMedia && root.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        s.upto = N; at = N; finish(k); draw(); return;
      }
      timer = setInterval(function () {
        s.upto += 1; at = s.upto;
        if (s.upto >= N) { clearInterval(timer); timer = null; finish(k); }
        draw();
      }, 70);
      draw();
    }

    draw();
  }

  PW.mountTraining = mountTraining;
})(this);
