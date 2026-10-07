import {unit, randomGenerator} from './foundation-models.js?v=reading-20261006-r8';

export function legalIndices(values, legal) {
  if (!Array.isArray(values) || values.length !== legal.length || !values.every(Number.isFinite)) throw new Error('Finite values and a matching mask are required.');
  const indices = legal.flatMap((allowed, i) => allowed ? [i] : []);
  if (!indices.length) throw new Error('At least one action must be legal.');
  return indices;
}
export function tdUpdate(q, reward, nextValues, legal, alpha, gamma, terminated, truncated = false) {
  unit(alpha, 'Learning rate'); unit(gamma, 'Discount');
  if (!Number.isFinite(q) || !Number.isFinite(reward)) throw new Error('Q and reward must be finite.');
  const continuation = terminated ? 0 : Math.max(...legalIndices(nextValues, legal).map(i => nextValues[i]));
  const target = reward + gamma * continuation, error = target - q;
  return {target, error, value: q + alpha * error, terminated, truncated};
}
export function epsilonProbabilities(values, legal, epsilon) {
  unit(epsilon, 'Epsilon');
  const indices = legalIndices(values, legal), best = Math.max(...indices.map(i => values[i]));
  const ties = indices.filter(i => values[i] === best);
  return values.map((_, i) => legal[i] ? epsilon / indices.length + (ties.includes(i) ? (1 - epsilon) / ties.length : 0) : 0);
}
export function selectAction(values, legal, epsilon, rng) {
  const probabilities = epsilonProbabilities(values, legal, epsilon), draw = rng();
  if (!Number.isFinite(draw) || draw < 0 || draw >= 1) throw new Error('Random draw must be in [0,1).');
  let cumulative = 0;
  for (let i = 0; i < probabilities.length; i++) { cumulative += probabilities[i]; if (draw < cumulative) return i; }
  return probabilities.findLastIndex(p => p > 0);
}
export function sarsaTarget(qValues, action, reward = 0, gamma = 1) {
  unit(gamma, 'Discount');
  if (!Number.isInteger(action) || !Number.isFinite(qValues[action]) || !Number.isFinite(reward)) throw new Error('Supply a valid committed action and finite reward.');
  return reward + gamma * qValues[action];
}
export function binIndex(x, edges) {
  if (!Number.isFinite(x) || x < 0 || x > 1) throw new Error('Observation must be in [0,1].');
  if (edges.length < 2 || edges[0] !== 0 || edges.at(-1) !== 1 || edges.some((e, i) => !Number.isFinite(e) || (i > 0 && e <= edges[i - 1]))) throw new Error('Edges must strictly increase from 0 to 1.');
  return x === 1 ? edges.length - 2 : edges.findIndex((edge, i) => i < edges.length - 1 && x >= edge && x < edges[i + 1]);
}
export function tableSize(counts, actions = 2) {
  if (!counts.length || [...counts, actions].some(n => !Number.isInteger(n) || n < 1)) throw new Error('Bin counts and actions must be positive integers.');
  const states = counts.reduce((a, b) => a * b, 1), entries = states * actions;
  if (!Number.isSafeInteger(entries * 8)) throw new Error('Table is too large for exact counting.');
  return {states, entries, bytes: entries * 8};
}
export function representationCeiling(edges) {
  binIndex(0, edges);
  return edges.slice(0, -1).reduce((sum, lo, i) => {
    const hi = edges[i + 1];
    const left = Math.max(0, Math.min(hi, 0.5) - lo), right = Math.max(0, hi - Math.max(lo, 0.5));
    return sum + Math.max(left, right);
  }, 0);
}
const rngAt = (seed, offset) => randomGenerator((seed + offset) >>> 0);
function settings(episodes, epsilon, alpha, seed) {
  if (!Number.isInteger(episodes) || episodes < 1 || episodes > 5000) throw new Error('Training budget must be 1–5000 episodes.');
  unit(epsilon, 'Training epsilon'); unit(alpha, 'Learning rate'); randomGenerator(seed);
}
export function trainBandit(seed, episodes, epsilon, alpha = 0.1) {
  settings(episodes, epsilon, alpha, seed);
  const q = [0.6, 0.1, 99], mask = [true, true, false], visits = [0, 0, 0];
  const policy = rngAt(seed, 303), rewards = [rngAt(seed, 101), rngAt(seed, 202)];
  let total = 0;
  for (let t = 0; t < episodes; t++) {
    const a = selectAction(q, mask, epsilon, policy), reward = rewards[a]() < [0.4, 0.8][a] ? 1 : 0;
    visits[a]++; total += reward; q[a] += alpha * (reward - q[a]);
  }
  const evaluationPolicy = rngAt(seed, 606), evaluationRewards = [rngAt(seed, 404), rngAt(seed, 505)];
  let evalTotal = 0; const evalVisits = [0, 0, 0];
  for (let t = 0; t < 200; t++) { const a = selectAction(q, mask, 0, evaluationPolicy); evalVisits[a]++; evalTotal += evaluationRewards[a]() < [0.4, 0.8][a] ? 1 : 0; }
  return {q, visits, trainingMean: total / episodes, evaluationMean: evalTotal / 200, evalVisits, expectedGreedy: epsilonProbabilities(q, mask, 0).reduce((sum, p, a) => sum + p * [0.4, 0.8, 0][a], 0)};
}
export function trainShortcut(seed, episodes, epsilon, alpha, algorithm) {
  settings(episodes, epsilon, alpha, seed);
  if (!['q-learning', 'sarsa'].includes(algorithm)) throw new Error('Unknown algorithm.');
  const q = {START: [0, 0], RISK: [0, 0], SAFE: [0]}, policy = rngAt(seed, 303);
  let total = 0, slips = 0;
  for (let t = 0; t < episodes; t++) {
    const a = selectAction(q.START, [true, true], epsilon, policy), state = a === 0 ? 'RISK' : 'SAFE';
    const mask = q[state].map(() => true);
    // Select once, use it for the SARSA target, then execute precisely that action.
    const next = selectAction(q[state], mask, epsilon, policy);
    const target = algorithm === 'sarsa' ? q[state][next] : Math.max(...q[state]);
    q.START[a] += alpha * (target - q.START[a]);
    const reward = state === 'SAFE' ? 3 : next === 0 ? 6 : -10;
    if (reward === -10) slips++; total += reward;
    q[state][next] += alpha * (reward - q[state][next]);
  }
  const evaluationPolicy = rngAt(seed, 606); let evalTotal = 0;
  for (let t = 0; t < 200; t++) {
    const a = selectAction(q.START, [true, true], 0, evaluationPolicy);
    const next = selectAction(q[a === 0 ? 'RISK' : 'SAFE'], a === 0 ? [true, true] : [true], 0, evaluationPolicy);
    evalTotal += a === 1 ? 3 : next === 0 ? 6 : -10;
  }
  return {q, trainingMean: total / episodes, evaluationMean: evalTotal / 200, slips};
}
export function trainBins(seed, episodes, edges, epsilon = 0.2, alpha = 0.1) {
  settings(episodes, epsilon, alpha, seed); binIndex(0, edges);
  const q = edges.slice(1).map(() => [0, 0]), policy = rngAt(seed, 303), observations = rngAt(seed, 101);
  let total = 0;
  for (let t = 0; t < episodes; t++) {
    const x = observations(), b = binIndex(x, edges), a = selectAction(q[b], [true, true], epsilon, policy);
    const reward = a === (x < 0.5 ? 0 : 1) ? 1 : 0; total += reward; q[b][a] += alpha * (reward - q[b][a]);
  }
  let evalTotal = 0;
  // Fixed paired midpoint grid; tie values use their exact action probabilities.
  for (let i = 0; i < 1000; i++) { const x = (i + 0.5) / 1000, b = binIndex(x, edges); evalTotal += epsilonProbabilities(q[b], [true, true], 0)[x < 0.5 ? 0 : 1]; }
  return {q, trainingMean: total / episodes, evaluationMean: evalTotal / 1000, ceiling: representationCeiling(edges)};
}
