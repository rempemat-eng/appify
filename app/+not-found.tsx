import { router, Stack } from 'expo-router';
import { CozyPanel } from '@/components/cozy-ui';
import { Page, PixelButton, PixelText } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { PixelScene } from '@/components/pixel-scenes';

export default function NotFoundScreen() {
  return (
    <>
      <Stack.Screen options={{ title: 'A QUIET DETOUR' }} />
      <Page>
        <PixelScene kind="trail" height={192} mini />
        <CozyPanel style={{ padding: 16, gap: 12 }}>
          <PixelText accessibilityRole="header" style={{ fontSize: 16 }}>
            A QUIET DETOUR
          </PixelText>
          <BodyText>That page isn&apos;t here. Head back to your garden to find your way.</BodyText>
          <PixelButton label="BACK TO THE GARDEN" onPress={() => router.replace('/')} />
        </CozyPanel>
      </Page>
    </>
  );
}
