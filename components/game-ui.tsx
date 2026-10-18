import { useEffect, useRef, useState } from 'react';
import {
  PixelRatio,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type TextProps,
  type TextStyle,
  type ViewStyle,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, {
  cancelAnimation,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import Svg, { Rect } from 'react-native-svg';
import * as Haptics from 'expo-haptics';
import { useReducedMotion } from '@/lib/motion';
import { cozy as c } from '@/lib/cozy';
import { CozyBackground } from '@/components/cozy-ui';
import { FrameShape, frameTones, mixColor, usePixelUnit } from '@/components/pixel-frame';
import { Pulse } from '@/components/pixel-feedback';
import { playSound } from '@/lib/sound';
import { status, clock, useGame, type Player } from '@/lib/game';
import { visitorPixels } from '@/lib/visitor-art';
import { isVisitorId, visitorInfo } from '@/lib/visitors';
import { GROUND_SHADOW, petPixels } from '@/lib/pet-art';
import { grasslings, growthStage } from '@/lib/grasslings';
import { gameColumn, gameLayout, hotbarClearance, hudClearance, touchReach } from '@/lib/layout';
import { PixelIcon } from '@/components/pixel-icon';

export function PixelText({ style, ...props }: TextProps) {
  const display = (StyleSheet.flatten(style)?.fontSize ?? 15) >= 16;
  return (
    <Text
      {...props}
      style={[
        styles.text,
        style,
        { fontFamily: display ? 'PressStart2P_400Regular' : 'PixelifySans_700Bold' },
      ]}
    />
  );
}
export function PixelButton({
  label,
  onPress,
  disabled = false,
  light = false,
  small = false,
  danger = false,
  gold = false,
  energyCost,
  supportingText,
  onLongPress,
  onDisabledPress,
  haptic = true,
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  light?: boolean;
  small?: boolean;
  danger?: boolean;
  gold?: boolean;
  energyCost?: number;
  supportingText?: string;
  onLongPress?: () => void;
  onDisabledPress?: () => void;
  haptic?: boolean;
}) {
  const u = usePixelUnit();
  const [pressed, setPressed] = useState(false);
  const tone =
    frameTones[
      disabled ? 'disabled' : danger ? 'danger' : gold ? 'gold' : light ? 'paper' : 'leaf'
    ];
  const depth = 2 * u;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}
      aria-disabled={disabled}
      disabled={disabled && !onDisabledPress}
      onPressIn={() => setPressed(true)}
      onPressOut={() => setPressed(false)}
      onPress={() => {
        if (disabled) {
          onDisabledPress?.();
          return;
        }
        if (haptic) {
          void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          playSound('tap');
        }
        onPress();
      }}
      onLongPress={onLongPress}
      style={{ paddingBottom: depth }}
    >
      <View
        pointerEvents="none"
        style={{ position: 'absolute', left: 0, right: 0, top: depth, bottom: 0 }}
      >
        <FrameShape
          tone={{ ...tone, fill: tone.base, light: tone.base, dark: tone.base }}
          unit={u}
          bevel={false}
        />
      </View>
      <View
        style={{
          minHeight: small ? 44 : 52,
          paddingHorizontal: small ? 4 * u : 9 * u,
          paddingVertical: 4 * u,
          alignItems: 'center',
          justifyContent: 'center',
          transform: [{ translateY: pressed && !disabled ? depth : 0 }],
        }}
      >
        <FrameShape tone={tone} unit={u} />
        <Text
          numberOfLines={2}
          style={{
            fontFamily: 'PixelifySans_700Bold',
            color: disabled ? '#6E6457' : c.buttonInk,
            fontSize: small ? 13 : 16,
            lineHeight: small ? 16 : 20,
            textAlign: 'center',
            letterSpacing: 0.5,
          }}
        >
          {label}
        </Text>
        {supportingText && (
          <Text
            style={{
              fontFamily: 'PixelifySans_500Medium',
              color: c.buttonInk,
              fontSize: 12,
              textAlign: 'center',
            }}
          >
            {supportingText}
          </Text>
        )}
        {energyCost !== undefined && <EnergyPips value={energyCost} />}
      </View>
    </Pressable>
  );
}
/** Energy as three bolts from the icon set; spent ones are greyed. */
export function EnergyPips({ value }: { value: number }) {
  return (
    <View
      accessibilityLabel={`${value} energy`}
      style={{ flexDirection: 'row', gap: 5, marginTop: 5 }}
    >
      {[0, 1, 2].map((pip) => (
        <PixelIcon key={pip} name="energy" size={16} muted={pip >= value} />
      ))}
    </View>
  );
}
export function Pet({
  species = 'BLOB',
  size = 192,
  level = 1,
  facing = 'right',
  hat = null,
  grumpy = false,
  sleeping = false,
  walking = false,
  bob = true,
  hit = 0,
  attack = 0,
  victory = false,
  slumped = false,
  dave = false,
  yawning = false,
  visitor = null,
  onPress,
  actionLabel,
  groundShadow = true,
  curled = false,
  active = true,
  gardenPose,
  decorative = false,
}: {
  /** a picture only (HUD portraits): no button, no greeting */
  decorative?: boolean;
  active?: boolean;
  gardenPose?: { id: number; kind: 'nestle' | 'sniff' | 'ponder' };
  curled?: boolean;
  groundShadow?: boolean;
  species?: Player['species'];
  size?: number;
  level?: number;
  facing?: 'left' | 'right';
  hat?: string | null;
  grumpy?: boolean;
  sleeping?: boolean;
  walking?: boolean;
  bob?: boolean;
  hit?: number;
  attack?: number;
  victory?: boolean;
  slumped?: boolean;
  dave?: boolean;
  yawning?: boolean;
  visitor?: string | null;
  onPress?: () => void;
  actionLabel?: string;
}) {
  const reduced = useReducedMotion();
  const gardenPoseId = gardenPose?.id;
  const gardenPoseKind = gardenPose?.kind;
  const canAnimate = active && !reduced;
  const canPose = !!gardenPose && active && !walking && !sleeping && !slumped;
  const canWalk = canAnimate && walking && !sleeping && !slumped;
  const canIdle = canAnimate && bob && !sleeping && !walking && !slumped && !canPose;
  // One art pixel is a whole number of device pixels (coherence plan, step 6), so a
  // garden companion sits on the same grid as the world around it.
  const dpr = PixelRatio.get();
  const pixelStep = Math.max(1, Math.round((size / 32) * dpr)) / dpr;
  const scaledSize = pixelStep * 32;
  const y = useSharedValue(0);
  const x = useSharedValue(0);
  const patY = useSharedValue(0);
  const walkSettle = useSharedValue(0);
  const poseX = useSharedValue(0);
  const poseY = useSharedValue(0);
  const [breath, setBreath] = useState(false);
  const [walkFrame, setWalkFrame] = useState(0);
  const [blink, setBlink] = useState(false);
  const [idle, setIdle] = useState<'rest' | 'yawn' | 'look'>('rest');
  const [heart, setHeart] = useState(0);
  const [flashState, setFlashState] = useState({ hit, flashing: false });
  const motionKey = `${canAnimate}-${walking}-${sleeping}-${slumped}-${bob}`;
  const [motionMode, setMotionMode] = useState(motionKey);
  const seenMotion = useRef({ hit: 0, attack: 0, victory: false });
  const wasWalking = useRef(false);
  const seenGardenPose = useRef<string | null>(null);
  if (motionMode !== motionKey) {
    setMotionMode(motionKey);
    setBreath(false);
    setWalkFrame(0);
    setBlink(false);
    setIdle('rest');
    setFlashState({ hit, flashing: false });
    if (!active) setHeart(0);
  }
  if (flashState.hit !== hit) setFlashState({ hit, flashing: hit !== 0 && canAnimate });
  useEffect(() => {
    if (canAnimate) return;
    cancelAnimation(x);
    cancelAnimation(y);
    cancelAnimation(patY);
    cancelAnimation(walkSettle);
    x.set(0);
    y.set(0);
    patY.set(0);
    walkSettle.set(0);
  }, [canAnimate, x, y, patY, walkSettle]);
  useEffect(
    () => () => {
      cancelAnimation(patY);
      patY.set(0);
    },
    [patY],
  );
  useEffect(() => {
    cancelAnimation(poseX);
    cancelAnimation(poseY);
    poseX.set(0);
    poseY.set(0);
    const key =
      gardenPoseId !== undefined && gardenPoseKind ? `${gardenPoseId}-${gardenPoseKind}` : null;
    const unseen = seenGardenPose.current !== key;
    seenGardenPose.current = key;
    if (unseen && canPose && canAnimate && gardenPoseKind) {
      // The body and its hat stay rigid. Native-pixel rounding below makes
      // anticipation, one held action and the settle distinct little poses.
      const direction = gardenPoseKind === 'ponder' ? -1 : 1;
      const nestle = gardenPoseKind === 'nestle';
      poseX.set(
        withSequence(
          withTiming(nestle ? 0 : -direction, { duration: 120 }),
          withTiming(nestle ? 0 : -direction, { duration: 120 }),
          withTiming(nestle ? 0 : direction, { duration: 240 }),
          withTiming(nestle ? 0 : direction, { duration: 720 }),
          withTiming(0, { duration: 240 }),
        ),
      );
      poseY.set(
        withSequence(
          withTiming(nestle ? 0 : -1, { duration: 120 }),
          withTiming(nestle ? 0 : -1, { duration: 120 }),
          withTiming(gardenPoseKind === 'ponder' ? 0 : 1, { duration: 240 }),
          withTiming(gardenPoseKind === 'ponder' ? 0 : 1, { duration: 720 }),
          withTiming(0, { duration: 240 }),
        ),
      );
    }
    return () => {
      cancelAnimation(poseX);
      cancelAnimation(poseY);
      poseX.set(0);
      poseY.set(0);
    };
  }, [gardenPoseId, gardenPoseKind, canPose, canAnimate, poseX, poseY]);
  useEffect(() => {
    if (!canIdle) return undefined;
    // Slow pixel breathing, with separate phases for the garden's companions.
    let timer: ReturnType<typeof setInterval> | undefined;
    const start = setTimeout(
      () => {
        setBreath(true);
        timer = setInterval(() => setBreath((v) => !v), 1400);
      },
      300 + Math.random() * 1000,
    );
    return () => {
      clearTimeout(start);
      if (timer) clearInterval(timer);
    };
  }, [canIdle]);
  useEffect(() => {
    if (!canAnimate || sleeping) return undefined;
    let timer: ReturnType<typeof setTimeout>;
    let close: ReturnType<typeof setTimeout>;
    function schedule() {
      timer = setTimeout(
        () => {
          setBlink(true);
          close = setTimeout(() => setBlink(false), 160);
          schedule();
        },
        3000 + Math.random() * 2000,
      );
    }
    schedule();
    return () => {
      clearTimeout(timer);
      clearTimeout(close);
    };
  }, [canAnimate, sleeping]);
  useEffect(() => {
    if (!canIdle) return undefined;
    let timer: ReturnType<typeof setTimeout>;
    let reset: ReturnType<typeof setTimeout>;
    function schedule() {
      timer = setTimeout(
        () => {
          setIdle(Math.random() > 0.5 ? 'yawn' : 'look');
          reset = setTimeout(() => setIdle('rest'), 900);
          schedule();
        },
        10000 + Math.random() * 5000,
      );
    }
    schedule();
    return () => {
      clearTimeout(timer);
      clearTimeout(reset);
    };
  }, [canIdle]);
  useEffect(() => {
    const changed = seenMotion.current.victory !== victory;
    seenMotion.current.victory = victory;
    if (changed && victory && canAnimate)
      y.set(withSequence(withTiming(-12, { duration: 160 }), withTiming(0, { duration: 180 })));
    return () => {
      cancelAnimation(y);
      y.set(0);
    };
  }, [victory, canAnimate, y]);
  useEffect(() => {
    if (!heart || !active) return undefined;
    const timer = setTimeout(() => setHeart(0), 600);
    return () => clearTimeout(timer);
  }, [heart, active]);
  useEffect(() => {
    const stopping = wasWalking.current && !canWalk;
    wasWalking.current = canWalk;
    cancelAnimation(walkSettle);
    walkSettle.set(0);
    if (!canWalk) {
      if (stopping && canAnimate && !sleeping && !slumped)
        walkSettle.set(
          withSequence(withTiming(1, { duration: 0 }), withTiming(0, { duration: 120 })),
        );
      return () => {
        cancelAnimation(walkSettle);
        walkSettle.set(0);
      };
    }
    const timer = setInterval(() => setWalkFrame((frame) => (frame + 1) % 4), 120);
    return () => {
      clearInterval(timer);
      cancelAnimation(walkSettle);
      walkSettle.set(0);
    };
  }, [canWalk, canAnimate, sleeping, slumped, walkSettle]);
  useEffect(() => {
    const changed = seenMotion.current.hit !== hit;
    seenMotion.current.hit = hit;
    if (!changed || !hit || !canAnimate) return undefined;
    const timer = setTimeout(() => setFlashState({ hit, flashing: false }), 34);
    x.set(
      withSequence(
        withTiming(facing === 'right' ? -4 : 4, { duration: 50 }),
        withTiming(0, { duration: 100 }),
      ),
    );
    return () => {
      clearTimeout(timer);
      cancelAnimation(x);
      x.set(0);
    };
  }, [hit, canAnimate, x, facing]);
  useEffect(() => {
    const changed = seenMotion.current.attack !== attack;
    seenMotion.current.attack = attack;
    if (changed && attack && canAnimate)
      x.set(
        withSequence(
          withTiming(facing === 'right' ? 8 : -8, { duration: 100 }),
          withTiming(0, { duration: 160 }),
        ),
      );
    return () => {
      cancelAnimation(x);
      x.set(0);
    };
  }, [attack, facing, canAnimate, x]);
  const motion = useAnimatedStyle(() => ({
    transform: [
      {
        translateY: canAnimate
          ? Math.round(y.value) + Math.round(patY.value + walkSettle.value) * pixelStep
          : 0,
      },
      { translateX: canAnimate ? Math.round(x.value) : 0 },
    ],
  }));
  const visitorId = isVisitorId(visitor) ? visitor : null;
  const petLabel = visitorId ? visitorInfo(visitorId).name : grasslings[species].name;
  const pixels = visitorId
    ? visitorPixels(visitorId, hat, sleeping || (canAnimate && blink), groundShadow)
    : petPixels(
        species,
        level,
        hat,
        sleeping || (canAnimate && (blink || (canIdle && idle === 'yawn'))) || yawning,
        grumpy,
        dave,
        groundShadow,
      );
  // Hats and head foliage move with the body. Avoid lifting a sprite whose art
  // already touches the top of its 32px frame; its silhouette must stay intact.
  const headroom = pixels.every((pixel) => pixel.y > 0);
  const passing = walkFrame === 1 || walkFrame === 3;
  const bodyLift = canWalk && passing && headroom ? -1 : 0;
  const bodyBounds = pixels.reduce(
    (bounds, pixel) =>
      pixel.y >= 27
        ? bounds
        : {
            left: Math.min(bounds.left, pixel.x),
            right: Math.max(bounds.right, pixel.x),
            top: Math.min(bounds.top, pixel.y),
          },
    { left: 31, right: 0, top: 31 },
  );
  // Where each art pixel is drawn this frame. Walking is a four-frame cycle: a foot
  // steps forward and lifts on the contact frames, the body rises a pixel on the
  // passing frames, and the head (ears, leaves, hat) follows one frame late, so the
  // body squashes and stretches a little and the head bobs after it (secondary motion).
  // The whole body leans a pixel into the step on contact.
  const headLine = bodyBounds.top + 7;
  const headLift = canWalk && (walkFrame === 0 || walkFrame === 2) && headroom ? -1 : 0;
  const lean = canWalk && (walkFrame === 0 || walkFrame === 2) ? 1 : 0;
  const place = (rx: number, ry: number, color: string) => {
    const shadow = groundShadow && ry >= 29 && color === GROUND_SHADOW;
    const foot = !shadow && ry >= 27 && rx >= 6 && rx <= 27;
    const leftStep = canWalk && walkFrame === 0 && rx < 17;
    const rightStep = canWalk && walkFrame === 2 && rx >= 17;
    const stepping = foot && (leftStep || rightStep);
    const head = !foot && !shadow && ry < headLine;
    const drawX = stepping ? rx + (leftStep ? -1 : 1) : !foot && !shadow && head ? rx + lean : rx;
    const drawY =
      curled && sleeping
        ? 7 + Math.floor((ry * 24) / 32)
        : canWalk && !shadow
          ? ry + (head ? headLift : bodyLift) - (stepping ? 1 : 0)
          : canIdle && breath && ry >= 16 && !shadow
            ? ry - 1
            : ry;
    return { drawX, drawY };
  };
  // A puff of dust kicked up behind the stepping foot (two pale pixels, then gone).
  const dust =
    canWalk && groundShadow && (walkFrame === 0 || walkFrame === 2)
      ? walkFrame === 0
        ? [
            { x: 4, y: 29 },
            { x: 3, y: 28 },
          ]
        : [
            { x: 5, y: 30 },
            { x: 3, y: 29 },
          ]
      : [];
  const poseMotion = useAnimatedStyle(() => {
    const staticX = gardenPoseKind === 'nestle' ? 0 : gardenPoseKind === 'ponder' ? -1 : 1;
    const staticY = gardenPoseKind === 'ponder' ? 0 : 1;
    const direction = facing === 'left' ? -1 : 1;
    const desiredX = canPose ? (reduced ? staticX : Math.round(poseX.value)) * direction : 0;
    const desiredY = canPose ? (reduced ? staticY : Math.round(poseY.value)) : 0;
    const minX = facing === 'left' ? -(31 - bodyBounds.right) : -bodyBounds.left;
    const maxX = facing === 'left' ? bodyBounds.left : 31 - bodyBounds.right;
    return {
      transform: [
        { translateX: Math.min(maxX, Math.max(minX, desiredX)) * pixelStep },
        { translateY: Math.min(1, Math.max(-bodyBounds.top, desiredY)) * pixelStep },
      ],
    };
  });
  return (
    <Animated.View
      accessibilityLabel={`${dave ? 'DOOMSCROLL DAVE weed creature' : `${petLabel} ${growthStage(level)} Grassling`}${slumped ? ', wilted' : ''}${sleeping ? ', sleeping' : ''}`}
      style={[{ width: scaledSize, height: scaledSize }, motion]}
    >
      {decorative ? (
        <View style={{ backgroundColor: c.transparent }}>
          {heart > 0 && (
            <View
              pointerEvents="none"
              style={{ position: 'absolute', top: -16, left: scaledSize / 2 - 16, zIndex: 4 }}
            >
              <PixelIcon name="heart" size={32} />
            </View>
          )}
          <Animated.View style={poseMotion}>
            <Svg
              width={scaledSize}
              height={scaledSize}
              viewBox="0 0 32 32"
              style={{
                backgroundColor: c.transparent,
                transform: [
                  { scaleX: facing === 'left' ? -1 : 1 },
                  { translateY: slumped ? 8 : 0 },
                  { translateX: canIdle && idle === 'look' ? 3 : 0 },
                ],
              }}
            >
              {pixels
                .filter((pixel) => !canPose || pixel.y < 27)
                .map(({ x: rx, y: ry, color }) => {
                  const { drawX, drawY } = place(rx, ry, color);
                  return (
                    <Rect
                      key={`${rx}-${ry}`}
                      x={drawX}
                      y={drawY}
                      width={1}
                      height={1}
                      fill={
                        flashState.flashing && canAnimate
                          ? c.flash
                          : slumped
                            ? color === c.ink || color === c.night
                              ? c.night
                              : c.wilt
                            : color
                      }
                    />
                  );
                })}
              {dust.map((d) => (
                <Rect
                  key={`dust-${d.x}-${d.y}`}
                  x={d.x}
                  y={d.y}
                  width={1}
                  height={1}
                  fill="#E8DCC0"
                  opacity={0.7}
                />
              ))}
              {((canIdle && idle === 'yawn') || yawning) && (
                <Rect x={21} y={22} width={3} height={3} fill={c.ink} />
              )}
            </Svg>
          </Animated.View>
          {canPose && (
            <Svg
              width={scaledSize}
              height={scaledSize}
              viewBox="0 0 32 32"
              pointerEvents="none"
              style={{
                position: 'absolute',
                left: 0,
                top: 0,
                transform: [{ scaleX: facing === 'left' ? -1 : 1 }],
              }}
            >
              {pixels
                .filter((pixel) => pixel.y >= 27)
                .map(({ x: rx, y: ry, color }) => (
                  <Rect key={`${rx}-${ry}`} x={rx} y={ry} width={1} height={1} fill={color} />
                ))}
            </Svg>
          )}
        </View>
      ) : (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={actionLabel ?? `Greet ${petLabel}`}
          accessibilityState={{ disabled: !active }}
          disabled={!active}
          // at least 44 px to tap, even when the companion is drawn small
          style={{ backgroundColor: c.transparent, ...touchReach(scaledSize) }}
          onPress={() => {
            if (!active) return;
            cancelAnimation(patY);
            patY.set(0);
            setHeart((count) => count + 1);
            if (canAnimate)
              patY.set(
                withSequence(
                  withTiming(1, { duration: 70 }),
                  withTiming(-3, { duration: 110 }),
                  withTiming(1, { duration: 110 }),
                  withTiming(0, { duration: 90 }),
                ),
              );
            if (onPress) {
              onPress();
              return;
            }
            void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          }}
        >
          {heart > 0 && (
            <View
              pointerEvents="none"
              style={{ position: 'absolute', top: -16, left: scaledSize / 2 - 16, zIndex: 4 }}
            >
              <PixelIcon name="heart" size={32} />
            </View>
          )}
          <Animated.View style={poseMotion}>
            <Svg
              width={scaledSize}
              height={scaledSize}
              viewBox="0 0 32 32"
              style={{
                backgroundColor: c.transparent,
                transform: [
                  { scaleX: facing === 'left' ? -1 : 1 },
                  { translateY: slumped ? 8 : 0 },
                  { translateX: canIdle && idle === 'look' ? 3 : 0 },
                ],
              }}
            >
              {pixels
                .filter((pixel) => !canPose || pixel.y < 27)
                .map(({ x: rx, y: ry, color }) => {
                  const { drawX, drawY } = place(rx, ry, color);
                  return (
                    <Rect
                      key={`${rx}-${ry}`}
                      x={drawX}
                      y={drawY}
                      width={1}
                      height={1}
                      fill={
                        flashState.flashing && canAnimate
                          ? c.flash
                          : slumped
                            ? color === c.ink || color === c.night
                              ? c.night
                              : c.wilt
                            : color
                      }
                    />
                  );
                })}
              {dust.map((d) => (
                <Rect
                  key={`dust-${d.x}-${d.y}`}
                  x={d.x}
                  y={d.y}
                  width={1}
                  height={1}
                  fill="#E8DCC0"
                  opacity={0.7}
                />
              ))}
              {((canIdle && idle === 'yawn') || yawning) && (
                <Rect x={21} y={22} width={3} height={3} fill={c.ink} />
              )}
            </Svg>
          </Animated.View>
          {canPose && (
            <Svg
              width={scaledSize}
              height={scaledSize}
              viewBox="0 0 32 32"
              pointerEvents="none"
              style={{
                position: 'absolute',
                left: 0,
                top: 0,
                transform: [{ scaleX: facing === 'left' ? -1 : 1 }],
              }}
            >
              {pixels
                .filter((pixel) => pixel.y >= 27)
                .map(({ x: rx, y: ry, color }) => (
                  <Rect key={`${rx}-${ry}`} x={rx} y={ry} width={1} height={1} fill={color} />
                ))}
            </Svg>
          )}
        </Pressable>
      )}
    </Animated.View>
  );
}
export function FloatingZ() {
  const y = useSharedValue(0);
  const reduced = useReducedMotion();
  useEffect(() => {
    y.set(
      reduced
        ? 0
        : withRepeat(
            withSequence(withTiming(-10, { duration: 1500 }), withTiming(0, { duration: 0 })),
            -1,
          ),
    );
    return () => cancelAnimation(y);
  }, [reduced, y]);
  const motion = useAnimatedStyle(() => ({
    opacity: 1 + y.value / 16,
    transform: [{ translateY: y.value }],
  }));
  return (
    <Animated.View pointerEvents="none" style={motion}>
      <Text style={{ fontFamily: 'PixelifySans_700Bold', color: c.paper, fontSize: 20 }}>
        z z z
      </Text>
    </Animated.View>
  );
}
export function PixelEgg({
  cracking = false,
  color = c.body,
  size = 96,
}: {
  cracking?: boolean;
  color?: string;
  size?: number;
}) {
  const reduced = useReducedMotion();
  const value = useSharedValue(0);
  useEffect(() => {
    value.set(
      reduced
        ? 0
        : withRepeat(
            withSequence(
              withTiming(-5, { duration: cracking ? 70 : 300 }),
              withTiming(5, { duration: cracking ? 70 : 300 }),
            ),
            -1,
          ),
    );
  }, [cracking, reduced, value]);
  const motion = useAnimatedStyle(() => ({ transform: [{ rotate: `${value.value}deg` }] }));
  const rows = [
    '....KKKK....',
    '..KKBBBBKK..',
    '.KBBBBBBBBK.',
    '.KBBBKKBBBK.',
    'KBBBBKKBBBBK',
    'KBBBBBBBBBBK',
    'KBBKKBBBBBBK',
    'KBBKKBBBBBBK',
    'KBBBBBBBBBBK',
    '.KBBBBBBBBK.',
    '..KKBBBBKK..',
    '....KKKK....',
  ];
  const pixels = rows.flatMap((row, y) =>
    Array.from(row, (p, x) => ({ x, y, p })).filter((pixel) => pixel.p !== '.'),
  );
  return (
    <Animated.View style={motion}>
      <Svg width={size} height={size} viewBox="0 0 12 12">
        {pixels.map((pixel) => (
          <Rect
            key={`${pixel.x}-${pixel.y}`}
            x={pixel.x}
            y={pixel.y}
            width={1}
            height={1}
            fill={pixel.p === 'K' ? c.ink : color}
          />
        ))}
        {cracking && <Rect x={6} y={1} width={1} height={10} fill={c.ink} />}
      </Svg>
    </Animated.View>
  );
}
export function Meter({
  value,
  max = 100,
  height = 12,
  color = c.positive,
}: {
  value: number;
  max?: number;
  height?: number;
  color?: string;
}) {
  const u = usePixelUnit();
  const share = max > 0 ? Math.max(0, Math.min(1, value / max)) : 0;
  // A dark pixel track with a lit top row on the fill, like the HUD's bars.
  return (
    <View
      accessibilityRole="progressbar"
      accessibilityValue={{ min: 0, max, now: value }}
      style={{ height, padding: u, flexDirection: 'row', backgroundColor: '#3B2F2A' }}
    >
      <View style={{ width: `${Math.round(share * 100)}%`, backgroundColor: color }}>
        <View style={{ height: u, backgroundColor: mixColor(color, c.highlight, 0.4) }} />
      </View>
      <View style={{ flex: 1, backgroundColor: '#8C7A64' }} />
    </View>
  );
}
export function StatusChip({ player, compact = false }: { player: Player; compact?: boolean }) {
  const now = useGame((s) => s.now);
  const state = status(player, now);
  const care = state.kind === 'care';
  const color =
    state.kind === 'exposed'
      ? c.danger
      : care
        ? c.amber
        : player.mode !== 'awake'
          ? c.night
          : c.terracotta;
  const label = `${compact && care ? 'CARE' : state.label}${care ? ` ${clock(state.left)}` : ''}`;
  return (
    <Pulse
      active={state.kind === 'exposed'}
      color={c.paper}
      duration={1400}
      style={{
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
        paddingHorizontal: compact ? 6 : 10,
        paddingVertical: compact ? 6 : 8,
        minHeight: compact ? 44 : undefined,
        maxWidth: '100%',
        borderRadius: 0,
        backgroundColor: color,
      }}
    >
      <PixelIcon name="shield" size={16} />
      <Text
        numberOfLines={1}
        style={{
          fontFamily: 'PixelifySans_700Bold',
          fontSize: 11,
          lineHeight: 17,
          flexShrink: 1,
          color: care ? c.buttonInk : c.paper,
        }}
      >
        {label}
      </Text>
    </Pulse>
  );
}
export function Page({ children, style }: { children: React.ReactNode; style?: ViewStyle }) {
  const insets = useSafeAreaInsets();
  return (
    <View style={{ flex: 1 }}>
      <CozyBackground />
      <ScrollView
        contentContainerStyle={[
          {
            ...gameColumn,
            padding: gameLayout.gutter,
            paddingTop: hudClearance(insets.top),
            paddingBottom: hotbarClearance(insets.bottom),
            gap: 12,
          },
          style,
        ]}
      >
        {children}
      </ScrollView>
    </View>
  );
}
export const styles = {
  text: { fontFamily: 'PixelifySans_700Bold', color: c.ink, fontSize: 15, lineHeight: 22 },
  title: { fontSize: 20, lineHeight: 32 },
  section: { gap: 12 },
} satisfies Record<string, TextStyle | ViewStyle>;
