/* Pit Wall, Replay mode (Phase 5): the capstone's DQN, recorded in replay_policy.js, races the
   oracle on the same dice twice: once with exploration off and once as the plan evaluates it,
   with ε still on. Needs engine.js, oracle.js, replay_policy.js, replay.js and ui.js. ui.js mounts
   it for <div data-widget="pitwall" data-mode="replay">.

   Options (data attributes on the node)
     data-seed   the first race's seed (default 7)
     data-eps    the evaluation ε to start with (default 0.05); 0 is exploration off
     data-blind  "1" shows only what the evaluation reports: the oracle and the DQN as evaluated,
                 with no ε picker and no ε-off strip (the case brief, before the case is solved)
   Personal best: pitwall.best.replay = { gap, eps, races, at }, the exact expected gap to the
   optimum at the ε you evaluated with ("Evaluate 1,000 races"). Points count a gap of 1 s or less. */
(function (root) {
  "use strict";
  var PW = root.PitWall;
  if (!PW || !PW.replay || !PW.oracle) return;
  var R = PW.replay, A = PW.A, DRY = PW.DRY, NAMES = PW.ACTION_NAMES, BATCH = 1000;
  var EPS = [0, 0.01, 0.05, 0.1, 0.2];
  var ctx = null;

  function context() {
    if (!ctx) {
      var m = new PW.RaceModel(), sol = PW.oracle.solve(m);
      ctx = { model: m, sol: sol, policy: sol.asPolicy(),
        optimum: sol.value({ lap: 1, compound: A, age: 1, sc: 0, usedBoth: false, weather: DRY }), exact: {} };
    }
    return ctx;
  }
  function exact(eps) {
    var c = context();
    if (c.exact[eps] === undefined) c.exact[eps] = R.expectedTime(c.model, eps);
    return c.exact[eps];
  }
  function exploreRng(seed) { return PW.rngFrom((seed * 2654435761) >>> 0 ^ 0x5bd1e995); }
  function comma(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ","); }

  function mountReplay(node) {
    var U = PW.ui, fx = U.fx;
    var seed = parseInt(node.getAttribute("data-seed") || "7", 10);
    var eps = parseFloat(node.getAttribute("data-eps") || "0.05");
    var blind = node.getAttribute("data-blind") === "1";
    var batch = null, msg = "";
    node.classList.add("pw-panel", "pitwall", "pw-replay");

    /* The strip, with the random calls ringed and the unplanned stops in red. Each cell's title
       gives the network's three numbers there, as seconds to the flag. */
    function strip(log, label, withQ) {
      var H = context().model.horizon;
      var h = '<div class="pw-kicker" style="margin:10px 0 0"><b>' + label + "</b></div>" +
        '<div class="lapstrip" style="--laps:' + H + '" role="img" aria-label="' + label + '">';
      for (var i = 0; i < H; i++) {
        var e = log[i], after = e.action === PW.PIT_A ? A : e.action === PW.PIT_B ? PW.B : e.state.compound;
        var cls = "lc " + (after === PW.B ? "b" : "a") + (e.state.sc ? " sc" : "") + (e.action !== PW.STAY_OUT ? " pit" : "");
        // blind: mark only the unplanned stops, and never say why they happened
        if (e.random && (!blind || e.pointless)) cls += e.pointless ? " rnd pointless" : " rnd";
        var t = "lap " + (i + 1) + ": " + NAMES[e.action] + ", " + fx(e.time) + " s";
        if (e.random && blind) { if (e.action !== e.greedy) t += " (the network's own pick here: " + NAMES[e.greedy] + ")"; }
        else if (e.random) t += e.action === e.greedy ? " (a random call that matched the greedy one)" : " (random; greedy: " + NAMES[e.greedy] + ")";
        if (withQ) {
          var qv = R.q(e.state);
          t += ". The network expects to the flag: " + qv.map(function (v, a) { return v === null ? null : ["stay out", "box for A", "box for B"][a] + " " + fx(v); })
            .filter(Boolean).join(", ");
        }
        h += '<div class="' + cls + '" title="' + t + '"></div>';
      }
      return h + "</div>";
    }

    function oneRace(s, e) {
      var c = context(), dice = PW.drawDice(c.model, s);
      return { oracle: PW.simulate(c.model, c.policy, dice, DRY), off: R.race(c.model, dice, 0, null),
        on: R.race(c.model, dice, e, exploreRng(s)) };
    }

    function evaluate() {
      var c = context(), sum = { off: 0, on: 0, oracle: 0 }, on = { randoms: 0, changed: 0, pointless: 0, hit: 0 };
      for (var s = 1; s <= BATCH; s++) {
        var r = oneRace(10000 + s, eps);
        sum.off += r.off.time; sum.on += r.on.time; sum.oracle += r.oracle.time;
        on.randoms += r.on.randoms; on.changed += r.on.changed; on.pointless += r.on.pointless;
        if (r.on.pointless) on.hit++;
      }
      batch = { eps: eps, off: sum.off / BATCH, on: sum.on / BATCH, oracle: sum.oracle / BATCH, stats: on };
      var gap = exact(eps) - c.optimum, prev = U.load().pitwall.best.replay;
      if (!prev || gap < prev.gap - 1e-9) {
        U.save(function (st) { st.pitwall.best.replay = { gap: gap, eps: eps, races: R.meta.races, at: Date.now() }; });
      }
      if (root.F1NAV) root.F1NAV.refresh();
    }

    function batchTable() {
      if (!batch) return "";
      var c = context(), st = batch.stats;
      function row(name, mean, ex, extra) {
        return "<tr><td>" + name + "</td><td>" + fx(mean) + "</td><td>" + fx(ex) + '</td><td class="' + (ex - c.optimum > 1 ? "t-yellow" : "t-green") +
          '">+' + fx(ex - c.optimum) + "</td><td>" + extra + "</td></tr>";
      }
      return '<table class="pw-trace"><thead><tr><th>' + comma(BATCH) + " races, same dice</th><th>mean</th><th>exact expected</th><th>gap</th><th>per race</th></tr></thead><tbody>" +
        row("oracle", batch.oracle, c.optimum, "the best average there is") +
        (blind || !batch.eps ? "" : row("DQN, ε off", batch.off, exact(0), "no random calls")) +
        row(blind ? "the champion, as evaluated" : "DQN, ε " + batch.eps, batch.on, exact(batch.eps),
          batch.eps ? (blind ? "" : fx(st.randoms / BATCH) + " random calls, " + fx(st.changed / BATCH) + " changed the call, ") + fx(st.pointless / BATCH) +
          " unplanned stops; " + Math.round(100 * st.hit / BATCH) + "% of races had one" : "no random calls") +
        "</tbody></table>";
    }

    function draw() {
      var c = context(), r = oneRace(seed, eps), best = U.load().pitwall.best.replay;
      var gOff = exact(0) - c.optimum, gOn = exact(eps) - c.optimum, ex = R.stats(c.model, eps);
      var h = '<div class="pw-kicker"><b>Replay</b> · Phase 5 · ' + (blind ? "the champion's evaluation" : "the capstone DQN, trained " + comma(R.meta.races) +
        " races (seed " + R.meta.seed + ")") + " · dry race, safety car on · race " + seed + "</div>";
      if (blind) {
        h += '<div class="pw-result">' +
          "<div><span>evaluation report</span><b class=\"t-yellow\">+" + fx(gOn) + " s</b><small>expected gap to the optimum</small></div>" +
          "<div><span>unplanned pit stops</span><b>" + fx(ex.pointless) + "</b><small>a race, on average</small></div>" +
          "<div><span>races with at least one</span><b>" + Math.round(100 * ex.anyPointless) + "%</b><small>exact, from the model</small></div></div>";
        h += strip(r.oracle.log, "oracle · " + fx(r.oracle.time) + " s", false) +
          strip(r.on.log, "the champion, as evaluated · " + fx(r.on.time) + " s", true);
        h += U.LEGEND.replace("</div>", '<span><i class="rnd-key bad"></i>an unplanned stop</span></div>');
      } else {
        h += '<div class="pw-result">' +
          "<div><span>DQN · ε off</span><b>+" + fx(gOff) + " s</b><small>expected gap to the optimum</small></div>" +
          "<div><span>DQN · ε " + eps + " at evaluation</span><b>+" + fx(gOn) + " s</b><small>" + fx(ex.randoms) + " random calls, " + fx(ex.pointless) + " unplanned stops a race</small></div>" +
          "<div><span>cost of evaluating with ε on</span><b class=\"" + (gOn - gOff > 0.005 ? "t-yellow" : "t-green") + "\">+" + fx(gOn - gOff) + " s</b><small>the same network, the same races</small></div></div>";
        h += strip(r.oracle.log, "oracle · " + fx(r.oracle.time) + " s", false) +
          strip(r.off.log, "DQN, ε off · " + fx(r.off.time) + " s", true);
        if (eps) h += strip(r.on.log, "DQN, ε " + eps + " · " + fx(r.on.time) + " s" + (r.on.randoms ? " · " + r.on.randoms + " random call" + (r.on.randoms > 1 ? "s" : "") : " · no random calls this race"), true);
        h += U.LEGEND.replace("</div>", '<span><i class="rnd-key"></i>random call</span><span><i class="rnd-key bad"></i>unplanned stop</span></div>');
      }
      h += '<div class="pw-actions">' +
        '<button class="pw-btn go" data-pw="next">Next race</button>' +
        '<button class="pw-btn" data-pw="eval">Evaluate ' + comma(BATCH) + " races</button>" +
        (blind ? "" : '<label class="pw-kicker">ε at evaluation <select data-pw="eps">' + EPS.map(function (v) {
          return '<option value="' + v + '"' + (v === eps ? " selected" : "") + ">" + (v ? v : "0 (off)") + "</option>";
        }).join("") + "</select></label>") + "</div>";
      h += '<p class="pw-msg" aria-live="polite">' + (msg || "Hover a lap to see what the network expects from each call there, in seconds to the flag.") + "</p>";
      h += batchTable();
      h += '<p class="pw-msg">' + (best ? "Best evaluation so far: <b>+" + fx(best.gap) + " s</b> from the optimum (ε " + best.eps + ")." : "No evaluation run yet.") +
        " An evaluation within 1 s of the optimum scores 5 championship points.</p>";
      node.innerHTML = h;

      function on(sel, ev, fn) { var e = node.querySelector('[data-pw="' + sel + '"]'); if (e) e.addEventListener(ev, fn); }
      on("next", "click", function () { seed += 1; msg = ""; draw(); });
      on("eval", "click", function () {
        evaluate();
        msg = "Means over " + comma(BATCH) + " races carry sampling noise; the exact column has none." + (blind ? "" : " Every row saw the same safety cars.");
        draw();
      });
      on("eps", "change", function (e) { eps = parseFloat(e.target.value); batch = null; msg = ""; draw(); });
    }

    draw();
  }

  PW.mountReplay = mountReplay;
})(this);
