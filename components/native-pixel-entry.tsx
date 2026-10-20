import { lazy, Suspense } from 'react';
import { Redirect } from 'expo-router';
import { Text } from 'react-native';

// Do not initialize Skia (or decode the specimens) in the normal app. Metro still
// bundles the dependency so both flag states can be checked by export:ios.
const Probe = lazy(() => import('@/components/native-pixel-probe'));

export default function NativePixelsRoute() {
  if (process.env.EXPO_PUBLIC_NATIVE_PIXELS !== '1') return <Redirect href="/" />;
  return (
    <Suspense fallback={<Text>Loading native pixel probe…</Text>}>
      <Probe />
    </Suspense>
  );
}
