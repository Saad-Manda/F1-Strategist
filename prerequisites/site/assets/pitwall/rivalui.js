/* Pit Wall, Rival mode (Phase 6): race the toy race against a scripted rival, with blocking off
   (the plan's race as written: each car drives its own lap time) or on (the wake, being held up,
   passing). Needs engine.js, duel.js and ui.js. ui.js mounts it for
   <div data-widget="pitwall" data-mode="rival">.

   Options (data attributes on the node)
     data-seed      the race's dice (default 1); "New race" draws fresh ones
     data-blocking  "0" or "1" (default "1")
     data-rival     the lap the rival stops for B (default 9)
     data-fixed     "1" hides the blocking switch (the case brief shows the plan's race only)
   Personal best: pitwall.best.rival = { time, best, gap, seed, rivalLap, at }, recorded for
   races with blocking on only, where gap = your time - the best one- or two-stop plan on the
   same dice. Points count a gap of 1 s or less. */
(function (root) {
  "use strict";
  var PW = root.PitWall;
  if (!PW || !PW.duel || !PW.ui) return;
  var D = PW.duel, NAMES = PW.ACTION_NAMES, KEYS = ["s", "a", "b"], RIVAL_LAPS = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14];

  function mountRival(node) {
    var U = PW.ui, fx = U.fx, signed = U.signed;
    var seed = parseInt(node.getAttribute("data-seed") || "1", 10);
    var blocking = node.getAttribute("data-blocking") !== "0";
    var rivalLap = parseInt(node.getAttribute("data-rival") || "9", 10);
    var fixed = node.getAttribute("data-fixed") === "1";
    var duel, msg, result, boardOpen = false;
    node.classList.add("pw-panel", "pitwall", "pw-rival");
    node.setAttribute("tabindex", "-1");

    function opts(extra) {
      var o = { seed: seed, interaction: blocking, rivalLap: rivalLap };
      for (var k in extra) o[k] = extra[k];
      return o;
    }
    function start(fresh) {
      if (fresh) seed = 100 + Math.floor(Math.random() * 99900);
      duel = new D.Duel(opts());
      result = null;
      msg = "Lights out. You start on " + U.tyre(PW.A) + ", 0.3 s behind the rival and 0.3 s a lap faster. The rival stops for B on lap " +
        rivalLap + " and never changes its plan." + (blocking ? " Blocking is on: a car within 1 s of the one ahead is held up unless it passes." : " Blocking is off: each car drives its own lap time, as in the plan's race.");
      draw();
    }

    function describe(e) {
      var t = "Lap " + e.lap + ": <b>" + NAMES[e.action] + "</b>, " + fx(e.time) + " s.";
      if (e.rivalAction !== PW.STAY_OUT) t += " The rival boxes for " + PW.COMPOUND_NAMES[e.rivalAction === PW.PIT_A ? PW.A : PW.B] + ".";
      if (e.passed) t += e.passer === "agent" ? " <b>You pass the rival</b> (a " + Math.round(100 * e.chance) + "% chance this lap)." : " <b>The rival passes you.</b>";
      else if (e.held && e.tail === 0) t += " <b>Held up</b>: you could not get past, so you drove the rival's lap.";
      else if (e.tail === 0 && e.wake > 0) t += " Its wake cost you " + fx(e.wake) + " s.";
      t += " You are " + (e.ahead ? "<b>P1</b>, " + fx(-(e.totals[0] - e.totals[1])) + " s ahead." : "<b>P2</b>, " + fx(e.totals[0] - e.totals[1]) + " s behind.");
      return t;
    }

    function call(a) {
      if (!duel || duel.done) return;
      var s = duel.state(), lg = duel.model.legal(s.lap, s.compound, s.weather, s.usedBoth);
      if (lg.actions.indexOf(a) < 0) { msg = "<b>" + NAMES[a] + "</b> is not allowed: " + lg.why[a] + "."; draw(); return; }
      duel.step(a);
      msg = describe(duel.log[duel.log.length - 1]);
      if (duel.done) finish();
      draw();
    }

    function myPlan() {
      var p = {};
      duel.log.forEach(function (e) { if (e.action !== PW.STAY_OUT) p[e.lap] = e.action; });
      return p;
    }

    function finish() {
      var best = D.bestPlan(opts()), you = duel.time[0], gap = you - best.total, plan = myPlan();
      var others = [6, 9, 12].map(function (r) { return { lap: r, total: D.play(plan, opts({ rivalLap: r })).total }; });
      var prev = PW.ui.load().pitwall.best.rival, pb = false;
      if (blocking && (!prev || gap < prev.gap - 1e-9)) {
        pb = true;
        U.save(function (st) { st.pitwall.best.rival = { time: you, best: best.total, gap: gap, seed: seed, rivalLap: rivalLap, at: Date.now() }; });
        if (root.F1NAV) root.F1NAV.refresh();
      }
      result = { you: you, best: best, gap: gap, ahead: duel.agentAhead(), others: others, pb: pb, prev: prev };
    }

    /* Every one-stop plan on these dice, blocking off and on, against this rival. */
    function board() {
      var rows = "", cols = fixed ? [blocking] : [false, true], res = {}, best = {};
      cols.forEach(function (b) {
        res[b] = [];
        for (var lap = 3; lap <= 13; lap++) {
          var p = {}; p[lap] = PW.PIT_B;
          var r = D.play(p, opts({ interaction: b }));
          res[b].push({ lap: lap, total: r.total, ahead: r.finishedAhead });
          if (best[b] === undefined || r.total < best[b] - 1e-12) best[b] = r.total;
        }
      });
      for (var i = 0; i < res[cols[0]].length; i++) {
        rows += "<tr><td>lap " + res[cols[0]][i].lap + (res[cols[0]][i].lap === rivalLap ? " (the rival's lap)" : "") + "</td>";
        cols.forEach(function (b) {
          var r = res[b][i];
          rows += '<td class="' + (Math.abs(r.total - best[b]) < 1e-9 ? "t-green" : "") + '">' + fx(r.total) + "</td><td>" + (r.ahead ? "P1" : "P2") + "</td>";
        });
        rows += "</tr>";
      }
      var head = cols.map(function (b) { return "<th>blocking " + (b ? "on" : "off") + "</th><th>finish</th>"; }).join("");
      return '<details class="pw-details pw-board"' + (boardOpen ? " open" : "") + "><summary>Every one-stop plan on these dice, against a rival stopping on lap " + rivalLap +
        '</summary><table class="pw-trace"><thead><tr><th>box for B on</th>' + head + "</tr></thead><tbody>" + rows + "</tbody></table>" +
        '<p class="pw-msg">Race time to the flag, counting the 0.3 s you start behind. Green is the fastest stop in its column. Change the rival\'s lap above and watch which column moves.</p></details>';
    }

    /* Gap to the rival after each lap: above the line you are behind, below it you are ahead. */
    function gapChart() {
      var H = duel.model.horizon, W = 600, Ht = 120, pad = 30, cap = 8;
      function x(l) { return pad + (W - pad - 8) * l / H; }
      function y(g) { return Ht / 2 - (Ht / 2 - 10) * Math.max(-cap, Math.min(cap, g)) / cap; }
      var pts = [x(0) + "," + y(duel.startGap)].concat(duel.log.map(function (e) { return x(e.lap) + "," + y(e.totals[0] - e.totals[1]); }));
      var pits = duel.log.filter(function (e) { return e.rivalAction !== PW.STAY_OUT; }).map(function (e) {
        return '<line class="goal" x1="' + x(e.lap) + '" x2="' + x(e.lap) + '" y1="6" y2="' + (Ht - 6) + '"></line><text class="goal" x="' + (x(e.lap) + 3) + '" y="16">rival stops</text>';
      }).join("");
      return '<svg class="pw-chart" viewBox="0 0 ' + W + " " + Ht + '" role="img" aria-label="gap to the rival after each lap">' +
        '<line class="grid" x1="' + pad + '" x2="' + (W - 8) + '" y1="' + y(0) + '" y2="' + y(0) + '"></line>' + pits +
        '<text x="0" y="' + (y(cap) + 4) + '">+' + cap + "</text><text x=\"0\" y=\"" + (y(-cap) + 4) + '">−' + cap + "</text>" +
        '<text x="' + (pad + 4) + '" y="' + (y(0) - 5) + '">behind ↑ · ahead ↓</text>' +
        '<polyline points="' + pts.join(" ") + '" style="stroke:var(--accent)"></polyline></svg>';
    }

    function draw() {
      var H = duel.model.horizon, s = duel.state(), h = "";
      h += '<div class="pw-head"><div class="pw-kicker"><b>Rival</b><span>Phase 6</span><span>toy race · ' + H + " laps · dry, no safety car</span><span>race #" + seed + "</span></div>";
      h += '<div class="pw-kicker">' + (fixed ? "" : '<label class="pw-toggle"><input type="checkbox" data-pw="blocking"' + (blocking ? " checked" : "") + "> blocking (held up unless you pass)</label>") +
        '<label>Rival stops on <select data-pw="rival">' + RIVAL_LAPS.map(function (l) {
          return '<option value="' + l + '"' + (l === rivalLap ? " selected" : "") + ">lap " + l + "</option>";
        }).join("") + "</select></label></div></div>";
      var rv = duel.rivalState(), g = duel.gap();
      if (!duel.done) {
        h += '<div class="pw-head"><div class="pw-lap">LAP ' + s.lap + " <small>/ " + H + "</small></div><div>" +
          '<span class="pw-flag ' + (blocking ? "sc" : "green") + '">' + (blocking ? "BLOCKING ON" : "BLOCKING OFF") + "</span></div></div>";
        h += '<div class="pw-stats"><div class="pw-stat"><span>your tyre</span><b>' + U.tyre(s.compound) + " " + s.age + (s.age === 1 ? " lap" : " laps") +
          '</b></div><div class="pw-stat"><span>rival\'s tyre</span><b>' + U.tyre(rv.compound) + " " + rv.age + (rv.age === 1 ? " lap" : " laps") +
          '</b></div><div class="pw-stat"><span>position</span><b>' + (duel.agentAhead() ? "P1" : "P2") +
          '</b></div><div class="pw-stat"><span>gap to the rival</span><b>' + (g > 0 ? fx(g) + " behind" : fx(-g) + " ahead") + "</b></div></div>";
        var lg = duel.model.legal(s.lap, s.compound, s.weather, s.usedBoth);
        h += '<div class="pw-calls">';
        for (var a = 0; a < 3; a++) {
          var ok = lg.actions.indexOf(a) >= 0;
          h += '<button type="button" class="pw-call" data-pw-call="' + a + '"' + (ok ? "" : ' disabled aria-disabled="true"') + ">" + NAMES[a] +
            (ok ? "<kbd>" + KEYS[a].toUpperCase() + "</kbd>" : '<span class="why">' + lg.why[a] + "</span>") + "</button>";
        }
        h += "</div>";
        h += '<p class="pw-msg" aria-live="polite">' + msg + "</p>";
      } else {
        var r = result;
        h += '<div class="pw-head"><div class="pw-lap">FLAG <small>' + (r.ahead ? "you finish P1" : "you finish P2") + "</small></div></div>";
        h += '<div class="pw-result"><div><span>you</span><b class="' + (r.gap <= 1 ? "t-green" : "t-yellow") + '">' + fx(r.you) + "</b><small>" + (r.ahead ? "P1, " : "P2, ") +
          (blocking ? (r.pb ? "personal best" : r.prev ? "best gap so far +" + fx(r.prev.gap) : "") : "practice: blocking off") + "</small></div>" +
          '<div><span>best plan on these dice</span><b class="t-purple">' + fx(r.best.total) + "</b><small>" + D.planName(r.best.plan) + "; you " + signed(r.gap) + " s</small></div>" +
          "<div><span>rival</span><b>" + fx(duel.time[1]) + "</b><small>one stop, lap " + rivalLap + "</small></div></div>";
        h += '<p class="pw-msg" aria-live="polite">' + msg + " Your calls against a rival stopping on another lap: " + r.others.map(function (o) {
          return "lap " + o.lap + " → " + fx(o.total) + " s";
        }).join(", ") + "." + (blocking ? (r.gap <= 1 ? " <b>Within a second of the best plan.</b>" : "") + " A race with blocking on within 1 s of the best plan scores 5 championship points." :
          " Practice races (blocking off) don't count for points.") + "</p>";
      }
      h += gapChart();
      h += U.strip(duel.log, H, duel.done ? 0 : s.lap, "you") +
        U.strip(duel.log.map(function (e) { return { state: e.rival, action: e.rivalAction, time: e.rivalTime }; }), H, 0, "rival") + U.LEGEND;
      h += '<div class="pw-actions">' + (duel.done ? '<button type="button" class="pw-btn go" data-pw="new">New race</button>' : "") +
        '<button type="button" class="pw-btn" data-pw="again">' + (duel.done ? "Same dice again" : "Restart") + "</button></div>";
      h += board();
      node.innerHTML = h;

      Array.prototype.forEach.call(node.querySelectorAll("[data-pw-call]"), function (b) {
        b.addEventListener("click", function () { call(parseInt(b.getAttribute("data-pw-call"), 10)); });
      });
      function on(sel, ev, fn) { var e = node.querySelector('[data-pw="' + sel + '"]'); if (e) e.addEventListener(ev, fn); }
      on("new", "click", function () { start(true); });
      on("again", "click", function () { start(false); });
      on("blocking", "change", function (e) { blocking = e.target.checked; start(false); });
      on("rival", "change", function (e) { rivalLap = parseInt(e.target.value, 10); start(false); });
      var bd = node.querySelector(".pw-board");
      if (bd) bd.addEventListener("toggle", function () { boardOpen = bd.open; });
    }

    document.addEventListener("keydown", function (ev) {
      if (ev.ctrlKey || ev.metaKey || ev.altKey || !duel || duel.done) return;
      var t = ev.target;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable)) return;
      var a = KEYS.indexOf(String(ev.key).toLowerCase());
      if (a < 0) return;
      var r = node.getBoundingClientRect();
      if (r.bottom < 0 || r.top > (window.innerHeight || 800)) return;
      ev.preventDefault();
      call(a);
    });

    start(false);
  }

  PW.mountRival = mountRival;
})(this);
