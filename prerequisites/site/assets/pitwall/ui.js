/* Pit Wall UI: play the toy race one call at a time, then see it as the course sees it.
   Needs engine.js and oracle.js first. Mounts on <div data-widget="pitwall"> through
   window.LAB_WIDGETS (labs.js runs the mounts), or directly with PitWall.mount(node).

   Options (data attributes on the node)
     data-mode     "race" (Phase 1) or "oracle" (Phase 3.5: the oracle's call and the cost of yours
                   each lap, Oracle A in the rain, and the time split into expectation, calls
                   and luck), or "learner" (Phase 4: a table learner trains on the race; drawn
                   by learnerui.js, which needs learner.js), or "replay" (Phase 5: the capstone DQN
                   on the race, exploration off and on; drawn by replayui.js, which needs replay.js
                   and replay_policy.js), or "rival" (Phase 6: a second car, blocking off or on; drawn by
                   rivalui.js, which needs duel.js), or "duel" (Phase 8: the pit-timing duel; drawn by
                   pitgameui.js, which needs duel.js, pitgame_data.js and pitgame.js), or "training"
                   (Phase 9: recorded learning runs, replayed; drawn by trainingui.js, which needs
                   training_data.js). Each mode
                   keeps its own personal best.
     data-numbers  "1" starts Oracle mode with the oracle's numbers on the buttons
     data-weather  "fixed" (dry all race, default) or "markov" (rain can come and go)
     data-seed     a fixed race (same safety car and weather every time); default is a fresh race
     data-picker   "1" shows the mode and dry/rain pickers (the Pit Wall page)
   Personal bests go in f1prereq.v1 as pitwall.best[mode] = { time, oracle, gap, seed, weather, at },
   where gap = your time - the oracle's time on the same dice. Points count a gap of 1 s or less. */
