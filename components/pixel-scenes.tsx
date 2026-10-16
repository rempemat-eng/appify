import { useState } from 'react';
import { Image, StyleSheet, View, type ColorValue, type ViewStyle } from 'react-native';
import Svg, { G, Rect } from 'react-native-svg';
import { propPixels, sceneColors as c, type PropKind } from '@/lib/scene-art';
import { status, useGame, type Player } from '@/lib/game';
import {
  sceneFrame,
  sceneFocus,
  sceneImages,
  sceneNight,
  sceneReturn,
  sceneSkies,
  sceneSkyColors,
} from '@/lib/scene-assets';
import battleDay from '@/assets/battle/backdrop-day.png';
import battleNight from '@/assets/battle/backdrop-night.png';
import battlePlatform from '@/assets/battle/platform.png';
import battlePlatformNight from '@/assets/battle/platform-night.png';

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
export type SceneKind = keyof typeof sceneImages | 'night';
// Decorative frames use actual garden/world drawings at native resolution.
// Keep the old 160px viewport and 39px ground contract: WelcomeBack measures
// its companion and ground inset against this same integer pixel scale.
export function PixelScene({
  kind = 'habitat',
  height = 240,
  children,
  player,
  style,
  sunrise = false,
  skyOnly = false,
  groundInset,
}: {
  sunrise?: boolean;
  skyOnly?: boolean;
  groundInset?: number;
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
  const pixel = Math.max(1, Math.floor(bounds.width / sceneFrame.window));
  const now = useGame((s) => s.now);
  const hour = new Date(now).getHours();
  const night = !sunrise && (kind === 'night' || (kind === 'habitat' && (hour < 6 || hour >= 21)));
  const care = player ? status(player, now).kind === 'care' : false;
  const phase = sunrise || (care && !night) ? 'sunrise' : night ? 'night' : 'day';
  const source =
    phase === 'sunrise'
      ? sceneReturn
      : phase === 'night'
        ? sceneNight
        : sceneImages[kind === 'night' ? 'habitat' : kind];
  const ground = groundInset === undefined ? sceneFrame.ground * pixel : Math.max(0, groundInset);
  // An inset of zero puts the authored footline at the scene's bottom edge.
  // Short return scenes can reveal sky above the companion without lifting it.
  // Scenery-only banners frame their landmarks rather than the companion's
  // feet. Keep the full ground contract for characters, explicit insets and
  // the separately authored night/sunrise frames.
  const focusY =
    children == null && groundInset === undefined && !skyOnly && phase === 'day'
      ? sceneFocus[kind === 'night' ? 'habitat' : kind]
      : undefined;
  const imageBottom =
    focusY === undefined
      ? ground - sceneFrame.ground * pixel
      : Math.round(bounds.height / 2 - (sceneFrame.height - focusY) * pixel);
  const imageWidth = sceneFrame.width * pixel;
  const imageHeight = sceneFrame.height * pixel;
  // A sky-only backdrop covers a tall nap screen using an integer scale, with
  // no stretched stars, foreground props, hidden timers or animation work.
  const skyPixel = Math.max(pixel, Math.ceil(bounds.height / sceneFrame.height));
  const skyWidth = sceneFrame.width * skyPixel;
  const skyHeight = sceneFrame.height * skyPixel;
  return (
    <View
      onLayout={(event) => {
        const { width, height: measuredHeight } = event.nativeEvent.layout;
        setBounds((previous) =>
          previous.width === width && previous.height === measuredHeight
            ? previous
            : { width, height: measuredHeight },
        );
      }}
      style={[
        {
          height,
          overflow: 'hidden',
          borderRadius: 12,
          borderWidth: 2,
          borderColor: c.ink,
          backgroundColor: sceneSkyColors[phase],
        },
        style,
      ]}
    >
      <View
        pointerEvents="none"
        aria-hidden
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
        // @ts-expect-error dataSet is a react-native-web prop (nearest-neighbour pixels).
        dataSet={{ pixel: 'true' }}
        style={StyleSheet.absoluteFill}
      >
        <Image
          source={skyOnly ? sceneSkies[phase] : source}
          resizeMode="stretch"
          style={{
            position: 'absolute',
            left: Math.floor((bounds.width - (skyOnly ? skyWidth : imageWidth)) / 2),
            ...(skyOnly ? { top: 0 } : { bottom: imageBottom }),
            width: skyOnly ? skyWidth : imageWidth,
            height: skyOnly ? skyHeight : imageHeight,
          }}
        />
      </View>
      {children}
    </View>
  );
}
// DS-style battle field (scripts/art/battle.py): backdrop anchored to the stage's
// bottom edge at an integer pixel scale, plus a grassy platform under each fighter.
const BATTLE = { width: 216, height: 150, feet: 24, platformW: 64, platformH: 20 };
export function RaidGarden({
  pixel,
  petSize,
  inset = 12,
}: {
  attacker?: Player;
  defender?: Player;
  pixel: number;
  petSize: number;
  inset?: number;
}) {
  const hour = new Date(useGame((s) => s.now)).getHours();
  const night = hour < 6 || hour >= 21;
  const [stageHeight, setStageHeight] = useState(0);
  // Backdrop pixels: as big as the layout's pixel size, but small enough that the
  // horizon stays visible on short (laptop) stages.
  const bgPixel = Math.max(1, Math.min(pixel, Math.floor((stageHeight || 9999) / 100)));
  const bw = BATTLE.width * bgPixel;
  const bh = BATTLE.height * bgPixel;
  // Platforms follow the fighters' size and sit centred on their feet line.
  const pw = Math.round(petSize * 0.8);
  const ph = Math.round((pw * BATTLE.platformH) / BATTLE.platformW);
  const platformBottom = BATTLE.feet * pixel - ph * 0.62;
  return (
    <View
      pointerEvents="none"
      onLayout={(e) => setStageHeight(e.nativeEvent.layout.height)}
      // @ts-expect-error dataSet is a react-native-web prop (crisp pixel scaling via CSS)
      dataSet={{ pixel: 'true' }}
      style={[
        StyleSheet.absoluteFill,
        { backgroundColor: night ? '#1A2142' : '#A9D3E6', overflow: 'hidden' },
      ]}
    >
      <Image
        source={night ? battleNight : battleDay}
        resizeMode="stretch"
        style={{
          position: 'absolute',
          bottom: 0,
          left: '50%',
          marginLeft: -bw / 2,
          width: bw,
          height: bh,
        }}
      />
      {[
        { key: 'attacker', left: inset + petSize / 2 - pw / 2 },
        { key: 'defender', right: inset + petSize / 2 - pw / 2 },
      ].map(({ key, ...side }) => (
        <Image
          key={key}
          source={night ? battlePlatformNight : battlePlatform}
          resizeMode="stretch"
          style={{ position: 'absolute', bottom: platformBottom, width: pw, height: ph, ...side }}
        />
      ))}
    </View>
  );
}
