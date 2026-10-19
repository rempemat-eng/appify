import assert from "node:assert/strict";
import { moveTo, restoreWorld } from "./world-save";
import { hiddenBehind } from "./occlusion";
import {
  checkDecor,
  foundKeepsakes,
  keepsakes,
  newKeepsakes,
  restoreDecor,
} from "./decor";
import { decorSizes } from "./decor-sizes";
import { regionWalk, TILE } from "./region-walk";
import {
  GARDEN_YARD,
  doors,
  exitWalk,
  exits,
  inGardenYard,
  missionPlaces,
  passAt,
  regionPasses,
  regionPoint,
  rings,
  travelPoints,
  travelRoute,
  travelVehicle,
  stopsIn,
} from "./world-places";
import {
  HUT_DOOR,
  atGardenExit,
  gardenExitToward,
  makeWalkGrid,
} from "./garden-path";
import { regionTiles, tileAt, tileOrigin } from "./region-walk";
import { regionBounds } from "./region-walk";
import { readSave, writeSave } from "./save-data";
import { residentLines, residentRoutes } from "./resident-routes";
import { zoneMaps, zoneWindows } from "./zone-maps";

let checks = 0;
const ok = (value: unknown, message: string) => {
  assert.ok(value, message);
  checks++;
};

// restoring: only a whole spot inside its region survives
ok(restoreWorld(null) === null, "no spot stays none");
ok(
  restoreWorld({ region: "nowhere", x: 1, y: 1 }) === null,
  "an unknown region is dropped",
);
ok(
  restoreWorld({ region: "valley", x: -5, y: 10 }) === null,
  "a spot outside its region is dropped",
);
ok(
  restoreWorld({ region: "valley", x: Number.NaN, y: 10 }) === null,
  "a broken number is dropped",
);
{
  // 18 Oct: the valley's old castle corner is the Headland now, and the castle is in the
  // Ember Lands as 'hearthold'. An old visit inks the Headland, never the far castle.
  const old = restoreWorld({
    region: "valley",
    x: 480,
    y: 900,
    visited: ["castle", "harbour"],
  });
  ok(
    old?.visited.includes("headland") === true &&
      old.visited.includes("harbour"),
    "a saved visit to the old castle corner is a visit to the Headland",
  );
  ok(
    old?.visited.includes("hearthold") === false &&
      !old.visited.includes("castle"),
    "an old castle visit never inks the castle in the Ember Lands",
  );
  const both = restoreWorld({
    region: "valley",
    x: 480,
    y: 900,
    visited: ["castle", "headland"],
  });
  ok(
    both?.visited.filter((z) => z === "headland").length === 1,
    "the Headland is listed once",
  );
}
const good = restoreWorld({
  region: "valley",
  x: 480,
  y: 900,
  visited: ["town", "town", "atlantis", 4],
});
ok(good && good.region === "valley" && good.x === 480, "a good spot is kept");
ok(good && good.visited.join() === "town", "visited keeps known zones once");
ok(
  restoreWorld({ region: "west", x: 10, y: 10 })?.visited.length === 0,
  "visited defaults to none",
);

// moving records the zone underfoot once
const a = moveTo(null, "valley", 480, 1200);
ok(a.visited.length === 1, "the first zone is seen");
const b = moveTo(a, "valley", 490, 1210);
ok(b.visited.length === 1, "the same zone is not added twice");

// the save keeps the spot, and an old save without one loads as none
const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const restore = (v: unknown) => {
  if (isRecord(v)) v.world = restoreWorld(v.world);
  return v;
};
const worldOf = (data: unknown) => (isRecord(data) ? data.world : undefined);
const raw = writeSave({ world: a }, null).raw;
const back = { world: worldOf(readSave(raw, restore).data) };
ok(
  JSON.stringify(back.world) === JSON.stringify(a),
  "the spot round-trips through the save",
);
const old = {
  world: worldOf(readSave(JSON.stringify({ saveVersion: 1 }), restore).data),
};
ok(old.world === null, "a save from before the world loads with no spot");

