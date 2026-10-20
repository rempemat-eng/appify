import { lazy, Suspense, useCallback, useEffect, useState } from 'react';
import {
  Image,
  PixelRatio,
  Pressable,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from 'react-native';
import { Stack, useIsFocused } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAppActive } from '@/lib/app-active';
import { useReducedMotion } from '@/lib/motion';
import { pixelScale } from '@/lib/pixel-scale';
import {
  clampCamera,
  summarizeCadence,
  tileLayout,
  visibleTiles,
  type Point,
  type ProbeTile,
} from '@/lib/native-pixels';

// The RN baseline can run before initializing Skia. Reload the app between modes
// for profiler comparisons: switching alone does not clear the decoded caches.
const NativePixelTiles = lazy(() => import('./native-pixel-tiles'));
const tiles: readonly ProbeTile[] = [
  { id: '0,2', x: 0, y: 0, source: require('@/assets/native-pixels/t_0_2.png') },
  { id: '1,2', x: 256, y: 0, source: require('@/assets/native-pixels/t_1_2.png') },
  { id: '2,2', x: 512, y: 0, source: require('@/assets/native-pixels/t_2_2.png') },
  { id: '0,3', x: 0, y: 256, source: require('@/assets/native-pixels/t_0_3.png') },
  { id: '1,3', x: 256, y: 256, source: require('@/assets/native-pixels/t_1_3.png') },
  { id: '2,3', x: 512, y: 256, source: require('@/assets/native-pixels/t_2_3.png') },
  { id: '0,4', x: 0, y: 512, source: require('@/assets/native-pixels/t_0_4.png') },
  { id: '1,4', x: 256, y: 512, source: require('@/assets/native-pixels/t_1_4.png') },
  { id: '2,4', x: 512, y: 512, source: require('@/assets/native-pixels/t_2_4.png') },
  { id: '0,5', x: 0, y: 768, source: require('@/assets/native-pixels/t_0_5.png') },
  { id: '1,5', x: 256, y: 768, source: require('@/assets/native-pixels/t_1_5.png') },
  { id: '2,5', x: 512, y: 768, source: require('@/assets/native-pixels/t_2_5.png') },
];
type Renderer = 'RN Image' | 'Skia linear' | 'Skia nearest';
const modes: readonly Renderer[] = ['RN Image', 'Skia linear', 'Skia nearest'];

function Control({
  label,
  onPress,
  disabled = false,
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={[styles.button, disabled && styles.disabled]}
    >
      <Text style={styles.buttonText}>{label}</Text>
    </Pressable>
  );
}

