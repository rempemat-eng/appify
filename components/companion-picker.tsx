import { useState } from 'react';
import { Modal, Pressable, ScrollView, View, useWindowDimensions } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { cozy as c, panelStyle } from '@/lib/cozy';
import { useGame, type Player } from '@/lib/game';
import { companionOptions, companionProfile } from '@/lib/companion-profiles';
import type { VisitorId } from '@/lib/visitors';
import { Pet, PixelButton, PixelText } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { CozyPanel, CozySheet } from '@/components/cozy-ui';

export function CompanionPicker({
  player,
  open,
  onOpenChange,
}: {
  player: Player;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { height } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const inBattle = useGame((s) => Boolean(s.battle));
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
      <CozyPanel style={{ padding: 14, gap: 10 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
          <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
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
            <BodyText style={{ fontSize: 11, fontFamily: 'Nunito_800ExtraBold' }}>
              YOUR COMPANION
            </BodyText>
            <BodyText numberOfLines={1} style={{ fontFamily: 'Nunito_800ExtraBold' }}>
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
              padding: 16,
              gap: 14,
            }}
          >
            <PixelText accessibilityRole="header" style={{ fontSize: 14, lineHeight: 24 }}>
              COMPANIONS
            </PixelText>
            <ScrollView
              style={{ flexShrink: 1 }}
              contentContainerStyle={{ gap: 16, paddingBottom: 4 }}
            >
              <BodyText style={{ fontSize: 12 }}>
                Preview a friend, then choose who comes along. Your level, hats, cards and progress
                stay with you.
              </BodyText>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator
                contentContainerStyle={{ gap: 10, paddingBottom: 8 }}
              >
                {options.map((option) => (
                  <Pressable
                    key={option.id ?? 'starter'}
                    accessibilityRole="button"
                    accessibilityLabel={`Preview ${option.name}, ${option.habit} companion${option.id === active.id ? ', active' : ''}`}
                    accessibilityState={{ selected: option.id === preview.id }}
                    onPress={() => setPreviewId(option.id)}
                    style={({ pressed }) => ({
                      ...panelStyle,
                      width: 116,
                      minHeight: 118,
                      padding: 8,
                      gap: 4,
                      alignItems: 'center',
                      borderColor: option.id === preview.id ? c.leafOutline : c.outline,
                      backgroundColor: option.id === preview.id ? c.sage : c.paper,
                      opacity: pressed ? 0.75 : 1,
                    })}
                  >
                    <View
                      pointerEvents="none"
                      accessibilityElementsHidden
                      importantForAccessibility="no-hide-descendants"
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
                    </View>
                    <BodyText
                      numberOfLines={1}
                      style={{ fontSize: 12, fontFamily: 'Nunito_800ExtraBold' }}
                    >
                      {option.name}
                    </BodyText>
                    <BodyText style={{ fontSize: 10 }}>
                      {option.habit}
                      {option.id === active.id ? ' · ACTIVE' : ''}
                    </BodyText>
                  </Pressable>
                ))}
              </ScrollView>
              <View style={{ ...panelStyle, padding: 14, gap: 12, backgroundColor: tint }}>
                <View style={{ gap: 4 }}>
                  <BodyText style={{ fontSize: 18, fontFamily: 'Nunito_800ExtraBold' }}>
                    {preview.name}
                  </BodyText>
                  <BodyText style={{ fontSize: 12 }}>
                    {preview.habit} FAMILY · {preview.traits.join(' · ')}
                  </BodyText>
                </View>
                <BodyText>{preview.description}</BodyText>
                <View style={{ gap: 4 }}>
                  <BodyText style={{ fontSize: 11, fontFamily: 'Nunito_800ExtraBold' }}>
                    IN BATTLE
                  </BodyText>
                  <BodyText style={{ fontSize: 12 }}>{preview.battleNote}</BodyText>
                </View>
              </View>
              <View style={{ gap: 6, paddingHorizontal: 2 }}>
                <BodyText style={{ fontSize: 11, fontFamily: 'Nunito_800ExtraBold' }}>
                  A LITTLE REAL-WORLD ADVENTURE
                </BodyText>
                <BodyText style={{ fontFamily: 'Nunito_800ExtraBold' }}>
                  {preview.invitation.title}
                </BodyText>
                <BodyText style={{ fontSize: 12 }}>{preview.invitation.body}</BodyText>
                <BodyText style={{ fontSize: 11 }}>
                  An optional idea. Choose a break that fits your day.
                </BodyText>
              </View>
              <BodyText style={{ fontSize: 12 }}>
                {options.length === 1
                  ? 'Your first friend visits after a break of 10 simulated MIN. Befriend visitors to invite them along.'
                  : 'Befriend more garden visitors to meet new companions. Rarity describes discovery, not extra strength.'}
              </BodyText>
              {locked && (
                <BodyText style={{ fontSize: 12 }}>
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
