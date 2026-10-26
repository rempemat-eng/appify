import { useMemo } from 'react';
import { Image, View, type ImageSourcePropType } from 'react-native';
import Animated, { useAnimatedStyle, type SharedValue } from 'react-native-reanimated';
import { ROCKET, rocketArt, type RocketArt, type RocketArtKey } from '@/lib/rocket-assets';
import {
  LAYOUT,
  PUFF_GONE,
  armFrames,
  boosterAt,
  camera,
  docked,
  dustFor,
  flames,
  grainAt,
  legFrame,
  onMoon,
  puffAt,
  puffsFor,
  rcsFrame,
  shadowAt,
  shake,
  vehicleTop,
  type Flight,
  type Grain,
  type Puff,
} from '@/lib/rocket-flight';

/**
 * The rocket and lander journeys (lib/rocket-flight.ts has the beats, scripts/art/rocket.py
 * the pictures): a column of the world, the pad at its foot and Halcyon at its head, drawn
 * on the world's pixel grid (one art px = u CSS px, every position a whole number of art px)
 * and moved by one clock, `t` (0 to 1 over the leg). Everything here is presentation: the
 * journey (components/journey.tsx) decides when it starts, stops and arrives.
 */
const art = (k: RocketArtKey): RocketArt => rocketArt[k];
const Y0 = -2600; // the column's top, so every picture's top is positive inside it
const MOON_BG = '#05040A';
const REGOLITH = ['#100C08', '#3C3630', '#686159', '#8E877E', '#ABA190', '#C5B8A1'];

type Ctx = { flight: Flight; t: SharedValue<number>; u: number; cx: number; ms: number; h: number };

/** A static picture at a world position (its top left), in the column. */
function Pic({ k, x, y, u }: { k: RocketArtKey; x: number; y: number; u: number }) {
  const a = rocketArt[k];
  return (
    <Image
      source={a.source}
      resizeMode="stretch"
      style={{
        position: 'absolute',
        left: x * u,
        top: (y - Y0) * u,
        width: a.w * u,
        height: a.h * u,
      }}
    />
  );
}

/** A looping tile repeated across the screen at a world height. */
function Band({
  k,
  y,
  u,
  cx,
  across,
}: {
  k: RocketArtKey;
  y: number;
  u: number;
  cx: number;
  across: number;
}) {
  const a = rocketArt[k];
  const n = Math.ceil(across / a.w) + 2;
  const left = cx - Math.floor((n * a.w) / 2);
  return (
    <>
      {Array.from({ length: n }, (_, i) => (
        <Pic key={`${k}-${i}`} k={k} x={left + i * a.w} y={y} u={u} />
      ))}
    </>
  );
}

/** One frame of a sheet (frames stacked top to bottom), shown in a box that the worklet
 *  `at` moves (world top left) and steps (frame; -1 or past the last hides it). */
function Sheet({
  source,
  fw,
  fh,
  frames,
  u,
  t,
  at,
  flip,
}: {
  source: ImageSourcePropType;
  fw: number;
  fh: number;
  frames: number;
  u: number;
  t: SharedValue<number>;
  at: (p: number) => { x: number; y: number; frame: number };
  flip?: boolean;
}) {
  // (t is read here, in the style's own closure, so the style follows the clock)
  const box = useAnimatedStyle(() => {
    const a = at(t.value);
    const hidden = a.frame < 0 || a.frame >= frames;
    return {
      opacity: hidden ? 0 : 1,
      transform: [
        { translateX: a.x * u },
        { translateY: (a.y - Y0) * u },
        { scaleX: flip ? -1 : 1 },
      ],
    };
  });
  const strip = useAnimatedStyle(() => {
    const a = at(t.value);
    const f = Math.max(0, Math.min(frames - 1, a.frame));
    return { transform: [{ translateY: -f * fh * u }] };
  });
  return (
    <Animated.View
      pointerEvents="none"
      style={[
        {
          position: 'absolute',
          left: 0,
          top: 0,
          width: fw * u,
          height: fh * u,
          overflow: 'hidden',
        },
        box,
      ]}
    >
      <Animated.Image
        source={source}
        resizeMode="stretch"
        style={[
          { position: 'absolute', left: 0, top: 0, width: fw * u, height: fh * frames * u },
          strip,
        ]}
      />
    </Animated.View>
  );
}

