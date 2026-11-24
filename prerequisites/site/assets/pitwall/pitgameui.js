/* Pit Wall, Duel mode (Phase 8): the pit-timing duel. You are the follower, 0.5 s behind an equal
   car; each car stops once, onto B, on a lap from 2 to 18. Pick your lap; the leader picks its own
   by one of three rules from the labs; one race is run on one of the labs' 20 seeds of pass dice.
   Needs engine.js, duel.js, pitgame_data.js, pitgame.js and ui.js. ui.js mounts it for
   <div data-widget="pitwall" data-mode="duel">.

   Options (data attributes on the node)
     data-leader    "eq" (fictitious play's equilibrium mix, default), "latest" (a best reply to
                    your previous stop: latest-only self-play) or "pool" (the plan's pool rule,
                    after 1,000 rounds of self-play)
     data-blocking  "0" or "1" (default "1")
     data-show      "1" shows each lap's expected payoff against the leader on the buttons
     data-seed      the first draw's seed (default 8)
   Personal best: pitwall.best.duel = { gap, leader, mean, best, at }, blocking on only, after 10
   rounds against one leader: gap = (the best mean payoff any follower can hold against that leader
   - your mean expected payoff over your last 10 rounds) / 0.05, in seconds of margin (the payoff
   pays 0.05 per second). Points count a gap of 1 s or less. */