// every place, station, door and exit is open ground reachable in its region
const places = [
  ...Object.entries(missionPlaces).map(
    ([k, p]) => [`mission ${k}`, p] as const,
  ),
  ...Object.entries(travelPoints).map(([k, p]) => [`station ${k}`, p] as const),
  ...Object.entries(doors).map(([k, p]) => [`door ${k}`, p] as const),
  ...Object.entries(exits).map(([k, p]) => [`exit ${k}`, p] as const),
  ...rings.map((p, i) => [`ring ${i}`, p] as const),
];
for (const [name, place] of places) {
  const at = regionPoint(place);
  const rows = regionWalk(place.region);
  const grid = makeWalkGrid(rows, {
    cell: TILE.cell,
    width: regionBounds(place.region).width,
    start: at,
  });
  const c = grid.toCell(at);
  ok(grid.walkable(c.cx, c.cy), `${name} stands on open ground`);
  // reachable from the region's travel point (the valley: from the gate exit)
  const from =
    place.region === "home"
      ? regionPoint(doors.inside)
      : place.region === "valley"
        ? regionPoint(exits.gate)
        : regionPoint(travelPoints[stopsIn(place.region)[0]]);
  if (Math.hypot(from.x - at.x, from.y - at.y) < TILE.cell) continue;
  const path = grid.findPath(from, at);
  ok(path.length > 0, `${name} can be walked to`);
  const end = path[path.length - 1];
  ok(
    Math.hypot(end.x - at.x, end.y - at.y) < 12,
    `${name}: the walk ends there`,
  );
}

// Walking out of the garden screen (and back): each exit is asked for only past its
// own gap, stands at it, starts at the same spot in the valley's garden and walks on
// into the right neighbour; arriving back inside the yard is home again.
ok(
  gardenExitToward({ x: 160, y: 560 }) === "gate",
  "a tap past the gate asks for the gate",
);
ok(
  gardenExitToward({ x: 60, y: 560 }) === null,
  "a tap past the fence asks for nothing",
);
ok(
  gardenExitToward({ x: 204, y: 20 }) === "trail",
  "a tap past the trail asks for the trail",
);
ok(
  gardenExitToward({ x: 60, y: 20 }) === null,
  "the forest above the clearing is no exit",
);
ok(
  gardenExitToward({ x: 4, y: 300 }) === "west",
  "the meadow’s west side leads out",
);
ok(
  gardenExitToward({ x: 316, y: 300 }) === "east",
  "the meadow’s east side leads out",
);
ok(
  gardenExitToward({ x: 160, y: 300 }) === null,
  "the middle of the garden is no exit",
);
ok(
  gardenExitToward({ x: Number.NaN, y: 300 }) === null,
  "a bad point asks for nothing",
);
ok(
  atGardenExit("gate", { x: 162, y: 522 }),
  "the gate hotspot stands at the gate",
);
ok(!atGardenExit("gate", { x: 60, y: 522 }), "the fence beside it does not");
const valley = makeWalkGrid(regionWalk("valley"), {
  cell: TILE.cell,
  width: regionBounds("valley").width,
  start: regionPoint(exits.gate),
});
const gardenTile = regionTiles("valley").find((t) => t.id === "garden")!;
const g0 = tileOrigin("valley", gardenTile);
const neighbour = {
  gate: "town",
  trail: "ridge",
  west: "woodland",
  east: "riverside",
} as const;
for (const [exit, gx, gy] of [
  ["gate", 162, 522],
  ["trail", 198, 50],
  ["west", 18, 400],
  ["east", 302, 250],
] as const) {
  const walk = exitWalk(exit, gx, gy);
  ok(
    walk.start.x === g0.x + gx && walk.start.y === g0.y + gy,
    `${exit}: starts where it left`,
  );
  ok(
    inGardenYard("valley", walk.start),
    `${exit}: that spot is in the garden's yard`,
  );
  const path = valley.findPath(walk.start, walk.goal);
  const end = path[path.length - 1];
  ok(
    end && tileAt("valley", end.x, end.y)?.id === neighbour[exit],
    `${exit}: walks on into the ${neighbour[exit]}`,
  );
  ok(
    end && !inGardenYard("valley", end),
    `${exit}: and out of the yard, so walking back is going home`,
  );
}
ok(!inGardenYard("steam", g0), "only the valley has the garden");
ok(
  inGardenYard("valley", {
    x: g0.x + GARDEN_YARD.minX,
    y: g0.y + GARDEN_YARD.maxY,
  }) !== null,
  "the yard includes its edges",
);
ok(
  doors.hut.at[0] === HUT_DOOR.x && doors.hut.at[1] === HUT_DOOR.y,
  "the world and the garden agree where the hut door is",
);
// the pass from the desert into the Ember Lands: both ends open and reachable, and
// each leads to the other, walking on inward
for (const { a: endA, b: endB } of regionPasses) {
  for (const [here, there] of [
    [endA, endB],
    [endB, endA],
  ] as const) {
    const at = regionPoint(here);
    const grid = makeWalkGrid(regionWalk(here.region), {
      cell: TILE.cell,
      width: regionBounds(here.region).width,
      start: at,
    });
    const c = grid.toCell(at);
    ok(
      grid.walkable(c.cx, c.cy),
      `the pass in ${here.zone} stands on open ground`,
    );
    const from =
      here.region === "west"
        ? regionPoint(travelPoints.west)
        : regionPoint(travelPoints.lava);
    // (from the lava station at the caldera's tunnel it is a long walk: through the
    // castle and over both its bridges, down the Scorched Pass)
    ok(
      grid.findPath(from, at).length > 0,
      `${here.zone}: the station walks to the pass`,
    );
    const p = passAt(here.region, at);
    ok(
      p && p.region === there.region,
      `the pass in ${here.zone} leads to ${there.zone}`,
    );
  }
}
ok(
  passAt("west", regionPoint(travelPoints.west)) === null,
  "the station is no pass",
);
console.log(`World save and places: ${checks} checks passed.`);

