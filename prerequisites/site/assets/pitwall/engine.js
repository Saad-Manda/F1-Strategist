/* Pit Wall engine: the toy race of the capstones, a line-for-line port of labs/labkit/toyrace.py.
   Checked against the Python by labs/tools/pitwall_parity.py (lap times and values to 1e-9).
   Works in the browser (window.PitWall) and in Node (module.exports). */
(function (root) {
  "use strict";

  var STAY_OUT = 0, PIT_A = 1, PIT_B = 2;
  var A = 0, B = 1, DRY = 0, WET = 1;

  var C = {
    HORIZON: 20, BASE_LAP: 10.0, PIT_LOSS: 4.0,
    PACE: [0.0, 0.6], WEAR_RATE: [0.05, 0.02], CLIFF_AGE: [6, 11], CLIFF_SEVERITY: [0.15, 0.08],
    CLIFF_CAP: 4.0, FUEL_PER_LAP: 0.03, WET_PENALTY: [6.0, 5.5], WARMUP: { 1: 1.2, 2: 0.5 },
    SC_HAZARD: 0.06, SC_CONTINUE: 2 / 3, SC_LAP_TIME: 14.0, SC_PIT_DISCOUNT: 0.4,
    WEATHER_CHAIN: [[0.9, 0.1], [0.3, 0.7]]
  };

  function RaceModel(opts) {
    opts = opts || {};
    this.horizon = opts.horizon !== undefined ? opts.horizon : C.HORIZON;
    this.pitLoss = opts.pitLoss !== undefined ? opts.pitLoss : C.PIT_LOSS;
    this.scHazard = opts.scHazard !== undefined ? opts.scHazard : C.SC_HAZARD;
    this.scContinue = opts.scContinue !== undefined ? opts.scContinue : C.SC_CONTINUE;
    this.weather = opts.weather || "fixed";
    if (this.weather !== "fixed" && this.weather !== "markov") throw new Error('weather must be "fixed" or "markov"');
    // weatherTrace: the whole race's weather known in advance (Oracle A), one entry per lap
    this.weatherTrace = opts.weatherTrace ? opts.weatherTrace.slice() : null;
    if (this.weatherTrace && this.weatherTrace.length !== this.horizon) throw new Error("weatherTrace needs one entry per lap");
  }

  RaceModel.prototype.lapCost = function (lap, compound, age, weather, sc) {
    if (sc) return C.SC_LAP_TIME;
    var over = Math.max(0, age - C.CLIFF_AGE[compound]);
    var wear = C.WEAR_RATE[compound] * age + Math.min(C.CLIFF_SEVERITY[compound] * over * over, C.CLIFF_CAP);
    var fuel = C.FUEL_PER_LAP * (this.horizon - lap);
    var wet = weather === WET ? C.WET_PENALTY[compound] : 0.0;
    return C.BASE_LAP + C.PACE[compound] + wear + fuel + wet + (C.WARMUP[age] || 0.0);
  };

  RaceModel.prototype.pitCost = function (sc) {
    return this.pitLoss * (sc ? C.SC_PIT_DISCOUNT : 1.0);
  };

  RaceModel.prototype.cost = function (lap, compound, age, action, weather, sc) {
    return this.lapCost(lap, compound, age, weather, sc) + (action !== STAY_OUT ? this.pitCost(sc) : 0.0);
  };

  RaceModel.nextTyre = function (compound, age, action) {
    if (action === PIT_A) return [A, 1];
    if (action === PIT_B) return [B, 1];
    return [compound, age + 1];
  };

  RaceModel.prototype.scProb = function (scNow) { return scNow ? this.scContinue : this.scHazard; };

  RaceModel.prototype.weatherProbs = function (lap, weather) {
    if (this.weatherTrace) {
      var nxt = lap < this.horizon ? this.weatherTrace[lap] : weather;  // trace[lap] is lap + 1's weather
      return nxt === DRY ? [1.0, 0.0] : [0.0, 1.0];
    }
    if (this.weather === "markov") return C.WEATHER_CHAIN[weather];
    return weather === DRY ? [1.0, 0.0] : [0.0, 1.0];
  };

  /* The Phase 1 capstone's four mask rules. Returns the legal actions, and why each other one is not. */
  RaceModel.prototype.legal = function (lap, compound, weather, usedBoth) {
    var legal = [STAY_OUT, PIT_A, PIT_B], why = {};
    function drop(a, reason) { var i = legal.indexOf(a); if (i >= 0) { legal.splice(i, 1); why[a] = reason; } }
    drop(compound === A ? PIT_A : PIT_B, "already on that compound");
    if (weather === WET) drop(PIT_B, "B is unsafe in the wet");
    if (weather === DRY && !usedBoth && this.horizon - lap <= 1) drop(STAY_OUT, "both compounds must be used in the dry");
    if (!legal.length) { legal = [STAY_OUT]; delete why[STAY_OUT]; }
    return { actions: legal, why: why };
  };
  RaceModel.prototype.legalActions = function (lap, compound, weather, usedBoth) {
    return this.legal(lap, compound, weather, usedBoth).actions;
  };

  /* Dice: two uniform draws per lap, [safety car for the next lap, weather for the next lap],
     in the order simulate() consumes them. Mulberry32, so a seed gives the same race every time. */
  function rngFrom(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function drawDice(model, seed) {
    var r = rngFrom(seed), d = [];
    for (var i = 0; i < 2 * model.horizon; i++) d.push(r());
    return d;
  }

  /* The race as a state machine, so the UI can play it one call at a time. */
  function Race(model, dice, startWeather) {
    this.model = model; this.dice = dice; this.k = 0;
    this.lap = 1; this.compound = A; this.age = 1; this.sc = 0; this.usedBoth = false;
    this.weather = model.weatherTrace ? model.weatherTrace[0] : startWeather === undefined ? DRY : startWeather;
    this.total = 0; this.log = []; this.done = false;
  }
  Race.prototype.state = function () {
    return { lap: this.lap, compound: this.compound, age: this.age, sc: this.sc, usedBoth: this.usedBoth, weather: this.weather };
  };
  Race.prototype.step = function (action) {
    if (this.done) throw new Error("race is over");
    var m = this.model, s = this.state();
    var legal = m.legalActions(s.lap, s.compound, s.weather, s.usedBoth);
    var illegal = legal.indexOf(action) < 0;
    if (illegal) action = Math.min.apply(null, legal);
    var t = m.cost(s.lap, s.compound, s.age, action, s.weather, s.sc);
    this.total += t;
    var nt = RaceModel.nextTyre(s.compound, s.age, action);
    this.usedBoth = this.usedBoth || nt[0] !== s.compound;
    this.compound = nt[0]; this.age = nt[1];
    this.sc = this.dice[this.k++] < m.scProb(s.sc) ? 1 : 0;
    this.weather = this.dice[this.k++] < m.weatherProbs(s.lap, s.weather)[WET] ? 1 : 0;
    this.log.push({ state: s, action: action, time: t, illegal: illegal });
    this.lap += 1;
    if (this.lap > m.horizon) this.done = true;
    return t;
  };

  /* simulate(): drive a whole race with a policy(lap, compound, age, sc, usedBoth, weather). */
  function simulate(model, policy, dice, startWeather) {
    var r = new Race(model, dice, startWeather);
    while (!r.done) { var s = r.state(); r.step(policy(s.lap, s.compound, s.age, s.sc, s.usedBoth, s.weather)); }
    return { time: r.total, actions: r.log.map(function (e) { return e.action; }), log: r.log, usedBoth: r.usedBoth };
  }

  var api = {
    STAY_OUT: STAY_OUT, PIT_A: PIT_A, PIT_B: PIT_B, A: A, B: B, DRY: DRY, WET: WET,
    ACTION_NAMES: ["STAY OUT", "BOX FOR A", "BOX FOR B"], COMPOUND_NAMES: ["A", "B"],
    CONST: C, RaceModel: RaceModel, Race: Race, simulate: simulate, drawDice: drawDice, rngFrom: rngFrom
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else { root.PitWall = root.PitWall || {}; for (var k in api) root.PitWall[k] = api[k]; }
})(this);