/** A picture that the worklet `at` moves (world top left) and shows or hides. */
function Moving({
  k,
  u,
  t,
  at,
}: {
  k: RocketArtKey;
  u: number;
  t: SharedValue<number>;
  at: (p: number) => { x: number; y: number; show: boolean };
}) {
  const a = rocketArt[k];
  const style = useAnimatedStyle(() => {
    const p = at(t.value);
    return {
      opacity: p.show ? 1 : 0,
      transform: [{ translateX: p.x * u }, { translateY: (p.y - Y0) * u }],
    };
  });
  return (
    <Animated.Image
      source={a.source}
      resizeMode="stretch"
      style={[{ position: 'absolute', left: 0, top: 0, width: a.w * u, height: a.h * u }, style]}
    />
  );
}

function PuffView({ q, c }: { q: Puff; c: Ctx }) {
  const a = rocketArt[`puff-${q.kind}`];
  const [fw, fh] = a.frame;
  const { t, cx } = c;
  return (
    <Sheet
      source={a.source}
      fw={fw}
      fh={fh}
      frames={a.frames}
      u={c.u}
      t={t}
      at={(p) => {
        'worklet';
        const s = puffAt(q, p);
        return {
          x: cx + s.x - fw / 2,
          y: s.y - fh / 2,
          frame: s.frame === PUFF_GONE ? -1 : s.frame,
        };
      }}
    />
  );
}

function GrainView({ g, c }: { g: Grain; c: Ctx }) {
  const { t, cx, u } = c;
  const style = useAnimatedStyle(() => {
    const s = grainAt(g, t.value);
    return {
      opacity: s ? 1 : 0,
      transform: [
        { translateX: (cx + (s?.x ?? 0)) * u },
        { translateY: ((s?.y ?? 0) - 2 - Y0) * u },
      ],
    };
  });
  return (
    <Animated.View
      pointerEvents="none"
      style={[
        {
          position: 'absolute',
          left: 0,
          top: 0,
          width: g.w * u,
          height: 2 * u,
          backgroundColor: REGOLITH[g.tone],
        },
        style,
      ]}
    >
      {/* each grain lit on top, its underside nearly black (no air to soften it) */}
      <View
        style={{
          position: 'absolute',
          left: 0,
          top: u,
          width: g.w * u,
          height: u,
          backgroundColor: REGOLITH[1],
        }}
      />
    </Animated.View>
  );
}

/** The vehicle: the upper stage (four leg frames) or the lander (four), one shown at a time. */
function Vehicle({ c }: { c: Ctx }) {
  const { flight, t, cx } = c;
  const moon = onMoon(flight);
  const keys: RocketArtKey[] = moon
    ? ['lander0', 'lander1', 'lander2', 'lander3']
    : ['upper0', 'upper1', 'upper2', 'upper3'];
  const half = art(keys[0]).cx ?? 0;
  return (
    <>
      {keys.map((k, i) => (
        <Moving
          key={k}
          k={k}
          u={c.u}
          t={t}
          at={(p) => {
            'worklet';
            return { x: cx - half, y: vehicleTop(flight, p), show: legFrame(flight, p) === i };
          }}
        />
      ))}
    </>
  );
}

/** Everything that moves above the vehicle's ground: flames, thrusters, the booster, the
 *  gantry's arms, smoke and dust, the port's lamp. */
