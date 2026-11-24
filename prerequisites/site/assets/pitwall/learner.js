/* Pit Wall learner: Phase 4's table learner on the toy race. It is the Phase 4 capstone's
   OffPolicyLearner (labs/solutions/phase4/p4_cap_toy_learners) with one change: the table is
   keyed by a binned state, so you can see what binning hides.

   The learner sees (laps-remaining bin, compound, tyre-age bin, sc, used both). Two binnings:
     "fine"    one bin per lap: the capstone's unbinned state.
     "coarse"  one bin per 5 laps, for laps remaining and for tyre age: the real plan's shape
               (12 laps-remaining bins, 10 tyre-age bins over an age of 0-50). Ages 5-9 share a
               bin, and tyre A's cliff (after age 6) and the best stop (age 8) are both inside it.
   Dry weather; the safety car is on unless the model turns it off.

   Training follows run_race() in the capstone: reward = -(lap time - offset), the Q-learning
   target takes a max over the next lap's legal actions, and epsilon decays linearly per update.
   The greedy policy is scored exactly by oracle.expectedTime, so its gap has no sampling noise.
   Works in the browser (window.PitWall.learner) and in Node (module.exports). */
(function (root) {
  "use strict";
  var node = typeof module !== "undefined" && module.exports;
  var PW = node ? require("./engine.js") : root.PitWall;
  var OR = node ? require("./oracle.js") : root.PitWall.oracle;
  var A = PW.A, DRY = PW.DRY, RaceModel = PW.RaceModel;

  var BIN_WIDTH = { fine: 1, coarse: 5 };
  var MAX_BIN = 64;  // room for any age or laps remaining in the toy race

  function width(bins) {
    var w = BIN_WIDTH[bins];
    if (!w) throw new Error('bins must be "fine" or "coarse"');
    return w;
  }
  function ageBin(age, bins) { return Math.floor(age / width(bins)); }
  /* Laps remaining after this one, binned the same way (the plan bins laps remaining, not laps). */
  function lapBin(lap, bins, horizon) { return Math.floor((horizon - lap) / width(bins)); }

  function Learner(opts) {
    opts = opts || {};
    this.bins = opts.bins || "coarse";
    this.w = width(this.bins);
    this.horizon = opts.horizon || PW.CONST.HORIZON;
    this.alpha = opts.alpha !== undefined ? opts.alpha : 0.1;
    this.epsStart = opts.epsStart !== undefined ? opts.epsStart : 1.0;
    this.epsEnd = opts.epsEnd !== undefined ? opts.epsEnd : 0.05;
    this.decaySteps = opts.decaySteps !== undefined ? opts.decaySteps : 120000;  // the first 6,000 races
    this.offset = opts.offset !== undefined ? opts.offset : PW.CONST.BASE_LAP;
    this.seed = opts.seed !== undefined ? opts.seed : 1;
    this.rng = PW.rngFrom(this.seed);
    this.epsilon = this.epsStart;
    this.steps = 0; this.races = 0;
    var cells = MAX_BIN * 2 * MAX_BIN * 2 * 2;
    this.table = new Float64Array(cells * 3);  // a cell never visited reads as [0, 0, 0]
    this.visits = new Int32Array(cells);
  }

  /* The cell a state falls in: one number. */
  Learner.prototype.key = function (lap, c, age, sc, used) {
    var lb = Math.floor((this.horizon - lap) / this.w), ab = Math.floor(age / this.w);
    return (((lb * 2 + c) * MAX_BIN + ab) * 2 + sc) * 2 + (used ? 1 : 0);
  };
  Learner.prototype.q = function (k) { return [this.table[3 * k], this.table[3 * k + 1], this.table[3 * k + 2]]; };

  /* epsilon-greedy over the legal actions; ties go to the lower action number. */
  Learner.prototype.act = function (k, legal, greedy) {
    if (!greedy && this.rng() < this.epsilon) return legal[Math.floor(this.rng() * legal.length)];
    var t = this.table, best = legal[0];
    for (var i = 1; i < legal.length; i++) if (t[3 * k + legal[i]] > t[3 * k + best]) best = legal[i];
    return best;
  };

  Learner.prototype.learn = function (k, a, reward, kNext, done, legalNext) {
    var t = this.table, target = reward;
    if (!done) {
      var m = -Infinity;
      for (var i = 0; i < legalNext.length; i++) m = Math.max(m, t[3 * kNext + legalNext[i]]);
      target += m;
    }
    t[3 * k + a] += this.alpha * (target - t[3 * k + a]);
    this.visits[k] += 1;
    this.steps += 1;
    this.epsilon = Math.max(this.epsEnd, this.epsStart - this.steps * (this.epsStart - this.epsEnd) / this.decaySteps);
  };

  /* One training race: the capstone's run_race() with train=True, dry weather. */
  Learner.prototype.trainRace = function (model) {
    var c = A, age = 1, sc = 0, used = false, total = 0, H = model.horizon;
    for (var lap = 1; lap <= H; lap++) {
      var k = this.key(lap, c, age, sc, used);
      var a = this.act(k, model.legalActions(lap, c, DRY, used), false);
      var t = model.cost(lap, c, age, a, DRY, sc);
      total += t;
      var nt = RaceModel.nextTyre(c, age, a), nUsed = used || nt[0] !== c;
      var nSc = this.rng() < model.scProb(sc) ? 1 : 0;
      this.learn(k, a, -(t - this.offset), this.key(lap + 1, nt[0], nt[1], nSc, nUsed), lap === H,
        model.legalActions(lap + 1, nt[0], DRY, nUsed));
      c = nt[0]; age = nt[1]; sc = nSc; used = nUsed;
    }
    this.races += 1;
    return total;
  };

  Learner.prototype.train = function (model, races) {
    var times = [];
    for (var i = 0; i < races; i++) times.push(this.trainRace(model));
    return times;
  };

  /* The table read as a policy(lap, compound, age, sc, usedBoth, weather). */
  Learner.prototype.policy = function (model) {
    var self = this;
    return function (lap, c, age, sc, used, w) {
      return self.act(self.key(lap, c, age, sc, used), model.legalActions(lap, c, w, used), true);
    };
  };

  /* The greedy policy's exact expected time, and its gap to the optimum (never negative). */
  Learner.prototype.score = function (model, sol) {
    var exp = OR.expectedTime(model, this.policy(model), DRY);
    var opt = sol.value({ lap: 1, compound: A, age: 1, sc: 0, usedBoth: false, weather: DRY });
    return { expected: exp, optimum: opt, gap: exp - opt };
  };

  /* A policy's race with no safety car: the plan it runs on a quiet day. Actions, one per lap. */
  function quietPlan(model, policy) {
    var c = A, age = 1, used = false, actions = [];
    for (var lap = 1; lap <= model.horizon; lap++) {
      var a = policy(lap, c, age, 0, used, DRY), nt = RaceModel.nextTyre(c, age, a);
      actions.push(a); used = used || nt[0] !== c; c = nt[0]; age = nt[1];
    }
    return actions;
  }
  Learner.prototype.quietPlan = function (model) { return quietPlan(model, this.policy(model)); };

  var api = { Learner: Learner, ageBin: ageBin, lapBin: lapBin, quietPlan: quietPlan, BIN_WIDTH: BIN_WIDTH };
  if (node) module.exports = api;
  else { root.PitWall = root.PitWall || {}; root.PitWall.learner = api; }
})(this);
