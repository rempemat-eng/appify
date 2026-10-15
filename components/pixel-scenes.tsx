import { useEffect, useState } from 'react';
import { StyleSheet, View, type ColorValue, type ViewStyle } from 'react-native';
import Svg, { G, Rect, Text as SvgText } from 'react-native-svg';
import { useReducedMotion } from 'react-native-reanimated';
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
}: {
  species?: Player['species'];
  level?: number;
  kind?: SceneKind;
  height?: number;
  children?: React.ReactNode;
  mini?: boolean;
  player?: Player;
  style?: ViewStyle;
}) {
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
  const night = kind === 'night' || (kind === 'habitat' && (hour < 6 || hour >= 21));
  const dusk = hour >= 17 && hour < 21;
  const morning = hour >= 6 && hour < 10;
  const burrow = kind === 'habitat' && species === 'RAT';
  const stage = Math.min(3, level);
  const sky = night
    ? [c.midnight, c.nightMid, c.nightLow]
    : burrow
      ? [c.ink, c.root, c.dirt]
      : state?.kind === 'care'
        ? [c.dawn, c.gold, c.body]
        : dusk
          ? [c.pink, c.orange, c.body]
          : morning
            ? [c.dawn, c.paper, c.skyLight]
            : [c.sky, c.skyLight, c.paper];
  const moving = ['park', 'book', 'mountain'].includes(kind);
  const travel = mini ? 0 : (tick * 1.5) % 160;
  const ground =
    kind === 'night' ? c.night : species === 'CUBE' ? c.stone : burrow ? c.dirt : c.leafLight;
  const props: PropKind[] =
    species === 'BLOB'
      ? ['grass', 'mushroom', 'grass', 'mushroom', 'grass', 'tree']
      : species === 'RAT'
        ? ['root', 'lamp', 'cable', 'root', 'cable', 'lamp']
        : ['rock', 'crystal', 'grass', 'rock', 'crystal', 'rock'];
  return (
    <View
      style={[
        { height, overflow: 'hidden', borderWidth: 2, borderColor: c.ink, backgroundColor: sky[0] },
        style,
      ]}
    >
      <View pointerEvents="none" style={StyleSheet.absoluteFill}>
        <Svg width="100%" height="100%" viewBox="0 0 160 120" preserveAspectRatio="none">
          {[0, 1, 2].map((i) => (
            <Rect key={i} x={0} y={i * 27} width={160} height={30} fill={sky[i]} />
          ))}
          <Rect x={0} y={81} width={160} height={39} fill={ground} />
          <Rect
            x={0}
            y={91}
            width={160}
            height={29}
            fill={kind === 'night' ? c.nightMid : burrow ? c.root : c.dirt}
          />
          <Rect
            x={0}
            y={113}
            width={160}
            height={7}
            fill={kind === 'night' ? c.midnight : c.wood}
          />
          {night ? (
            <>
              <Pixels kind="moon" x={122} y={9} scale={1.4} />
              {Array.from({ length: 22 }, (_, i) => (
                <Rect
                  key={i}
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
                  <G key={i}>
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
            !burrow &&
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
          {kind === 'habitat' && (
            <>
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
              {burrow && (
                <>
                  <Pixels kind="root" x={26} y={0} scale={2} />
                  <Pixels kind="root" x={119} y={0} scale={1.5} />
                </>
              )}
              {state?.kind === 'exposed' &&
                !mini &&
                [0, 1, 2].map((i) => {
                  const y = (tick * 2 + i * 32) % 108;
                  const pop = y > 93;
                  return (
                    <G key={i}>
                      <Rect
                        x={12 + i * 59 - (pop ? 3 : 0)}
                        y={y}
                        width={pop ? 20 : 14}
                        height={pop ? 2 : 13}
                        fill={c.red}
                      />
                      {!pop && (
                        <SvgText
                          x={19 + i * 59}
                          y={y + 10}
                          fontSize={10}
                          fontWeight="bold"
                          textAnchor="middle"
                          fill={c.paper}
                        >
                          1
                        </SvgText>
                      )}
                    </G>
                  );
                })}
              {state?.kind === 'care' && (
                <>
                  <Rect x={0} y={0} width={160} height={95} fill={c.gold} opacity={0.12} />
                  <Pixels kind="sun" x={7} y={5} />
                  <SvgText x={26} y={17} fill={c.ink} fontSize={8}>
                    {state.left}
                  </SvgText>
                </>
              )}
              {player && player.mood < 30 && (
                <>
                  <Pixels kind="cloud" x={64} y={12} scale={2} tint={c.rain} />
                  {[0, 1, 2, 3, 4].map((i) => (
                    <Rect
                      key={i}
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
                  key={i}
                  kind={kind === 'town' ? 'house' : (['tree', 'library', 'mountain'] as const)[i]}
                  x={8 + i * 51}
                  y={kind === 'trail' ? 12 + (i % 2) * 32 : 29 + (i % 2) * 7}
                  scale={2.5}
                />
              ))}
              {Array.from({ length: 27 }, (_, i) => (
                <Rect
                  key={i}
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
                <G key={i}>
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
              <Pixels kind="nest" x={31} y={65} scale={6} />
            </>
          )}
        </Svg>
      </View>
      {children}
    </View>
  );
}
export function BattlePad({ species }: { species: Player['species'] }) {
  const fill = species === 'BLOB' ? c.moss : species === 'RAT' ? c.dirt : c.slate;
  return (
    <Svg width={96} height={20} viewBox="0 0 48 10">
      {[0, 1, 2, 3, 4].map((i) => (
        <Rect
          key={i}
          x={Math.abs(2 - i) * 5 + 1}
          y={i * 2}
          width={46 - Math.abs(2 - i) * 10}
          height={2}
          fill={i === 4 ? c.ink : fill}
        />
      ))}
    </Svg>
  );
}
