import { Tabs, usePathname } from 'expo-router';
import { View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { CozyBackground } from '@/components/cozy-ui';
import { PixelDissolve } from '@/components/pixel-feedback';
import { GameHotbar, GameHud } from '@/components/game-hud';
import { GameMenus } from '@/components/game-menus';
import { cozy as c } from '@/lib/cozy';
import { useReducedMotion } from '@/lib/motion';

// One game screen: every tab draws under a floating HUD and above a pixel
// hotbar, so the garden can fill the phone and the controls sit on top of it.
export default function TabLayout() {
  const path = usePathname();
  const reduced = useReducedMotion();
  return (
    <View style={{ flex: 1 }}>
      <CozyBackground />
      {/* eslint-disable-next-line react/style-prop-object -- Expo StatusBar uses a string style enum, not a ViewStyle. */}
      <StatusBar style="light" />
      <Tabs
        tabBar={(props) => <GameHotbar {...props} />}
        screenOptions={{
          headerShown: false,
          sceneStyle: { backgroundColor: c.transparent },
          animation: reduced ? 'none' : 'fade',
          tabBarHideOnKeyboard: true,
        }}
      >
        <Tabs.Screen name="index" options={{ title: 'HOME' }} />
        <Tabs.Screen name="missions" options={{ title: 'MISSIONS' }} />
        <Tabs.Screen name="arena" options={{ title: 'ARENA' }} />
        <Tabs.Screen name="shop" options={{ title: 'SHOP' }} />
        {/* the world beyond the valley and the hut's inside, under the same HUD and
            hotbar as the home hub (docs/vision/home-hub.md, phase 2); no tab of its own */}
        <Tabs.Screen name="world" options={{ title: 'HOME', href: null }} />
      </Tabs>
      <GameHud />
      <GameMenus />
      <PixelDissolve key={path} />
    </View>
  );
}
