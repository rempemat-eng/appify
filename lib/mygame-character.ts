/** Presentation bridge for the MyGame drawings. The caller owns movement, combat,
 * collision, action identity and the shared (paused when inactive) animation clock. */
export const MYGAME_CHARACTERS = [
  'bramble',
  'morel',
  'velvet',
  'cairn',
  'iona',
  'tam',
  'brine',
  'pendle',
  'mirra',
  'ashe',
  'clack',
  'nix',
  'rook',
  'mote',
] as const;
export type MyGameCharacterId = (typeof MYGAME_CHARACTERS)[number];
export type MyGameView = 'E' | 'SE' | 'S' | 'SW' | 'W' | 'NW' | 'N' | 'NE';
export type MyGamePoint = { x: number; y: number };
export type MyGameFrame = {
  asset: string;
  rect: readonly [number, number, number, number];
  atlasSize: readonly [number, number];
  duration: number;
  /** Stored PNG origin in the view's virtual frame. */
  cropOffset: readonly [number, number];
};
export type MyGameClip = {
  frames: readonly MyGameFrame[];
  loop: boolean;
  releaseFrame: number | null;
  holdFrame: number | null;
  /** Source-pixel offset from the foot, drawn separately for this view. */
  releaseAnchor: readonly [number, number] | null;
};
export type MyGameCharacterView = {
  frameSize: readonly [number, number];
  footPivot: readonly [number, number];
  bodyHeight: number;
  status?: string;
  missingClips?: readonly string[];
  clips: Readonly<Record<string, MyGameClip>>;
};
export type MyGameCharacterAsset = {
  id: MyGameCharacterId;
  views: Partial<Record<MyGameView, MyGameCharacterView>>;
};

/** Exact views only: upper-left lighting and weapon hands prohibit mirrored art. */
export function myGameClip(asset: MyGameCharacterAsset, view: MyGameView, name: string) {
  return asset.views[view]?.clips[name];
}

export function clipDuration(clip: MyGameClip) {
  return clip.frames.reduce((sum, frame) => sum + frame.duration, 0);
}

export function releaseTime(clip: MyGameClip): number | null {
  return clip.releaseFrame === null
    ? null
    : clip.frames.slice(0, clip.releaseFrame).reduce((sum, frame) => sum + frame.duration, 0);
}

/** Half-open crossing, for one non-looping action instance. This is a presentation
 * event only; gameplay must keep its own authoritative release/hit decisions. */
export function crossedRelease(clip: MyGameClip, previous: number, current: number) {
  const at = releaseTime(clip);
  return at !== null && !clip.loop && current >= at && previous < at && current >= previous;
}

export function sampleMyGameClip(
  clip: MyGameClip,
  elapsed: number,
  options: { holding?: boolean; reducedMotion?: boolean } = {},
) {
  const duration = clipDuration(clip);
  if (
    !clip.frames.length ||
    !Number.isFinite(duration) ||
    duration <= 0 ||
    !clip.frames.every((f) => Number.isFinite(f.duration) && f.duration > 0)
  ) {
    throw new Error('MyGame clip needs positive frame durations');
  }
  for (const index of [clip.releaseFrame, clip.holdFrame]) {
    if (index !== null && (!Number.isInteger(index) || index < 0 || index >= clip.frames.length))
      throw new Error('MyGame event frame outside clip');
  }
  const time = Number.isFinite(elapsed) ? Math.max(0, elapsed) : 0;
  const finished = !clip.loop && time >= duration;
  // Reduced motion keeps a meaningful held/act pose. It does not change game time.
  if (options.reducedMotion) {
    const index =
      options.holding && clip.holdFrame !== null ? clip.holdFrame : (clip.releaseFrame ?? 0);
    return {
      index,
      frame: clip.frames[index],
      finished: options.holding && clip.holdFrame !== null ? false : finished,
    };
  }
  let position = clip.loop ? time % duration : Math.min(time, duration);
  if (options.holding && clip.holdFrame !== null) {
    const holdAt = clip.frames.slice(0, clip.holdFrame).reduce((sum, f) => sum + f.duration, 0);
    if (position >= holdAt) {
      return { index: clip.holdFrame, frame: clip.frames[clip.holdFrame], finished: false };
    }
  }
  for (let index = 0; index < clip.frames.length; index++) {
    const frame = clip.frames[index];
    if (position < frame.duration || index === clip.frames.length - 1) {
      return { index, frame, finished };
    }
    position -= frame.duration;
  }
  throw new Error('Unreachable MyGame frame');
}

/** One transform for body and muzzle. Logical foot/depth stays on the support
 * surface while the sprite rises; the shadow is not pulled into the air. */