(function (root) {
  "use strict";
  var PW = root.PitWall;
  if (!PW || !PW.oracle) return;
  var KEY = "f1prereq.v1", NAMES = PW.ACTION_NAMES, KEYS = ["s", "a", "b"];
  var solved = {};

  function load() {
    var s;
    try { s = JSON.parse(localStorage.getItem(KEY)); } catch (e) { s = null; }
    s = s || {};
    s.pitwall = s.pitwall || {};
    s.pitwall.best = s.pitwall.best || {};
    return s;
  }
  function save(fn) {
    var s = load(); fn(s);
    try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) { /* storage unavailable */ }
  }
  function fx(x, d) { return x.toFixed(d === undefined ? 2 : d); }
  function signed(x, d) {
    var r = Math.abs(x) < 0.5 * Math.pow(10, -(d === undefined ? 2 : d)) ? 0 : x;  // no "−0.00" from float noise
    return (r > 0 ? "+" : r < 0 ? "−" : "±") + fx(Math.abs(r), d);
  }
  function solveFor(weather) {
    if (!solved[weather]) {
      var m = new PW.RaceModel({ weather: weather });
      solved[weather] = { model: m, sol: PW.oracle.solve(m) };
    }
    return solved[weather];
  }
  function newSeed() { return 100 + Math.floor(Math.random() * 99900); }

  function tyre(c) { return '<span class="pw-tyre' + (c === PW.B ? " b" : "") + '">' + PW.COMPOUND_NAMES[c] + "</span>"; }

  function strip(entries, H, nowLap, label) {
    var h = (label ? '<div class="pw-kicker" style="margin:10px 0 0"><b>' + label + "</b></div>" : "") +
      '<div class="lapstrip" style="--laps:' + H + '" role="img" aria-label="' + (label || "lap strip") + '">';
    for (var lap = 1; lap <= H; lap++) {
      var e = entries[lap - 1], cls = "lc";
      if (e) {
        var after = e.action === PW.PIT_A ? PW.A : e.action === PW.PIT_B ? PW.B : e.state.compound;
        cls += after === PW.B ? " b" : " a";
        if (e.state.sc) cls += " sc";
        if (e.state.weather === PW.WET) cls += " wet";
        if (e.action !== PW.STAY_OUT) cls += " pit";
      }
      if (lap === nowLap) cls += " now";
      h += '<div class="' + cls + '" title="lap ' + lap + (e ? ": " + NAMES[e.action] + ", " + fx(e.time) + " s" : "") + '"></div>';
    }
    return h + "</div>";
  }
  var LEGEND = '<div class="lapstrip-legend"><span><i style="background:var(--tyre-a)"></i>on A</span>' +
    '<span><i style="background:var(--tyre-b)"></i>on B</span><span>P = pit stop</span>' +
    '<span><i style="background:rgba(242,201,76,.6)"></i>safety car</span>' +
    '<span><i style="background:rgba(90,169,255,.5)"></i>wet</span></div>';

  function mount(node) {
    var mode = node.getAttribute("data-mode") || "race";
    if (mode === "learner") { if (PW.mountLearner) PW.mountLearner(node); return; }
    if (mode === "replay") { if (PW.mountReplay) PW.mountReplay(node); return; }
    if (mode === "rival") { if (PW.mountRival) PW.mountRival(node); return; }
    if (mode === "duel") { if (PW.mountDuel) PW.mountDuel(node); return; }
    if (mode === "training") { if (PW.mountTraining) PW.mountTraining(node); return; }
    var weather = node.getAttribute("data-weather") || "fixed";
    var fixedSeed = node.getAttribute("data-seed");
    var picker = node.getAttribute("data-picker") === "1";
    var seed = fixedSeed ? parseInt(fixedSeed, 10) : newSeed();
    var race, dice, ctx, asMdp = false, lastMsg = "";
    var showNums = node.getAttribute("data-numbers") === "1";

    node.classList.add("pw-panel", "pitwall");
    node.setAttribute("tabindex", "-1");

    function start(newDice) {
      ctx = solveFor(weather);
      if (newDice) seed = newSeed();
      dice = PW.drawDice(ctx.model, seed);
      race = new PW.Race(ctx.model, dice);
      lastMsg = "Lights out. You start on " + tyre(PW.A) + " (fast, wears out by lap 6 or so). " +
        "You must run both compounds in a dry race.";
      draw();
    }

    function call(a) {
      if (race.done) return;
      var s = race.state(), lg = ctx.model.legal(s.lap, s.compound, s.weather, s.usedBoth);
      if (lg.actions.indexOf(a) < 0) { lastMsg = "<b>" + NAMES[a] + "</b> is not allowed: " + lg.why[a] + "."; draw(); return; }
      var best = ctx.sol.best(s), reg = ctx.sol.regret(s, a);
      var t = race.step(a), ns = race.state();
      lastMsg = "Lap " + s.lap + ": <b>" + NAMES[a] + "</b>, " + fx(t) + " s." +
        (mode === "oracle" ? (reg > 1e-9 ? " The oracle: <b>" + NAMES[best] + "</b>. Yours cost <b class=\"t-yellow\">+" + fx(reg) + " s</b> on average." : " The oracle agrees.") : "") +
        (!race.done && ns.sc && !s.sc ? " <b>Safety car out</b> for lap " + ns.lap + ": laps are slow and a stop costs 40%." : "") +
        (!race.done && !ns.sc && s.sc ? " Safety car in." : "") +
        (!race.done && ns.weather !== s.weather ? (ns.weather === PW.WET ? " <b>Rain</b> from lap " + ns.lap + "." : " The track is drying.") : "");
      if (race.done) finish();
      draw();
    }

    function finish() {
      var orc = PW.simulate(ctx.model, ctx.sol.asPolicy(), dice);
      var hind = PW.oracle.hindsight(ctx.model, dice);
      race.result = { you: race.total, oracle: orc.time, hind: hind.time, orcLog: orc.log, hindActions: hind.actions };
      if (mode === "oracle") {
        race.result.dYou = PW.oracle.decompose(ctx.sol, race.log);
        race.result.dOrc = PW.oracle.decompose(ctx.sol, orc.log);
        if (weather === "markov") { var fa = PW.oracle.foresight(ctx.model, dice); race.result.foreA = fa.time; race.result.foreLog = fa.log; }
      }
      var gap = race.total - orc.time, prev = load().pitwall.best[mode], pb = !prev || race.total < prev.time;
      if (pb) {
        save(function (s) {
          s.pitwall.best[mode] = { time: race.total, oracle: orc.time, gap: gap, seed: seed, weather: weather, at: Date.now() };
        });
        if (root.F1NAV) root.F1NAV.refresh();
      }
      race.result.pb = pb; race.result.prev = prev;
    }

    function hindLog() {
      // replay the hindsight actions on the same dice for the strip
      var r = new PW.Race(ctx.model, dice), acts = race.result.hindActions;
      while (!r.done) r.step(acts[r.lap - 1]);
      return r.log;
    }

    /* time = expected at the start + cost of the calls + luck. Luck is shown as what is left after the
       rounded parts, so each row adds up as printed. */
    function splitTable() {
      var r = race.result;
      function row(name, d, time, cls) {
        var st = Math.round(d.start * 100) / 100, rg = Math.round(d.regret * 100) / 100, tm = Math.round(time * 100) / 100;
        return "<tr><td>" + name + "</td><td>" + fx(st) + "</td><td>" + (rg > 0 ? "+" + fx(rg) : "0.00") + "</td><td>" +
          signed(tm - st - rg) + '</td><td class="' + cls + '">' + fx(tm) + "</td></tr>";
      }
      var you = r.dYou, orc = r.dOrc, edge = (orc.luck - you.luck);
      return '<table class="pw-trace pw-split"><thead><tr><th>where the time went</th><th>expected at the start</th>' +
        "<th>cost of the calls</th><th>luck</th><th>time</th></tr></thead><tbody>" +
        row("you", you, r.you, "t-green") + row("oracle", orc, r.oracle, "t-purple") + "</tbody></table>" +
        '<p class="pw-msg">' + (r.you < r.oracle - 1e-9
          ? "You beat the oracle, and your calls still cost " + fx(you.regret) + " s on average. Your luck beat its luck by " + fx(edge) + " s, which is more than your calls cost. Better dice, not better calls."
          : you.regret < 1e-9 ? "Every call you made was as good as the oracle's on average. Any gap is luck."
          : "Your calls cost " + fx(you.regret) + " s on average" + (Math.abs(edge) > 0.005 ? ", and luck moved you " + signed(-edge) + " s against the oracle" : "") + ".") +
        " The cost of a call is how much slower the rest of the race is, on average, after it than after the best call. It is never negative. Luck is whatever the dice added or took away, and it can go either way.</p>";
    }

    function traceTable() {
      var h = '<table class="pw-trace"><thead><tr><th>lap</th><th>state (tyre, age, SC, both, wet)</th><th>your call</th>' +
        "<th>lap time</th><th>reward</th><th>centred</th><th>sum</th>" + (race.done ? "<th>best call</th><th>cost of yours</th>" : "") +
        (race.done && mode === "oracle" ? "<th>luck</th>" : "") +
        "</tr></thead><tbody>", sum = 0;
      race.log.forEach(function (e, i) {
        var s = e.state; sum -= e.time;
        h += "<tr><td>" + s.lap + "</td><td>(" + PW.COMPOUND_NAMES[s.compound] + ", " + s.age + ", " + s.sc + ", " +
          (s.usedBoth ? 1 : 0) + ", " + s.weather + ")</td><td>" + NAMES[e.action] + "</td><td>" + fx(e.time) + "</td><td>" +
          signed(-e.time) + "</td><td>" + signed(-(e.time - PW.CONST.BASE_LAP)) + "</td><td>" + fx(sum).replace("-", "−") + "</td>";
        if (race.done) {
          var best = ctx.sol.best(s), reg = ctx.sol.regret(s, e.action);
          h += "<td>" + NAMES[best] + "</td><td" + (reg > 1e-9 ? ' class="t-yellow"' : "") + ">" + (reg > 1e-9 ? "+" + fx(reg) + " s" : "—") + "</td>";
          if (mode === "oracle") h += "<td>" + signed(race.result.dYou.rows[i].luck) + "</td>";
        }
        h += "</tr>";
      });
      return h + "</tbody></table>" +
        '<p class="pw-msg">Reward = −(lap time). Centred = −(lap time − 10), the same ranking of policies with smaller numbers.' +
        (race.done ? " Cost of yours = how much slower, on average, the rest of the race is after your call than after the best one." : "") + "</p>";
    }

    function draw() {
      var s = race.state(), H = ctx.model.horizon, h = "";
      h += '<div class="pw-head"><div class="pw-kicker"><b>The Pit Wall</b><span>toy race · ' + H + " laps</span>" +
        (weather === "markov" ? "<span>rain possible</span>" : "<span>dry</span>") + "<span>race #" + seed + "</span></div>";
      if (picker || mode === "oracle") {
        h += '<div class="pw-kicker">';
        if (picker) h += '<label>Mode <select data-pw="mode"><option value="race"' + (mode === "race" ? " selected" : "") +
          '>Race · Phase 1</option><option value="oracle"' + (mode === "oracle" ? " selected" : "") + ">Oracle · Phase 3.5</option></select></label>";
        if (mode === "oracle") h += '<label class="pw-toggle"><input type="checkbox" data-pw="numbers"' + (showNums ? " checked" : "") + "> show the oracle's numbers</label>";
        h += "</div>";
      }
      if (picker) {
        h += '<div class="pw-kicker"><label>Weather <select data-pw="weather">' +
          '<option value="fixed"' + (weather === "fixed" ? " selected" : "") + ">dry, safety car possible</option>" +
          '<option value="markov"' + (weather === "markov" ? " selected" : "") + ">rain can come and go</option></select></label></div>";
      }
      h += "</div>";

      if (!race.done) {
        h += '<div class="pw-head"><div class="pw-lap">LAP ' + s.lap + " <small>/ " + H + "</small></div><div>" +
          (s.sc ? '<span class="pw-flag sc">SAFETY CAR</span> ' : '<span class="pw-flag green">GREEN</span> ') +
          (s.weather === PW.WET ? '<span class="pw-flag wet">WET</span>' : "") + "</div></div>";
        h += '<div class="pw-stats"><div class="pw-stat"><span>tyre</span><b>' + tyre(s.compound) + " " + s.age +
          (s.age === 1 ? " lap" : " laps") + '</b></div><div class="pw-stat"><span>last lap</span><b>' +
          (race.log.length ? fx(race.log[race.log.length - 1].time) : "—") + '</b></div><div class="pw-stat"><span>race time</span><b>' +
          fx(race.total) + '</b></div><div class="pw-stat"><span>' + (mode === "oracle" && showNums ? "expected to the flag" : "both used") + "</span><b>" +
          (mode === "oracle" && showNums ? fx(ctx.sol.value(s)) : s.usedBoth ? "yes" : "not yet") + "</b></div></div>";
        var lg = ctx.model.legal(s.lap, s.compound, s.weather, s.usedBoth);
        h += '<div class="pw-calls">';
        for (var a = 0; a < 3; a++) {
          var ok = lg.actions.indexOf(a) >= 0;
          h += '<button type="button" class="pw-call" data-pw-call="' + a + '"' + (ok ? "" : ' disabled aria-disabled="true"') + ">" +
            NAMES[a] + (ok ? "<kbd>" + KEYS[a].toUpperCase() + "</kbd>" : '<span class="why">' + lg.why[a] + "</span>") +
            (ok && mode === "oracle" && showNums ? '<span class="q">' + (ctx.sol.regret(s, a) > 1e-9 ? "+" + fx(ctx.sol.regret(s, a)) + " s on average" : "the oracle's call") + "</span>" : "") +
            "</button>";
        }
        h += "</div>";
        h += '<p class="pw-msg" aria-live="polite">' + lastMsg + "</p>";
        h += strip(race.log, H, s.lap) + LEGEND;
      } else {
        var r = race.result, gap = r.you - r.oracle;
        h += '<div class="pw-head"><div class="pw-lap">FLAG <small>race over</small></div></div>';
        h += '<div class="pw-result">' +
          '<div><span>you</span><b class="' + (r.pb ? "t-green" : "t-yellow") + '">' + fx(r.you) + "</b><small>" +
          (r.pb ? "personal best" : "best so far " + fx(r.prev.time)) + "</small></div>" +
          '<div><span>oracle (best on average)</span><b class="t-purple">' + fx(r.oracle) + "</b><small>you " + signed(gap) + " s</small></div>" +
          (r.foreA !== undefined ? '<div><span>oracle A (knew the weather)</span><b class="t-purple">' + fx(r.foreA) + "</b><small>you " + signed(r.you - r.foreA) + " s</small></div>" : "") +
          '<div><span>hindsight (knew the dice)</span><b class="t-purple">' + fx(r.hind) + "</b><small>you " + signed(r.you - r.hind) + " s</small></div></div>";
        h += '<p class="pw-msg">' + (gap <= 1.0
          ? "<b>Within a second of the oracle.</b>" + (gap < -1e-9 ? " You beat it on these dice: the oracle plays the odds, and the odds went your way." : "")
          : "The oracle used the same safety car and weather and was " + fx(gap) + " s quicker. Open the race as an MDP to see where.") +
          " The oracle cannot see the future; hindsight can, which is why nobody beats hindsight.</p>";
        if (mode === "oracle") h += splitTable();
        h += strip(race.log, H, 0, "you") + strip(r.orcLog, H, 0, "oracle") + (r.foreLog ? strip(r.foreLog, H, 0, "oracle A") : "") +
          strip(hindLog(), H, 0, "hindsight") + LEGEND;
        h += '<div class="pw-actions"><button type="button" class="pw-btn go" data-pw="new">New race</button>' +
          '<button type="button" class="pw-btn" data-pw="again">Same dice again</button></div>';
      }

      if (race.log.length) {
        h += '<details class="pw-details"' + (asMdp ? " open" : "") + '><summary>This race as an MDP: states, actions, rewards</summary>' + traceTable() + "</details>";
      }
      node.innerHTML = h;

      Array.prototype.forEach.call(node.querySelectorAll("[data-pw-call]"), function (b) {
        b.addEventListener("click", function () { call(parseInt(b.getAttribute("data-pw-call"), 10)); });
      });
      var det = node.querySelector(".pw-details");
      if (det) det.addEventListener("toggle", function () { asMdp = det.open; });
      var bn = node.querySelector('[data-pw="new"]'), ba = node.querySelector('[data-pw="again"]'), sel = node.querySelector('[data-pw="weather"]');
      if (bn) bn.addEventListener("click", function () { start(true); });
      if (ba) ba.addEventListener("click", function () { start(false); });
      if (sel) sel.addEventListener("change", function () { weather = sel.value; start(!fixedSeed); });
      var ms = node.querySelector('[data-pw="mode"]'), nb = node.querySelector('[data-pw="numbers"]');
      if (ms) ms.addEventListener("change", function () { mode = ms.value; start(false); });
      if (nb) nb.addEventListener("change", function () { showNums = nb.checked; draw(); });
    }

    // S / A / B while the Pit Wall is on screen and you are not typing somewhere else
    document.addEventListener("keydown", function (ev) {
      if (ev.ctrlKey || ev.metaKey || ev.altKey || !race || race.done) return;
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

  PW.mount = mount;
  PW.ui = { strip: strip, LEGEND: LEGEND, fx: fx, signed: signed, load: load, save: save, tyre: tyre };
  root.LAB_WIDGETS = root.LAB_WIDGETS || {};
  root.LAB_WIDGETS.pitwall = mount;
})(this);
