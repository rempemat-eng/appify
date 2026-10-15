import { useEffect, useState } from 'react';
import { Pressable, ScrollView, View } from 'react-native';
import { feedback } from '@/lib/game';
import { motionPreference, useReducedMotion } from '@/lib/motion';
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
  useEffect(() => {
    if (id !== 'phone' && id !== 'wake') return undefined;
    if (tip.id === id && tip.visible && eligible) useGame.setState({ homeTipActive: id });
    else if (useGame.getState().homeTipActive === id) useGame.setState({ homeTipActive: null });
    return () => {
      if (useGame.getState().homeTipActive === id) useGame.setState({ homeTipActive: null });
    };
  }, [eligible, id, tip.id, tip.visible]);
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
const sections = [
  [
    'Demo clock',
    'DEMO x60: 1 real second = 1 simulated offline minute. Breaks are simulated; device screen usage is not verified. The 3-minute play allowance and 30-minute reset use REAL time, including battles and ordinary dialogs. A 10-MIN simulated break resets the allowance.',
  ],
  [
    'Garden status',
    'CARE WINDOW protects your garden for 30 real seconds after a qualifying return. RECOVERING shields it after a raid. EXPOSED means rivals can raid. A simulated break or mission shields the garden.',
  ],
  [
    'Offline cards',
    'Every 15 accumulated offline MIN earns a common card. Feeding, shopping and battles never earn offline cards. Your deck holds 20; each new card replaces the weakest when full. Tap a battle card to lift it, then tap again to play. PASS restores energy.',
  ],
  [
    'Missions',
    'Park: 15 MIN, 20 GRASS. Book: 30 MIN, 60 GRASS. Mountain: 60 MIN, 150 GRASS at LV 2, plus an unowned hat or 50 GRASS if you own all hats. Common offline cards stack with a rare Park/Book card or epic Mountain card. Completed missions bring postcards. No per-minute GRASS on missions; returning early keeps common cards but not completion rewards.',
  ],
  [
    'Raids and sparring',
    'Up to 3 raids per day. Only exposed rivals can be raided. Sparring pays 5 GRASS for each of your first 3 wins per day; losses pay nothing and never use raid allowance. If play time runs out during a fight, finish it and collect the result before taking a break.',
  ],
  [
    'Together',
    'Invite a rival; both start the shared break on acceptance. Both must complete at least 10 simulated MIN for +50% GRASS and a Together badge. An early return keeps ordinary rewards, without the shared bonus. A lost connection keeps the wake report pending for retry.',
  ],
  [
    'Visitors and guardians',
    'Visitors arrive only after time away. Befriending is free. A visitor stays through WELCOME BACK and waits 10 simulated MIN after you return to the garden. Pick any befriended guardian; all share your account level, hats and deck. Your original species stays saved. First meetings and dated postcards live in the Field Journal.',
  ],
  [
    'Streak and growth',
    '120 offline MIN qualifies today for the streak, with one missed day forgiven per week. Level-ups cost 50 × your current level in GRASS. LV 2 gives a 4-card hand; LV 3 adds Digital Sunset and BLOOM. Further levels increase battle HP and attack, not a new growth stage.',
  ],
] as const;
export function GardenGuide({ onClose }: { onClose: () => void }) {
  const tips = useGame((s) => s.tips);
  const insets = useSafeAreaInsets();
  const preference = motionPreference((s) => s.reduced);
  const reduced = useReducedMotion();
  const [saving, setSaving] = useState(false);
  return (
    <View
      style={{
        flex: 1,
        backgroundColor: c.paper,
        paddingTop: 16,
        paddingHorizontal: 16,
        paddingBottom: insets.bottom + 12,
        gap: 12,
      }}
    >
      <PixelText accessibilityRole="header" style={{ fontSize: 16 }}>
        GARDEN GUIDE
      </PixelText>
      <ScrollView contentContainerStyle={{ gap: 20, paddingBottom: 16 }}>
        <Pressable
          accessibilityRole="switch"
          accessibilityLabel="Reduce decorative motion"
          accessibilityState={{ checked: preference, disabled: saving }}
          disabled={saving}
          onPress={() => {
            setSaving(true);
            void motionPreference
              .getState()
              .setReduced(!preference)
              .then(() => feedback('select'))
              .catch(() =>
                useGame.getState().notify('Could not save motion preference. Try again.', true),
              )
              .finally(() => setSaving(false));
          }}
          style={{ minHeight: 48, borderWidth: 2, borderColor: c.ink, padding: 12, gap: 6 }}
        >
          <BodyText style={{ fontFamily: 'Inter_700Bold' }}>
            Reduce motion · {preference ? 'ON' : 'OFF'}
          </BodyText>
          <BodyText style={{ fontFamily: 'Inter_400Regular' }}>
            {reduced
              ? 'Motion reduced. Your device setting is also respected.'
              : 'Keep action feedback without decorative motion or text delays.'}
          </BodyText>
        </Pressable>
        {sections.map(([heading, text]) => (
          <View key={heading} style={{ gap: 6 }}>
            <BodyText
              accessibilityRole="header"
              style={{ fontFamily: 'Inter_700Bold', fontSize: 16 }}
            >
              {heading}
            </BodyText>
            <BodyText style={{ fontFamily: 'Inter_400Regular', fontSize: 14, lineHeight: 21 }}>
              {text}
            </BodyText>
          </View>
        ))}
        {tips.length > 0 && (
          <BodyText
            accessibilityRole="header"
            style={{ fontFamily: 'Inter_700Bold', fontSize: 16 }}
          >
            Your garden tips
          </BodyText>
        )}
        {Array.from(new Set(tips)).map((id) => (
          <BodyText key={id} style={{ fontFamily: 'Inter_400Regular' }}>
            {gardenTips[id].text}
          </BodyText>
        ))}
      </ScrollView>
      <PixelButton label="DONE" onPress={onClose} />
    </View>
  );
}