function Movers({ c, children }: { c: Ctx; children?: React.ReactNode }) {
  const { flight, t, cx, ms, u } = c;
  const puffs = useMemo(() => puffsFor(flight), [flight]);
  const dust = useMemo(() => dustFor(flight), [flight]);
  const moon = onMoon(flight);
  const fb = rocketArt['flame-booster'];
  const fu = rocketArt['flame-upper'];
  const fl = rocketArt['flame-lander'];
  const rcs = rocketArt.rcs;
  const booster = rocketArt.booster;
  const upperHalf = rocketArt.upper0.cx ?? 0;
  const landerHalf = rocketArt.lander0.cx ?? 0;
  const back = puffs.filter((q) => q.kind !== 'fire');
  const front = puffs.filter((q) => q.kind === 'fire');
  return (
    <>
      {back.map((q) => (
        <PuffView key={`${q.kind}-${q.at}-${q.x}`} q={q} c={c} />
      ))}
      {/* the upper stage sits behind the booster's forward skirt while they are stacked */}
      {!moon && <Vehicle c={c} />}
      {flight === 'launch' && (
        <>
          <Moving
            k="booster"
            u={u}
            t={t}
            at={(p) => {
              'worklet';
              const b = boosterAt(flight, p);
              return { x: cx - (booster.cx ?? 0) + (b?.x ?? 0), y: b?.y ?? 0, show: !!b };
            }}
          />
          <Sheet
            source={fb.source}
            fw={fb.frame[0]}
            fh={fb.frame[1]}
            frames={fb.frames}
            u={u}
            t={t}
            at={(p) => {
              'worklet';
              const b = boosterAt(flight, p);
              return {
                x: cx + (b?.x ?? 0) - fb.frame[0] / 2,
                y: (b?.y ?? 0) + 95,
                frame: b ? flames(flight, p, ms).booster : -1,
              };
            }}
          />
        </>
      )}
      {moon && <Vehicle c={c} />}
      {!moon && (
        <Sheet
          source={fu.source}
          fw={fu.frame[0]}
          fh={fu.frame[1]}
          frames={fu.frames}
          u={u}
          t={t}
          at={(p) => {
            'worklet';
            return {
              x: cx - fu.frame[0] / 2,
              y: vehicleTop(flight, p) + 68,
              frame: flames(flight, p, ms).upper,
            };
          }}
        />
      )}
      {moon && (
        <Sheet
          source={fl.source}
          fw={fl.frame[0]}
          fh={fl.frame[1]}
          frames={fl.frames}
          u={u}
          t={t}
          at={(p) => {
            'worklet';
            return {
              x: cx - fl.frame[0] / 2,
              y: vehicleTop(flight, p) + 58,
              frame: flames(flight, p, ms).lander,
            };
          }}
        />
      )}
      {[-1, 1].map((side) => (
        <Sheet
          key={`rcs-${side}`}
          source={rcs.source}
          fw={rcs.frame[0]}
          fh={rcs.frame[1]}
          frames={rcs.frames}
          u={u}
          flip={side < 0}
          t={t}
          at={(p) => {
            'worklet';
            const half = moon ? landerHalf - 2 : upperHalf - 13;
            return {
              x: cx + side * half - (side < 0 ? rcs.frame[0] : 0),
              y: vehicleTop(flight, p) + (moon ? 35 : 31),
              frame: rcsFrame(flight, p, ms),
            };
          }}
        />
      ))}
      {flight === 'launch' &&
        (['arm0', 'arm1'] as const).map((k, i) => {
          const a = rocketArt[k];
          return (
            <Sheet
              key={k}
              source={a.source}
              fw={a.frame[0]}
              fh={a.frame[1]}
              frames={a.frames}
              u={u}
              t={t}
              at={(p) => {
                'worklet';
                return {
                  x: cx + LAYOUT.earth.tower - a.frame[0] + 1,
                  y: i === 0 ? LAYOUT.earth.arm0 : LAYOUT.earth.arm1,
                  frame: armFrames(flight, p)[i],
                };
              }}
            />
          );
        })}
      {front.map((q) => (
        <PuffView key={`${q.kind}-${q.at}-${q.x}`} q={q} c={c} />
      ))}
      {dust.map((g) => (
        <GrainView key={`${g.at}-${g.x}-${g.d}`} g={g} c={c} />
      ))}
      {children}
    </>
  );
}

/** The station's port lamps: hazard ochre while waiting, green once a vehicle is docked. */
function PortLamps({ c, dock }: { c: Ctx; dock: number }) {
  const { flight, t, cx, u } = c;
  const green = useAnimatedStyle(() => ({ opacity: docked(flight, t.value) ? 1 : 0 }));
  const lamps = [-12, -9, -6, -3, 0, 3, 6, 9];
  const row = -dock - 98 + 93;
  return (
    <>
      {lamps.map((x) => (
        <View
          key={`wait-${x}`}
          style={{
            position: 'absolute',
            left: (cx + x) * u,
            top: (row - Y0) * u,
            width: u,
            height: u,
            backgroundColor: '#DAAD54',
          }}
        />
      ))}
      {lamps.map((x) => (
        <Animated.View
          key={`green-${x}`}
          style={[
            {
              position: 'absolute',
              left: (cx + x) * u,
              top: (row - Y0) * u,
              width: u,
              height: u,
              backgroundColor: '#9FE6CC',
            },
            green,
          ]}
        />
      ))}
    </>
  );
}

/**
 * One flight's scene at the clock `t`. `width` and `height` are the screen's (CSS px), `u`
 * CSS px per art px.
 */
