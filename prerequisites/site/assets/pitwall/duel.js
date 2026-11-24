/* Pit Wall, Rival mode engine (Phase 6): the two-car duel race, a line-for-line port of
   labs/labkit/duel.py. Needs engine.js first (in Node: require it and pass it in).
   Checked against the Python by labs/tools/pitwall_duel_parity.py: every lap time of every
   one- and two-stop plan, blocking off and on, on shared dice, to 1e-9.

   The dice: one uniform number per lap, used for a pass attempt when there is one. Python draws
   them from numpy; here they come from PitWall.rngFrom(seed). The parity check feeds the same
   numbers to both sides, so the two engines are compared on identical dice.

   Blocking off (interaction false) is the plan's race as written: each car drives its own lap
   time, and position is only a readout of time. Blocking on adds the wake, being held up and
   passing (duel.py's header has the rules). */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) module.exports = factory;
  else factory(root.PitWall);
})(this, function (PW) {
  "use strict";
  var STAY_OUT = PW.STAY_OUT, PIT_A = PW.PIT_A, PIT_B = PW.PIT_B, A = PW.A, B = PW.B;
  var C = {
    FOLLOW_GAP: 1.0, WAKE_MAX: 0.5, WAKE_RANGE: 1.5, PASS_STEEPNESS: 5.0, PASS_CAP: 0.95,
    AFTER_PASS: 0.2, RIVAL_SLOWER: 0.3, START_GAP: 0.3, RIVAL_LAP: 9
  };
  var QUIET = new PW.RaceModel({ scHazard: 0.0 });

  function wakeLoss(gap) {
    if (gap >= C.WAKE_RANGE) return 0.0;
    return C.WAKE_MAX * (C.WAKE_RANGE - Math.max(gap, 0.0)) / C.WAKE_RANGE;
  }
  function passChance(delta) {
    if (delta >= 0) return 0.0;
    return Math.min(C.PASS_CAP, 1.0 / (1.0 + Math.exp(C.PASS_STEEPNESS * (delta + 0.5))));
  }
  function dice(seed, horizon) {
    var r = PW.rngFrom(seed), d = [];
    for (var i = 0; i < (horizon || QUIET.horizon); i++) d.push(r());
    return d;
  }

  /* opts: rivalScript {lap: action} (default {9: PIT_B}) or rivalLap, interaction (default true),
     passing (default true), rivalSlower, startGap, dice (one number per lap) or seed. */
  function Duel(opts) {
    opts = opts || {};
    this.model = opts.model || QUIET;
    var script = opts.rivalScript;
    if (!script) { script = {}; script[opts.rivalLap || C.RIVAL_LAP] = PIT_B; }
    this.rivalScript = script;
    this.offset = [0.0, opts.rivalSlower !== undefined ? opts.rivalSlower : C.RIVAL_SLOWER];
    this.startGap = opts.startGap !== undefined ? opts.startGap : C.START_GAP;
    this.interaction = opts.interaction !== false;
    this.passing = opts.passing !== false;
    this.dice = opts.dice || dice(opts.seed || 0, this.model.horizon);
    this.lap = 1; this.compound = [A, A]; this.age = [1, 1]; this.usedBoth = [false, false];
    this.time = [this.startGap, 0.0];
    this.log = []; this.done = false;
  }
  Duel.prototype.agentAhead = function () { return this.time[0] < this.time[1]; };
  Duel.prototype.gap = function () { return this.time[0] - this.time[1]; };
  /* The agent's state, in the engine's shape, for the legal-call mask and the lap strip. */
  Duel.prototype.state = function () {
    return { lap: this.lap, compound: this.compound[0], age: this.age[0], sc: 0, usedBoth: this.usedBoth[0], weather: PW.DRY };
  };
  Duel.prototype.rivalState = function () {
    return { lap: this.lap, compound: this.compound[1], age: this.age[1], sc: 0, usedBoth: this.usedBoth[1], weather: PW.DRY };
  };
  Duel.prototype.step = function (action) {
    if (this.done) throw new Error("the race is over");
    var m = this.model, lap = this.lap, i;
    var states = [this.state(), this.rivalState()];
    var actions = [action, this.rivalScript[lap] !== undefined ? this.rivalScript[lap] : STAY_OUT];
    var own = [0, 1].map(function (k) { return m.cost(lap, this.compound[k], this.age[k], actions[k], PW.DRY, 0) + this.offset[k]; }, this);
    var times = own.slice();
    var u = this.dice[lap - 1];
    var lead = this.time[0] < this.time[1] ? 0 : 1, tail = 1 - lead;
    var gap = this.time[tail] - this.time[lead];
    var held = false, passed = false, wake = 0.0, chance = 0.0;
    if (this.interaction) {
      wake = wakeLoss(gap);
      times[tail] += wake;
      if (gap < C.FOLLOW_GAP) {
        chance = this.passing ? passChance(times[tail] - times[lead]) : 0.0;
        if (this.passing && u < chance) passed = true;
        else if (times[tail] < times[lead]) { held = true; times[tail] = times[lead]; }
      }
    }
    var before = this.time.slice();
    for (i = 0; i < 2; i++) this.time[i] += times[i];
    if (passed && this.time[tail] > this.time[lead] - C.AFTER_PASS) this.time[tail] = this.time[lead] - C.AFTER_PASS;
    for (i = 0; i < 2; i++) {
      var nt = PW.RaceModel.nextTyre(this.compound[i], this.age[i], actions[i]);
      this.usedBoth[i] = this.usedBoth[i] || nt[0] !== this.compound[i];
      this.compound[i] = nt[0]; this.age[i] = nt[1];
    }
    this.lap += 1;
    if (this.lap > m.horizon) this.done = true;
    var lapTimes = [this.time[0] - before[0], this.time[1] - before[1]];
    var e = {
      lap: lap, state: states[0], rival: states[1], action: actions[0], rivalAction: actions[1],
      time: lapTimes[0], rivalTime: lapTimes[1], own: own, tail: tail, gapBefore: gap, u: u, chance: chance,
      wake: wake, held: held, passed: passed, passer: passed ? (tail === 0 ? "agent" : "rival") : null,
      totals: this.time.slice(), ahead: this.agentAhead()
    };
    this.log.push(e);
    return lapTimes[0];
  };

  /* A whole race from an open-loop plan {lap: action}. */
  function play(plan, opts) {
    var d = new Duel(opts);
    while (!d.done) d.step(plan[d.lap] !== undefined ? plan[d.lap] : STAY_OUT);
    return { total: d.time[0], rival: d.time[1], finishedAhead: d.agentAhead(), log: d.log };
  }
  function oneStopPlans(H) {
    var out = [];
    for (var lap = 1; lap < (H || 20); lap++) { var p = {}; p[lap] = PIT_B; out.push(p); }
    return out;
  }
  function twoStopPlans(H) {
    var out = [];
    for (var l1 = 1; l1 < (H || 20); l1++) for (var l2 = l1 + 1; l2 < (H || 20); l2++) { var p = {}; p[l1] = PIT_B; p[l2] = PIT_A; out.push(p); }
    return out;
  }
  var NAMES = ["stay out", "box for A", "box for B"];
  function planName(plan) {
    var laps = Object.keys(plan).map(Number).sort(function (a, b) { return a - b; });
    return laps.map(function (l) { return "lap " + l + " " + NAMES[plan[l]]; }).join(" + ") || "no stop";
  }
  /* The best open-loop plan on these dice (one- and two-stop plans, as the labs rank them). */
  function bestPlan(opts) {
    var plans = oneStopPlans().concat(twoStopPlans()), best = null;
    plans.forEach(function (p) {
      var r = play(p, opts);
      if (!best || r.total < best.total - 1e-12) best = { plan: p, total: r.total, finishedAhead: r.finishedAhead, log: r.log };
    });
    return best;
  }

  var api = { CONST: C, QUIET: QUIET, wakeLoss: wakeLoss, passChance: passChance, dice: dice, Duel: Duel, play: play,
    oneStopPlans: oneStopPlans, twoStopPlans: twoStopPlans, planName: planName, bestPlan: bestPlan };
  PW.duel = api;
  return api;
});