// every resident has something to say when the companion stops beside them
for (const who of Object.keys(residentRoutes))
  ok(residentLines[who], `${who} has a line`);
console.log(
  `Residents: ${Object.keys(residentRoutes).length} have a line each.`,
);

// lit windows: every pane sits inside the sprite it belongs to, wherever that sprite stands
let panes = 0;
for (const zone of Object.values(zoneMaps)) {
  for (const [id, sprite, , , w, h] of zone.objects) {
    for (const [x, y, pw, ph] of zoneWindows[sprite] ?? []) {
      ok(
        x >= 0 && y >= 0 && x + pw <= w && y + ph <= h && pw > 0 && ph > 0,
        `${id}: a pane inside ${sprite}`,
      );
      panes++;
    }
  }
}
ok(panes > 20, "the valley houses have lit windows");
console.log(`Lit windows: ${panes} panes inside their buildings.`);

// travel follows the lines: every station reaches every other, neighbours in one leg
const stations = [
  "valley",
  "steam",
  "west",
  "lava",
  "neon",
  "space",
  "moon",
] as const;
for (const from of stations)
  for (const to of stations) {
    if (from === to) continue;
    const route = travelRoute(from, to);
    ok(
      route.length > 0 && route[route.length - 1] === to,
      `${from} reaches ${to}`,
    );
    ok(
      route.every((r) => travelPoints[r]),
      `${from} to ${to} stops only at stations`,
    );
  }
ok(
  travelRoute("valley", "steam").join() === "steam",
  "the valley train goes to Cogsworth",
);
ok(
  travelRoute("valley", "moon").join() === "steam,neon,space,moon",
  "Lumen is four legs from the valley",
);
ok(
  travelRoute("lava", "neon").join() === "west,steam,neon",
  "the caldera to the city changes twice",
);
ok(travelRoute("valley", "valley").length === 0, "no trip to where you are");
console.log("Travel: every station reaches every other along the lines.");
ok(travelVehicle("steam", "neon") === "maglev", "the maglev runs to the city");
ok(
  travelVehicle("lava", "west") === "carts",
  "the mine carts run to the caldera",
);
ok(travelVehicle("space", "moon") === "shuttle", "the shuttle flies to Lumen");
ok(
  travelVehicle("valley", "steam") === "train",
  "the valley train is a steam train",
);

