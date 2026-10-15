import { PixelTabIcon, PixelDissolve } from '@/components/pixel-feedback';
import { usePathname } from 'expo-router';
import { Tabs } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { GameHeader } from '@/components/game-ui';
import { View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { feedback, palette as c } from '@/lib/game';
export default function TabLayout() {
  const insets = useSafeAreaInsets();
  const path = usePathname();
  return (
    <View style={{ flex: 1, backgroundColor: c.paper }}>
      <StatusBar {...{ style: 'dark' as const }} />
      <GameHeader />
      <Tabs
        screenOptions={{
          headerShown: false,
          sceneStyle: { backgroundColor: c.paper },
          tabBarStyle: {
            backgroundColor: c.paper,
            borderTopColor: c.ink,
            borderTopWidth: 2,
            elevation: 0,
            shadowOpacity: 0,
            height: 68 + Math.max(insets.bottom, 10),
            paddingTop: 8,
            paddingBottom: Math.max(insets.bottom, 10),
          },
          tabBarActiveTintColor: c.ink,
          tabBarInactiveTintColor: c.shade,
          tabBarLabelStyle: { fontFamily: 'PressStart2P_400Regular', fontSize: 11, marginTop: 5 },
          tabBarItemStyle: { paddingHorizontal: 0, flex: 0.9 },
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
            tabBarItemStyle: { flex: 1.3 },
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
