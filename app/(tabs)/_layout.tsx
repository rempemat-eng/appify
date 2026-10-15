import { useEffect } from 'react';
import { Home, Trees, Swords, ShoppingBag } from 'lucide-react-native';
import { Tabs } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { GameHeader } from '@/components/game-ui';
import { GameOverlays } from '@/components/game-overlays';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { feedback, palette as c, startGame } from '@/lib/game';
export default function TabLayout() {
  const insets = useSafeAreaInsets();
  useEffect(() => startGame(), []);
  return (
    <>
      <StatusBar {...{ style: 'dark' as const }} />
      <Tabs
        screenOptions={{
          header: () => <GameHeader />,
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
            tabBarIcon: ({ color }) => <Home color={color} size={22} strokeWidth={2.5} />,
          }}
        />
        <Tabs.Screen
          name="missions"
          options={{
            title: 'MISSIONS',
            tabBarItemStyle: { flex: 1.3 },
            tabBarIcon: ({ color }) => <Trees color={color} size={22} strokeWidth={2.5} />,
          }}
        />
        <Tabs.Screen
          name="arena"
          options={{
            title: 'ARENA',
            tabBarIcon: ({ color }) => <Swords color={color} size={22} strokeWidth={2.5} />,
          }}
        />
        <Tabs.Screen
          name="shop"
          options={{
            title: 'SHOP',
            tabBarIcon: ({ color }) => <ShoppingBag color={color} size={22} strokeWidth={2.5} />,
          }}
        />
      </Tabs>
      <GameOverlays />
    </>
  );
}