// The companion's outline shows through a building or a big tree in front of it, never
// through what it stands in front of (lib/occlusion.ts).
{
  const house = { x: 100, y: 100, w: 60, h: 50, z: 150 };
  ok(
    hiddenBehind([house], { x: 130, y: 140 }),
    "behind a house the outline shows",
  );
  ok(
    !hiddenBehind([house], { x: 130, y: 170 }),
    "in front of the house it does not",
  );
  ok(
    !hiddenBehind([house], { x: 220, y: 140 }),
    "beside the house it does not",
  );
  ok(
    !hiddenBehind([{ x: 120, y: 136, w: 20, h: 6, z: 142 }], {
      x: 130,
      y: 140,
    }),
    "a low fence across the feet does not count as hiding",
  );
}
console.log(
  "Occlusion: the outline shows only behind what hides the companion.",
);

// Keepsakes (C12): collect once, place freely, never cut the room off (lib/decor.ts).
{
  ok(
    foundKeepsakes([]).join() === "fern_pot,stool,rag_rug",
    "the hut starts with its own three keepsakes",
  );
  ok(
    foundKeepsakes(["headland"]).includes("shell_bowl"),
    "the Headland leaves the shell bowl",
  );
  ok(
    newKeepsakes(["town"], "hearthold").join() === "dragon_plush",
    "walking into Hearthold finds the dragon plush, once",
  );
  ok(
    newKeepsakes(["hearthold"], "hearthold").length === 0,
    "a place walked again finds nothing",
  );
  ok(
    keepsakes.every((k) => decorSizes[k.id]) &&
      Object.keys(decorSizes).length === keepsakes.length,
    "every keepsake has its drawing and every drawing a keepsake",
  );
  ok(
    checkDecor("hut", [], "stool", 160, 380).ok,
    "a stool stands on open floor",
  );
  ok(!checkDecor("hut", [], "stool", 160, 20).ok, "not in the wall");
  const door = zoneMaps.home.stands.door;
  const atDoor = checkDecor("hut", [], "stool", door[0], door[1] + 2);
  ok(
    !atDoor.ok && atDoor.why === "spot",
    "not where the companion stands at the door",
  );
  ok(checkDecor("hut", [], "rag_rug", 160, 380).ok, "a rug lies on open floor");
  ok(
    checkDecor("hut", [{ item: "rag_rug", x: 160, y: 380 }], "stool", 160, 372)
      .ok,
    "a stool may stand on the rug",
  );
  ok(
    !checkDecor("hut", [{ item: "stool", x: 160, y: 380 }], "cairn", 160, 380)
      .ok,
    "two keepsakes never share a spot",
  );
  ok(
    checkDecor("hut", [{ item: "stool", x: 160, y: 380 }], "stool", 120, 380)
      .ok,
    "moving a keepsake ignores where it stood",
  );
  // a doorway half filled: the keepsake that would close it is refused
  const half = [
    { item: "stool", x: 144, y: 404 },
    { item: "cairn", x: 160, y: 404 },
  ];
  ok(
    half.every(
      (p, i) => checkDecor("hut", half.slice(0, i), p.item, p.x, p.y).ok,
    ),
    "two keepsakes may stand in the doorway",
  );
  const closing = [168, 172, 176, 180].map((x) =>
    checkDecor("hut", half, "cog_clock", x, 404),
  );
  ok(
    closing.some((c) => !c.ok && c.why === "cut-off"),
    "the one that would close the doorway is refused for cutting the room off",
  );
  let allowed = 0;
  for (let y = 8; y < 576; y += 8)
    for (let x = 8; x < 320; x += 8)
      if (checkDecor("hut", [], "cog_clock", x, y).ok) allowed++;
  ok(allowed > 300, "most of the floor is free for keepsakes");
  const restored = restoreDecor(
    [
      { item: "stool", x: 160, y: 380 },
      { item: "stool", x: 120, y: 380 },
      { item: "dragon_plush", x: 100, y: 380 },
      { item: "cairn", x: 160, y: 20 },
      { item: "nothing", x: 1, y: 1 },
      "junk",
    ],
    [],
  );
  ok(
    restored.length === 1 &&
      restored[0].item === "stool" &&
      restored[0].x === 160,
    "a save keeps one of each found keepsake where it may stand; the rest wait in the chest",
  );
}
{
  // ... and out in the garden, by the same rules against the garden's own walk
  ok(
    checkDecor("garden", [], "stool", 60, 340).ok,
    "a stool stands in the open garden",
  );
  const nap = checkDecor("garden", [], "cairn", 143, 128);
  ok(!nap.ok && nap.why === "spot", "not on the way to the nap hotspot");
  ok(!checkDecor("garden", [], "rag_rug", 160, 316).ok, "not on the bridge");
  ok(
    checkDecor("garden", [{ item: "stool", x: 160, y: 380 }], "stool", 60, 340)
      .ok,
    "a keepsake moves out of the hut into the garden",
  );
  ok(
    checkDecor(
      "hut",
      [{ item: "cairn", x: 60, y: 340, area: "garden" }],
      "stool",
      160,
      380,
    ).ok,
    "a garden keepsake takes no room in the hut",
  );
  const both = restoreDecor(
    [
      { item: "stool", x: 160, y: 380 },
      { item: "fern_pot", x: 60, y: 340, area: "garden" },
    ],
    [],
  );
  ok(
    both.length === 2 &&
      both[1].area === "garden" &&
      both[0].area === undefined,
    "a save keeps where each keepsake stands, inside or out",
  );
}
console.log("Keepsakes: found by walking, placed freely, never in the way.");

