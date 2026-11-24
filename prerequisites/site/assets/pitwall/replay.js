/* Pit Wall, Replay (Phase 5): race the DQN recorded in replay_policy.js. The record holds the
   network's greedy call on every dry state, so the policy runs here without the network.
   - act(state): the greedy call; q(state): the network's three Q-values, as seconds to the flag
   - expectedTime(model, eps): the exact expected race time of ε-greedy around the greedy call,
     where a random call is a uniform pick among the legal actions, the greedy one included
     (labs/tools/pitwall_replay_export.py computes the same in Python; `check` compares them)
   - race(model, dice, eps, explore): one race on the given dice; explore() gives the exploration
     draws, kept apart from the dice so ε on and off see the same safety cars
   - stats(model, eps): the expected random, changed and pointless calls per race, exact
   Needs engine.js, oracle.js and replay_policy.js. Works in the browser and in Node. */
(function (root) {
  "use strict";
  var node = typeof module !== "undefined" && module.exports;
  var PW = node ? require("./engine.js") : root.PitWall;
  var DATA = node ? require("./replay_policy.js") : root.PitWall && root.PitWall.replayData;
  if (!PW || !DATA) return;
  var A = PW.A, DRY = PW.DRY, RaceModel = PW.RaceModel, H = PW.CONST.HORIZON;

  function idx(lap, c, age, sc, used) { return ((((lap - 1) * 2 + c) * H + (age - 1)) * 2 + sc) * 2 + (used ? 1 : 0); }
  function act(s) { return +DATA.acts[idx(s.lap, s.compound, s.age, s.sc, s.usedBoth)]; }
  function q(s) { var i = 3 * idx(s.lap, s.compound, s.age, s.sc, s.usedBoth); return DATA.q.slice(i, i + 3); }
  function policy(lap, c, age, sc, used) { return +DATA.acts[idx(lap, c, age, sc, used)]; }

  function expectedTime(model, eps) {
    var V = {}, c, age, sc, used, lap;
    function k(lap, c, age, sc, used) { return lap + "," + c + "," + age + "," + sc + "," + (used ? 1 : 0); }
    for (c = 0; c < 2; c++) for (age = 1; age <= H + 1; age++) for (sc = 0; sc < 2; sc++)
      for (used = 0; used < 2; used++) V[k(H + 1, c, age, sc, used)] = 0.0;
    for (lap = H; lap >= 1; lap--)
      for (c = 0; c < 2; c++) for (age = 1; age <= lap; age++) for (sc = 0; sc < 2; sc++)
        for (used = 0; used < 2; used++) {
          var legal = model.legalActions(lap, c, DRY, !!used), g = policy(lap, c, age, sc, used);
          if (legal.indexOf(g) < 0) g = Math.min.apply(null, legal);
          var pSc = model.scProb(sc), total = 0.0;
          for (var i = 0; i < legal.length; i++) {
            var a = legal[i], p = eps / legal.length + (a === g ? 1.0 - eps : 0.0);
            var nt = RaceModel.nextTyre(c, age, a), nu = used || nt[0] !== c ? 1 : 0;
            var nxt = (1 - pSc) * V[k(lap + 1, nt[0], nt[1], 0, nu)] + pSc * V[k(lap + 1, nt[0], nt[1], 1, nu)];
            total += p * (model.cost(lap, c, age, a, DRY, sc) + nxt);
          }
          V[k(lap, c, age, sc, used)] = total;
        }
    return V[k(1, A, 1, 0, 0)];
  }

  /* Expected counts per race under ε-greedy, exact (a forward pass over the state distribution):
     randoms (the dice said explore), changed (the call differs from the greedy one) and pointless
     (a random pit stop where the greedy call was to stay out), and anyPointless, the chance a race
     has at least one. */
  function stats(model, eps) {
    var P = {}, out = { randoms: 0, changed: 0, pointless: 0, anyPointless: 0 };
    function k(c, age, sc, used, f) { return c + "," + age + "," + sc + "," + (used ? 1 : 0) + "," + f; }
    P[k(A, 1, 0, 0, 0)] = { c: A, age: 1, sc: 0, used: 0, f: 0, p: 1.0 };
    for (var lap = 1; lap <= H; lap++) {
      var N = {};
      for (var key in P) {
        var s = P[key], legal = model.legalActions(lap, s.c, DRY, !!s.used), g = policy(lap, s.c, s.age, s.sc, s.used);
        if (legal.indexOf(g) < 0) g = Math.min.apply(null, legal);
        var pSc = model.scProb(s.sc);
        out.randoms += s.p * eps;
        for (var i = 0; i < legal.length; i++) {
          var a = legal[i], pa = eps / legal.length + (a === g ? 1.0 - eps : 0.0);
          if (a !== g) out.changed += s.p * pa;
          var bad = a !== g && a !== PW.STAY_OUT && g === PW.STAY_OUT, nf = s.f || bad ? 1 : 0;
          if (bad) out.pointless += s.p * pa;
          var nt = RaceModel.nextTyre(s.c, s.age, a), nu = s.used || nt[0] !== s.c ? 1 : 0;
          for (var nsc = 0; nsc < 2; nsc++) {
            var q = s.p * pa * (nsc ? pSc : 1 - pSc), nk = k(nt[0], nt[1], nsc, nu, nf);
            if (!q) continue;
            if (!N[nk]) N[nk] = { c: nt[0], age: nt[1], sc: nsc, used: nu, f: nf, p: 0 };
            N[nk].p += q;
          }
        }
      }
      P = N;
    }
    for (var key2 in P) if (P[key2].f) out.anyPointless += P[key2].p;
    return out;
  }

  /* One race. Each log entry gains: greedy (the call with exploration off), random (the dice said
     explore) and pointless (the random pick was a pit stop the greedy call would not make). */
  function race(model, dice, eps, explore) {
    var r = new PW.Race(model, dice, DRY), randoms = 0, pointless = 0, changed = 0;
    while (!r.done) {
      var s = r.state(), g = act(s), a = g, rand = false;
      if (eps > 0 && explore() < eps) {
        var legal = model.legalActions(s.lap, s.compound, s.weather, s.usedBoth);
        a = legal[Math.min(legal.length - 1, Math.floor(explore() * legal.length))];
        rand = true; randoms++;
      }
      r.step(a);
      var e = r.log[r.log.length - 1];
      e.greedy = g; e.random = rand; e.pointless = rand && a !== PW.STAY_OUT && g === PW.STAY_OUT;
      if (a !== g) changed++;
      if (e.pointless) pointless++;
    }
    return { time: r.total, log: r.log, randoms: randoms, changed: changed, pointless: pointless };
  }

  var api = { meta: DATA.meta, act: act, q: q, policy: policy, expectedTime: expectedTime, stats: stats, race: race };
  if (node) module.exports = api;
  else root.PitWall.replay = api;
})(this);
