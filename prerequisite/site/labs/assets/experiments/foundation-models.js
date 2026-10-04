// Pure teaching models: shared by the widgets and independent numeric checks.
export function unit(value, name = 'probability') {
  if (!Number.isFinite(value) || value < 0 || value > 1) throw new Error(`${name} must be between 0 and 1.`);
  return value;
}
export function returns(rewards, gamma) {
  unit(gamma, 'Discount');
  let tail = 0;
  const result = [];
  for (let t = rewards.length - 1; t >= 0; t--) {
    if (!Number.isFinite(rewards[t])) throw new Error('Rewards must be finite.');
    tail = rewards[t] + gamma * tail;
    result.push(tail);
  }
  return result.reverse();
}
export function branchValues(gamma, viaProbability) {
  unit(gamma, 'Discount'); unit(viaProbability);
  const direct = 3, via = 1 + gamma * 4;
  return {direct, via, policy: (1 - viaProbability) * direct + viaProbability * via, optimal: Math.max(direct, via)};
}
export function backward(horizon, gamma) {
  if (!Number.isInteger(horizon) || horizon < 0 || horizon > 10) throw new Error('Horizon must be an integer from 0 to 10.');
  unit(gamma, 'Discount');
  const rows = [{h: 0, A: 0, B: 0, direct: null, via: null, action: 'No action'}];
  for (let h = 1; h <= horizon; h++) {
    const direct = 3, via = 1 + gamma * rows[h - 1].B;
    rows.push({h, A: Math.max(direct, via), B: 4, direct, via, action: via > direct ? 'VIA' : via < direct ? 'DIRECT' : 'DIRECT / VIA (tie)'});
  }
  return rows;
}
export function expectedValue(outcomes) {
  if (!Array.isArray(outcomes) || !outcomes.length) throw new Error('Supply at least one outcome.');
  const total = outcomes.reduce((sum, [probability, reward]) => {
    unit(probability);
    if (!Number.isFinite(reward)) throw new Error('Rewards must be finite.');
    return sum + probability;
  }, 0);
  if (Math.abs(total - 1) > 1e-10) throw new Error('Probabilities must sum to 1; the row is not silently normalized.');
  return outcomes.reduce((sum, [probability, reward]) => sum + probability * reward, 0);
}
export const WEATHER = [[0.8, 0.2], [0.3, 0.7]];
export function advance(distribution, matrix = WEATHER) {
  expectedValue(distribution.map(p => [p, 0]));
  if (matrix.length !== distribution.length || matrix.some(row => row.length !== distribution.length)) throw new Error('Matrix dimensions do not match.');
  matrix.forEach(row => expectedValue(row.map(p => [p, 0])));
  return distribution.map((_, j) => distribution.reduce((sum, p, i) => sum + p * matrix[i][j], 0));
}
export function randomGenerator(seed) {
  if (!Number.isInteger(seed) || seed < 0 || seed > 4294967295) throw new Error('Seed must be an integer from 0 to 4294967295.');
  let state = seed >>> 0;
  return () => { state = (Math.imul(1664525, state) + 1013904223) >>> 0; return state / 4294967296; };
}
export function sampleNext(state, random, matrix = WEATHER) {
  if (!Number.isInteger(state) || !matrix[state]) throw new Error('Unknown state.');
  expectedValue(matrix[state].map(p => [p, 0]));
  const draw = unit(random(), 'Random draw');
  if (draw >= 1) throw new Error('Random draw must be less than 1.');
  let sum = 0;
  for (let j = 0; j < matrix[state].length; j++) {
    sum += matrix[state][j];
    if (draw < sum) return j;
  }
  return matrix[state].length - 1;
}
export function switchStep(mode, action) {
  if (![0, 1].includes(mode) || !['FLIP', 'CLAIM'].includes(action)) throw new Error('Unknown mode or action.');
  return action === 'FLIP' ? {mode: 1 - mode, reward: 0, terminated: false} : {mode, reward: mode === 1 ? 1 : -1, terminated: true};
}
