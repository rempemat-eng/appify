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
}: {
  sunrise?: boolean;
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
    : sunrise || state?.kind === 'care'
      ? [c.dawn, c.gold, c.body]
      : dusk
        ? [c.pink, c.orange, c.body]
        : morning
          ? [c.dawn, c.paper, c.skyLight]
          : [c.sky, c.skyLight, c.paper];
  const moving = ['park', 'book', 'mountain'].includes(kind);
  const travel = mini ? 0 : (tick * 1.5) % 160;
  const ground = kind === 'night' ? c.night : species === 'CUBE' ? c.stone : c.leafLight;
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
          <G transform={`translate(${Math.floor((columns - 160) / 2)} ${rows - 120})`}>
            {[0, 1, 2].map((i) => (
              <Rect
                key={`sky-${i}`}
                x={-columns}
                y={i * 27}
                width={columns * 3}
                height={30}
                fill={sky[i]}
              />
            ))}
            <Rect x={-columns} y={81} width={columns * 3} height={39} fill={ground} />
            <Rect
              x={-columns}
              y={91}
              width={columns * 3}
              height={29}
              fill={kind === 'night' ? c.nightMid : c.dirt}
            />
            <Rect
              x={-columns}
              y={113}
              width={columns * 3}
              height={7}
              fill={kind === 'night' ? c.midnight : c.wood}
            />
            {night ? (
              <>
                <Pixels kind="moon" x={122} y={9} scale={1.4} />
                {Array.from({ length: 22 }, (_, i) => (
                  <Rect
                    key={`star-${i}`}
                    x={(i * 37 + 7) % 155}
                    y={(i * 19 + 4) % 67}
                    width={i % 4 === 0 ? 2 : 1}
                    height={i % 4 === 0 ? 2 : 1}
                    fill={c.paper}
                    opacity={mini ? 1 : 0.45 + 0.55 * Math.abs(Math.sin(tick / 8 + i))}
                  />
                ))}
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
            {(kind === 'habitat' || kind === 'night') && (
              <>
                {species === 'BLOB' && <Pixels kind="tree" x={-16} y={-5} scale={5} />}
                {species === 'RAT' && <Rect x={57} y={81} width={39} height={39} fill={c.body} />}
                {stage >= 3 &&
                  [0, 1, 2, 7, 8, 9].map((i) => (
                    <Pixels key={`fence-${i}`} kind="fence" x={i * 16} y={72} />
                  ))}
                {Array.from({ length: stage * 3 }, (_, i) => (
                  <Pixels
                    key={`growth-${i}`}
                    kind={stage >= 2 && i % 2 ? 'flower' : 'grass'}
                    x={(i * 29 + 8) % 149}
                    y={94 + (i % 2) * 7}
                    scale={0.7}
                  />
                ))}
                {props.slice(0, stage * 2).map((prop, i) => (
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
                ))}
                {Array.from({ length: weedCount }, (_, i) => (
                  <Pixels
                    key={`weed-${i}`}
                    kind="weed"
                    x={i % 2 ? 145 - Math.floor(i / 2) * 10 : Math.floor(i / 2) * 10}
                    y={88 - (i % 3) * 4}
                    scale={1 + Math.min(0.8, (now - exposure.since) / 90000)}
                  />
                ))}
                {(sunrise || state?.kind === 'care') && (
                  <>
                    <Rect x={0} y={0} width={160} height={95} fill={c.gold} opacity={0.12} />
                    <Pixels kind="sun" x={7} y={5} />
                  </>
                )}
                {player && player.mood < 30 && (
                  <>
                    <Pixels kind="cloud" x={64} y={12} scale={2} tint={c.rain} />
                    {[0, 1, 2, 3, 4].map((i) => (
                      <Rect
                        key={`rain-${i}`}
                        x={67 + i * 6}
                        y={35 + ((tick * 3 + i * 6) % 24)}
                        width={1}
                        height={4}
                        fill={c.rain}
                      />
                    ))}
                  </>
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
                    kind={kind === 'town' ? 'house' : (['tree', 'library', 'mountain'] as const)[i]}
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
        player={defender}
        style={{
          ...StyleSheet.absoluteFill,
          height: '100%',
          borderWidth: 0,
          borderRadius: 0,
        }}
      />
      <View style={{ position: 'absolute', left: 4, bottom: 39 * pixel }}>
        <PixelProp kind={signatureProp(attacker)} size={16 * pixel} />
      </View>
      <View style={{ position: 'absolute', right: 4, bottom: 39 * pixel }}>
        <PixelProp kind={signatureProp(defender)} size={16 * pixel} />
      </View>
    </View>
  );
}
