import { useEffect, useState } from 'react';
import { Image, StyleSheet, View, type ColorValue, type ViewStyle } from 'react-native';
import Animated, {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';
import { useReducedMotion } from '@/lib/motion';
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
import battleSkyDay from '@/assets/battle/sky-day.png';
import battleSkyNight from '@/assets/battle/sky-night.png';
import battleFarDay from '@/assets/battle/far-day.png';
import battleFarNight from '@/assets/battle/far-night.png';
import battleNearDay from '@/assets/battle/near-day.png';
import battleNearNight from '@/assets/battle/near-night.png';
import battlePlatform from '@/assets/battle/platform.png';
import battlePlatformNight from '@/assets/battle/platform-night.png';
import { JOURNEY, YARD_FEET, journeyLayers, journeyYards } from '@/lib/journey-assets';

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
  // The View keeps the icon in normal stacking order: on web a bare SVG paints
  // beneath absolutely positioned siblings such as pixel frames.
  return (
    <View style={{ width: size, height: size }}>
      <Svg width={size} height={size} viewBox="0 0 16 16" accessibilityLabel={kind}>
        <Pixels kind={kind} tint={tint} />
      </Svg>
    </View>
  );
}
export type SceneKind = keyof typeof sceneImages | 'night';
// Decorative frames use actual garden/world drawings at native resolution.
// The frames are drawn at the garden's density (step 7c) with a 320 px viewport and
// a 78 px ground contract (lib/scene-assets.ts): WelcomeBack and the visitor sheet
// measure the companion and ground inset against this same integer pixel scale.
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
  // The integer scale that shows the viewport and always covers the frame's width.
  const pixel = Math.max(
    1,
    Math.floor(bounds.width / sceneFrame.window),
    Math.ceil(bounds.width / sceneFrame.width),
  );
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
          borderRadius: 0,
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
// The battle field (scripts/art/battle.py): a close-up of the world in three layers,
// the sky, the far hills and treeline, and the near meadow, anchored to the stage's
// bottom edge at the battle's art pixel, plus a raised mound under each fighter. On
// entry the far and near layers settle into place at different speeds (a short,
// finite parallax in whole art pixels; none with reduced motion).
const BATTLE = { width: 216, height: 150, feet: 24, platformW: 48, platformH: 18 };
const ENTRANCE = { far: 6, near: 16, ms: 560 };
export function RaidGarden({
  pixel,
  petSize,
  inset = 12,
  region,
}: {
  attacker?: Player;
  defender?: Player;
  pixel: number;
  petSize: number;
  inset?: number;
  /** A region whose own ring this is: its sky, far land and yard (journey art) instead. */
  region?: string | null;
}) {
  const hour = new Date(useGame((s) => s.now)).getHours();
  const night = hour < 6 || hour >= 21;
  const reduced = useReducedMotion();
  const enter = useSharedValue(reduced ? 0 : 1);
  useEffect(() => {
    if (reduced) {
      enter.set(0);
      return;
    }
    enter.set(withTiming(0, { duration: ENTRANCE.ms, easing: Easing.out(Easing.cubic) }));
  }, [enter, reduced]);
  const farStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: Math.round(enter.value * ENTRANCE.far) * pixel }],
  }));
  const nearStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: Math.round(enter.value * ENTRANCE.near) * pixel }],
  }));
  const bw = BATTLE.width * pixel;
  const bh = BATTLE.height * pixel;
  const layer = {
    position: 'absolute' as const,
    bottom: 0,
    left: '50%' as const,
    marginLeft: -bw / 2,
    width: bw,
    height: bh,
  };
  const yard = region ? journeyYards[region] : undefined;
  const land = region ? journeyLayers[region] : undefined;
  if (yard && land) {
    // the region's own land, at the same art pixel, its standing line on the fighters' feet
    const jw = JOURNEY.width * pixel;
    const jh = JOURNEY.height * pixel;
    const jl = {
      position: 'absolute' as const,
      left: '50%' as const,
      marginLeft: -jw / 2,
      bottom: (BATTLE.feet - YARD_FEET) * pixel,
      width: jw,
      height: jh,
    };
    return (
      <View
        pointerEvents="none"
        // @ts-expect-error dataSet is a react-native-web prop (crisp pixel scaling via CSS)
        dataSet={{ pixel: 'true' }}
        style={[StyleSheet.absoluteFill, { backgroundColor: land.above, overflow: 'hidden' }]}
      >
        <Image source={land.sky} resizeMode="stretch" style={{ ...jl, width: jw, height: jh }} />
        <Animated.View style={[StyleSheet.absoluteFill, farStyle]}>
          <Image source={land.far} resizeMode="stretch" style={{ ...jl, width: jw, height: jh }} />
        </Animated.View>
        <Animated.View style={[StyleSheet.absoluteFill, nearStyle]}>
          <Image source={yard} resizeMode="stretch" style={{ ...jl, width: jw, height: jh }} />
        </Animated.View>
        {night && region === 'steam' && (
          <View style={[StyleSheet.absoluteFill, { backgroundColor: 'rgba(22,28,66,0.42)' }]} />
        )}
      </View>
    );
  }
  // Mounds share the art pixel and sit centred under each fighter's feet.
  const pw = BATTLE.platformW * pixel;
  const ph = BATTLE.platformH * pixel;
  const platformBottom = BATTLE.feet * pixel - 9 * pixel;
  return (
    <View
      pointerEvents="none"
      // @ts-expect-error dataSet is a react-native-web prop (crisp pixel scaling via CSS)
      dataSet={{ pixel: 'true' }}
      style={[
        StyleSheet.absoluteFill,
        { backgroundColor: night ? '#1A2142' : '#A9D3E6', overflow: 'hidden' },
      ]}
    >
      <Image
        source={night ? battleSkyNight : battleSkyDay}
        resizeMode="stretch"
        style={{ ...layer, width: bw, height: bh }}
      />
      <Animated.View style={[layer, farStyle]}>
        <Image
          source={night ? battleFarNight : battleFarDay}
          resizeMode="stretch"
          style={{ width: bw, height: bh }}
        />
      </Animated.View>
      <Animated.View style={[StyleSheet.absoluteFill, nearStyle]}>
        <Image
          source={night ? battleNearNight : battleNearDay}
          resizeMode="stretch"
          style={{ ...layer, width: bw, height: bh }}
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
      </Animated.View>
    </View>
  );
}
