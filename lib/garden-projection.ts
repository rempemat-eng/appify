// 2.5D ("HD-2D"-style) projection for the garden: the ground plane tilts away
// from the camera around its bottom edge, while sprites stay upright billboards
// scaled by depth. Pure maths shared by the UI and the Reanimated worklet.
//
// Flat view is the identity (f = 1), so every caller can always project.

export type ViewMode = 'flat' | 'tilt';

export type Projection = {
  mode: ViewMode;
  /** screen px per native garden px at the near (bottom) edge */
  scale: number;
  /** native garden size */
  w: number;
  h: number;
  /** screen width of the world */
  width: number;
  /** tilt angle (radians) and perspective distance (screen px) */
  sin: number;
  cos: number;
  persp: number;
  /** screen y of the plane's near edge (bottom of the world) */
  bottom: number;
  /** total screen height of the world (sky band + projected plane) */
  height: number;
  /** screen y of the far edge (the horizon line) */
  horizon: number;
};

export const TILT_DEG = 38;

export function makeProjection(
  mode: ViewMode,
  width: number,
  native: { width: number; height: number },
  skyBand = 0,
): Projection {
  const scale = width / native.width;
  if (mode === 'flat') {
    const height = Math.round(native.height * scale);
    return {
      mode,
      scale,
      w: native.width,
      h: native.height,
      width,
      sin: 0,
      cos: 1,
      persp: 1,
      bottom: height,
      height,
      horizon: 0,
    };
  }
  const a = (TILT_DEG * Math.PI) / 180;
  const sin = Math.sin(a);
  const cos = Math.cos(a);
  const persp = width * 3;
  const depth = native.height * scale;
  const planeH = (depth * cos * persp) / (persp + depth * sin);
  const height = Math.round(planeH + skyBand);
  return {
    mode,
    scale,
    w: native.width,
    h: native.height,
    width,
    sin,
    cos,
    persp,
    bottom: height,
    height,
    horizon: height - planeH,
  };
}

/** Screen position (sx, sy) and depth scale f of a native ground point. */
export function project(p: Projection, x: number, y: number) {
  'worklet';
  const d = (p.h - y) * p.scale; // distance from the near edge, on the plane
  const f = p.persp / (p.persp + d * p.sin);
  const cx = p.width / 2;
  return { sx: cx + (x * p.scale - cx) * f, sy: p.bottom - d * p.cos * f, f };
}

/** Inverse of project for a tap on the ground (screen -> native point). */
export function unproject(p: Projection, sx: number, sy: number) {
  const Y = p.bottom - sy;
  const d = (Y * p.persp) / (p.persp * p.cos - Y * p.sin);
  const f = p.persp / (p.persp + d * p.sin);
  const cx = p.width / 2;
  return { x: ((sx - cx) / f + cx) / p.scale, y: p.h - d / p.scale };
}

/** Upright billboard for a sprite whose feet sit at (x + w/2, y + h). */
export function billboard(p: Projection, x: number, y: number, w: number, h: number) {
  const { sx, sy, f } = project(p, x + w / 2, y + h);
  const bw = w * p.scale * f;
  const bh = h * p.scale * f;
  return { left: sx - bw / 2, top: sy - bh, width: bw, height: bh, f };
}

/** Screen bounding box of a flat rectangle lying on the ground (hit areas). */
export function groundRect(p: Projection, x: number, y: number, w: number, h: number) {
  const a = project(p, x, y);
  const b = project(p, x + w, y);
  const c = project(p, x, y + h);
  const d = project(p, x + w, y + h);
  const left = Math.min(a.sx, c.sx);
  const right = Math.max(b.sx, d.sx);
  return { left, top: a.sy, width: right - left, height: c.sy - a.sy };
}

/**
 * A point in the air: (x, y) in sprite space above a ground point at groundY
 * (e.g. chimney smoke above the hut's footprint). Flat view: identity.
 */
export function lift(p: Projection, x: number, y: number, groundY: number) {
  const s = project(p, x, groundY);
  return { sx: s.sx, sy: s.sy - (groundY - y) * p.scale * s.f, f: s.f };
}
