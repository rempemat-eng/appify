import { type ComponentRef, useEffect, useRef } from 'react';
import { AccessibilityInfo, Platform, ScrollView, Text, View } from 'react-native';
import { cozy as c } from '@/lib/cozy';
import { gameStore, type SaveLoadProblem } from '@/lib/game';
import { barControl, iconSize, panelGap, contentInset, type } from '@/lib/ui-tokens';
import { CozyBackground, CozySheet } from '@/components/cozy-ui';
import { PixelButton } from '@/components/game-ui';
import { FrameFill, usePixelUnit } from '@/components/pixel-frame';
import { PixelIcon, type IconName } from '@/components/pixel-icon';

/**
 * The screen shown instead of onboarding when the saved game could not be loaded
 * (C5, PR #15). The store owns every decision: this only asks it to start fresh,
 * confirm, cancel or try loading again, and never keeps its own copy of the
 * confirmation token. Starting fresh copies the old save to a backup key first.
 */
const copy: Record<SaveLoadProblem['kind'], { icon: IconName; title: string; body: string }> = {
  unreadable: {
    icon: 'journal',
    title: 'YOUR SAVE WOULD NOT OPEN',
    body: 'Part of your saved garden could not be read. It is still on this device and nothing has been changed. You can try loading it again, or start a new garden and keep the old save as a backup.',
  },
  newer: {
    icon: 'arrowUp',
    title: 'UPDATE THE APP',
    body: 'This garden was saved by a newer version of NapAttack. Update the app to keep playing. Your save is still on this device and nothing has been changed.',
  },
  storage: {
    icon: 'journal',
    title: 'COULD NOT READ YOUR SAVE',
    body: 'Your save could not be read just now, or it changed while it was being checked. Nothing has been replaced. Try loading it again.',
  },
};

const START_FRESH_QUESTION = 'Your old save will be kept on this device. Start a new garden?';

type Host = ComponentRef<typeof View>;

/** Move focus (web) or the screen reader (native) to a group that just appeared. */
function focusGroup(node: Host | null) {
  if (!node) return;
  if (Platform.OS === 'web') node.focus();
  else AccessibilityInfo.sendAccessibilityEvent(node, 'focus');
}

function startFresh() {
  gameStore.getState().requestSaveRecovery();
}
/** The token is read from the store at the moment of confirming, never cached here. */
function confirmFresh() {
  const problem = gameStore.getState().saveLoadProblem;
  if (problem?.kind !== 'unreadable' || problem.busy || !problem.confirmationId) return;
  void gameStore.getState().confirmSaveRecovery(problem.confirmationId);
}
/** Cancel, Escape and Back: close the confirmation, unless a fresh start is running. */
export function cancelFreshStart() {
  const problem = gameStore.getState().saveLoadProblem;
  if (problem?.kind !== 'unreadable' || problem.busy || !problem.confirmationId) return;
  gameStore.getState().cancelSaveRecovery();
}
function retry() {
  void gameStore.getState().retrySaveLoad();
}

export function SaveRecovery({ problem }: { problem: SaveLoadProblem }) {
  const u = usePixelUnit();
  const busy = problem.kind === 'unreadable' && problem.busy;
  const error = problem.kind === 'unreadable' ? problem.error : null;
  // The confirmation stays up (disabled) while the backup and fresh start run.
  const confirming = problem.kind === 'unreadable' && (problem.confirmationId !== null || busy);
  const view = confirming ? 'confirm' : problem.kind;
  const { icon, title, body } = copy[problem.kind];
  // Focus follows the group that replaced the one the player just used, so a
  // keyboard or screen reader never lands on a control that has gone.
  const group = useRef<Host>(null);
  const shown = useRef(view);
  useEffect(() => {
    if (shown.current === view) return;
    shown.current = view;
    focusGroup(group.current);
  }, [view]);
  return (
    <View style={{ flex: 1, backgroundColor: c.paper }}>
      <CozyBackground />
      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={{ flexGrow: 1, justifyContent: 'center', padding: 16 }}
      >
        <CozySheet style={{ gap: panelGap(u) }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: panelGap(u) }}>
            <View
              style={{
                width: barControl(u),
                height: barControl(u),
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <FrameFill tone="parchment" inset />
              <PixelIcon name={icon} size={iconSize.medium(u)} />
            </View>
            <Text
              accessibilityRole="header"
              style={[type.title, { flex: 1, minWidth: 0, color: c.ink }]}
            >
              {title}
            </Text>
          </View>
          <Text style={[type.body, { color: c.ink }]}>{body}</Text>
          {confirming ? (
            <View
              key="confirm"
              ref={group}
              tabIndex={-1}
              accessibilityLiveRegion="polite"
              style={{ gap: panelGap(u), padding: contentInset(u) }}
            >
              <FrameFill tone="parchment" />
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: panelGap(u) }}>
                <PixelIcon name="sprout" size={iconSize.medium(u)} />
                <Text style={[type.heading, { flex: 1, minWidth: 0, color: c.ink }]}>
                  {START_FRESH_QUESTION}
                </Text>
              </View>
              <PixelButton
                label={busy ? 'STARTING FRESH...' : 'YES, START FRESH'}
                disabled={busy}
                onPress={confirmFresh}
              />
              <PixelButton label="CANCEL" small light disabled={busy} onPress={cancelFreshStart} />
            </View>
          ) : (
            <View key={view} ref={group} tabIndex={-1} style={{ gap: panelGap(u) }}>
              {error && (
                <View
                  accessibilityRole="alert"
                  accessibilityLiveRegion="assertive"
                  style={{ padding: contentInset(u) }}
                >
                  <FrameFill tone="danger" />
                  <Text style={[type.label, { color: c.buttonInk }]}>{error}</Text>
                </View>
              )}
              {problem.kind === 'unreadable' && (
                <PixelButton label="START FRESH" disabled={busy} onPress={startFresh} />
              )}
              {/* The only way forward when the save could not be read; optional otherwise. */}
              <PixelButton
                label="TRY LOADING AGAIN"
                small={problem.kind !== 'storage'}
                light={problem.kind !== 'storage'}
                disabled={busy}
                onPress={retry}
              />
            </View>
          )}
        </CozySheet>
      </ScrollView>
    </View>
  );
}
