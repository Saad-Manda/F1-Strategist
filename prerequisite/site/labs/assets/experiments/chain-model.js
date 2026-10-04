// Live browser calculation of the same small model as the local Python exercise.
export function resetChain(cap = 6) {
  if (!Number.isInteger(cap) || cap < 1 || cap > 20) throw new Error('Choose a whole step limit from 1 to 20.');
  return { position: 0, steps: 0, total: 0, terminated: false, truncated: false, cap };
}
export function stepChain(state, action) {
  if (state.terminated || state.truncated) throw new Error('This episode has ended. Reset before another action.');
  if (action !== 0 && action !== 1) throw new Error('Choose LEFT or RIGHT.');
  const position = Math.max(0, Math.min(2, state.position + (action === 1 ? 1 : -1)));
  const reward = position === 2 ? 5 : -1;
  const steps = state.steps + 1;
  const terminated = position === 2;
  const truncated = !terminated && steps >= state.cap;
  return { ...state, position, steps, total: state.total + reward, reward, terminated, truncated };
}
export function seededActionGenerator(seed) {
  let value = seed >>> 0;
  return () => {
    value = (Math.imul(value, 1664525) + 1013904223) >>> 0;
    return value < 2147483648 ? 0 : 1;
  };
}
