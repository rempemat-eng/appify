import { useEffect, useState } from 'react';
import { StyleSheet, View, type ColorValue, type ViewStyle } from 'react-native';
import Svg, { G, Rect } from 'react-native-svg';
import { useReducedMotion } from '@/lib/motion';
import { propPixels, sceneColors as c, type PropKind } from '@/lib/scene-art';
import { status, useGame, type Player } from '@/lib/game';

function Pixels({
  kind,
  x = 0,
  y = 0,
  scale = 1,
  tint,
}: {
  kind: PropKind;
  x?: number;
  y?: number;
  scale?: number;
  tint?: ColorValue;
}) {
  return (
    <G transform={`translate(${x} ${y}) scale(${scale})`}>
      {propPixels[kind].map((p) => (
        <Rect key={`${p.x}-${p.y}`} x={p.x} y={p.y} width={1} height={1} fill={tint ?? p.color} />
      ))}
    </G>
  );
}
export function PixelProp({
  kind,
  size = 48,
  tint,
}: {
  kind: PropKind;
  size?: number;
  tint?: ColorValue;
}) {
  return (
    <Svg width={size} height={size} viewBox="0 0 16 16" accessibilityLabel={kind}>
      <Pixels kind={kind} tint={tint} />
    </Svg>
  );
}
export type SceneKind =
  | 'habitat'
  | 'night'
  | 'park'
  | 'book'
  | 'mountain'
  | 'town'
  | 'market'
  | 'nest'
  | 'trail';
