import { Tabs, usePathname } from 'expo-router';
import { View, useWindowDimensions } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GameHeader } from '@/components/game-ui';
import { CozyBackground } from '@/components/cozy-ui';
import { PixelTabIcon, PixelDissolve } from '@/components/pixel-feedback';
import { feedback } from '@/lib/game';
import { cozy as c, panelStyle } from '@/lib/cozy';
import { artGeometry } from '@/lib/art-direction';
import { useReducedMotion } from '@/lib/motion';
import { gameLayout, gameSideInset } from '@/lib/layout';
export default function TabLayout() {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const sideInset = gameSideInset(width);
  const path = usePathname();
  const reduced = useReducedMotion();
  return (
    <View style={{ flex: 1 }}>
      <CozyBackground />
      {/* eslint-disable-next-line react/style-prop-object -- Expo StatusBar uses a string style enum, not a ViewStyle. */}
      <StatusBar style="dark" />
      <GameHeader />
      <Tabs
        screenOptions={{
          headerShown: false,
          sceneStyle: { backgroundColor: c.transparent },
          animation: reduced ? 'none' : 'fade',
          tabBarStyle: {
            ...panelStyle,
            position: 'absolute',
            left: sideInset,
            right: sideInset,
            bottom: insets.bottom + gameLayout.dockBottomGap,
            backgroundColor: c.paper,
            borderWidth: 2,
            borderTopWidth: 2,
            borderColor: c.outline,
            height: gameLayout.dockHeight,
            paddingTop: 6,
            paddingBottom: 6,
          },
          tabBarActiveTintColor: c.ink,
          tabBarInactiveTintColor: c.shade,
          tabBarLabelPosition: 'below-icon',
          tabBarHideOnKeyboard: true,
          tabBarItemStyle: {
            minHeight: 44,
            borderRadius: artGeometry.controlRadius,
            marginHorizontal: 2,
          },
          tabBarLabelStyle: {
            fontFamily: 'Nunito_800ExtraBold',
            fontSize: 12,
            lineHeight: 16,
            marginTop: 3,
          },
        }}
        screenListeners={({ navigation }) => ({
          tabPress: () => {
            if (!navigation.isFocused()) feedback('select');
          },
        })}
      >
        <Tabs.Screen
          name="index"
          options={{
            title: 'HOME',
            tabBarIcon: ({ color, focused }) => (
              <PixelTabIcon kind="house" color={color} focused={focused} />
            ),
          }}
        />
        <Tabs.Screen
          name="missions"
          options={{
            title: 'MISSIONS',
            tabBarIcon: ({ color, focused }) => (
              <PixelTabIcon kind="map" color={color} focused={focused} />
            ),
          }}
        />
        <Tabs.Screen
          name="arena"
          options={{
            title: 'ARENA',
            tabBarIcon: ({ color, focused }) => (
              <PixelTabIcon kind="swords" color={color} focused={focused} />
            ),
          }}
        />
        <Tabs.Screen
          name="shop"
          options={{
            title: 'SHOP',
            tabBarIcon: ({ color, focused }) => (
              <PixelTabIcon kind="bag" color={color} focused={focused} />
            ),
          }}
        />
      </Tabs>
      <PixelDissolve key={path} />
    </View>
  );
}
