/* Pit Wall, Duel mode engine (Phase 8): the pit-timing duel of labs/labkit/pitgame.py. Two equal
   cars, the follower 0.5 s behind, one stop each onto B on a lap from 2 to 18. Needs engine.js,
   duel.js and pitgame_data.js (in Node: pass the three in).

   The tyres are pitgame's DuelModel: 0.25 s (A) and 0.15 s (B) of wear per lap of age, a 0.3 s
   out-lap warm-up, B 0.3 s slower, no safety car. The follower's payoff is +1 for finishing ahead,
   -1 if not, plus 0.05 per second of final margin; the leader's is the negative.

   pitgame_data.js ships the two 17 x 17 payoff matrices from pitgame's cache, the 20 seeds' pass
   dice that made them (numpy's, so a race here is the race the labs ran), and the solutions the
   labs compute: fictitious play's equilibrium, the latest-only cycle and the plan's pool.
   labs/tools/pitwall_duel_game_export.py check recomputes both matrices here, race by race, from
   the dice, and compares them with the cache to 1e-9. */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) module.exports = factory;
  else factory(root.PitWall, root.PitWall.duel, root.PitWall.pitgameData);
})(this, function (PW, D, DATA) {
  "use strict";
  var C = PW.CONST, A = PW.A, B = PW.B, PIT_B = PW.PIT_B;
  var G = { START_GAP: 0.5, MARGIN_WEIGHT: 0.05, WEAR: [0.25, 0.15], WARMUP: 0.3, B_SLOWER: 0.3 };

  function DuelModel() {
    PW.RaceModel.call(this, { scHazard: 0.0 });
    this.wear = G.WEAR.slice(); this.warmup = G.WARMUP; this.bSlower = G.B_SLOWER;
  }
  DuelModel.prototype = Object.create(PW.RaceModel.prototype);
  DuelModel.prototype.constructor = DuelModel;
  DuelModel.prototype.lapCost = function (lap, compound, age) {
    var fuel = C.FUEL_PER_LAP * (this.horizon - lap);
    return C.BASE_LAP + (compound === B ? this.bSlower : 0.0) + this.wear[compound] * age + fuel + (age === 1 ? this.warmup : 0.0);
  };
  var MODEL = new DuelModel();
  var LAPS = DATA.laps, N = LAPS.length;

  /* One race on seed s (0 to 19) of the labs' dice: the follower stops on fLap, the leader on lLap. */
  function race(fLap, lLap, s, interaction) {
    var plan = {}; plan[fLap] = PIT_B;
    var script = {}; script[lLap] = PIT_B;
    return D.play(plan, { model: MODEL, rivalScript: script, rivalSlower: 0.0, startGap: G.START_GAP, interaction: interaction, dice: DATA.dice[s] });
  }
  function payoffOf(r) { return (r.finishedAhead ? 1.0 : -1.0) + G.MARGIN_WEIGHT * (r.rival - r.total); }
  function matrix(interaction) {
    var U = [];
    for (var i = 0; i < N; i++) {
      U.push([]);
      for (var j = 0; j < N; j++) {
        var s = 0;
        for (var k = 0; k < DATA.dice.length; k++) s += payoffOf(race(LAPS[i], LAPS[j], k, interaction));
        U[i].push(s / DATA.dice.length);
      }
    }
    return U;
  }

  function U(blocking) { return blocking ? DATA.on.U : DATA.off.U; }
  /* The follower's expected payoff for each lap against a leader mixture. */
  function rowValues(M, col) { return M.map(function (row) { return row.reduce(function (s, x, j) { return s + x * col[j]; }, 0); }); }
  /* The follower's payoff against each leader lap, when the follower plays a mixture. */
  function colValues(M, row) { return M[0].map(function (_, j) { return M.reduce(function (s, r, i) { return s + row[i] * r[j]; }, 0); }); }
  function argmax(v) { var b = 0; for (var i = 1; i < v.length; i++) if (v[i] > v[b]) b = i; return b; }
  function argmin(v) { var b = 0; for (var i = 1; i < v.length; i++) if (v[i] < v[b]) b = i; return b; }
  function pure(i) { var v = new Array(N).fill(0); v[i] = 1; return v; }
  function exploitability(M, row, col) { return Math.max.apply(null, rowValues(M, col)) - Math.min.apply(null, colValues(M, row)); }

  var api = { CONST: G, MODEL: MODEL, LAPS: LAPS, DATA: DATA, race: race, payoffOf: payoffOf, matrix: matrix, U: U,
    rowValues: rowValues, colValues: colValues, argmax: argmax, argmin: argmin, pure: pure, exploitability: exploitability };
  PW.pitgame = api;
  return api;
});
