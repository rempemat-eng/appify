import { useState } from 'react';
import { Platform, Share, View } from 'react-native';
import * as Clipboard from 'expo-clipboard';
import { cozy as c } from '@/lib/cozy';
import { feedback } from '@/lib/game';
import { PixelButton } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';

export function FriendCode({ code }: { code: string }) {
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [manual, setManual] = useState(false);
  const invite = `Join me in NapAttack! My code is ${code}. Add it in Arena, then invite me to a Together nap.`;
  async function copy(text: string, sharing = false) {
    try {
      const copied = await Clipboard.setStringAsync(text);
      if (!copied) throw new Error('Clipboard unavailable');
      setManual(false);
      setNotice(sharing ? 'Invite copied.' : 'Code copied.');
      feedback();
    } catch {
      setManual(sharing);
      setNotice(
        sharing ? 'Select and copy the invitation below.' : 'Select and copy your code above.',
      );
      feedback('error');
    }
  }
  async function act(sharing: boolean) {
    if (pending) return;
    setPending(true);
    setNotice(null);
    setManual(false);
    try {
      if (!sharing) await copy(code);
      else if (Platform.OS !== 'web') await Share.share({ message: invite });
      else if (typeof navigator !== 'undefined' && typeof navigator.share === 'function') {
        try {
          await navigator.share({ text: invite });
        } catch (error) {
          if (!(error instanceof Error && error.name === 'AbortError')) await copy(invite, true);
        }
      } else await copy(invite, true);
    } catch {
      await copy(invite, true);
    } finally {
      setPending(false);
    }
  }
  return (
    <View style={{ gap: 12 }}>
      <BodyText>Your friend code</BodyText>
      <BodyText
        selectable
        accessibilityLabel={`Your friend code: ${code}`}
        style={{ fontSize: 28, fontFamily: 'PixelifySans_700Bold', color: c.ink }}
      >
        {code}
      </BodyText>
      <View style={{ flexDirection: 'row', gap: 12 }}>
        <View style={{ flex: 1 }}>
          <PixelButton
            label="Copy code"
            small
            light
            disabled={pending}
            onPress={() => void act(false)}
          />
        </View>
        <View style={{ flex: 1 }}>
          <PixelButton
            label="Share invite"
            small
            light
            disabled={pending}
            onPress={() => void act(true)}
          />
        </View>
      </View>
      {notice && (
        <BodyText accessibilityLiveRegion="polite" style={{ fontSize: 12 }}>
          {notice}
        </BodyText>
      )}
      {manual && <BodyText selectable>{invite}</BodyText>}
    </View>
  );
}
