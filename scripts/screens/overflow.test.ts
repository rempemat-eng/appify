import assert from 'node:assert/strict';
import { runInNewContext } from 'node:vm';
import { screenOverflow } from './overflow';

let checks = 0;
const equal = (actual: unknown, expected: unknown, label: string) => {
  assert.deepEqual(actual, expected, label);
  checks++;
};
const destinations = [
  'LIBRARY',
  'MOUNTAIN',
  'PARK',
  "MOSS'S STALL",
  'SPARRING RING',
  'HOME GARDEN',
];
type Rail = {
  labels?: string[];
  overflowX?: string;
  overflowY?: string;
  scrollWidth?: number;
  clientWidth?: number;
  left?: number;
  visibility?: string;
};
function collect(
  screen: string,
  width: number,
  rails: Rail[],
  documentWidth = width,
  bodyWidth = width,
): string[] {
  const elements = rails.map((rail) => {
    const labels = rail.labels ?? [];
    const buttons = labels.map((label) => ({ getAttribute: () => label }));
    const left = rail.left ?? 16;
    const clientWidth = rail.clientWidth ?? width - 32;
    return {
      tagName: 'DIV',
      scrollWidth: rail.scrollWidth ?? 738,
      clientWidth,
      getAttribute: () => null,
      getBoundingClientRect: () => ({
        width: clientWidth,
        height: 44,
        left,
        right: left + clientWidth,
        top: 100,
        bottom: 144,
      }),
      style: {
        overflowX: rail.overflowX ?? 'auto',
        overflowY: rail.overflowY ?? 'hidden',
        visibility: rail.visibility ?? 'visible',
        display: 'block',
      },
      querySelectorAll: (selector: string) => {
        if (selector === '[role="button"]') return buttons;
        if (selector === '[role="button"][aria-label^="Preview "]')
          return buttons.filter((_, i) => labels[i].startsWith('Preview '));
        if (selector === '[role="button"][aria-label$="tap to select"]')
          return buttons.filter((_, i) => labels[i].endsWith('tap to select'));
        throw new Error('unreviewed DOM query: ' + selector);
      },
    };
  });
  // Execute the same serialized function as page.evaluate. The DOM measurements
  // are substituted: this checks diagnostics, not browser layout or visual quality.
  const result = runInNewContext('(' + screenOverflow.toString() + ')(current)', {
    current: screen,
    innerWidth: width,
    innerHeight: 640,
    document: {
      documentElement: { scrollWidth: documentWidth },
      body: { scrollWidth: bodyWidth },
      querySelectorAll: () => elements,
    },
    getComputedStyle: (element: { style: unknown }) => element.style,
  });
  return Array.from(result);
}
for (const width of [320, 402]) {
  const rail = { labels: destinations };
  const error = [`DIV: horizontal scroll 738 > ${width - 32}`];
  equal(collect('missions', width, [rail]), [], `${width}: current six-place rail is intentional`);
  equal(
    collect('missions', width, [
      { labels: destinations.map((s) => (s === 'MOUNTAIN' ? s + ' · LV 2' : s)) },
    ]),
    [],
    `${width}: level-gate suffix does not hide the same destination`,
  );
  for (const screen of ['garden', 'shop', 'companions', 'battle'])
    equal(collect(screen, width, [rail]), error, `${width}: not a rail exception on ${screen}`);
  for (const labels of [
    [],
    destinations.slice(1),
    [...destinations, 'EXTRA'],
    [...destinations.slice(0, -1), 'LIBRARY'],
    [...destinations.slice(0, -1), 'HOME GARDEN · NOT A GATE'],
  ])
    equal(
      collect('missions', width, [{ labels }]),
      error,
      `${width}: incomplete/unrelated rail fails`,
    );
  for (const overflowY of ['auto', 'scroll'])
    equal(
      collect('missions', width, [{ ...rail, overflowY }]),
      error,
      `${width}: a vertical sheet is never excused by its descendant labels`,
    );
  equal(
    collect('missions', width, [rail, {}]),
    error,
    `${width}: an allowed rail cannot hide a separate overflowing element`,
  );
  equal(
    collect('missions', width, [rail], width + 10),
    [`Document width ${width + 10} > viewport ${width}`],
    `${width}: document overflow still fails`,
  );
  equal(
    collect('missions', width, [rail], width, width + 20),
    [`Document width ${width + 20} > viewport ${width}`],
    `${width}: body overflow still fails`,
  );
  equal(
    collect('missions', width, [{ scrollWidth: width - 32 }]),
    [],
    'fitting content stays valid',
  );
  equal(collect('missions', width, [{ visibility: 'hidden' }]), [], 'hidden art is not measured');
  equal(collect('missions', width, [{ left: width + 1 }]), [], 'off-screen art is not measured');
}
equal(
  collect('companions', 320, [{ labels: ['Preview A', 'Preview B'] }]),
  [],
  'companion rail retained',
);
equal(collect('battle', 320, [{ labels: ['Card, tap to select'] }]), [], 'battle hand retained');
equal(
  collect('missions', 320, [{ labels: ['Preview A', 'Preview B'] }]),
  ['DIV: horizontal scroll 738 > 288'],
  'companion labels never exempt an unrelated Missions rail',
);
console.log(
  `Screen overflow diagnostics: ${checks} checks passed (substituted DOM, not browser layout).`,
);
