/** Node-only bounded reference adapter; never imported by the Expo game. */
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import vm from 'node:vm';

const reference = JSON.parse(readFileSync(new URL('./original-modules.json', import.meta.url), 'utf8'));
const hash = (value) => createHash('sha256').update(value).digest('hex');
export const canonicalProvenance = reference.provenance;

/** Expose selected original private pure functions only for rule extraction/probes.
 * Original source remains intact in original-modules.json and is hash-verified. */
export function loadCanonicalCombat({ referenceHelpers = false } = {}) {
  if (hash(reference.catalogue) !== reference.provenance.catalogueSha256 || hash(reference.engine) !== reference.provenance.engineSha256) throw new Error('Canonical module hash mismatch');
  const modules = new Map();
  const load = (source, expected, expectedDependencies) => {
    let factory, id, dependencies;
    vm.runInNewContext(source, { __d: (f, i, d) => { factory = f; id = i; dependencies = d; } }, { timeout: 1000 });
    if (id !== expected || JSON.stringify(dependencies) !== JSON.stringify(expectedDependencies)) throw new Error('Unexpected reference module');
    const exports = {};
    factory({}, (key) => {
      if (!modules.has(key)) throw new Error(`Unexpected reference dependency ${key}`);
      return modules.get(key);
    }, null, null, { exports }, exports, dependencies);
    modules.set(id, exports);
    return exports;
  };
  load(reference.catalogue, 3501, []);
  let source = reference.engine;
  if (referenceHelpers) {
    const ending = '},3500,[3501]);';
    if (!source.endsWith(ending)) throw new Error('Reference extraction boundary changed');
    source = source.slice(0, -ending.length) + '_e.__reference={duration:R,releaseTime:D,primary:E,secondary:q,activateForm:M,endForm:X};' + ending;
  }
  return load(source, 3500, [3501]);
}
