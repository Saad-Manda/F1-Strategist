// Node half of labs/tools/pitwall_duel_game_export.py check: recomputes both payoff matrices with
// site/assets/pitwall/pitgame.js from the shipped dice, and the shipped equilibrium's exploitability.
"use strict";
const path = require("path");
const dir = path.join(__dirname, "..", "..", "site", "assets", "pitwall");
const PW = require(path.join(dir, "engine.js"));
const D = require(path.join(dir, "duel.js"))(PW);
const DATA = require(path.join(dir, "pitgame_data.js"));
const G = require(path.join(dir, "pitgame.js"))(PW, D, DATA);
const out = { on: G.matrix(true), off: G.matrix(false) };
for (const tag of ["on", "off"]) out["expl_" + tag] = G.exploitability(DATA[tag].U, DATA[tag].eq.f, DATA[tag].eq.l);
process.stdout.write(JSON.stringify(out));