export function projectMyGameCharacter(input: {
  asset: Pick<MyGameCharacterView, 'frameSize' | 'footPivot'>;
  foot: MyGamePoint;
  supportHeight: number;
  airborneHeight: number;
  worldUnit: number;
  assetPixelsPerWorldPixel: number;
  devicePixelRatio: number;
  depthOffset?: number;
}) {
  const { asset, foot, supportHeight, airborneHeight, worldUnit, assetPixelsPerWorldPixel } = input;
  if (
    ![worldUnit, assetPixelsPerWorldPixel, input.devicePixelRatio].every(
      (v) => Number.isFinite(v) && v > 0,
    )
  ) {
    throw new Error('MyGame projection needs explicit positive world unit, asset density and DPR');
  }
  if (
    ![foot.x, foot.y, supportHeight, airborneHeight].every(Number.isFinite) ||
    airborneHeight < 0 ||
    (input.depthOffset !== undefined && !Number.isFinite(input.depthOffset))
  ) {
    throw new Error('MyGame projection needs finite positions and nonnegative airborne height');
  }
  const ratio = input.devicePixelRatio;
  const snap = (value: number) => Math.round(value * ratio) / ratio;
  const sourceUnit = worldUnit / assetPixelsPerWorldPixel;
  const bodyFoot = {
    x: foot.x * worldUnit,
    y: (foot.y - supportHeight - airborneHeight) * worldUnit,
  };
  const left = snap(bodyFoot.x - asset.footPivot[0] * sourceUnit);
  const top = snap(bodyFoot.y - asset.footPivot[1] * sourceUnit);
  return {
    left,
    top,
    sourceUnit,
    width: asset.frameSize[0] * sourceUnit,
    height: asset.frameSize[1] * sourceUnit,
    shadow: { x: snap(foot.x * worldUnit), y: snap((foot.y - supportHeight) * worldUnit) },
    // AtlasWalk prop zIndex is the unscaled region-space foot, +300000 on a deck.
    depth: Math.round(foot.y) + (input.depthOffset ?? 0),
    crisp:
      sourceUnit * ratio >= 1 &&
      Math.abs(sourceUnit * ratio - Math.round(sourceUnit * ratio)) < 1e-8,
    anchor(offset: readonly [number, number]) {
      return {
        x: left + (asset.footPivot[0] + offset[0]) * sourceUnit,
        y: top + (asset.footPivot[1] + offset[1]) * sourceUnit,
      };
    },
  };
}

type SupportTile = { walk: string; terrain: string; tiers?: string; deck?: string };
export type MyGameWorldSource = {
  tileSize: number;
  cellSize: number;
  tiles: Readonly<Record<string, Readonly<Record<string, SupportTile>>>>;
};
const expand = (rle: string) =>
  rle.replace(/(\d+)([^\d])/g, (_match, n: string, c: string) => c.repeat(Number(n)));

/** Read the real generated world without adding a terrace, stair, collision rule or
 * save format. Heights need the world's explicit resolver when tiers/decks exist. */
export function makeMyGameWorldSupport(source: MyGameWorldSource) {
  if (source.tileSize <= 0 || source.cellSize <= 0 || source.tileSize % source.cellSize !== 0) {
    throw new Error('Invalid world support grid');
  }
  const cells = source.tileSize / source.cellSize;
  const cache = new Map<string, { walk: string; terrain: string; tiers?: string; deck?: string }>();
  return (plane: string, point: MyGamePoint) => {
    if (!Number.isFinite(point.x) || !Number.isFinite(point.y))
      throw new Error('Invalid world point');
    const tx = Math.floor(point.x / source.tileSize);
    const ty = Math.floor(point.y / source.tileSize);
    const key = `${tx},${ty}`;
    const raw = source.tiles[plane]?.[key];
    if (!raw)
      return {
        walkable: false,
        material: '-',
        height: undefined,
        needsHeightResolver: false,
      } as const;
    const cacheKey = `${plane}/${key}`;
    let tile = cache.get(cacheKey);
    if (!tile) {
      tile = {
        walk: expand(raw.walk),
        terrain: expand(raw.terrain),
        tiers: raw.tiers && expand(raw.tiers),
        deck: raw.deck && expand(raw.deck),
      };
      if (tile.walk.length !== cells * cells || tile.terrain.length !== cells * cells)
        throw new Error(`Invalid support tile ${cacheKey}`);
      cache.set(cacheKey, tile);
    }
    const x = Math.floor((point.x - tx * source.tileSize) / source.cellSize);
    const y = Math.floor((point.y - ty * source.tileSize) / source.cellSize);
    const index = y * cells + x;
    const needsHeightResolver = tile.tiers !== undefined || tile.deck !== undefined;
    return {
      walkable: tile.walk[index] === '.',
      material: tile.terrain[index],
      height: needsHeightResolver ? undefined : 0,
      needsHeightResolver,
    };
  };
}
