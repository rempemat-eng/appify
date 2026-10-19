import type { ConfigContext, ExpoConfig } from '@expo/config';

type ExpoPlugins = NonNullable<ExpoConfig['plugins']>;

export default ({ config }: ConfigContext): ExpoConfig => {
  const nativePlugins: ExpoPlugins =
    process.env.EXPO_PLATFORM === 'native'
      ? [['expo-dev-client', { launchMode: 'most-recent' }]]
      : [];

  return {
    ...config,
    name: 'NapAttack',
    description: 'nap to grow. wake to raid.',
    icon: './public/icons/napattack.png',
    slug: 'screenagotchi',
    version: process.env.BILT_APP_VERSION ?? '1.0.0',
    orientation: 'portrait',
    userInterfaceStyle: 'light',
    scheme: 'screenagotchi',
    runtimeVersion: {
      policy: 'appVersion',
    },
    assetBundlePatterns: ['**/*'],
    ios: {
      deploymentTarget: '16.4',
      infoPlist: {
        ITSAppUsesNonExemptEncryption: false,
        CFBundleDisplayName: 'NapAttack',
      },
      supportsTablet: true,
      bundleIdentifier: process.env.BILT_IOS_BUNDLE_ID ?? 'me.bilt.appify',
    },
    android: {
      package: process.env.BILT_ANDROID_PACKAGE ?? 'me.bilt.appify',
    },
    web: {
      bundler: 'metro',
      // 'single' = SPA export: one index.html + client routing, so edge serving
      // needs only a single 404→index.html fallback rule.
      output: 'single',
      favicon: './public/icons/napattack.png',
    },
    // the Expo project the cloud builds (EAS) belong to: @napattack/screenagotchi
    owner: 'napattack',
    extra: {
      appStoreAppId: process.env.BILT_APP_STORE_APP_ID,
      eas: { projectId: '4d8c2dff-3489-4b00-9045-5f4521baa82b' },
    },
    plugins: [
      'expo-router',
      'expo-font',
      [
        'expo-splash-screen',
        { image: './public/icons/napattack.png', imageWidth: 200, backgroundColor: '#FBF4E4' },
      ],
      ...nativePlugins,
    ],
    experiments: {
      typedRoutes: true,
      reactCompiler: true,
    },
  };
};
