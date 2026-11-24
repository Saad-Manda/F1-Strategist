/* Pit Wall oracle: the exact answers the Phase 3.5 capstone computes.
   - solve(model): backward induction over every state, the best policy on average (it does not
     know the future). Port of toyrace.solve: ties go to the lower action number.
   - hindsight(model, dice): the best race had you known the safety car and weather in advance.
   - foresight(model, dice): Oracle A, which knows this race's weather in advance but not the
     safety car. Solved exactly on the weather the dice produce, then played on the same dice.
   - expectedTime(model, policy): the exact expected time of a fixed policy (toyrace.expected_time).
   - decompose(sol, log): a race's time = V(start) + the cost of its calls + luck, lap by lap.
   Checked against Python by labs/tools/pitwall_parity.py. */
(function (root) {
  "use strict";
  var PW = typeof module !== "undefined" && module.exports ? require("./engine.js") : root.PitWall;
  var A = PW.A, B = PW.B, DRY = PW.DRY, WET = PW.WET, RaceModel = PW.RaceModel;

  function key(lap, c, age, sc, used, w) { return lap + "," + c + "," + age + "," + sc + "," + (used ? 1 : 0) + "," + w; }

  /* Returns { V, Q, policy, value(state), best(state), regret(state, action) }.
     Q[key] holds the expected total from this lap to the flag for each legal action. */
  function solve(model) {
    var H = model.horizon, V = {}, Q = {}, policy = {};
    var c, age, sc, used, w, lap;
    for (c = 0; c < 2; c++) for (age = 1; age <= H + 1; age++) for (sc = 0; sc < 2; sc++)
      for (used = 0; used < 2; used++) for (w = 0; w < 2; w++) V[key(H + 1, c, age, sc, used, w)] = 0.0;
    for (lap = H; lap >= 1; lap--) {
      for (c = 0; c < 2; c++) for (age = 1; age <= lap; age++) for (sc = 0; sc < 2; sc++)
        for (used = 0; used < 2; used++) for (w = 0; w < 2; w++) {
          var pSc = model.scProb(sc), pW = model.weatherProbs(lap, w), totals = {};
          var legal = model.legalActions(lap, c, w, !!used), bestA = -1, bestT = Infinity;
          for (var i = 0; i < legal.length; i++) {
            var a = legal[i], nt = RaceModel.nextTyre(c, age, a), nUsed = used || nt[0] !== c ? 1 : 0;
            var exp = 0.0;
            for (var nsc = 0; nsc < 2; nsc++) for (var nw = 0; nw < 2; nw++) {
              var p = (nsc ? pSc : 1 - pSc) * pW[nw];
              exp += p * V[key(lap + 1, nt[0], nt[1], nsc, nUsed, nw)];
            }
            var tot = model.cost(lap, c, age, a, w, sc) + exp;
            totals[a] = tot;
            if (tot < bestT || (tot === bestT && a < bestA)) { bestT = tot; bestA = a; }
          }
          var k = key(lap, c, age, sc, used, w);
          Q[k] = totals; policy[k] = bestA; V[k] = bestT;
        }
    }
    function kOf(s) { return key(s.lap, s.compound, s.age, s.sc, s.usedBoth, s.weather); }
    return {
      V: V, Q: Q, policy: policy,
      value: function (s) { return V[kOf(s)]; },
      best: function (s) { return policy[kOf(s)]; },
      regret: function (s, a) { var q = Q[kOf(s)]; return q[a] === undefined ? NaN : q[a] - V[kOf(s)]; },
      asPolicy: function () {
        return function (lap, c, age, sc, used, w) { return policy[key(lap, c, age, sc, used, w)]; };
      }
    };
  }

  /* The safety-car and weather sequence the dice produce. Neither depends on the pit calls. */
  function conditions(model, dice, startWeather) {
    var sc = [0], w = [startWeather === undefined ? DRY : startWeather];
    for (var lap = 1; lap < model.horizon; lap++) {
      sc.push(dice[2 * (lap - 1)] < model.scProb(sc[lap - 1]) ? 1 : 0);
      w.push(dice[2 * (lap - 1) + 1] < model.weatherProbs(lap, w[lap - 1])[WET] ? 1 : 0);
    }
    return { sc: sc, weather: w };
  }

  /* Perfect foresight: a deterministic backward pass with the conditions known. */
  function hindsight(model, dice, startWeather) {
    var H = model.horizon, cond = conditions(model, dice, startWeather), V = {}, P = {};
    function k(lap, c, age, used) { return lap + "," + c + "," + age + "," + (used ? 1 : 0); }
    var lap, c, age, used;
    for (c = 0; c < 2; c++) for (age = 1; age <= H + 1; age++) for (used = 0; used < 2; used++) V[k(H + 1, c, age, used)] = 0;
    for (lap = H; lap >= 1; lap--) {
      var sc = cond.sc[lap - 1], w = cond.weather[lap - 1];
      for (c = 0; c < 2; c++) for (age = 1; age <= lap; age++) for (used = 0; used < 2; used++) {
        var legal = model.legalActions(lap, c, w, !!used), bestA = -1, bestT = Infinity;
        for (var i = 0; i < legal.length; i++) {
          var a = legal[i], nt = RaceModel.nextTyre(c, age, a), nUsed = used || nt[0] !== c ? 1 : 0;
          var tot = model.cost(lap, c, age, a, w, sc) + V[k(lap + 1, nt[0], nt[1], nUsed)];
          if (tot < bestT || (tot === bestT && a < bestA)) { bestT = tot; bestA = a; }
        }
        V[k(lap, c, age, used)] = bestT; P[k(lap, c, age, used)] = bestA;
      }
    }
    var actions = [], st = { c: A, age: 1, used: 0 };
    for (lap = 1; lap <= H; lap++) {
      var a2 = P[k(lap, st.c, st.age, st.used)], nt2 = RaceModel.nextTyre(st.c, st.age, a2);
      actions.push(a2); st = { c: nt2[0], age: nt2[1], used: st.used || nt2[0] !== st.c ? 1 : 0 };
    }
    return { time: V[k(1, A, 1, 0)], actions: actions, conditions: cond };
  }

  function foresight(model, dice, startWeather) {
    var cond = conditions(model, dice, startWeather);
    var mA = new RaceModel({ horizon: model.horizon, pitLoss: model.pitLoss, scHazard: model.scHazard,
      scContinue: model.scContinue, weatherTrace: cond.weather });
    var solA = solve(mA), run = PW.simulate(mA, solA.asPolicy(), dice);
    return { time: run.time, log: run.log, actions: run.actions, value: solA.value({ lap: 1, compound: A, age: 1, sc: 0, usedBoth: false, weather: cond.weather[0] }), model: mA, sol: solA };
  }

  /* The backward pass with the action fixed by policy(lap, c, age, sc, used, w); an illegal action
     becomes the first legal one. No dice: the number has no sampling noise. */
  function expectedTime(model, policy, startWeather) {
    var H = model.horizon, V = {}, c, age, sc, used, w, lap;
    for (c = 0; c < 2; c++) for (age = 1; age <= H + 1; age++) for (sc = 0; sc < 2; sc++)
      for (used = 0; used < 2; used++) for (w = 0; w < 2; w++) V[key(H + 1, c, age, sc, used, w)] = 0.0;
    for (lap = H; lap >= 1; lap--)
      for (c = 0; c < 2; c++) for (age = 1; age <= lap; age++) for (sc = 0; sc < 2; sc++)
        for (used = 0; used < 2; used++) for (w = 0; w < 2; w++) {
          var legal = model.legalActions(lap, c, w, !!used), a = policy(lap, c, age, sc, !!used, w);
          if (legal.indexOf(a) < 0) a = Math.min.apply(null, legal);
          var nt = RaceModel.nextTyre(c, age, a), nUsed = used || nt[0] !== c ? 1 : 0;
          var pSc = model.scProb(sc), pW = model.weatherProbs(lap, w), exp = 0.0;
          for (var nsc = 0; nsc < 2; nsc++) for (var nw = 0; nw < 2; nw++)
            exp += (nsc ? pSc : 1 - pSc) * pW[nw] * V[key(lap + 1, nt[0], nt[1], nsc, nUsed, nw)];
          V[key(lap, c, age, sc, used, w)] = model.cost(lap, c, age, a, w, sc) + exp;
        }
    return V[key(1, A, 1, 0, 0, startWeather === undefined ? (model.weatherTrace ? model.weatherTrace[0] : DRY) : startWeather)];
  }

  /* Telescoping V along the race: time - V(start) = sum over laps of
       regret = Q(s, a) - V(s)                  what the call cost, on average (never negative)
       luck   = time(s, a) + V(s') - Q(s, a)    how the dice went against the average (either sign)
     with V after the flag = 0. */
  function decompose(sol, log) {
    var rows = [], regret = 0, luck = 0;
    for (var i = 0; i < log.length; i++) {
      var e = log[i], v = sol.value(e.state), q = sol.Q[key(e.state.lap, e.state.compound, e.state.age, e.state.sc, e.state.usedBoth, e.state.weather)][e.action];
      var vNext = i + 1 < log.length ? sol.value(log[i + 1].state) : 0;
      var r = { lap: e.state.lap, v: v, q: q, regret: q - v, luck: e.time + vNext - q };
      regret += r.regret; luck += r.luck; rows.push(r);
    }
    return { start: log.length ? sol.value(log[0].state) : 0, regret: regret, luck: luck, rows: rows };
  }

  var api = { solve: solve, hindsight: hindsight, conditions: conditions, foresight: foresight, expectedTime: expectedTime, decompose: decompose };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else { root.PitWall = root.PitWall || {}; root.PitWall.oracle = api; }
})(this);
