// One source for catalog generation and future lesson navigation.
// Routes on planned entries are reserved, not links to implemented lessons.
export async function loadLabRegistry() {
  const response = await fetch(new URL('./lab-registry.json', import.meta.url));
  if (!response.ok) throw new Error(`Could not load lab curriculum (${response.status}).`);
  const registry = await response.json();
  if (registry.schemaVersion !== 1 || !Array.isArray(registry.labs)) {
    throw new Error('Unsupported lab curriculum format.');
  }
  return registry;
}
