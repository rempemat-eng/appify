import { createClient, asyncStorage } from '@biltme/backend';
import AsyncStorage from '@react-native-async-storage/async-storage';

function configuredClient() {
  // Keep direct env accesses so Expo can inline these public build settings.
  const url = process.env.EXPO_PUBLIC_BILT_URL?.trim();
  const key = process.env.EXPO_PUBLIC_BILT_ANON_KEY?.trim();
  if (!url || !key) return null;
  try {
    return createClient(url, key, {
      auth: {
        storage: asyncStorage(AsyncStorage),
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: false,
      },
    });
  } catch {
    // A malformed online configuration must not prevent loading a local save.
    return null;
  }
}

export const bilt = configuredClient();
export const backendConfigured = bilt !== null;
export const backendUnavailableMessage =
  'Online play is not configured in this build. Your garden, missions, shop and sparring still work on this device.';
