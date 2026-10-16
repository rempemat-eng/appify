// oxlint-disable-next-line eslint-plugin-import/no-unassigned-import
import '../global.css';

import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { Nunito_600SemiBold } from '@expo-google-fonts/nunito/600SemiBold';
import { Nunito_800ExtraBold } from '@expo-google-fonts/nunito/800ExtraBold';
import { Nunito_600SemiBold_Italic } from '@expo-google-fonts/nunito/600SemiBold_Italic';
import { PressStart2P_400Regular } from '@expo-google-fonts/press-start-2p/400Regular';
import { useFonts } from 'expo-font';
import Constants, { ExecutionEnvironment } from 'expo-constants';
import { Platform } from 'react-native';
import { useEffect, useState } from 'react';
import * as DevClient from 'expo-dev-client';
import { HeroUINativeProvider } from 'heroui-native';
import { Uniwind } from 'uniwind';
import {
  ErrorBoundary as ExpoErrorBoundary,
  type ErrorBoundaryProps,
  SplashScreen,
  Stack,
  usePathname,
} from 'expo-router';

import { patchExpoGoAssetUrls } from '@/lib/expoGoAssets';
import { initPostHog } from '@/lib/posthog';
import { registerServiceWorker } from '@/lib/registerServiceWorker';
import { NapAttackSplash } from '@/components/napattack-brand';
import { GameOverlays } from '@/components/game-overlays';
import { loadMotionPreference, watchSystemMotion } from '@/lib/motion';
import { startGame } from '@/lib/game';
import { reportErrorToParent } from '@/lib/reportPreviewError';

/**
 * Custom ErrorBoundary that reports React render errors to the parent window (Bilt preview iframe)
 * and then renders the default Expo error UI.
 */
function ErrorBoundary({ error, retry }: ErrorBoundaryProps) {
  useEffect(() => {
    if (Platform.OS === 'web' && error) {
      const message = [error.message, error.stack].filter(Boolean).join('\n');
      reportErrorToParent(message);
    }
  }, [error]);
  return <ExpoErrorBoundary error={error} retry={retry} />;
}

export { ErrorBoundary };

// Before any screen renders an Image or loads a font.
patchExpoGoAssetUrls();

// Starter is light-only by default. Remove this when implementing requested dark mode.
Uniwind.setTheme('light');

void SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const pathname = usePathname();
  const [splashDone, setSplashDone] = useState(false);
  useEffect(() => {
    if (Platform.OS !== 'web') return;
    const page =
      pathname === '/missions'
        ? 'Missions'
        : pathname === '/arena'
          ? 'Arena'
          : pathname === '/shop'
            ? 'Shop'
            : pathname === '/journal'
              ? 'Field Journal'
              : 'Home';
    document.title = `${page} · NapAttack`;
  }, [pathname]);
  useEffect(() => {
    const stopMotion = watchSystemMotion();
    void loadMotionPreference();
    const stopGame = startGame();
    return () => {
      stopGame();
      stopMotion();
    };
  }, []);
  const [loaded, error] = useFonts({
    Nunito_600SemiBold,
    Nunito_800ExtraBold,
    Nunito_600SemiBold_Italic,
    PressStart2P_400Regular,
  });

  // Report uncaught JS errors and unhandled promise rejections to parent (Bilt preview iframe)
  useEffect(() => {
    if (Platform.OS !== 'web' || typeof window === 'undefined') return undefined;

    const handleError = (event: ErrorEvent) => {
      const message = event.error?.stack ?? event.message ?? 'Unknown error';
      reportErrorToParent(message);
    };

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const err = event.reason;
      const message =
        err instanceof Error ? [err.message, err.stack].filter(Boolean).join('\n') : String(err);
      reportErrorToParent(message);
    };

    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  useEffect(() => {
    const isExpoGo = Constants.executionEnvironment === ExecutionEnvironment.StoreClient;
    if (__DEV__ && Platform.OS !== 'web' && !isExpoGo) {
      const timer = setTimeout(() => {
        DevClient.closeMenu();
        DevClient.hideMenu();
      }, 1000);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, []);

  useEffect(() => {
    if (Platform.OS === 'web') {
      initPostHog();
    }
  }, []);

  useEffect(() => {
    registerServiceWorker();
  }, []);

  useEffect(() => {
    if (loaded || error) {
      void SplashScreen.hideAsync();
    }
  }, [loaded, error]);

  if (!loaded && !error) {
    return null;
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }} onTouchStart={() => setSplashDone(true)}>
      <HeroUINativeProvider>
        <Stack>
          <Stack.Screen name="(tabs)" options={{ title: 'NapAttack', headerShown: false }} />
          <Stack.Screen name="journal" options={{ title: 'FIELD JOURNAL' }} />
        </Stack>
        {splashDone && <GameOverlays />}
        {!splashDone && <NapAttackSplash onFinish={setSplashDone} />}
      </HeroUINativeProvider>
    </GestureHandlerRootView>
  );
}