(function (root) {
  "use strict";
  var PW = root.PitWall;
  if (!PW || !PW.pitgame || !PW.ui) return;
  var G = PW.pitgame, DATA = G.DATA, LAPS = G.LAPS, N = LAPS.length, SESSION = 10;
  var LEADERS = { eq: "the equilibrium mix (fictitious play)", latest: "latest-only: a best reply to your last stop", pool: "the plan's pool, after 1,000 rounds" };

  /* The best long-run mean a follower can get against latest-only: the max-mean cycle of
     "my next lap, against the leader's reply to my last one" (Karp's algorithm). */
  function bestAgainstLatest(M) {
    function reply(i) { return G.argmin(M[i]); }
    var F = [new Array(N).fill(0)], k, u, v, best = -Infinity;
    for (k = 1; k <= N; k++) {
      F.push(new Array(N).fill(-Infinity));
      for (v = 0; v < N; v++) for (u = 0; u < N; u++) F[k][v] = Math.max(F[k][v], F[k - 1][u] + M[v][reply(u)]);
    }
    for (v = 0; v < N; v++) {
      var m = Infinity;
      for (k = 0; k < N; k++) m = Math.min(m, (F[N][v] - F[k][v]) / (N - k));
      best = Math.max(best, m);
    }
    return best;
  }
  var bestCache = {};
  function bestFor(leader, blocking) {
    var key = leader + (blocking ? "1" : "0");
    if (bestCache[key] === undefined) {
      var sol = blocking ? DATA.on : DATA.off, M = sol.U;
      bestCache[key] = leader === "latest" ? bestAgainstLatest(M) : Math.max.apply(null, G.rowValues(M, leader === "pool" ? sol.pool.l : sol.eq.l));
    }
    return bestCache[key];
  }

  function mountDuel(node) {
    var U = PW.ui, fx = U.fx, signed = U.signed;
    var leader = node.getAttribute("data-leader") || "eq";
    var blocking = node.getAttribute("data-blocking") !== "0";
    var show = node.getAttribute("data-show") === "1";
    var r = PW.rngFrom(parseInt(node.getAttribute("data-seed") || "8", 10));
    var rounds = [], prev = null, last = null, tbl = { open: false };
    node.classList.add("pw-panel", "pitwall", "pw-duel");

    function sol() { return blocking ? DATA.on : DATA.off; }
    function leaderMix() {
      if (leader === "latest") return G.pure(prev === null ? LAPS.indexOf(8) : G.argmin(sol().U[prev]));
      return leader === "pool" ? sol().pool.l : sol().eq.l;
    }
    function draw1(mix) { var u = r(), c = 0; for (var j = 0; j < N; j++) { c += mix[j]; if (u < c) return j; } return N - 1; }

    function play(i) {
      var mix = leaderMix(), j = draw1(mix), s = Math.floor(r() * DATA.dice.length);
      var race = G.race(LAPS[i], LAPS[j], s, blocking), pay = G.payoffOf(race);
      var expected = G.rowValues(sol().U, mix)[i];
      last = { i: i, j: j, seed: s, race: race, pay: pay, expected: expected, cell: sol().U[i][j] };
      rounds.push(last);
      prev = i;
      record();
      draw();
    }

    function mean(xs) { return xs.reduce(function (a, b) { return a + b; }, 0) / xs.length; }
    function sessionGap() {
      if (rounds.length < SESSION) return null;
      var m = mean(rounds.slice(-SESSION).map(function (x) { return x.expected; }));
      return { mean: m, best: bestFor(leader, blocking), gap: (bestFor(leader, blocking) - m) / G.CONST.MARGIN_WEIGHT };
    }
    function record() {
      var g = sessionGap();
      if (!g || !blocking) return;
      var prevBest = U.load().pitwall.best.duel;
      if (!prevBest || g.gap < prevBest.gap - 1e-9) {
        U.save(function (st) { st.pitwall.best.duel = { gap: g.gap, leader: leader, mean: g.mean, best: g.best, at: Date.now() }; });
        if (root.F1NAV) root.F1NAV.refresh();
      }
    }

    function strips() {
      if (!last) return "";
      var log = last.race.log, H = log.length;
      return U.strip(log, H, 0, "you · stop on lap " + LAPS[last.i] + " · " + fx(last.race.total) + " s") +
        U.strip(log.map(function (e) { return { state: e.rival, action: e.rivalAction, time: e.rivalTime }; }), H, 0, "leader · stop on lap " + LAPS[last.j] + " · " + fx(last.race.rival) + " s") + U.LEGEND;
    }

    function deltas() {
      if (rounds.length < 2) return "";
      var c = {}, lo = 0, hi = 0;
      rounds.forEach(function (x) { var d = LAPS[x.i] - LAPS[x.j]; c[d] = (c[d] || 0) + 1; lo = Math.min(lo, d); hi = Math.max(hi, d); });
      var max = Math.max.apply(null, Object.keys(c).map(function (k) { return c[k]; })), h = "";
      for (var d = lo; d <= hi; d++) {
        h += '<div class="pw-dcol"><i style="height:' + Math.round(46 * (c[d] || 0) / max) + 'px"' + (d === 0 ? ' class="zero"' : "") + "></i><span>" + (d > 0 ? "+" : "") + d + "</span></div>";
      }
      return '<div class="pw-kicker" style="margin:10px 0 0"><b>Your stop minus the leader\'s, ' + rounds.length + " rounds</b><span>negative: you stopped first</span></div>" +
        '<div class="pw-deltas" role="img" aria-label="pit-delta histogram">' + h + "</div>" +
        U.table(tbl, "Rounds by your stop lap minus the leader's (negative: you stopped first)", ["Your stop minus the leader's", "Rounds"],
          Object.keys(c).map(Number).sort(function (a, b) { return a - b; }).map(function (d) { return [(d > 0 ? "+" : "") + d, c[d]]; }));
    }

    function draw() {
      var s = sol(), values = G.rowValues(s.U, leaderMix()), best = bestFor(leader, blocking), g = sessionGap(), h = "";
      h += '<div class="pw-head"><div class="pw-kicker"><b>Duel</b><span>Phase 8</span><span>pit-timing duel · you follow 0.5 s behind an equal car · one stop onto B, lap 2 to 18</span></div>' +
        '<div class="pw-kicker"><label>Leader <select data-pw="leader">' + Object.keys(LEADERS).map(function (k) {
          return '<option value="' + k + '"' + (k === leader ? " selected" : "") + ">" + LEADERS[k] + "</option>";
        }).join("") + '</select></label><label class="pw-toggle"><input type="checkbox" data-pw="blocking"' + (blocking ? " checked" : "") + "> blocking</label>" +
        '<label class="pw-toggle"><input type="checkbox" data-pw="show"' + (show ? " checked" : "") + "> show what each lap is worth</label></div></div>";
      h += '<p class="pw-msg">' + (leader === "latest" ? "This leader stops on its best reply to <b>your previous stop</b>" + (prev === null ? " (lap 8 before you have stopped)" : ": lap " + LAPS[G.argmin(s.U[prev])] + " next") + "." :
        "This leader draws its stop from " + (leader === "pool" ? "the mixture the plan's pool rule left after 1,000 rounds of self-play" : "fictitious play's mixture after 10,000 rounds") + ": " +
        leaderMix().map(function (p, j) { return p > 0.005 ? "lap " + LAPS[j] + " " + Math.round(100 * p) + "%" : ""; }).filter(Boolean).join(", ") + ".") +
        " Payoff: +1 for finishing ahead, −1 if not, plus 0.05 a second of margin.</p>";
      h += '<div class="pw-laps">' + LAPS.map(function (l, i) {
        var top = Math.abs(values[i] - Math.max.apply(null, values)) < 1e-9;
        return '<button type="button" class="pw-call pw-lap' + (show && top ? " top" : "") + '" data-pw-lap="' + i + '">lap ' + l + (show ? '<span class="q">' + signed(values[i], 2) + "</span>" : "") + "</button>";
      }).join("") + "</div>";
      if (last) {
        h += '<p class="pw-msg" aria-live="polite">You stopped on lap <b>' + LAPS[last.i] + "</b>, the leader on lap <b>" + LAPS[last.j] + "</b>. On race #" + last.seed + " you finished <b>" +
          (last.race.finishedAhead ? "P1" : "P2") + "</b>, " + fx(Math.abs(last.race.rival - last.race.total)) + " s " + (last.race.finishedAhead ? "ahead" : "behind") + ": payoff " + signed(last.pay) +
          ". That pairing pays " + signed(last.cell) + " averaged over all 20 seeds, and lap " + LAPS[last.i] + " was worth " + signed(last.expected) + " against this leader.</p>";
      } else {
        h += '<p class="pw-msg" aria-live="polite">Pick a lap.</p>';
      }
      h += '<div class="pw-result"><div><span>rounds</span><b>' + rounds.length + "</b><small>" + rounds.filter(function (x) { return x.race.finishedAhead; }).length + " finished ahead</small></div>" +
        "<div><span>your mean, last " + SESSION + "</span><b>" + (rounds.length ? signed(mean(rounds.slice(-SESSION).map(function (x) { return x.expected; }))) : "—") + "</b><small>expected payoff of your picks</small></div>" +
        '<div><span>best any follower can hold</span><b class="t-purple">' + signed(best) + "</b><small>" + (g ? "you " + (g.gap <= 1 ? '<b class="t-green">' : "") + fx(Math.max(0, g.gap), 1) + " s</b> from it" : "against this leader") + "</small></div></div>";
      h += strips() + deltas();
      if (rounds.length) {
        h += '<details class="pw-details"><summary>Every round</summary><table class="pw-trace"><thead><tr><th>round</th><th>you</th><th>leader</th><th>race</th><th>finish</th><th>payoff</th><th>worth</th></tr></thead><tbody>' +
          rounds.map(function (x, k) {
            return "<tr><td>" + (k + 1) + "</td><td>" + LAPS[x.i] + "</td><td>" + LAPS[x.j] + "</td><td>#" + x.seed + "</td><td>" + (x.race.finishedAhead ? "P1" : "P2") + "</td><td>" + signed(x.pay) + "</td><td>" + signed(x.expected) + "</td></tr>";
          }).reverse().join("") + "</tbody></table></details>";
      }
      var pb = U.load().pitwall.best.duel;
      h += '<div class="pw-actions"><button type="button" class="pw-btn" data-pw="reset">New session</button></div>';
      h += '<p class="pw-msg">' + (pb ? "Best session: <b>" + fx(Math.max(0, pb.gap), 1) + " s</b> from the best against " + LEADERS[pb.leader] + "." : "No session of " + SESSION + " rounds with blocking on yet.") +
        " Ten rounds with blocking on, within 1 s of the best any follower can hold against that leader (0.05 of payoff), score 5 championship points.</p>";
      node.innerHTML = h;
      U.keepTable(node, tbl);

      Array.prototype.forEach.call(node.querySelectorAll("[data-pw-lap]"), function (b) {
        b.addEventListener("click", function () { play(parseInt(b.getAttribute("data-pw-lap"), 10)); });
      });
      function on(sel, ev, fn) { var e = node.querySelector('[data-pw="' + sel + '"]'); if (e) e.addEventListener(ev, fn); }
      function reset() { rounds = []; prev = null; last = null; draw(); }
      on("leader", "change", function (e) { leader = e.target.value; reset(); });
      on("blocking", "change", function (e) { blocking = e.target.checked; reset(); });
      on("show", "change", function (e) { show = e.target.checked; draw(); });
      on("reset", "click", reset);
    }

    draw();
  }

  PW.mountDuel = mountDuel;
  PW.duelGame = { bestFor: bestFor };
})(this);