// Blend two #RRGGBB colours (t = 0 gives a, 1 gives b).
function mix(a: string, b: string, t: number) {
  if (!/^#[0-9a-f]{6}$/i.test(a) || !/^#[0-9a-f]{6}$/i.test(b)) return t < 0.5 ? a : b;
  const ch = (hex: string, i: number) => parseInt(hex.slice(1 + i * 2, 3 + i * 2), 16);
  return `#${[0, 1, 2]
    .map((i) => Math.round(ch(a, i) + (ch(b, i) - ch(a, i)) * t).toString(16).padStart(2, '0'))
    .join('')}`;
}
// Six stepped bands from sky[0] (top) through sky[1] to sky[2] (horizon).
function skyBands(sky: string[], height: number) {
  const steps = 6;
  return Array.from({ length: steps }, (_, i) => {
    const t = i / (steps - 1);
    const color = t < 0.5 ? mix(sky[0], sky[1], t * 2) : mix(sky[1], sky[2], (t - 0.5) * 2);
    return { y: Math.round((height * i) / steps), color };
  });
}
// Stepped sky gradient with one dithered row per step. Primitive props let the
// React Compiler skip it on animation ticks, when the sky hasn't changed.
function SkyBands({
  colors,
  columns,
  rows,
  height,
}: {
  colors: string;
  columns: number;
  rows: number;
  height: number;
}) {
  const bands = skyBands(colors.split(','), height);
  return bands.map((band, i) => (
    <G key={`sky-band-${i}`}>
      <Rect x={0} y={band.y} width={columns} height={rows} fill={band.color} />
      {i > 0 &&
        Array.from({ length: Math.ceil(columns / 2) }, (_, d) => (
          <Rect
            key={d}
            x={d * 2 + (i % 2)}
            y={band.y}
            width={1}
            height={1}
            fill={bands[i - 1].color}
          />
        ))}
    </G>
  ));
}
export function PixelScene({
  species = 'BLOB',
  level = 1,
  kind = 'habitat',
  height = 240,
  children,
  mini = false,
  player,
  style,
  sunrise = false,
  skyOnly = false,
  groundInset,
  hideSignposts = false,
  rainCloudBottom,
}: {
  rainCloudBottom?: number;
  sunrise?: boolean;
  skyOnly?: boolean;
  groundInset?: number;
  hideSignposts?: boolean;
  species?: Player['species'];
  level?: number;
  kind?: SceneKind;
  height?: number;
  children?: React.ReactNode;
  mini?: boolean;
  player?: Player;
  style?: ViewStyle;
}) {
  const [bounds, setBounds] = useState({ width: 320, height });
  const pixel = Math.max(1, Math.floor(bounds.width / 160));
  const columns = Math.ceil(bounds.width / pixel);
  const rows = Math.ceil(bounds.height / pixel);
  const reduced = useReducedMotion();
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (mini || reduced) return undefined;
    const timer = setInterval(() => setTick((t) => t + 1), 180);
    return () => clearInterval(timer);
  }, [mini, reduced]);
  const now = useGame((s) => s.now);
  const state = player ? status(player, now) : null;
  const hour = new Date(now).getHours();
  const night = !sunrise && (kind === 'night' || (kind === 'habitat' && (hour < 6 || hour >= 21)));
  const dusk = hour >= 17 && hour < 21;
  const morning = hour >= 6 && hour < 10;
  const exposed = state?.kind === 'exposed';
  const [exposure, setExposure] = useState({ exposed, since: now });
  if (exposure.exposed !== exposed) setExposure({ exposed, since: now });
  const weedCount = exposed ? Math.min(9, 1 + Math.floor((now - exposure.since) / 12000)) : 0;
  const stage = Math.min(3, level);
  const sky = night
    ? [c.midnight, c.nightMid, c.nightLow]
    : sunrise
      ? [c.sunrisePeach, c.sunriseYellow, c.sunriseYellow]
      : state?.kind === 'care'
        ? [c.dawn, c.gold, c.body]
        : dusk
          ? [c.pink, c.orange, c.body]
          : morning
            ? [c.dawn, c.paper, c.skyLight]
            : [c.sky, c.skyLight, c.paper];
  const moving = ['park', 'book', 'mountain'].includes(kind);
  const travel = mini ? 0 : (tick * 1.5) % 160;
  const ground = night ? c.nightGrass : species === 'CUBE' ? c.stone : c.leafLight;
  const groundRows = groundInset === undefined ? 39 : Math.round(groundInset / pixel);
  const sceneTop = rows - groundRows - 81;
  const props: PropKind[] =
    species === 'BLOB'
      ? ['mushroom', 'hammock', 'grass', 'flower', 'flower', 'fence']
      : species === 'RAT'
        ? ['signpost', 'flower', 'grass', 'flower', 'flower', 'fence']
        : ['lamp', 'stones', 'grass', 'flower', 'flower', 'fence'];
  return (
    <View
      onLayout={(e) =>
        setBounds({ width: e.nativeEvent.layout.width, height: e.nativeEvent.layout.height })
      }
      style={[
        {
          height,
          overflow: 'hidden',
          borderRadius: 14,
          borderWidth: 2,
          borderColor: c.ink,
          backgroundColor: sky[0],
        },
        style,
      ]}
    >
      <View pointerEvents="none" style={StyleSheet.absoluteFill}>
        <Svg width={columns * pixel} height={rows * pixel} viewBox={`0 0 ${columns} ${rows}`}>
          <Rect x={0} y={0} width={columns} height={rows} fill={sky[0]} />
          {(night || sunrise || skyOnly) && (
            <SkyBands
              colors={sky.join(',')}
              columns={columns}
              rows={rows}
              height={Math.max(0, rows - groundRows)}
            />
          )}
          {!skyOnly && (
            <G transform={`translate(${Math.floor((columns - 160) / 2)} ${sceneTop})`}>
              {!sunrise &&
                !night &&
                [0, 1, 2].map((i) => (
                  <Rect
                    key={`sky-${i}`}
                    x={-columns}
                    y={i * 27}
                    width={columns * 3}
                    height={30}
                    fill={sky[i]}
                  />
                ))}
              {!skyOnly && (
                <Rect x={-columns} y={81} width={columns * 3} height={rows + 81} fill={ground} />
              )}
              {!skyOnly && (
                <>
                  <Rect
                    x={-columns}
                    y={91}
                    width={columns * 3}
                    height={Math.max(0, groundRows - 10)}
                    fill={night ? c.nightMid : c.dirt}
                  />
                  <Rect
                    x={-columns}
                    y={81 + groundRows - 7}
                    width={columns * 3}
                    height={7}
                    fill={night ? c.midnight : c.wood}
                  />
                </>
              )}
              {night ? (
                <>
                  <G transform={`translate(${-Math.floor((columns - 160) / 2)} ${-sceneTop})`}>
                    <Pixels kind="moon" x={columns - 28} y={8} scale={1.4} />
                    {Array.from(
                      // Density scales with sky area so wide scenes don't look sparse.
                      { length: Math.min(70, Math.round((columns * (rows - groundRows)) / 260)) },
                      (_, i) => {
                        // Deterministic scatter (hash per star), so stars don't line up
                        // into rows on wide screens and stay put between renders.
                        const hx = Math.abs(Math.sin(i * 12.9898 + 78.233) * 43758.5453) % 1;
                        const hy = Math.abs(Math.sin(i * 39.3468 + 11.135) * 24634.6345) % 1;
                        const size = i % 9 === 0 ? 2 : 1;
                        const twinkle = i % 3 === 0 && !mini;
                        return (
                          <Rect
                            key={`star-${i}`}
                            x={Math.floor(hx * Math.max(1, columns - 30))}
                            y={3 + Math.floor(hy * Math.max(1, rows - groundRows - 14))}
                            width={size}
                            height={size}
                            fill={i % 5 === 0 ? c.dawn : c.paper}
                            opacity={
                              twinkle
                                ? 0.35 + 0.65 * Math.abs(Math.sin(tick / 9 + i))
                                : size === 2
                                  ? 0.95
                                  : 0.55 + (i % 4) * 0.12
                            }
                          />
                        );
                      },
                    )}
                  </G>
                  {kind === 'night' &&
                    Array.from({ length: 5 }, (_, i) => (
                      <G key={`night-firefly-${i}`}>
                        <Rect
                          x={18 + i * 28 + Math.round(Math.sin(tick / 25 + i) * 9)}
                          y={64 + Math.round(Math.cos(tick / 30 + i) * 16)}
                          width={4}
                          height={4}
                          fill={c.gold}
                          opacity={0.2}
                        />
                        <Rect
                          x={19 + i * 28 + Math.round(Math.sin(tick / 25 + i) * 9)}
                          y={65 + Math.round(Math.cos(tick / 30 + i) * 16)}
                          width={2}
                          height={2}
                          fill={c.dawn}
                        />
                      </G>
                    ))}
                </>
              ) : (
                kind !== 'book' && (
                  <>
                    {[0, 1].map((layer) => (
                      <G key={layer} opacity={layer === 0 ? 0.5 : 0.9}>
                        {[0, 1, 2].map((i) => (
                          <Pixels
                            key={i}
                            kind="cloud"
                            x={((i * 72 + tick * (layer === 0 ? 0.18 : 0.4)) % 210) - 30}
                            y={9 + layer * 18 + (i % 2) * 5}
                            scale={layer === 0 ? 1.2 : 1.7}
                          />
                        ))}
                      </G>
                    ))}
                  </>
                )
              )}
              {!skyOnly && (kind === 'habitat' || kind === 'night') && (
                <>
                  {species === 'BLOB' && <Pixels kind="tree" x={-16} y={-5} scale={5} />}
                  {(species === 'RAT' || kind === 'night') &&
                    Array.from({ length: Math.ceil(groundRows / 3) }, (_, i) => {
                      const halfWidth = 7 + i * 2;
                      return (
                        <G key={`dirt-path-${i}`}>
                          <Rect
                            x={77 - halfWidth}
                            y={81 + i * 3}
                            width={halfWidth * 2}
                            height={3}
                            fill={night ? c.nightEdge : c.wood}
                          />
                          <Rect
                            x={79 - halfWidth}
                            y={81 + i * 3}
                            width={halfWidth * 2 - 4}
                            height={3}
                            fill={night ? c.nightPath : c.body}
                          />
                        </G>
                      );
                    })}
                  {stage >= 3 &&
                    [0, 1, 2, 7, 8, 9].map((i) => (
                      <Pixels key={`fence-${i}`} kind="fence" x={i * 16} y={72} />
                    ))}
                  {Array.from({ length: stage * 3 }, (_, i) => (
                    <Pixels
                      key={`growth-${i}`}
                      kind={stage >= 2 && i % 2 ? 'flower' : 'grass'}
                      x={i === 2 ? 122 : i === 8 ? 136 : (i * 29 + 8) % 149}
                      y={94 + (i % 2) * 7}
                      scale={0.7}
                    />
                  ))}
                  {props
                    .slice(0, stage * 2)
                    .map((prop, i) =>
                      hideSignposts && prop === 'signpost' ? null : (
                        <Pixels
                          key={`${prop}-${[4, 127, 29, 104, 0, 135][i]}`}
                          kind={prop}
                          x={
                            [4, 127, 29, 104, 0, 135][i] +
                            (prop === 'grass' ? Math.round(Math.sin(tick / 12 + i)) : 0)
                          }
                          y={prop === 'root' ? 0 : stage === 1 ? 79 : 73 - (i % 2) * 8}
                          scale={1.2 + (i % 2) * 0.3}
                        />
                      ),
                    )}
                  {Array.from({ length: weedCount }, (_, i) => (
                    <Pixels
                      key={`weed-${i}`}
                      kind="weed"
                      x={i % 2 ? 145 - Math.floor(i / 2) * 10 : Math.floor(i / 2) * 10}
                      y={88 - (i % 3) * 4}
                      scale={1 + Math.min(0.8, (now - exposure.since) / 90000)}
                    />
                  ))}
                  {(sunrise || (!night && state?.kind === 'care')) && (
                    <>
                      <Pixels kind="sun" x={112} y={Math.max(4 - sceneTop, 61)} />
                    </>
                  )}
                  {player && player.mood < 30 && kind !== 'night' && (
                    <G
                      transform={`translate(72 ${Math.max(-sceneTop, rainCloudBottom === undefined ? 100 - Math.ceil(236 / pixel) : rainCloudBottom / pixel - 18 - sceneTop)})`}
                    >
                      <Pixels kind="raincloud" />
                      {[0, 1, 2].map((i) => (
                        <Rect
                          key={`rain-${i}`}
                          x={4 + i * 4}
                          y={13 + ((tick + i) % 3)}
                          width={1}
                          height={3}
                          fill={c.rain}
                        />
                      ))}
                    </G>
                  )}
                </>
              )}
              {((player?.mode !== undefined && player.mode !== 'awake') || kind === 'night') &&
                Array.from({ length: 7 }, (_, i) => (
                  <Rect
                    key={`firefly-${i}`}
                    x={12 + i * 21 + Math.round(Math.sin(tick / 14 + i) * 4)}
                    y={54 + ((i * 11) % 37)}
                    width={2}
                    height={2}
                    fill={c.gold}
                    opacity={0.5 + Math.abs(Math.sin(tick / 9 + i)) * 0.5}
                  />
                ))}
              {moving && (
                <G transform={`translate(${-travel} 0)`}>
                  {[0, 1, 2, 3].map((i) => (
                    <G key={i} transform={`translate(${i * 80} 0)`}>
                      {kind === 'park' ? (
                        <>
                          <Pixels kind="tree" x={2} y={33} scale={3} />
                          <Pixels kind="bench" x={49} y={73} scale={1.8} />
                        </>
                      ) : kind === 'book' ? (
                        <>
                          <Rect x={0} y={0} width={80} height={91} fill={c.root} />
                          <Pixels kind="shelf" x={8} y={4} scale={4} />
                        </>
                      ) : (
                        <>
                          <Pixels kind="mountain" x={0} y={7} scale={5} />
                          <Pixels kind="mountain" x={42} y={42} scale={3} />
                        </>
                      )}
                    </G>
                  ))}
                </G>
              )}
              {(kind === 'town' || kind === 'trail') && (
                <>
                  {[0, 1, 2].map((i) => (
                    <Pixels
                      key={`landmark-${i}`}
                      kind={
                        kind === 'town' ? 'house' : (['tree', 'library', 'mountain'] as const)[i]
                      }
                      x={8 + i * 51}
                      y={kind === 'trail' ? 12 + (i % 2) * 32 : 29 + (i % 2) * 7}
                      scale={2.5}
                    />
                  ))}
                  {Array.from({ length: 27 }, (_, i) => (
                    <Rect
                      key={`path-dot-${i}`}
                      x={14 + i * 5}
                      y={kind === 'trail' ? 69 + Math.round(Math.sin(i / 5) * 12) : 89}
                      width={2}
                      height={2}
                      fill={c.ink}
                    />
                  ))}
                  {kind === 'town' && <Pixels kind="lamp" x={74} y={73} scale={1.5} />}
                </>
              )}
              {kind === 'market' && (
                <>
                  <Rect x={9} y={11} width={142} height={4} fill={c.ink} />
                  <Rect x={13} y={14} width={4} height={101} fill={c.wood} />
                  <Rect x={143} y={14} width={4} height={101} fill={c.wood} />
                  {Array.from({ length: 10 }, (_, i) => (
                    <G key={`night-firefly-${i}`}>
                      <Rect
                        x={10 + i * 14}
                        y={15}
                        width={14}
                        height={22}
                        fill={i % 2 ? c.paper : c.error}
                      />
                      <Rect
                        x={10 + i * 14}
                        y={37}
                        width={14}
                        height={i % 2 ? 5 : 8}
                        fill={i % 2 ? c.paper : c.error}
                      />
                    </G>
                  ))}
                  <Rect x={16} y={75} width={127} height={4} fill={c.wood} />
                  <Rect x={16} y={104} width={127} height={11} fill={c.wood} />
                  <Pixels kind="frog" x={68} y={75} scale={2} />
                </>
              )}
              {kind === 'nest' && (
                <>
                  <Pixels kind="tree" x={-8} y={22} scale={5} />
                  <Pixels kind="tree" x={120} y={28} scale={4} />
                  <Rect x={16} y={82} width={128} height={26} fill={c.dirt} />
                  <Rect x={16} y={81} width={128} height={3} fill={c.ink} />
                  <Pixels kind="signpost" x={6} y={62} scale={2} />
                  <Pixels kind="grass" x={130} y={87} />
                </>
              )}
            </G>
          )}
        </Svg>
      </View>
      {children}
    </View>
  );
}
const signatureProp = (p: Player): PropKind =>
  p.id === 'bot'
    ? 'weed'
    : p.species === 'BLOB'
      ? 'mushroom'
      : p.species === 'RAT'
        ? 'signpost'
        : 'stones';

