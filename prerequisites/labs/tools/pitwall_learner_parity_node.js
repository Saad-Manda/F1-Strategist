// Node half of pitwall_learner_parity.py: reads the cases on stdin, trains learner.js, prints results.
"use strict";
const path = require("path");
const site = path.resolve(__dirname, "..", "..", "site", "assets", "pitwall");
const PW = require(path.join(site, "engine.js"));
const OR = require(path.join(site, "oracle.js"));
const L = require(path.join(site, "learner.js"));

let input = "";
process.stdin.on("data", (d) => (input += d));
process.stdin.on("end", () => {
  const spec = JSON.parse(input);
  const model = new PW.RaceModel();
  const out = {};
  for (const bins of spec.bins) {
    for (const seed of spec.seeds) {
      const l = new L.Learner({ bins, seed, decaySteps: spec.decay });
      const times = l.train(model, spec.races);
      const table = {};
      for (let k = 0; k < l.visits.length; k++) if (l.visits[k]) table[k] = l.q(k);
      out[bins + "/" + seed] = {
        times, table, epsilon: l.epsilon, steps: l.steps,
        expected: OR.expectedTime(model, l.policy(model), PW.DRY),
      };
    }
  }
  process.stdout.write(JSON.stringify(out));
});