export default function NativePixelProbe() {
  const { width: screenWidth } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const dpr = PixelRatio.get();
  const pixel = pixelScale(screenWidth, dpr);
  const focused = useIsFocused();
  const active = useAppActive();
  const reduced = useReducedMotion();
  const [view, setView] = useState({ width: 0, height: 0 });
  const [camera, setCamera] = useState<Point>({ x: 0, y: 0 });
  const [mode, setMode] = useState<Renderer>('RN Image');
  const [sweep, setSweep] = useState(false);
  const [cadence, setCadence] = useState<ReturnType<typeof summarizeCadence> | null>(null);
  const [error, setError] = useState('');
  const reportError = useCallback((failure: Error) => setError(failure.message), []);
  const at = clampCamera(camera, view.width, view.height, pixel, dpr);
  const mounted = visibleTiles(tiles, at, view.width, view.height, pixel);

  useEffect(() => {
    if (!sweep || !focused || !active || reduced) {
      return undefined;
    }
    let frame = 0;
    let start: number | undefined;
    let previous: number | undefined;
    const samples: number[] = [];
    const step = (now: number) => {
      start ??= now;
      if (previous !== undefined) samples.push(now - previous);
      previous = now;
      const elapsed = now - start;
      // Three round trips through horizontal and vertical tile boundaries, finite.
      const phase = (1 - Math.cos((elapsed / 10_000) * Math.PI * 2)) / 2;
      setCamera(
        clampCamera({ x: phase * 768, y: phase * 1024 }, view.width, view.height, pixel, dpr),
      );
      if (elapsed >= 30_000) {
        setCadence(summarizeCadence(samples, 1000 / 60));
        setSweep(false);
      } else frame = requestAnimationFrame(step);
    };
    frame = requestAnimationFrame(step);
    return () => {
      cancelAnimationFrame(frame);
      setSweep(false);
    };
  }, [sweep, focused, active, reduced, view.width, view.height, pixel, dpr]);

  const pan = (x: number, y: number) => {
    setSweep(false);
    setCamera(clampCamera({ x: at.x + x, y: at.y + y }, view.width, view.height, pixel, dpr));
  };
  return (
    <View style={[styles.page, { paddingBottom: insets.bottom }]}>
      <Stack.Screen options={{ title: 'C34 · native pixels' }} />
      <Text style={styles.note}>
        2× world tiles · {dpr}× density · {(pixel * dpr).toFixed(0)} device px/art px
      </Text>
      <View style={styles.controls}>
        {modes.map((item) => (
          <Control
            key={item}
            label={`${mode === item ? '✓ ' : ''}${item}`}
            onPress={() => {
              setSweep(false);
              setCadence(null);
              setError('');
              setMode(item);
            }}
          />
        ))}
      </View>
      <Text style={styles.note}>
        {mounted.length}/12 mounted · {mounted.length} MiB raw RGBA (estimate, excludes caches/GPU)
      </Text>
      <View
        style={styles.viewport}
        onLayout={(event) => {
          const { width, height } = event.nativeEvent.layout;
          setView((old) =>
            old.width === width && old.height === height ? old : { width, height },
          );
        }}
      >
        {focused &&
          active &&
          view.width > 0 &&
          view.height > 0 &&
          (mode === 'RN Image' ? (
            mounted.map((tile) => {
              const box = tileLayout(tile, at, pixel, dpr);
              return (
                <Image
                  key={tile.id}
                  source={tile.source}
                  resizeMode="stretch"
                  onError={(event) => setError(event.nativeEvent.error)}
                  style={{
                    position: 'absolute',
                    left: box.left,
                    top: box.top,
                    width: box.width,
                    height: box.height,
                  }}
                />
              );
            })
          ) : (
            <Suspense fallback={<Text>Loading Skia…</Text>}>
              <NativePixelTiles
                tiles={mounted}
                camera={at}
                pixel={pixel}
                dpr={dpr}
                width={view.width}
                height={view.height}
                nearest={mode === 'Skia nearest'}
                onError={reportError}
              />
            </Suspense>
          ))}
      </View>
      {!!error && (
        <Text accessibilityRole="alert" style={styles.note}>
          Image error: {error}
        </Text>
      )}
      <View style={styles.controls}>
        <Control label="←" onPress={() => pan(-128, 0)} />
        <Control label="↑" onPress={() => pan(0, -128)} />
        <Control label="↓" onPress={() => pan(0, 128)} />
        <Control label="→" onPress={() => pan(128, 0)} />
        <Control
          label={sweep ? 'STOP' : 'SWEEP 30s'}
          disabled={reduced}
          onPress={() => {
            setCadence(null);
            setSweep((value) => !value);
          }}
        />
      </View>
      <Text style={styles.note}>
        {reduced ? 'Reduced motion: use the arrow buttons. ' : ''}
        {cadence
          ? `JS callbacks: n=${cadence.count}, p50 ${cadence.p50.toFixed(1)} ms, p95 ${cadence.p95.toFixed(1)} ms, >16.67 ms ${cadence.overBudget}. `
          : ''}
        Use device profilers for memory and rendered frame time.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: '#FBF4E4' },
  viewport: { flex: 1, overflow: 'hidden', backgroundColor: '#20252b' },
  controls: { flexDirection: 'row', flexWrap: 'wrap', gap: 4, paddingHorizontal: 8 },
  button: {
    minWidth: 44,
    minHeight: 44,
    paddingHorizontal: 8,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ded3bc',
  },
  buttonText: { fontSize: 13, color: '#29251d' },
  disabled: { opacity: 0.45 },
  note: { color: '#29251d', fontSize: 12, padding: 8 },
});