export function RaidGarden({ attacker, defender }: { attacker: Player; defender: Player }) {
  const [width, setWidth] = useState(375);
  const pixel = Math.max(1, Math.floor(width / 160));
  return (
    <View
      onLayout={(e) => setWidth(e.nativeEvent.layout.width)}
      pointerEvents="none"
      style={StyleSheet.absoluteFill}
    >
      <PixelScene
        species={defender.species}
        level={defender.level}
        // Weeds show an exposed rival's garden in real raids; Dave's practice garden
        // is always "exposed", so skip them there to keep the fighters readable.
        player={defender.id === 'bot' ? undefined : defender}
        hideSignposts
        style={{
          ...StyleSheet.absoluteFill,
          height: '100%',
          borderWidth: 0,
          borderRadius: 0,
        }}
      />
      <View style={{ position: 'absolute', left: 0, bottom: 41 * pixel }}>
        <PixelProp kind={signatureProp(attacker)} size={12 * pixel} />
      </View>
      {(signatureProp(attacker) !== 'signpost' || signatureProp(defender) !== 'signpost') && (
        <View style={{ position: 'absolute', right: 4, bottom: 39 * pixel }}>
          <PixelProp kind={signatureProp(defender)} size={16 * pixel} />
        </View>
      )}
    </View>
  );
}
