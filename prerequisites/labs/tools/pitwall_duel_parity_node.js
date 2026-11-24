// Node half of labs/tools/pitwall_duel_parity.py: reads cases as JSON on stdin, plays each one
// with site/assets/pitwall/duel.js, and prints every lap's agent and rival totals as JSON.
"use strict";
const path = require("path");
const PW = require(path.join(__dirname, "..", "..", "site", "assets", "pitwall", "engine.js"));
const D = require(path.join(__dirname, "..", "..", "site", "assets", "pitwall", "duel.js"))(PW);
let input = "";
process.stdin.on("data", (c) => { input += c; });
process.stdin.on("end", () => {
  const cases = JSON.parse(input);
  const out = cases.map((c) => {
    const r = D.play(c.plan, { dice: c.dice, interaction: c.interaction, passing: c.passing, rivalLap: c.rivalLap });
    return { agent: r.log.map((e) => e.totals[0]), rival: r.log.map((e) => e.totals[1]), passes: r.log.filter((e) => e.passed).length };
  });
  process.stdout.write(JSON.stringify(out));
});