// The connected world (Matt, 18 Oct 19:07): saves from the old shape land in the same
// place in their zone, and the desert walks on into the fire country.
{
  const castle = restoreWorld({
    region: "lava",
    x: 160,
    y: 576 + 300,
    visited: ["hearthold"],
  });
  const h = regionTiles("west").find((t) => t.id === "hearthold")!;
  const ho = tileOrigin("west", h);
  ok(
    castle?.region === "west" &&
      castle.x === ho.x + 160 &&
      castle.y === ho.y + 300,
    "a spot saved in the old Ember Lands is the same spot in Hearthold today",
  );
  const g = regionTiles("west").find((t) => t.id === "gulch")!;
  const go = tileOrigin("west", g);
  const town = restoreWorld({
    region: "west",
    x: 320 + 100,
    y: 200,
    visited: [],
  });
  ok(
    town?.x === go.x + 100 && town.y === go.y + 200,
    "a spot saved in the old Dust Gulch is the same spot in it today",
  );
  ok(
    restoreWorld({ region: "west", x: go.x + 100, y: go.y + 200, layout: 2 })
      ?.y ===
      go.y + 200,
    "a spot saved in today’s shape is read as it is",
  );
  ok(
    restoreWorld({ region: "lava", x: 1, y: 1, layout: 99 }) === null,
    "an unknown shape starts fresh",
  );
  // Neon Harbour grew into the city (layout 4): the region now starts two rows higher,
  // so a spot saved in the old core or the Skyport keeps its place in that zone
  const no = tileOrigin(
    "neon",
    regionTiles("neon").find((t) => t.id === "neon")!,
  );
  const so = tileOrigin(
    "neon",
    regionTiles("neon").find((t) => t.id === "skyport")!,
  );
  for (const layout of [1, 2, 3]) {
    const core = restoreWorld({
      region: "neon",
      x: 160.5,
      y: 192.25,
      visited: ["neon"],
      layout,
    });
    ok(
      core?.region === "neon" &&
        core.x === no.x + 160.5 &&
        core.y === no.y + 192.25,
      `a layout-${layout} spot in Neon's old core is the same spot in it today`,
    );
    ok(
      tileAt("neon", core!.x, core!.y)?.id === "neon",
      `and it stands in the old core (layout ${layout})`,
    );
    const sky = restoreWorld({
      region: "neon",
      x: 320 + 70.5,
      y: 84.25,
      visited: ["skyport"],
      layout,
    });
    ok(
      sky?.x === so.x + 70.5 &&
        sky.y === so.y + 84.25 &&
        tileAt("neon", sky.x, sky.y)?.id === "skyport",
      `a layout-${layout} spot on the Skyport's platform is the same spot today`,
    );
    ok(
      core!.visited.join() === "neon" && sky!.visited.join() === "skyport",
      "visits are kept",
    );
  }
  const today = restoreWorld(
    moveTo(
      moveTo(null, "neon", no.x + 160, no.y - 200),
      "neon",
      no.x + 160,
      no.y + 192,
    ),
  );
  const again = restoreWorld(today);
  ok(
    today?.x === no.x + 160 &&
      today.y === no.y + 192 &&
      again?.y === today.y &&
      again?.visited.join() === "market,neon",
    "a spot saved in today’s city reads back the same, and again",
  );
  const rows = regionWalk("west");
  const grid = makeWalkGrid(rows, {
    cell: TILE.cell,
    width: regionBounds("west").width,
    start: regionPoint(travelPoints.west),
  });
  ok(
    grid.findPath(
      regionPoint(travelPoints.west),
      regionPoint(travelPoints.lava),
    ).length > 0,
    "Dust Gulch’s platform walks all the way to the caldera’s cart bay",
  );
}
console.log(
  "Layouts: old saves carried forward; the desert walks into the fire country.",
);

