import { useState } from 'react';
import { Modal, Pressable, ScrollView, View, useWindowDimensions } from 'react-native';
import { router } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { cozy as c } from '@/lib/cozy';
import { useGame, type Player } from '@/lib/game';
import { companionOptions, companionProfile } from '@/lib/companion-profiles';
import type { VisitorId } from '@/lib/visitors';
import { Pet, PixelButton, PixelText } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { CozyPanel, CozySheet } from '@/components/cozy-ui';
import { FrameFill, usePixelUnit } from '@/components/pixel-frame';
import { contentInset, layers, siblingGap, type } from '@/lib/ui-tokens';
import { CompanionMemories } from '@/components/companion-memories';

export function CompanionPicker({
  player,
  open,
  onOpenChange,
  showCard = true,
}: {
  player: Player;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  showCard?: boolean;
}) {
  const { height } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const u = usePixelUnit();
  const inBattle = useGame((s) => Boolean(s.battle));
  const memories = useGame((s) => s.companionMemories);
  const active = companionProfile(player);
  const options = companionOptions(player);
  const [selection, setSelection] = useState({ open, activeId: active.id, id: active.id });
  if (selection.open !== open || selection.activeId !== active.id)
    setSelection({ open, activeId: active.id, id: active.id });
  const previewId = selection.id;
  const setPreviewId = (id: VisitorId | null) => setSelection({ ...selection, id });
  const preview = options.find((option) => option.id === previewId) ?? active;
  const chosen = preview.id === active.id;
  const locked = player.mode !== 'awake' || inBattle;
  const tint = preview.habit === 'REST' ? c.rest : preview.habit === 'ROAM' ? c.sage : c.amber;
  const close = () => onOpenChange(false);
  return (
    <>
      {showCard && (
        <CozyPanel style={{ padding: 14, gap: 10 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
            <View
              aria-hidden
              accessibilityElementsHidden
              importantForAccessibility="no-hide-descendants"
            >
              <Pet
                visitor={active.id}
                species={active.species}
                level={player.level}
                hat={player.hat}
                size={64}
                bob={false}
                active={false}
              />
            </View>
            <View style={{ flex: 1, minWidth: 0, gap: 3 }}>
              <BodyText style={{ fontSize: 11, fontFamily: 'PixelifySans_700Bold' }}>
                YOUR COMPANION
              </BodyText>
              <BodyText numberOfLines={1} style={{ fontFamily: 'PixelifySans_700Bold' }}>
                {active.name}
              </BodyText>
              <BodyText style={{ fontSize: 12 }}>
                {active.habit} · {active.traits.join(' · ')}
              </BodyText>
            </View>
          </View>
          <PixelButton small light label="CHANGE COMPANION" onPress={() => onOpenChange(true)} />
          <BodyText accessibilityLiveRegion="polite" style={{ fontSize: 12 }}>
            {active.name} is your active companion.
          </BodyText>
        </CozyPanel>
      )}
      <Modal visible={open} transparent animationType="none" onRequestClose={close}>
        <View
          style={{
            flex: 1,
            justifyContent: 'flex-end',
            padding: 16,
            paddingTop: insets.top + 16,
            paddingBottom: insets.bottom + 16,
            backgroundColor: c.shadow,
          }}
        >
          <CozySheet
            style={{
              width: '100%',
              maxWidth: 608,
              maxHeight: Math.max(180, height - insets.top - insets.bottom - 32),
              alignSelf: 'center',
              gap: 14,
            }}
          >
            <PixelText accessibilityRole="header" style={type.title}>
              COMPANIONS
            </PixelText>
            <ScrollView
              style={{ flexShrink: 1 }}
              contentContainerStyle={{ gap: 16, paddingBottom: 4 }}
            >
              <BodyText style={type.body}>
                Preview a friend, then choose who comes along. Your level, hats, cards and progress
                stay with you.
              </BodyText>
              {/* the friends sit in a well, so the cards stand out from the sheet */}
              <View style={{ padding: contentInset(u) }}>
                <FrameFill fill={layers.well} outline={c.outline} inset />
                <ScrollView
                  horizontal
                  showsHorizontalScrollIndicator
                  contentContainerStyle={{ gap: siblingGap(u) * 2, paddingBottom: u }}
                >
                  {options.map((option) => (
                    <View
                      key={option.id ?? 'starter'}
                      style={{
                        width: 116,
                        minHeight: 118,
                        padding: contentInset(u),
                        marginBottom: u,
                      }}
                    >
                      <FrameFill
                        depth={1}
                        fill={option.id === preview.id ? c.sage : c.paper}
                        outline={option.id === preview.id ? c.leafOutline : c.outline}
                      />
                      <View
                        aria-hidden
                        accessibilityElementsHidden
                        importantForAccessibility="no-hide-descendants"
                        style={{ alignItems: 'center', gap: 4, pointerEvents: 'none' }}
                      >
                        <Pet
                          visitor={option.id}
                          species={option.species}
                          level={player.level}
                          hat={player.hat}
                          size={64}
                          bob={false}
                          active={false}
                        />
                        <BodyText numberOfLines={1} style={type.label}>
                          {option.name}
                        </BodyText>
                        <BodyText style={type.caption}>
                          {option.habit}
                          {option.id === active.id ? ' · ACTIVE' : ''}
                        </BodyText>
                      </View>
                      <Pressable
                        accessibilityRole="button"
                        accessibilityLabel={`Preview ${option.name}, ${option.habit} companion${option.id === active.id ? ', active' : ''}`}
                        accessibilityState={{ selected: option.id === preview.id }}
                        onPress={() => setPreviewId(option.id)}
                        style={({ pressed }) => ({
                          position: 'absolute',
                          top: 3 * u,
                          left: 3 * u,
                          right: 3 * u,
                          bottom: 3 * u,
                          zIndex: 1,
                          backgroundColor: pressed ? 'rgba(56,99,52,0.14)' : c.transparent,
                        })}
                      />
                    </View>
                  ))}
                </ScrollView>
              </View>
              <View
                style={{ padding: contentInset(u) + u, gap: siblingGap(u) * 3, marginBottom: u }}
              >
                <FrameFill depth={1} fill={tint} outline={c.outline} />
                <View style={{ gap: 4 }}>
                  <BodyText accessibilityRole="header" style={type.heading}>
                    {preview.name}
                  </BodyText>
                  <BodyText style={type.label}>
                    {preview.habit} FAMILY · {preview.traits.join(' · ').toUpperCase()}
                  </BodyText>
                </View>
                <BodyText style={type.body}>{preview.description}</BodyText>
                <View style={{ gap: 4 }}>
                  <BodyText style={type.label}>IN BATTLE</BodyText>
                  <BodyText style={type.body}>{preview.battleNote}</BodyText>
                </View>
              </View>
              <View style={{ gap: 6, paddingHorizontal: 2 }}>
                <BodyText style={type.label}>A LITTLE REAL-WORLD ADVENTURE</BodyText>
                <BodyText style={type.heading}>{preview.invitation.title}</BodyText>
                <BodyText style={type.body}>{preview.invitation.body}</BodyText>
                <BodyText style={type.caption}>
                  An optional idea. Choose a break that fits your day.
                </BodyText>
              </View>
              <CompanionMemories
                memories={memories}
                companionKey={preview.id ?? 'starter'}
                companionName={preview.name}
              />
              <PixelButton
                small
                light
                label="OPEN MEMORY JOURNAL"
                onPress={() => {
                  close();
                  router.push('/journal?tab=memories');
                }}
              />
              <BodyText style={type.caption}>
                {options.length === 1
                  ? 'Your first friend visits after a break of 10 simulated MIN. Befriend visitors to invite them along.'
                  : 'Befriend more garden visitors to meet new companions. Rarity describes discovery, not extra strength.'}
              </BodyText>
              {locked && (
                <BodyText style={type.caption}>
                  Finish your nap or battle before changing companions.
                </BodyText>
              )}
            </ScrollView>
            <PixelButton
              label={chosen ? `${preview.name} IS ACTIVE` : `BRING ${preview.name}`}
              disabled={chosen || locked}
              onPress={() => {
                useGame.getState().selectGuardian(preview.id);
                if (companionProfile(useGame.getState().player ?? player).id === preview.id)
                  close();
              }}
            />
            <PixelButton small light label="DONE" onPress={close} />
          </CozySheet>
        </View>
      </Modal>
    </>
  );
}
