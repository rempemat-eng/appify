// Both tsx import paths must share the same simulated device storage.
const storageKey = Symbol.for('napattack.integration.storage');
const values = (globalThis[storageKey] ??= new Map());

module.exports = {
  async getItem(key) {
    return values.get(key) ?? null;
  },
  async setItem(key, value) {
    values.set(key, value);
  },
  async removeItem(key) {
    values.delete(key);
  },
  async clear() {
    values.clear();
  },
  async getAllKeys() {
    return [...values.keys()];
  },
};
