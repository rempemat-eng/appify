'use strict';

// Reproducible exact schematic, not generated game art or a collision mask.
const fs = require('node:fs');
const path = require('node:path');
const read = (name) => JSON.parse(fs.readFileSync(path.join(__dirname, name), 'utf8'));
const base = read('topology.json'),
  extra = read('biome-extensions.json');
const zones = [...base.zones, ...extra.zones];
const links = [...base.connections, ...extra.connections];
const transport = read('transport-contract.json');
const panels = {
  valley: {
    x: 60,
    y: 160,
    minCol: -1,
    minRow: -3,
    title: 'Home valley + Frostline',
    color: '#e0eadc',
  },
  sunreach: {
    x: 470,
    y: 160,
    minCol: -1,
    minRow: -1,
    title: 'Sunreach / earlier proposal',
    color: '#efdfc8',
  },
  steam: {
    x: 470,
    y: 650,
    minCol: 0,
    minRow: 0,
    title: 'Cogsworth',
    color: '#e3e8de',
  },
  isles: {
    x: 760,
    y: 860,
    minCol: 0,
    minRow: 0,
    title: 'Tidebloom Isles',
    color: '#d3ece6',
  },
  neon: {
    x: 1110,
    y: 650,
    minCol: 0,
    minRow: 0,
    title: 'Neon Harbour',
    color: '#e0e1f0',
  },
  space: {
    x: 1120,
    y: 160,
    minCol: 0,
    minRow: 0,
    title: 'Halcyon',
    color: '#e0e7f2',
  },
  moon: {
    x: 1330,
    y: 160,
    minCol: 0,
    minRow: 0,
    title: 'Lumen',
    color: '#e9def2',
  },
  home: {
    x: 60,
    y: 1120,
    minCol: 0,
    minRow: 0,
    title: 'Hut interior',
    color: '#efe1cc',
  },
};
const scale = 0.25,
  w = 320 * scale,
  h = 576 * scale;
const escape = (text) => String(text).replaceAll('&', '&amp;').replaceAll('<', '&lt;');
const zoneMap = new Map(zones.map((zone) => [zone.id, zone]));
const box = (id) => {
  const z = zoneMap.get(id),
    p = panels[z.region];
  return { x: p.x + (z.col - p.minCol) * w, y: p.y + (z.row - p.minRow) * h };
};
const center = (id) => {
  const p = box(id);
  return [p.x + w / 2, p.y + h * 0.64];
};
const point = (endpoint) => {
  const p = box(endpoint.zone);
  return [p.x + endpoint.at[0] * scale, p.y + endpoint.at[1] * scale];
};
const modeOffsets = {
  train: [0, 0],
  carts: [12, 14],
  maglev: [18, 12],
  capsule: [20, -12],
  shuttle: [-5, -25],
};
const displayNames = {
  ridge: 'Ridge cabin',
  garden: 'Home garden',
  halt: 'Valley Halt',
  town: 'Crossroads',
  harbour: 'Driftwood',
  castle: 'Hearthold',
  junction: 'Cogsworth',
  station: 'Halcyon',
  lumen: 'Lumen',
  oasis: 'Palm oasis',
  gulch: 'Dust Gulch',
  basalt_pass: 'Basalt pass',
  lava_bridge: 'Bridge / fork',
  caldera: 'Caldera',
  springs: 'Cinder springs',
  neon: 'Neon quay',
  skyport: 'Skyport',
  home: 'Nap hut',
};
const parts = [
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1500 1430" role="img" aria-labelledby="title desc"><title id="title">Expanded NapAttack segment contract</title><desc id="desc">31 proposed segments with exact cardinal walk connections, a snowy upper circuit, a separate island circuit and one explicitly proposed sea link. No current game implementation claimed.</desc><rect width="1500" height="1430" fill="#f8f4e9"/><style>text{font-family:Arial,sans-serif;fill:#263b37}.label{font-size:11px;font-weight:700;text-anchor:middle}.sub{font-size:10px;text-anchor:middle;fill:#53665f}.panel{font-size:20px;font-weight:700}.note{font-size:14px}</style>',
  '<text x="40" y="43" font-size="29" font-weight="700">NAPATTACK / EXPANDED SEGMENT CONTRACT</text>',
  '<text x="40" y="75" class="note">Gold = walking; sleepers = rail; blue solid = maglev; blue dashes = lift/shuttle; teal dots = proposed sea link. Proposal only.</text>',
  '<text x="40" y="100" class="note">Circles = station/platform nodes. Different modes transfer through a forecourt, not a rail join. Dark borders outside gold ports stay closed.</text>',
];
for (const panel of Object.values(panels))
  parts.push(
    `<text class="panel" x="${panel.x}" y="${panel.y - 22}">${escape(panel.title)}</text>`,
  );
