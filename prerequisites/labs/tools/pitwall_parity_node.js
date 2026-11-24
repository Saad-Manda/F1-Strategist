// Node half of pitwall_parity.py: reads the cases on stdin, runs the Pit Wall engine, prints results.
"use strict";
const path = require("path");
const site = path.resolve(__dirname, "..", "..", "site", "assets", "pitwall");
const PW = require(path.join(site, "engine.js"));
const OR = require(path.join(site, "oracle.js"));

let input = "";
process.stdin.on("data", (d) => (input += d));
process.stdin.on("end", () => {
  const cases = JSON.parse(input);
  const out = {};
  for (const [name, spec] of Object.entries(cases)) {
    const model = new PW.RaceModel(spec.model);
    const sol = OR.solve(model);
    const scripts = {
      oracle: sol.asPolicy(),
      b_on_8: (lap) => (lap === 8 ? PW.PIT_B : PW.STAY_OUT),
      b_then_a: (lap) => (lap === 6 ? PW.PIT_B : lap === 13 ? PW.PIT_A : PW.STAY_OUT),
    };
    const races = spec.dice.map((dice) => {
      const r = {};
      for (const [pname, pol] of Object.entries(scripts)) {
        const res = PW.simulate(model, pol, dice);
        r[pname] = { time: res.time, laps: res.log.map((e) => e.time), actions: res.actions };
      }
      r.hindsight = OR.hindsight(model, dice).time;
      return r;
    });
    out[name] = { V: sol.V, policy: sol.policy, races, expected_b_on_8: OR.expectedTime(model, scripts.b_on_8) };
  }
  process.stdout.write(JSON.stringify(out));
});
