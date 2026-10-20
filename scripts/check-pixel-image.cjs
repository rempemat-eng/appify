/** Adapter contract only: React, RN and Skia are substituted boundaries. This
 * checks sampling selection, Image geometry and the single-canvas composition;
 * it does not run Skia or establish device appearance, timing or memory. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

const root = path.join(__dirname, '..');
const element = (type, props) => ({ type, props });
function load(file, boundaries) {
  const destination = { exports: {} };
  const source = ts.transpileModule(fs.readFileSync(path.join(root, file), 'utf8'), {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
    },
  }).outputText;
  vm.runInNewContext(source, {
    module: destination,
    exports: destination.exports,
    require(id) {
      if (id === 'react/jsx-runtime') return { jsx: element, jsxs: element };
      assert.ok(id in boundaries, `Unexpected adapter dependency: ${id}`);
      return boundaries[id];
    },
  });
  return destination.exports;
}
const web = load('components/pixel-image.tsx', {
  'react-native': { Image: 'RNImage', View: 'RNView' },
});
let requested;
let decoded = { specimen: true };
const native = load('components/pixel-image.native.tsx', {
  '@shopify/react-native-skia': {
    Canvas: 'SkiaCanvas',
    Image: 'SkiaImage',
    FilterMode: { Nearest: 'nearest', Linear: 'linear' },
    MipmapMode: { None: 'none' },
    useImage(source, onError) {
      requested = { source, onError };
      return decoded;
    },
  },
});
const imageProps = { source: 17, x: -13.5, y: 2, width: 384, height: 384 };
const failures = [];
const onError = (error) => failures.push(error.message);
const baseline = web.PixelImage({ ...imageProps, onError });
assert.equal(baseline.type, 'RNImage');
assert.equal(baseline.props.source, 17);
assert.equal(baseline.props.resizeMode, 'stretch');
assert.equal(
  JSON.stringify(baseline.props.style),
  JSON.stringify({
    position: 'absolute',
    left: -13.5,
    top: 2,
    width: 384,
    height: 384,
  }),
);
baseline.props.onError({ nativeEvent: { error: 'specimen failed' } });
assert.deepEqual(failures, ['specimen failed']);
for (const nearest of [undefined, true, false]) {
  const node = native.PixelImage({ ...imageProps, onError, nearest });
  assert.equal(node.type, 'SkiaImage', 'an image is a draw node, not another canvas');
  assert.equal(node.props.image, decoded);
  assert.equal(node.props.sampling.filter, nearest === false ? 'linear' : 'nearest');
  assert.equal(node.props.sampling.mipmap, 'none');
  assert.equal(node.props.x, imageProps.x);
  assert.equal(node.props.width, imageProps.width);
  assert.equal(requested.source, imageProps.source);
  assert.equal(requested.onError, onError);
}
decoded = null;
assert.equal(native.PixelImage(imageProps).props.image, null, 'loading has no stale image');

const geometry = load('lib/native-pixels.ts', {});
function expand(node) {
  if (Array.isArray(node)) return node.flatMap(expand);
  if (!node || typeof node !== 'object') return [];
  if (typeof node.type === 'function') return expand(node.type(node.props));
  return [node, ...expand(node.props.children)];
}
for (const [adapter, surface, image] of [
  [web, 'RNView', 'RNImage'],
  [native, 'SkiaCanvas', 'SkiaImage'],
]) {
  const renderer = load('components/native-pixel-tiles.tsx', {
    '@/components/pixel-image': adapter,
    '@/lib/native-pixels': geometry,
  }).default;
  const tiles = Array.from({ length: 12 }, (_, i) => ({
    id: String(i),
    source: i,
    x: (i % 3) * 256,
    y: Math.floor(i / 3) * 256,
  }));
  const nodes = expand(
    renderer({
      tiles,
      camera: { x: 100, y: 128 },
      pixel: 4 / 3,
      dpr: 3,
      width: 402,
      height: 655,
      nearest: true,
      onError,
    }),
  );
  assert.equal(
    nodes.filter((n) => n.type === surface).length,
    1,
    'one surface for all mounted tiles',
  );
  assert.equal(nodes.filter((n) => n.type === image).length, 12);
  assert.equal(nodes[0].props.pointerEvents, 'none');
  assert.equal(nodes[0].props.style.width, 402);
  assert.equal(nodes[0].props.style.height, 655);
  if (surface === 'RNView') assert.equal(nodes[0].props.dataSet.pixel, 'true');
}
console.log(
  'PASS: pixel-image adapter preserves web Image geometry and native nearest/no-mipmap sampling with one surface per mounted set (substituted boundaries, not device results).',
);