/** A zone's named stand in its region's pixels. */
function standAt(region: "valley" | "isles", zone: string, stand: string) {
  const t = regionTiles(region).find((x) => x.id === zone)!;
  const o = tileOrigin(region, t);
  const p = (
    zoneMaps as Record<
      string,
      { stands: Record<string, readonly [number, number]> }
    >
  )[zone].stands[stand];
  return { x: o.x + p[0], y: o.y + p[1] };
}

// The Frostline Highlands: the valley grows north; a saved spot stays where it was in its
// zone, and the high loop and the lookout are walked from the ridge cabin.
{
  const g = regionTiles("valley").find((t) => t.id === "garden")!;
  const go = tileOrigin("valley", g);
  const home = restoreWorld({
    region: "valley",
    x: 320 + 160,
    y: 576 + 200,
    layout: 2,
  });
  ok(
    home?.region === "valley" && home.x === go.x + 160 && home.y === go.y + 200,
    "a valley spot saved before the Frostline is the same spot in the garden today",
  );
  const rows = regionWalk("valley");
  const at = (zone: string, stand: string) => standAt("valley", zone, stand);
  const cabin = at("ridge", "cabin");
  const grid = makeWalkGrid(rows, {
    cell: TILE.cell,
    width: regionBounds("valley").width,
    start: cabin,
  });
  for (const [zone, stand] of [
    ["hollow", "clearing"],
    ["snowmelt", "shore"],
    ["saddle", "bothy"],
    ["summit", "scope"],
  ] as const)
    ok(
      grid.findPath(cabin, at(zone, stand)).length > 0,
      `the ridge cabin walks to ${zone}`,
    );
  ok(
    grid.findPath(at("woodland", "clearing"), at("hollow", "clearing")).length >
      0,
    "the woodland reaches the hollow (the long way round, by the ridge)",
  );
}
console.log(
  "Frostline: the high loop is walked from the ridge, old spots stay put.",
);

// The Tidebloom Isles: the ferry runs from Driftwood's jetty, and the island is one loop.
{
  ok(
    travelRoute("pier", "isles").join() === "isles",
    "the ferry runs from the jetty to the isles",
  );
  ok(travelVehicle("pier", "isles") === "ferry", "and it is a ferry");
  ok(
    travelRoute("valley", "isles").length === 0,
    "the valley train does not run to the isles",
  );
  const rows = regionWalk("isles");
  const at = (zone: string, stand: string) => standAt("isles", zone, stand);
  const pier = regionPoint(travelPoints.isles);
  const grid = makeWalkGrid(rows, {
    cell: TILE.cell,
    width: regionBounds("isles").width,
    start: pier,
  });
  for (const [zone, stand] of [
    ["rainforest", "bridge"],
    ["headwaters", "pool"],
    ["cove", "beach"],
  ] as const)
    ok(
      grid.findPath(pier, at(zone, stand)).length > 0,
      `the pier walks to ${zone}`,
    );
}
console.log(
  "Isles: the ferry runs from the jetty; the island is walked from its pier.",
);
