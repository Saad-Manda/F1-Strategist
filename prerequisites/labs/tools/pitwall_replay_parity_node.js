// Node half of pitwall_replay_export.py check: the exact expected times replay.js computes.
"use strict";
const path = require("path");
const site = path.resolve(__dirname, "..", "..", "site", "assets", "pitwall");
const PW = require(path.join(site, "engine.js"));
const OR = require(path.join(site, "oracle.js"));
const R = require(path.join(site, "replay.js"));

const model = new PW.RaceModel();
const sol = OR.solve(model);
const out = { optimum: sol.value({ lap: 1, compound: PW.A, age: 1, sc: 0, usedBoth: false, weather: PW.DRY }), expected: {}, stats: {} };
for (const e of [0.0, 0.01, 0.05, 0.1, 0.2]) {
  const k = e === 0 ? "0.0" : String(e);
  out.expected[k] = R.expectedTime(model, e);
  out.stats[k] = R.stats(model, e);
}
// the greedy table, scored by the oracle's own fixed-policy evaluation, must agree with ε = 0
const greedy = OR.expectedTime(model, R.policy, PW.DRY);
if (Math.abs(greedy - out.expected["0.0"]) > 1e-9) { console.error("greedy mismatch", greedy, out.expected["0.0"]); process.exit(1); }
process.stdout.write(JSON.stringify(out));
