import { useEffect, useState } from 'react';
import { Pressable, ScrollView, Switch, View } from 'react-native';
import { feedback } from '@/lib/game';
import { useMotionPreference, useReducedMotion } from '@/lib/motion';
import { ChevronDown, ChevronUp, X } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { gardenTips, type GardenTipId } from '@/lib/first-session';
import { CozyBackground, CozySheet } from '@/components/cozy-ui';
import { cozy as c } from '@/lib/cozy';
import { useGame } from '@/lib/game';
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
          borderRadius: 14,
          backgroundColor: c.paper,
          borderWidth: 2,
          borderColor: c.outline,
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
          style={{ flex: 1, fontFamily: 'PixelifySans_500Medium', fontSize: 12, lineHeight: 18 }}
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
    'A home, an outing, a story',
    'Your companion lives in the garden and explores a little further when you take a mission. Return with cards and postcards, meet visitors and choose who comes along next. There is no need to do everything: the garden is here when a break fits your day.',
  ],
  [
    'Explore your garden',
    'Tap an open patch to walk there. Visit the watering can to tend the flowers, the bench to share a page, the lantern to change its glow, or the pond to meet a little neighbour. Tap your companion for a pat. These are small moments to enjoy whenever you like; they do not cost GRASS or earn rewards. The hut, mailbox, stall, signpost and gate lead to the rest of your garden life.',
  ],
  [
    'Demo clock',
    'Demo timer only. Sleep and phone inactivity are not measured. DEMO x60: 1 real second = 1 simulated offline minute. Breaks are simulated; device screen usage is not verified. The 3-minute play allowance and 30-minute reset use REAL time, including battles and ordinary dialogs. A 10-MIN simulated break resets the allowance.',
  ],
  [
    'Garden status',
    'NAPPING shields your garden while your Grassling grows. Naps are simulated in this demo. In connected play, awake gardens can be raided when EXPOSED. CARE WINDOW protects your garden for 30 real seconds after a qualifying return. RECOVERING shields it after a raid. Missions also shield the garden.',
  ],
  [
    'Offline cards',
    'Every 15 accumulated offline MIN earns a common card. Feeding, shopping and battles never earn offline cards. Your deck holds 20; each new card replaces the weakest when full. Tap a battle card to lift it, then tap again to play. PASS restores energy.',
  ],
  [
    'Missions',
    'Park Patrol: 15 MIN, 20 GRASS. Book Club: 30 MIN, 60 GRASS. Mountain Retreat: 60 MIN, 150 GRASS at LV 2, plus an unowned hat or 50 GRASS if you own all hats. Common offline cards stack with a rare Park/Book card or epic Mountain card. Completed missions bring postcards. No per-minute GRASS on missions; returning early keeps common cards but not completion rewards.',
  ],
  [
    'Real life and little keepsakes',
    'Before a nap or mission, optionally choose Rest, Read, Move or Create; Just a break needs no reflection. On returning, choose whether to keep a lantern, bookmark, leaf or sketch memory with the companion who began that break. Memories are self-reported, give no extra rewards and stay on this device in the Field Journal. The daily rhythm planner can also make room for rest, focus and your own time. It follows device-local time, including overnight windows; it does not block apps, measure sleep or change rewards.',
  ],
  [
    'Raids and sparring',
    'Dave is available for local practice. Sparring pays 5 GRASS for each of your first 3 wins per day; losses pay nothing and never use raid allowance. Player raids require a connected multiplayer build: up to 3 per day, against exposed rivals only. If play time runs out during a fight, finish it and collect the result before taking a break.',
  ],
  [
    'Together',
    'Together requires a connected multiplayer build. Invite a rival; both start the shared break on acceptance. Both must complete at least 10 simulated MIN for +50% GRASS and a Together badge. An early return keeps ordinary rewards, without the shared bonus. A lost connection keeps the wake report pending for retry.',
  ],
  [
    'Visitors and guardians',
    'Visitors arrive only after time away: your first one after any nap or mission of 10+ simulated MIN, then by chance on longer breaks (hints in the Field Journal). Befriending is free. A visitor stays through WELCOME BACK and waits 10 simulated MIN (10 real seconds in this demo) after you return to the garden. Preview any befriended companion before choosing them; all share your account level, GRASS, hats, deck and collection. Your original name and species stay saved. First meetings, dated postcards and kept memories live in the Field Journal.',
  ],
  [
    'Streak and growth',
    '120 offline MIN qualifies today for the streak, with one missed day forgiven per week. Level-ups cost 50 × your current level in GRASS. LV 2 gives a 4-card hand; LV 3 adds Digital Sunset and BLOOM. Further levels increase battle HP and attack, not a new growth stage.',
  ],
] as const;
export function GardenGuide({ onClose }: { onClose: () => void }) {
  const tips = useGame((s) => s.tips);
  const insets = useSafeAreaInsets();
  const preference = useMotionPreference((s) => s.reduced);
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
      <CozyBackground />
      <CozySheet style={{ flex: 1, padding: 16, gap: 12 }}>
        <PixelText accessibilityRole="header" style={{ fontSize: 16 }}>
          GARDEN GUIDE
        </PixelText>
        <ScrollView contentContainerStyle={{ gap: 20, paddingBottom: 16 }}>
          <View
            style={{
              minHeight: 52,
              borderRadius: 14,
              borderWidth: 2,
              borderColor: c.outline,
              padding: 12,
              gap: 6,
            }}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
              <BodyText style={{ flex: 1, fontFamily: 'PixelifySans_700Bold' }}>
                Reduce motion · {preference ? 'ON' : 'OFF'}
              </BodyText>
              <Switch
                accessibilityLabel="Reduce decorative motion"
                accessibilityState={{ checked: preference, disabled: saving }}
                value={preference}
                disabled={saving}
                trackColor={{ false: c.shade, true: c.moss }}
                thumbColor={c.paper}
                onValueChange={(value) => {
                  setSaving(true);
                  void useMotionPreference
                    .getState()
                    .setReduced(value)
                    .then(() => feedback('select'))
                    .catch(() =>
                      useGame
                        .getState()
                        .notify('Could not save motion preference. Try again.', true),
                    )
                    .finally(() => setSaving(false));
                }}
              />
            </View>
            <BodyText style={{ fontFamily: 'PixelifySans_500Medium' }}>
              {reduced
                ? 'Motion reduced. Your device setting is also respected.'
                : 'Normal decorative motion and text delays are on.'}
            </BodyText>
          </View>
          {sections.map(([heading, text]) => (
            <View key={heading} style={{ gap: 6 }}>
              <BodyText
                accessibilityRole="header"
                style={{ fontFamily: 'PixelifySans_700Bold', fontSize: 16 }}
              >
                {heading}
              </BodyText>
              <BodyText
                style={{ fontFamily: 'PixelifySans_500Medium', fontSize: 14, lineHeight: 21 }}
              >
                {text}
              </BodyText>
            </View>
          ))}
          {tips.length > 0 && (
            <BodyText
              accessibilityRole="header"
              style={{ fontFamily: 'PixelifySans_700Bold', fontSize: 16 }}
            >
              Your garden tips
            </BodyText>
          )}
          {Array.from(new Set(tips)).map((id) => (
            <BodyText key={id} style={{ fontFamily: 'PixelifySans_500Medium' }}>
              {gardenTips[id].text}
            </BodyText>
          ))}
        </ScrollView>
        <PixelButton label="DONE" onPress={onClose} />
      </CozySheet>
    </View>
  );
}