export function RocketScene({
  flight,
  t,
  width,
  height,
  u,
  ms,
  insetTop = 0,
  insetBottom = 0,
}: {
  flight: Flight;
  t: SharedValue<number>;
  width: number;
  height: number;
  u: number;
  ms: number;
  /** the HUD's and the hotbar's room (CSS px), so the pad and the port frame clear of them */
  insetTop?: number;
  insetBottom?: number;
}) {
  const across = Math.ceil(width / u);
  const h = Math.floor(height / u);
  // (the label sits under the HUD, SKIP above the hotbar)
  const top = Math.ceil((insetTop + 48) / u);
  const bottom = Math.ceil((insetBottom + 64) / u);
  const cx = Math.round(across / 2);
  const c: Ctx = { flight, t, u, cx, ms, h };
  const moon = onMoon(flight);
  const E = LAYOUT.earth;
  const M = LAYOUT.moon;
  const dock = moon ? M.dock : E.dock;
  const cam = useAnimatedStyle(() => ({
    transform: [
      { translateX: shake(flight, t.value) * u },
      { translateY: -(camera(flight, t.value, h, top, bottom) - Y0) * u },
    ],
  }));
  const shadow = rocketArt['lander-shadow'];
  const sky = rocketArt.sky;
  return (
    <View
      pointerEvents="none"
      // @ts-expect-error dataSet is a react-native-web prop (crisp pixel scaling via CSS)
      dataSet={{ pixel: 'true' }}
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        width,
        height,
        overflow: 'hidden',
        backgroundColor: MOON_BG,
      }}
    >
      <Animated.View
        style={[{ position: 'absolute', left: 0, top: 0, width, height: 4000 * u }, cam]}
      >
        {!moon && (
          <>
            {/* the night sky's column (1x: a soft fade), then the stars where it is dark */}
            {Array.from({ length: Math.ceil(across / sky.w) + 2 }, (_, i) => (
              <Image
                key={`sky-${i}`}
                source={sky.source}
                resizeMode="stretch"
                style={{
                  position: 'absolute',
                  left:
                    (cx - Math.floor(((Math.ceil(across / sky.w) + 2) * sky.w) / 2) + i * sky.w) *
                    u,
                  top: (E.sky - ROCKET.skyH - Y0) * u,
                  width: sky.w * u,
                  height: sky.h * u,
                }}
              />
            ))}
            {[0, 1, 2, 3].map((k) => (
              <Band
                key={`stars-${k}`}
                k="stars"
                y={E.starsFrom - 256 * (k + 1)}
                u={u}
                cx={cx}
                across={across}
              />
            ))}
            <Band k="clouds-high" y={E.cloudsHigh} u={u} cx={cx} across={across} />
            <Band k="clouds-low" y={E.cloudsLow} u={u} cx={cx} across={across} />
            <Band k="skyline" y={E.deck - rocketArt.skyline.h} u={u} cx={cx} across={across} />
            <Band k="deck" y={E.deck} u={u} cx={cx} across={across} />
            <Pic k="tower" x={cx + E.tower - 1} y={E.deck + 4 - rocketArt.tower.foot} u={u} />
            <Pic k="mount" x={cx - (rocketArt.mount.cx ?? 0)} y={E.mountTop} u={u} />
          </>
        )}
        {moon && (
          <>
            {[0, 1, 2, 3, 4, 5].map((k) => (
              <Band
                key={`stars-${k}`}
                k="stars"
                y={M.horizon - 256 * (k + 1)}
                u={u}
                cx={cx}
                across={across}
              />
            ))}
            <Pic k="planet" x={cx + M.planet[0]} y={M.planet[1]} u={u} />
            <Band k="moon-ground" y={M.horizon} u={u} cx={cx} across={across} />
            <Pic k="lumen-pad" x={cx - (rocketArt['lumen-pad'].cx ?? 0)} y={M.padTop} u={u} />
            <Moving
              k="lander-shadow"
              u={u}
              t={t}
              at={(p) => {
                'worklet';
                const s = shadowAt(flight, p);
                return { x: cx - shadow.w / 2 + (s?.x ?? 0), y: -3, show: !!s };
              }}
            />
          </>
        )}
        <Pic k="station" x={cx - (rocketArt.station.cx ?? 0)} y={-dock - 98} u={u} />
        <PortLamps c={c} dock={dock} />
        <Movers c={c} />
      </Animated.View>
    </View>
  );
}