for (const zone of zones) {
  const p = box(zone.id),
    panel = panels[zone.region];
  const snow = extra.districts[0].zones.includes(zone.id);
  const words = (zone.name ?? displayNames[zone.id] ?? zone.id.replaceAll('_', ' ')).split(' ');
  const lines = [''];
  for (const word of words) {
    if ((lines.at(-1) + ' ' + word).trim().length > 12 && lines.at(-1)) lines.push(word);
    else lines[lines.length - 1] = (lines.at(-1) + ' ' + word).trim();
  }
  parts.push(
    `<rect x="${p.x}" y="${p.y}" width="${w}" height="${h}" fill="${snow ? '#e1edf2' : panel.color}" stroke="#56675d" stroke-width="2.5"/>`,
    ...lines.map(
      (line, i) =>
        `<text class="label" x="${p.x + w / 2}" y="${p.y + 24 + i * 13}">${escape(line)}</text>`,
    ),
    `<text class="sub" x="${p.x + w / 2}" y="${p.y + 62}">[${zone.col},${zone.row}] / tier ${zone.tier}</text>`,
  );
}
for (const link of links.filter((candidate) => candidate.kind === 'walk')) {
  for (const endpoint of [link.a, link.b]) {
    const p = box(endpoint.zone),
      middle = (link.span[0] + link.span[1]) / 2;
    const side = endpoint.side;
    const seam =
      side === 'north'
        ? [p.x + middle * scale, p.y]
        : side === 'south'
          ? [p.x + middle * scale, p.y + h]
          : side === 'west'
            ? [p.x, p.y + middle * scale]
            : [p.x + w, p.y + middle * scale];
    parts.push(
      `<path d="M${center(endpoint.zone).join(',')} L${seam.join(',')}" fill="none" stroke="#b68d46" stroke-width="2"/>`,
    );
    const r = link.span.map((n) => n * scale);
    const d = ['north', 'south'].includes(side)
      ? `M${p.x + r[0]},${seam[1]} H${p.x + r[1]}`
      : `M${seam[0]},${p.y + r[0]} V${p.y + r[1]}`;
    parts.push(`<path d="${d}" stroke="#e7b443" stroke-width="6"/>`);
  }
}
const routes = {
  'valley-cogsworth': [
    [390, 820],
    [390, 740],
  ],
  'cogsworth-gulch': [
    [560, 600],
    [560, 500],
  ],
  'gulch-caldera': [
    [650, 520],
    [750, 520],
  ],
  'cogsworth-neon': [
    [650, 600],
    [1220, 600],
  ],
  'neon-halcyon': [
    [1390, 790],
    [1390, 410],
    [1160, 410],
  ],
  'halcyon-lumen': [],
  'garden-hut': [
    [350, 750],
    [350, 1200],
  ],
  'harbour-isles': [
    [420, 1080],
    [620, 1210],
    [785, 1210],
  ],
};
for (const link of links.filter((candidate) => candidate.kind !== 'walk')) {
  const sea = link.kind === 'proposed-sea-link',
    door = link.kind === 'door';
  const offset = modeOffsets[link.vehicle] ?? [0, 0];
  const drawingPoint = (endpoint) => point(endpoint).map((n, i) => n + offset[i]);
  const pts = [drawingPoint(link.a), ...(routes[link.id] ?? []), drawingPoint(link.b)];
  const color = sea ? '#147f87' : door ? '#987e5c' : '#4a77a0';
  const rail = ['train', 'carts'].includes(link.vehicle);
  if (rail) {
    // A continuous dark bed, perpendicular sleepers and a continuous light rail pair.
    // No surface conversion or hidden gap between station endpoints.
    parts.push(
      `<polyline points="${pts.map((p) => p.join(',')).join(' ')}" fill="none" stroke="#535450" stroke-width="7" stroke-linejoin="round"/>`,
    );
    for (let segment = 1; segment < pts.length; segment += 1) {
      const [a, b] = [pts[segment - 1], pts[segment]],
        dx = b[0] - a[0],
        dy = b[1] - a[1];
      const length = Math.hypot(dx, dy);
      if (!length) continue;
      for (let distance = 5; distance < length; distance += 9) {
        const x = a[0] + (dx * distance) / length,
          y = a[1] + (dy * distance) / length;
        parts.push(
          `<path d="M${x - (dy * 5) / length},${y + (dx * 5) / length} L${x + (dy * 5) / length},${y - (dx * 5) / length}" stroke="#535450" stroke-width="2"/>`,
        );
      }
    }
    parts.push(
      `<polyline points="${pts.map((p) => p.join(',')).join(' ')}" fill="none" stroke="#f8f4e9" stroke-width="3" stroke-linejoin="round"/>`,
    );
  } else if (link.vehicle === 'maglev') {
    parts.push(
      `<polyline points="${pts.map((p) => p.join(',')).join(' ')}" fill="none" stroke="#557c9b" stroke-width="8" stroke-linejoin="round"/>`,
      `<polyline points="${pts.map((p) => p.join(',')).join(' ')}" fill="none" stroke="#c9e0eb" stroke-width="3" stroke-linejoin="round"/>`,
    );
  } else
    parts.push(
      `<polyline points="${pts.map((p) => p.join(',')).join(' ')}" fill="none" stroke="${color}" stroke-width="${sea ? 3.5 : 2}" stroke-dasharray="${sea || door ? '3 6' : '8 6'}"/>`,
    );
  if (link.kind === 'transit') {
    const network = transport.networks.find((n) => n.connectionIds.includes(link.id));
    for (const [index, stop] of link.serviceEndpoints.entries()) {
      const p = index === 0 ? pts[0] : pts.at(-1);
      parts.push(
        `<circle cx="${p[0]}" cy="${p[1]}" r="5" fill="#f8f4e9" stroke="#263b37" stroke-width="2"/>`,
      );
      if (network.terminals.some((terminal) => terminal.stop === stop)) {
        parts.push(`<rect x="${p[0] - 7}" y="${p[1] + 7}" width="14" height="3" fill="#263b37"/>`);
      }
    }
  }
  if (sea) {
    for (const p of [pts[0], pts.at(-1)]) {
      parts.push(
        `<rect x="${p[0] - 7}" y="${p[1] - 4}" width="14" height="8" fill="#147f87" stroke="#f8f4e9" stroke-width="1.5"/>`,
        `<text x="${p[0] - 8}" y="${p[1] + 19}" font-size="10" fill="#147f87">pier</text>`,
      );
    }
  }
  const labelAt =
    pts.length === 2
      ? [(pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2]
      : pts[Math.max(1, Math.floor(pts.length / 2))];
  parts.push(
    `<text x="${labelAt[0] + 5}" y="${labelAt[1] - 9}" font-size="12" fill="${color}">${sea ? 'PROPOSED SEA LINK / not in game' : door ? 'explicit hut door' : escape(link.vehicle)}</text>`,
  );
}
for (const interchange of transport.interchanges) {
  const stop = base.transitStops.find((candidate) => candidate.id === interchange.stop);
  const anchor = point(stop);
  const platforms = interchange.networks.map((id) => {
    const network = transport.networks.find((candidate) => candidate.id === id);
    return anchor.map((n, i) => n + modeOffsets[network.mode][i]);
  });
  parts.push(
    `<polyline points="${platforms.map((p) => p.join(',')).join(' ')}" fill="none" stroke="#74796d" stroke-width="2" stroke-dasharray="2 2"/>`,
  );
}
const closed = box('fir_hollow');
parts.push(
  `<path d="M${closed.x},${closed.y + h} H${closed.x + w}" stroke="#b35a51" stroke-width="5"/>`,
  '<text x="370" y="1240" class="note">31 segments / 8 physical regions / 28 walk seams / 5 walking circuits</text>',
  '<text x="370" y="1266" class="note">6 retained transit services + 1 separately proposed sea link; no new service implemented.</text>',
  '<text x="370" y="1290" class="note">Fir Hollow / Woodland: closed escarpment. Snowy circuit is optional beyond existing ridge cabin.</text>',
  '<text x="370" y="1316" class="note">No ocean footpath. Watercourses are not walking edges. All unlisted ports/corners stay visibly closed.</text>',
  '<text x="370" y="1342" class="note">Use JSON for exact local endpoints. Panel positions are atlas layout, not connected world coordinates.</text>',
  '<text x="370" y="1368" class="note">Earlier fire-country proposal differs from newer main; reconcile with Claude, do not overwrite.</text>',
  '</svg>',
);
const output = path.join(__dirname, 'biome-connections.svg');
fs.writeFileSync(output, parts.join('\n') + '\n');
console.log('Rendered biome-connections.svg from both proposal contracts.');
