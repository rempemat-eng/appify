import { useEffect, useState } from 'react';
import { Modal, Pressable, ScrollView, View } from 'react-native';
import { ChevronDown, ChevronUp, X } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { gardenTips, type GardenTipId } from '@/lib/first-session';
import { palette as c, useGame } from '@/lib/game';
import { BodyText } from '@/components/pixel-feedback';
import { PixelButton, PixelText } from '@/components/game-ui';

export function GardenTip({
  id,
  eligible = true,
  floating = false,
  pointsUp = false,
  onDismiss,
}: {
  id: GardenTipId;
  eligible?: boolean;
  floating?: boolean;
  pointsUp?: boolean;
  onDismiss?: () => void;
}) {
  const seen = useGame((s) => s.tips.includes(id));
  const seeTip = useGame((s) => s.seeTip);
  const [tip, setTip] = useState({ id, eligible, visible: eligible && !seen });
  if (tip.id !== id || tip.eligible !== eligible) {
    setTip({ id, eligible, visible: eligible && !seen });
  }
  useEffect(() => {
    if (tip.id === id && tip.eligible === eligible && tip.visible && eligible && !seen) {
      seeTip(id);
    }
  }, [eligible, id, seeTip, seen, tip]);
  if (tip.id !== id || !tip.visible || !eligible) return null;
  const Arrow = pointsUp ? ChevronUp : ChevronDown;
  return (
    <View
      style={[
        {
          backgroundColor: c.paper,
          borderWidth: 2,
          borderColor: c.ink,
          paddingLeft: 12,
          zIndex: 30,
        },
        floating
          ? {
              position: 'absolute',
              left: 0,
              right: 0,
              ...(pointsUp ? { top: '100%' } : { bottom: '100%' }),
            }
          : {},
      ]}
    >
      {pointsUp && <Arrow size={18} color={c.ink} />}
      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
        <BodyText
          accessibilityLiveRegion="polite"
          style={{ flex: 1, fontFamily: 'Inter_600SemiBold', fontSize: 12, lineHeight: 18 }}
        >
          {gardenTips[id].text}
        </BodyText>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Dismiss ${gardenTips[id].control} tip`}
          onPress={() => {
            setTip({ id, eligible, visible: false });
            onDismiss?.();
          }}
          style={{ minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' }}
        >
          <X size={18} color={c.ink} />
        </Pressable>
      </View>
      {!pointsUp && <Arrow size={18} color={c.ink} />}
    </View>
  );
}
export function GardenGuide({ open, onClose }: { open: boolean; onClose: () => void }) {
  const tips = useGame((s) => s.tips);
  const insets = useSafeAreaInsets();
  return (
    <Modal visible={open} onRequestClose={onClose} animationType="fade">
      <View
        style={{
          flex: 1,
          backgroundColor: c.paper,
          paddingTop: insets.top + 24,
          paddingHorizontal: 20,
          paddingBottom: insets.bottom + 16,
          gap: 20,
        }}
      >
        <PixelText style={{ fontSize: 16 }}>GARDEN GUIDE</PixelText>
        <ScrollView contentContainerStyle={{ gap: 24, paddingBottom: 20 }}>
          {tips.length === 0 ? (
            <BodyText>Your Grassling’s first-time tips will appear here.</BodyText>
          ) : (
            tips.map((id) => (
              <View key={id} style={{ gap: 8 }}>
                <PixelText>{gardenTips[id].control.toUpperCase()}</PixelText>
                <BodyText style={{ fontFamily: 'Inter_600SemiBold', fontSize: 14, lineHeight: 21 }}>
                  {gardenTips[id].text}
                </BodyText>
              </View>
            ))
          )}
        </ScrollView>
        <PixelButton label="DONE" onPress={onClose} />
      </View>
    </Modal>
  );
}
