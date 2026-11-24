// Node half of pitwall_training_export.py check: every recorded plan, replayed by engine.js on the
// quiet race (no safety car, dry), must be the recorded gap away from oracle.js's optimum, to 1e-9.
"use strict";
const path = require("path");
const site = path.resolve(__dirname, "..", "..", "site", "assets", "pitwall");
const PW = require(path.join(site, "engine.js"));
const OR = require(path.join(site, "oracle.js"));
const D = require(path.join(site, "training_data.js"));

const model = new PW.RaceModel({ scHazard: 0.0 });
const opt = OR.solve(model).value({ lap: 1, compound: PW.A, age: 1, sc: 0, usedBoth: false, weather: PW.DRY });
if (Math.abs(opt - D.optimum) > 1e-9) { console.error("optimum mismatch", opt, D.optimum); process.exit(1); }
const dice = new Array(2 * model.horizon).fill(0.5);
let plans = 0, worst = 0, illegal = 0;
for (const [key, run] of Object.entries(D.runs)) {
  if (run.gap.length !== D.races / D.every + 1) { console.error("checkpoints", key, run.gap.length); process.exit(1); }
  run.plan.forEach(function (p, i) {
    const r = PW.simulate(model, function (lap) { return +p[lap - 1]; }, dice);
    if (r.log.some(function (e) { return e.illegal; })) illegal++;
    worst = Math.max(worst, Math.abs(r.time - opt - run.gap[i]));
    plans++;
  });
}
if (worst > 1e-9 || illegal) { console.error("TRAINING PARITY FAILED", plans, "plans, worst", worst, "illegal", illegal); process.exit(1); }
console.log("TRAINING PARITY OK (" + Object.keys(D.runs).length + " runs, " + plans + " plans replayed, worst difference " + worst.toExponential(1) + ")");
